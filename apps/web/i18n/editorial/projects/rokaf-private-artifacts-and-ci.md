GitLab에서 코드를 빌드하면 Kaniko가 컨테이너 이미지를 만들고, Nexus에 저장했다. Kubernetes에서 서비스를 배포할 때도 내부 Registry를 사용했다. 외부 인터넷에 의존하지 않고 빌드와 배포를 이어갈 수 있는 길을 만든 셈이었다.

그런데 나중에 Nexus와 CoreDNS가 함께 장애를 겪자 일부 Pod가 재시작에 필요한 이미지를 가져오지 못했다. `IfNotPresent`로 설정했으니 이전에 받은 이미지를 사용할 거라고 생각했지만, 실제로 Pod가 올라가는 노드에 이미지가 남아 있지 않으면 결국 Registry로 돌아가야 했다. 문제는 그 Registry도 멈춰 있다는 것이었다.

돌아보면 이런 식으로 기대했던 동작과 실제 실행 경로가 어긋난 적이 여러 번 있었다. `/kaniko/executor`가 없다고 나오는데 의도한 이미지에서는 실행 파일이 보였고, Nexus 관리 화면은 열리는데 Docker Client에서는 `x509`나 `404`가 나타났다. 처음에는 오류마다 설정을 고치느라 바빴다. 기록을 다시 읽고 나서야 공통된 질문이 보였다.

**지금 실패한 작업을 시작하려면, 먼저 무엇이 준비돼 있어야 할까.**

2026년 초 폐쇄망 K3s에서 GitLab Runner·Kaniko·Nexus를 운영하며 겪은 문제들이다. 서로 다른 날짜의 사건이므로 한 번에 해결한 이야기로 묶지는 않았다. 실제 내부 서버 주소, 포트와 계정, 노드 이름과 배치 정보는 제외했다.

## Kaniko Kubernetes Executor 실행 환경

처음에는 Kubernetes Executor를 사용하는 GitLab Runner에서 Kaniko를 실행하면 자연스럽게 Docker 이미지를 만들 수 있을 거라고 생각했다. Docker Daemon을 별도로 띄우지 않아도 되기 때문이다.

하지만 1월에 처음 만난 오류는 이미지 빌드까지 가지도 못했다.

`exec: "sh": executable file not found in $PATH`

Kaniko의 기본 Executor 이미지는 일반적인 Linux 작업용 이미지처럼 셸을 제공하지 않는다. Runner가 CI 스크립트를 실행하는 방식과 이미지에 들어 있는 실행 환경이 맞아야 했는데, 그 전제가 어긋난 것이다.

이때 Nexus 권한이나 Dockerfile을 바꿔도 문제는 해결되지 않는다. 아예 스크립트를 실행하지 못하고 있었기 때문이다.

그래서 셸을 제공하는 작은 Wrapper 이미지 안에 Kaniko의 `/kaniko` 실행 파일들을 포함하도록 구성했다. 이전에 실패하던 CI Job은 이 변경 뒤 실제로 실행되기 시작했다. 여기까지는 분명하게 고친 부분이다.

바로 다음에는 Docker 인증 설정을 복사할 때 `cp`가 빈 경로를 받는 오류가 나왔다. Job에 필요한 CI File 변수가 전달되지 않은 것이었다. 실행 파일이 준비됐다는 사실과 Registry의 인증 정보를 올바르게 받는다는 사실은 또 달랐다.

## Kaniko Wrapper 이미지와 실행 경로

2월에는 서버 재시작 이후 `/kaniko/executor: No such file or directory`가 다시 나타났다. 처음과 똑같은 오류로 보였다.

그런데 의도했던 이미지를 직접 열어 확인하면 `/kaniko/executor`가 존재했다. 그렇다면 정말 이미지에 파일이 없는 문제인지, 아니면 그 이미지를 사용하지 않는 환경에서 스크립트가 실행되는 것인지부터 다시 확인해야 했다.

3월에 조사한 실행 환경에서는 예상했던 Kubernetes Job 컨테이너와 다른 Hostname과 파일시스템이 나타났다. Runner 식별자도 내가 의도한 Runner와 맞지 않는 정황이 있었다. Helm Values에서 `runners.tags`와 `runUntagged`를 명확하게 고정하지 않았다는 점도 확인했다.

같은 `.gitlab-ci.yml`이더라도 어떤 Runner가 Job을 가져가느냐에 따라 전혀 다른 셸과 파일시스템에서 실행될 수 있다. 그래서 이 시점부터는 오류를 읽기 전에 **어느 Runner가 어떤 Executor로 실제 명령을 실행했는지**를 확인하게 됐다.

이는 Runner 선택이 잘못됐다는 강한 단서였지만, 모든 이후 Job이 올바른 Runner로 고정됐다는 전수 검증 자료까지 남아 있지는 않다. **1월에 Wrapper로 해결한 셸 문제**와 **2~3월에 다시 나타난 실행 환경 불일치**를 같은 근본 원인이라고 쓰지 않는 이유다.

## x509 오류가 Kaniko에서 난다는 보장은 없었다

Nexus를 HTTPS로 사용하면서 사설 인증서 문제도 여러 차례 만났다. 실제로 Builder 이미지에 적절한 CA를 포함해 Kaniko의 Registry Push 경로에서 발생한 인증서 문제를 해결한 경우가 있었다.

하지만 다른 실패는 Kaniko가 시작되기 전이었다. Kubernetes가 **CI Job 이미지를 Pull하는 단계**에서 `x509` 오류가 나타난 것이다.

아직 실행되지도 않은 Kaniko 이미지 안에 CA를 넣는다고 해결할 수는 없다. 그 이미지를 처음 받아오는 주체는 K3s 노드의 Container Runtime이다. 노드가 해당 Registry의 인증서를 신뢰해야 Job 컨테이너가 실행된다.

다른 PC에서 `docker login`이나 `docker pull`을 하는 경우도 별개다. Docker의 Registry별 신뢰 저장소는 K3s Containerd 설정이나 Kaniko 컨테이너의 CA Bundle과 같지 않다.

{{figure /figures/journals/registry-tls-trust-boundaries.svg | CI 이미지 Pull, Kaniko Push, Docker Client 접근은 서로 다른 위치에서 TLS를 검증한다. 어느 하나의 CA 설정이 성공했다고 다른 요청도 정상이라고 말할 수는 없었다.}}

인증서를 생성하는 과정에서는 Java가 중복된 Extension을 허용하지 않는다는 오류도 겪었다. Root CA를 등록하는 것으로 끝나는 일이 아니었다. 어떤 이름이나 IP 주소에 대해 인증서를 발급했는지, 실제 접속 주소가 SAN에 들어 있는지, 인증서 체인을 올바르게 구성했는지를 확인해야 했다.

Docker Registry의 `/v2/` 요청이 `401 Unauthorized`를 반환하면 TLS 연결 이후 인증 단계에 도달했을 가능성이 있다. 반면 `x509: certificate signed by unknown authority`는 HTTP 인증 전에 인증서 검증이 실패한 것이다. 서로 다른 오류를 같은 자격 증명 문제로 취급해서는 안 됐다.

K3s의 `registries.yaml`과 Docker의 Registry별 CA 설정도 이런 차이를 드러낸다. 검증을 통째로 꺼서 당장의 오류를 없애기보다는, **실패한 요청을 누가 만들었는지**부터 좁혀보려고 했다.

## Nexus 웹 화면과 Docker Registry는 다른 입구였다

Helm으로 Nexus를 배포하고 웹 UI에 접속했을 때는 일단 서비스가 준비된 것처럼 느껴졌다. 하지만 관리 UI와 Docker Registry API는 서로 다른 Connector와 Port를 사용할 수 있다.

당시에는 관리 화면과 Docker API의 외부 접속을 나누고, 가능하면 특정 노드에서만 해당 포트를 노출하는 방식도 검토했다. Service Port와 Target Port, TCP 라우팅을 연결한다고 해도 Docker Client가 실제로 `/v2/` API에 도착하는지까지 따로 확인해야 했다.

실제로 `404`를 만났을 때는 Docker Client가 어느 Connector에 접근하는지, 요청 경로가 Nexus에서 어떤 Repository로 해석되는지를 의심해야 했다. `x509`라면 그보다 먼저 TLS 연결을 살펴야 했다. Repository 하나에서는 Push가 되는데 다른 Repository에서는 `401`이 나오는 조사도 있었다.

`401`을 보자마자 비밀번호부터 바꿀 문제는 아니다. 이미 Nexus에는 도달했지만 Token의 Scope나 해당 Repository에 부여된 Push 권한이 맞지 않을 수 있다. 네트워크 접속, 인증, Repository 권한은 서로 다른 단계다.

모든 Connector와 Repository에서 최종적으로 Push·Pull을 성공했다고 증명할 자료까지는 없다. 정확한 검증은 특정 Endpoint에 로그인하고 이미지를 Push한 뒤 Digest를 확인하고, 해당 Client에서 다시 Pull하는 과정이어야 한다.

## MinIO에 Blob Store를 연결하고도 남은 질문

Nexus의 상태는 영속적으로 보존하면서, 이미지 Blob 데이터는 MinIO와 같은 S3 호환 저장소에 둘 수 있을지 고민했다.

Helm에서는 `persistence.enabled`와 Longhorn PVC를 사용하도록 구성했다. Chart가 참조하는 `bashImage` 같은 보조 이미지도 폐쇄망에 준비해야 했다. Nexus 본체 이미지만 가져온다고 설치에 필요한 이미지가 모두 갖춰지는 것은 아니었다.

MinIO S3 Blob Store를 연결할 때는 **Path-style Access**를 활성화했다. 이후 의도한 MinIO Endpoint가 정상적으로 생성되고, Bucket 아래에 Prefix와 Blob Store 이름이 결합된 경로로 객체가 생성되는 것을 직접 확인했다. 적어도 그 경로에서 Nexus가 객체를 저장하고 있다는 사실은 관측한 셈이었다.

하지만 MinIO로 Blob 데이터를 옮긴다고 Nexus 전체가 Stateless가 되지는 않는다. Repository 메타데이터, 내부 DB, 작업 상태와 Connector 구성은 여전히 고려해야 한다. MinIO의 객체가 남아 있어도 Nexus의 메타데이터가 그 객체를 찾지 못하면 이미지를 제공할 수 없다.

성능도 쉽게 단정할 수 없었다. 해당 배치에서는 SSD를 사용할 수 없어 HDD 기반 저장소를 전제로 해야 했다. MinIO가 여러 디스크에 I/O를 분산할 수 있는 반면 네트워크, Erasure Coding과 작은 파일 처리에는 추가 비용도 있다. 실제로 어느 구성이 더 빠른지 확인한 벤치마크는 남아 있지 않다.

**S3 객체 저장 성공, Nexus의 영속 상태 보존, Docker Registry 기능, 장애 복구**를 하나의 성공으로 묶을 수는 없었다.

## Registry 장애 시 복구 이미지 의존성

4월에는 더 근본적인 문제가 드러났다. Nexus와 CoreDNS에 동시에 문제가 생긴 상황에서 일부 Pod가 이미지를 Pull하지 못했다.

`imagePullPolicy: IfNotPresent`가 설정돼 있으면 이미지를 무조건 다시 가져오지는 않는다는 점은 맞다. 하지만 **해당 Pod가 실행되는 노드에 요청한 이미지가 실제로 있어야** 한다. 다른 노드에만 남아 있는 이미지나 예전에 한 번 성공했던 Pull은 새 Pod를 보장하지 않는다.

특히 Nexus도 같은 K3s 클러스터 위에서 실행된다. Nexus를 복구하려면 Nexus 이미지와 그 의존성 이미지가 필요하다. 그 이미지를 오직 멈춰 있는 Nexus에서만 공급받는다면, 복구에 필요한 첫 단계에서 다시 Nexus를 요구하는 순환 의존성이 생긴다. CoreDNS까지 함께 이상하다면 Registry 이름을 해석하는 과정도 영향을 받는다.

{{figure /figures/journals/registry-bootstrap-cycle-cut.svg | Nexus가 다른 서비스와 자기 자신의 이미지 공급원일 때 생기는 순환 의존성을 나타냈다. 독립적인 Bootstrap 이미지 공급은 검토한 설계 방향이지, 전체 복구 테스트를 통과했다는 뜻은 아니다.}}

이 경험 뒤에는 핵심 이미지만이라도 Registry와 독립적으로 보유하는 방법을 살펴봤다. 중요 이미지의 Node-local Preload나 별도의 작은 Bootstrap Registry가 그 후보였다.

그렇다고 두 번째 Registry만 만든다고 해결되는 것도 아니다. 그 Registry도 같은 DNS, 스토리지, K3s 장애 영역에 묶여 있다면 같이 멈출 수 있다. 필요한 것은 Registry 이름의 복제보다 **복구의 출발점이 같은 장애에 묶여 있지 않도록 만드는 것**이었다.

실제로 Nexus와 CoreDNS 장애에서 ImagePull 문제가 나타났다는 사실은 확인된다. 하지만 제안했던 Bootstrap 구조가 모든 동시 장애를 복구했다는 실증 결과는 없다.

## 무엇을 먼저 확인할지가 바뀌었다

이후에는 CI 실패를 한 종류로 취급하지 않게 됐다.

| 나타난 증상 | 먼저 살펴볼 것 | 바로 내릴 수 없는 결론 |
| --- | --- | --- |
| `sh` 실행 불가 | Job 이미지와 셸 지원 여부 | Nexus 권한 오류 |
| `/kaniko/executor` 없음 | 실제 Runner·Executor·파일시스템 | 모든 Kaniko 이미지에 파일이 없음 |
| Job 이미지 Pull 중 `x509` | K3s 노드의 Registry CA | Kaniko 내부 문제 |
| Kaniko Push 중 `x509` | Builder CA와 Endpoint SAN | 다른 노드의 CA까지 해결됨 |
| Docker API `401` | Credential·Token Scope·Repository 권한 | 비밀번호만 잘못됨 |
| Docker API `404` | Connector와 URL 경로 | Nexus 데이터 유실 |
| UI 접속과 S3 저장 성공 | 관리 화면과 Blob Store | Registry Push/Pull 전체 성공 |
| `IfNotPresent`인데 Pull 실패 | 실제 배치 노드의 이미지·DNS·Registry | 클러스터 전체 이미지 캐시 존재 |

같은 소스를 다시 빌드하려면 Git Commit 외에도 정확한 Builder 이미지, 베이스 이미지, 패키지 미러, CA, Registry 권한을 함께 알아야 했다. 완성된 이미지의 Digest가 무엇이고 그 이미지를 어떤 GitOps 배포 설정에서 사용했는지도 별도로 기록해야 한다.

[폐쇄망 GitOps와 Argo CD 기록](/projects/rokaf-offline-gitops-delivery/)에서는 이미지를 만드는 일과 Kubernetes가 원하는 상태로 배포하는 일이 서로 다른 책임이라는 점을 다뤘다.

이후 Nexus와 CoreDNS가 함께 중단됐을 때 일부 Pod는 재시작에 필요한 이미지를 가져오지 못했다. Registry에 도달하지 못하는 상황에서도 복구 가능한 이미지 보관 경로와 노드별 이미지 캐시 범위를 따로 확인해야 했다. 이 문제는 앞선 Kaniko 실행·TLS 장애와 구분해서 남겼다.

## 참고 문서

- [GitLab Runner — Kubernetes Executor](https://docs.gitlab.com/runner/executors/kubernetes/)
- [Kaniko — Executor와 Debug 이미지](https://github.com/GoogleContainerTools/kaniko)
- [K3s — Private Registry와 CA](https://docs.k3s.io/installation/private-registry)
- [K3s — 이미지 반입](https://docs.k3s.io/add-ons/import-images)
- [Sonatype — Docker Repository Connector](https://support.sonatype.com/hc/en-us/articles/115013153887-Docker-Repository-Configuration-and-Client-Connection)
- [Sonatype — Docker Authentication](https://help.sonatype.com/en/docker-authentication.html)
- [Sonatype — Blob Stores](https://help.sonatype.com/en/blob-stores.html)
