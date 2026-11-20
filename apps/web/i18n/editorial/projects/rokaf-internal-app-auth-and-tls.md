Outline는 처음부터 아예 열리지 않는 서비스가 아니었다. 브라우저에서 위키 화면은 볼 수 있었다. 그런데 문서를 편집하다 보면 갑자기 입력이 먹지 않았고, 분명 올렸다고 생각한 이미지가 새로고침하면 사라지는 PC도 있었다. 며칠 뒤에는 GitLab으로 로그인하는 과정이 막혔다.

그때는 모두 같은 서비스에서 벌어진 일이니 설정 하나가 잘못된 것이 아닐까 생각하기 쉬웠다. 하지만 다시 기록을 보면 문제가 생긴 곳이 매번 달랐다. 사용자의 브라우저와 Outline 사이, Outline 서버와 GitLab 사이, 편집 화면의 WebSocket 연결, 그리고 이미지 파일을 가져오는 경로가 각각 따로 움직이고 있었다.

이 글은 2026년 초 폐쇄망 환경에서 Outline을 운영하며 추적했던 문제를 정리한 것이다. 실제로 고친 부분도 있었지만, 끝까지 원인을 확정하지 못한 부분도 있었다. 그 차이를 남겨두고 싶었다.

## Outline WebSocket 편집 연결

2월 3일, Nginx를 통해 Outline에 접근했을 때 실시간 연결이 제대로 만들어지지 않았다. 브라우저에서는 WebSocket 요청이 HTTP `400`으로 끝나는 것이 보였다.

Outline은 페이지를 보여주는 데 필요한 일반 HTTP 요청 외에도 실시간 공동 편집을 위한 연결을 사용한다. 브라우저에서 문서 내용을 읽었다고 해서, 편집 내용을 실시간으로 주고받는 경로까지 살아 있다는 뜻은 아니다.

당시에는 Nginx의 WebSocket 처리를 점검했다. 필요할 때 HTTP/1.1을 사용하도록 하고, `Upgrade`와 `Connection` 헤더를 전달하도록 설정했다. `/realtime`로 들어오는 요청도 확인했으며, 지속적인 연결에 영향을 줄 수 있는 Buffering과 Timeout 설정도 검토했다.

설정을 바꾼 뒤에는 응답이 **`101 Switching Protocols`**로 바뀌었다. 이 숫자는 이전에 보던 `400`과 성격이 다르다. 서버가 WebSocket으로 프로토콜을 전환하는 요청을 받아들였다는 뜻이기 때문이다.

처음에는 이 정도면 편집 문제도 해결됐다고 생각했다. 하지만 곧 그 판단이 너무 빨랐다는 걸 알았다. `101`은 연결이 만들어진 사실을 알려줄 뿐, 모든 PC에서 모든 편집 결과가 저장됐다는 것까지 확인해주지는 않는다.

## 같은 위키인데 PC마다 다르게 움직였다

일부 Windows PC에서는 여전히 문서 수정이 간헐적으로 멈췄고, 이미지를 올려도 새로고침하면 사라지는 현상이 있었다. 다른 PC에서는 재현되지 않으니 서버 전체가 항상 고장 난 것도 아니었다.

문제가 발생하는 브라우저에서 개발자 도구를 확인했다. 인증서 관련 메시지가 있었고, 해당 인증서를 PC에 설치하자 그쪽 경고는 없어졌다. 하지만 이미지 요청에서는 `ERR_NAME_NOT_RESOLVED`나 `ERR_BLOCKED_BY_ORB` 같은 오류가 남았다. Nginx 접근 로그에서도 HTTP `401`이 보였다.

여기서부터는 오류를 한 덩어리로 묶을 수 없었다.

`ERR_NAME_NOT_RESOLVED`는 브라우저가 접근하려는 주소의 이름을 찾지 못했다는 뜻이다. 위키 메인 화면을 열 수 있는지와는 별개의 문제다. 이미지 URL에 다른 호스트 이름이 들어 있다면, 바로 그 이름이 해당 PC에서 해석되는지 확인해야 한다.

인증서 오류는 다른 층위다. 브라우저가 연결하려는 주소에 대해 서버가 제시한 인증서를 신뢰하는지, 인증서의 이름이 그 주소와 일치하는지가 중요하다. 인증서를 설치했다고 해서 존재하지 않는 DNS 이름을 찾을 수 있게 되는 것은 아니다.

`401`은 HTTP 요청이 인증·인가 단계에서 거부됐다는 결과다. 세션이나 Cookie가 원인일 수도 있지만 로그 한 줄만으로 어느 값이 잘못됐는지는 확정할 수 없었다.

`ERR_BLOCKED_BY_ORB`도 브라우저가 응답을 차단했다는 단서일 뿐이다. 이것만 보고 MinIO에 데이터가 없다고 말하거나 WebSocket이 다시 고장 났다고 결론 내릴 수는 없다.

한 페이지에서 이미지를 보여주는 데에는 위키 화면의 주소와 다른 파일 URL이 사용될 수 있다. 저장소가 S3 호환 API를 사용한다면 파일을 받아오는 요청의 Host, TLS, Origin, 권한이 위키 화면과 다를 수도 있다. 이 가능성은 Outline의 일반적인 저장소 구조를 이해하기 위한 설명이지, 당시 문제가 특정 MinIO 설정 하나 때문이라고 증명한 자료는 아니다.

결국 **WebSocket의 `101`은 확인했고, 일부 PC의 인증서 경고도 해결했지만, 모든 PC에서 편집과 이미지 저장이 완전히 정상화됐다는 근거는 남아 있지 않다.**

{{figure /figures/journals/outline-client-boundaries.svg | 브라우저 화면, WebSocket, 파일 URL, Outline 서버의 GitLab 요청은 서로 다른 조건에서 성공하거나 실패할 수 있다. 당시에 확인한 상태와 아직 원인이 열려 있는 상태를 구분했다.}}

## GitLab OAuth Userinfo Timeout

2월 23일에는 다른 문제가 발생했다. GitLab을 통해 Outline에 로그인하는 과정에서 `Bad Gateway`가 나타났고, 서버 로그에는 `ValidateSSOAccessTask`와 함께 `/oauth/userinfo` 요청의 `connect ETIMEDOUT`이 보였다.

처음에는 특정 사용자에게만 나타나는 문제처럼 보였다. 계정이나 권한이 잘못된 것은 아닐까 하는 생각도 들었다. 그런데 이후 다른 사용자에게서도 실패가 나타났고, 여러 서버에서 GitLab의 HTTPS 주소에 직접 접근하는 테스트도 실패했다.

그러면 확인해야 할 범위가 달라진다. 특정 계정 하나의 권한보다 먼저, **Outline이 GitLab의 인증 관련 Endpoint에 실제로 도달할 수 있는지** 확인해야 했다.

OAuth 로그인은 화면에서 버튼을 누르고 GitLab에 다녀오는 것으로 끝나지 않는다. 브라우저가 GitLab의 인증 화면으로 이동한 뒤 Outline의 Callback으로 돌아오는 과정도 있고, Outline 서버가 직접 GitLab에 Token이나 사용자 정보를 요청하는 과정도 있다.

브라우저에서 GitLab 로그인 페이지가 열린다고 해서 Outline Pod에서도 같은 서버에 접근할 수 있는 것은 아니다. 요청을 보내는 주체가 다르기 때문이다.

{{figure /figures/journals/outline-oidc-request-sequence.svg | 브라우저가 이동하는 인증 화면 경로와 Outline Backend가 직접 요청하는 Token·Userinfo 경로를 분리했다. 실제로 관측했던 Timeout과 이후 별도로 발생한 Callback 오류도 서로 다른 위치에 놓았다.}}

`ETIMEDOUT`은 정해진 시간 안에 연결이 완료되지 않았다는 뜻이다. 인증 정보가 틀렸거나 OAuth Client Secret이 만료됐다는 판단과는 다르다. 연결 자체가 성립하지 않았다면 사용자 정보의 내용이나 권한을 검사하기도 전에 요청이 실패했을 수 있다.

당시 인증 서비스 관련 조사에서 `EAI_AGAIN`처럼 이름 해석 실패를 나타내는 메시지도 본 적이 있다. 이것 역시 연결 Timeout과 똑같은 단계는 아니다. DNS 조회가 실패하는 경우와, 주소는 정해졌지만 연결이 끝내 완료되지 않는 경우를 구분해야 했다.

여러 서버에서도 접근에 실패했다는 관측은 문제를 특정 Outline Pod 밖으로 넓혀 볼 근거가 됐다. 하지만 어느 네트워크 장비나 경로가 정확한 원인이었는지, 이후 모든 사용자의 로그인이 정상화됐는지까지 입증한 최종 자료는 없다. 그 부분은 확인되지 않은 결과로 남겨두는 편이 맞다.

## 공개 접속 주소를 바꾸니 또 다른 오류가 나왔다

몇 달 뒤인 6월에는 Outline의 외부 접속 주소를 변경하면서 OIDC Callback 문제를 만났다. GitLab이 **`The redirect URI included is not valid`**라고 응답했다.

2월의 `ETIMEDOUT`과는 다른 종류의 실패였다. 이번에는 요청을 보내지 못한 문제가 아니라, 인증 제공자가 전달된 Redirect URI를 유효하지 않다고 판단한 것이다.

Outline의 OIDC Callback은 `/auth/oidc.callback` 형태다. 외부 주소를 바꾸면서 Scheme, Host, Port 중 하나라도 달라졌다면 Outline이 요청에 넣는 Callback 주소와 GitLab에 등록된 주소도 다시 대조해야 한다.

당시 새로 사용하려던 주소는 기록에서 확인되지만, 군 내부 접근 주소이므로 여기에는 옮기지 않았다. 중요한 것은 주소 자체가 아니라 **인증 제공자가 기억하는 Callback 설정과 애플리케이션이 실제로 보내는 Callback 주소가 하나의 쌍을 이룬다**는 점이었다.

주소 변경 뒤에는 브라우저가 특정 이름을 찾지 못하는 문제도 함께 검토했다. 하지만 그 원인이 기존 GitLab 연결 Timeout과 같았다거나, Callback 문제까지 모두 해결됐다고 말할 자료는 없다.

Outline 문서에는 OIDC Provider를 자동으로 탐지하는 방식과 `OIDC_AUTH_URI`, `OIDC_TOKEN_URI`, `OIDC_USERINFO_URI`를 직접 지정하는 방식이 모두 소개돼 있다. 이 변수들이 어디로 요청을 보내는지 알려주는 것은 사실이지만, 현재 문서의 옵션을 내가 당시 전부 적용했다는 뜻은 아니다.

## HTTP 상태 하나가 다른 계층의 성공을 대신하지는 않는다

이번에는 성공과 실패를 다음처럼 나누어 보는 편이 이해하기 쉬웠다.

| 그때 확인한 단서 | 말할 수 있는 것 | 아직 말할 수 없는 것 |
| --- | --- | --- |
| 위키 화면 표시 | 메인 화면을 받을 수 있음 | 로그인, 편집, 파일 접근의 정상 동작 |
| 실시간 연결 `400`에서 `101` | WebSocket Upgrade 성공 | 모든 PC의 문서 저장 성공 |
| 클라이언트 인증서 설치 후 경고 해소 | 해당 인증서의 신뢰 문제 개선 | 모든 이미지·세션 경로 해결 |
| 이미지 `ERR_NAME_NOT_RESOLVED` | 브라우저에서 해당 URL 이름을 해석하지 못함 | 저장소의 실제 파일 유실 |
| Nginx `401` | 요청이 인증·인가 경계에서 거부됨 | 어느 Cookie·Session이 원인인지 |
| GitLab `/oauth/userinfo`의 `ETIMEDOUT` | Outline에서 GitLab으로 가는 연결이 완료되지 않음 | 특정 계정·권한 오류, 단일 네트워크 원인 |
| Callback URI 오류 | 등록한 주소와 요청한 주소의 정합성 문제를 검토해야 함 | 이전 Timeout과 같은 장애라는 결론 |

브라우저가 Outline을 신뢰하는 문제, Outline 서버가 GitLab의 인증서를 신뢰하는 문제, 이미지 주소를 브라우저가 해석하는 문제는 각각 다른 자리에서 확인해야 했다.

특히 **위키가 열린다는 사실 하나로 나머지 경로까지 정상이라고 생각했던 것**이 여러 문제를 한 번에 해결하려 들게 만든 원인이었다.

## 브라우저·서버 요청별 추가 검증

같은 문제가 다시 나타나면 어떤 설정부터 바꿔야 할지 목록부터 만들지는 않을 것 같다. 먼저 실패한 요청을 한 건 집어 들고 시작할 것이다.

브라우저가 보낸 요청인지, Outline이 GitLab에 보낸 요청인지. 요청한 주소를 그 주체가 해석할 수 있는지. TLS 연결은 성립했는지. HTTP 응답이 있다면 어느 서버가 반환했는지. 그리고 그 결과가 실제 문서 저장이나 로그인까지 이어지는지.

WebSocket은 `101`을 확인한 뒤에도 문제가 나타났던 PC에서 문서를 수정하고 새로고침해봐야 한다. 이미지는 개발자 도구에 기록된 실제 URL을 확인하고 해당 PC에서 열리는지 봐야 한다. OAuth는 Outline 프로세스가 실행되는 환경에서 GitLab Endpoint로 접속되는지 확인하고, Callback은 인증 제공자에 등록된 주소와 실제 요청의 주소를 비교해야 한다.

Outline의 실시간 편집 경로를 수정해 **WebSocket `101 Switching Protocols` 응답을 확인**했고, 일부 PC의 인증서 신뢰 문제도 해결했다. GitLab `ETIMEDOUT`과 OAuth Callback, 브라우저별 이미지·저장 오류는 별도 요청 경로에서 나타났으므로 각각의 재현·검증이 필요한 상태로 남겼다.

## 참고 문서

- [Outline — OIDC 구성](https://docs.getoutline.com/s/hosting/doc/oidc-8CPBm6uC0I)
- [Outline — Self-hosting 문제 해결](https://docs.getoutline.com/s/hosting/doc/troubleshooting-HXckrzCqDJ)
- [Outline — Nginx Reverse Proxy](https://docs.getoutline.com/s/hosting/doc/nginx-6htaRboR57)
- [Outline — 파일 저장소](https://docs.getoutline.com/s/hosting/doc/file-storage-N4M0T6Ypu7)
- [Nginx — WebSocket Proxying](https://nginx.org/en/docs/http/websocket.html)
- [GitLab — OAuth Provider 설정](https://docs.gitlab.com/integration/oauth_provider/)
