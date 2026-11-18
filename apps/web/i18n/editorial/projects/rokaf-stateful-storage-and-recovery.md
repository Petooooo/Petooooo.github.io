Longhorn에서 Replica 수를 2개에서 1개로 줄였더니 볼륨 상태가 바로 **Healthy**로 바뀌었다.

처음에는 문제가 해결된 것처럼 보였다. 그런데 Replica 목록에는 여전히 두 개가 남아 있었고, 그중 하나는 정상으로 돌아오지 않았다. 다시 생각해보면 Longhorn이 알려준 것은 “두 개의 정상 복제본을 복구했다”가 아니었다. **내가 목표를 하나로 낮췄으니 그 조건은 만족했다**는 뜻이었다.

2026년 초, 폐쇄망 K3s에서 영속 데이터를 운영하며 여러 번 비슷한 상황을 만났다. Replica는 Unknown이나 Stopped로 표시됐고, 어떤 볼륨은 Detach와 Attach 사이에서 움직이지 않았다. 노드는 다시 Ready가 됐지만 그 노드에 있던 Replica가 바로 정상으로 돌아온 것은 아니었다.

서로 다른 날에 일어난 장애들이라 하나의 사건으로 묶어 복구 순서를 재구성할 수는 없다. 대신 그때마다 무엇을 실제로 확인했고, 무엇을 확인하지 못했는지 남겨보려 한다. 여기서는 내부 PVC 식별자, 노드 번호, 구체적인 디스크 경로와 용량은 공개하지 않는다.

## Healthy라는 글자에 안심했던 순간

1월 말, 특정 Longhorn 볼륨의 상태가 Degraded였다. 설정된 Replica 수는 2개. 하나는 Healthy였지만 다른 하나는 Unknown이었다. 문제가 생긴 Replica의 로그를 UI에서 살펴보려고 했으나 당시 화면에서는 Delete 외에 유용한 로그 조회 메뉴를 찾지 못했다.

정확히 어느 단계에서 멈췄는지부터 알아야 했지만, 먼저 볼륨 상태를 바꿔볼 방법을 살펴봤다. 설정된 Replica 수를 2개에서 1개로 낮추자 볼륨이 Healthy로 표시됐다.

여기서 헷갈리기 쉬운 것은 세 가지다.

- **원하는 Replica 수**는 이제 하나였다.
- **볼륨 상태**는 바뀐 목표에 따라 Healthy가 됐다.
- **실제로 안전하게 사용할 수 있는 복제본**이 다시 두 개가 됐다는 증거는 없었다. 목록에 보이는 옛 Replica 객체는 여전히 의심스러운 상태였다.

{{figure /figures/journals/longhorn-desired-vs-actual-replicas.svg | Replica 목표를 2개에서 1개로 낮추기 전과 후의 관측 결과를 나란히 비교했다. 초록색 상태 표시가 원래의 이중 복제를 되찾았다는 의미는 아니었다. 실제 노드 배치도는 아니다.}}

당장 서비스를 다시 붙여야 하는 상황이라면 복제본 하나로 운용하는 선택이 필요할 수도 있다. 하지만 그때부터는 다음 장애를 막아줄 여분의 복제본이 없다. 같은 볼륨을 Healthy라고 부르더라도 이전과 같은 수준의 장애 내성을 갖춘 것은 아니다.

당시에는 유일하게 Healthy로 보이던 Replica에서 **Deleting Snapshot** 작업도 진행 중이었다. 내가 직접 시작하지 않은 작업이었다. 이게 장애의 원인이었다거나 데이터가 망가졌다고 확인한 것은 아니다. 다만 마지막으로 신뢰할 만한 복제본이 작업 중인 상태에서 다른 Replica를 삭제하거나 강제로 정리하는 것은 더 신중해야 했다.

UI에서 보기 싫은 오류 하나를 없애는 것보다, **다음 작업이 실패하면 어느 데이터를 가지고 복구할 수 있는지**가 더 중요했다.

## 파일이 남아 있는데 Replica는 Stopped였다

이후 이어진 조사에서는 문제가 있는 Replica가 놓여 있던 노드가 살아 있었고 디스크에도 `.img` 파일이 남아 있었다. 그런데 Longhorn에서 확인한 상태는 여전히 Stopped였다.

Offline Replica Rebuilding을 활성화해보기도 했다. 설정을 켠 뒤 다시 확인했지만 관측한 시점에는 Stopped 상태가 바뀌지 않았다.

처음에는 파일이 그대로 있으니 그 파일을 다시 읽게 하면 되지 않을까 생각했다. 하지만 디스크에 파일이 있다는 사실과 Longhorn이 정상 Replica로 받아들일 수 있다는 사실은 다르다. 파일을 구성하는 Snapshot의 관계가 유효한지, 마지막 쓰기가 어디까지 반영됐는지, 다른 복제본과 일관성이 맞는지 확인해야 한다.

Longhorn 문서에서도 Offline Rebuilding은 아무 상황에서나 강제로 시작되는 기능이 아니다. 지원 버전과 설정에 따라, Detach된 Degraded 볼륨인지, 재사용 가능한 Replica가 있는지, 복제본을 만들 디스크와 Instance Manager가 준비됐는지 등을 확인한다. **설정을 Enabled로 바꾸는 것과 실제 Rebuilding이 시작되는 것은 별개의 결과**다.

한 번은 Replica를 지우려 했을 때 Longhorn이 다른 정상 복제본이 없고 현재 Replica가 복구할 데이터를 가지고 있을 수 있다는 경고와 함께 삭제를 거부하기도 했다. 그때는 삭제가 안 되는 것이 오히려 중요한 안전장치로 보였다.

Replica 객체를 없애면 목록이 깨끗해질지는 모른다. 하지만 그 안에 유일하게 남은 복구 가능한 데이터가 있다면 그 조작은 되돌릴 수 없는 일이 될 수도 있다.

남아 있는 기록에서 확인할 수 있는 결과는 분명하다. 파일은 존재했고, Replica는 Stopped였으며, Offline Rebuilding을 켜도 즉시 정상화되지 않았다. **마지막까지 두 개의 Healthy Replica가 복구됐다는 검증 결과는 없다.**

## 노드가 돌아온다고 데이터까지 돌아오는 것은 아니다

비슷한 시기에 다른 노드에서는 Kubernetes의 Condition이 모두 Unknown으로 바뀌었다. 상태 메시지에는 `Kubelet stopped posting node status`가 나왔다. 그런데 K3s Agent의 Journal은 그만큼 명확한 이상을 보여주지 않았다.

그 노드의 디스크에는 중요한 Longhorn Replica 데이터가 남아 있었다. 무작정 디렉터리를 정리하거나 초기화할 수 있는 상황이 아니었다.

상태를 확인한 뒤 재부팅을 진행했고, 노드는 다시 Ready로 돌아왔다.

그건 분명 의미 있는 결과였다. 하지만 그 순간 확인한 것은 **Control Plane이 다시 그 노드를 정상적으로 볼 수 있게 됐다는 사실**이다. Replica Engine이 정상으로 붙었는지, 볼륨을 Mount할 수 있는지, 이전 데이터로 읽기·쓰기가 가능한지는 별도로 봐야 한다.

예전에는 노드가 복귀하고 Pod가 Running이면 장애가 끝난 것처럼 느꼈다. 실제로는 그 아래 여러 계층에서 복구 시간이 따로 흘렀다. 노드를 살리는 일과 그 노드에 있던 데이터를 다시 서비스에 연결하는 일은 서로 다른 작업이었다.

## Detaching을 끝내지 못한 볼륨

1월의 다른 사건에서는 큰 Longhorn 볼륨이 Detaching 상태에서 벗어나지 못했다. Faulted나 NotReady 표시가 함께 나타났고, 결국 Pod가 필요한 볼륨을 붙이지 못해 정상 실행으로 넘어가지 못했다.

Instance Manager 로그를 확인하다가 다음 문구를 만났다.

`failed to unregister process ... since it is state stopping rather than stopped`

실제 Process와 PVC 식별자는 제외했다. 여기서 중요한 것은 `stopping`과 `stopped`의 차이다. Longhorn은 프로세스를 등록 해제하려 했지만, Process Manager가 보는 실제 상태는 아직 완전히 멈춘 것이 아니었다.

Pod가 스케줄링되지 않는 문제라고만 생각했다면 이 로그까지 보지 못했을 것이다. Kubernetes가 어느 노드에 Pod를 놓는지와 Longhorn이 Engine·Replica 프로세스를 관리하는 일은 서로 다른 계층이다.

{{figure /figures/journals/longhorn-attachment-fault-domains.svg | 애플리케이션 요청에서 파일시스템, CSI, Attachment 상태, Instance Manager, 실제 Replica 파일까지 계층을 펼쳤다. Detaching과 stopping, Busy Mount, Node Ready가 서로 다른 위치의 증거라는 점을 보여준다.}}

나중에 Force Detach를 시도했던 별도 상황에서는 Port가 이미 사용 중이라는 오류를 보기도 했다. 또 다른 노드 정리 과정에서는 Longhorn CSI의 `globalmount` 경로를 지우려 하자 `Device or resource busy`가 발생했다.

이런 현상을 보면 Force Detach가 끝났다고 해서 모든 프로세스와 파일시스템의 사용 관계가 즉시 사라진다고 생각해서는 안 된다. 장치나 Mount를 누가 붙잡고 있는지, 이전 Engine 프로세스가 완전히 종료됐는지, CSI가 남겨둔 상태는 무엇인지 확인해야 한다.

그렇다고 포트 충돌, Busy Mount와 1월의 `stopping` 오류가 모두 같은 근본 원인이었다고 말할 수는 없다. 서로 다른 시점의 관측을 비슷한 유형이라는 이유로 하나의 사건으로 만들어서는 안 된다.

당시 Instance Manager를 재시작하는 방안도 검토했다. 하지만 실제로 재시작한 뒤 Attach와 Replica 재구축, 전체 데이터 검증이 성공했다는 최종 결과는 남아 있지 않다. 검토한 해결책과 확인된 복구 결과를 구분해야 한다.

## PVC가 Bound여도 사용자는 파일을 못 열 수 있다

장애를 조사할 때 여러 상태값이 한꺼번에 눈에 들어온다. Pod는 Running인지, PVC는 Bound인지, Longhorn 볼륨이 Attached인지, Replica는 Healthy인지. 하나하나 중요하지만 어느 하나만으로 최종 복구를 증명할 수는 없었다.

| 화면이나 로그에서 본 상태 | 우선 확인할 영역 | 그것만으로 알 수 없는 것 |
| --- | --- | --- |
| Pod가 스케줄링되고 PVC가 Bound | CSI Attach·Mount 이벤트 | 애플리케이션이 실제 데이터를 사용하는지 |
| 볼륨 Detaching·Faulted | Longhorn Attachment 상태와 Engine 로그 | 디스크 데이터 자체가 손상됐는지 |
| Process가 stopping에 멈춤 | Instance Manager의 프로세스 생명주기 | 강제 종료해도 안전한지 |
| `globalmount`가 Busy | 열린 Mount와 장치 사용 주체 | Replica를 삭제해야 하는지 |
| Node가 Ready로 복구 | Kubelet·Control Plane 연결 | Replica가 최신 데이터로 복구됐는지 |
| Replica 목표 2→1 이후 Healthy | 실제 정상 Replica 수와 재구축 계획 | 예전의 이중 복제가 복구됐는지 |

이 때문에 한 번에 여러 설정을 바꾸는 것이 점점 부담스러웠다. Force Detach를 하기 전에 기존 Writer가 아직 디바이스를 사용하고 있는지 봐야 한다. Replica를 지우기 전에 남아 있는 데이터가 복구에 필요한지 확인해야 한다. 노드를 재시작하기 전에 문제를 설명해줄 로그와 상태를 확보해야 한다.

장애를 빨리 종료하는 것도 중요하지만, 마지막 데이터를 잃는 방식으로 종료해서는 안 된다.

## 복구를 위해 남겨둬야 하는 공간

Replica를 하나로 줄이니 볼륨이 Healthy가 됐던 경험은 용량을 계획하는 방식에도 영향을 줬다.

평상시에 데이터를 저장할 디스크만 있으면 충분한 것이 아니었다. 장애가 나면 **사라진 Replica를 다시 만들 공간**이 필요하다. 남은 Replica에서 데이터를 읽고 다른 노드에 쓰는 동안 네트워크와 디스크 I/O도 사용한다. Snapshot을 정리하거나 Replica를 재구축하는 작업이 평소의 데이터베이스 I/O와 경쟁할 수도 있다.

특히 데이터가 큰 볼륨이라면 여유 디스크가 있다는 말만으로 재구축이 가능하다고 판단할 수 없다. 어느 노드가 복제본을 받을 수 있는지, 해당 디스크가 스케줄링 가능한지, 실제 사용량과 Snapshot 데이터가 얼마나 되는지, 중간에 또 장애가 나면 어떻게 되는지를 봐야 한다.

이것이 재구축에 필요한 일종의 복구 예산이었다. 단순히 Replicas를 2로 설정했다고 해서 그 목표를 언제든 복원할 수 있다는 뜻은 아니었다.

StorageClass를 선택할 때도 비슷한 고민을 했다. 작은 단일 서비스는 Longhorn으로 볼륨을 옮겨 붙일 수 있다는 장점이 있다. 하지만 ClickHouse처럼 자체 Replication을 수행하는 데이터베이스라면 아래쪽 블록 볼륨의 복제가 추가적인 I/O와 복구 순서를 만들어낼 수 있다. 분산 MinIO도 어떤 계층이 실제 데이터의 사본을 책임질지 먼저 정해야 한다.

Longhorn이 나쁘다거나 로컬 디스크가 언제나 낫다는 이야기는 아니다. **동일한 데이터를 여러 계층에서 복제하는 비용과 책임을 이해하고 선택해야 한다**는 뜻이다.

## Healthy 다음에 확인하고 싶었던 것

같은 종류의 장애를 다시 만난다면 복구 여부를 몇 가지로 나눠 적고 싶다.

먼저 노드가 살아 있는가. 다음으로 볼륨이 안전하게 Attach되고 Mount됐는가. 그다음 원래 의도했던 수의 **실제로 사용 가능한 Replica**가 회복됐는가. 애플리케이션은 자신의 로그와 데이터를 정상적으로 읽고 쓰는가. 마지막으로 실제 클라이언트가 기대한 결과를 받는가.

이 단계가 끝나도 전체 데이터 무결성 검증이나 백업에서의 복원 시험은 별도로 필요하다. Replica가 두 개라고 해서 실수로 삭제한 데이터가 이전 상태로 돌아오지는 않는다. Snapshot과 Backup은 또 다른 복구 목적을 가진다.

그때 내가 확인했던 것은 노드가 Ready로 돌아온 사실, Replica 목표를 하나로 낮춘 뒤 볼륨 상태가 Healthy가 된 사실, 그리고 Stopped·Unknown 상태와 `stopping` 로그가 실제로 존재했다는 사실이었다. **두 개의 정상 Replica가 모두 재구축되고 애플리케이션의 데이터 무결성까지 검증됐다는 기록은 없다.**

결국 가장 조심해야 할 순간은 빨간 오류가 보일 때만이 아니었다. 스스로 복제 목표를 낮춘 뒤 초록색 표시를 보고 문제가 끝났다고 판단하려던 순간도 그만큼 위험했다.

## 함께 읽을 기록

- [MinIO 이전과 객체 대조](/projects/rokaf-object-storage-migration/)
- [데이터베이스 복제·마이그레이션](/projects/rokaf-database-ha-and-langfuse-migrations/)
- [K3s 플랫폼 운영 판단](/projects/independent-on-premises-k3s-platform-engineering/)

## 참고 문서

- [Longhorn — Offline Replica Rebuilding](https://longhorn.io/docs/1.13.0/advanced-resources/rebuilding/offline-replica-rebuilding/) — 지원 버전과 적용 조건은 실제 설치 버전에 맞게 확인해야 한다.
- [Longhorn — Replica Rebuilding](https://longhorn.io/docs/1.13.0/advanced-resources/rebuilding/)
- [Longhorn — Volume Attachments](https://longhorn.io/docs/1.13.0/advanced-resources/volumeattachment/)
- [Longhorn — Volume Recovery](https://longhorn.io/docs/1.13.0/high-availability/recover-volume/)
