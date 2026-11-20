2025년 7월 부대에 배치된 이후 폐쇄망에서 AI 서비스를 지원하는 온프레미스 K3s 플랫폼을 직접 구축하고 운영했다. 특히 **여러 GPU를 중앙에서 관리하고 사용자에게 제공하는 공용 연산 환경**을 만든 일이 중요한 축이었다. KAI Scheduler를 직접 반입·배포해 운영했고, JupyterHub를 구축해 Notebook 환경도 실제 서비스로 제공했다. 이미지 배포, 네트워크, 저장소, 데이터베이스와 장애 복구까지 그 공용 환경을 유지하는 데 필요한 문제들을 함께 다뤘다.

플랫폼 설계와 최초 배포, 운영 중 장애 조사와 개선을 맡았지만, 여기에서 돌아가는 모든 애플리케이션을 내가 개발했다는 뜻은 아니다. 내가 책임졌던 일은 각 서비스가 **실제로 배포되고, 접근할 수 있으며, 필요한 권한을 가지고, 문제가 생겼을 때 복구할 수 있는 환경**을 만드는 것이었다.

이 작업으로 공군참모총장 표창을 받았다. 아래 내용은 그 경험 중 공개 가능한 기술적 판단을 중심으로 다시 정리한 기록이다. 실제 군 내부 네트워크나 장비 배치, 접근 경로를 설명하는 문서는 아니다.

## 서비스를 하나씩 띄우는 것과 플랫폼을 운영하는 것

처음에는 필요한 서비스가 있으면 Helm Chart나 Manifest를 살펴보고 설치하는 일이 많았다. 한 서비스가 뜨면 다음 서비스를 추가하는 식으로 진행할 수도 있었다. 하지만 운영하다 보니 문제는 설치 순간보다 그 이후에 나타났다.

Registry가 고장 났을 때 이미지를 어디에서 가져올 것인가. Secret이나 사설 CA를 갱신하면 어느 프로세스의 신뢰가 달라지는가. Pod는 다시 시작됐는데 PVC가 붙지 않으면 서비스가 살아났다고 말할 수 있는가. GPU를 스케줄러가 할당했다는 사실만으로 모델이 실행될 수 있는가.

K3s는 이런 서비스의 공통 실행 환경을 제공했지만 모든 책임을 대신해주지는 않았다. 그래서 플랫폼을 YAML 파일의 모음보다는 **서로 다른 계층이 교환하는 약속**으로 이해하려 했다.

{{figure /figures/k3s-capabilities.svg | K3s 운영 환경에서 중요했던 책임 영역을 나눈 개념도다. 실제 네트워크나 장비의 물리적 배치를 표현하지 않는다.}}

## 주제별 플랫폼 운영 기록

하나의 프로젝트에 모든 내용을 쌓아두면 개별 설계 판단이 흐려졌다. 그래서 가장 많이 고민했던 문제를 별도로 기록했다.

| 주제 | 기록 |
| --- | --- |
| 이미지 공급 | [내부 Registry와 Kaniko 실행 환경](/projects/rokaf-private-artifacts-and-ci/) — Kaniko 실행 환경, Registry CA, S3 Blob Store와 복구 이미지의 순환 의존성 |
| 배포 조정 | [GitOps의 두 제어 루프](/projects/rokaf-offline-gitops-delivery/) — 빌드 성공과 Kubernetes 상태 동기화의 차이 |
| Longhorn 복구 | [Longhorn Replica 장애와 볼륨 복구](/projects/rokaf-stateful-storage-and-recovery/) — Unknown·Stopped Replica, Attach 장애와 데이터 검증의 차이 |
| 스토리지 배치 | [Kubernetes 스토리지 배치와 장애 영역 설계](/projects/rokaf-storage-placement-and-failure-domains/) — 노드별 Local-path 경로, Longhorn 복구, DB 자체 복제, MinIO 객체 분산의 책임 구분 |
| 객체 저장소 | [MinIO 이전과 객체 차이 검증](/projects/rokaf-object-storage-migration/) — 전송, IAM, Lifecycle, 누락 객체 |
| 채팅 첨부파일 | [Rocket.Chat 첨부파일 GridFS·MinIO 이전](/projects/rokaf-chat-attachments-object-storage/) — 파일 식별자와 S3 Key·업로드 메타데이터를 맞추는 문제 |
| 데이터베이스 | [DB 고가용성과 마이그레이션](/projects/rokaf-database-ha-and-langfuse-migrations/) — MongoDB, PostgreSQL, ClickHouse와 Keeper |
| ClickHouse | [ReplicatedMergeTree로 데이터 옮기기](/projects/rokaf-clickhouse-replication-migration/) — 테이블 메타데이터, Replica 상태, 데이터 검증 |
| 인증과 인가 | [ServiceAccount부터 객체 권한까지](/projects/rokaf-identity-rbac-and-policy/) — Kubernetes RBAC와 애플리케이션 권한 |
| 네트워크 | [Traefik·MetalLB·사설 TLS](/projects/rokaf-networking-and-tls/) — DNS, 요청 경로, 인증서 신뢰 |
| Plane CE 초기 설정 | [Plane CE 초기 설정과 API 라우팅](/projects/rokaf-plane-ce-bootstrap-routing/) — 관리자 화면과 인증 API의 라우팅, 추가 프록시와 파일 저장소 경계 |
| Outline 인증과 편집 | [Outline WebSocket·OAuth·TLS 장애](/projects/rokaf-internal-app-auth-and-tls/) — GitLab 연결 Timeout, WebSocket Upgrade, 브라우저 인증서와 이미지 요청 문제 |
| 서비스 연동 | [자체 호스팅 서비스 연동](/projects/rokaf-self-hosted-services-integration/) — SMTP, Helm 환경변수, 파일 저장소와 Registry 클라이언트의 의존성 |
| 외부 접속 | [ServiceLB와 호스트 포트 충돌](/projects/rokaf-service-lb-hostport-conflict/) — VIP 주소와 포트 자원의 소유권 |
| 중앙 GPU 관리 플랫폼 | [KAI Scheduler·JupyterHub 구축과 운영](/projects/rokaf-central-gpu-platform-kai-jupyterhub/) — 폐쇄망 반입, 공용 GPU 자원 관리, 사용자 Notebook 환경 제공 |
| GPU 자원 공유 정책 | [Time-slicing과 MIG의 차이](/projects/rokaf-gpu-scheduling-and-capacity/) — VRAM 경합, 논리 슬롯, 장애 시 배치 용량 |
| 관측성 | [사라진 메트릭의 원인 추적](/projects/rokaf-observability-and-failure-evidence/) — Prometheus WAL과 DCGM Exporter 배치 |
| RabbitMQ Worker | [RabbitMQ 메시지 재전달과 Worker 중복 처리](/projects/rokaf-async-workers-and-idempotency/) — Shovel 메시지 이전, Heartbeat 장애와 Claim·Lease 기반 작업 복구 |
| 문서 번역 파이프라인 | [작업 상태·Lease·재시도](/projects/document-translation-pipeline/) — PDF·DOCX·HWPX Worker와 영속 Job 상태를 설계·구현하고 내부망에 배포·운영 |

원인이 끝까지 확정되지 않았던 조사도 따로 남겼다. [Langfuse v4 마이그레이션](/projects/rokaf-langfuse-v4-migration-field-notes/)에서는 Timeout이 떠도 내부 진행 상태가 완료일 수 있다는 것을 확인했고, [DNS와 VIP 문제](/projects/rokaf-dns-vip-open-investigations/)에서는 하나의 증상에 여러 경로가 관여할 수 있다는 한계를 남겼다. [K3s iptables 규칙 적용 장애와 Pod 통신 경로](/projects/rokaf-k3s-cni-service-datapath/)에서는 iptables 규칙 초기화 문제를 복구한 과정과, 별도로 원인이 남아 있던 Pod·ClusterIP 통신 문제를 구분했다. [GPU 리소스 발견](/projects/rokaf-gpu-discovery-open-investigation/)과 [Control Plane 장애](/projects/rokaf-control-plane-incident-log/)도 마찬가지로 관측과 가설을 구분해 정리했다. [Linux 메모리 압박과 earlyoom 서비스 오류](/projects/rokaf-memory-pressure-and-service-recovery/)에서는 메모리 포화와 systemd 오류, 이후 프로세스 종료 기록을 서로 다른 사건으로 구분했다.

## 운영하면서 반복해서 부딪힌 선택

### 단순한 구성이 항상 나쁜 것은 아니다

하나의 인스턴스가 오히려 이해하고 복구하기 쉬운 경우도 있다. 반대로 Replica를 늘리고 별도의 Coordinator를 붙이면 장애 허용 범위가 넓어질 수 있지만 운영할 상태와 복구 순서도 늘어난다.

복제본 개수보다 먼저 물어야 할 것은 **어떤 장애까지 버틸 것인가, 실제로 복구했을 때 무엇을 검증할 것인가**였다.

### 공유 클러스터는 공유된 실패 영역을 만든다

클러스터 하나에 여러 서비스를 모으면 배포와 관리가 편해진다. 그러나 DNS, 사설 Registry, 인증서, 저장 공간, Ingress 같은 공통 의존성이 고장 나면 서로 관계없어 보이는 서비스가 동시에 영향을 받을 수 있다.

실제로 어느 접속 경로가 어떤 컨트롤러에 의해 만들어지는지 모르면, 새 Service 하나가 기존 서비스의 호스트 포트에 영향을 주는 일도 이해하기 어렵다. 네트워크 계층을 조사할 때는 트래픽의 이동 경로뿐 아니라 **그 경로를 누가 만들고 관리하는가**도 확인해야 했다.

### 복제는 자원을 소비한다

Longhorn 볼륨의 Replica든 데이터베이스 자체의 복제든 장애에 대비하기 위해 저장 공간과 동기화 작업이 필요하다. 여유 공간이 부족하면 복제본이 존재하더라도 재구축하지 못할 수 있다.

GPU에서도 비슷한 문제가 있었다. Time-slicing으로 스케줄러에 보이는 슬롯을 늘렸다고 모델이 사용할 VRAM까지 늘어나는 것은 아니다. 장치 사용률이 낮아 보여도 실제로 배치 가능한 모델 수는 작을 수 있다. **자원이 표시되는 것과 자원이 실제로 사용 가능한 것은 다른 문제**였다.

## 운영 변경 검증 기준

어떤 설정을 바꾼 뒤 Pod가 Running이 되면 우선 안심하게 된다. 하지만 그것만으로 기존 문제가 해결됐다고 기록하기에는 부족했다.

나는 변경을 검토할 때 네 가지 질문을 남기려 했다.

1. 원래 문제를 일으킨 조건을 제거했는가, 아니면 우연히 그 조건을 피해갔는가?
2. 변경으로 새로운 공통 의존성이나 실패 영역이 생기지 않았는가?
3. 정상 여부를 어떤 실제 요청과 데이터 상태로 확인할 수 있는가?
4. 플랫폼 자체가 고장 났을 때 복구에 필요한 이미지와 데이터에 접근할 수 있는가?

특히 데이터베이스와 객체 저장소는 시작된 프로세스보다 **복구된 상태의 정확성**이 중요했다. 마이그레이션 화면이 실패를 표시하더라도 영속 진행 상태와 실제 데이터가 이미 바뀌어 있을 수 있었다.

이 질문들을 모든 변경에 대한 자동 검증으로 완성했다고 주장할 수는 없다. 다만 문제를 다시 만났을 때 판단을 반복하지 않기 위해 남긴 기준이다.

## Kubernetes 운영에서 마주한 시스템 경계

처음에는 Kubernetes API에서 보이는 상태로 충분할 때가 많았다. 하지만 PVC가 붙지 않거나, 볼륨이 Read-only가 되거나, 노드가 메모리 압박을 받는 순간에는 Pod 상태보다 아래 계층을 이해해야 설명할 수 있는 일이 늘어났다.

어떤 쓰기가 실제로 디스크에 반영됐는지, 파일시스템이 오류를 만났을 때 무엇을 보장하는지, VFS와 I/O 경로에서 어떤 대기와 재시도가 발생하는지 같은 질문이 자연스럽게 따라왔다.

그래서 이후에는 Linux 커널과 파일시스템, 메모리 관리, 영속 I/O를 더 깊이 공부하려 한다. 운영 경험을 연구 관심사에 억지로 연결하기보다는, **운영 중 끝까지 설명하고 싶었지만 아직 충분히 이해하지 못한 문제들이 그 아래 계층에 있었다**고 표현하는 편이 맞겠다.

이 페이지는 폐쇄망 K3s 플랫폼에서 직접 맡았던 설계·배포·운영 범위를 정리한 개요다. 세부 장애 기록에는 실제로 확인한 증상과 조치, 검증하지 못한 부분을 구분해 남겼다.

*이 기록에는 실제 내부 주소·호스트 배치·인증정보·보안 설정·구체적인 복구 명령을 포함하지 않았다. 일부 설계는 실제 운영 결과가 아니라 조사와 선택 단계의 판단임을 구분한다.*
