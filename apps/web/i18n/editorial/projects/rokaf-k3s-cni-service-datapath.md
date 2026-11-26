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

### Network Namespace와 첫 번째 라우팅 지점

일반적인 Linux Pod는 인터페이스와 Route, Socket 상태를 가진 별도의 Network Namespace에서 실행된다. veth Pair는 한쪽 인터페이스로 보낸 Ethernet Frame을 반대쪽에 전달한다. Bridge 기반 CNI라면 Host 쪽 veth를 Bridge에 연결한다. 같은 서브넷에 있는 Pod끼리는 Layer 2에서 전달할 수 있고 서브넷 밖으로 가는 트래픽은 Pod의 기본 Gateway를 거쳐 Host의 IP Routing으로 이어진다. Host Network를 사용하는 Pod나 다른 CNI에서는 경로가 달라질 수 있다.

{{figure /figures/journals/datapath-01-namespace.svg | Bridge 기반 Pod 연결의 가상 구조. 로컬 Layer 2 전달과 Routing 경로는 같은 필터 Hook을 모두 거친다고 볼 수 없다.}}

Pod별 Namespace가 있다고 해서 각 Pod마다 물리 NIC를 갖는 것은 아니다. Bridge를 지나는 모든 Frame이 Host에서 IP Routing되는 것도 아니다. Bridge Netfilter가 활성화되면 브리지 트래픽에도 IP 계층 필터가 적용될 수 있으므로 커널 설정과 규칙의 종류를 확인해야 한다. Pod 인터페이스, Host veth, Tunnel Device 중 어디에서 패킷을 관측했는지도 중요하다.

## Flannel 인터페이스와 노드 간 전달 경로

Flannel 인터페이스가 `UP`인 것은 분명히 확인한 사실이다. 하지만 해당 노드에 인터페이스가 있다는 것과 다른 노드의 Pod까지 실제 패킷이 도달한다는 것은 다르다.

K3s에 포함된 Flannel은 반드시 별도 Kubernetes Deployment나 DaemonSet Pod로 보이는 형태가 아니다. `flannel`이라는 이름의 Pod를 찾지 못했다고 Flannel이 설치되지 않았다고 단정하면 조사 방향을 잘못 잡게 된다. K3s Agent의 네트워크 구성과 실제 인터페이스, Route, 패킷 흐름을 함께 봐야 했다.

같은 노드끼리 통신이 성공하더라도 다른 노드로 가는 터널 패킷이 중간에서 차단될 수 있다. 요청은 도착했지만 응답이 다른 경로로 돌아가 실패할 수도 있다. 호스트 방화벽이나 Network Policy에서 패킷이 걸리는 단계도 따로 있다.

### VXLAN과 노드 간 캡슐화

Flannel의 일반적인 VXLAN 구성에서는 다른 노드의 Pod 서브넷으로 가는 Route가 Tunnel Device 쪽을 가리킨다. 공개 구현을 살펴보면 원격 노드별로 Route와 Neighbor, FDB 항목을 관리한다. Neighbor는 원격 Tunnel Endpoint의 링크 계층 식별자를 찾는 데 쓰이고, FDB는 그 식별자를 원격 Underlay 주소와 연결한다. 이 세 가지 관계가 맞아야 하며 인터페이스가 UP이라는 사실만으로는 확인할 수 없다.

VXLAN은 내부 Ethernet Frame을 외부 UDP/IP 패킷에 담는다. 내부 IP의 목적지는 여전히 상대 Pod이고 외부 IP는 수신 노드의 Tunnel Endpoint를 가리킨다. 수신 측에서 외부 헤더를 제거한 뒤 내부 Frame을 백엔드 방향으로 전달한다. 일반적인 IPv4 Underlay에서 내부 Ethernet과 외부 IPv4, UDP, VXLAN 헤더로 인해 내부 IP 패킷에 50바이트가 추가된다. VLAN 등의 부가 헤더가 없고 Underlay IP MTU가 1500바이트라고 가정하면 내부 IP MTU는 1450바이트가 된다. 당시 실제 Backend와 MTU를 확인한 결과는 아니다.

{{figure /figures/journals/datapath-02-vxlan.svg | 내부 주소와 외부 주소를 분리한 가상의 VXLAN 패킷. 헤더 크기는 추가 VLAN이 없는 IPv4 Underlay를 가정했다.}}

2025년 11월 24일 기록에는 Flannel 인터페이스 이름과 Route 상태가 남아 있었지만 Backend나 Tunnel의 전체 구성은 확인되지 않았다. Pod 대역의 주소로 연결하다 TCP Timeout이 발생한 별도 기록도 있었다. 이는 또 다른 요청이 실패했다는 증거이지 해당 주소가 일반적인 Pod였거나 VXLAN이 실패 원인이었다는 증거는 아니다.

그렇기 때문에 당시 확인한 사실을 다음처럼 제한해서 해석했다.

| 확인한 상태 | 알 수 있는 사실 | 아직 알 수 없는 사실 |
| --- | --- | --- |
| Flannel 인터페이스 `UP` | 로컬 인터페이스가 존재하고 올라와 있음 | 노드 사이 실제 전달이 되는지 |
| Pod 네트워크 Route 존재 | 노드에 목적지 경로가 등록돼 있음 | 필터·Overlay·반환 경로까지 정상인지 |
| Service NAT 규칙 존재 | Service 관련 패킷 처리 규칙이 등록돼 있음 | 실패한 요청이 그 규칙을 통과했는지 |
| EndpointSlice에 Ready 주소 존재 | 백엔드 후보가 준비 상태로 등록돼 있음 | 실제 DNS 질의에 응답하는지 |
| 일부 Pod에서 DNS 실패 | 해당 Pod가 이름 해석에 실패했음 | CoreDNS 프로세스 자체가 고장 났는지 |

실제로는 일부 Pod만 영향을 받았기 때문에 정상 Pod와 실패 Pod의 **출발 노드와 통신 경로**를 나란히 기록해야 했다. 하지만 당시 관측 범위에는 그 비교가 충분히 남아 있지 않다.

### 주소와 포트를 따라가는 Service 요청

가상의 UDP Client를 192.0.2.10:40000, DNS Service를 198.51.100.53:53, 선택된 Endpoint를 203.0.113.20:8053으로 두자. 모두 설명용 주소와 포트이며 운영망의 설정이 아니다. 일반적인 Routing 기반 iptables Service에서는 DNAT로 목적지를 Endpoint로 변경한 뒤 전달 경로를 결정한다. Hairpin이나 외부 출발지 등 Masquerade가 필요한 조건이 없다고 가정하면 Client의 출발 주소는 그대로다. Endpoint는 Service 주소가 아니라 자신의 주소와 Target Port로 요청을 받는다.

응답의 출발지는 Endpoint의 주소와 포트다. 응답이 기존 NAT Binding을 만든 Conntrack 문맥을 통과하면 역방향 DNAT로 출발지가 다시 Service 주소와 포트로 변환된다. Client에서는 처음 요청했던 상대가 응답한 것으로 보인다. 그래서 요청만 도착했거나 Backend에서 응답을 보냈다는 사실만으로 Client까지 정상 응답이 돌아갔다고 할 수 없다.

{{figure /figures/journals/datapath-03-tuples.svg | 가상의 DNS 요청 및 응답에서 주소와 포트가 바뀌는 네 단계. 이 예제에서는 Client 출발 주소를 유지하고 응답의 출발지를 Service로 복원한다.}}

Conntrack은 연결의 Original 및 Reply Tuple을 관리한다. Stateful NAT에서는 첫 패킷이 규칙에 매칭돼 Binding을 만들면 이후 패킷은 그 Binding을 사용한다. UDP에는 TCP와 같은 Handshake가 없지만 커널은 요청과 응답의 흐름을 추적할 수 있다. 다른 DNS 질의는 새로운 Tuple을 쓸 수도 있다. NAT 규칙의 카운터가 해당 연결의 모든 패킷 수를 의미하는 것은 아니다.

{{figure /figures/journals/datapath-04-conntrack.svg | DNAT의 Original·Reply Tuple과 선택적인 SNAT 예시. 실제 Conntrack Table에서 추출한 값은 아니다.}}

SNAT이 필요한 정책을 적용한다면 Endpoint에는 바뀐 출발 주소가 보인다. 응답에서는 역변환으로 Client의 목적지를 복원하고 DNAT의 역변환으로 Service 출발 주소도 복원해야 한다. 그림 생성 코드는 두 경우의 왕복 변환과 관계없는 응답의 거부를 검증한다. 실제 kube-proxy나 커널 NAT를 실행한 실험은 아니다.

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

### Netfilter Hook과 Route 결정

일반적인 IPv4 전달 패킷은 PREROUTING을 지나 Route를 결정하고 FORWARD, POSTROUTING을 통과한다. 보통 Conntrack이 Destination NAT보다 먼저 상태를 연결한다. DNAT 후 목적지가 로컬이라면 INPUT으로 향한다. Host가 직접 생성한 패킷은 OUTPUT에서 처리되며 목적지가 변경되면 경로를 다시 결정할 수 있다. 전달 경로의 Source NAT는 일반적으로 FORWARD 필터 이후 POSTROUTING에서 수행된다. 이는 논리적 Hook의 설명이며 실제 Chain 구성과 Priority가 항상 같다는 뜻은 아니다.

{{figure /figures/journals/datapath-05-hooks.svg | IPv4 전달 패킷, 로컬 입력, Host에서 생성한 출력 패킷의 Hook 경로. Bridge와 XDP 등은 생략했다.}}

FORWARD에서는 원래 Service IP가 아니라 변환된 Backend 주소를 기준으로 필터링할 수 있다. Conntrack에서는 Original Tuple을 살펴보고 Backend 인터페이스에서는 전달 과정 이후의 패킷을 관측한다. Service 규칙이 Endpoint를 제대로 선택했더라도 그 뒤에서 Drop될 수 있다. 반대로 이미 만들어진 NAT Binding을 사용하는 패킷이라면 NAT 규칙의 카운터가 매번 증가하지 않을 수 있다.

관련 Namespace에서 Conntrack의 현재 항목 수와 최대 한도, 삽입 실패나 Drop 통계, 해당 Flow의 상태를 비교할 것이다. 단순히 항목 수가 높다는 것만으로 Table 고갈을 확정할 수는 없다. 실제 실패한 질의와 Tuple, 시각, 인터페이스가 맞아야 한다. 당시에는 이 카운터를 함께 측정한 기록이 없다.

특히 `DOCKER-USER`는 Docker가 iptables Backend를 사용할 때의 체인이다. Docker의 nftables Backend는 같은 체인을 새로 만들지 않고 자체 Base Chain과 Priority를 사용한다. 두 환경에서 규칙을 확인하는 방법이 같다고 가정할 수 없다. 그렇다고 기존 로그가 실제로 iptables/nftables의 불일치를 증명하는 것은 아니다.

Service의 `KUBE-SVC-*` 규칙이 존재해도 패킷이 거기를 통과했다고 볼 수 없다. `conntrack` 고갈 역시 생각해 볼 수 있는 원인이었지만, 당시 사용량·한도·Drop 카운터를 같은 시각에 측정하지 못했다. 이 문제들의 실제 원인은 아직 확인되지 않았다.

## K3s iptables 규칙 적용 장애 복구

다른 시점의 K3s 기동 과정에는 조금 더 구체적인 기록이 남았다.

```text
Failed to bootstrap IPTables:
failed to apply partial iptables-restore
```

함께 나타난 메시지는 다른 프로세스가 xtables Lock을 점유해 `iptables-restore`가 잠금을 얻지 못했다는 내용이었다. 이는 **규칙을 적용하는 작업이 실패한 것**이지, 앞에서 조사한 DNS 요청이 특정 Docker 규칙에 의해 Drop됐다는 증거는 아니다.

이 iptables 초기화 문제를 해결하기 위해 K3s 기동 상태와 규칙 적용 과정을 조사했다. `/run/xtables.lock` 파일을 지우고 K3s를 재시작하는 시도도 있었지만, 파일이 다시 생기고 처음에는 규칙 복원이 계속 실패했다. 이후 규칙이 재생성됐고 **`bootstrap done` 로그가 확인됐다.** **iptables 규칙 적용 오류를 넘어서 K3s가 정상적인 Bootstrap 단계까지 진행하도록 복구한 것**이다. 다만 원래 Lock을 점유한 프로세스와 복구를 결정적으로 만든 조치는 남은 기록만으로 특정할 수 없다.

iptables는 정상 동작 중에도 `/run/xtables.lock`을 사용해 규칙 변경을 조정한다. 그러므로 잠금 파일이 있다는 이유만으로 삭제하는 것은 올바른 복구 방법이 아니다. 잠금 파일 경로를 없앤다고 그 잠금을 잡고 있던 프로세스까지 종료되지도 않는다. `iptables-restore`에는 잠금 획득을 기다리는 `-w` 옵션이 있지만, K3s에 실제 적용하고 검증한 설정 변경은 아니다.

### Lock 파일의 이름을 지운다고 잠금이 풀리는 것은 아니다

xtables 매뉴얼은 배타적 Lock 파일을 설명한다. 공개 iptables 소스에서는 열린 FD에 flock을 사용한다. 앞서 [VFS 글](/projects/linux-vfs-mount-lifecycle/)에서 확인했듯 파일 이름과 열린 파일 객체는 다르다. Lock을 가진 프로세스가 살아 있는 동안 파일 이름을 지워도 기존 FD가 Inode와 잠금을 유지할 수 있다. 같은 이름을 다시 만들면 다른 Inode와 별개의 잠금 영역이 생길 수 있다. 결국 서로 다른 파일을 잠근 두 Writer가 각각 배타적 권한을 얻었다고 판단하는 문제가 생긴다.

이 동작을 확인하기 위해 실제 xtables Lock 대신 임시 디렉터리의 일반 파일을 사용했다. 같은 Inode를 두 번 독립적으로 열어 배타적 Lock을 요청하자 두 번째 요청은 경합으로 실패했다. 이름을 삭제하고 동일한 이름의 새 파일을 만들자 기존 Lock을 유지한 채 새 Inode에 Lock을 잡을 수 있었다. 새 Inode의 또 다른 독립적인 Lock 요청은 실패했다. 기존 Lock을 해제하면 원래 Inode를 참조하던 FD가 그 Lock을 얻을 수 있었으며 새 Inode의 잠금과는 별개였다.

{{figure /figures/journals/datapath-06-lock.svg | 임시 파일을 이용한 실제 flock 실험. 이름을 지워도 원래 잠금이 해제되지 않고, 다시 만든 파일은 다른 Inode를 가리킬 수 있다. 실제 방화벽과 운영 Lock 파일에는 접근하지 않았다.}}

이 실험은 잠금 파일 삭제가 일반적인 복구 방법으로 적절하지 않은 이유를 보여준다. 당시 복구를 입증한 것은 규칙 재생성과 Bootstrap 완료 기록이었다. 다음 장애에서는 실제 잠금 주체와 실행 인자를 확인하고 지원되는 대기·조정 방법을 사용한 뒤 규칙 적용과 통신 성공을 각각 검증할 것이다.

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

- [Linux network namespaces](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) · [Flannel VXLAN implementation](https://github.com/flannel-io/flannel/blob/master/pkg/backend/vxlan/vxlan.go) · [Netfilter hooks](https://wiki.nftables.org/wiki-nftables/index.php/Netfilter_hooks) · [Stateful NAT](https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_%28NAT%29) · [Conntrack sysctl](https://docs.kernel.org/6.2/networking/nf_conntrack-sysctl.html) · [iptables locking implementation](https://android.googlesource.com/platform/external/iptables/+/refs/tags/android-12.1.0_r25/iptables/xshared.c) · [flock(2)](https://man7.org/linux/man-pages/man2/flock.2.html).
