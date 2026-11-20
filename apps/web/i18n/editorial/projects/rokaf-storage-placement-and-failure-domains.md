K3s의 한 노드에서 PVC가 예상하지 않은 디렉터리에 만들어지는 것을 발견했다. 데이터 디스크에 모아두려고 했던 저장소가 홈 디렉터리 아래에 자리 잡고 있었다. 처음에는 Local-path Provisioner의 경로 설정만 바꾸면 끝날 일이라고 생각했다. 그런데 `config.json`의 `nodePathMap`을 고친 뒤에도 이미 만들어진 PVC는 기존 위치를 그대로 사용했다.

돌이켜보면 이상한 동작은 아니었다. Provisioner 설정은 **다음에 볼륨을 만들 때 사용할 경로**를 결정한다. 이미 만들어진 PersistentVolume은 어떤 노드의 어떤 저장 공간을 사용하는지 별도의 참조를 가지고 있다. 설정을 바꾼다고 기존 데이터가 복사되거나 볼륨의 위치가 저절로 바뀌지는 않는다.

당시 그 PVC의 사용자는 MongoDB Replica Set의 한 멤버였다. 다른 정상 멤버들이 데이터를 가지고 있고 쿼럼을 유지할 수 있다면, 문제가 있는 Secondary의 로컬 데이터를 새 볼륨에 Initial Sync로 다시 채우는 방안을 선택할 여지가 있었다. 반대로 유일한 데이터 사본을 가진 서비스라면 같은 방법을 쓸 수 없었을 것이다.

이 사건 이후 Local-path, Longhorn, ClickHouse 복제, MinIO 분산 저장소를 하나의 'PVC 종류'로 생각하지 않게 됐다. **어느 계층이 데이터를 복구할 책임을 갖는지**가 먼저였고, Kubernetes StorageClass는 그 책임을 수행하기 위한 일부였다.

## Local-path 경로를 바꾸고도 기존 PVC가 남았던 이유

K3s에 포함된 Local-path Provisioner는 노드의 디렉터리를 기반으로 PV를 만든다. 설정 파일의 `nodePathMap`에서는 노드마다 사용할 디렉터리를 지정할 수 있고, 기본 경로와 예외 경로도 구분할 수 있다. 내가 확인한 것도 바로 이 노드별 경로 설정이었다.

설정 변경 전에는 한 노드가 의도하지 않은 디렉터리를 사용하고 있었고, 다른 노드들은 데이터 저장소에 맞춘 경로를 사용하도록 구성돼 있었다. 해당 노드의 경로를 수정한 뒤에야 이미 할당된 PVC의 처리 문제가 남았다는 사실을 확인했다.

Local-path의 PV는 데이터를 저장한 노드에 묶인다. Pod를 다른 노드에 띄운다고 그 디렉터리의 내용이 함께 따라오지 않는다. **노드 선택 조건이 있는 볼륨**이기 때문에, Pod의 Scheduling과 데이터의 실제 위치를 함께 살펴야 한다. 일반적으로 PVC는 이미 바인딩된 PV를 계속 참조한다. 새 `nodePathMap`은 기존 PV의 데이터 경로를 일괄 수정하거나 이전하지 않는다.

특히 데이터가 남아 있는 상황에서는 경로를 옮기기 위해 PVC를 지웠다가 다시 만드는 일이 위험할 수 있다. 삭제 시 데이터가 어떻게 처리되는지는 PV의 Reclaim Policy, Provisioner의 정리 동작, 실제 파일의 보존 여부에 따라 다르다. 경로 설정과 데이터 이동, 기존 PV 정리는 **서로 다른 작업**이다.

당시 대상이 MongoDB Replica Set의 교체 가능한 멤버라는 점 때문에 접근 방법이 달라졌다. 정상 멤버에서 다시 동기화할 수 있는 Secondary라면 기존 PVC를 폐기하고 새 볼륨으로 멤버를 재구성하는 방안을 검토할 수 있었다. 물론 시작하기 전에 해당 멤버가 Primary가 아닌지, 다른 멤버들이 정상인지, 과반수를 유지하는지, 재동기화할 데이터와 시간이 충분한지 확인해야 한다.

이것은 모든 MongoDB PVC를 지워도 된다는 뜻이 아니다. 특히 이 사건에서 **기존 PVC 삭제부터 Initial Sync 완료까지의 전체 과정을 성공적으로 검증한 기록은 남아 있지 않다.** 실제로 완료한 것은 경로 설정을 바로잡는 작업이고, 기존 볼륨의 재생성은 데이터 보존 조건에 맞춰 따로 판단할 작업이었다.

## Longhorn은 경로보다 Replica 상태가 중요했다

다른 영속 워크로드에서는 Longhorn을 사용했다. 애플리케이션이 데이터의 복제를 직접 관리하지 않는다면, Kubernetes에 볼륨을 제공하는 Longhorn이 Replica를 여러 노드에 유지하고 장애 시 접근을 복구하도록 만드는 선택이 유용했다. 다만 Replica를 두 개 설정했다는 것과 두 개가 실제로 정상 상태라는 것은 달랐다.

직접 조사했던 사건에서 Longhorn 볼륨은 목표 Replica가 2개였지만 하나가 `Unknown`으로 보이면서 `Degraded`였다. 임시로 목표를 1개로 낮추자 UI가 `Healthy`로 바뀌었다. 볼륨을 사용할 가능성은 개선됐지만 원래 계획했던 두 사본의 장애 내성을 복구한 것은 아니었다.

또 다른 시점에는 Replica의 실제 파일이 노드에 남아 있는데도 Longhorn이 `Stopped`로 표시했고, Instance Manager의 프로세스가 `stopping` 상태에서 빠져나오지 못해 Detach가 지연되는 문제도 조사했다. 파일이 있다는 사실은 최신 쓰기가 반영된 정상 Replica라는 증거가 아니었다.

Longhorn에서 장애 영역을 판단하려면 단순히 Replica 개수를 보는 것보다 **서로 다른 디스크와 노드에 실제로 배치됐는지, 재구축할 여유 용량과 통신 경로가 있는지, Attach와 애플리케이션 읽기·쓰기가 가능한지** 살펴야 했다. Anti-affinity 설정이나 노드·디스크 Scheduling 정책도 이런 목표에 영향을 준다.

`Healthy` 표시가 바뀌었다고 바로 복구 완료라고 쓰지 않은 이유다. 구체적인 당시 상태와 남은 검증은 [Longhorn Replica 장애와 볼륨 복구](/projects/rokaf-stateful-storage-and-recovery/)에 기록했다.

## ClickHouse는 데이터베이스가 복제 상태를 알고 있었다

ClickHouse에서는 다른 선택을 했다. 독립된 ClickHouse Pod를 두 개 만든다고 기존 MergeTree 테이블이 자동으로 복제되는 것은 아니다. 내가 수행했던 Standalone → ReplicatedMergeTree 이전에서는 Keeper가 테이블 복제의 조정 메타데이터를 관리하고, 실제 데이터 Part는 각 Replica가 자기 저장 공간에 가지고 있었다.

이런 구조에서 저장 공간 아래에 Longhorn 복제를 한 겹 더 얹는 것이 항상 좋은 선택은 아니었다. 데이터베이스도 Part를 전송하며 Replica를 따라잡고, 블록 스토리지도 별도로 Replica를 재구축한다면 하나의 장애 뒤에 두 종류의 복구 트래픽이 발생할 수 있다. 물론 블록 복제 자체가 언제나 잘못이라는 뜻은 아니다. 장애 요구사항과 운영 비용을 놓고 어느 계층이 데이터를 다시 만들 책임을 맡을지 정해야 한다.

이전 중에는 `KEEPER_EXCEPTION`, Read-only 상태와 Replica별 동기화 지연을 겪었다. 이후 `system.replicas`에서 `is_readonly = 0`이고 Queue가 비어 있는 상태를 확인했다. 하지만 그 값만으로 과거 데이터의 Row 전체가 같거나 View 결과까지 정확하다는 결론을 내릴 수는 없었다.

이 관점에서는 **로컬 디스크를 가진 Pod가 다른 노드로 자동 이동하는 능력**보다, 살아남은 ClickHouse Replica가 데이터를 제공하고 교체된 Replica가 다시 따라잡을 수 있는 능력이 중요했다. 다만 이 글에서 구체적인 전체 장애 조치 시험을 완료했다고 주장하지는 않는다. 자세한 작업은 [ClickHouse 이전: Standalone에서 ReplicatedMergeTree로](/projects/rokaf-clickhouse-replication-migration/)에 남겼다.

## MinIO에서는 객체 저장소가 데이터 분산을 맡았다

MinIO를 처음 운영할 때는 Standalone 인스턴스를 Longhorn 볼륨 위에 올려 사용했다. 이후 분산 MinIO로 옮기면서 여러 저장 멤버가 데이터를 분산 보관하도록 구성했다. 여기서는 객체 단위의 Erasure Coding이 별도의 장애 허용 모델을 제공한다.

분산 MinIO에 들어가는 모든 디스크를 다시 Longhorn 복제 볼륨으로 구성하면 저장 비용과 쓰기·복구 경로가 중첩될 수 있었다. 그래서 **서로 독립적인 로컬 저장소를 가진 멤버에 객체 저장소의 분산 책임을 맡기는 방향**으로 설계·구성했다. 그렇다고 로컬 경로를 사용하기만 하면 장애 내성이 생긴다는 뜻은 아니다. 각 멤버가 실제로 독립된 저장 장애 영역에 있는지, Erasure Set과 Parity 설정이 허용하는 장애 수가 얼마인지가 중요하다.

분산 인스턴스를 구성하고 대량 데이터를 복사한 뒤에도 원본과 대상의 객체 개수·크기 비교에는 차이가 남았다. 일부 전송 실패와 미완료 Multipart Upload, IAM 이전도 따로 조사했다. 정상적으로 시작된 분산 저장소와 기존 데이터를 빠짐없이 옮긴 저장소는 다른 검증 결과였다.

따라서 여기서는 분산 MinIO를 배포하고 데이터 이전을 수행했다는 사실까지만 다룬다. **객체 단위의 최종 무결성 대조가 전부 완료됐다는 뜻은 아니다.** 관련 기록은 [MinIO 이전: Standalone에서 분산 구성으로](/projects/rokaf-object-storage-migration/)에 있다.

## 네 가지 저장 방식이 서로 다른 책임을 갖는다

{{figure /figures/journals/storage-failure-domain-matrix.svg | Local-path, Longhorn, 데이터베이스 복제, 분산 MinIO가 각각 어느 계층에서 데이터 복구를 담당하는지 비교했다. 실제 디스크 배치도나 내부 노드 구조는 아니다.}}

| 저장 방식 | 데이터를 복구하는 주체 | 노드에 문제가 생겼을 때 | 확인해야 할 상태 |
| --- | --- | --- | --- |
| Local-path | 기본적으로 자동 복제 없음. 사용자 또는 상위 애플리케이션 | 원래 노드에 묶인 데이터. 다른 노드로 옮기려면 별도 이전·복원 필요 | 실제 경로, PV 바인딩·Node Affinity, 백업 또는 재동기화 가능 여부 |
| Longhorn | 블록 스토리지의 Replica·Engine | 남은 정상 Replica로 볼륨을 제공하고 적절한 위치에 재구축해야 함 | 실제 Healthy Replica 수, Attach, 재구축, 애플리케이션 I/O |
| ClickHouse·MongoDB | 데이터베이스 자체 Replication | 정상 DB 멤버에서 읽기·쓰기를 지속하고 교체 멤버를 다시 동기화해야 함 | DB 쿼럼·Primary·Replica 지연·데이터 결과 |
| 분산 MinIO | 객체 단위 Erasure Coding | Erasure Set의 허용 범위에서 객체 읽기·쓰기와 Healing을 수행 | 객체 조회, Healing, 디스크·멤버 상태, 데이터 대조 |

이 비교는 어떤 방식이 다른 방식보다 무조건 낫다는 표가 아니다. Local-path를 쓰면서 MongoDB가 자체 복제를 수행하는 것도 가능하고, Longhorn이 제공하는 PVC가 꼭 데이터베이스에 부적합한 것은 아니다. 목적은 **데이터를 복구할 사람이 어떤 상태와 도구를 먼저 확인해야 하는지** 명확히 정하는 것이다.

같은 Kubernetes 클러스터에 이런 방식을 함께 운영하면 장애 대응 순서도 달라진다. Local-path 볼륨은 PV가 가리키는 노드와 디렉터리부터 살펴야 한다. Longhorn은 Replica와 Engine, Attach 상태를 봐야 한다. 데이터베이스 자체 복제를 쓰면 애플리케이션의 합의·복제 상태를 읽어야 한다. MinIO에서는 객체의 실제 조회 결과와 Erasure Set의 상태가 중요하다.

## Replica 수와 장애 영역

저장소를 나눠 운영하면서 특히 경계했던 것은 '여러 사본을 만들었다'는 설정값이었다. 서로 다른 Replica가 한 물리 장치에 의존한다면 디스크 장애를 함께 맞을 수 있다. 다른 노드에 있어도 공통 전원·네트워크·스토리지 장치에 의존하면 장애 범위를 완전히 분리했다고 말할 수 없다. 내부 장비 배치를 공개하거나 특정 장애 내성을 입증할 자료가 없기 때문에 이 글에서는 실제 위치를 그리지 않았다.

또 복제는 백업이 아니다. 실수로 삭제한 데이터는 정상 Replica에도 복제될 수 있다. ClickHouse와 MongoDB의 데이터 복제가 원본 데이터의 모든 논리적 오류에서 보호해 주는 것은 아니고, MinIO의 Erasure Coding도 애플리케이션이 잘못 삭제한 객체를 자동으로 되돌려주지는 않는다. 복구 시점이 다른 백업과 복원 검증이 필요한 이유다.

원래 데이터를 보존해야 하는지, 다른 정상 사본으로부터 재생성할 수 있는지, 장비 하나가 멈췄을 때 어디에서 서비스를 계속 제공할지는 볼륨을 만들기 전에 결정해야 했다. 기존 Local-path PVC의 경로를 고치며 부딪힌 문제도 결국 그 결정에 연결돼 있었다.

## 배치 설정 변경과 복구 검증 범위

실제로 확인한 것은 노드별 Local-path 경로 설정을 수정했다는 점, 변경 전 PV가 자동 이전되지 않는다는 제약, Longhorn의 목표 Replica를 낮춘 뒤 표시가 바뀐 상태, ClickHouse 복제 전환 과정의 중간 상태, 분산 MinIO 구성과 데이터 이전 후의 객체 차이였다.

Local-path Provisioner의 `nodePathMap`을 수정하고 기존 PV가 새 경로로 자동 이동하지 않는 동작을 확인했다. 이 경험을 Longhorn의 Replica 복구, ClickHouse·MongoDB의 DB 자체 복제, 분산 MinIO의 객체 복구 책임과 연결해 **데이터의 복구 주체에 따라 StorageClass와 배치를 선택하는 기준**을 정리했다. 각 스토리지의 완전한 장애 조치와 데이터 정합성 검증은 해당 계층의 실제 읽기·쓰기 결과로 판단해야 한다.

## 관련 기록과 참고 자료

- [Longhorn Replica 장애와 볼륨 복구](/projects/rokaf-stateful-storage-and-recovery/)
- [MinIO 이전: Standalone에서 분산 구성으로](/projects/rokaf-object-storage-migration/)
- [ClickHouse 이전: Standalone에서 ReplicatedMergeTree로](/projects/rokaf-clickhouse-replication-migration/)
- [K3s Volumes and Storage](https://docs.k3s.io/add-ons/storage)
- [Local Path Provisioner — Configuration](https://github.com/rancher/local-path-provisioner)
- [Longhorn — Replica Scheduling](https://longhorn.io/docs/1.13.0/nodes-and-volumes/nodes/scheduling/)
- [MinIO — Erasure Coding](https://min.io/docs/minio/kubernetes/upstream/operations/concepts/erasure-coding.html)
