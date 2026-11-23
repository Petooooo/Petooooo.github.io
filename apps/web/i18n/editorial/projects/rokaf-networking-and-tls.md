내부 서비스의 HTTPS 주소를 열었을 때 브라우저에 `NET::ERR_CERT_AUTHORITY_INVALID`가 나타난 적이 있다. Traefik에 인증서도 넣었고, `IngressRoute`의 경로도 맞게 설정했다고 생각했다. 그런데 브라우저가 받은 인증서의 이름은 내가 준비한 서비스 인증서가 아니라 `TRAEFIK DEFAULT CERT`였다.

처음에는 라우팅 규칙을 다시 살폈다. 하지만 어느 경로로 보내는지 결정하기 전에, Traefik이 이미 다른 인증서를 내보내고 있었다. 이 문제를 겪고 나서야 **접속에 실패했다는 결과보다 요청이 어디까지 도달했는지**가 더 중요하다는 생각이 들었다.

그 뒤로도 비슷해 보이는 접속 장애를 여럿 만났다. 새 `LoadBalancer` Service 하나를 만들었는데 관계없어 보이던 기존 서비스의 접속이 끊겼고, Outline은 웹 화면이 열려도 실시간 편집을 위한 연결이 실패했다. 어떤 경우에는 DNS나 VIP의 동작까지 의심해야 했다. 겉으로는 모두 '서비스에 접속할 수 없다'는 문제였지만, 같은 설정을 고쳐 해결할 일들은 아니었다.

## Traefik 기본 인증서와 IP 접근

폐쇄망에서는 모든 서비스에 원하는 DNS 이름을 붙일 수 없었다. 그래서 직접 IP와 포트로 접속해야 하는 경우가 있었다. 이때 HTTPS는 단순히 사설 CA를 신뢰하게 하는 것만으로 끝나지 않았다. 브라우저가 실제로 접속한 **IP가 인증서의 SAN에 포함돼 있는지**, 그리고 그 연결에서 **어떤 인증서가 선택됐는지**를 따로 확인해야 했다.

당시에는 `PathPrefix('/')` 같은 HTTP 라우팅 규칙을 고쳐도 기본 인증서 문제가 사라지지 않았다. `Host(...)` 조건을 더하는 것도 IP 직접 접속의 TLS 문제를 해결하지는 못했다. 서버는 HTTP 경로를 읽기 전에 TLS 핸드셰이크를 끝내야 하고, 그때 보낼 인증서를 먼저 선택하기 때문이다. DNS 이름을 이용한 SNI와 IP 직접 접속에서의 인증서 선택도 같은 조건이 아니다.

문제의 경계를 확인할 때는 실제 접속 경로의 인증서를 읽어봤다. `openssl s_client`로 받아온 인증서의 Subject·Issuer를 `openssl x509`로 확인하고, 기대한 인증서의 Fingerprint와 비교했다. 설정 파일에 인증서가 있다는 것보다 **클라이언트가 실제로 어떤 인증서를 받는지**가 결정적인 정보였다.

내가 선택한 방식은 필요한 IP를 SAN에 포함한 인증서를 준비하고, Traefik의 `TLSStore default`에 기본 인증서를 지정하는 것이었다. 그 뒤에는 동일한 접속 경로에서 기본 인증서 대신 의도한 인증서가 선택되는지 확인할 수 있었다. 다만 인증서를 올바르게 내보내는 것과 모든 사용자 PC가 발급 CA를 신뢰하는 것은 여전히 별개다.

{{figure /figures/journals/network-request-path.svg | 같은 접속 장애처럼 보여도 실제 확인할 곳은 서로 달랐다. 인증서 선택과 호스트 포트 충돌은 확인된 사건이고, DNS·VIP·CNI 원인에 대해서는 추가 증거가 필요하다.}}

## K3s ServiceLB HostPort 충돌

다른 시점에는 Traefik의 외부 접근 경로를 확장하려고 `LoadBalancer` Service를 추가했다. MetalLB가 VIP를 맡을 것이라고 생각했고, 기존 애플리케이션은 건드리지 않았다. 그런데 이전부터 사용하던 호스트 포트 경로가 갑자기 작동하지 않았다.

그때 같은 서비스에 이르는 다른 `NodePort` 경로는 여전히 열렸고, 새로 기대했던 VIP 경로는 처음에 연결을 거부했다. 모든 Pod나 CNI가 동시에 고장 난 상황으로 단정하기 어려웠다. 무엇이 달라졌는지 찾아보니 K3s에 내장된 ServiceLB가 새 Service를 보고 `svclb-*` 리소스를 만들고 있었다. 그 Pod들이 요청한 `hostPort`는 기존 접속에 필요했던 포트와 겹쳤다.

새 Service의 포트를 바꾸면 충돌이 피해졌고, Service를 삭제하자 기존 접속 경로가 돌아왔다. 처음에 의심했던 MetalLB가 그 `hostPort`를 직접 점유한 것은 아니었다. MetalLB의 외부 주소 광고와 K3s ServiceLB의 호스트 포트 사용은 서로 다른 책임이다.

이 경험은 새 Kubernetes 오브젝트를 하나 추가할 때도 그것을 감시하는 컨트롤러가 **호스트 수준의 공유 자원**을 요구할 수 있다는 것을 보여줬다. 이후 ServiceLB를 비활성화하는 방향으로 구성을 조정했고, 같은 충돌이 다시 나타나지 않았다는 운영 관측도 있었다. 다만 모든 노드와 모든 신규 Service를 대상으로 장기간 검증한 기록까지 남아 있는 것은 아니다. 구체적인 추가·삭제·복구 과정은 [ServiceLB 호스트 포트 충돌 기록](/projects/rokaf-service-lb-hostport-conflict/)에서 따로 다뤘다.

## 웹 페이지가 열려도 실시간 연결은 실패했다

Outline에서는 또 다른 층위를 봤다. Wiki 화면 자체는 열렸는데 문서의 실시간 편집은 정상적으로 동작하지 않았다. 이 조사에는 Traefik뿐 아니라 Outline 앞단의 Nginx 프록시도 관여했다.

처음 확인한 WebSocket 연결은 HTTP `400`이었다. Nginx가 `Upgrade`와 `Connection` 헤더를 전달하는 방식, `/realtime` 경로, HTTP/1.1과 연결 유지 설정을 살핀 뒤에는 **`101 Switching Protocols`** 응답을 확인했다.

이때의 `101`은 중요한 진전이었다. 하지만 편집한 문서가 모든 PC에서 끝까지 저장됐다는 뜻은 아니었다. 일부 클라이언트에서는 인증서 경고나 이미지 요청의 DNS 오류, 별도의 HTTP `401`도 보였다. 브라우저에서 Wiki 첫 화면을 가져오는 요청, WebSocket을 업그레이드하는 요청, 이미지를 내려받는 요청은 시작점과 실패 조건이 서로 달랐다.

당시 GitLab 인증 경로에서도 `EAI_AGAIN`과 `ETIMEDOUT` 같은 오류가 있었다. 이름을 찾지 못한 단계와 TCP 연결이 제시간에 맺어지지 않은 단계는 구분해야 했다. GitLab 로그인 화면이 브라우저에서 열렸다고 해서 Outline 서버가 GitLab의 사용자 정보 API에 접속할 수 있다는 의미는 아니다. 확인된 WebSocket 핸드셰이크 개선을 인증·첨부파일 문제까지 모두 해결했다는 이야기로 만들지는 않았다.

## 같은 접속 주소도 어디에서 호출했는지가 중요했다

서비스를 외부로 노출할 때는 `ClusterIP`, `NodePort`, `hostPort`, `LoadBalancer`가 자주 함께 등장했다. 그 위에 Traefik의 `IngressRoute`와 `IngressRouteTCP`까지 얹으면 설정만 보고는 어느 경로로 요청이 흘러가는지 판단하기 어렵다.

`ClusterIP`는 클러스터 내부 Service 접근을 제공하고, `NodePort`는 노드의 포트를 통한 경로를 만든다. `hostPort`는 특정 Pod가 호스트 포트를 사용하도록 요구한다. `LoadBalancer`는 구현에 따라 외부 주소와 전달 경로를 제공한다. Traefik은 선택된 EntryPoint에서 HTTP(S) 라우팅을 수행하거나 설정된 TCP 경로를 처리한다. 서로 같은 종류의 포트 설정이 아니므로 한쪽이 성공했다고 다른 쪽도 동작한다고 볼 수 없다.

Nexus처럼 관리 화면과 Docker Registry API의 접근 경로가 다른 서비스는 더욱 주의해야 했다. UI가 열리더라도 Registry의 `/v2/` 응답, TLS, 인증과 권한은 따로 확인해야 한다. `IngressRouteTCP`를 검토한 사실이 곧 그 TCP 경로로 모든 Registry 요청을 성공시켰다는 증거는 아니다.

비슷하게, 브라우저에서 `x509` 오류가 난 경우와 K3s의 containerd가 이미지를 가져올 때 `x509` 오류를 내는 경우도 서로 다른 클라이언트를 상대한다. 브라우저와 컨테이너 런타임, Kaniko는 같은 CA 저장소를 자동으로 공유하지 않는다.

## DNS·VIP·CNI 추가 조사

CoreDNS 가용성이나 MetalLB VIP의 불안정한 접근도 조사했다. 어떤 경우에는 특정 Pod에서 CoreDNS 또는 `ClusterIP`로 가는 요청이 실패하면서 Flannel, Service 전달 규칙, `iptables`, `conntrack`까지 확인할 필요가 있었다. 네트워크 인터페이스와 일부 NAT 규칙이 존재한다는 사실만으로 실제 패킷이 의도한 경로로 처리된다는 보장은 없었다.

하지만 이것들을 앞서 확인한 ServiceLB 포트 충돌과 한 원인으로 묶지는 않는다. 외부 VIP 광고 문제와 Pod에서 Service로 향하는 내부 전달 문제는 다른 경계다. Docker와 K3s가 같은 호스트에서 만든 방화벽 규칙이 영향을 줬을 가능성도 검토했지만, 그 자체가 확정된 근본 원인은 아니었다.

별도의 **K3s 기동 장애에서는 iptables 규칙 적용 오류를 복구**했다. `iptables-restore`가 xtables Lock을 확보하지 못하던 상태에서 조사와 재시작을 진행했고, 이후 규칙이 다시 생성되며 `bootstrap done`이 확인됐다. 이 기동 복구는 실제 완료한 작업이며, 앞서 조사한 DNS·VIP 문제의 원인을 확정한 것과는 다르다.

## 이후에는 서비스 도메인 노출 절차를 따로 정리했다

나중에 새 서비스를 붙일 때마다 주소와 TLS를 제각각 설정하는 문제를 줄이려고, 기존 사설 CA·cert-manager·Traefik IngressRoute·CoreDNS·MetalLB VIP를 하나의 서비스 노출 절차로 묶었다. [폐쇄망 K3s에서 서비스 주소와 TLS를 한 흐름으로 묶은 기록](/projects/rokaf-gitops-domain-tls-standardization/)에 그 과정을 따로 적었다. 다만 이것을 앞서 조사했던 간헐적인 DNS·VIP·CNI 장애 전체가 해결됐다는 의미로 연결하지는 않는다.

## 오류를 보기보다 실패한 요청의 주체를 먼저 봤다

이후 비슷한 접속 문제를 만나면 우선 요청을 **누가 보냈는지**부터 확인하려 한다. 브라우저인지, 특정 Pod인지, K3s의 containerd인지, 백엔드에서 외부 API를 호출하는 애플리케이션인지가 먼저다. 같은 주소라도 시작점이 다르면 DNS와 인증서 신뢰, 방화벽 경로가 다를 수 있기 때문이다.

그다음에는 이름 해석에 실패했는지, 대상 IP와 포트로 연결했는지, TLS에서 어떤 인증서를 받았는지, Traefik 라우터가 요청을 받았는지, Service Endpoint에 준비된 대상이 있는지, 실제 애플리케이션 동작이 되는지를 순서대로 본다. 매번 이 순서를 완벽하게 수행했다는 뜻이 아니라, 실패를 설명하는 데 필요한 증거를 잃지 않으려는 기준이다.

Traefik에서는 클라이언트에 실제 전달된 인증서를 확인했고, ServiceLB에서는 `svclb-*`의 `hostPort` 충돌과 복구를 확인했다. Outline에서는 프록시 경로를 바로잡은 뒤 WebSocket 응답이 **`400`에서 `101 Switching Protocols`로 바뀌는 것**을 확인했다. DNS·VIP·CNI 문제는 이 복구 결과와 구분해 별도로 조사했다.

## 관련 기록

- [K3s ServiceLB와 MetalLB의 호스트 포트 충돌](/projects/rokaf-service-lb-hostport-conflict/)
- [Outline의 WebSocket·GitLab 인증 경로](/projects/rokaf-internal-app-auth-and-tls/)
- [DNS와 VIP 미해결 조사](/projects/rokaf-dns-vip-open-investigations/)
- [Nexus·Kaniko와 사설 인증서](/projects/rokaf-private-artifacts-and-ci/)
