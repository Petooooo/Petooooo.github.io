별도의 시스템 디스크와 데이터 디스크를 가진 K3s 노드에서 워크로드를 운영하며 이미지 Layer와 런타임 데이터가 시스템 디스크를 차지하는 문제를 줄이고 싶었다. 처음에는 저장 경로 하나를 바꾸면 될 것 같았지만, 실제로는 서로 다른 주체가 관리하는 데이터와 참조 관계까지 생각해야 했다.

2025년 11월 27일 containerd의 Root를 지정하려고 K3s 옵션을 사용했을 때 다음 오류가 발생했다.

```text
flag provided but not defined: -containerd-root-dir
```

앞선 11월 22일 기록에는 이미 /data 아래의 별도 K3s Data Directory를 사용한 노드가 있었다. 이후 운영 기록에서도 /data 아래의 설정이 확인된다. 다만 이전 디스크에서 데이터를 모두 복사하고 무결성을 검증했다는 뜻은 아니다. 12월 1일에는 containerd의 임시 Mount 경로가 없다는 오류를 논의했지만 당시 원본 출력 전체와 최종 해결 결과는 남아 있지 않다. 1월 4일에는 K3s Agent에 containerd 관련 옵션을 전달하려다가 또 오류를 만났다. 1월 18일에는 별도로 진행한 Docker Overlay 이전이 잘 됐다고 기록했고, kubelet의 Volume 경로는 여전히 /var/lib/kubelet/pods 아래에서 확인했다.

Docker 이전이 성공했다는 사실만으로 K3s의 embedded containerd나 kubelet, 영속 Volume까지 모두 옮겨졌다고 볼 수는 없다. 당시 모든 노드의 복사 전후 목록과 검증 기록은 남아 있지 않다. 이번에는 확인한 설정과 문제를 바탕으로 저장 경로가 실제로 어떤 관계를 가지며, 이전 시 무엇을 검증해야 하는지 정리했다.

## 런타임의 저장 영역은 하나가 아니다

containerd는 영속 데이터를 두는 Root와 실행 중 상태를 관리하는 State를 구분한다. Root에는 Content Blob, Snapshot 디렉터리와 메타데이터 DB 등 Plugin의 영속 데이터가 들어간다. State에는 Socket, 프로세스 및 Mount 관련 실행 상태 등이 있다. 독립적으로 실행하는 containerd의 일반적인 기본 경로는 /var/lib/containerd와 /run/containerd지만, K3s처럼 다른 시스템에 내장된 구성에서는 경로가 달라질 수 있다.

Content Store와 Snapshotter도 구분해야 한다. [OverlayFS Snapshot 장애](/projects/linux-containerd-overlayfs-snapshot-failures/)에서 다뤘듯 Image Digest는 콘텐츠를, Committed Snapshot은 Layer 변경 내용을 적용한 파일시스템 상태를 나타낸다. Content Store만 복사한다고 Snapshot 메타데이터의 의존 관계가 보존되지는 않는다. Snapshot 디렉터리만 남고 메타데이터가 없다면 런타임에서 정상적으로 사용할 수 있는 목록이라고 보기 어렵다.

{{figure /figures/journals/runtime-01-storage-domains.svg | containerd의 영속 데이터, 실행 상태, kubelet 경로와 Volume은 서로 다른 관리 영역이다. 예시 경로는 실제 노드의 전체 목록이 아니다.}}

kubelet에는 별도의 상태와 Pod Volume Mount 경로가 있다. CSI Volume은 Controller와 Node에서 별도의 생명주기를 갖고, Local Path나 hostPath Volume은 특정 호스트의 파일시스템에 데이터를 둘 수 있다. Pod가 Volume을 사용한다고 그 데이터가 containerd Snapshot 체인에 포함되는 것은 아니다. Docker에도 자체 저장 경로 설정이 있고 버전과 Image Store 방식에 따라 containerd 저장소를 별도로 사용할 수 있다. 실제 구성을 확인하지 않고 Docker의 data-root가 모든 데이터를 옮긴다고 가정해서는 안 된다.

## K3s의 data-dir가 바꾸는 것

처음 만난 옵션 오류는 설정 인터페이스를 잘못 선택했다는 단서였다. containerd 실행 파일에서 Root와 State를 지정할 수 있다고 해서 같은 옵션이 K3s CLI에도 존재하는 것은 아니다.

K3s가 지원하는 설정은 data-dir다. 공개 Agent 설정 소스를 보면 지정한 Data Directory 아래 agent/containerd를 embedded containerd의 Root로 사용하고, agent/etc/containerd/config.toml에 설정을 생성한다. 예를 들어 다음과 같다.

```yaml
data-dir: /data/k3s
```

이는 지원되는 설정의 예시이지 운영 노드에서 준비 없이 경로를 바꾸라는 의미는 아니다. 이 경우 일반적인 embedded Root는 /data/k3s/agent/containerd가 된다. Server 노드에서는 Data Directory에 제어면 상태와 인증 정보, 로컬 Datastore가 있을 수도 있다. Image Cache만 옮기는 것보다 영향 범위가 훨씬 넓다.

{{figure /figures/journals/runtime-02-config.svg | K3s Data Directory에서 파생되는 설정과 영속 Root, 별도의 Runtime State 및 kubelet 저장 영역.}}

containerd 설정은 K3s가 생성한다. Template 방식도 버전에 따라 다르다. K3s는 2025년 2월 v1.32.2+k3s1 등을 통해 containerd 2.0을 포함하기 시작했고 Version 3 Template을 지원한다. 버전에 따라 Root와 State, Address를 전달하는 방법이 달라질 수 있으므로 설치된 버전의 생성된 설정과 실행 인자를 함께 확인해야 한다. 생성된 파일을 직접 수정하면 다음 기동에서 덮어쓸 수 있다. 외부 CRI Endpoint를 지정하는 구성은 단순히 경로 하나를 바꾸는 것과도 다르다.

결국 파일이 어디에 있는지만 볼 것이 아니라 어느 설정으로 그 경로가 결정됐고 누가 사용하는지, 실제로 어느 파일시스템을 가리키는지를 확인해야 했다.

## 경로와 Symbolic Link, Bind Mount

다른 저장장치의 데이터를 애플리케이션에서 접근하도록 만드는 방법은 여러 가지다. 지원되는 설정을 바꾸면 새로운 경로를 직접 지정할 수 있다. Symbolic Link는 조회 시 VFS가 해석할 경로 문자열을 저장한다. Bind Mount는 기존 파일시스템의 하위 트리를 Mount Namespace 안의 다른 위치에 연결한다. 같은 데이터를 접근하는 데 쓸 수 있지만 동작은 동일하지 않다.

{{figure /figures/journals/runtime-03-paths.svg | 명시적 경로 설정, Symbolic Link 해석, Bind Mount를 통한 접근. Bind Mount는 데이터 복사가 아니라 새로운 Mount 연결이다.}}

Symbolic Link의 대상이 없다면 Dangling Link가 된다. 반면 데이터 디스크가 Mount되지 않았는데 Root Filesystem에 대상 디렉터리가 남아 있다면 그곳으로 정상적으로 연결되는 것처럼 보일 수 있다. Bind Mount 역시 원래 Source Filesystem이 먼저 연결되지 않았다면 의도하지 않은 디렉터리를 연결할 수 있다. 기존 디렉터리 위에 Mount하면 해제할 때까지 이전 내용이 가려진다. 단순히 경로가 존재하는지 확인하는 것만으로는 이런 문제를 발견하기 어렵다.

임시 디렉터리에서 파일과 그 디렉터리를 가리키는 Symbolic Link를 만들고 동일한 파일에 접근하는지 확인했다. 그 뒤 대상 디렉터리의 이름을 바꾸고 이전 이름에 다른 내용을 담은 디렉터리를 새로 생성했다. 이름을 바꾼 직후에는 Link 조회가 실패하고 새 디렉터리를 만들자 다른 파일을 읽었다. 최초에 열어 둔 FD에서는 계속 원래 파일의 내용을 읽을 수 있었다. Hard Link를 추가해 Inode와 Link Count도 확인했다. 실제 Linux 파일 호출로 검증했지만 Bind Mount를 생성하거나 운영 저장소를 변경한 실험은 아니다.

{{figure /figures/journals/runtime-04-path-experiment.svg | 실제 경로 조회 실험. Link가 가리키는 대상은 바뀔 수 있지만 먼저 열어 둔 FD는 원래 파일을 참조한다.}}

[VFS와 Mount 생명주기](/projects/linux-vfs-mount-lifecycle/)에서 살펴본 경로와 객체의 구분이 여기서도 중요하다. 설정을 바꾼 뒤 Snapshot이나 임시 Mount 경로가 보이지 않는다면 먼저 런타임에서 그 경로가 어느 파일시스템을 가리키는지 확인해야 한다.

## 파일 복사와 런타임 이전의 차이

같은 Mount 안에서 파일을 옮길 때에는 rename을 사용할 수 있지만 서로 다른 Mount 사이에서는 EXDEV가 발생해 복사와 삭제가 필요할 수 있다. 이때 전체 이전이 원자적으로 일어나는 것은 아니다. 런타임이 메타데이터나 Snapshot, Mount 상태를 변경하는 동안 복사하면 어느 한 시점에도 존재하지 않았던 상태가 만들어질 수 있다.

실제로 이전한다면 먼저 노드 역할과 재생성할 수 없는 데이터를 구분할 것이다. Server Datastore는 지원되는 백업과 Quorum을 고려한 유지보수 계획이 필요하다. 워크로드를 Drain했다고 제어면의 가용성이 보장되는 것은 아니다. Agent 역시 로컬 Volume이나 고유한 Writable Layer 데이터를 따로 확인해야 한다. 폐쇄망에서는 이미지 재구성에 필요한 Registry나 이미지 Archive를 사용할 수 있는지도 중요하다.

다음으로 실제 Writer를 멈추고 선택한 이전 방식에 필요한 범위에서 Task와 Shim, Mount 참조가 정리됐는지 확인할 것이다. systemd 서비스가 멈췄다고 모든 컨테이너와 Mount가 종료됐다는 뜻은 아니다. 새 저장소로 복사할 때에는 권한과 숫자 UID/GID, Hard Link 관계, Extended Attribute, 특수 파일, 필요한 ACL과 Sparse File 속성을 보존해야 한다. OverlayFS의 Whiteout과 Opaque Directory 속성도 중요하다. rsync의 Archive Mode만으로 모든 속성이 보존되는 것은 아니므로 추가 옵션과 실행 권한, 대상 파일시스템 지원 여부를 확인해야 한다. Dry Run도 예상 변경 목록을 확인하는 작업이지 전체 데이터의 정합성을 검증하지는 않는다.

{{figure /figures/journals/runtime-05-cutover.svg | 노드 역할과 데이터 목록 확인부터 Writer 정지, 복사, Mount 검증과 실행 확인에 이르는 이전 절차. 당시 완료된 작업을 재현한 것이 아니다.}}

영속 메타데이터와 Snapshot 데이터는 일관된 상태로 함께 관리해야 한다. 검증이 끝나기 전까지는 정지 상태의 원본을 보존하는 편이 좋다. 새 런타임이 쓰기를 시작한 뒤 이전 경로로 되돌리면 그동안 생성한 데이터를 잃을 수도 있다. 따라서 Rollback은 Link 하나를 바꾸는 작업이 아니라 어느 데이터가 최신이고 유효한지 판단하는 과정이다.

## 디스크 연결이 서비스 시작보다 먼저 이뤄져야 한다

Mountpoint 디렉터리는 실제 디스크가 연결되지 않은 상태에서도 존재할 수 있다. 이때 서비스가 시작하면 Root Filesystem에 새로운 런타임 디렉터리가 생성될 수 있다. 이후 데이터 디스크가 Mount되면 앞서 만든 파일들은 가려지고 같은 경로에서 다른 데이터가 보인다. 이미지나 메타데이터가 없어진 것처럼 보이고 용량 확인 결과도 혼동할 수 있다.

systemd를 사용하는 구성에서는 RequiresMountsFor로 경로 접근에 필요한 Mount Unit의 의존성을 설정할 수 있다. 실제 데이터 Mount와 Server 또는 Agent 서비스에 맞게 구성해야 한다. 다만 해당 Mount Unit 자체가 없다면 Root Filesystem으로 접근할 수도 있으므로 의존성 설정만으로 의도한 장치가 연결됐음을 증명할 수는 없다.

다음에 조사한다면 findmnt로 런타임 Root가 어느 파일시스템에 속하는지 확인하고 정확한 Mountpoint와 Source 또는 UUID를 사전 목록과 비교할 것이다. 지원되는 환경에서는 서비스 시작 전 확인 조건을 추가해 잘못된 파일시스템에 쓰는 것을 방지할 수도 있다. 런타임의 Mount Namespace가 Host와 다르다면 해당 프로세스의 관점에서도 확인해야 한다. 아래는 당시 실행 기록이 아닌 읽기 전용 검사 예시다.

```bash
findmnt -T "$RUNTIME_ROOT"
findmnt --mountpoint "$DATA_MOUNT"
df -hT "$RUNTIME_ROOT"
stat -c '%d %i %n' "$RUNTIME_ROOT"
```

경로 문자열이 같은 것만으로는 부족하다. 실제 파일시스템과 런타임의 참조, 애플리케이션 데이터가 서로 일치해야 한다.

## 어느 지점까지 확인해야 이전이 끝난 것일까

서비스 시작 여부보다 먼저 Root가 의도한 Mount를 가리키는지 확인할 것이다. 이미지와 Snapshot 목록도 원본과 일치하는지 살펴야 한다. 그 뒤 통제된 워크로드가 Writable Snapshot을 만들고 정상 실행되며 기대한 데이터를 읽을 수 있는지 확인한다. 영속 Volume 연결과 앱 데이터의 검증은 별도 항목이다. 허용된 유지보수 범위에서는 재시작 후에도 같은 저장 경로와 데이터가 유지되는지 확인할 필요가 있다.

[Disk I/O와 Writeback](/projects/linux-disk-io-journaling-writeback/)에서 살펴본 것처럼 바이트를 복사했다는 사실과 데이터의 영속성을 보장했다는 사실도 다르다. 시스템 디스크의 사용량이 줄어들었다고 앱의 데이터가 정상이라는 뜻은 아니다. 결국 저장 경로를 옮기는 작업의 핵심은 런타임이 계속 동작하는 데 필요한 식별자와 참조, 데이터를 잃지 않으면서 실제 저장 위치를 바꾸는 것이다.

## 관련 기록과 참고 자료

- [OverlayFS Snapshot 장애](/projects/linux-containerd-overlayfs-snapshot-failures/) · [VFS와 Mount 생명주기](/projects/linux-vfs-mount-lifecycle/) · [Disk I/O와 Writeback](/projects/linux-disk-io-journaling-writeback/) · [제어면 장애 기록](/projects/rokaf-control-plane-incident-log/) · [스토리지 배치와 장애 영역](/projects/rokaf-storage-placement-and-failure-domains/)
- [K3s Agent 옵션](https://docs.k3s.io/cli/agent) · [K3s Agent 설정 소스](https://github.com/k3s-io/k3s/blob/main/pkg/agent/config/config.go) · [Containerd Template](https://docs.k3s.io/advanced) · [Containerd 운영 문서](https://github.com/containerd/containerd/blob/main/docs/ops.md)
- [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html) · [mount(8)](https://man7.org/linux/man-pages/man8/mount.8.html) · [rsync 매뉴얼](https://rsync.samba.org/ftp/rsync/rsync.1) · [systemd Unit 의존성](https://www.freedesktop.org/software/systemd/man/257/systemd.unit.html)
