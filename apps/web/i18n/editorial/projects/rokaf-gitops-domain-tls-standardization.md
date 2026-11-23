> **2026년 11월, 폐쇄망 K3s의 서비스 도메인과 TLS를 정리한 기록이다.** 기존에 사용하던 사설 Root CA와 MetalLB VIP를 바탕으로 cert-manager의 Certificate, Traefik IngressRoute, CoreDNS 레코드를 한 흐름으로 묶었다. 아래의 도메인과 IP, CA·Secret 이름은 실제 값이 아니라 설명을 위한 예시다.

앱을 Kubernetes에 배포하고 Service까지 만들어 두어도, 그 서비스를 **어떤 주소로 접속하게 할 것인지**는 별개 문제였다. 사용자가 기억할 도메인이 있어야 하고, 그 이름이 VIP로 해석되어야 하고, Traefik이 올바른 앱으로 연결해야 했다. HTTPS까지 들어가면 인증서 발급부터 실제 클라이언트의 신뢰까지 챙길 부분이 더 생겼다.

예전에는 Traefik이 `TRAEFIK DEFAULT CERT`를 보여주는 일을 겪었다. IP로 직접 접속하던 때에는 SAN이 맞는지와 어느 CA를 신뢰해야 하는지도 하나씩 확인해야 했다. **설정에 인증서가 있다는 사실과 사용자가 올바른 HTTPS 연결을 맺는 것은 달랐다.** 그래서 이번에는 새 서비스를 붙일 때마다 설정을 제각각 만드는 대신, 공통으로 따라갈 수 있는 패턴을 마련했다.

## 도메인 하나를 열기까지 필요한 경로

{{figure /figures/journals/gitops-domain-01-request-path.svg | 클라이언트가 CoreDNS에서 이름을 해석한 뒤 VIP, Traefik, IngressRoute, Service, Pod로 이동하는 흐름이다. 각 단계는 서로 다른 책임이고, 실제 내부망 배치도가 아닌 개념도다.}}

사용자가 `app.apps.example.test`로 접근하면 CoreDNS가 도메인을 VIP로 해석하고, 요청이 Traefik의 `websecure` EntryPoint로 들어온다. 그 다음 `IngressRoute`의 Host·Path 규칙이 서비스 목적지를 결정한다. 이 연결에서 사용할 인증서는 cert-manager가 관리하는 TLS Secret에서 가져온다.

이렇게 나눠 보니 이전에 여러 문제를 한데 묶어 생각한 이유도 보였다. **CoreDNS는 인증서를 만들지 않고, MetalLB는 HTTP 요청을 어떤 앱으로 보낼지 선택하지 않는다.** Certificate가 Ready인 것과 클라이언트가 사설 Root CA를 신뢰하는 것도 서로 다른 조건이었다.

## 예전에 만들었던 Root CA를 다시 활용했다

{{figure /figures/journals/gitops-domain-02-ca-lifecycle.svg | GitOps에 선언한 Certificate와 cert-manager, CA 발급 체계, 생성된 TLS Secret, Traefik의 관계다. CA Private Key는 Git에 저장하지 않는다.}}

앱이 늘어날 때마다 개별 Self-Signed 인증서를 만들고 싶지는 않았다. 이전에 Root CA 체계를 만들고 Traefik과 다른 클라이언트의 Trust Store를 다뤄본 경험이 있었다. 이번에는 그 **기존 CA 신뢰 체계를 cert-manager에 연결**해, 필요한 인증서를 GitOps에서 선언하는 방식으로 정리했다.

GitOps repo에 `Certificate` Manifest를 추가하면 cert-manager가 `issuerRef`로 발급 주체를 참조하고, 결과 인증서와 Key Pair를 `secretName`에 해당하는 Kubernetes TLS Secret으로 관리한다. **Git에 넣는 것은 어떤 인증서가 필요한지에 대한 선언이지, Root CA의 Private Key나 발급된 서버 Key가 아니다.** 실제 클라이언트에 Root CA Trust Anchor를 배포하는 문제도 별도로 남는다.

사용한 필드와 구조를 공개용 값으로 바꾸면 다음과 같다.

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: apps-https-certificate
  namespace: example-apps
spec:
  secretName: apps-https-tls
  issuerRef:
    kind: ClusterIssuer
    name: internal-ca-issuer  # 공개용 예시 식별자
  commonName: apps.example.test
  dnsNames:
    - apps.example.test
    - "*.apps.example.test"
  ipAddresses:
    - 192.0.2.80          # 문서 예시용 VIP
  privateKey:
    algorithm: RSA
    size: 2048
    rotationPolicy: Never
```

{{figure /figures/journals/gitops-domain-03-certificate-fields.svg | Certificate의 issuerRef, Secret, DNS SAN, IP SAN, RSA 2048, rotationPolicy가 각각 담당하는 부분을 나눠 표현했다.}}

`commonName`에는 도메인을 적었고, `dnsNames`에는 실제 접속에 사용할 도메인과 Wildcard 범위를 넣었다. 여기에서 **CoreDNS의 주소와 Certificate의 DNS SAN은 다른 개념**이라는 점을 구분해야 한다. `dnsNames`는 DNS 서버 IP를 적는 칸이 아니다. 클라이언트가 접속하는 호스트 이름을 검증하기 위한 목록이다. 클라이언트가 다른 DNS Alias를 쓰는 경우라면 그 별칭도 SAN에 포함해야 할 수 있다.

`ipAddresses`에는 기존 MetalLB VIP를 넣었다. IP로 직접 HTTPS 접속을 할 때 인증서가 그 IP를 식별하도록 한 것이다. 도메인 접속에 IP SAN이 반드시 필요한 것은 아니다. 또 `*.apps.example.test` 형태의 Wildcard는 한 단계 하위 이름을 대상으로 하므로 더 깊은 이름까지 모두 커버한다고 생각하면 안 된다.

당시 설정한 Private Key 조건은 `RSA 2048`과 `rotationPolicy: Never`였다. 다만 **Never는 Certificate 자동 갱신을 중단한다는 뜻이 아니다.** 재발급할 때 같은 Private Key를 재사용한다는 의미다. 보안적으로는 `Always`를 통해 키를 교체하는 편이 더 권장되지만, 이 글에서는 실제로 사용했던 정책을 그대로 기록했다. Secret의 인증서가 갱신되면 Traefik이 바뀐 인증서를 제공하는지도 확인해야 한다.

## TLS 인증서를 선택하는 시점과 라우팅하는 시점

{{figure /figures/journals/gitops-domain-04-tls-before-route.svg | TLS Handshake에서 먼저 인증서를 선택하고, 그 뒤 HTTP Host 및 PathPrefix 규칙이 적용된다는 순서를 나타냈다.}}

이전에 `TRAEFIK DEFAULT CERT` 문제를 해결하면서 알게 된 사실이 여기서도 중요했다. `PathPrefix("/")`를 바꿔도 **TLS Handshake에서 이미 잘못된 인증서를 보낸 문제**는 해결되지 않는다. TLS에서 인증서를 선택하고 나서야 HTTP Host와 Path를 기준으로 실제 요청을 라우팅할 수 있기 때문이다.

기존 클러스터에서 사용하던 `traefik.containo.us/v1alpha1` 그룹의 `IngressRoute`를 추가했다. `entryPoints`는 `websecure`, `match`에는 해당 앱의 Subdomain과 `PathPrefix("/")`를 넣고 `tls.secretName`은 cert-manager가 생성한 TLS Secret과 연결했다.

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: example-app-https
  namespace: example-apps
spec:
  entryPoints: [websecure]
  routes:
    - kind: Rule
      match: Host(`app.apps.example.test`) && PathPrefix(`/`)
      services:
        - name: example-app-service
          port: 80
  tls:
    secretName: apps-https-tls
```

{{figure /figures/journals/gitops-domain-05-host-routing.svg | 여러 Subdomain이 같은 VIP를 가리켜도 Traefik은 Host 규칙을 보고 서로 다른 Kubernetes Service로 연결한다. Wildcard 인증서가 곧 Wildcard 라우터는 아니다.}}

Wildcard 인증서는 여러 이름에 사용할 수 있지만 **그것만으로 각 요청의 목적지가 자동으로 정해지지는 않는다.** 앱별로 정확한 Host Match를 두거나 의도적으로 설계한 `HostRegexp`가 필요하다. 위 예시에서는 다른 앱의 요청까지 한 곳에 들어가지 않도록 정확한 Host를 명시했다. 참고로 현재 Traefik 문서에서는 `traefik.io/v1alpha1`도 사용하므로 다른 클러스터에 적용하기 전에 실제 설치된 CRD 버전을 확인해야 한다. TLS Secret의 Namespace도 IngressRoute와 맞아야 한다.

## 앱에서 다시 HTTP로 보내는 문제

HTTPS Route를 붙였는데도 앱이 자기 Base URL을 `http://`로 알고 절대 경로를 만들거나 사용자를 평문 주소로 돌려보내는 경우가 있었다. 이럴 때는 Traefik의 `Middleware`와 `redirectScheme`으로 **HTTP로 들어오는 요청을 HTTPS로 돌리는 규칙**을 넣었다.

{{figure /figures/journals/gitops-domain-06-redirect.svg | web EntryPoint의 HTTP 요청은 RedirectScheme으로 HTTPS로 전환하고, websecure EntryPoint의 요청은 실제 앱으로 보낸다. 앱의 Base URL 설정 문제까지 자동 해결되는 것은 아니다.}}

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: force-https
  namespace: example-apps
spec:
  redirectScheme:
    scheme: https
    permanent: true
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: example-app-http
  namespace: example-apps
spec:
  entryPoints: [web]
  routes:
    - kind: Rule
      match: Host(`app.apps.example.test`) && PathPrefix(`/`)
      middlewares:
        - name: force-https
      services:
        - name: example-app-service
          port: 80
```

여기에도 중요한 조건이 있다. **websecure Route에만 Redirect Middleware를 붙여서는 web으로 들어오는 HTTP를 잡을 수 없다.** HTTP 요청을 받는 별도 Route가 필요하다. 반대로 앱 자체가 HTTPS 요청을 받은 뒤에도 계속 `Location: http://…`를 만들어 보내면 HTTP → HTTPS → HTTP의 Redirect Loop가 발생할 수 있다. 그때는 앱의 `BASE_URL`이나 `X-Forwarded-Proto` 같은 Proxy Header 처리를 같이 고쳐야 한다. 앞단의 Redirect로 해결되는 범위와 앱 자체 설정을 수정해야 하는 범위는 구분해 두었다.

## CoreDNS 레코드에서 공통 VIP로

{{figure /figures/journals/gitops-domain-07-dns-vip.svg | 여러 서비스 이름이 CoreDNS A 레코드를 통해 하나의 VIP를 가리킨 뒤, Traefik Host Routing으로 서로 다른 Service에 도달하는 모습을 보여준다. 실제 Zone 정보와 VIP는 포함하지 않았다.}}

CoreDNS Zone File에는 앱별 `A` 레코드를 넣었다. 새 Subdomain을 특정 Pod나 Node IP에 직접 연결하는 대신 **기존 MetalLB VIP를 가리키게 했다.** 그 결과 도메인으로 들어온 요청은 공통 접점에서 받고, 어떤 앱으로 보낼지는 Traefik의 Host Rule에서 결정할 수 있었다.

아래는 실제 레코드가 아닌 `apps.example.test` Zone을 가정한 예시다.

```text
app       IN A 192.0.2.80
wiki      IN A 192.0.2.80
dashboard IN A 192.0.2.80
```

DNS Record를 추가하는 것과 CoreDNS가 실제로 해당 Zone을 Serving하고 설정 변경을 반영하는 것은 별개의 일이다. 또한 DNS에서 VIP를 반환하더라도 모든 클라이언트 네트워크에서 그 VIP에 도달할 수 있다는 증거는 아니다.

## 새 서비스를 추가하는 과정이 분명해졌다

{{figure /figures/journals/gitops-domain-08-gitops-contract.svg | GitOps repo에서 선언하는 Certificate, IngressRoute, 선택적 Middleware와 실제 생성되는 Secret 및 DNS 관리 경계를 구분했다.}}

이제 서비스가 늘어나더라도 기본 순서를 반복할 수 있게 됐다. **Subdomain 결정 → Certificate 선언 → TLS Secret 상태 확인 → IngressRoute 작성 → 필요하면 HTTP Redirect → CoreDNS A 레코드 추가 → 실제 클라이언트에서 접속 확인.**

GitOps에는 `Desired State`와 변경 기록을 남긴다. cert-manager가 인증서를 발급하고, Traefik이 라우팅하고, CoreDNS가 이름을 해석한다. 만약 CoreDNS Zone 파일은 GitOps repo 외부에서 관리한다면 그것까지 GitOps로 자동화됐다고 말하면 안 된다. 각 리소스의 관리 범위가 다르다는 점도 실제 운영에서는 중요했다.

## 단순히 Ready라고 끝내지 않기로 했다

{{figure /figures/journals/gitops-domain-09-verification.svg | Certificate, DNS, VIP, 실제 TLS 인증서, Host Routing, HTTP Redirect, App Base URL을 각각 확인해야 하는 이유를 계층별로 정리했다. 모든 앱에서 검증이 완료됐다는 표시가 아니다.}}

`Certificate`가 Ready여도 브라우저에서 기본 인증서를 받을 수 있고, DNS가 VIP를 알려줘도 사용자 네트워크에서 연결이 막힐 수 있다. 첫 화면이 HTTPS로 열린다고 해도 로그인 Callback이나 Cookie, 앱 내부 링크가 여전히 잘못됐을 수 있다. 그래서 한 개의 성공 상태만으로 전체 경로가 정상이라고 판단하지 않으려 했다.

| 확인할 곳 | 실제로 살펴볼 내용 |
| --- | --- |
| Certificate | Issuer, SAN, Secret, 만료 시각과 갱신 상태 |
| CoreDNS | 사용자가 쓰는 Resolver에서 이름이 올바른 VIP로 해석되는지 |
| MetalLB VIP | 실제 클라이언트 경로에서 해당 VIP와 Port에 접근되는지 |
| TLS | SNI와 함께 접속했을 때 의도한 인증서가 전달되는지 |
| IngressRoute | 해당 Host와 Path가 원하는 Service로 연결되는지 |
| HTTP Redirect | HTTPS로 전환된 뒤 무한 Redirect가 발생하지 않는지 |
| 앱 | 외부 Base URL, Callback, Cookie와 주요 기능이 정상인지 |

이것은 **검증해야 하는 항목을 정리한 것이지**, 모든 앱과 PC에서 전수 테스트를 완료했다는 주장까지는 아니다. 특히 예전에 조사한 간헐적 DNS·VIP·CNI 문제를 이번 도메인 노출 표준화만으로 모두 해결했다고 표현하지 않는다.

## 설정 하나보다 문제를 나누는 기준이 남았다

처음에는 서비스가 안 열리면 IngressRoute나 Pod부터 살펴보기 쉬웠다. 하지만 이번에는 **어떤 계층이 무슨 역할을 책임지는지**가 더 뚜렷해졌다. DNS는 이름을 해석하고, MetalLB는 VIP를 맡고, Traefik은 TLS와 HTTP Routing을 다룬다. cert-manager는 인증서 상태를 맞추고, 앱은 자신이 만들어 내는 URL을 책임진다.

이것들을 GitOps에 맞춰 정리하고 나니 개별 앱마다 예외 설정을 덧대기보다는 **서비스를 노출하는 절차 자체를 하나의 흐름으로 볼 수 있게 됐다.** 다음에 문제가 생겨도 어느 경계부터 확인해야 할지 설명하기가 쉬워졌다는 점에서 의미가 컸다.

**함께 읽을 기록:** [Traefik·MetalLB와 기존 TLS 장애](/projects/rokaf-networking-and-tls/) · [폐쇄망 GitOps 배포](/projects/rokaf-offline-gitops-delivery/) · [Outline 인증과 WebSocket 문제](/projects/rokaf-internal-app-auth-and-tls/) · [On-Premises K3s 플랫폼 전체 구성](/projects/independent-on-premises-k3s-platform-engineering/).

**관련 문서:** [cert-manager Certificate](https://cert-manager.io/docs/usage/certificate/) · [Traefik IngressRoute](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/crd/http/ingressroute/) · [Traefik RedirectScheme](https://doc.traefik.io/traefik/middlewares/http/redirectscheme/).

*문서에 나온 도메인·VIP·CA 식별자·Namespace·Manifest는 공개용 예시다. 그림 역시 실제 내부망을 캡처한 것이 아니라 설명을 위해 새로 그린 벡터 도식이다.*
