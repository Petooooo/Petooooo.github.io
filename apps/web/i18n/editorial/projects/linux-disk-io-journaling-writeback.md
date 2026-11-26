2026년 2월 24일, K3s 노드에서 디스크 I/O를 조사하던 중 `pidstat -d 1`의 출력에서 눈에 띄는 값을 발견했다. 컨테이너 프로세스가 아닌 JBD2 커널 스레드의 쓰기량이었다.

```text
Task       kB_wr/s
jbd2/...   26122.88
```

당시 보고한 값을 옮기고 내부 장치 식별자는 제외했다. 전체 터미널 로그를 복원한 것은 아니다. sysstat 매뉴얼은 표의 kB를 KiB 단위로 설명하므로 그 기준으로 환산하면 약 25.51 MiB/s다. 이어서 디렉터리별 용량을 살펴봤을 때 OverlayFS Snapshot 디렉터리는 약 19GB로 확인됐다. 당시 런타임 CLI는 사용할 수 있었지만 CRI 조회 도구는 불안정했다.

두 값은 같은 시간 구간에서 수집한 시계열이 아니다. 하나는 태스크에 귀속된 쓰기량의 변화율이고 다른 하나는 디렉터리가 이미 점유하고 있던 공간이다. 어느 워크로드가 쓰기를 시작했는지, 실제 장치가 포화됐는지, Snapshot 디렉터리가 Journal 쓰기의 원인이었는지까지는 알 수 없다. 장치 지연 시간과 실제 ext4 Mount Option, 최종 원인 분석 결과도 남아 있지 않다.

{{figure /figures/journals/disk-io-01-observation.svg | 당시 관측한 쓰기량과 디렉터리 용량은 서로 다른 물리량이다. 임의의 시계열이나 두 값의 인과관계를 만들지 않았다.}}

궁금했던 것은 애플리케이션이 시작한 쓰기가 왜 다른 커널 실행 문맥의 활동으로 나타날 수 있는가였다. 공간 점유량, 쓰기 처리량, 데이터의 영속성도 함께 구분할 필요가 있었다.

## Buffered Write와 Page Cache

일반적인 Buffered Write는 File Descriptor를 통해 시작한다. VFS가 열린 File 객체를 찾아 파일시스템의 구현으로 연결하면, 데이터는 해당 캐시 페이지에 복사되고 Dirty 상태로 표시된다. 정확한 경로는 파일시스템과 매핑, 쓰기 옵션에 따라 다르다. write가 성공해 반환한 값은 받아들인 바이트 수이며 요청보다 적을 수도 있다. 이 시점에 데이터가 영속 저장장치에 도달했다고 보장하는 것은 아니다. Direct I/O나 동기 쓰기 옵션, 메모리 매핑을 이용한 쓰기는 다른 경로와 완료 조건을 가질 수 있다.

Page Cache는 읽기만 빠르게 해주는 공간이 아니다. 여러 변경을 모아 저장장치에 전달할 수도 있다. ext4의 Delayed Allocation은 Writeback 단계까지 블록 할당을 미뤄 작은 쓰기마다 공간을 할당하는 것보다 연속적인 공간을 확보할 기회를 준다. 하지만 Dirty Page는 메모리를 차지하고 결국 저장장치에 반영해야 한다. Dirty Page의 양이나 경과 시간에 따라 백그라운드 Writeback이 일어나고, 쓰기 속도가 회수 가능한 속도를 앞지르면 애플리케이션의 쓰기 자체가 제한될 수도 있다. write가 반환됐다고 해서 I/O 비용이 없어진 것은 아니다.

{{figure /figures/journals/disk-io-02-buffered-path.svg | Buffered Write를 단순화한 흐름. 파일 데이터와 Journal에 기록하는 메타데이터는 별개이며 모든 Journal Mode에서 동일한 순서를 따른다는 뜻은 아니다.}}

캐시 페이지를 이해할 때는 변경되지 않은 Clean 상태, 수정된 Dirty 상태, 저장장치에 반영 중인 Writeback 상태를 구분하면 편하다. 반영 중에 다시 수정되는 경우도 있다. 먼저 시작한 I/O가 끝나더라도 더 새로운 변경 내용이 남아 있다면 다시 저장해야 한다.

{{figure /figures/journals/disk-io-03-page-states.svg | Writeback 중 다시 수정되는 경우를 포함한 페이지 상태 변화. 실제 커널에서는 상태 Flag가 동시에 설정될 수 있다.}}

이 부분은 앞서 작성한 [Linux 메모리 압박 기록](/projects/rokaf-memory-pressure-and-service-recovery/)과도 연결된다. Dirty Page를 회수하기 전에 I/O가 필요할 수 있으므로 저장장치 지연과 메모리 압박이 서로 영향을 줄 수 있다. meminfo의 Dirty와 Writeback, 회수 및 쓰기 지표, Memory·I/O PSI를 함께 확인하는 편이 좋다.

## ext4와 JBD2 Transaction

ext4는 JBD2를 이용해 Journal Transaction을 관리한다. Journal은 파일시스템 변경을 복구하기 위한 기록이지 애플리케이션 로그가 아니다. 기록되는 블록의 최종 위치 자체도 아니다. 일반적인 Full Transaction에서는 Descriptor Block으로 기록할 블록을 식별하고 해당 내용과 필요한 Revoke 정보를 저장한다. 유효한 Commit Record와 형식에 맞는 무결성 검증을 통해 완료된 Transaction을 구분한다. 이후 Checkpoint에서는 기록된 변경을 본래 블록 위치에 반영하고 안전하게 재사용할 수 있는 Journal 공간을 확보한다.

{{figure /figures/journals/disk-io-04-journal-transaction.svg | 일반적인 JBD2 Transaction과 이후 Checkpoint. 완료됐지만 최종 위치에 반영되지 않은 유효한 Transaction은 복구 시 Replay할 수 있다. Fast Commit 등은 생략했다.}}

시스템이 갑자기 중단되는 상황에서는 Commit과 Checkpoint의 차이가 중요하다. 끝나지 않은 Transaction을 완료된 것처럼 Replay해서는 안 된다. 반대로 유효하게 Commit됐지만 최종 위치에 모두 반영되지 않은 Transaction은 Replay로 복구할 수 있다. 이는 파일시스템의 일관성을 위한 것이며, 애플리케이션에서 서로 다른 여러 파일에 수행한 쓰기를 하나의 원자적 작업으로 만들어 주지는 않는다.

ext4의 Data Mode에 따라 일반 파일 데이터와 Journal 메타데이터의 관계도 달라진다.

| Mode | 파일 데이터 | 메타데이터 |
| --- | --- | --- |
| data=ordered | 관련 Dirty Data를 메타데이터 Commit에 앞서 반영하도록 순서를 보장 | Journal 기록 |
| data=writeback | 메타데이터 Commit 전 데이터 반영 순서를 보장하지 않음 | Journal 기록 |
| data=journal | 파일 데이터도 Journal을 거침 | Journal 기록 |

일반적인 기본값은 ordered지만 당시 Mount Option을 확인할 수 없으므로 설명을 위한 예시로만 사용했다. Data Journaling은 추가 쓰기를 발생시킬 수 있고 Writeback Mode는 데이터 기록 순서에 대한 보장이 약하다. 어느 방식을 선택하더라도 애플리케이션이 필요한 영속성 보장을 따로 고려해야 한다.

JBD2는 블록 할당이나 디렉터리 변경, 메타데이터 갱신 등 여러 작업에서 발생한 Journal 처리를 담당할 수 있다. 쓰기량이 높게 나타났다고 해서 그 스레드가 쓰기를 처음 요청한 애플리케이션이라는 뜻은 아니다. 모든 메타데이터 쓰기가 그 스레드에 귀속되는 것도 아니고 파일시스템의 Writeback 전체가 Journal 기록인 것도 아니다. 스레드 이름은 어느 계층을 조사할지 알려주는 단서에 가깝다.

## write와 fsync, 디렉터리의 영속성

쓰기 요청이 받아들여졌는지, 다른 Reader가 예상한 파일 내용을 읽을 수 있는지, 파일시스템과 장치의 영속성 계약에 따라 데이터가 동기화됐는지는 서로 다른 문제다. 두 번째 Reader는 Page Cache에서만 데이터를 얻을 수도 있다. 일반적인 FD를 닫는 것 역시 fsync 성공 여부를 확인하는 작업을 대신할 수 없다.

기존 파일을 새 버전으로 교체할 때에는 같은 디렉터리에 임시 파일을 만들고 내용을 쓰고 fsync한 뒤, 대상 이름으로 rename하고 부모 디렉터리도 fsync하는 방식을 사용할 수 있다. 파일에 대한 fsync만으로 새 디렉터리 항목의 영속성을 보장할 수는 없기 때문이다. 실행 중인 시스템에서 rename이 원자적으로 보이는 것과 전원이 끊긴 뒤에도 변경이 유지되는 것은 다르다. 각 호출의 실패를 확인해야 하며 파일시스템과 장치의 Flush 동작에 대한 전제도 필요하다.

{{figure /figures/journals/disk-io-05-durability.svg | 파일 동기화와 디렉터리 동기화는 각각 다른 영속성 경계에 해당한다. 같은 디렉터리 안의 파일 교체 예시이며 모든 하드웨어 장애를 견딘다는 의미는 아니다.}}

이번에는 임시 디렉터리에서 실제 시스템 호출로 이 과정을 확인했다. 4096바이트를 쓰고 fsync 전 Readback을 확인한 뒤 파일을 동기화하고 기존 이름으로 rename했다. 디렉터리를 동기화한 후 최종 데이터가 일치하는지도 확인했다. fsync 전에도 읽기는 성공했지만, 이는 내용이 보인다는 증거일 뿐 영속성을 확인한 결과는 아니다. 교체 전 파일을 열어 둔 FD로는 rename 이후에도 기존 내용을 읽을 수 있었다. 앞서 [VFS 참조 생명주기 실험](/projects/linux-vfs-mount-lifecycle/)에서 다룬 원리와 같다. 이번 실험은 호출의 성공과 내용 일치를 확인한 것으로 실제 전원 장애, 디스크 성능이나 당시 Journal 동작을 검증하지 않았다.

## Block Layer와 I/O 지표

파일시스템의 I/O는 Block Request로 변환된다. Multi-queue Block Layer에서는 소프트웨어 제출 큐와 하드웨어 Dispatch Queue를 통해 요청을 처리한다. 여러 요청이 합쳐지거나 하나의 요청이 분할되기도 한다. MD RAID 같은 논리 장치는 요청을 하위 장치에 매핑한다. 복제 방식과 쓰기 정렬 등에 따라 실제 구성 장치의 I/O는 논리 장치에서 본 것보다 많거나 다른 형태일 수 있다. 장치의 Cache나 SSD 내부 동작도 별도 계층이다.

쓰기량만으로 저장장치가 포화됐는지는 알 수 없다. Throughput은 단위 시간당 전송량, IOPS는 특정 계층에서 단위 시간당 완료한 요청 수다. 평균 요청 크기는 같은 종류의 작업을 같은 시간 동안 측정했을 때 두 값을 연결할 수 있다. await에는 큐 대기와 처리 시간이 포함되고 평균 큐 길이는 처리 중이거나 대기 중인 요청의 정도를 보여준다. 여러 요청을 병렬로 처리하거나 Block Device가 여러 계층으로 연결된 환경에서는 Utilization 하나만으로 포화를 판단하기 어렵다.

가령 초당 6400개의 4 KiB 요청과 초당 100개의 256 KiB 요청은 모두 25 MiB/s다. 같은 Throughput이라도 요청 횟수와 실제 지연, 장치에 주는 부하는 크게 다를 수 있다. 이 계산은 그림 생성 코드로 검증했으며 당시 서버에서 측정한 값은 아니다.

{{figure /figures/journals/disk-io-06-accounting.svg | 애플리케이션의 작업량, 파일시스템 처리와 장치 카운터의 측정 범위가 다르다. 예시에서는 요청 크기와 횟수가 달라도 같은 Throughput을 얻는다.}}

당시에는 파일 생성이나 삭제가 잦아 메타데이터 작업이 많았는지, 컨테이너 Writable Layer나 로그, 영속 Volume에 데이터가 기록되고 있었는지, 실제로 Writeback이나 장치 큐에서 지연이 발생했는지 확인할 필요가 있었다. 용량이 큰 읽기 전용 이미지 캐시가 쓰기 부하를 거의 발생시키지 않을 수도 있다.

## 원인을 확인하기 위한 관측 방법

같은 문제가 발생한다면 최초 관측의 시각을 기록하고 여러 계층의 지표를 같은 시간 구간에서 수집할 것이다. 아래는 도구가 설치된 노드에서 활용할 수 있는 읽기 전용 조사 예시이며, 당시 모두 실행했다는 기록은 아니다.

```bash
pidstat -d 1 5
iostat -xz 1 5
grep -E '^(Dirty|Writeback):' /proc/meminfo
cat /proc/pressure/io
findmnt -T "$TARGET"
df -hT "$TARGET"
```

대상 프로세스가 확인되면 /proc/PID/io의 변화량과 지원되는 경우 cgroup I/O 지표를 비교할 것이다. wchar와 write_bytes는 의미가 다르다. 후자는 태스크가 저장 계층에 쓰도록 유발한 바이트 수를 나타내며 영속성이 검증된 데이터 크기는 아니다. 취소된 쓰기나 여러 워크로드가 공유하는 파일시스템 작업, Kernel Worker 때문에 최초 요청 주체를 추적하기 어려울 수 있다. 논리 장치와 구성 장치의 카운터를 모두 더해서 애플리케이션 쓰기량으로 해석해서도 안 된다.

디렉터리별 용량 조사는 여전히 필요하다. 적절한 간격으로 반복하면 늘어나는 경로를 찾는 데 도움이 된다. 다만 파일의 논리적 크기와 할당 블록, 공유 데이터, 삭제된 뒤 열린 파일은 서로 다른 문제다. 넓은 범위를 재귀 조회하는 과정 자체도 부하를 만들 수 있다. 컨테이너 런타임의 데이터라면 디렉터리를 직접 삭제하기보다 [OverlayFS 장애 기록](/projects/linux-containerd-overlayfs-snapshot-failures/)에서 설명한 것처럼 런타임의 메타데이터를 먼저 살펴야 한다.

궁극적으로 확인하고 싶은 것은 어떤 작업에서 쓰기가 시작돼 파일시스템을 거쳐 장치에 전달됐는지다. 당시 한 번의 관측만으로는 그 연결을 증명할 수 없었다. Journal의 쓰기량을 낮추는 것만으로 해결했다고 볼 수는 없다. 필요한 쓰기를 늦추거나 복구에 필요한 보장을 약하게 만드는 결과일 수도 있기 때문이다.

## 관련 기록과 참고 자료

- [Linux 메모리 압박](/projects/rokaf-memory-pressure-and-service-recovery/) · [VFS와 Mount 생명주기](/projects/linux-vfs-mount-lifecycle/) · [OverlayFS Snapshot 장애](/projects/linux-containerd-overlayfs-snapshot-failures/) · [제어면과 디스크 장애](/projects/rokaf-control-plane-incident-log/) · [관측과 장애 증거](/projects/rokaf-observability-and-failure-evidence/)
- [ext4 Journal](https://docs.kernel.org/filesystems/ext4/journal.html) · [ext4 Mount Option](https://docs.kernel.org/admin-guide/ext4.html) · [Linux VM 설정](https://docs.kernel.org/admin-guide/sysctl/vm.html) · [write(2)](https://man7.org/linux/man-pages/man2/write.2.html) · [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html)
- [proc_pid_io(5)](https://man7.org/linux/man-pages/man5/proc_pid_io.5.html) · [blk-mq](https://docs.kernel.org/block/blk-mq.html) · [pidstat(1)](https://man7.org/linux/man-pages/man1/pidstat.1.html) · [iostat(1)](https://man7.org/linux/man-pages/man1/iostat.1.html)
