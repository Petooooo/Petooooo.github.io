2026년 3월 19일, K3s의 스토리지 문제를 살펴보던 중 로그 수집 시스템의 Ingester와 Querier가 모두 `CreateContainerError` 상태에 빠진 것을 발견했다. 애플리케이션이 실행된 뒤 죽은 것이 아니라 containerd가 컨테이너를 생성하는 과정에서 오류가 발생했다.

```text
failed to create containerd container:
  failed to stat parent:
    stat .../snapshots/<id>/fs: no such file or directory
```

내부 경로와 Snapshot 식별자는 제외하고 오류의 의미만 남겼다. 당시 궁금했던 것은 런타임이 사용할 부모 Snapshot을 알고 있으면서도 왜 그 파일시스템 디렉터리를 찾지 못하는가였다. Registry에 연결되지 않거나 애플리케이션 자체가 종료되는 것과는 다른 문제였다.

이후 Digest와 함께 `committed`라는 출력이 남아 있지만 어떤 명령의 결과였는지, 두 워크로드가 모두 복구됐는지까지는 확인되지 않는다. 당시 설치된 containerd의 정확한 버전과 최종 상태도 남아 있지 않다. 앞서 Longhorn의 Attach 및 Mount 오류가 있었지만 그것이 Snapshot 디렉터리 누락을 유발했다고 단정할 근거는 없다.

## OCI 이미지와 압축을 푼 파일시스템

Registry는 콘텐츠의 해시를 주소로 사용하는 객체를 배포한다. OCI Image Manifest는 실행 설정을 담은 Config와 순서가 정해진 Layer 목록을 가리킨다. Content Store에 압축된 Layer Blob이 모두 존재하더라도 실제 마운트할 파일시스템이 준비됐다는 뜻은 아니다. Config에는 압축을 풀어 얻은 Layer의 Digest인 DiffID가 순서대로 기록된다. 압축된 Blob의 Digest와 DiffID, 여러 변경 내용을 순서대로 적용한 ChainID는 서로 다른 대상을 식별한다.

containerd는 Unpack 과정에서 Snapshotter와 Diff Applier를 이용해 Layer를 차례대로 적용한다. 처음에는 부모가 없는 Active Snapshot을 준비하고 첫 번째 Layer를 적용해 Commit할 수 있다. 다음 Layer는 그 Committed Snapshot을 부모로 둔 Active Snapshot에 적용한다. 각 단계에서 Commit된 Snapshot은 이후 재사용할 수 있는 논리적으로 불변인 파일시스템 상태가 된다. 컨테이너를 생성할 때에는 마지막 Committed Snapshot을 부모로 하는 새로운 쓰기 가능한 Active Snapshot을 준비한다. 이미 적용한 이미지 전체를 컨테이너마다 다시 만들 필요가 없는 이유다.

{{figure /figures/journals/overlay-01-content-flow.svg | Content Store의 Manifest와 Blob, Unpack으로 만들어진 Committed Snapshot, 컨테이너의 Active Snapshot은 각각 다른 데이터다.}}

이 차이를 이해하는 데 ChainID의 계산 방식이 도움이 된다. 두 Layer의 DiffID를 D0, D1이라고 하면 첫 번째 ChainID는 D0이고, 다음 ChainID는 D0와 공백 하나, D1을 이어 붙인 문자열의 Digest다. 이때 각 Digest의 알고리즘 접두사도 포함된다. 같은 Layer라도 적용 순서를 바꾸면 일반적으로 ChainID가 달라진다. Snapshotter가 내부 디렉터리에 붙이는 숫자 ID는 이와 또 다른 식별자다. 이미지 이름이나 Digest를 보고 디렉터리 번호를 추측해서는 안 된다.

설명에 사용한 작은 예제에서는 내용이 정해진 Tar Archive 두 개를 생성하고 하나를 압축해 SHA-256을 계산했다. 압축 전후 Digest가 다르고, Layer 순서에 따라 ChainID가 달라지며 동일한 입력으로 계산을 반복하면 같은 결과가 나오는지 검증했다. 실제 Registry에서 이미지를 받아 Unpack하거나 속도를 측정한 실험은 아니다.

## OverlayFS가 여러 디렉터리를 하나로 보여주는 방식

일반적인 쓰기 가능한 OverlayFS Mount는 순서가 있는 Lower Directory와 Upper Directory, Work Directory를 사용한다. 컨테이너가 보는 것은 이들을 합쳐 보여주는 Merged Mount다. 같은 이름의 일반 파일이 있으면 보통 Upper의 파일이 우선하고, 디렉터리는 양쪽의 이름을 합쳐 보여줄 수 있다. Lower끼리 이름이 겹치면 위쪽에 있는 Layer가 오래된 Layer보다 우선한다.

Workdir은 OverlayFS가 내부 작업에 사용하는 공간이다. 처음에는 비어 있어야 하고 Upperdir과 같은 파일시스템에 있어야 한다. 컨테이너에 파일을 보여주는 또 하나의 Layer는 아니다. 정확한 Mount 옵션은 Snapshotter와 커널의 구현에 따라 다르며, 구성에 따라 Overlay Mount 대신 Bind Mount가 쓰이기도 한다.

{{figure /figures/journals/overlay-02-layer-layout.svg | 두 Lower Layer를 참조하는 쓰기 가능한 Overlay. Workdir은 Upperdir의 보조 작업 공간이며 파일을 보여주는 Layer가 아니다.}}

이 구조에서는 이미지가 크더라도 컨테이너마다 같은 크기의 쓰기 공간이 필요한 것은 아니다. 두 컨테이너가 동일한 Committed Snapshot을 공유하면서 각자 Upper Directory를 가질 수 있다. 이미지 저장 공간과 초기 준비 비용을 줄일 수 있지만, 공유하는 Lower Directory가 두 컨테이너의 공통 의존성이 된다는 점도 중요하다.

## Copy-up과 Whiteout, 쓰기 비용

Lower에 config.txt라는 파일이 있다고 생각해 보자. 읽을 때에는 전체 파일을 Upper에 복사하지 않아도 된다. 일반적인 데이터 Copy-up 경로에서는 파일을 쓰기 위해 열면 필요한 메타데이터와 파일 내용을 Upper로 복사한 후 그곳에서 수정한다. metacopy 같은 옵션이나 메타데이터만 바꾸는 경우에는 세부 동작이 달라질 수 있다. 여기서는 일반적인 데이터 Copy-up을 가정했다.

Merged Mount에서 Lower에 있던 파일을 지우는 경우에도 공유 중인 원본 Layer를 직접 지워서는 안 된다. OverlayFS는 Upper에 Whiteout을 만들어 그 이름을 가린다. Upper Directory를 Opaque로 표시하면 Lower Directory의 내용이 보이지 않도록 할 수도 있다. OCI Layer Archive에도 .wh.filename 같은 삭제 표현이 있지만, Archive에 기록되는 형식과 커널 OverlayFS의 실제 저장 형식은 동일하지 않다.

{{figure /figures/journals/overlay-03-copy-up-whiteout.svg | Lower에서 읽기, Upper 복사본 수정, Whiteout으로 가리기의 세 단계. Lower의 원본 데이터는 그대로 남는다.}}

큰 Lower 파일을 일부만 수정하더라도 첫 쓰기에서 발생하는 공간 및 I/O 비용은 애플리케이션이 실제 변경한 크기보다 클 수 있다. 이미 Upper에 복사본이 있다면 이후 쓰기에서 Lower 파일 전체를 다시 복사할 필요는 없다. 컨테이너의 쓰기 Layer에서 발생하는 I/O와 별도 Mount된 Volume의 I/O를 구분해야 하는 이유이기도 하다. 그림 생성 코드에는 읽기 우선순위, 복사와 삭제 표시를 확인하는 간단한 메모리 모델을 포함했다. 실제 OverlayFS 구현이나 커널의 Copy-up 성능을 측정한 결과는 아니다.

## Snapshot 메타데이터와 실제 디렉터리의 불일치

Snapshotter는 Snapshot의 Key, 종류, Parent와 내부 Storage ID를 관리한다. Committed Snapshot은 이후 Snapshot의 부모로 재사용되고 Active Snapshot은 변경 가능한 준비 상태나 컨테이너의 쓰기 상태가 된다. 논리적인 관계와 실제 저장 디렉터리가 서로 일치해야 한다. 메타데이터에서 부모 ID를 찾았다는 사실만으로 런타임의 Mount Namespace에서 그 디렉터리에 접근할 수 있다는 것을 증명하지는 못한다.

containerd의 공개 Overlay Snapshotter 소스를 살펴보면 임시 디렉터리를 만들고 트랜잭션 안에서 Snapshot 메타데이터를 생성한다. 일반적인 소유권 상속 경로에서는 첫 번째 부모 ID에 대응하는 Upper Directory에 stat을 호출해 UID와 GID를 얻고 새로 준비한 fs 디렉터리에 적용한다. 부모 디렉터리 조회에 실패하면 당시 관측했던 부모 stat 오류와 같은 형태로 오류를 반환한다. 새로운 Mount 정보를 반환하기 전의 실패이며 준비 과정에서 만든 상태도 정리한다. 버전과 ID Mapping 구성에 따라 세부 구현은 달라질 수 있다. 당시 바이너리나 Stack Trace를 복원한 것이 아니라 공개 소스에서 관측 오류와 일치하는 경로를 찾아 설명한 것이다.

{{figure /figures/journals/overlay-04-parent-dependency.svg | 하나의 Committed Parent를 공유하는 두 가상의 Active Snapshot. 부모 관계를 찾아도 대응 디렉터리가 런타임의 파일시스템에서 보이지 않을 수 있다.}}

따라서 당시 오류는 막연한 컨테이너 생성 실패보다 조사 범위를 더 좁혀 준다. 필수 경로를 조회하지 못했다는 뜻이지, 그 경로가 왜 없어졌는지까지 알려주지는 않는다. 런타임 외부에서의 삭제, 불완전한 복원, Backing Mount 누락 등은 가능한 설명일 뿐 확인된 원인은 아니다. 경로가 없다는 사실 자체가 물리 디스크 고장을 증명하는 것도 아니다.

작은 재현 예제에서는 임시 디렉터리와 Snapshot 이름을 Storage ID에 연결하는 딕셔너리를 사용했다. 두 자식이 같은 실제 부모 디렉터리를 참조하도록 만든 뒤 비어 있는 가상의 부모 디렉터리만 제거했다. 메타데이터는 그대로인데 두 자식의 stat이 모두 FileNotFoundError로 실패하고 독립된 다른 부모의 조회는 여전히 성공하는지 확인했다. 일반 파일시스템 호출을 이용해 논리적 불일치를 재현한 것이며 containerd를 실행하거나 OverlayFS를 Mount하지 않았다.

## 컨테이너 생성 단계와 실패 지점

Pod가 노드에 배치된 이후에도 이미지 확인, 다운로드, Unpack, Active Snapshot 준비, Root Filesystem Mount, 프로세스 실행 등의 과정이 남아 있다. kubelet이 보여주는 상태와 이벤트의 자세한 메시지를 함께 봐야 한다. 당시 부모 stat 오류는 Snapshot 준비 단계의 문제를 가리켰다. 애플리케이션 코드가 실행됐을 필요조차 없는 오류이므로 처음부터 애플리케이션 코드의 문제로 접근할 이유는 없었다.

{{figure /figures/journals/overlay-05-creation-boundary.svg | 컨테이너 생성의 논리적 단계와 부모 stat 오류의 위치. 실제 실행 Trace는 아니며 CRI 구현에 따라 단계가 합쳐지거나 순서가 달라질 수 있다.}}

이미지 Pull 성공만으로 복구를 판단하기 어려운 이유도 여기에 있다. 필요한 Blob이 이미 캐시에 있거나 Unpack 과정에서 기존 Snapshot 메타데이터를 재사용할 수 있다. Pull이 성공해도 필요한 모든 디렉터리가 실제로 존재한다고 볼 수 없다. Commit이 성공했다는 출력도 새로운 컨테이너의 Root Filesystem을 Mount하고 애플리케이션이 실행됐거나 영속 Volume이 연결됐음을 증명하지는 못한다.

다시 같은 상황을 만난다면 먼저 이미지 식별자, 발생 노드, 자세한 CRI 오류, 런타임 버전, 실제 Snapshotter 및 Snapshot 목록을 읽기 전용으로 확보할 것이다. 참조 경로가 런타임의 Mount Namespace에서 어떻게 보이는지, 실제 Backing Filesystem이 정상인지, 다른 컨테이너도 같은 부모를 공유하는지 살펴야 한다. Registry 접근 문제는 [CI 이미지 배포 기록](/projects/rokaf-private-artifacts-and-ci/)에서, 스토리지와 제어면의 가용성 문제는 [Control Plane 장애 기록](/projects/rokaf-control-plane-incident-log/)에서 별도로 다뤘다.

## 이미지 복구와 애플리케이션 데이터 보존

이미지에 필요한 Blob과 Config를 신뢰할 수 있는 출처에서 확보할 수 있다면 이미지를 다시 구성할 수 있다. 하지만 Active Writable Layer에는 그 컨테이너만 가지고 있는 데이터가 있을 수 있으므로 제거하면 해당 데이터가 사라진다. PVC Volume은 이미지 Snapshot 체인 밖에서 별도의 Attach 및 파일시스템 생명주기를 가진다. 일부 임시 Volume도 별도 Mount다. 이는 데이터의 소유권과 복구 책임에 관한 구분이지 애플리케이션이 항상 의도한 위치에 데이터를 쓴다는 보장은 아니다.

{{figure /figures/journals/overlay-06-recovery-boundaries.svg | Blob, Committed Snapshot, Writable Layer, PVC의 복구 책임과 검증 기준. 컨테이너가 실행 중이라는 사실만으로 영속 데이터의 정상 상태까지 증명할 수는 없다.}}

Garbage Collection은 눈에 보이는 디렉터리 이름이 아니라 런타임의 참조와 Lease를 기준으로 이뤄진다. containerd의 논리적 Remove와 Snapshotter의 Cleanup도 메타데이터를 기준으로 조정된다. 디렉터리를 직접 지우면 사용 중인 참조만 남을 수 있다. 누락된 ID와 같은 이름으로 빈 디렉터리를 만들어도 단순 존재 확인을 통과할 뿐 실제 Layer의 내용은 돌아오지 않는다. 고유한 데이터와 일관된 상태 기록을 먼저 보존한 뒤, 유지보수 범위를 정하고 설치 버전이 지원하는 복구 절차를 적용하는 것이 좋다.

복구 여부도 나눠서 확인할 것이다. 올바른 이미지 콘텐츠가 있는가, Snapshot 체인이 사용 가능한가, 새로운 Root Filesystem을 준비할 수 있는가, 애플리케이션이 실행되는가, 의도한 Volume의 데이터가 정상인가. Backing Mount가 빠진 상태에서 다른 파일시스템에 Unpack을 다시 수행하면 오히려 문제를 키울 수 있다. 런타임 저장 경로를 옮긴 상황이라면 설정과 실제 Mount가 일치하는지도 확인해야 한다. 3월 19일 사건에서 이 항목들을 모두 검증했다는 기록은 없다.

이번 경험에서 중요했던 것은 Registry의 이미지, 논리적인 Snapshot 기록, 실제 파일시스템 변경 내용을 담은 디렉터리, 실행 중인 애플리케이션이 각기 다른 조건으로 존재하고 동작한다는 점이었다. 어느 경계에서 실패했는지 이해하면 다음에 무엇을 확인해야 할지 좁힐 수 있다.

## 관련 기록과 참고 자료

- [Longhorn과 영속 스토리지 복구](/projects/rokaf-stateful-storage-and-recovery/) · [스토리지 배치와 장애 영역](/projects/rokaf-storage-placement-and-failure-domains/) · [Linux 메모리 압박](/projects/rokaf-memory-pressure-and-service-recovery/)
- [OCI Manifest](https://specs.opencontainers.org/image-spec/manifest/) · [OCI Config와 ChainID](https://github.com/opencontainers/image-spec/blob/main/config.md) · [OCI Layer 변경 형식](https://specs.opencontainers.org/image-spec/layer/)
- [containerd Content Flow](https://github.com/containerd/containerd/blob/main/docs/content-flow.md) · [Overlay Snapshotter 소스](https://github.com/containerd/containerd/blob/main/plugins/snapshots/overlay/overlay.go) · [Linux OverlayFS 문서](https://docs.kernel.org/filesystems/overlayfs.html)
