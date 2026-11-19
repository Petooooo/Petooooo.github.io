K3s에서 한 애플리케이션이 시작할 때마다 내부 서비스의 이름을 해석하지 못하고 실패했다. 모든 Pod가 같은 증상을 보이는 것은 아니었다. 네트워크 상태를 확인하니 Flannel 인터페이스는 `UP`이고 Pod 대역으로 향하는 Route도 있었다. Kubernetes Service와 관련된 NAT 규칙도 보였다.

설정은 대체로 갖춰져 있는 듯했지만, 그 사실만으로 실패했던 DNS 요청이 CoreDNS까지 도착했다고 말할 수는 없었다. 그때부터 **Pod IP로 보내는 패킷과 ClusterIP로 보내는 패킷이 어떤 단계를 거치는지** 다시 구분해 보기 시작했다.

남아 있는 운영 기록에는 일부 Pod의 DNS·Service IP 접속 실패와, 별도의 Pod 주소 대역 목적지에 대한 TCP Timeout이 있다. 하지만 실패 시각에 맞춘 전체 패킷 캡처나 규칙별 카운터는 남아 있지 않았다. 어떤 네트워크 설정을 고쳐서 근본 원인을 해결했다는 보고서가 아니라, 실제로 확인한 현상과 조사 과정에서 좁혀야 했던 지점을 정리한 글이다.

## Pod IP와 ClusterIP는 같은 방식으로 전달되지 않는다

Pod IP는 실제 워크로드의 네트워크 Endpoint를 가리킨다. K3s에서 Flannel을 사용하는 경우에는 CNI 설정과 Linux Routing이 Pod까지 가는 경로를 형성한다. 같은 노드에 있는 Pod끼리의 통신과 다른 노드의 Pod로 보내는 통신은 경로가 다를 수 있다. 다른 노드를 거쳐야 할 때는 사용 중인 Flannel Backend에 따라 Overlay를 통과하기도 한다.

반면 **ClusterIP는 Service의 가상 주소**다. kube-proxy가 iptables 모드로 동작한다면 해당 주소와 포트로 들어온 패킷을 Service 규칙이 잡아 적절한 Endpoint로 DNAT하고, 그제야 실제 백엔드 Pod를 향해 전달한다. nftables·IPVS 모드나 별도 Service 구현을 사용한다면 내부 처리 방식은 달라진다. 따라서 당시 노드가 어떤 프록시 모드로 동작했는지 먼저 확인해야 한다.

이 차이는 Route를 살펴볼 때 중요했다. Pod 대역의 Route는 보이는데 Service CIDR을 위한 일반적인 Route가 없다는 이유만으로 설정 누락을 의심할 수는 없다. ClusterIP는 **일반적인 Pod 네트워크의 라우팅 항목을 하나 더 만든 주소가 아니기 때문**이다.

{{figure /figures/journals/cni-podip-vs-clusterip.svg | 같은 출발 Pod에서 백엔드 Pod IP를 직접 향하는 경로와 ClusterIP를 거쳐 Service 변환을 받은 뒤 백엔드로 향하는 경로를 나눴다. 실제 클러스터의 내부 주소나 노드 배치가 아니라 kube-proxy의 iptables 모드를 예로 든 개념도다.}}

처음부터 비교해야 했던 것은 같은 출발 Pod에서 **같은 애플리케이션 요청을 두 경로로 보내는 결과**였다. 실제 백엔드 Pod IP로는 접속되는데 ClusterIP로만 실패한다면 Service 변환, Endpoint 선택, 응답 패킷의 상태 처리를 우선 살펴볼 수 있다. 둘 다 실패한다면 CNI 경로나 백엔드 프로세스 자체를 더 먼저 봐야 한다.

당시에는 이 두 결과를 같은 조건에서 나란히 기록하지 못했다. 따라서 위의 분기는 증명된 사건 경과가 아니라 다음 조사를 위한 비교 방법이다.

## Flannel 인터페이스가 UP이었다는 의미

Flannel 인터페이스가 `UP`인 것은 분명히 확인한 사실이다. 하지만 해당 노드에 인터페이스가 있다는 것과 다른 노드의 Pod까지 실제 패킷이 도달한다는 것은 다르다.

K3s에 포함된 Flannel은 반드시 별도 Kubernetes Deployment나 DaemonSet Pod로 보이는 형태가 아니다. `flannel`이라는 이름의 Pod를 찾지 못했다고 Flannel이 설치되지 않았다고 단정하면 조사 방향을 잘못 잡게 된다. K3s Agent의 네트워크 구성과 실제 인터페이스, Route, 패킷 흐름을 함께 봐야 했다.

같은 노드끼리 통신이 성공하더라도 다른 노드로 가는 터널 패킷이 중간에서 차단될 수 있다. 요청은 도착했지만 응답이 다른 경로로 돌아가 실패할 수도 있다. 호스트 방화벽이나 Network Policy에서 패킷이 걸리는 단계도 따로 있다.

그렇기 때문에 당시 확인한 사실을 다음처럼 제한해서 해석했다.

| 확인한 상태 | 알 수 있는 사실 | 아직 알 수 없는 사실 |
| --- | --- | --- |
| Flannel 인터페이스 `UP` | 로컬 인터페이스가 존재하고 올라와 있음 | 노드 사이 실제 전달이 되는지 |
| Pod 네트워크 Route 존재 | 노드에 목적지 경로가 등록돼 있음 | 필터·Overlay·반환 경로까지 정상인지 |
| Service NAT 규칙 존재 | Service 관련 패킷 처리 규칙이 등록돼 있음 | 실패한 요청이 그 규칙을 통과했는지 |
| EndpointSlice에 Ready 주소 존재 | 백엔드 후보가 준비 상태로 등록돼 있음 | 실제 DNS 질의에 응답하는지 |
| 일부 Pod에서 DNS 실패 | 해당 Pod가 이름 해석에 실패했음 | CoreDNS 프로세스 자체가 고장 났는지 |

실제로는 일부 Pod만 영향을 받았기 때문에 정상 Pod와 실패 Pod의 **출발 노드와 통신 경로**를 나란히 기록해야 했다. 하지만 당시 관측 범위에는 그 비교가 충분히 남아 있지 않다.

## ClusterIP에 Ping을 보냈던 검사

DNS Service IP로 ICMP Ping을 보내는 시도도 있었다. 당시에는 주소에 도달하는지 빠르게 알고 싶었던 것이지만, 그 결과는 DNS 서비스가 정상인지 판단하기에 충분하지 않았다.

Kubernetes의 ClusterIP는 모든 ICMP 요청에 답하는 일반 서버 주소가 아니다. Service는 지정된 프로토콜과 포트의 요청을 전달한다. DNS의 경우 핵심 검사는 UDP 53번 포트로 보내는 실제 DNS 질의이며, 필요한 경우 TCP 질의도 비교해야 한다. Ping에 응답하지 않아도 DNS 질의는 성공할 수 있다.

다음에는 우선 Service와 EndpointSlice를 확인한 뒤 같은 Pod에서 두 목적지를 비교하겠다.

```bash
kubectl -n kube-system get service kube-dns
kubectl -n kube-system get endpointslices \
  -l kubernetes.io/service-name=kube-dns
```

위 명령은 검사 방법을 설명하기 위한 읽기 전용 예시다. 원래 장애에서 이 명령을 실행하고 특정 결과를 얻었다는 뜻은 아니다. 실제 질의에서는 Service의 포트와 백엔드의 포트가 다를 수 있으므로, **같은 질문을 올바른 프로토콜과 포트로 보냈는지**까지 맞춰야 한다.

이 비교가 없었던 탓에 DNS 이름 해석 실패를 CoreDNS 애플리케이션 장애로 단정할 수도, kube-proxy의 Service 변환 문제로 확정할 수도 없었다.

## iptables와 conntrack을 의심했던 이유

Service NAT 규칙을 살피면서 몇 가지 가능한 장애 지점을 검토했다. 다만 모두 당시의 원인으로 확인된 것은 아니다.

첫 번째는 Service 변환이다. iptables 모드에서는 `KUBE-SVC-*` 계열 규칙이 Endpoint 선택에 관여할 수 있다. 하지만 규칙을 출력해서 봤다는 사실은 그 요청이 해당 규칙에 매칭됐다는 의미가 아니다. 실제 프록시 모드와 해당 시각의 패킷·카운터를 확인해야 한다.

두 번째는 호스트의 필터링과 포워딩이었다. 목적지가 DNAT된 뒤에도 FORWARD 단계나 Network Policy에서 차단될 수 있고, 요청은 통과했지만 반환 패킷이 실패할 수도 있다. Docker와 K3s가 같은 호스트에서 각각 규칙을 설치하는 환경이라면 실제 적용 순서와 어느 구성 요소가 규칙을 만들었는지도 확인해야 한다.

세 번째는 `conntrack`이다. NAT는 연결 상태의 영향을 받을 수 있고, 테이블이 꽉 차거나 상태가 맞지 않으면 일부 통신에서 문제가 나타날 수 있다. 그러나 **당시에 conntrack 용량 고갈을 보여주는 카운터나 동일 시각 로그를 확보하지 못했다.** 가능성을 확인했던 것이지, 고갈로 인한 장애라고 확정한 것은 아니다.

iptables와 nftables의 관계도 비슷했다. 두 명령이 서로 다른 규칙 표시를 제공할 수 있으므로 어떤 프론트엔드와 프록시 모드가 실제로 사용되는지 알아야 한다. 그렇다고 기존 로그에 `legacy/nft` 충돌이 확인됐던 것은 아니다.

실제 패킷이 어느 규칙을 통과하는지 모른 채 전체 iptables 체인을 비우거나 CNI를 바꾸는 방식은 피해야 했다. 다른 서비스의 통신까지 끊을 수 있고, 원인을 조사할 상태 자체를 지워버릴 수 있기 때문이다. 이번 사건에서는 특정 규칙 수정 이후 문제가 재현 가능하게 복구됐다는 자료가 없다.

## 다음 재현에서는 어떤 순서로 비교할까

{{figure /figures/journals/cni-service-diagnostic-matrix.svg | Pod IP 직접 연결, ClusterIP 경유 연결, DNS 실제 프로토콜, 노드 간 경로, NAT 카운터와 conntrack 상태를 비교하는 검사표다. 사고 당시의 테스트 결과가 아니라 다음 조사를 위해 구분해야 하는 항목이다.}}

가장 먼저 할 일은 실패했던 Pod를 기준으로 **같은 요청을 최대한 동일한 조건에서 반복하는 것**이다.

| 비교할 요청 | 확인하려는 지점 |
| --- | --- |
| 백엔드 Pod IP와 실제 대상 포트 | 직접 라우팅·백엔드 응답 |
| ClusterIP와 Service 포트 | Service 변환·Endpoint 선택 |
| DNS ClusterIP와 CoreDNS Endpoint에 동일 질의 | DNS 애플리케이션과 전달 경로 구분 |
| 같은 노드·다른 노드의 Pod에 요청 | 로컬 CNI·노드 간 Overlay 차이 |
| 요청 시각의 NAT Rule 카운터와 conntrack | 실제 규칙 매칭·연결 상태 |
| 정상 Pod·실패 Pod에서 같은 요청 | 출발 위치에 따른 차이 |

주의할 점은 Service의 `port`와 백엔드의 `targetPort`가 다를 수 있다는 사실이다. Pod IP와 ClusterIP에 단순히 같은 포트 번호로 접속했다가 한쪽만 실패한다고 해서 곧바로 Service 변환 문제라고 판단하면 안 된다.

한 번 성공한 요청도 특정 순간의 경로가 동작했다는 것만 확인해 준다. 간헐적인 장애였다면 같은 시간대의 반복 결과와 반환 패킷까지 남겨야 한다.

## Cilium을 검토했지만 전환한 것은 아니었다

이후 K3s 구성을 다시 검토하면서 Flannel을 유지할지, Cilium 같은 다른 CNI를 고려할지도 살펴봤다. 커널 요구사항과 네트워크 정책, Service 구현, Observability, 폐쇄망 이미지 배포와 업데이트까지 함께 고려해야 하는 선택이었다.

다만 이번 DNS 실패가 Flannel 자체의 버그 때문에 발생했다는 증거는 없다. **원인도 확정하지 않은 채 CNI를 바꾼다면**, 새로운 구현의 장단점은 평가할 수 있어도 기존 장애를 해결했다고 입증할 수는 없다. 실제로 확인된 것은 Flannel 사용 환경에서의 장애 조사와 대안 검토이지 Cilium 전환 완료가 아니다.

별도의 [K3s ServiceLB·MetalLB 호스트 포트 충돌](/projects/rokaf-service-lb-hostport-conflict/) 사건과도 구분해야 한다. 그때는 새로운 LoadBalancer Service가 `svclb-*`의 HostPort 사용을 유발했고, Service를 제거한 뒤 기존 접속이 복구되는 과정을 확인했다. **호스트 포트를 누가 점유했는가**와 **Pod에서 ClusterIP로 보낸 패킷을 누가 변환하는가**는 다른 문제다.

## 현재까지 확인한 범위

기록으로 확인할 수 있는 사실은 일부 Pod의 DNS·Service IP 접근 실패, Flannel 인터페이스와 Pod Route의 존재, Service NAT 규칙의 존재다. 별도로 Pod 주소 대역 목적지에 대한 Timeout도 있었다. 이것들을 하나의 인과관계로 연결할 패킷 추적 기록은 남아 있지 않다.

따라서 **실제 FORWARD 규칙의 Drop, conntrack 고갈, iptables/nftables 충돌, Flannel Overlay 결함이나 Cilium 전환을 통한 복구** 중 어느 것도 확인된 최종 원인·해결책이라고 기록하지 않는다.

다시 장애가 발생한다면 실패한 Pod의 실제 DNS 요청을 먼저 확보하고, 동일한 요청을 백엔드 Endpoint와 ClusterIP에 각각 보낸 뒤 소스 노드의 프록시 규칙·필터링·응답 경로를 비교할 것이다. 그 결과가 확보되기 전까지는 이 사건의 근본 원인을 미확정으로 남겨두는 편이 맞다.

## 관련 기록과 참고 자료

- [CoreDNS·MetalLB VIP 접속 장애 조사](/projects/rokaf-dns-vip-open-investigations/)
- [K3s 네트워크: Traefik·MetalLB·TLS](/projects/rokaf-networking-and-tls/)
- [Kubernetes — Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)
- [Kubernetes — Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [K3s — Basic Network Options](https://docs.k3s.io/networking/basic-network-options/)
- [Docker — Firewall rules](https://docs.docker.com/engine/network/firewall-iptables/)
