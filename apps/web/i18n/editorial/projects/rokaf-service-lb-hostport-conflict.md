Kubernetes에 `LoadBalancer` Service를 하나 추가했을 뿐인데, 다른 서비스로 들어가던 접속이 끊겼다. 기존 애플리케이션을 다시 배포한 것도 아니었다. 새 Service는 가상 IP를 받도록 만든 것이어서 처음에는 MetalLB의 주소 할당이나 Service Endpoint를 의심했다.

하지만 실제로 달라진 것은 애플리케이션보다 **호스트에서 사용할 수 있는 포트**였다. K3s에 기본으로 포함된 ServiceLB가 여전히 실행 중이었고, 새로운 `LoadBalancer` Service를 발견하자 `svclb-*` 리소스를 생성했다. 그 Pod들은 Service에 해당하는 포트를 `hostPort`로 요청하고 있었다. 기존 접속 경로도 같은 호스트 포트에 의존하고 있었다.

문제가 된 새 Service의 포트를 바꾸면 충돌이 사라졌다. Service 자체를 삭제하자 ServiceLB가 만든 리소스도 사라졌고 기존 접속이 돌아왔다. 나중에 가장 확신 있게 설명할 수 있었던 부분은 바로 이 **추가 → 충돌 → 검사 → 제거 → 복구**의 순서였다.

## 새 서비스와 관계없어 보이던 접속이 끊겼다

당시 눈에 보인 현상은 단순했다. 기존의 호스트 포트 기반 접속이 멈췄다. 그렇다고 클러스터 전체의 네트워크가 무너진 것은 아니었다. 다른 NodePort 경로로는 접근할 수 있었고, 새로 기대했던 VIP 경로는 처음에는 연결이 거부됐다.

이 두 결과를 함께 보니 추측의 범위를 줄일 수 있었다. 애플리케이션이 완전히 죽었거나 CNI 전체가 고장 났다고 말하기 어려웠다. 무엇보다 어느 접속 경로가 어떤 컴포넌트에 의해 만들어지는지를 먼저 살펴야 했다.

처음에는 새로 만든 Service만 확인했다. 그런데 `LoadBalancer` Service를 추가하면 K3s의 기본 ServiceLB 컨트롤러가 별도의 작업을 시작할 수 있다. 내가 직접 만들지 않은 `svclb-*` Pod가 그것이다. 이름보다 중요한 것은 Pod가 **호스트 수준에서 포트를 요구한다는 사실**이었다.

{{figure /figures/journals/k3s-servicelb-port-contention.svg | 새 Service를 추가하기 전, 추가한 뒤, 다시 제거한 뒤를 나눠 보았다. 표시된 충돌은 동일한 호스트 포트에 대한 경쟁을 뜻하며 두 프로세스가 동시에 포트를 정상 점유했다는 의미는 아니다.}}

Kubernetes에서 서로 다른 Namespace를 쓰면 리소스가 꽤 독립적으로 보인다. 하지만 `hostPort`는 그렇게 나뉘는 자원이 아니다. 서로 무관한 애플리케이션이더라도 같은 호스트와 포트에 접근하려 한다면 영향을 주고받을 수 있다.

이 기록이 구체적으로 증명하는 것은 ServiceLB가 충돌하는 호스트 포트를 요청했고 새 Service를 제거하면 기존 접근이 복구됐다는 점이다. 실제 커널에서 어떤 순서로 Bind가 실패했는지, iptables 규칙이 정확히 어느 순간 바뀌었는지까지 추적한 결과는 아니다.

## MetalLB와 ServiceLB는 무엇을 소유하는가

두 컴포넌트는 모두 LoadBalancer와 관련돼 있어 이름만 보면 역할이 겹치는 것처럼 느껴진다. 하지만 실제 책임은 다르다.

MetalLB는 적절한 외부 IP를 할당하고, L2 또는 BGP 방식으로 그 주소에 대한 도달 경로를 알리는 일을 한다. 주소를 받은 트래픽이 실제 애플리케이션까지 전달되는지는 Kubernetes의 Service 포워딩과 Endpoint 상태 등 다른 계층에도 달려 있다.

반면 K3s의 ServiceLB는 `LoadBalancer` Service를 보고 호스트 포트 기반의 Pod를 만들어 외부 접속 경로를 제공한다. 내가 MetalLB에 외부 주소 관리를 맡기려 했는데도 ServiceLB가 남아 있었다면, 하나의 Service 생성이 별도의 호스트 포트 점유까지 촉발할 수 있었던 셈이다.

{{figure /figures/journals/k3s-servicelb-metallb-ownership.svg | MetalLB의 주소 할당·광고와 ServiceLB의 호스트 포트 기반 노출은 서로 다른 책임이다. 실제 네트워크 구성을 공개한 그림은 아니다.}}

내가 해결하려던 문제는 단순히 “LoadBalancer 두 개가 충돌한다”는 막연한 표현보다 정확했다. **새 Service가 ServiceLB를 통해 호스트 포트 자원을 요구했고, 그 자원에 의존하던 기존 경로가 영향을 받았다.**

## 설정 한 줄로 해결되지 않았던 이유

찾아보던 설정 중 하나가 `allocateLoadBalancerNodePorts: false`였다. 이름에 LoadBalancer와 NodePort가 모두 들어 있으니, 포트 충돌과 연관될 것 같았다.

하지만 이 옵션은 Kubernetes가 `LoadBalancer` Service에 NodePort를 할당할지 결정하는 설정이다. K3s의 ServiceLB 컨트롤러를 끄는 옵션이 아니며, ServiceLB가 `hostPort`를 사용하는 Pod를 만들지 못하게 하는 것도 아니다.

여기서 구분해야 할 포트와 주소가 여럿이었다.

| 이름 | 실제 의미 |
| --- | --- |
| Service port | Service가 클라이언트에 제공하는 포트 |
| Target port | 선택된 애플리케이션 Endpoint가 듣는 포트 |
| NodePort | Kubernetes가 노드를 통해 Service에 접근하도록 할당한 포트 |
| `hostPort` | 특정 Pod가 호스트 네트워크 문맥에서 요청하는 포트 |
| VIP | 서비스의 가상 네트워크 주소. 모든 포트를 선점했다는 뜻은 아님 |

특히 **VIP는 IP 주소이고 `hostPort`는 호스트의 포트 자원**이다. MetalLB가 VIP를 할당했다고 해서 MetalLB가 해당 포트를 직접 Bind했다고 결론 내리면 잘못된 계층을 조사하게 된다.

새 Service의 포트를 바꿨더니 문제가 사라진 것은 중요한 실험이었다. 다만 그것은 당장의 충돌을 피해간 것이지, 앞으로 새 `LoadBalancer` Service를 만들 때마다 어느 구현이 책임질지를 정해준 것은 아니었다.

## 외부 노출을 누가 책임질지 정하기

장기적으로는 두 가지 방향을 생각할 수 있었다. ServiceLB를 외부 노출의 주체로 유지하고 호스트 포트 배치를 고려하는 방법이 하나다. 다른 하나는 이미 사용하던 MetalLB에 외부 주소 할당을 맡기고, K3s의 기본 ServiceLB는 비활성화해 의도하지 않은 호스트 포트 요구를 막는 방법이다.

기존 플랫폼 구성을 생각하면 두 번째가 더 자연스러웠다. 실제 장애 조사에서도 **ServiceLB를 끄는 방향**으로 의견을 모았다. 그렇지만 여러 K3s 서버에 설정이 일관되게 적용됐는지, 이후 생성한 모든 `LoadBalancer` Service에서 `svclb-*` 리소스가 다시 나타나지 않았는지까지 남아 있는 자료로 증명할 수는 없다.

그래서 여기서는 “영구적으로 해결했다”보다 “왜 이 운영 모델을 선택했는가”를 남긴다. 한 컨트롤러가 외부 주소를 관리한다는 사실과, 다른 컨트롤러가 몰래 호스트 포트를 요구하지 않는다는 사실을 각각 검증해야 했다.

사후 검증이 충분하려면 다음 결과가 필요하다. 새 Service를 만들어도 ServiceLB Pod가 불필요하게 생기지 않아야 한다. 기존 호스트 포트 경로는 계속 열려 있어야 한다. VIP로 접근한 요청이 실제 백엔드에 도달해야 한다. 그리고 Service 포트를 바꾸거나 테스트 Service를 다시 만들어도 같은 결과가 반복돼야 한다.

이것은 **내가 원했던 검증 기준**이다. 당시 이 항목을 모두 완료했다고 주장하는 것은 아니다.

## 포트 충돌보다 오래 남은 질문

Kubernetes 오브젝트 하나를 만들면 화면에서 보이는 리소스 하나만 생기는 것이 아니다. 컨트롤러가 그 오브젝트를 해석해 Pod를 배치하고, 노드 수준의 포트와 경로를 사용할 수 있다.

이번 장애에서 직접 확인할 수 있었던 연결고리는 분명하다. 새로운 `LoadBalancer` Service를 만들자 기존 접속이 끊겼고, ServiceLB의 포트 요청을 확인했다. 새 Service 포트를 바꾸자 충돌을 피할 수 있었으며, Service를 삭제하자 기존 접속이 복구됐다.

하지만 이 사실을 근거로 나중의 모든 DNS 장애, VIP 불안정, Pod-to-ClusterIP 접근 문제까지 같은 원인으로 설명하고 싶지는 않다. 그 문제들은 CNI와 Service 포워딩, iptables, DNS의 동작을 따로 조사해야 한다.

새 LoadBalancer Service를 추가하면서 K3s ServiceLB가 기존 접속 경로와 겹치는 `hostPort`를 요청했다. Service의 포트를 바꾸거나 삭제하자 충돌이 사라지고 기존 경로가 복구되는 것을 확인했다. 별도의 DNS·VIP 문제까지 이 원인으로 설명할 자료는 없다.

## 참고 자료

- [K3s ServiceLB 동작과 비활성화](https://docs.k3s.io/networking/networking-services)
- [MetalLB와 K3s ServiceLB](https://metallb.io/configuration/k3s/index.html)
- [Kubernetes Service 유형](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Traefik·MetalLB·TLS 요청 경로 조사](/projects/rokaf-networking-and-tls/)
- [DNS와 VIP 조사 기록](/projects/rokaf-dns-vip-open-investigations/)