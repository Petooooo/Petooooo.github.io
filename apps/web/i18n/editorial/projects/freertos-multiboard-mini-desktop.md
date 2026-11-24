> **2023년 『RTOS를 이용한 Mini Desktop 설계』 최종 보고서를 다시 읽으며 정리한 글이다.** 세 개의 STM32 보드가 함께 동작하도록 만든 대학 팀 프로젝트였다. 나는 전체 구조와 임베디드 로직, RTOS 기반 작업 간 조율에 참여했다. 당시 보고서에는 블록 다이어그램, GPIO 연결표, C 코드, 실제 보드 사진과 터미널 화면, 소스 코드 부록이 남아 있다. 이 글의 SVG는 그 자료를 바탕으로 다시 그린 설명용 도식이며, **원본 화면을 그대로 옮긴 것도 새로 측정한 하드웨어 실험 결과도 아니다.**

STM32 세 대 위에서 '데스크톱'을 만든다는 말은 처음부터 조금 모호했다. PC의 창 관리자를 흉내 내겠다는 뜻은 아니었다. 버튼으로 커서를 움직이고, 창을 겹쳐 놓고, 작은 프로그램 두 개를 실행하는 동안에도 입력과 센서 측정, 화면 출력이 서로 발목을 잡지 않게 만드는 것이 목표였다.

보고서에 적힌 요구사항은 커서 조작, 여러 애플리케이션의 동시 실행, 무입력 상태를 감지한 Sleep/Resume이었다. 이를 세 개의 보드와 총 10개의 FreeRTOS Task로 나누어 구현했다. 지금 다시 보면 흥미로운 부분은 Task의 개수보다 **각 보드가 어떤 상태를 책임지고, 그 상태를 어떤 신호로 다른 보드에 전달했는가**에 있다.

## 세 보드가 하나의 화면을 만들기까지

{{figure /figures/journals/mini-desktop-01-overall-system.svg | 원본 보고서의 전체 구성도를 바탕으로 재구성한 세 보드의 역할. 각 Task 번호는 보고서와 소스 부록의 번호를 따른다.}}

Board 1은 초음파 거리와 절전 상태를, Board 2는 버튼과 커서 입력을, Board 3은 화면 구성과 게임을 담당했다. 번호로 보면 Board 1에는 Task 1·5·8, Board 2에는 Task 2·3·4, Board 3에는 Task 6·7·9·10이 놓였다. 한 보드가 모든 입력을 모아 처리하는 구조가 아니라 각 보드가 자기 역할을 수행하고 필요한 결과만 밖으로 내보내는 구조였다.

이 글을 다시 쓰면서 이전 설명의 중요한 오류도 고쳤다. **보드 사이의 제어 신호와 6-bit 거리 데이터는 UART가 아니라 GPIO로 전달했다.** UART2는 Board 3이 조립한 ASCII 화면을 PC 터미널에 보내는 경로였다. 각 보드의 디버깅에 UART를 사용한 코드가 있더라도 그것을 보드 간 주 통신 수단으로 볼 수는 없다.

{{figure /figures/journals/mini-desktop-02-gpio-versus-uart.svg | 보드 간 GPIO 신호와 PC 터미널을 향하는 UART2의 역할을 구분했다. 두 경로의 지연과 일관성 문제는 서로 다르다.}}

GPIO에서는 여러 Pin의 현재 상태를 읽어 하나의 의미로 해석한다. 반면 UART 출력은 문자의 연속이다. 화면 문자열을 전송하는 도중 버퍼가 바뀌면 사용자는 서로 다른 시점의 문자가 뒤섞인 화면을 보게 될 수 있다. 같은 '통신'으로 묶어 설명하기보다 두 경로의 문제가 어디에서 생기는지 따로 보는 것이 정확하다.

## Board 1: 초음파 거리 측정과 절전 판단

Board 1의 세 작업은 `ULTRASONIC_Task`, `SleepCount_Task`, `SleepButton_Task`였다. 원본 생성 코드의 우선순위는 차례로 2, 1, 3이다. 버튼으로 절전을 요청하는 경로를 다른 두 작업보다 높은 우선순위에 두어 센서 측정이나 카운터 처리 중에도 반응하도록 의도했다.

{{figure /figures/journals/mini-desktop-03-board1-original.svg | 초음파 센서, 무입력 카운터, 수동 Sleep 버튼을 담당하는 Board 1의 세 작업을 원본 구성에 맞춰 재구성했다.}}

거리 센서는 HC-SR04였다. `PA5`로 TRIG를 내보내고 `PA6`의 ECHO를 `TIM3 Input Capture`로 읽었다. TRIG에 최소 10µs의 HIGH Pulse를 주면 센서가 측정을 시작하고, 돌아오는 ECHO의 HIGH 지속 시간을 이용해 거리를 계산했다. Task Delay만으로 짧은 펄스를 쫓기보다 타이머 하드웨어에서 상승·하강 에지를 포착한 것이다.

{{figure /figures/journals/mini-desktop-04-ultrasonic-input-capture.svg | TIM3 Input Capture에서 ECHO의 Rising/Falling Edge를 잡아 시간 차이를 얻는 과정. 측정 파형의 실측 기록이 아니라 원본 설계의 동작을 설명한 도식이다.}}

보고서에서 가정한 타이머 단위와 음속 근사를 사용하면 계산은 다음과 같다.

`Distance(cm) = Difference(µs) × 0.034 / 2`

왕복 시간으로부터 한쪽 방향의 거리를 구하므로 2로 나눈다. 원본 코드에서는 타이머 Overflow, 예상과 다른 에지 순서, 다음 이벤트를 위해 Input Capture Polarity를 바꾸는 문제도 다뤘다. 센서를 한 번 읽는 함수보다 이런 경계 조건을 처리하는 로직이 중요했다.

다른 방법도 검토했었다. RTOS Tick으로 ECHO 시간을 재려 했지만, 보고서에는 충분한 분해능을 얻지 못한 시도가 남아 있다. Tick 간격이 1ms라면 같은 근사에서 **한 Tick이 약 17cm의 편도 거리**에 해당한다. 센티미터 단위의 상호작용을 구현하기에는 거칠기 때문에 TIM3 Input Capture를 사용했다. 이것이 당시 구현에서의 판단이지, 모든 FreeRTOS 설정이 같은 Tick 해상도에 묶인다는 뜻은 아니다.

### 측정값을 6개의 GPIO 선으로 나누다

측정한 거리는 **63cm를 상한으로 제한**했다. 6-bit로 나타낼 수 있는 범위가 0–63이기 때문이다. Board 3은 `PC9`, `PC8`, `PB8`, `PC6`, `PB9`, `PC5`에서 각각 Distance의 bit 5부터 bit 0까지 읽었다.

{{figure /figures/journals/mini-desktop-05-distance-sixbit-gpio.svg | 6-bit 거리 값을 전달한 GPIO Pin Map. Pin과 Bit의 대응은 원본 소스의 Board 3 입력 정의에 근거한다.}}

사용자의 존재를 감지하는 센서와 입력이 없었던 시간을 세는 로직은 별개의 판단 경로였다. 초음파 Presence Flag, 비활동 카운터, 버튼과 Move Enable에 의한 카운터 초기화가 함께 등장한다. 원본에는 **약 15초 동안 입력이 없을 때 자동 Sleep을 요청하는 규칙**과 수동 Sleep 버튼 경로가 기록되어 있다.

{{figure /figures/journals/mini-desktop-10-sleep-entry-logic.svg | 무입력에 따른 자동 Sleep 요청과 수동 버튼 경로. 작업 상태의 변화이며 측정된 RTOS 응답시간 그래프는 아니다.}}

우선순위 3이라는 값만으로 버튼 반응시간의 상한이 증명되지는 않는다. 보고서는 의도한 우선순위 설정과 최종 화면 전환을 보여주지만, 인터럽트부터 화면이 바뀌기까지의 Worst-case Latency를 따로 측정하지는 않았다.

## Board 2: 다섯 개의 버튼을 커서 입력으로 바꾸기

Board 2는 전기적으로 단순해 보이지만 스케줄링과 출력 상태의 충돌을 생각해야 했다. `CLICK_Task`는 B1 버튼을, `MOVE_Task`는 네 방향 스위치를, `NONE_Task`는 이동하지 않는 상태를 처리했다. 출력에는 Click용 `PC1`, 방향용 `PA7`·`PA6`, Move Enable용 `PB6` 등이 사용됐다.

{{figure /figures/journals/mini-desktop-06-board2-original.svg | 버튼 입력을 Click, Move, None으로 나누고 GPIO 출력으로 연결한 Board 2의 동작 구조.}}

상하좌우 네 방향을 두 Bit로 표현했다. Board 3의 Decode Logic에서 `PC0`·`PC1`의 조합이 방향을 나타내고, `PC2`의 Enable 값이 실제 이동 여부를 결정했다.

{{figure /figures/journals/mini-desktop-07-cursor-direction-encoding.svg | Board 3 입력 기준으로 정리한 방향 코드. Enable이 0이면 방향 Bit와 관계없이 커서는 멈춘다.}}

Enable이 1일 때만 두 방향 Bit를 해석했다. Click 신호는 이동과 동시에 유지할 수 있었다. 이 조합 덕분에 창을 한 번 선택하는 데서 그치지 않고, 제목 표시줄을 누른 상태에서 방향 버튼으로 창을 끌어 움직일 수 있었다.

그런데 Move와 None 출력이 서로 충돌하는 문제가 있었다. 둘 다 GPIO 상태를 갱신하면서 배타적이어야 할 상태가 함께 나타난 것이다. 이를 막기 위해 공유 커서 Mutex로 Move/None 경로를 조율했다. 반면 `CLICK_Task`는 이동 중에도 Click을 유지할 수 있도록 독립된 작업으로 두었다.

### 원본 코드에 남은 우선순위의 불일치

과거 설명에는 방향 입력이 있을 때 **Move가 None보다 우선한다**는 의도가 적혀 있다. 하지만 보고서 부록의 실제 `xTaskCreate` 코드에서는 `MOVE_Task`의 우선순위가 1, `NONE_Task`의 우선순위가 2이고 `CLICK_Task`도 2였다. 일반적인 FreeRTOS 스케줄링에서는 숫자가 높은 쪽이 우선하므로 설명과 코드가 일치하지 않는다.

{{figure /figures/journals/mini-desktop-09-task-priority-source.svg | 세 보드의 Task 생성 우선순위를 원본 부록에 근거해 정리했다. Board 2의 Move/None 불일치도 숨기지 않았다.}}

어떤 버전이 최종적으로 보드에 Flash되었는지는 남은 자료만으로 단정할 수 없다. 검증하려면 실제 실행 바이너리의 Task Priority를 읽고 버튼이 바뀔 때 Mutex를 누가 소유하는지 확인해야 한다. 또 세 보드가 각각 별개의 FreeRTOS Scheduler를 가지므로, 10개의 Task에 하나의 전역 우선순위가 존재하는 것처럼 해석해서도 안 된다.

## Board 3: 네 개의 Task가 하나의 터미널 화면을 공유하다

Board 3의 `PrintNCalculate_Task`는 커서 좌표와 창의 위치, 직렬 출력 화면을 관리했다. `Sleep_Task`는 화면 상태를 바꾸었고, `Gomoku_Task`와 `Curling_Task`는 각 게임의 배열과 상태를 갱신했다.

{{figure /figures/journals/mini-desktop-08-board3-original.svg | PrintNCalculate, Sleep, Gomoku, Curling Task로 이루어진 Board 3. 입력은 GPIO로 받고 화면 문자열은 UART2로 전송했다.}}

실제 출력 장치는 LCD가 아니었다. Board 3이 **ASCII 문자 프레임**을 만든 뒤 UART2로 PC 터미널에 보냈다. 보고서의 화면에는 바탕화면 버튼, Gomoku와 Curling 창, 점과 격자, 돌, 점수, 목표 표시가 함께 보인다.

{{figure /figures/journals/mini-desktop-13-terminal-ui-gomoku-curling.svg | 원본 터미널 화면에 나타난 Gomoku·Curling의 ASCII 창을 벡터 문자로 재구성했다. 원본 Screenshot과 Pixel 단위로 동일한 이미지는 아니다.}}

문자 기반 출력이라서 화면을 어떻게 겹쳐 그릴지, 출력 중에 상태가 바뀌면 어떻게 할지 결정해야 했다. `gomokuScreen`, `curlingScreen`, `isClick`, `isChange` 같은 Flag와 `gomokuArray`, `curlingArray`가 그 판단에 사용됐다.

### 화면이 바뀌었을 때만 다시 조립하기

Renderer는 바탕화면, 아래에 놓인 창, 활성 창, 커서를 현재 상태에 맞게 합성했다. 원본 설명에는 **좌표 계산에 약 50ms, UART 출력에 약 200ms**가 필요했다는 기록이 있다. 그래서 화면 변화 여부를 나타내는 `isChange`를 활용하고, 같은 PrintNCalculate 작업 안에서 계산과 출력을 조율했다.

{{figure /figures/journals/mini-desktop-12-ascii-compositor.svg | 배경부터 활성 창과 커서까지의 화면 계층과 변화 Flag. 50ms·200ms는 당시 소스 설명의 값이지 새로 측정한 Benchmark가 아니다.}}

이 수치만으로 화면이 언제나 5fps를 보장했다고 주장할 수는 없다. UART 전송 속도를 따로 검증한 기록도 아니다. 핵심은 입력을 처리하는 빈도와 긴 화면 프레임을 출력하는 빈도가 같을 필요는 없다는 설계 선택이다.

### CoordinateMutex가 필요했던 이유

초기에는 게임 Task가 배열을 고치는 도중 PrintNCalculate가 문자 프레임을 출력하면서 **이전 화면과 새 화면의 문자가 뒤섞이는 문제**가 있었다. Task를 더 많이 만드는 것으로는 해결되지 않는 종류의 문제였다.

{{figure /figures/journals/mini-desktop-11-coordinate-mutex-tearing.svg | 공유 배열이 출력 중 바뀔 때의 화면 혼합을 설명한 예시와 Mutex로 보호한 경우. 관측된 문제의 재구성이며 실제 캡처는 아니다.}}

그래서 `CoordinateMutex`로 화면 좌표와 게임 배열의 공유 접근을 보호했다. 일관된 Frame을 조립하고 보내는 것이 목적이었다. 다만 긴 UART 출력 동안 Lock을 잡고 있으면 입력 작업이 기다리는 시간이 늘어날 수도 있다. 원본은 Mutex의 필요성과 화면 혼합 현상을 기록하지만 Lock Hold Time은 측정하지 않았다. 따라서 보호 범위를 얼마나 짧게 유지할 수 있는지는 여전히 남는 설계 질문이다.

## 창을 끌어 움직일 때 비로소 데스크톱처럼 보였다

원본 결과에는 Gomoku 창을 끌어 이동시키기 전과 후의 터미널 화면이 남아 있다. B1으로 Click 상태를 유지하고 SW1–SW4로 방향을 입력했다. 커서가 창의 제목 표시줄에 있고 Drag 상태가 활성화되어 있을 때 창 좌표를 갱신했다.

{{figure /figures/journals/mini-desktop-14-window-drag-before-after.svg | Gomoku 창의 Drag 전후 상태를 벡터로 다시 표현했다. 원본 이미지의 위치 변화는 참고했지만 저해상도 픽셀을 확대하거나 그대로 따라 그린 것은 아니다.}}

동시에 Gomoku와 Curling을 띄우는 장면도 있다. 한 창을 클릭하면 앞으로 가져오면서 다른 게임의 상태는 유지했다. 아무 프로그램이나 설치할 수 있는 범용 PC가 아니라, **서로 다른 FreeRTOS 애플리케이션이 하나의 일관된 인터페이스를 공유하도록 만든 것**에 가까웠다.

## Gomoku와 거리로 조작하는 Curling

Gomoku에서는 빈 교차점을 클릭하면 돌을 놓고 O와 X가 번갈아 진행했다. 이미 돌이 있는 칸을 클릭해도 차례가 넘어가지 않도록 했다. 게임 Task가 배열을 갱신하면 Renderer가 다음 화면에서 이를 표현했다.

Curling은 하드웨어 연결이 더 직접적으로 드러나는 기능이었다. 병뚜껑 같은 물체를 초음파 센서 쪽으로 움직이면 Board 1이 거리를 측정해 6-bit GPIO로 내보냈다. Board 3의 Curling Task가 그 Distance 값에 따라 화면의 공과 점수를 바꾸었다. 원본 설명에는 **약 15cm에 놓인 목표 지점**, **50cm 이내에서 확인하는 움직임**, 그리고 Player 1의 점수가 **9점에서 19점으로 10점 올라간 화면**이 나온다.

{{figure /figures/journals/mini-desktop-15-curling-distance-game.svg | 6-bit 거리 입력이 Curling의 공 위치와 점수로 이어지는 과정. 예시 점수는 원본 보고서의 실행 화면을 근거로 한다.}}

6-bit라는 사실은 표현 가능한 거리 값의 상한을 설명하지만 센서의 실제 정확도나 지연을 증명하지는 않는다. 이 글을 위해 게임을 새로 구동해 시험한 것도 아니다. 점수 변화는 당시 보고서의 화면과 설명에 한정해서 해석했다.

## Sleep은 단순히 검은 화면을 내보내는 기능이 아니었다

Board 3의 `Sleep_Task`는 Sleep GPIO를 읽고 `screenState`, `isChange`를 변경했으며 `SleepMutex`로 관련 작업을 조율했다. 게임 Task들도 절전 상태에서 기다렸다가 돌아올 수 있도록 동기화에 참여했다.

{{figure /figures/journals/mini-desktop-16-sleep-resume-screen.svg | 활성 화면에서 Blank Screen으로 넘어가고 돌아오는 상태 전환. 모든 Task가 실제로 Suspend됐다는 측정 증거로 보아서는 안 된다.}}

그렇다고 '10개 Task가 모두 정지했다'고 적을 수는 없다. 보고서에서 확인되는 것은 **화면 전환과 게임 Task의 Mutex 기반 대기**다. 보드마다 별도 Scheduler가 돌고 있고 관리용 작업도 존재하므로, 세 보드 전체가 완전히 Suspend되었다는 주장은 기록보다 앞서간다.

최종 화면에는 Curling이 실행 중인 상태에서 Sleep 버튼을 누르자 터미널이 비어 있는 모습이 남아 있다. 중요한 것은 검은 화면을 출력했다는 사실만이 아니라 화면 상태와 각 애플리케이션의 실행 상태를 함께 다루려 했다는 점이다.

## 최종 보고서가 증명하는 범위

원본 결과는 커서 Drag, Gomoku와 Curling 창의 동시 표시, 버튼에 따른 Blank Screen 전환을 보여준다. 소스 부록에는 세 보드의 Task 생성, GPIO Pin 정의, 동기화 코드가 있고 설계 과정에서 겪은 출력 충돌 문제도 기록돼 있다.

하지만 Worst-case Latency 분석, 최악 응답시간 보장, 실측 전력 절감량은 제시되지 않았다. Move/None의 우선순위처럼 서술과 코드가 어긋난 부분도 남아 있다. 이런 불일치를 지워 완벽한 구현처럼 꾸미는 것보다, 당시 무엇을 확인했고 지금 무엇을 더 검증해야 하는지 나누어 두는 편이 이 프로젝트의 기술적 의미를 더 정확하게 보여준다.

## 세 개의 프로그램이 하나의 시스템이 된다는 것

처음에는 STM32 세 대가 각각 별개로 동작하는 프로그램처럼 느껴졌다. 입력과 게임 상태, 화면을 실제로 연결하고 나서야 경계가 보이기 시작했다. GPIO의 한 Bit와 UART의 긴 문자열은 전혀 다른 책임을 갖고 있었고, Mutex는 이름만 붙여 놓는 것이 아니라 **구체적으로 어떤 공유 데이터를 언제 보호해야 하는지** 설명할 수 있어야 했다. Task Priority 역시 주변 작업과의 관계를 이해할 때 비로소 의미가 생겼다.

작은 Mini-Desktop이었지만, Scheduling과 데이터의 소유권, Synchronization을 따로 배울 항목이 아니라 하나의 시스템 설계 문제로 생각하게 된 경험이었다. 이후 임베디드 소프트웨어와 인프라를 다루면서도 이 관점이 계속 남았다.

**자료:** 『RTOS를 이용한 Mini Desktop 설계』, 2023년 대학 팀 프로젝트 최종 보고서, 본문 2–32쪽 및 소스 부록 33–64쪽. 원본 사진과 Screenshot은 이 글에 재배포하지 않았다. 그림 제작 스크립트와 원본 근거 설명은 포트폴리오 저장소에 남겨두었으며, 추가 SVG는 새 하드웨어 측정 결과가 아니라 설명을 위한 재구성이다.
