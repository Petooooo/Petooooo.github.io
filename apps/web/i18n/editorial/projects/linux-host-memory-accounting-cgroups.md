2026년 8월, 호스트 메모리 사용량이 전체의 약 5분의 1 수준에서 포화에 가깝게 급증했다. 그런데 당시 살펴본 Kubernetes Pod 그래프에는 그에 상응하는 증가가 나타나지 않았다. 별도의 earlyoom 종료 기록에서 선택한 프로세스의 RSS는 약 608 MiB였다. 종료 대상으로 선택됐다는 사실만으로 전체 증가분을 설명할 수 없었다. [앞서 작성한 EarlyOOM 글](/projects/rokaf-memory-pressure-and-service-recovery/)에서는 압박에 대한 대응을 다뤘다면 이번에는 각각의 지표가 무엇을 세는지에 집중했다.

8월 30–31일의 추가 조사 기록에는 호스트 관리 데몬의 OOM Task Dump도 남아 있었다. RSS는 54,101,261페이지, swapents는 2,687,499페이지, pgtables_bytes는 910,581,760바이트였다. 당시 기본 페이지 크기를 4 KiB로 가정하면 RSS 약 206.4 GiB, Swap Entry 약 10.25 GiB, Page Table 약 868 MiB에 해당한다. 각 값의 의미는 다르며 페이지 크기는 확인되지 않은 당시 환경에 대한 가정이다. OOM Task Dump는 종료 대상 목록이 아니라 판단 범위에 속한 태스크들의 상태를 보여준다. 이 데몬은 상당한 메모리 소비 후보였지만 두 8월 관측을 완전히 같은 시각에 대조할 수는 없고, 모두 독점 페이지였는지 어떤 할당 경로가 증가를 유발했는지도 알 수 없다. 완전한 매핑 기록과 재발 방지 검증도 남아 있지 않다. 내부 노드명과 PID, 관리 경로 등은 제외했다.

{{figure /figures/journals/memacct-01-evidence.svg | 8월의 별도 관측 기록. OOM Task Dump는 종료 대상 하나보다 강한 소비 주체 단서를 주지만, 당시 페이지 크기나 전체 증가분의 귀속을 확정하지는 못한다.}}

## RSS와 PSS, 가상 주소 공간

VSZ 혹은 VmSize는 매핑된 가상 주소 공간의 크기다. 실제 RAM에 올라오지 않은 예약 영역도 포함한다. RSS는 현재 프로세스 주소 공간에서 상주하는 페이지를 센다. 여러 프로세스가 공유 라이브러리 페이지를 참조하면 각각의 RSS에 포함되므로 이를 모두 합산했을 때 실제 물리 메모리보다 크게 나올 수 있다.

PSS는 페이지 크기를 매핑 참조 수에 비례해 나눈다. 한 번만 매핑됐다면 전체 크기를, 두 번 매핑됐다면 각각 절반을 센다. USS는 보통 smaps의 Private Clean과 Private Dirty를 더해 해당 프로세스만 사용하는 상주 메모리의 근사값으로 활용한다. 프로세스를 종료했을 때 반환되는 커널 자원 전체를 의미하지는 않으며 Huge Page나 특수 매핑도 고려해야 한다. 일부 프로세스의 PSS 합만으로 매핑되지 않은 캐시나 커널 메모리까지 설명할 수도 없다.

{{figure /figures/journals/memacct-02-shared-pages.svg | 개인 페이지와 공유 페이지의 예시. RSS는 공유 영역을 각 매핑에 모두 포함하고 PSS는 나눠 집계한다. 수치는 설명을 위한 가상 값이다.}}

### 실제 공유 매핑 실험

작은 Linux 예제를 작성했다. memfd_create로 4 MiB 크기의 메모리 기반 파일을 만들고 MAP_SHARED로 매핑한 뒤 각 페이지에 접근했다. fork로 만든 자식도 같은 영역에 접근하도록 하고 Pipe로 동기화한 다음 두 프로세스가 살아 있는 상태에서 /proc/PID/smaps 중 해당 매핑만 읽었다. 공유 데이터는 4 MiB이며 시스템의 메모리를 소진시키는 실험은 아니다.

| 매핑 측정값 | 부모 | 자식 | 합계 |
| --- | ---: | ---: | ---: |
| Size (KiB) | 4096 | 4096 | 8192 |
| RSS (KiB) | 4096 | 4096 | 8192 |
| PSS (KiB) | 2048 | 2048 | 4096 |
| Private Clean + Dirty (KiB) | 0 | 0 | 0 |

Shared Dirty는 두 매핑 모두 4096 KiB였다. RSS를 더하면 공유 데이터의 두 배가 되지만 PSS 합은 4096 KiB로 돌아온다. 실제 예제에서 얻은 특정 매핑의 결과이며 당시 서버의 장애 수치나 프로세스 전체 사용량이 아니다. 물리 페이지 번호나 호스트 총사용량, cgroup Charge는 측정하지 않았다.

{{figure /figures/journals/memacct-03-experiment.svg | 두 프로세스가 4 MiB를 공유한 실제 smaps 측정값. RSS 합은 8192 KiB, PSS 합은 4096 KiB였다.}}

## 호스트 메모리 지표의 중첩

호스트에서는 MemAvailable과 AnonPages, Cached, Shmem, Slab, SReclaimable, SUnreclaim, KernelStack, PageTables, SwapFree의 변화를 먼저 살필 것이다. MemAvailable은 Swap 없이 확보할 수 있는 메모리의 추정값이며 물리 페이지의 별도 영역이 아니다. Cached에는 tmpfs 및 공유 메모리도 포함될 수 있고 Slab에는 회수 가능 및 불가능한 Slab이 함께 집계된다. Page Table과 Kernel Stack 역시 일반적인 프로세스 RSS에 포함되지 않는 실제 메모리 비용이다.

{{figure /figures/journals/memacct-04-host-fields.svg | 주요 호스트 지표와 포함 관계. 전체 물리 메모리를 나눈 비율이나 실측 메모리 구성도가 아니다.}}

AnonPages가 늘었다면 익명 상주 데이터 쪽을, SUnreclaim이 늘었다면 다른 커널 자원 쪽을 조사할 수 있다. 하나의 관측값만으로 누수라고 판단할 수는 없다. Copy-on-Write가 일어난 파일 매핑에도 익명 페이지가 포함될 수 있다. Dirty와 Writeback은 추가적인 독립 메모리 영역이 아니라 페이지의 상태다. 저장장치 지연이 페이지 회수에 영향을 주는 과정은 [Disk I/O와 Writeback 글](/projects/linux-disk-io-journaling-writeback/)에서 다뤘다.

## cgroup의 Charge는 PSS와 다르다

컨테이너는 호스트 커널을 공유한다. Memory Controller는 메모리를 여러 물리 머신으로 분리하는 대신 계층에 따라 사용량을 집계하고 제어한다. cgroup v2의 memory.current는 해당 cgroup과 하위 계층의 사용량을 포함한다. memory.stat에는 anon, file, kernel 등과 shmem, slab 같은 관련 세부 항목이 있으며 모두 독립적인 합산 항목은 아니다. 커널 버전별로 지원 항목도 다르다. Swap은 memory.swap.current에서 별도로 확인한다.

메모리를 처음 생성한 cgroup에 Charge가 잡히면 일반적으로 해제될 때까지 그곳에 남는다. 프로세스를 다른 cgroup으로 옮긴다고 이미 할당한 메모리까지 전부 이동하는 것은 아니다. 여러 cgroup이 공유하는 페이지도 PSS처럼 사용 비율에 따라 나뉘어 Charge되는 것은 아니다. 따라서 PSS는 상주 매핑의 비례 사용량을, memory.current는 매핑 밖의 메모리까지 포함하는 Controller의 귀속량을 보여주는 지표다.

{{figure /figures/journals/memacct-05-cgroup-hierarchy.svg | 가상의 계층 및 Charge 예시. 부모는 자식 사용량을 포함하고 공유 페이지의 Charge는 PSS와 동일한 방식으로 분배되지 않는다.}}

실제 조사에서는 우선 cgroup v1, v2 또는 혼합 환경인지 확인해야 한다. 당시 설정이 보존되지 않아 예제는 v2로 한정했다. Pod 아래에 컨테이너 cgroup이 있고 별도의 시스템 서비스나 다른 런타임은 다른 영역에 속할 수 있다. Pod 부모와 하위 컨테이너의 값을 함께 더하면 중복된다. 서로 겹치지 않는 일부 하위 계층을 합하더라도 호스트 전체와 같지는 않다.

memory.high는 회수와 Throttling을 유도하고 memory.max는 Charge의 강한 제한으로 회수에 실패하면 해당 범위에서 OOM이 발생할 수 있다. memory.events는 계층 이벤트를, memory.events.local은 해당 cgroup 자체의 이벤트를 센다. 재시작으로 cgroup이 새로 만들어지면 카운터 역시 달라질 수 있으므로 같은 대상을 같은 시간 구간에서 비교해야 한다.

## Kubernetes Working Set의 측정 범위

Kubernetes의 리소스 메트릭은 Memory Working Set을 보고한다. 운영체제와 통계 제공 방식에 따라 계산이 다르다. 대표적인 cAdvisor 구현에서는 사용량에서 cgroup 버전에 맞는 Inactive File 값을 빼고 음수라면 0으로 처리한다. 회수 가능한 일부 메모리도 포함될 수 있으므로 RSS나 PSS, 절대 회수할 수 없는 메모리와 동일하지 않다.

가령 사용량 1024 MiB와 Inactive File 384 MiB인 가상의 cgroup에서는 이 방식의 Working Set이 640 MiB가 된다. 전체 사용량이 같아도 Inactive File 변화에 따라 Working Set이 달라질 수 있다. 선택한 Pod 밖에서 발생한 메모리 증가 역시 해당 시계열에서는 보이지 않을 수 있다. 당시 Dashboard의 정확한 Query와 통계 제공자, 수집 시각은 보존되지 않아 이 계산을 당시 적용했던 공식이라고 단정하지 않았다.

{{figure /figures/journals/memacct-06-working-set.svg | Working Set의 가상 계산과 측정 범위 차이. 실제 8월 Dashboard의 Query 및 측정값이 아니다.}}

## 어떤 증거를 함께 남길 것인가

다시 조사한다면 동일한 시각과 Boot ID, 노드와 cgroup 식별자를 기준으로 기록할 것이다. 아래 명령은 당시 실행 결과가 아니라 읽기 전용 조사 예시다.

```bash
cat /proc/meminfo
cat /proc/pressure/memory
ps -eo pid,comm,rss,vsz --sort=-rss
cat "/proc/$PID/smaps_rollup"
cat "/proc/$PID/cgroup"
findmnt -t cgroup,cgroup2
```

호스트의 Mount Namespace에서 대상 v2 cgroup 경로를 확인한 뒤 제공되는 memory.current, memory.stat, memory.swap.current, memory.events 및 memory.events.local을 살필 것이다. 호스트 메트릭, 컨테이너 사용량과 Working Set의 수집 구간을 맞추고 부모 시계열 중복, Label Filter, 재시작 및 Scrape 누락도 확인할 필요가 있다. 그래프가 평평하더라도 Query 범위나 오래된 데이터 때문일 수 있다. PSI는 실행이 얼마나 지연됐는지를 보여주며 소유권 지표는 아니다. RSS 순위로 조사 후보를 좁힌 후 비교적 비용이 큰 smaps는 대상 프로세스 중심으로 수집하는 편이 좋다.

호스트 관리 데몬의 큰 RSS는 Pod 그래프 밖까지 범위를 넓힐 필요성을 보여주는 중요한 단서다. 다음 단계는 익명 상주 페이지인지 공유 매핑인지, 커널 Charge까지 포함하면 어떤 변화가 있었는지 같은 시각에 확인하는 것이다. 서비스 재시작을 통한 정상화와 할당 경로 규명, 재발 방지 검증은 별개다. 종료 대상으로 선택된 프로세스, 큰 상주 메모리를 가진 프로세스, Charge를 부담하는 cgroup, 지속적인 증가를 일으킨 원인을 서로 구분하는 것이 이번 기록의 핵심이다.

## 관련 기록과 참고 자료

- [메모리 압박과 EarlyOOM](/projects/rokaf-memory-pressure-and-service-recovery/) · [VFS와 Mount 생명주기](/projects/linux-vfs-mount-lifecycle/) · [Disk I/O와 Writeback](/projects/linux-disk-io-journaling-writeback/) · [모니터링 장애 증거](/projects/rokaf-observability-and-failure-evidence/)
- [Linux proc 파일시스템](https://docs.kernel.org/filesystems/proc.html) · [cgroup v2 Memory Controller 및 소유권](https://docs.kernel.org/6.6/admin-guide/cgroup-v2.html) · [Linux OOM Task Dump 소스](https://github.com/torvalds/linux/blob/master/mm/oom_kill.c)
- [Kubernetes Resource Metrics Pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/) · [cAdvisor Working Set 구현 관련 논의](https://github.com/kubernetes/kubernetes/issues/118916) · [PSI](https://docs.kernel.org/accounting/psi.html) · [memfd_create(2)](https://man7.org/linux/man-pages/man2/memfd_create.2.html)
