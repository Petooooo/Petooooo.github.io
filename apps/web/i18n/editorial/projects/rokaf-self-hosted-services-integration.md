언젠가부터 실행 중인 Pod의 개수가 그다지 중요한 숫자로 보이지 않기 시작했다. 채팅방은 잘 열리는데 관리자가 인증 메일을 받지 못해 설정을 변경할 수 없었다. Nexus 관리 화면은 보이는데 Docker 이미지는 Push되지 않았다. MinIO의 주소에 접속할 수 있어도 그 주소를 사용하는 애플리케이션에서는 파일 업로드가 실패했다.

폐쇄망 K3s 플랫폼에 여러 서비스를 올리면서 겪었던 일들이다. Rocket.Chat, GitLab, Outline, Plane, Nexus처럼 서로 다른 목적으로 만들어진 애플리케이션을 한 클러스터에서 운영하려면, 컨테이너를 실행하는 것만으로 끝나지 않았다. 각 애플리케이션은 인증, 데이터베이스, 파일 저장소, 네트워크, 메일 서버와 서로 다른 방식으로 연결돼 있었다.

이번에는 한 서비스의 장애를 처음부터 끝까지 따라가는 대신, **서비스를 연결할 때 무엇이 실제로 준비됐다고 말할 수 있는지**에 대한 고민을 정리하고 싶다. 앞서 별도로 쓴 Rocket.Chat 파일 이전이나 Plane·Outline 라우팅 장애를 그대로 반복하지 않고, 그 사례들 사이에서 공통으로 드러났던 운영 판단을 살펴봤다.

Penpot과 Uptime Kuma처럼 이름만 확인되고 구체적인 장애·검증 기록이 부족한 서비스는 이번 글에서 억지로 다루지 않았다. 실제 주소와 포트, 계정, 인증서 정보, 노드 배치 역시 공개하지 않는다.

## 채팅은 되는데 관리자 인증 메일이 오지 않았다

Rocket.Chat이 사용자에게 메시지를 전달하는 것과 SMTP로 이메일을 보내는 것은 별개의 기능이다. 처음에는 이메일이 조금 불편한 부가 기능 정도라고 생각할 수도 있다. 하지만 OAuth 관련 설정을 활성화한 뒤 관리 작업을 하려니 이메일로 전달되는 인증 코드가 필요했다. 메일이 오지 않으면 관리자 화면에 접근할 수 있어도 다음 단계를 진행하지 못하는 상황이었다.

처음 마주친 오류는 이랬다.

`You have not provided a mail URL`

Rocket.Chat에는 `MAIL_URL`을 설정할 수 있다. 이 값을 넣었다고 생각했는데 오류가 나니 가장 먼저 환경변수가 애플리케이션에 전달됐는지를 의심했다.

여기서 한 차례 혼란이 있었다. 설정 파일에는 값을 추가했지만 내가 확인한 환경에서는 보이지 않았다. 그래서 Helm이 값을 제대로 전달했는지, 실제로 실행 중인 Pod에서 어떤 값을 읽고 있는지 확인하는 방향으로 조사했다.

나중에는 Node 프로세스에서 직접 `process.env.MAIL_URL`을 확인했다. 그때는 SMTP URL이 출력됐고, 인증 정보를 포함한 형식으로 바꿔 시험해도 프로세스에서 값을 볼 수 있었다.

그렇다고 SMTP 문제가 해결됐다고 말할 수는 없다.

**설정이 프로세스에 존재한다는 사실**과 **그 설정으로 인증 메일이 실제 수신자에게 도착했다는 사실**은 전혀 다르다. 메일 서버까지 TCP 연결이 가능한지, SMTP 인증이 받아들여지는지, 서버가 발송을 승인하는지, 최종적으로 사용자가 메일을 받는지 모두 따로 확인해야 한다.

당시 로그와 점검 결과가 증명한 것은 적어도 한 시점에 Node 런타임이 `MAIL_URL`을 읽고 있었다는 것이다. 관리자의 인증 코드가 도착하고 차단됐던 작업을 다시 마쳤다는 완전한 검증 결과는 남아 있지 않다.

{{figure /figures/journals/service-integration-config-evidence.svg | Rocket.Chat의 SMTP 설정을 Helm 값, 실제 Deployment, Node 런타임, SMTP 통신, 사용자 인증 메일이라는 서로 다른 검증 지점으로 나누었다. 프로세스에서 설정이 보인다는 사실만으로 발송 성공을 의미하지는 않는다.}}

이런 문제를 겪고 나니 SMTP를 ‘알림 옵션’ 정도로만 분류할 수 없었다. 인증 코드가 필수인 작업에서는 메일 서버가 관리 기능의 실질적인 의존성이 된다. 평소에는 멀쩡하던 시스템이 특정 작업에서만 막힐 수 있는 이유다.

## Helm values에 썼다고 Pod에 적용되는 것은 아니다

메일 설정을 점검하면서 Helm Chart의 값이 실제로 어떻게 소비되는지도 다시 살펴봤다.

특히 `extraEnv`와 `extraEnvVars`의 차이를 확인했던 일이 기억난다. 같은 Release 안에서도 애플리케이션 Chart와 PostgreSQL Subchart가 환경변수를 받는 필드 이름이 달랐다. 당시 애플리케이션에는 `extraEnv`를 써야 했는데, `extraEnvVars`는 PostgreSQL의 `primary` 설정 쪽에서 사용하는 값이었다.

`values.yaml`이 YAML 문법에 맞는다는 사실은 충분하지 않다. Chart가 그 이름을 실제로 읽지 않으면 파일에는 설정이 있지만 생성된 Deployment에는 없을 수 있다.

그래서 설정값을 바꾼 뒤에는 어떤 순서로 확인해야 하는지 생각을 바꿨다.

먼저 Helm에서 렌더링한 매니페스트에 기대했던 `env` 항목이 생겼는지 봐야 한다. Secret을 쓰는 경우에는 `valueFrom.secretKeyRef`가 올바른 Secret과 Key를 참조해야 한다. 그다음 실제 Deployment와 Pod에 반영됐는지 확인하고, 마지막으로 애플리케이션 프로세스가 그 값을 사용하는지 확인해야 한다.

이 단계들은 서로를 대신하지 못한다. Secret이 있어도 Pod에서 참조하지 않으면 소용이 없다. Pod의 환경변수가 맞아도 SMTP 서버에서 인증을 거부할 수 있다. 메일 발송에 성공했더라도 수신자에게 도착하지 않으면 인증 작업은 끝나지 않는다.

보안상으로도 고민이 있었다. SMTP URL에 사용자 이름과 암호가 들어갈 수 있기 때문에 운영 설정 파일이나 공개된 Helm Values에 그대로 넣고 싶지 않았다. Kubernetes Secret을 통해 값을 참조하는 방향을 검토했다. 다만 Secret을 사용한다는 이유만으로 자동으로 모든 접근이 안전해지는 것은 아니다. Secret 조회 권한과 로그 노출, 실제 Pod의 값 전달까지 함께 확인해야 한다.

나중에는 메일 알림이 지나치게 많이 발송되는 문제도 겪었다. 메일이 아예 오지 않는 문제와는 반대처럼 보이지만, 애플리케이션 입장에서는 모두 SMTP 의존성과 연결되는 사용자 경험이다. Offline Email Notification 같은 설정을 살펴볼 이유는 있었지만, 특정 옵션 하나가 원인이었고 그것을 꺼서 해결했다는 최종 검증 자료는 확인되지 않는다.

## 같은 MinIO를 쓴다고 파일 접근 방식까지 같지는 않았다

여러 애플리케이션이 공통으로 MinIO를 사용하면 관리하기 편하다고 생각했다. 실제로 객체 저장소를 공유 인프라로 운영하는 것은 충분히 의미 있는 선택이었다. 하지만 파일을 저장하고 다시 찾는 방법까지 MinIO가 통일해주는 것은 아니었다.

Rocket.Chat에서 예전 첨부파일을 GridFS에서 MinIO로 옮길 때가 좋은 예다. MinIO에 새 파일이 정상적으로 올라가더라도, 과거 메시지가 참조하는 Upload ID와 S3 Key가 맞지 않으면 오래된 이미지는 열리지 않았다. 그 문제는 [GridFS에서 MinIO로 옮긴 첨부파일의 참조 관계](/projects/rokaf-chat-attachments-object-storage/)에서 따로 다뤘다.

다른 경우에는 Traefik의 `ServersTransport`가 문제였다. 참조하는 IngressRoute와 리소스의 Namespace가 맞지 않아 처음에는 Transport를 찾지 못했다. 리소스를 MinIO Namespace로 옮기자 **Transport를 찾지 못한다는 오류는 없어졌다.**

하지만 파일 업로드에서는 여전히 Self-signed Certificate 관련 `400` 오류가 나타났다.

여기서 중요한 차이가 있었다. Traefik이 설정 리소스를 찾는 것과 실제 통신 상대의 인증서를 신뢰하는 것은 다르다. Traefik의 Upstream TLS 설정을 고쳤다고 해서 브라우저나 애플리케이션 프로세스가 사용하는 인증서 신뢰 저장소까지 바뀌는 것은 아니다.

어느 프로그램이 TLS 연결을 만들고 있는지부터 구분해야 했다. 브라우저가 직접 파일 URL에 접근할 수도 있고, 애플리케이션 Backend가 MinIO에 요청할 수도 있다. 이들은 같은 주소를 사용하더라도 이름 해석과 신뢰 체계가 서로 다를 수 있다.

그러므로 이 사례에서 확실히 해결했다고 말할 수 있는 것은 **ServersTransport 참조 오류**다. 파일 업로드의 최종 성공까지 검증했다는 뜻은 아니다.

## Nexus 관리 화면과 Docker Registry는 다른 입구였다

Nexus도 비슷했다. 관리 UI에 접속된다고 해서 Docker Registry가 준비된 것은 아니었다.

Nexus는 Repository를 관리하는 웹 UI와 Docker 이미지가 Push·Pull되는 API를 각각 다른 Connector와 Port로 제공할 수 있다. Kubernetes 위에서는 이 차이를 Service Port, Target Port, Ingress와 TLS 설정에 맞게 연결해야 했다.

당시에는 관리 화면과 Docker API를 서로 다른 외부 포트로 노출하는 구성을 검토했고, 가능하면 특정 노드에서만 접근을 허용하고 싶었다. 단순히 포트 하나를 더 여는 문제가 아니라, 사용자가 웹에서 확인하는 주소와 Docker Client가 Registry로 사용하는 주소를 다르게 생각해야 한다는 뜻이었다.

실제로 Docker 이미지를 옮기는 과정에서는 `x509` 오류와 `404`를 만났다. 이미지를 적절한 이름으로 Tag한 뒤 지정한 Registry로 Push하고, 다시 다른 Client에서 Pull하는 과정을 확인해야 했다. 관리 UI가 정상으로 뜨는 것으로 대신할 수 없는 테스트였다.

Nexus의 Blob Storage를 MinIO 같은 S3 호환 저장소에 놓는 방안도 검토했다. 객체 데이터가 저장되는 계층과 Nexus 자체의 메타데이터, Docker Registry 프로토콜은 다시 서로 다른 책임을 맡는다.

특히 이미지 Registry는 다른 서비스와 달리 자기 자신의 복구에도 관여할 수 있다. Nexus가 멈췄는데 Kubernetes가 Nexus 이미지를 오직 그 Nexus에서만 Pull하도록 구성돼 있다면, 장애가 생겼을 때 필요한 이미지를 가져오는 경로부터 막힐 수 있다. 이전에 [폐쇄망 이미지 공급과 GitOps](/projects/rokaf-offline-gitops-delivery/)를 정리하면서 독립적인 초기 이미지 공급 경로를 고민했던 이유다.

이때 검토한 설계가 실제 전체 장애 복구 훈련을 통과했다거나 MinIO를 사용하면 Nexus가 자동으로 HA가 된다는 결론은 내리지 않았다. UI, Docker API, Blob Store, Bootstrap 이미지는 나누어 검증해야 할 영역이었다.

## 서비스가 ‘정상’이라는 말은 너무 넓었다

다른 서비스에서도 비슷한 경우를 봤다.

Plane에서는 첫 화면이 나타났지만 API 경로가 잘못돼 계정 등록이 막혔다. 라우팅을 수정한 뒤 계정과 Workspace 생성은 성공했고, 이후 Pages의 실시간 연결은 `/live`를 따로 설정해 복구했다. 두 기능 모두 같은 서비스의 일부지만 서로 다른 요청을 사용했다. [Plane 기록](/projects/rokaf-plane-ce-bootstrap-routing/).

Outline에서는 WebSocket 연결이 `101`로 전환되는 것을 확인했지만, GitLab의 사용자 정보 요청에서는 `ETIMEDOUT`이 나왔고 일부 PC에서는 이미지와 인증서 관련 문제가 남았다. [Outline 기록](/projects/rokaf-internal-app-auth-and-tls/).

MongoDB 역시 서비스 하나가 존재한다고 애플리케이션에서 곧바로 사용할 수 있는 것은 아니었다. Replica Set 멤버 이름을 애플리케이션 Pod에서 해석할 수 있는지, 필요한 경우 Primary를 찾을 수 있는지, 데이터를 읽고 쓸 수 있는지를 따로 확인해야 했다. [데이터베이스 고가용성 기록](/projects/rokaf-database-ha-and-langfuse-migrations/)에 그 과정이 남아 있다.

이 사례들이 모두 같은 날 발생한 하나의 장애는 아니다. 서로 다른 시점에 겪은 문제를 돌이켜보니, **Pod Ready 상태와 실제 기능별 준비 상태는 별개**라는 공통점이 보였다.

{{figure /figures/journals/service-integration-evidence-matrix.svg | Rocket.Chat·Nexus·Plane·Outline을 서비스 이름과 인증·메일·스토리지·접근 경로 같은 기능별 검증 기준으로 나누었다. 성공, 실패, 설계 검토, 미검증을 같은 상태로 취급하지 않기 위한 표다.}}

이 그림에서 빈칸은 실패가 아니라 확인한 근거가 없다는 뜻이다. 특정 기능이 실제로 동작하지 않았다고 관측한 것과, 아직 검사하지 못한 것을 같은 표시로 다루면 오히려 기록이 부정확해진다.

## 이제는 서비스마다 마지막 사용자 동작을 정한다

새로운 서비스를 설치한다면 Helm Release가 성공했다는 사실과 Pod의 Ready 상태를 먼저 확인하겠지만, 거기에서 끝내지는 않을 것 같다.

로그인을 제공하는 서비스라면 실제 사용자로 들어가 필요한 역할에 접근되는지 확인해야 한다. 데이터베이스를 사용하는 애플리케이션이라면 데이터를 바꾸고 새로고침하거나 재시작한 뒤에도 같은 상태가 남는지 확인해야 한다. 객체 저장소를 쓴다면 새 파일을 업로드하고 다시 열어봐야 하며, 과거 파일을 옮기는 작업이라면 이전 메시지에서 같은 파일을 찾을 수 있는지도 봐야 한다.

메일이 관리 기능에 사용된다면 실제 검증 코드가 도착해 입력할 수 있어야 한다. Docker Registry라면 관리 화면이 아니라 Docker Client가 Push와 Pull을 성공해야 한다. 장애를 조사해야 하는 경우라면 실제 요청이 어느 경로에서 실패했는지 로그와 지표를 연결할 수 있어야 한다.

이것은 앞으로 적용하고 싶은 검증 기준이지, 당시 배포한 모든 서비스가 이미 모든 검사를 통과했다는 뜻은 아니다.

Kubernetes는 컨테이너를 배치하고 Service를 만들고 장애 시 Pod를 다시 실행할 수 있게 해줬다. 하지만 Rocket.Chat의 인증 메일이 반드시 도착해야 한다는 사실이나, 브라우저에서 보는 파일 주소가 다른 인증서를 사용한다는 사실까지 알지는 못한다.

서비스 통합 검증은 기능마다 달랐다. 실제 인증 메일 전송, 브라우저의 첨부파일 내려받기, Docker Registry 인증과 Push를 각각 테스트해야 했다. Pod가 Ready라는 사실은 이런 사용자 동작의 성공 여부를 대신하지 못했다.

## 참고 문서

- [Rocket.Chat — SMTP 설정](https://docs.rocket.chat/docs/configure-email)
- [Rocket.Chat — Kubernetes 배포 설정](https://docs.rocket.chat/docs/deploy-with-kubernetes)
- [Helm — Chart Values와 Template](https://helm.sh/docs/topics/charts/)
- [Sonatype — Docker Repository Connector](https://support.sonatype.com/hc/en-us/articles/115013153887-Docker-Repository-Configuration-and-Client-Connection)
- [Sonatype — Blob Store](https://help.sonatype.com/en/blob-stores.html)