3월의 한 새벽, K3s 서버 한 대가 거의 응답하지 않았다. 메모리 사용량이 100%에 가까워졌고, 명령을 실행하거나 상태를 확인하는 일도 몹시 느려졌다. 결국 서버를 재부팅했다. 그때 내가 확인하고 싶었던 것은 '무슨 프로세스가 메모리를 다 가져갔는가'였지만, 재부팅하고 보니 이전 부팅의 Journal이 남아 있지 않았다. `journalctl --list-boots`에는 현재 부팅만 있었다.

당시 확인한 범위에서는 커널 OOM Killer가 실행됐다는 기록도 없었다. 그렇다고 OOM이 발생하지 않았다고 증명한 것은 아니다. **사용 가능한 메모리가 줄어 시스템이 멈춘 듯 느려지는 현상**과, 커널이 실제로 프로세스를 종료하는 OOM 이벤트는 다르다. 기록이 없으면 그 사이에 무슨 일이 있었는지 되돌려 볼 수도 없다.

이 문제를 겪고 EarlyOOM을 설치하고 운영하는 방법을 살폈다. 하지만 처음 부딪힌 문제는 메모리 부족이 아니라 EarlyOOM 자신의 systemd 실행 오류였다. 뒤이어 다른 시점에는 EarlyOOM의 종료 로그는 확인됐지만, 종료된 프로세스의 크기와 서버 전체 메모리 사용량이 맞아떨어지지 않았다. 서로 다른 날의 사건들을 나누어 정리했다.

## 메모리 포화와 OOM 로그의 차이

서버가 느려졌을 때는 메모리 사용률 하나보다 `MemAvailable`과 Swap 여유, 페이지 회수(Reclaim), Swap 입출력, 실제 프로세스와 cgroup 사용량이 중요했다. 메모리 사용률이 높더라도 회수 가능한 Page Cache가 많으면 곧바로 장애라고 할 수 없다. 반대로 사용 가능한 메모리가 부족하고 계속 페이지를 회수하거나 Swap으로 내보낸다면, 커널 OOM Killer가 실행되기 전부터 시스템 응답성이 크게 떨어질 수 있다.

3월의 사건에서는 이런 지표를 장애 직전에 같은 시각으로 수집하지 못했다. 재부팅 후 남아 있는 Journal도 현재 부팅뿐이어서, 커널 OOM 이벤트가 없었다는 결론을 낼 수는 없었다. **실제로 확인한 결과는 서버가 심하게 느려졌고 재부팅했다는 사실**이다. OOM 발생 여부와 메모리 소비의 원인은 확인되지 않았다.

Swap 사용률이 거의 가득 찬 다른 노드들도 살펴봤지만, Swap이 많이 사용됐다는 숫자 하나만으로 그 순간 계속 Swap I/O가 발생했다고 판단할 수는 없다. 사용률은 점유된 공간을 보여주고, `vmstat`의 `si`·`so`나 PSI의 Memory Pressure는 회수와 대기 상황을 다른 각도에서 보여준다. 실제 병목을 설명하려면 같은 시간의 지표가 필요했다.

### 프로세스가 참조하는 페이지와 회수할 수 있는 페이지

프로세스가 확보한 가상 주소 공간 전체가 물리 RAM에 올라와 있는 것은 아니다. 아직 접근하지 않은 익명 매핑에 쓰기를 하면 Page Fault를 거쳐 물리 페이지가 배정될 수 있다. 파일을 매핑한 경우에는 Page Cache에 있던 페이지를 참조하기도 하고, 여러 프로세스의 매핑이 하나의 물리 페이지를 가리키기도 한다.

이 차이는 메모리를 회수할 때 중요해진다. 수정하지 않은 파일 페이지는 원본 파일에서 다시 읽을 수 있으므로 버릴 수 있다. 수정된 파일 페이지라면 Writeback이 필요할 수 있다. 개인 데이터가 담긴 익명 페이지를 내보내려면 그 내용을 보존할 공간이 필요한데, 보통 Swap이 이 역할을 한다. 잠겨 있거나 회수할 수 없는 페이지라면 선택지가 더 줄어든다. MemAvailable은 Swap을 사용하지 않고 추가로 확보할 수 있는 메모리의 추정값이지, 지금 당장 비어 있는 페이지 수만을 뜻하지 않는다.

{{figure /figures/journals/memory-01-page-ownership.svg | 페이지의 참조 및 회수 가능성을 나타낸 개념도. 실제 물리 주소나 장애 당시 메모리 구성은 아니다.}}

### 페이지 회수가 응답 지연으로 이어지는 과정

커널의 페이지 할당기는 호스트 메모리 사용률 하나가 아니라 Zone별 Watermark를 기준으로 여유 페이지를 관리한다. 일반적인 회수 가능한 할당 경로에서는 여유 페이지가 부족해지면 kswapd가 깨어나 백그라운드에서 페이지를 회수한다. 압박이 더 심해지면 할당을 요청한 태스크가 직접 회수에 참여하는 Direct Reclaim이 일어날 수 있다. 회수에 성공하면 다시 할당을 시도한다. 회수와 Compaction으로도 요청을 만족하지 못하면 할당 조건과 Order, 허용된 메모리 영역 및 cgroup 제약에 따라 실패하거나 OOM 판단으로 넘어간다. 모든 할당 실패가 곧 OOM Killer 실행을 뜻하지는 않는다.

{{figure /figures/journals/memory-02-reclaim-path.svg | 회수를 허용하는 일반적인 할당 경로를 단순화했다. Watermark는 Zone별 기준이며 실제 재시도와 Compaction 조건은 생략했다.}}

Direct Reclaim이 발생하면 본래 애플리케이션 일을 처리하던 스레드가 페이지를 스캔하거나 회수 진전을 기다리는 데 시간을 쓰게 된다. 워크로드가 방금 내보낸 페이지를 다시 찾는다면 Fault와 회수가 반복될 수 있다. 이미 차 있는 Swap 공간과 지금 일어나는 Swap 입출력은 별개의 값이다. 오래전에 내보낸 페이지가 남아 있을 뿐 입출력이 거의 없을 수도 있고, 사용한 Swap 공간이 비교적 작아도 자주 다시 읽고 쓰면 시스템이 크게 느려질 수 있다.

그래서 pswpin·pswpout, pgscan_direct, pgsteal, Major Fault의 변화량과 Memory PSI, 저장장치 지연을 함께 보는 편이 좋다. PSI의 some은 적어도 하나의 태스크가 대기한 시간의 비율이고, full은 측정 범위에서 유휴 상태가 아닌 태스크 전체가 동시에 대기한 시간의 비율이다. 이 값들 역시 누가 메모리를 소비했는지 직접 알려주지는 않는다. 3월 사건에는 이러한 지표가 남지 않아 페이지 회수 지연을 확정 원인으로 쓰지 않았다.

{{figure /figures/journals/memory-03-pressure-signals.svg | Swap 점유율은 같지만 입출력과 대기 정도가 다른 두 가상의 관측값. 장애 당시 실측값이 아니라 점유율만으로 Thrashing을 판정할 수 없음을 보여주는 예시다.}}

## earlyoom systemd 실행 오류

메모리 포화로 서버가 오랫동안 멈추는 상황을 줄이려고 EarlyOOM 1.9.0을 소스에서 빌드했다. 인터넷이나 패키지 환경이 일정하지 않은 운영 환경이라 실행 파일을 직접 준비했던 기록이 남아 있다. 빌드 과정에서 Git 메타데이터와 `pandoc`이 없다는 메시지가 있었지만, 컴파일 자체는 진행됐다.

이후 systemd 서비스를 설정하면서 재시작 루프가 나타났다. 상태에는 **종료 코드 `16`이 기록됐고**, 로그에는 다음과 같은 메시지도 있었다.

`Failed to stop EXEC spawning /usr/local/sbin/earlyoom: No such file or directory`

한편 같은 바이너리를 직접 `earlyoom -d`로 실행했을 때는 동작했다. 처음에는 수동 실행이 되는데 Service만 실패하니 무작정 권한이나 프로세스 문제로 생각하기 쉬웠다. 하지만 이 둘은 실행 조건이 달랐다. `-d`는 백그라운드 데몬화가 아니라 **디버그 출력을 켜는 옵션**이다. 시스템 서비스의 환경변수, `ExecStart`·`ExecStop`, 실행 파일 경로와 옵션을 그대로 재현한 시험이 아니었다.

EarlyOOM 공식 매뉴얼은 종료 코드 `16`을 **Swap 임계값 매개변수 오류**로 정의한다. 따라서 이 코드가 실제 EarlyOOM 프로세스의 Exit Status라면 `-s` 또는 `-S`와 같은 Swap 관련 인자를 먼저 확인할 근거가 있다. 반면 위의 `Failed to stop EXEC spawning` 메시지는 systemd가 **종료 명령의 실행 파일을 찾지 못한 오류**다. 하나는 프로그램이 받은 인자의 유효성, 다른 하나는 systemd의 프로세스 실행 경로에 관한 단서다. 같은 로그 묶음에 있었다고 둘을 하나의 원인으로 단정할 수는 없다.

당시 `/etc/systemd/system/earlyoom.service.d/override.conf`의 `ExecStart` 재정의와 `/etc/default/earlyoom`의 `EARLYOOM_ARGS`를 검토했다. 기본 Unit의 실행 명령과 Drop-in이 실제로 어떻게 합쳐지는지, 참조한 바이너리 경로가 존재하는지, 설정이 옵션 문자열을 의도대로 전달하는지를 분리해서 볼 필요가 있었다. 기존 Drop-in을 정리하고 설정 파일 중심으로 관리하는 방향도 검토했지만, **최종적으로 어떤 Unit·옵션 조합이 안정적으로 장기간 실행됐는지 확인할 자료는 남아 있지 않다.**

{{figure /figures/journals/memory-pressure-earlyoom.svg | 메모리 포화, EarlyOOM 서비스 실행 오류, 프로세스 종료 기록은 서로 다른 사건의 증거다. 종료 코드 16과 실행 파일 경로 오류의 해석을 구분하고, 메모리 급증의 원인은 미확정으로 남겼다.}}

### 인자 해석 오류와 실행 파일 오류의 분리

1.9.0의 main.c를 보면 Swap 임계값 인자를 해석하는 과정은 감시 루프에 들어가기 전에 수행된다. 잘못된 -s 인자에서 fatal(16, ...)을 호출하고, -S 인자에도 Swap 관련 오류 경로가 있다. 즉 종료 코드 16은 프로그램이 옵션을 처리하면서 발생하는 오류이지 커널 OOM에 의해 프로세스가 종료됐다는 뜻이 아니다. 반면 실행 파일 경로 오류는 프로그램이 인자를 해석하기도 전에 발생한다. 당시 로그가 Stop 명령에서 나온 만큼 Start에도 같은 경로를 사용했는지까지 확정할 수는 없다.

이런 경우 systemctl cat/show로 합쳐진 Unit과 ExecStart, ExecStop, MainPID, ExecMainCode, ExecMainStatus를 먼저 확인하고 실제 설치 위치와 대조하는 편이 좋다. 실행 중인 프로세스의 /proc/PID/cmdline에서는 NUL 문자로 구분된 실제 인자 배열을 확인할 수 있다. ExecStart를 Drop-in에서 바꾸려면 일반적으로 빈 ExecStart 항목으로 상속된 명령 목록을 초기화한 다음 재정의한다. EnvironmentFile의 인자 확장도 일반 Shell과 동일하다고 가정해서는 안 된다. Unit 파일을 수정했다는 사실과 Manager가 변경을 반영하고 새 프로세스가 정상적으로 실행됐다는 사실은 별개다.

{{figure /figures/journals/memory-04-service-startup.svg | 실행 파일 확인과 인자 해석은 별개의 실패 지점이다. 두 오류가 관측됐으나 당시 실제 인자 전체와 최종 안정화 결과는 확인되지 않았다.}}

## EarlyOOM이 실행 중이어도 모든 압박을 막는 것은 아니다

EarlyOOM은 주기적으로 사용 가능한 메모리와 Swap 여유를 검사한다. 기본 정책에서는 **메모리와 Swap이 모두 설정한 임계값 이하일 때** 프로세스 종료를 판단한다. 두 값이 더 낮은 임계값까지 내려가면 처음부터 `SIGKILL`을 보낼 수 있다.

이는 커널의 OOM Killer와 다른 경로다. EarlyOOM은 Userspace에서 상태를 감시하고 프로세스를 선택하며, 커널 OOM Killer는 커널의 할당 실패나 cgroup 메모리 한도 등 자체 조건에서 동작한다. EarlyOOM 설치 사실만으로 메모리 압박이 사라지는 것은 아니다. 설정이 실제로 적용되고 서비스가 계속 실행돼야 하며, 종료된 프로세스가 충분한 메모리를 반환해야 한다.

확인할 때는 `systemctl status`에서 Active 여부만 보기보다 **실제 `ExecStart`와 적용된 Environment, 현재 프로세스의 인자, `journalctl`의 종료 신호 기록**을 비교해야 했다. 또 `-r`은 메모리 상태 보고 간격을 조정할 뿐, 메모리 압박 감지 주기를 그 숫자로 고정하는 옵션이 아니다. 지나치게 드문 보고 때문에 실행 여부를 판단할 자료를 놓칠 수도 있었다.

### 1.9.0의 임계값 계산과 감시 루프

버전에 따라 달라지는 중요한 부분도 있다. earlyoom 1.9.0에서는 메모리 여유 비율의 분모로 MemTotal이 아닌 MemAvailable과 AnonPages의 합인 user memory total을 사용한다. Swap 여유 비율은 SwapTotal을 기준으로 하며, Swap이 없으면 0%로 처리한다. 가령 전체 RAM 32 GiB, MemAvailable 2 GiB, AnonPages 18 GiB인 가상 상황이라면 earlyoom의 비율은 10%이고 MemTotal로 나눈 값은 6.25%다. 실제 서버의 수치가 아니라 계산 방식의 차이를 보여주는 예시다.

기본값은 메모리와 Swap의 TERM 임계값이 각각 10%, KILL 임계값이 각각 5%다. 소스코드에서는 두 값이 모두 임계값 이하인지 확인하고 SIGKILL 조건부터 검사한다. 메모리 여유가 4%, Swap 여유가 8%라면 SIGTERM이고, 둘 다 4%라면 곧바로 SIGKILL이다. 반드시 SIGTERM을 먼저 보내는 구조는 아니다. 한쪽이 TERM 임계값보다 높으면 기본 조건에서는 신호를 보내지 않는다. -m과 -s는 비율, -M과 -S는 KiB 단위의 크기를 입력받는다. 크기로 지정하면 시작 시 비율로 환산하고 두 방식이 함께 지정됐을 때에는 매뉴얼에 명시된 방식으로 조합한다.

{{figure /figures/journals/memory-05-earlyoom-thresholds.svg | 1.9.0 기본 설정의 판단 영역과 예시 점. 그림 생성 코드에서 경계값을 포함한 가상 입력 여섯 가지를 검증했으며 실제 프로세스에 신호를 보내지는 않았다.}}

감시 루프는 /proc/meminfo를 읽고 신호를 판단한 뒤 종료 후보를 선택한다. 후보를 탐색하는 사이 메모리 상황이 좋아졌을 수 있으므로 다시 메모리 정보를 읽어 불필요한 종료를 피한다. 소스의 적응형 Sleep은 100–1000ms 사이로 제한되지만, 시스템이 심하게 느려진 상황에서도 그 주기를 지킨다는 보장은 없다. 정기 보고 간격과 감지 주기를 혼동해서도 안 된다. 결국 Userspace 감시 프로세스가 CPU 시간을 얻고 메모리에 접근하고 대상에게 신호를 보낼 권한이 있어야 한다. 대상을 종료했다고 바로 예상한 만큼 메모리가 반환되는 것도 아니다.

### 서로 다른 OOM 판단 범위

호스트에서 발생하는 커널 OOM, cgroup OOM, earlyoom은 같은 메커니즘이 아니다. 커널은 할당을 만족시키지 못한 범위에서 OOM 판단을 할 수 있다. cgroup v2의 memory.high는 회수와 Throttling을 유도하고, memory.max는 회수로 해결하지 못할 때 해당 cgroup 범위에서 OOM이 발생할 수 있는 한도다. 따라서 호스트에 여유 메모리가 있어도 cgroup 한도에 걸릴 수 있다. earlyoom은 자신이 볼 수 있는 호스트 메모리 지표를 감시하고 접근 가능한 종료 후보를 자체 정책에 따라 선택한다.

{{figure /figures/journals/memory-06-oom-scopes.svg | 세 가지 판단 경로의 조건과 확인할 증거를 비교했다. 한 경로의 종료 기록이 다른 경로에서 발생한 종료를 증명하지는 않는다.}}

earlyoom의 신호 전송 기록, 커널 OOM 기록, cgroup의 oom 및 oom_kill 카운터 증가, Kubernetes의 OOMKilled 상태는 각각 다른 증거다. kubelet의 Eviction 또한 별도 경로가 될 수 있다. 단순히 종료 코드 137 하나를 보고 어느 메커니즘이 동작했는지 판단하기보다 동일한 시각의 프로세스와 해당 cgroup의 이벤트 변화량을 비교해야 한다.

7월에는 보존된 로그에서 EarlyOOM의 `SIGTERM`·`SIGKILL`이나 커널 OOM 흔적을 찾으려 했지만 결과가 나오지 않았다. 그 시점의 기록은 **검색한 로그 구간에 해당 메시지가 없었다는 사실**만 보여준다. 짧은 압박이 없었다거나 서비스가 시스템을 확실히 보호했다는 증거는 아니었다.

## earlyoom 종료 로그와 원인 미확정

8월에는 다른 메모리 급증을 조사했다. 호스트 전체 메모리 사용량이 평소 약 20% 수준에서 거의 100%까지 상승한 구간이 있었지만, 그때 수집된 Kubernetes 컨테이너 지표에서는 그 크기에 대응하는 사용량 증가를 찾지 못했다. 메트릭이 수집된 시간대와 Pod별 값을 함께 봤기 때문에, 적어도 **확인한 Pod 지표만으로 호스트 전체 증가분을 설명하기 어려웠다**고 말할 수 있었다.

EarlyOOM의 종료 대상이 된 프로세스에서는 `VmRSS`가 약 **608 MiB**로 확인됐다. 이 숫자만으로 그 프로세스가 급격한 메모리 사용량 증가를 일으켰다고 생각하기는 어려웠다. 그렇다고 EarlyOOM이 반드시 잘못된 프로세스를 선택했다고 증명한 것도 아니다.

EarlyOOM은 기본적으로 가장 큰 RSS가 아니라 `oom_score` 등을 기준으로 종료 대상을 선택한다. 프로세스 하나의 `VmRSS`는 그 프로세스가 사용하는 물리 메모리의 일부 관측값이고, 호스트의 전체 메모리 사용량을 구성하는 익명 페이지, Shared Memory, Page Cache, Kernel Slab이나 다른 컨테이너·프로세스의 사용량과 같지 않다.

여기에 메모리의 소유권과 종료 대상 선정이라는 또 다른 차이가 있다. RSS는 실제 상주한 매핑을 세므로 여러 프로세스가 같은 페이지를 공유한다면 중복해서 집계할 수 있다. PSS는 공유 페이지의 비용을 나눠 계산한다. 개별 프로세스 RSS나 선택한 Pod Working Set 지표의 합만으로 호스트 전체 메모리를 설명할 수는 없다. 608 MiB는 종료 후보를 관측한 값이지 종료 후 실제 반환된 메모리 크기가 아니다. 다른 메모리 영역이 더 큰 비중을 차지하더라도 OOM Score가 높은 프로세스가 종료 후보가 될 수 있다.

그래서 이 시점에는 범위를 넓힐 필요가 있었다. K3s가 관리하는 컨테이너뿐 아니라 같은 호스트의 다른 Runtime이나 서비스 cgroup, `AnonPages`, `Shmem`, `Cached`, `SUnreclaim`와 같은 호스트 메모리 구성값을 같은 시각에 비교해야 했다. `memory.current`·`memory.stat`·`memory.events`를 살피는 방법도 검토했다. 하지만 실제로 어떤 cgroup이나 커널 메모리 항목이 급증분을 차지했는지 **확정된 결론은 없다**.

여기에서 확인된 것은 EarlyOOM이 적어도 해당 시점에는 프로세스 종료를 수행했다는 사실과, 선택된 한 프로세스의 RSS만으로 전체 메모리 급증을 설명할 수 없었다는 점이다. 3월의 서비스 설정 문제를 해결한 결과가 8월 사건에서 그대로 검증됐다고 기록할 근거는 없다.

추가로 확인한 8월 말 OOM Task Dump에는 상주 메모리가 큰 호스트 관리 데몬의 기록이 있었다. [호스트 메모리 Accounting 글](/projects/linux-host-memory-accounting-cgroups/)에서 단위와 추가 조사 단서를 다뤘다. 다만 이 기록만으로 최초 할당 경로나 위 관측과 동일한 시각의 증가분을 확정할 수는 없다.

## 다음 장애에는 무엇을 남겨야 할까

메모리 압박 조사를 다시 한다면 한 장의 사용률 그래프 대신 같은 시각의 지표를 함께 남길 것이다.

| 확인할 곳 | 필요한 기록 | 아직 확인하지 못했던 것 |
| --- | --- | --- |
| 호스트 메모리 | `MemAvailable`, `SwapFree`, `AnonPages`, `Shmem`, `Cached`, Slab | 전체 증가분의 구성 |
| 페이지 회수 | `vmstat`의 Swap I/O·Reclaim, Memory PSI | 시스템 지연의 직접 원인 |
| 워크로드·cgroup | Pod·비Pod 서비스의 `memory.current`, `memory.stat`, `memory.events` | 어떤 영역이 사용량을 늘렸는지 |
| EarlyOOM 서비스 | 실제 Unit, `EARLYOOM_ARGS`, Exit Status, 종료 대상 | 올바른 설정으로 계속 실행됐는지 |
| 재시작 전 로그 | Kernel OOM, EarlyOOM 종료, 프로세스·cgroup 스냅샷 | 장애 직전 원인과 복구 후 차이 |

메트릭을 남길 때에는 측정 시각과 Boot ID, 어느 노드와 cgroup에서 얻은 값인지도 함께 기록할 것이다. 호스트의 Cached와 Shmem 등은 일부 중첩될 수 있고 cgroup의 상위 항목과 하위 항목 역시 단순히 합치면 중복 집계가 된다. cgroup v2에서 memory.events는 계층의 이벤트를, memory.events.local은 해당 cgroup 자체의 이벤트를 보여주므로 동일한 대상을 추적하면서 변화량을 비교해야 한다.

Journald의 영속 저장은 재부팅 전후의 기록을 이어 볼 수 있게 하는 방법이다. 다만 보존 기간과 디스크 여유도 같이 고려해야 한다. 시스템이 느려져 직접 조회하기 어려운 상황에 대비해 가벼운 주기적 스냅샷이나 외부 수집도 검토할 만하다. 이전 부팅의 Journal을 실제 조회할 수 있는지, 수집 시각이 서로 맞는지까지 확인해야 기록 체계가 제대로 작동한다고 판단할 수 있다.

실제 서비스에 메모리 부하를 인위적으로 걸어 시험했다는 뜻은 아니다. 운영 중인 시스템에서 무리하게 메모리를 채워 OOM을 재현하는 것보다, 우선 필요한 메트릭과 로그를 보존하도록 준비하는 편이 적절했다.

3월에는 호스트 메모리 포화와 재부팅을 겪었고, earlyoom 1.9.0을 설정하면서 systemd 종료 코드 `16`과 실행 파일 경로 오류를 조사했다. 수동 실행은 정상이었지만 서비스 실행 경로에는 별도 문제가 있었다. 7월에는 검색한 로그에서 종료 기록이 발견되지 않았고, 8월에는 earlyoom의 프로세스 종료 로그와 호스트 메모리 급증을 확인했다. **메모리 급증을 유발한 프로세스·cgroup은 아직 특정하지 못했으므로**, 다음 장애에서는 OOM·earlyoom 로그와 cgroup별 메모리 변화를 같은 시점에 남기는 것이 우선이다.

## 관련 기록과 참고 자료

- [모니터링 장애: Prometheus WAL·node-exporter·DCGM](/projects/rokaf-observability-and-failure-evidence/)
- [K3s Control Plane 장애: etcd와 디스크 Read-only](/projects/rokaf-control-plane-incident-log/)
- [earlyoom 1.9.0 매뉴얼](https://sources.debian.org/src/earlyoom/1.9.0-1/MANPAGE.md)
- [earlyoom 1.9.0 설정과 실행](https://sources.debian.org/src/earlyoom/1.9.0-1/README.md)
- [Linux 커널 — Control Group v2 Memory](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

- [earlyoom 1.9.0 main.c](https://sources.debian.org/src/earlyoom/1.9.0-1/main.c/) · [Linux 메모리 관리 개념](https://docs.kernel.org/admin-guide/mm/concepts.html) · [물리 메모리와 Watermark](https://docs.kernel.org/mm/physical_memory.html)
- [PSI](https://docs.kernel.org/accounting/psi.html) · [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) · [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html) · [Journald 저장](https://www.freedesktop.org/software/systemd/man/257/systemd-journald%40.service.html)
