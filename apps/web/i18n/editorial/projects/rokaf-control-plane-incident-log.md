K3s에서 Control Plane이 불안정해지면 평소에 당연하게 사용하던 `kubectl` 요청부터 막힌다. 여러 서비스에 문제가 나타나면 개별 애플리케이션보다 클러스터의 상태를 저장하고 전달하는 쪽을 먼저 보게 된다. 당시에도 etcd 상태가 흔들리거나 손상이 의심되는 상황을 조사했고, 다른 기록에는 디스크가 Read-only로 동작하는 증상도 남아 있었다.

일단 API에 다시 접근할 수 있게 되면 운영은 이어갈 수 있다. 실제로 일부 상황에서는 가용성을 회복했다. 그러나 그 결과만으로 **etcd가 먼저 고장 났는지, 호스트의 저장 장치가 먼저 쓰기를 거부했는지** 설명할 수는 없었다. 기록이 충분하지 않은 상태에서 하나의 복구 과정을 모든 장애의 원인과 해결책으로 묶고 싶지는 않았다.

## API 중단과 etcd 상태 조사

K3s의 Control Plane에는 Kubernetes API와 Controller, Scheduler가 있고, embedded etcd로 구성한 경우에는 etcd가 클러스터의 상태를 저장한다. API가 응답하지 않거나 상태 변경을 처리하지 못하면 애플리케이션의 배포와 복구까지 영향을 받을 수 있다. 그렇다고 API 요청 실패가 곧 etcd 데이터 손상을 뜻하는 것은 아니다. K3s 프로세스, API까지의 네트워크 경로, 디스크 지연, etcd의 멤버 상태가 모두 관여할 수 있다.

특히 etcd는 단일 프로세스가 실행 중인지로만 판단하기 어렵다. 로컬 멤버 하나가 살아 있어도 클러스터가 쿼럼을 확보하지 못하면 새로운 상태를 정상적으로 Commit할 수 없다. 반대로 한 멤버에서 이상이 보이더라도 쿼럼이 유지되는 동안 다른 멤버들이 서비스를 계속 제공할 수 있다.

당시 etcd 상태를 살피는 과정에서 불안정과 손상이 의심되는 증상을 마주했다. 여기서 **'손상 의심'과 실제 데이터 손상 확인은 구별**해야 한다. 남아 있는 자료로는 멤버별 로그와 저장 장치 오류를 같은 시각에 대조해, 특정 디스크 문제가 etcd의 일관성 오류로 이어졌다고 입증할 수 없다. 그래서 이 글에서는 하나의 결정적인 etcd 복구 명령을 제시하거나 그 명령으로 모든 문제가 해결됐다고 쓰지 않았다.

## Read-only 증상과 파일시스템 진단

장애 기록에 Read-only가 나타났을 때 처음에는 저장 장치가 더 이상 쓰기를 받아들이지 않는 상황을 떠올렸다. 하지만 실제로는 **어느 계층이 Read-only라고 말했는지**가 먼저였다.

파일시스템이 I/O 오류나 내부 일관성 문제 이후 Read-only로 Remount됐을 수 있다. 처음부터 읽기 전용으로 마운트된 경로일 수도 있다. 애플리케이션이 파일을 수정할 권한이 없어 실패한 것과 파일시스템의 Read-only 전환도 같은 사건이 아니다. ClickHouse처럼 복제나 조정 상태 때문에 논리적으로 Read-only가 되는 데이터베이스도 있었다. 그런 DB 오류를 Linux 파일시스템의 상태로 그대로 해석할 수는 없다.

etcd는 데이터를 로컬에 영속적으로 기록하므로, 쓰기가 지연되거나 실패하는 저장 경로는 분명히 살펴볼 대상이었다. 파일시스템의 Journal, 블록 장치 I/O, `fsync` 지연과 오류, 디스크 상태에 관한 기록이 필요한 이유다. 하지만 스토리지 오류가 etcd 장애를 일으켰다는 설명에는 **두 종류의 로그를 같은 시간축으로 묶은 증거**가 있어야 한다.

당시의 자료에는 그 연결을 확정할 만큼 충분한 로그가 남아 있지 않았다. Read-only라는 문구 하나만으로 디스크의 물리적 손상, RAID 문제, etcd 데이터 손상까지 차례로 추정해서는 안 됐다.

{{figure /figures/journals/control-plane-incident-evidence.svg | etcd 불안정·손상 의심과 Read-only 증상은 관측된 별도 항목이다. 디스크 쓰기 실패에서 etcd, API 장애로 이어지는 인과관계는 아직 검증하지 못했으므로 점선으로 표시했다. 실제 장애 시각이나 내부 노드 배치는 나타내지 않았다.}}

## 3월 10일, 저장장치와 합의 클러스터의 장애

2026년 3월 10일에는 여러 Server 노드의 디스크와 RAID 장애, etcd Snapshot 손상 의심, K3s 기동 실패를 보고했다. 이후 복구를 논의하면서 managed etcd의 Membership이 이미 Reset됐다는 메시지를 확인했다. 이는 Reset Marker가 남아 있었다는 증거이지 Snapshot 복원 성공이나 새로운 클러스터의 정상 상태, 전체 데이터 검증을 의미하지 않는다. 당시 RAID Level이나 장치별 오류 수치, 배열의 실제 상태 및 최종 멤버 목록은 남아 있지 않다. 내부 장치와 노드 식별자는 제외했다.

여기서 구분해야 할 것은 두 종류의 중복성이다. RAID는 일부 구성 디스크가 실패해도 로컬 논리 장치를 사용할 수 있게 하고, Raft는 일부 투표 멤버가 실패해도 합의 상태를 유지할 수 있게 한다. RAID 디스크 하나가 Raft의 투표 멤버 하나에 대응하는 것은 아니다. 디스크가 여러 개라도 하나의 투표 멤버로 구성된 서버의 Vote는 하나다. 전원이나 저장소를 공유하면 장애가 서로 독립적이라는 가정도 깨질 수 있다.

{{figure /figures/journals/raid-01-layer-boundaries.svg | 로컬 저장장치와 클러스터 합의는 서로 다른 의존성이다. 계층 간 장애 전파는 가능하지만 당시 인과관계는 확인되지 않았다.}}

## Linux MD의 논리 블록과 중복성

Linux Software RAID는 여러 구성 장치 위에 MD Block Device를 제공한다. 그 위의 파일시스템은 각 디스크를 직접 고르는 대신 논리 블록에 접근한다. 실제 매핑은 RAID Level과 Layout에 따라 달라진다. RAID1은 데이터를 복제하고 RAID5는 데이터와 단일 Parity를 분산하며 RAID6는 두 번째 독립적인 Parity를 사용한다. RAID0에는 중복성이 없다. 장애 이후에도 동작하는지는 어떤 장치가 빠졌는지, 남은 데이터를 정상적으로 읽을 수 있는지에 따라 달라진다. RAID10도 어느 복제본을 잃었는지가 중요하다.

예를 들어 두 장치의 Mirror와 세 장치의 단일 Parity Stripe를 생각해 보자. 데이터 블록 A와 B가 있다면 Parity는 A XOR B다. 누락 위치를 알고 한 블록만 잃었다면 나머지 두 블록으로 재구성할 수 있다. 두 블록을 잃으면 정보가 부족하다. 세 블록이 모두 존재하는데 XOR 결과가 맞지 않는다고 어느 블록이 잘못됐는지까지 찾을 수 있는 것은 아니다.

이번에는 내용이 정해진 4096바이트 버퍼를 이용해 세 위치에서 각각 하나씩 누락시킨 뒤 복원 결과를 검증했다. 두 블록 누락을 거부하고 변경된 블록의 불일치도 확인했다. 실제 MD 배열을 만들거나 Rebuild 성능을 측정한 것은 아니다. 실제 RAID5에서는 Write Hole과 정합성 문제도 고려해야 하고 RAID6의 코딩 방식도 다르다.

{{figure /figures/journals/raid-02-redundancy.svg | 가상의 Mirror 및 단일 Parity 예시. 누락 위치가 알려진 블록 하나의 XOR 복원을 검증했으며 당시 RAID Level을 단정하지 않는다.}}

Degraded Array가 여전히 쓰기 가능할 수도 있다. Linux MD의 degraded는 빠진 활성 멤버 수를 나타내고 sync_action은 교체 장치를 만드는 recover, 중복성을 다시 맞추는 resync, 정합성을 점검하는 check 등의 작업을 보여준다. 동기화 작업이 idle이라고 모든 장치가 정상이라는 뜻은 아니다. Rebuild와 Resync 중에는 추가 I/O가 발생해 기존 쓰기의 지연 시간이 커질 수도 있다. 모든 멤버 수가 정상화돼도 파일시스템과 앱 데이터는 별도로 검증해야 한다.

{{figure /figures/journals/raid-03-md-state.svg | 배열의 멤버 상태와 동기화 작업을 구분한다. Rebuild 완료는 Block Layer의 복구 지점이지 앱 데이터 검증 결과가 아니다.}}

다시 조사한다면 커널의 Block I/O 오류와 /proc/mdstat, 읽기 전용 배열 정보, 관련 MD sysfs 항목을 같은 시각에 남길 것이다. 논리 MD 장치와 구성 장치의 I/O 카운터를 모두 더해 워크로드의 쓰기량이라고 해석해서는 안 된다. 상태를 확인하기 위해 Repair나 강제 Assemble, Membership 변경부터 수행하는 것도 피할 것이다. 남은 장치가 유일한 데이터 사본을 가지고 있을 수도 있기 때문이다.

## 배열 위의 파일시스템

디스크 요청이 실패하고 그 오류가 논리 배열을 통해 전달되면 파일시스템은 자체 정책에 따라 대응한다. ext4에서는 errors=remount-ro를 설정할 수 있다. 처음부터 읽기 전용으로 Mount한 경우도 있으며 개별 Mount의 쓰기 제약과 Superblock의 상태도 구분해야 한다. 애플리케이션 Replica의 논리적인 Read-only 상태와 Linux Mount의 Read-only 역시 별개다.

EIO와 EROFS, ENOSPC, EACCES는 서로 다른 실패를 나타낸다. errno는 조사 범위를 좁혀 주지만 실제 장치와 커널 오류 기록을 함께 봐야 한다. Buffered Write가 성공해도 동기화 과정에서 지연된 오류가 발생할 수 있다. 이 관계는 [JBD2와 Writeback 글](/projects/linux-disk-io-journaling-writeback/)에서 좀 더 자세히 살펴봤다.

{{figure /figures/journals/raid-04-filesystem.svg | Block Device에서 파일시스템과 앱 증상으로 이어질 수 있는 경로. 오류 종류를 구분했으며 실제 장애 순서를 재현한 것은 아니다.}}

파일시스템 검사는 해당 파일시스템의 오프라인 검사와 저장장치 정합성 조건에 맞게 수행해야 한다. 이 검사가 성공해도 멤버 DB의 논리적 일관성이 검증된 것은 아니다. 반대로 DB의 손상 경고만으로 물리 디스크의 고장을 특정할 수도 없다. 복구 작업 전에는 관련 로그와 지원되는 방식의 복구 가능한 사본을 보존하는 편이 좋다.

## Raft Quorum과 디스크 중복성

etcd의 쓰기는 Leader를 통해 제안되고 Raft Log로 복제된다. 합의 규칙을 충족하면 Commit되고 State Machine에 적용된다. Raft Log는 관련 메시지를 확인하기 전에 프로토콜이 요구하는 영속성을 확보해야 한다. 따라서 멤버 프로세스가 살아 있더라도 WAL Sync가 지연되거나 실패하면 새로운 제안의 처리에 문제가 생길 수 있다. Election이나 Heartbeat에는 스케줄링과 네트워크 지연도 관여한다. WAL Sync와 Backend Commit 지표는 저장 경로의 서로 다른 지점을 보여준다.

투표 멤버 N개의 안정적인 구성에서 과반수는 floor(N/2) + 1이다. 3개면 2개, 4개면 3개, 5개면 3개가 필요하다. 과반수를 유지하며 잃을 수 있는 멤버는 각각 1개, 1개, 2개다. 하지만 수가 충분하다는 사실만으로 쓰기가 된다는 보장은 없다. 필요한 통신이 가능하고 Leader를 선출해 영속적인 진행을 할 수 있어야 한다. Learner는 투표 멤버가 아니며 Membership 변경도 합의 규칙을 따라야 한다.

{{figure /figures/journals/raid-05-quorum.svg | 3·4·5개 투표 멤버의 가상 과반수 조건과 제안부터 Apply까지의 경계. 실제 운영 클러스터의 멤버 수가 아니다.}}

그림 생성 코드에서는 세 구성의 가능한 가용 멤버 조합 56개를 모두 검사해 과반수 조건과 장애 허용 수를 확인했다. 실제 Election이나 Log Replication, 네트워크 단절 및 Membership 변경을 시뮬레이션한 것은 아니다. 3개에서 4개로 투표 멤버를 늘려도 허용 가능한 장애 수가 늘지 않는 이유를 보여준다. K3s가 embedded etcd Server를 홀수로 구성하도록 권장하는 이유이기도 하다.

## 살아 있는 멤버의 복구와 Snapshot 복원

멤버 일부가 일시적으로 응답하지 않는 경우와 과반수를 영구적으로 잃은 경우는 다르다. Quorum이 유지된다면 전체 클러스터를 복원하기보다 실패한 멤버의 복구나 교체가 필요한 상황일 수 있다. 과반수를 영구적으로 잃었다면 신뢰할 수 있는 Snapshot이나 지원되는 잔존 상태 복구 방식으로 새로운 Membership을 구성해야 할 수 있다. 실제로 사용할 수 있는 데이터와 정합성, 설치 버전에 맞춰 선택할 문제다.

Membership Reset이 검증된 백업의 복원을 의미하지는 않는다. 3월의 Reset Marker 메시지에서 실제 복원 Revision이나 다시 참여한 멤버의 정상 상태를 확인할 수는 없다. Snapshot의 출처와 지원되는 무결성 검증 결과, Revision을 확인해야 한다. Kubernetes에서는 이전 Revision을 복원할 때 Watcher Cache의 상태와 버전별 지원 복구 절차도 고려해야 한다. K3s의 백업에는 암호화된 Bootstrap 데이터를 복구하기 위한 Server Token도 필요하다. etcd Snapshot에 모든 앱의 PVC 데이터가 들어가는 것은 아니다.

{{figure /figures/journals/raid-06-recovery-gates.svg | Block Device, 파일시스템, etcd Membership 및 Revision, Kubernetes Reconciliation, 앱 데이터의 별도 복구 기준. 제안하는 검증 계획이다.}}

다시 조사한다면 커널 및 MD 상태, Datastore의 실제 파일시스템, etcd Endpoint 상태와 Health, Alarm, WAL Sync와 Backend Commit 지연 시간, API 오류를 동일한 시각에 확보할 것이다. 허용된 복구 환경에서는 기대한 객체와 Revision 상태, Controller의 Reconciliation, 애플리케이션 데이터도 확인해야 한다. 검증을 끝내기 전까지 기존 데이터와 백업 출처를 보존하고 충돌할 수 있는 과거 멤버 DB를 무작정 재사용하지 않을 것이다.

기존 기록의 일부 서비스 복구는 중요한 결과지만, 3월의 RAID Rebuild 결과와 etcd 전체 무결성은 미확인 상태다. 아래의 별도 노드 재부팅 및 Ready 복귀와도 구분했다.

## 노드가 Ready로 돌아왔던 다른 사건

비슷한 시기의 Longhorn 조사에서는 다른 모습의 장애가 있었다. 어떤 노드는 Kubernetes Condition이 Unknown으로 바뀌었고, 상태 메시지에 `Kubelet stopped posting node status`가 나타났다. 해당 노드의 K3s Agent 로그만으로는 그 이유가 분명하지 않았다.

상태를 살핀 뒤 재부팅했고, 노드는 다시 `Ready`가 됐다. 이건 직접 확인한 복구 결과다. 하지만 그 노드에 있던 Longhorn Replica까지 정상화됐다는 뜻은 아니었다. Replica의 `Stopped` 상태, 볼륨 Attach, 실제 데이터 읽기·쓰기는 각각 따로 확인해야 했다.

이 노드 사건은 etcd 장애와 동일한 날에 발생했다거나 같은 디스크 문제가 원인이었다는 자료가 아니다. 다만 Control Plane에서 보이는 노드 상태와 실제 Stateful 워크로드의 복구 시점이 일치하지 않을 수 있음을 보여주는 운영 경험이었다. 자세한 과정은 [Longhorn Replica 장애와 볼륨 복구](/projects/rokaf-stateful-storage-and-recovery/)에 별도로 적었다.

## Control Plane 복구 검증 기준

etcd를 다시 사용할 수 있게 됐더라도 Kubernetes API와 그 위의 서비스가 정상이라고 바로 결론 낼 수 없다. 반대로 API가 잠시 응답하지 않았다고 모든 워크로드의 데이터가 손상된 것도 아니다. 장애 상황에서 각 구성 요소가 남긴 표시를 어떻게 해석해야 하는지 나누어 볼 필요가 있었다.

| 확인할 항목 | 그 결과로 알 수 있는 것 | 아직 확인해야 하는 것 |
| --- | --- | --- |
| 호스트 파일시스템과 I/O | 해당 장치·마운트의 오류와 쓰기 상태 | 이 오류가 etcd에 영향을 준 시점 |
| etcd 멤버·쿼럼 | 상태 저장 클러스터가 합의할 수 있는지 | 이전 데이터의 정확성·복원 범위 |
| Kubernetes API | 샘플 읽기·쓰기 요청이 처리되는지 | Controller의 이후 조정이 완료됐는지 |
| Controller·Scheduler | 필요한 Pod와 Endpoint를 다시 처리하는지 | Stateful 볼륨·DB까지 사용 가능한지 |
| 실제 서비스 | 사용자가 대표적인 기능을 수행할 수 있는지 | 전체 과거 데이터와 장기 장애 내성 |

이 표는 그때 모든 항목에 대해 검증을 완료했다는 뜻이 아니다. 일부 환경에서 API가 다시 열리고 노드가 Ready가 된 결과는 확인했지만, 모든 etcd 멤버에 대한 무결성 점검이나 전체 애플리케이션의 복구 검증까지 수행했다는 기록은 없다.

장애 조치 중에는 복구가 우선일 수 있다. 다만 원인을 규명해야 할 때는 무엇을 변경했는지뿐 아니라 **변경 전의 실패 상태를 어디까지 기록했는지**가 중요했다. 여러 컴포넌트를 동시에 재시작하거나 문제가 있는 데이터를 성급히 지우면 되돌릴 수 없는 상태가 될 수도 있다. 그래서 etcd의 복구 과정이나 내부 제어면 구성을 이 글에 명령 순서로 옮기지 않았다.

## 같은 시간에 남아 있어야 할 로그

다시 이 상황을 조사한다면 우선 한 클라이언트에서 실제 Kubernetes API 요청이 실패한 시각을 기록할 것이다. 그때 각 etcd 멤버가 어떤 상태였는지, 쿼럼이 형성됐는지, 관련 호스트의 쓰기 오류나 파일시스템 상태가 어땠는지 함께 확인해야 한다. 장애가 일어난 뒤 한참 지나서 정상화된 상태만 수집하면 선후관계를 놓치기 쉽다.

etcd 로그와 커널의 디스크 I/O 메시지, 마운트 상태, Kubernetes API 응답 결과는 다른 계층의 기록이다. 서로 시간대가 맞지 않으면 특정 오류가 먼저 발생했다는 주장을 하기 어렵다. 예를 들어 API가 실패한 직후 디스크 관련 메시지가 나타났다고 하더라도, 그 메시지가 이미 있던 API 장애의 원인인지 결과와 무관한 다른 사건인지는 별도로 입증해야 한다.

기록을 공개할 때는 실제 노드 번호와 내부 주소, 멤버 구성, 데이터 경로, 복구 명령을 제외했다. 대신 **어떤 증거가 어떤 단계의 문제를 확인하는지**에 집중했다. 구체적인 복구 조작을 따라 하게 하는 것보다, 실제 로그를 비교할 기준을 남기는 편이 이 글의 목적과 맞았다.

## 지금까지 확인한 범위

K3s의 **etcd 불안정·손상 의심과 디스크 Read-only 증상**을 조사했고, 일부 상황에서는 서비스 접근을 복구했다. 별도의 노드 장애에서는 `Kubelet stopped posting node status` 이후 `Ready` 복귀도 확인했다. 다만 특정 디스크 오류가 etcd와 모든 API 장애를 일으킨 하나의 원인이었는지는 확인되지 않았다. 호스트 I/O·파일시스템 로그와 etcd 멤버 상태를 같은 시간대에 연결해 보는 검증이 남아 있다.

## 관련 기록

- [Longhorn Replica 장애와 볼륨 복구](/projects/rokaf-stateful-storage-and-recovery/)
- [온프레미스 K3s 플랫폼 구축·운영](/projects/independent-on-premises-k3s-platform-engineering/)
- [CoreDNS·MetalLB VIP 접속 장애 조사](/projects/rokaf-dns-vip-open-investigations/)

- [Linux MD documentation](https://docs.kernel.org/admin-guide/md.html) · [ext4 error policies](https://docs.kernel.org/admin-guide/ext4.html) · [etcd FAQ](https://etcd.io/docs/v3.5/faq/) · [etcd performance](https://etcd.io/docs/v3.5/op-guide/performance/) · [etcd disaster recovery](https://etcd.io/docs/v3.5/op-guide/recovery/) · [K3s embedded etcd HA](https://docs.k3s.io/installation/ha-embedded/) · [K3s snapshot and restore](https://docs.k3s.io/cli/etcd-snapshot) · [K3s backup requirements](https://docs.k3s.io/datastore/backup-restore).
