K3s에서 한 애플리케이션이 시작할 때마다 내부 서비스의 이름을 해석하지 못하고 실패했다. 모든 Pod가 같은 증상을 보이는 것은 아니었다. 네트워크 상태를 확인하니 Flannel 인터페이스는 `UP`이고 Pod 대역으로 향하는 Route도 있었다. Kubernetes Service와 관련된 NAT 규칙도 보였다.

설정은 대체로 갖춰져 있는 듯했지만, 그 사실만으로 실패했던 DNS 요청이 CoreDNS까지 도착했다고 말할 수는 없었다. 그때부터 **Pod IP로 보내는 패킷과 ClusterIP로 보내는 패킷이 어떤 단계를 거치는지** 다시 구분해 보기 시작했다.

이 기록에는 서로 다른 두 문제가 있다. 하나는 일부 Pod에서 DNS·Service IP 접근이 실패한 사건이다. 이때는 실제 패킷이 어느 규칙에서 막혔는지 확인할 자료가 남지 않았다. 다른 하나는 **K3s 기동 중 iptables 규칙 적용이 실패했다가 정상적으로 Bootstrap을 마치도록 복구한 경험**이다. 해결한 규칙 적용 문제까지 단순한 추측으로 남기지 않되, DNS 문제의 원인을 같은 사건으로 묶지 않으려 한다.

## Pod IP 라우팅과 ClusterIP 변환

Pod IP는 실제 워크로드의 네트워크 Endpoint를 가리킨다. K3s에서 Flannel을 사용하는 경우에는 CNI 설정과 Linux Routing이 Pod까지 가는 경로를 형성한다. 같은 노드에 있는 Pod끼리의 통신과 다른 노드의 Pod로 보내는 통신은 경로가 다를 수 있다. 다른 노드를 거쳐야 할 때는 사용 중인 Flannel Backend에 따라 Overlay를 통과하기도 한다.

반면 **ClusterIP는 Service의 가상 주소**다. kube-proxy가 iptables 모드로 동작한다면 해당 주소와 포트로 들어온 패킷을 Service 규칙이 잡아 적절한 Endpoint로 DNAT하고, 그제야 실제 백엔드 Pod를 향해 전달한다. nftables·IPVS 모드나 별도 Service 구현을 사용한다면 내부 처리 방식은 달라진다. 따라서 당시 노드가 어떤 프록시 모드로 동작했는지 먼저 확인해야 한다.

이 차이는 Route를 살펴볼 때 중요했다. Pod 대역의 Route는 보이는데 Service CIDR을 위한 일반적인 Route가 없다는 이유만으로 설정 누락을 의심할 수는 없다. ClusterIP는 **일반적인 Pod 네트워크의 라우팅 항목을 하나 더 만든 주소가 아니기 때문**이다.

{{figure /figures/journals/cni-podip-vs-clusterip.svg | 같은 출발 Pod에서 백엔드 Pod IP를 직접 향하는 경로와 ClusterIP를 거쳐 Service 변환을 받은 뒤 백엔드로 향하는 경로를 나눴다. 실제 클러스터의 내부 주소나 노드 배치가 아니라 kube-proxy의 iptables 모드를 예로 든 개념도다.}}

처음부터 비교해야 했던 것은 같은 출발 Pod에서 **같은 애플리케이션 요청을 두 경로로 보내는 결과**였다. 실제 백엔드 Pod IP로는 접속되는데 ClusterIP로만 실패한다면 Service 변환, Endpoint 선택, 응답 패킷의 상태 처리를 우선 살펴볼 수 있다. 둘 다 실패한다면 CNI 경로나 백엔드 프로세스 자체를 더 먼저 봐야 한다.

당시에는 이 두 결과를 같은 조건에서 나란히 기록하지 못했다. 따라서 위의 분기는 증명된 사건 경과가 아니라 다음 조사를 위한 비교 방법이다.

## Flannel 인터페이스와 노드 간 전달 경로

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

## iptables 규칙을 누가 관리하는가

이 환경에서는 Docker가 사용되던 호스트에 K3s의 containerd 워크로드도 운영됐다. 서로 다른 런타임이지만, 둘 다 같은 호스트의 네트워크 규칙에 영향을 줄 수 있었다. 그때 확인한 Service NAT 규칙만으로는 어느 규칙 작성자가 실제 요청에 영향을 줬는지 알 수 없었다.

패킷의 경로와 규칙의 소유권을 분리해 볼 필요가 있었다. iptables를 사용하는 환경에서 호스트를 통과하는 패킷은 `PREROUTING`에서 목적지가 변환될 수 있고, 라우팅 결정 뒤 `FORWARD`에서 필터링을 거치며 `POSTROUTING`에서 출발지가 변환될 수도 있다. 호스트가 직접 생성한 트래픽은 `OUTPUT`을 사용할 수 있으므로 모든 요청이 똑같은 경로를 지나지는 않는다.

Docker의 iptables Backend는 `DOCKER-USER` 등 별도 체인과 Masquerade·포트 게시 규칙을 사용한다. 설정에 따라 `FORWARD` 기본 정책을 `DROP`으로 바꾸기도 한다. K3s에서는 kube-proxy가 Service 변환을, Flannel·CNI가 Pod 전달과 필요한 Masquerade를, Network Policy 컨트롤러가 정책 필터링을 담당할 수 있다. 다만 **당시에 Docker가 Kubernetes의 규칙을 실제로 변경하거나 차단했다고 입증한 자료는 없다.** 여러 구성 요소가 함께 규칙을 관리한다는 점 때문에 조사 범위를 넓힌 것이다.

{{figure /figures/journals/netfilter-host-runtime-ownership.svg | 호스트를 통과하는 패킷의 Netfilter Hook과 Docker·K3s 네트워크 구성 요소의 규칙 작성 범위를 비교했다. 별도의 K3s 기동 사건에서 확인된 xtables 잠금 경합과 이후 Bootstrap 완료도 따로 표시했다. 실제 규칙이나 내부 배치도는 아니다.}}

특히 `DOCKER-USER`는 Docker가 iptables Backend를 사용할 때의 체인이다. Docker의 nftables Backend는 같은 체인을 새로 만들지 않고 자체 Base Chain과 Priority를 사용한다. 두 환경에서 규칙을 확인하는 방법이 같다고 가정할 수 없다. 그렇다고 기존 로그가 실제로 iptables/nftables의 불일치를 증명하는 것은 아니다.

Service의 `KUBE-SVC-*` 규칙이 존재해도 패킷이 거기를 통과했다고 볼 수 없다. `conntrack` 고갈 역시 생각해 볼 수 있는 원인이었지만, 당시 사용량·한도·Drop 카운터를 같은 시각에 측정하지 못했다. 이 문제들의 실제 원인은 아직 확인되지 않았다.

## K3s iptables 규칙 적용 장애 복구

다른 시점의 K3s 기동 과정에는 조금 더 구체적인 기록이 남았다.

```text
Failed to bootstrap IPTables:
failed to apply partial iptables-restore
```

함께 나타난 메시지는 다른 프로세스가 xtables Lock을 점유해 `iptables-restore`가 잠금을 얻지 못했다는 내용이었다. 이는 **규칙을 적용하는 작업이 실패한 것**이지, 앞에서 조사한 DNS 요청이 특정 Docker 규칙에 의해 Drop됐다는 증거는 아니다.

이 iptables 초기화 문제를 해결하기 위해 K3s 기동 상태와 규칙 적용 과정을 조사했다. `/run/xtables.lock` 파일을 지우고 K3s를 재시작하는 시도도 있었지만, 파일이 다시 생기고 처음에는 규칙 복원이 계속 실패했다. 이후 규칙이 재생성됐고 로그에 **`bootstrap done`**이 나타났다. **iptables 규칙 적용 오류를 넘어서 K3s가 정상적인 Bootstrap 단계까지 진행하도록 복구한 것**이다. 다만 원래 Lock을 점유한 프로세스와 복구를 결정적으로 만든 조치는 남은 기록만으로 특정할 수 없다.

iptables는 정상 동작 중에도 `/run/xtables.lock`을 사용해 규칙 변경을 조정한다. 그러므로 잠금 파일이 있다는 이유만으로 삭제하는 것은 올바른 복구 방법이 아니다. 잠금 파일 경로를 없앤다고 그 잠금을 잡고 있던 프로세스까지 종료되지도 않는다. `iptables-restore`에는 잠금 획득을 기다리는 `-w` 옵션이 있지만, K3s에 실제 적용하고 검증한 설정 변경은 아니다.

이때 복구한 것은 **K3s가 iptables 규칙을 적용하는 기동 과정**이었다. 앞서 살펴본 Pod의 DNS·ClusterIP 접속 장애는 규칙이 적용된 뒤 실제 패킷이 통과하는 문제다. 두 사건의 시간대와 패킷 기록이 연결되지 않으므로 같은 원인이라고 쓰지는 않는다.

## Netfilter 규칙 변경 전 확인 사항

같은 통신 장애가 다시 발생한다면 먼저 실제 Firewall Backend와 기본 정책, NAT와 필터 체인을 읽기 전용으로 확인할 것이다.

```bash
sudo iptables -S FORWARD
sudo iptables -t nat -S
sudo nft list ruleset
```

이 명령은 검사의 예시일 뿐, 원래 장애에서 얻은 출력이 아니다. 실제 규칙에는 내부 주소와 서비스 구조가 포함될 수 있으므로 그대로 공개하지 않는다. 또 동일한 요청을 보내면서 Interface, Endpoint, 규칙 카운터, conntrack과 반환 패킷을 함께 확인해야 어느 단계에서 실패했는지 좁힐 수 있다.

실제 패킷이 어느 규칙을 통과하는지 모른 채 전체 iptables 체인을 비우거나 기본 `FORWARD` 정책을 바꾸고, Docker 규칙 관리를 끄거나 CNI를 교체하는 일은 피하려 한다. 다른 서비스까지 중단될 수 있기 때문이다. Docker의 `FORWARD DROP`, nftables Backend 충돌, conntrack 고갈이 **별도 DNS 장애의 원인이었다는 기록은 없다.** 이 구분은 앞선 iptables 기동 장애의 복구 결과와는 다르다.

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

**K3s iptables 규칙 적용 장애는 복구했다.** 기동 중 xtables Lock 경합으로 `iptables-restore`가 실패했지만, 조사와 재시작 과정을 거쳐 규칙 재생성과 `bootstrap done`을 확인했다.

**Pod의 DNS·ClusterIP 접속 장애는 별도로 남아 있다.** 이때는 Flannel 인터페이스와 Pod Route, Service NAT 규칙이 존재한다는 것까지 확인했다. 실제 `FORWARD` 필터, conntrack, Service 변환 또는 반환 경로 중 어느 단계에서 실패했는지는 패킷 추적 없이 확정할 수 없었다.

다시 장애가 발생한다면 실패한 Pod의 실제 DNS 요청을 먼저 확보하고, 동일한 요청을 백엔드 Endpoint와 ClusterIP에 각각 보낸 뒤 소스 노드의 프록시 규칙·필터링·응답 경로를 비교할 것이다. 그 결과가 확보되기 전까지는 이 사건의 근본 원인을 미확정으로 남겨두는 편이 맞다.

## 관련 기록과 참고 자료

- [CoreDNS·MetalLB VIP 접속 장애 조사](/projects/rokaf-dns-vip-open-investigations/)
- [K3s 네트워크: Traefik·MetalLB·TLS](/projects/rokaf-networking-and-tls/)
- [Kubernetes — Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)
- [Kubernetes — Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [K3s — Basic Network Options](https://docs.k3s.io/networking/basic-network-options/)
- [Docker — Firewall rules](https://docs.docker.com/engine/network/firewall-iptables/)
- [Docker — nftables Backend](https://docs.docker.com/engine/network/firewall-nftables/)
- [iptables — Lock file](https://man7.org/linux/man-pages/man8/iptables.8.html)
- [iptables-restore — 잠금 대기 옵션](https://man7.org/linux/man-pages/man8/iptables-restore.8.html)
