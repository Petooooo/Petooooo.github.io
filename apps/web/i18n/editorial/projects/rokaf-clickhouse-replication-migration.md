ClickHouse Pod를 하나 더 띄우는 일은 어렵지 않다. 하지만 기존 데이터를 가진 Standalone ClickHouse를 **실제로 복제되는 데이터베이스**로 바꾸려면 이야기가 달라진다.

처음에는 StatefulSet의 Replica 수를 늘리고 저장소를 연결하면 충분할 것처럼 보였다. 실제로는 테이블 엔진, Keeper의 복제 메타데이터, 각 노드의 데이터 Part, View와 Materialized View가 서로 다른 방식으로 상태를 관리하고 있었다. Pod가 두 개라는 사실은 그중 어느 것도 해결해주지 않았다.

## 데이터베이스 복제를 어느 계층에서 할 것인가

한 가지 방법은 Longhorn처럼 블록 스토리지를 복제하고 그 위에서 단일 ClickHouse 데이터베이스를 운영하는 것이다. 하지만 ClickHouse는 MergeTree 데이터 Part와 Replication 작업을 자체적으로 이해한다. 여기에 블록 복제까지 겹치면 평상시 쓰기뿐 아니라 장애 이후 재구축 트래픽도 늘 수 있다.

그렇다고 Local Storage가 항상 우월하다는 뜻은 아니다. 중요한 것은 **어느 계층이 최종적으로 데이터의 일관성과 복구를 책임지는가**를 정하는 것이다.

내가 선택한 방향은 ReplicatedMergeTree 계열 테이블과 Keeper를 이용한 데이터베이스 수준 복제였다. 이 구조에서는 각 Replica가 자체 저장소에 데이터 Part를 가지고 있고, Keeper는 복제 그룹의 메타데이터와 조정 작업을 관리한다. Keeper가 모든 테이블의 실제 데이터 파일을 보관하는 네트워크 드라이브인 것은 아니다.

{{figure /figures/journals/clickhouse-replica-ownership.svg | 독립적인 MergeTree 테이블과 Keeper를 이용하는 ReplicatedMergeTree의 상태 소유권을 비교했다. 그림은 개념도이며 실제 노드 배치를 나타내지 않는다.}}

## 기존 테이블이 있는 상태에서 시작했다

빈 데이터베이스에 ReplicatedMergeTree 테이블을 처음 만드는 것과, 이미 분석 데이터가 들어 있는 Standalone 환경을 옮기는 것은 다르다.

나는 기존 백업을 기준으로 테이블 엔진과 의존성을 정리했다. MergeTree 계열 스토리지 엔진을 복제 가능한 엔진으로 변환하되, View와 Materialized View는 일단 분리했다. 테이블의 엔진 이름만 바꾸는 것으로 모든 의존성이 해결되지 않기 때문이다.

특히 Materialized View는 Insert의 결과를 다른 테이블로 흘려보낼 수 있다. 원본과 대상, Insert가 들어오는 경로를 확인하지 않고 View를 여러 Replica에서 동시에 생성하면 중복 처리나 잘못된 집계가 생길 가능성이 있다. 그래서 기초 테이블의 변환과 동기화 상태를 먼저 확인하고 파생 View를 이후에 다루는 편이 디버깅하기 좋았다.

실제 기록에서는 의도한 기초 테이블들의 엔진 변환을 끝내고 `system.tables`로 확인했다. 하지만 그 자체가 과거의 모든 Row와 모든 파생 집계가 정확히 일치한다는 증명은 아니었다.

## Keeper 예외와 Read-only 상태

복제형 테이블에는 논리적인 복제 그룹의 경로와 각 Replica를 구분하는 이름이 필요하다. 같은 테이블을 복제하려면 같은 복제 그룹을 바라봐야 하지만, 각 멤버의 식별자는 서로 달라야 한다.

기존 데이터를 Attach하던 과정에서는 `KEEPER_EXCEPTION`을 만났고 Replica가 Read-only 상태로 들어간 시점도 있었다. 이런 오류를 한 줄로 “Keeper가 고장 났다”고 적으면 너무 많은 가능성을 지워버린다.

Keeper 세션의 문제일 수도 있고, 테이블 정의와 저장된 메타데이터가 어긋난 것일 수도 있으며, 복제 경로나 Replica 식별자가 충돌했을 수도 있다. 원인을 확정하기 전에 여러 테이블을 반복적으로 Detach·Attach하는 것은 위험하다. 조정 계층의 상태와 로컬 메타데이터를 나눠 확인해야 했다.

진행 후에는 복제 테이블이 더 이상 Read-only가 아니었고, 보이는 복제 대기열도 비어 있는 중간 상태를 확인했다.

- `is_readonly = 0`: 해당 시점에 검사한 Replica가 Read-only가 아니라는 뜻이다.
- `queue_size = 0`: 그 순간 해당 대기열에 처리할 작업이 남지 않았다는 뜻이다.

둘 다 의미 있는 신호였다. 하지만 모든 Replica의 데이터가 영구적으로 동일하다거나, 장애 상황에서도 모든 요청이 성공한다는 의미까지 담고 있지는 않다.

## 한쪽 Replica가 먼저 따라잡을 때

실제로 한 Replica는 데이터가 늘어나고 다른 Replica는 뒤늦게 따라오는 시점이 있었다. 비동기 복제를 운영한다면 이상한 모습은 아니다. 복제 작업이 진행되는 동안 잠깐씩 데이터 Part나 Row 수가 달라질 수도 있다.

여기서 느린 Replica를 다시 초기화하는 것보다 먼저 확인할 것은 **대기 작업이 무엇이며 그 차이가 줄고 있는가**였다. Replica 간 Part의 물리적 개수가 항상 같아야 하는 것도 아니다. Merge 작업에 따라 같은 논리 데이터를 서로 다른 Part 구성으로 가질 수 있다.

ReplacingMergeTree처럼 엔진 특성이 다른 경우 Row 수 비교 자체도 조심해야 한다. 물리 Part 수나 단순 Count 하나를 전체 무결성의 기준으로 삼을 수는 없다.

{{figure /figures/journals/clickhouse-migration-evidence.svg | 테이블 정의, Keeper 연결, Replica 쓰기 가능 상태, 대기열, 데이터 검증, 애플리케이션 요청은 서로 다른 검증 지점이다. 그림에 실제 마이그레이션 측정값을 넣지는 않았다.}}

검증할 때 참고한 정보의 역할도 분리해야 했다. `system.tables`는 엔진과 테이블 정의를 알려준다. `system.replicas`는 Replica 상태와 복제 진행 상황을 보여준다. 더 상세한 문제를 볼 때는 `system.replication_queue`와 실제 데이터 Part, 쿼리 결과를 함께 살펴야 한다.

## View를 다시 연결하는 시점

기초 테이블의 복제 상태가 안정된 뒤에는 View와 Materialized View가 어떤 Insert를 처리할지 정해야 했다.

Materialized View가 로컬 Insert를 소비하는지, 그 결과가 복제 대상 테이블을 통해 전파되는지, 동일한 논리 Insert가 다른 Replica에서도 다시 처리되는지에 따라 결과가 달라질 수 있다. 기초 데이터가 복제됐다는 사실만으로 집계 테이블이 중복 없이 생성된다고 말할 수 없다.

따라서 View 정의를 재생성하는 것은 작업의 마지막에 붙이는 형식적인 단계가 아니다. 어떤 테이블이 데이터의 원천이고 어떤 테이블이 파생 결과를 보관하는지 확인한 뒤 별도로 검증해야 하는 문제였다.

## 마이그레이션을 완료했다고 말하려면

정말 완료를 판단하려면 백업이 정상적으로 복원되는지, 의도한 모든 테이블이 동일한 복제 그룹에 속하는지, Replica마다 Read-only와 대기 작업에 문제가 없는지, 주요 Partition과 논리적인 쿼리 결과가 일치하는지 살펴야 한다.

여기서 끝내지 않고 실제 애플리케이션의 읽기·쓰기를 테스트해야 한다. 특히 View와 Materialized View가 개입하는 경로는 별도로 확인해야 한다. 장애를 가정해 한 Replica를 재시작한 뒤 남은 Replica의 사용 가능성과 재합류 과정까지 검증할 수 있다면 더 좋다.

이것은 **내가 필요하다고 판단한 완료 기준**이다. 모든 항목을 당시 충족했다는 뜻은 아니다.

기록으로 확인되는 사실은 기존 Standalone 데이터를 복제형 테이블로 전환한 작업, View를 별도로 다룬 결정, Keeper 예외와 Read-only 조사, 쓰기 가능한 상태와 빈 대기열을 확인한 중간 결과, 두 Replica의 진행 속도가 달랐던 과정이다. 전체 Row의 완전한 비교나 데이터 손실 0건, 모든 View의 결과 정합성, 장애 허용 수준까지 증명한 자료는 없다.

ClickHouse 마이그레이션에서 중요한 질문은 “복제본이 몇 개 있는가”보다 **어떤 데이터가 어느 Replica에서 읽히고, 그 정확성을 무엇으로 확인할 수 있는가**였다. Kubernetes에서 Pod를 늘리는 것과 데이터베이스가 같은 데이터를 제공하게 만드는 것은 분명히 다른 작업이었다.

## 참고 자료

- [ClickHouse ReplicatedMergeTree](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/replication)
- [ClickHouse system.replicas](https://clickhouse.com/docs/reference/system-tables/replicas)
- [ClickHouse system.replication_queue](https://clickhouse.com/docs/reference/system-tables/replication_queue)
- [데이터베이스 HA와 마이그레이션](/projects/rokaf-database-ha-and-langfuse-migrations/)
- [영속 저장소의 복구](/projects/rokaf-stateful-storage-and-recovery/)
