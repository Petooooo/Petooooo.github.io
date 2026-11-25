GitLab Runner를 K3s에 붙여 이미지를 빌드하고 Nexus에 올리는 흐름을 만들면서, '권한'이라는 말을 한 가지 뜻으로 쓰기 어렵다는 걸 느꼈다. Runner가 Kubernetes에 작업용 Pod를 만드는 일과 그 안에서 실행된 Kaniko가 Registry에 이미지를 올리는 일은 하나의 CI Job 안에서 이어진다. 하지만 두 요청을 허용하는 곳은 서로 달랐다.

비슷한 차이를 내부 서비스 로그인에서도 마주쳤다. Outline에서 GitLab 계정으로 로그인할 때에는 브라우저뿐 아니라 Outline 서버가 GitLab의 사용자 정보 API에 도달해야 했다. 한번은 그 요청에서 `ETIMEDOUT`이 발생했다. 사용자에게는 단순히 '로그인이 안 된다'고 보였지만, 그것은 그 사람에게 문서 접근 권한이 없다는 뜻과는 달랐다.

작업을 계속하다 보니 질문이 세 갈래로 나뉘었다. **자동화가 클러스터를 조작할 수 있는가, 사람이 서비스에 로그인할 수 있는가, 로그인한 사람이 특정 데이터를 다룰 수 있는가.** 세 질문을 모두 관리자와 일반 사용자라는 두 칸에 넣으려 하면 결국 필요한 것보다 많은 권한을 주거나, 엉뚱한 곳에서 문제를 찾게 된다.

## GitLab Runner RBAC와 Registry 인증

GitLab Runner를 Kubernetes Executor로 실행하면 Runner는 Kubernetes API에 작업을 요청하고, 클러스터는 Job에 필요한 Pod를 띄운다. 이때 필요한 것은 Runner가 사용하는 Kubernetes 신원과 그 신원에 연결된 API 권한이다.

ServiceAccount는 그 요청을 **누가 보내는지** 알려준다. Role과 ClusterRole에는 어느 API 리소스에 어떤 동작이 허용되는지 적고, RoleBinding 또는 ClusterRoleBinding으로 대상 신원과 연결한다. Namespace 하나에서 필요한 작업을 위해 클러스터 전체의 관리자 권한을 줄 이유는 없다.

그런데 실제 CI 파이프라인은 그다음에도 다른 경계를 지난다. Pod가 시작된 후 Kaniko가 빌드한 이미지를 Nexus에 Push하려면 Registry에서 받아들일 자격 증명과 저장소 권한이 필요하다. 한편 Job 이미지 자체를 가져오는 단계는 K3s의 containerd가 담당하므로, 이때는 또 노드의 Registry 연결과 인증서 신뢰가 관여한다.

이 세 단계는 한 화면의 CI 로그에 이어서 나타날 수 있다. 그렇다고 Runner의 Kubernetes Role을 넓히면 `x509` 오류가 사라지거나 Nexus의 Push 권한이 생기는 것은 아니다. 반대로 Registry 자격 증명을 올바르게 넣어도 Runner가 Kubernetes API에 필요한 작업을 요청할 수 없다면 Job은 시작하지 못한다.

권한을 고칠 때는 우선 **누가 요청을 보냈는지와 어느 서버가 그 요청을 거부했는지**를 분리해야 했다. 내가 실제로 진행했던 Runner·Kaniko·Nexus 통합 과정은 [사설 Registry와 CI 기록](/projects/rokaf-private-artifacts-and-ci/)에 더 자세히 남겼다. 특정 Role을 하나 적용해서 모든 CI 권한 문제가 영구히 해결됐다는 검증 기록까지 있는 것은 아니다.

{{figure /figures/journals/identity-policy-boundaries.svg | 같은 플랫폼에서도 Runner의 Kubernetes API 요청, Kaniko의 Registry Push, GitLab 로그인, 문서별 접근 판단은 서로 다른 신원과 정책을 사용한다. 앞의 세 경계는 실제 통합 경험을 바탕으로 했고, 마지막 객체별 관계 모델은 검토한 설계다.}}

## 요청을 보낸 신원과 권한을 부여한 범위

ServiceAccount 자체에 권한 목록이 들어 있는 것은 아니다. API Server가 요청의 신원을 확인하고 API Group, Resource, Subresource, Verb, Namespace, 필요한 경우 대상 객체 이름을 인가 판단에 사용한다. RBAC에서는 이 요청에 적용되는 RoleBinding과 ClusterRoleBinding을 통해 권한을 확인한다.

Role은 한 Namespace에 대한 규칙을 정의하고 ClusterRole은 Namespace 리소스뿐 아니라 클러스터 범위의 리소스에도 적용할 규칙을 정의할 수 있다. RoleBinding이 ClusterRole을 참조하더라도 그 Binding의 Namespace에 한정해서 권한을 부여한다. ClusterRoleBinding은 참조하는 ClusterRole의 권한을 클러스터 범위에 부여한다. RoleBinding의 대상 ServiceAccount는 다른 Namespace에 있어도 된다.

{{figure /figures/journals/identity-01-rbac-scope.svg | 가상의 Namespace A와 B를 이용해 신원과 Binding의 권한 범위를 설명했다. 실제 운영 권한 설정이 아니며 인가 이후 해당 요청의 Admission도 별도로 진행된다.}}

RBAC의 허용 규칙은 합산된다. 한 Binding을 제거하더라도 다른 Binding에서 같은 동작을 허용하면 권한이 남는다. 인증에 실패한 경우, 인가에서 거부된 경우, 인가를 통과하고 Admission에서 거부된 경우도 구분해야 한다. API 인가 결과가 허용이라고 해서 객체 생성부터 스케줄링, 컨테이너 실행까지 모두 성공한다는 뜻은 아니다.

Runner를 관리하는 프로세스와 실제 Job Pod가 같은 ServiceAccount를 사용할 필요도 없다. 전자는 Executor 설정에 필요한 API 권한이 있어야 하지만 후자는 API를 사용하지 않을 수도 있다. Kubernetes v1.32에서는 기본적으로 만료 시간이 있는 ServiceAccount Token을 Pod에 투영하고 kubelet이 이를 갱신한다. API를 사용하지 않는 워크로드에서는 자동 Token Mount를 끄는 것도 검토할 만하다. 당시 Runner에 적용했던 정확한 권한 규칙은 이 기록에 남아 있지 않다. 아래의 조회 전용 예시를 Runner 전체에 필요한 권한으로 해석해서는 안 된다.

## 최소 권한과 유효 권한 검사

Kubernetes에서 Role을 만들 때 가장 유혹적인 방법은 잘 동작하는 넓은 권한을 먼저 붙이는 것이다. 하지만 `*`로 리소스나 동작을 열어두면 YAML이 짧아지는 대신 사용자가 할 수 있는 일은 크게 늘어난다.

예를 들어 상태를 살펴보는 작업이라면 필요한 Pod나 Deployment를 조회하고 이벤트를 확인하는 수준으로 시작할 수 있다. 그렇다고 그 신원이 모든 Secret을 읽거나 다른 Pod 안에서 `exec`를 실행할 이유가 생기지는 않는다. 새 Pod를 만들 수 있는 권한 역시 그것이 사용할 ServiceAccount나 볼륨·기타 권한 조합과 함께 생각해야 한다.

그래서 자동화와 장애 복구를 같은 권한으로 묶고 싶지 않았다. 평소에 반복되는 배포 작업이 필요한 Namespace에서 특정 리소스를 수정하는 것과, 장애 때 사람이 예외적으로 강한 권한을 사용하는 일은 범위도 기록 방식도 달라야 한다.

`kubectl auth can-i`는 이 구분을 점검하는 데 유용하지만, **어떤 신원으로, 어느 Namespace에서, 어떤 Resource와 Verb를 확인했는가**가 같이 남아야 한다. 단순히 'yes' 한 줄이 나왔다고 그 계정의 전체 권한을 이해한 것은 아니다. 허용되는 동작뿐 아니라 허용돼서는 안 되는 동작도 같이 확인해야 했다.

### Pod 조회와 로그 조회는 서로 다른 요청이다

2026년 11월에는 기존 ServiceAccount가 다른 Pod의 로그도 읽을 수 있도록 권한을 추가하는 방법을 검토했다. 핵심은 관리자 권한을 새로 부여하는 것이 아니라, 로그를 읽는 API가 어떤 리소스로 분류되는지를 이해하는 것이었다. Kubernetes에서 로그는 `pods/log`라는 Subresource로 제공한다. Pod 오브젝트를 조회할 수 있다고 그 안의 컨테이너 로그까지 읽을 수 있는 것은 아니다. Pod 목록을 얻는 동작과 특정 Pod의 정보를 조회하는 동작도 서로 구분된다.

{{figure /figures/journals/identity-02-log-subresource.svg | pods의 get/list와 pods/log의 get만 허용한 가상의 조회 전용 신원. 다른 Binding이나 인가 방식이 있다면 결과는 달라질 수 있다.}}

대상 Pod가 있는 Namespace에서 필요한 조회와 로그 권한을 한정해서 부여하는 방식으로 검토했다. 신원이 속한 Namespace와 권한을 부여하는 Namespace는 다를 수 있다. 로그 조회 권한 자체로 Pod의 수정이나 삭제, exec, Secret API 조회까지 가능해지는 것은 아니다. 다만 로그 안에 민감한 데이터가 포함될 수 있으므로 읽기 권한이라고 해서 무조건 안전한 것도 아니다.

당시에는 권한을 구성하는 방법을 검토한 것이며 실제 적용 및 테스트 성공까지 확인한 기록은 없다. 적용할 때에는 대상 신원의 유효 권한을 확인하고 필요하지 않은 리소스, 동작, Namespace에서는 거부되는지도 함께 검사해야 한다. 관리자의 신원으로 요청하면서 다른 ServiceAccount의 권한을 확인했다고 판단해서는 안 된다.

## GitLab OAuth와 Backend 연결 장애

Outline이 GitLab의 사용자 정보를 요청하던 중 `connect ETIMEDOUT`이 나타났을 때, 로그인 문제를 사용자 Role 문제로 받아들였다면 잘못된 방향으로 갔을 것이다. 당시 조사에서는 이름 해석 실패를 뜻하는 `EAI_AGAIN`도 별도로 관측했다. 두 오류는 모두 접속 실패로 보일 수 있지만 하나는 DNS 조회, 다른 하나는 연결 과정에서 발생한다.

브라우저에서 GitLab 로그인 페이지가 열리는 것과 Outline 백엔드가 GitLab API에 연결되는 것도 별개의 경로였다. 서비스가 로그인에 실패했다고 해서 사용자가 권한이 없는 것이 아니며, 반대로 OAuth 과정을 통과했다고 해서 모든 문서를 수정할 자격이 생기는 것도 아니다.

이 차이를 인식한 뒤에는 인증(Authentication)과 인가(Authorization)를 다른 질문으로 보게 됐다. GitLab OAuth2 연동은 허용된 사용자 프로필을 이용해 세션을 구성할 수 있도록 하고, OIDC는 인증 계층을 별도로 제공한다. 하지만 그 사람이 특정 워크스페이스의 관리자일지, 어느 팀의 문서를 읽을 수 있을지는 애플리케이션의 정책이다. Kubernetes RBAC는 이런 문서와 팀의 관계를 알지 못한다.

그날의 네트워크 오류를 모두 해결했다는 뜻은 아니다. 확인된 오류와 이후에도 남은 조사 범위는 [Outline 인증·실시간 연결 기록](/projects/rokaf-internal-app-auth-and-tls/)에 구분해 두었다.

### 로그인 흐름과 문서 접근 판단

OAuth 2.0은 보호된 API에 대한 접근을 위임하는 방식이고 OIDC는 여기에 인증 계층을 추가한다. GitLab OAuth에서는 허용된 사용자 정보 요청을 통해 로그인한 사용자의 프로필을 얻을 수 있다. Authorization Code 방식에서는 브라우저가 리다이렉트와 Code를 전달하고 애플리케이션 Backend에서 Code 교환 및 사용자 정보 조회를 진행한다. 브라우저에서 로그인 화면에 도달했다는 것만으로 Backend의 연결 상태를 판단할 수 없었던 이유다.

{{figure /figures/journals/identity-03-oauth-boundary.svg | Authorization Code와 Session 생성 흐름을 단순화했다. 관측한 이름 해석·연결 오류를 표시했으며 모든 장애에서 정확히 어느 교환이 실패했는지 확정한 것은 아니다.}}

OIDC를 사용할 때에는 토큰의 발급자, 대상, 서명, 만료 시점과 흐름에 필요한 보호 조건을 확인해야 한다. 그러나 신원을 신뢰할 수 있게 됐다는 사실은 특정 문서 수정 권한과 별개다. 보호하려는 요청마다 애플리케이션이 실제 정책을 적용해야 한다.

## Keycloak·OpenFGA와 객체 단위 인가

여러 도구를 운영하다 보니 로그인을 통합하는 것으로 끝내기 어려운 문제가 보였다. 예를 들어 같은 팀에 속해 있더라도 한 사람은 프로젝트의 설정을 바꿀 수 있고, 다른 사람은 문서 한 개만 읽을 수 있어야 할 수 있다. 팀에서 빠진 사람에게 과거에 상속됐던 접근 권한이 남아 있어도 곤란하다.

이 문제를 살펴보면서 Keycloak과 OpenFGA를 검토했다. Keycloak은 OIDC 기반 인증과 클라이언트·토큰 관리에 가깝다. OpenFGA는 `user`, `team`, `document` 같은 주체와 객체의 관계를 이용해 `owner`, `editor`, `viewer` 등의 권한을 표현하는 데 초점을 둔다.

두 기술은 이름이 함께 등장하더라도 같은 역할을 하는 것은 아니다. Keycloak이 토큰을 발급했다고 OpenFGA가 자동으로 모든 문서 권한을 아는 것은 아니고, OpenFGA의 관계식이 Kubernetes의 Deployment 수정 권한까지 대신 결정하는 것도 아니다.

여기까지는 **객체 단위 인가를 어떻게 설계할 것인지 검토한 내용**이다. 모든 내부 애플리케이션의 로그인을 Keycloak으로 옮겼거나 OpenFGA를 공통 인가 엔진으로 배포하고 검증했다는 뜻이 아니다. 실제 사용한 OAuth 경로와 내가 고려한 관계 기반 정책을 구분해 남기려 한다.

중앙에 정책 판단을 모으는 경우에는 다른 질문도 생긴다. 팀 멤버십을 삭제하면 상속된 권한이 언제 사라지는가. 판단 결과를 캐시했다면 오래된 허가가 남지 않는가. 정책 서비스에 연결할 수 없을 때 애플리케이션이 무심코 접근을 허용하지는 않는가. 구성 요소를 하나 추가한다는 것은 새 장애 경계를 하나 만든다는 뜻이기도 했다.

### 팀을 통해 상속한 권한과 직접 부여한 권한

가상의 문서에 특정 사용자를 Viewer로 지정하거나 팀의 member Userset 전체를 Viewer로 지정하는 경우를 생각해 볼 수 있다. 문서를 읽을 수 있는 사용자는 직접 부여된 Viewer와 해당 팀의 구성원을 합친 집합이 된다. 모든 사람을 관리자와 일반 사용자로 분류하기보다 객체별 관계를 기록하고 관계의 정의를 통해 판단하는 방식이다.

{{figure /figures/journals/identity-04-relation-graph.svg | 직접 부여와 팀을 통한 상속의 가상 관계 그래프. 철회 전후 여섯 가지 판단은 로컬 집합 모델로 검증했으며 실제 OpenFGA를 실행한 결과는 아니다.}}

Alice가 Team A를 통해서만 문서를 읽을 수 있었다면 팀에서 제외되었을 때 해당 경로가 사라진다. Bob의 직접 권한은 유지되고 Carol은 두 경로가 모두 없으므로 접근할 수 없다. 하지만 분산 환경에서 권한을 철회했다고 해서 모든 판단 결과에 즉시 반영된다는 보장은 없다. 캐시된 허용 결과나 복제 지연, 다른 관계를 고려해야 한다. OpenFGA는 조회 지연과 일관성 사이의 우선순위를 선택할 수 있도록 하지만 허용 가능한 철회 지연과 캐시 무효화, 장애 시 동작은 애플리케이션에서도 결정해야 한다. 화면에서 버튼만 숨기는 것이 아니라 실제 리소스 요청의 경계에서 판단 결과를 적용해야 한다.

## 인가 허용·거부 테스트

허용된 작업이 성공하는 것만으로는 권한 설정이 적절한지 알기 어렵다. Runner가 의도한 Namespace에서 작업을 수행하는지 확인했다면, 무관한 Namespace의 Secret을 읽을 수 없어야 한다는 반대 방향도 확인해야 한다.

객체 단위 정책도 마찬가지다. Owner가 문서를 수정할 수 있는지만 시험하는 것이 아니라, Viewer는 수정할 수 없는지, 관계없는 사용자는 비공개 문서를 조회할 수 없는지, 팀에서 제외된 뒤에는 상속 권한이 철회되는지도 살펴야 한다. 특히 여러 권한이 겹치는 모델에서는 단일 Role 이름보다 **실제로 허용되는 최종 동작**이 중요하다.

Kubernetes ServiceAccount와 GitLab Runner의 RBAC, Registry 자격 증명, GitLab OAuth 연결 문제는 **서로 다른 인증·인가 경계**에서 다뤘다. 운영 중 확인한 범위는 이 구성 요소들의 접근 제어와 연동 문제이며, Keycloak·OpenFGA 기반 객체 단위 인가는 별도 설계 검토로 남아 있다. 정책을 확장할 때는 허용되는 요청뿐 아니라 실제로 거부해야 할 요청도 함께 시험할 계획이다.

## 참고 문서

- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) · [API 인가](https://kubernetes.io/docs/reference/access-authn-authz/authorization/) · [ServiceAccount](https://v1-32.docs.kubernetes.io/docs/concepts/security/service-accounts/)
- [GitLab Runner Kubernetes Executor](https://docs.gitlab.com/runner/executors/kubernetes/) · [GitLab OAuth Provider](https://docs.gitlab.com/integration/oauth_provider/)
- [OpenID Connect](https://openid.net/developers/how-connect-works/) · [OpenFGA 그룹 관계 모델](https://openfga.dev/docs/modeling/user-groups) · [OpenFGA 조회 일관성](https://openfga.dev/docs/interacting/consistency)

## 관련 기록

- [Nexus·Kaniko와 폐쇄망 CI](/projects/rokaf-private-artifacts-and-ci/)
- [Outline·GitLab 인증 경로](/projects/rokaf-internal-app-auth-and-tls/)
- [K3s 플랫폼 설계와 운영](/projects/independent-on-premises-k3s-platform-engineering/)
