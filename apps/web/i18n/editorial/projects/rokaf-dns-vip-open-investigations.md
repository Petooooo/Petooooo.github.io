K3s에서 내부 서비스에 접속이 되지 않을 때 처음에는 CoreDNS를 의심했다. 어떤 Pod에서는 DNS 요청이 실패했고, 다른 곳에서는 서비스가 열리는 듯했다. 특히 이름 해석 문제와 네트워크 접속 문제는 사용자가 보는 화면에서 구분하기 어려웠다.

그때 확인했던 서버의 상태는 한쪽으로 쉽게 결론 내릴 만한 모습이 아니었다. **Flannel 인터페이스는 UP이었고 Pod 네트워크 경로도 남아 있었다. Service와 관련된 NAT 규칙도 보였다.** 그런데 이런 설정이 존재한다는 사실과, 실제로 특정 Pod에서 보낸 패킷이 CoreDNS까지 도달한다는 사실은 같지 않았다.

비슷한 시기에 MetalLB VIP를 통해 노출한 서비스의 접속 안정성도 조사했다. 하지만 외부 VIP로 들어오는 요청과 Pod 내부에서 `ClusterIP`로 가는 DNS 요청은 서로 다른 출발점과 전달 경로를 가진다. 당시 자료로는 두 증상을 하나의 원인으로 묶을 수 없었다. 이 글에는 확인한 사실과 아직 증거가 부족한 부분을 그대로 나눠 남긴다.

## DNS가 실패했는데 Flannel은 살아 있었다

문제가 된 내부 경로에는 Pod에서 DNS Service로 보내는 요청이 있었다. 일부 Pod에서 CoreDNS 또는 Service의 가상 IP에 접근하지 못하면서 서비스 시작에 영향을 주는 증상이 관측됐다.

원인을 찾기 위해 노드의 네트워크 상태와 규칙을 살폈다. Flannel 인터페이스가 올라와 있었고 Pod 주소 대역으로 가는 경로가 존재했다. Service 관련 NAT 규칙도 확인할 수 있었다. 그렇다고 CoreDNS가 요청을 정상적으로 받고 답했다는 결론은 나오지 않았다.

Flannel 인터페이스의 UP 상태는 해당 인터페이스가 존재한다는 뜻이다. 실제 다른 노드까지 캡슐화된 패킷이 오가는지, 호스트 방화벽을 통과하는지, 반환 경로가 올바른지는 별도로 봐야 한다. NAT 규칙 역시 **설치됐다는 사실만으로 그 규칙이 실패한 요청에 적용됐다고 볼 수 없다.**

조사 과정에서는 DNS Service IP에 ICMP Ping을 보내는 시도도 있었다. 하지만 Kubernetes의 `ClusterIP`는 일반 서버 IP처럼 모든 ICMP 요청에 답해야 하는 주소가 아니다. Service에 설정된 UDP·TCP 포트의 실제 DNS 질의와 가상 IP에 보내는 Ping은 같은 검사가 아니다. 당시 Ping 결과만으로 CoreDNS가 고장 났다거나 kube-proxy가 제대로 동작하지 않는다고 판단해서는 안 됐다.

{{figure /figures/journals/dns-vip-investigation.svg | 실제로 관측한 DNS·Service IP 접근 이상과 확인한 네트워크 설정, 아직 입증하지 못한 Service 전달·VIP 광고 원인을 분리한 조사표다. 실제 내부 주소나 배치 구조를 나타내지는 않는다.}}

## DNS Service 경로와 CoreDNS Endpoint

이름 해석 실패를 조사할 때는 **같은 출발 Pod에서 어디로 요청을 보냈는가**가 중요하다. DNS Service 이름을 통해 조회한 결과와 CoreDNS의 실제 Endpoint로 직접 요청한 결과를 비교할 수 있다면, 조사의 범위를 줄일 수 있다.

예를 들어 특정 Pod에서 DNS `ClusterIP`를 통한 질의만 실패하고 적절한 CoreDNS Endpoint로 보낸 같은 질의는 성공한다면, 이름 해석 애플리케이션만 살피기보다 Service 프록시·Endpoint 선택·호스트 필터링을 조사할 근거가 생긴다. 둘 다 실패한다면 Pod의 직접 통신 경로나 CoreDNS 프로세스 상태까지 범위를 넓혀야 한다.

이것은 당시 두 종류의 질의를 모두 실행해 특정 결과를 얻었다는 의미가 아니다. **다음 재현에서 남겨야 할 비교 조건**이다. 정상 Pod와 실패 Pod가 모두 있다면 같은 DNS 이름과 같은 프로토콜을 사용해 출발 노드별 결과를 나란히 기록할 필요도 있다.

| 비교할 요청 | 확인하려는 지점 |
| --- | --- |
| 영향받은 Pod → DNS `ClusterIP:53` | Service 가상 IP를 거친 실제 UDP·TCP DNS 응답 |
| 같은 Pod → CoreDNS Endpoint의 DNS 포트 | Service 전달을 우회한 Resolver 및 Pod 경로 |
| 같은 노드와 다른 노드의 Pod → 동일한 목적지 | 출발 노드·CNI 경로에 따라 결과가 달라지는지 |
| EndpointSlice의 Ready 상태와 실제 질의 | 준비된 Endpoint가 실제 응답까지 제공하는지 |
| 실패 시각의 Service 규칙·패킷 흐름 | 규칙 존재 여부가 아니라 실제 매칭·전달 여부 |

특정 Pod에서만 실패했다면 CoreDNS 전체가 동시에 멈췄다고 단정할 이유가 줄어든다. 반면 같은 이름으로 보내는 모든 요청이 동일하게 실패했다면 Resolver 자체나 공유 Service 경로에 더 무게를 둘 수 있다. 어느 경우든 비교한 요청과 시간대가 같아야 한다.

## iptables·conntrack 조사 범위

Service 관련 NAT 규칙이 있었다는 관측 때문에 오히려 더 많은 질문이 생겼다. 패킷이 그 규칙을 실제로 통과했는지, Endpoint가 선택됐는지, 호스트의 FORWARD 필터나 Network Policy에서 차단됐는지, 응답이 원래 Pod까지 돌아왔는지까지 봐야 했다.

특히 `conntrack` 상태가 오래 남거나 테이블이 고갈됐다면 일부 요청에 영향을 줄 수 있다. 하지만 그 가능성이 있다는 것과, 당시에 실제로 고갈이 발생했다는 것은 다르다. **장애 발생 시점에 측정한 카운터와 제한값을 확보하지 못했으므로 conntrack을 확정 원인으로 쓸 수 없다.**

Docker와 K3s가 한 호스트에서 각각 네트워크 규칙을 생성할 수 있다는 점도 검토했다. 어느 컴포넌트가 어느 체인을 관리하는지 알아야 실제로 적용되는 규칙을 읽을 수 있다. 다만 Docker가 특정 규칙을 변경해 이번 DNS 장애를 만들었다고 입증한 자료는 없다. 단순히 iptables를 비우거나 CNI를 교체하는 조치로 종결한 사건으로 적지 않으려 한다.

이와 관련한 Pod IP·Service IP 전달 경로의 상세 조사 초안은 별도로 검토 중이다. 아직 근본 원인과 공개 가능한 설명 범위를 최종 확정하지 않았기 때문에 여기서는 추정된 수정 방법을 성공 사례로 옮겨 적지 않았다.

## MetalLB VIP는 별도의 질문이었다

외부에서 접근하는 `LoadBalancer` Service의 VIP는 Pod가 CoreDNS `ClusterIP`로 질의할 때와 같은 경로를 사용하는 것이 아니다. MetalLB는 Service에 할당한 외부 주소를 L2(ARP·NDP) 또는 BGP 같은 방식으로 네트워크에 알릴 수 있다. 실제 모드와 클라이언트의 네트워크 위치에 따라 확인할 증거가 달라진다.

당시에는 VIP의 접속이 불안정해 보이는 현상을 조사했지만, 클라이언트가 실패했던 시점에 어느 노드가 주소를 광고했는지, 그 광고가 실제로 변경됐는지, 패킷이 어느 노드까지 도착했는지를 일관되게 기록하지 못했다. **VIP가 반복적으로 다른 노드로 이동했다거나 MetalLB Speaker가 장애의 직접 원인이었다고 확정할 수는 없다.**

여기서도 같은 요청의 결과를 나누는 편이 낫다. VIP로의 TCP 연결이 실패했는지, 연결은 됐지만 TLS나 Traefik에서 멈췄는지, 올바른 Service Endpoint가 없었는지에 따라 다음 조사가 달라진다. DNS가 VIP 주소를 정상적으로 반환했더라도 그 주소에 도달할 수 있다는 보장은 없다.

또 하나의 혼동 요소는 K3s에 내장된 **ServiceLB**였다. 과거에는 LoadBalancer Service를 추가하자 `svclb-*`가 기존 서비스의 `hostPort`와 충돌했고, 새 Service를 제거하면 접속이 복구된 사건이 있었다. 이 원인은 실제 추가·삭제와 복구로 좁혔지만, 그것이 별도의 VIP 접속 불안정이나 DNS 질의 실패를 설명하는 것은 아니다. [ServiceLB 호스트 포트 충돌 기록](/projects/rokaf-service-lb-hostport-conflict/)에서 그 사건을 따로 다룬 이유다.

## 재시작 전 패킷·이벤트 기록

가용성을 회복하기 위해 CoreDNS나 네트워크 컴포넌트를 재시작해야 할 수 있다. 하지만 재시작한 뒤 접속이 된다는 결과는 그 시점의 복구를 보여줄 뿐, 재시작한 컴포넌트가 처음 문제를 일으켰다는 증거는 아니다.

간헐적인 장애에서는 재시작 전에 한 클라이언트의 실제 요청과 결과를 남길 수 있다면 좋겠다. 같은 시점에 DNS 질의 결과, VIP 또는 Service IP의 연결 상태, 준비된 Endpoint, 관련 이벤트를 함께 기록하고, 변경 직후에도 동일한 요청을 반복하는 방식이다.

당시에는 서로 다른 곳에서 수집한 증상이 있었지만 같은 시간축으로 묶인 클라이언트 요청과 패킷 전달 기록이 부족했다. 이 때문에 단순한 재시작이나 Replica 증설이 영구적인 해결책이었는지 검증했다고 쓸 수 없다. CoreDNS Replica를 늘리는 일도 한 Pod의 장애에는 도움이 될 수 있지만, 공통 Upstream Resolver나 노드 수준의 전달 장애까지 해결하는 것은 아니다.

다음에 재현한다면 다음 순서를 따르려 한다. 먼저 실패한 Pod와 정상 Pod에서 같은 DNS 요청을 반복한다. 그다음 Service IP와 실제 Endpoint를 비교해 내부 전달 문제를 좁힌다. 외부 VIP는 클라이언트의 연결 결과와 당시의 주소 광고·Endpoint 상태를 별도 시계열로 기록한다. 원인이 입증되기 전에는 실제 운영 환경에 무리한 규칙 삭제나 네트워크 교체를 적용하지 않을 것이다.

## 지금까지 확인한 범위

당시 일부 Pod에서 DNS·Service IP 접근 장애가 발생했지만 **Flannel 인터페이스와 Pod 경로, Service NAT 규칙은 존재**했다. 이 관측만으로 실패한 DNS 패킷이 어느 지점에서 멈췄는지 결정할 수는 없었다. 장애가 재현되면 같은 Pod에서 ClusterIP와 CoreDNS Endpoint로 실제 DNS 질의를 보내고, VIP 문제는 같은 시점의 광고 상태·응답 패킷을 따로 기록해야 한다. 두 경로 모두 아직 단일 원인이 확정되지 않았다.

## 관련 기록과 참고 자료

- [K3s 네트워크: Pod IP 라우팅과 ClusterIP 전달 경로](/projects/rokaf-k3s-cni-service-datapath/)
- [K3s 네트워크: Traefik·MetalLB·TLS](/projects/rokaf-networking-and-tls/)
- [K3s ServiceLB·MetalLB 호스트 포트 충돌](/projects/rokaf-service-lb-hostport-conflict/)
- [Kubernetes — Service 디버깅](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [Kubernetes — DNS 문제 조사](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
- [MetalLB — Troubleshooting](https://metallb.io/troubleshooting/)
