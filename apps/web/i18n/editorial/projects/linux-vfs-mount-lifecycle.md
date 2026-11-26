2026년 3월 23일, K3s 노드를 정리하던 중 kubelet의 데이터 디렉터리 아래에 있는 경로 일부를 제거하지 못했다. 당시 출력에는 CSI의 Staging Directory와 여러 Pod Volume 경로에서 발생한 오류가 남아 있다.

```text
rm: cannot remove '.../globalmount': Device or resource busy
```

내부 식별자는 제외했다. 여기서 중요한 것은 오류를 낸 명령이다. `umount`를 실행했다가 실패했다는 기록이 아니라 `rm`으로 디렉터리를 제거하는 과정에서 발생한 오류였다. 설정 파일이나 Projected Volume에 해당하는 경로에서도 비슷한 오류가 나타났다. 그 전후로 containerd의 Snapshot 경로 누락과 CSI 메타데이터 파일 누락도 확인했다. K3s를 재시작하고 Detach 상태의 PVC를 삭제했지만, 두 조치가 이 오류를 유발했는지 또는 이후 Unmount와 앱 복구까지 성공했는지는 기록만으로 알 수 없다.

왜 정리하려던 디렉터리가 보이는데도 삭제할 수 없었을까. [Containerd Snapshot 장애](/projects/linux-containerd-overlayfs-snapshot-failures/)에서는 필요한 디렉터리가 없었던 문제를 살펴봤다. 이번에는 존재하는 경로와 그 경로를 참조하는 객체의 생명주기가 중요하다.

## VFS 객체와 열린 파일

VFS는 ext4, tmpfs 등 서로 다른 파일시스템에 공통된 인터페이스를 제공한다. 경로를 탐색하는 동안 디렉터리 이름을 따라가고, 필요한 경우 Mount 경계를 넘어 Inode를 찾는다. Inode는 파일이나 디렉터리 같은 파일시스템 객체와 그 메타데이터를 나타낸다. Positive Dentry는 부모 디렉터리 아래의 이름과 Inode를 연결하며, Negative Dentry는 존재하지 않는 이름의 조회 결과를 캐시할 수도 있다. Hard Link가 있다면 여러 이름이 하나의 Inode를 참조한다.

Superblock은 파일시스템 인스턴스를 나타낸다. Mount는 파일시스템의 트리나 일부를 Namespace 안의 특정 위치에 연결한다. 따라서 여러 Mount가 같은 Superblock을 참조할 수 있고 Mount의 루트가 전체 파일시스템의 루트일 필요도 없다.

파일을 열면 커널에는 Open File Description에 해당하는 File 객체가 생긴다. 여기에 파일 위치와 File Status Flag 등이 저장되고, Mount와 Dentry로 이루어진 Path도 참조한다. Userspace의 File Descriptor는 이 객체를 가리키는 디스크립터 테이블의 인덱스다. Close-on-exec 같은 Descriptor Flag는 공유되는 File 객체가 아닌 디스크립터 자체에 속한다. 같은 경로를 별도로 open하면 일반적으로 새로운 File 객체가 생기지만, dup이나 fork로 복제한 디스크립터는 기존 File 객체와 파일 위치를 공유할 수 있다.

{{figure /figures/journals/vfs-01-object-graph.svg | 복제된 FD 두 개는 하나의 File 객체를 공유하고 별도의 open은 파일 위치가 다른 File 객체를 만든다. 최종적으로 동일한 Inode를 참조할 수 있다.}}

## 파일 위치와 unlink의 실제 실험

이 관계를 직접 확인하기 위해 ABCDEF라는 6바이트를 담은 임시 파일을 만들었다. 파일을 열고 FD를 dup으로 복제한 뒤 같은 경로를 별도로 한 번 더 열었다. 최초 FD에서 2바이트를 읽으면 AB, 복제한 FD에서 다시 2바이트를 읽으면 CD가 나왔다. 별도로 연 FD에서는 AB가 나왔다. 공유된 파일 위치는 4이고 별도로 연 파일의 위치는 2였다. 같은 Inode에 접근하지만 읽기 위치는 서로 달랐다.

이어서 Hard Link를 하나 더 생성했다. 처음 이름을 삭제하자 Link Count가 2에서 1로 줄었고, 나머지 이름을 삭제하자 0이 됐다. 두 이름으로 다시 open하는 것은 실패했지만 기존 FD는 사용할 수 있었다. 최초 FD를 닫은 뒤에도 복제한 FD로 EF를 읽을 수 있었고 fstat에서 동일한 Inode와 Link Count 0을 확인했다. 당시 운영 장애에서 확인한 수치가 아니라 이번에 임시 파일을 이용해 실행한 독립적인 예제다.

{{figure /figures/journals/vfs-02-reference-lifetime.svg | 실제 6바이트 실험 결과. 별도 open의 파일 위치는 독립적이며 이름이 모두 사라진 뒤에도 열린 참조가 남는다.}}

파일 이름을 삭제하는 것과 객체에 할당한 저장 공간을 반환하는 것은 별개의 일이다. 마지막 Hard Link가 사라지고 살아 있는 참조가 모두 해제된 뒤에야 파일시스템이 그 객체의 공간을 회수할 수 있다. FD를 닫아도 메모리 매핑이 파일 참조를 유지하는 경우가 있다. 실제 블록 반환 시점은 파일시스템 구현에 따라 달라지므로 이번 예제에서 디스크 공간이 얼마나 회수됐는지 측정하지는 않았다. 다만 기록 중인 큰 로그 파일을 삭제해도 프로세스가 여전히 파일을 열고 있다면 사용 공간이 즉시 줄지 않을 수 있는 이유를 설명한다.

## Mount Namespace와 경로의 가시성

경로는 프로세스의 Mount Namespace와 루트를 기준으로 해석된다. Mount가 연결되면 해당 지점에서 보이는 트리가 바뀌지만 기존의 디렉터리가 없어지는 것은 아니다. Bind Mount는 원본 파일을 복사하는 대신 기존 트리의 일부를 다른 위치에 연결한다. 같은 데이터에 접근하더라도 각각 다른 Mount를 가리킬 수 있다.

{{figure /figures/journals/vfs-03-mount-namespace.svg | 같은 파일시스템의 일부를 Host와 Workload에서 바라보는 가상의 구조. 실제 운영망의 Mount 배치가 아니다.}}

Mount Namespace를 복제했다고 해서 이후 Mount 이벤트가 항상 서로 격리되는 것도 아니다. Shared Mount에서는 Peer 간 이벤트를 전파하고, Slave Mount는 상위 Peer Group의 이벤트를 받되 반대로 보내지는 않는다. Private Mount는 이벤트를 전파하지 않는다. 따라서 경로가 같다는 이유로 Host와 컨테이너의 Mount 상태가 같다고 가정해서는 안 된다. 컨테이너로 실행되는 CSI Plugin이 생성한 Mount를 Host의 kubelet에서 볼 수 있게 해야 하는 경우에도 이 설정이 중요하다.

프로세스 기준 Mount 정보는 /proc/PID/mountinfo에서 확인할 수 있다. Mount ID와 Parent ID, 장치 Major/Minor, 파일시스템 내부의 Root, Mountpoint, Mount Option, Propagation 정보, 구분자 뒤의 파일시스템 정보를 담고 있다. Bind Mount는 같은 파일시스템을 사용하더라도 내부 Root가 다를 수 있다. 장치 번호만으로 경로가 어떤 Mount를 가리키는지 확정할 수는 없다. Unmount 후 ID가 재사용될 수 있으므로 측정 시각과 Namespace 식별자도 함께 보존하는 편이 좋다.

## 디렉터리 제거와 Unmount의 차이

Mountpoint는 한쪽 트리의 디렉터리이면서 다른 트리가 연결되는 지점이다. 이 디렉터리를 삭제하는 명령과 연결을 해제하는 명령은 다르다. Linux의 rmdir은 경로가 Mountpoint이거나 호출한 프로세스의 루트인 경우 EBUSY를 반환할 수 있다. 반면 일반 Unmount는 활성 참조나 하위 Mount 때문에 해제할 수 없을 때 실패할 수 있다. 열린 파일이나 작업 디렉터리, 메모리 매핑 등이 참조를 유지하는 경우도 있다. 다만 다른 독립적인 Mount를 통해 같은 Inode를 열고 있다는 사실만으로 이 Mount가 Busy라고 단정해서는 안 된다.

{{figure /figures/journals/vfs-04-operation-boundaries.svg | unlink, rmdir, 일반 Unmount, Lazy Detach는 서로 다른 관계를 바꾼다. 당시 rm 오류만으로 정확한 참조 주체나 Unmount 시도 여부를 알 수 없다.}}

Lazy Unmount는 Namespace에서 Mount를 분리하되 남아 있는 참조의 정리를 뒤로 미룬다. 파일시스템 사용이 완전히 중단됐거나 쓰기가 영속 저장됐다는 보장은 아니며, 그 상태에서 원격 블록 장치를 안전하게 Detach할 수 있다고 볼 수도 없다. Force Unmount 또한 파일시스템별 제약이 있다. Mount가 남은 상태로 재귀 삭제를 하면 Mountpoint 아래의 디렉터리뿐 아니라 실제로 연결된 파일시스템의 데이터가 삭제될 수 있다. 따라서 정리를 먼저 시도하기보다는 어떤 Mount가 남아 있는지 확인하는 편이 중요하다.

같은 문제를 다시 조사한다면 대상 경로 자체가 Mountpoint인지, 하위 Mount가 무엇인지, Host·kubelet·CSI Plugin의 Namespace에서 각각 어떻게 보이는지 먼저 읽기 전용으로 확인할 것이다.

```bash
findmnt --mountpoint "$TARGET"
findmnt -R --mountpoint "$TARGET"
cat /proc/self/mountinfo
cat "/proc/$PID/mountinfo"
readlink "/proc/$PID/ns/mnt"
```

일반적인 Target 조회에서 상위 Mount가 검색됐다고 대상 경로 자체가 Mountpoint인 것은 아니다. 정확한 Mountpoint와 Mount Tree를 확인한 뒤 FD, cwd, root, 매핑 등 참조를 살펴야 한다. 권한과 Namespace도 고려해야 한다. 위 명령은 재발 시 증거 확보를 위한 예시이며 당시 실행 기록은 아니다.

## CSI Staging과 Pod Volume

Staging을 지원하는 CSI Driver에서 파일시스템 Volume을 사용하는 경우 Node Plugin이 노드의 Staging Target에 장치를 Mount하고, NodePublishVolume으로 Pod가 사용할 Target에 연결할 수 있다. 흔히 Bind Mount를 이용한다. 런타임은 다시 그 Target을 컨테이너의 Mount Namespace에서 보이도록 구성한다. Access Mode와 Driver가 허용하는 경우 여러 사용자가 같은 Staging Mount를 공유할 수 있다. Raw Block Volume은 제공 방식이 다르므로 여기서는 파일시스템 Volume만 설명한다.

{{figure /figures/journals/vfs-05-csi-mount-topology.svg | 하나의 가상 파일시스템 Volume과 Staging Mount, 두 Pod Target. 컨테이너의 Mount는 같은 데이터를 바라보는 또 다른 연결이지 복제본이 아니다.}}

Controller Attachment와 Node Staging을 모두 지원하는 Driver의 일반적인 흐름은 ControllerPublishVolume, NodeStageVolume, NodePublishVolume이다. 정리할 때는 사용자 쪽에서 Volume 사용을 중단하고 해당 Target을 Unpublish한 뒤 필요한 Publication이 모두 사라지면 Unstage한다. 해당 Capability를 사용하는 경우 ControllerUnpublishVolume에서 Controller 쪽 Detach를 수행한다. 구체적인 순서와 재시도는 Driver와 Orchestrator, Access Mode에 따라 달라질 수 있다. RPC 성공만으로 앱 데이터의 정합성이 검증됐다고 할 수도 없다.

{{figure /figures/journals/vfs-06-teardown-evidence.svg | Volume 정리의 의존성과 단계별 증거. 실제로 발생한 rm 오류는 정상적인 정리 흐름과 구분했다.}}

3월의 오류는 kubelet이 정리하려는 경로와 커널에서 실제로 참조되는 Mount 상태가 서로 맞지 않을 수 있다는 점을 보여줬다. 그러나 globalmount라는 이름만으로 어떤 프로세스나 하위 Mount가 원인이었는지, 특정 Driver의 버그였는지 확정할 수는 없다. CSI 메타데이터 파일이 없다는 기록 역시 Mount가 해제됐다는 뜻은 아니다. Longhorn 프로세스 및 Attachment 상태는 [Longhorn 복구 기록](/projects/rokaf-stateful-storage-and-recovery/)에서 별도로 다뤘다.

복구 여부를 판단하려면 기존 사용자가 실제로 종료됐는지, 관련 Namespace에서 Publication과 Staging 참조가 정리됐는지, Driver 상태가 수렴했는지, 안전하게 다시 연결한 뒤 의도한 데이터에 접근할 수 있는지 확인해야 한다. 당시에는 이 모든 지점을 검증한 기록이 없다. 이번 경험에서 얻은 가장 중요한 교훈은 디렉터리 트리가 참조 관계의 일부만 보여준다는 점이다. 정리하려는 경로뿐 아니라 그 데이터를 살아 있게 유지하는 객체와 관리 주체를 함께 봐야 한다.

## 관련 기록과 참고 자료

- [Containerd와 OverlayFS Snapshot 장애](/projects/linux-containerd-overlayfs-snapshot-failures/) · [Longhorn 복구](/projects/rokaf-stateful-storage-and-recovery/) · [스토리지 배치와 장애 영역](/projects/rokaf-storage-placement-and-failure-domains/) · [Linux 메모리 압박](/projects/rokaf-memory-pressure-and-service-recovery/)
- [Linux VFS](https://docs.kernel.org/filesystems/vfs.html) · [open(2)](https://man7.org/linux/man-pages/man2/open.2.html) · [unlink(2)](https://man7.org/linux/man-pages/man2/unlink.2.html) · [rmdir(2)](https://man7.org/linux/man-pages/man2/rmdir.2.html) · [umount(2)](https://man7.org/linux/man-pages/man2/umount.2.html)
- [Mount Namespace](https://man7.org/linux/man-pages/man7/mount_namespaces.7.html) · [mountinfo](https://man7.org/linux/man-pages/man5/proc_pid_mountinfo.5.html) · [CSI 명세](https://github.com/container-storage-interface/spec/blob/master/spec.md) · [Kubernetes CSI Driver 문서](https://kubernetes-csi.github.io/docs/developing.html)
