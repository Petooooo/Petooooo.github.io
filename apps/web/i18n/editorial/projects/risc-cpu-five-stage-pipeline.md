2024년 5~6월에는 두 명이 한 팀을 이루어 **Verilog 기반 5단계 RISC CPU, RISC TOY**를 구현했다. IF·ID·EX·MEM·WB 구조로 명령어를 처리하는 프로세서였고, 나는 데이터 경로와 제어 로직을 구성하면서 **Forwarding, Load-use Stall, Branch·Jump에 따른 Control Hazard, Register File의 Writeback 타이밍**을 직접 다뤘다. 명령어를 조합한 Testbench로 레지스터 값과 실행 흐름도 확인했다.

당시에 남긴 13쪽 설계 보고서를 다시 읽어보니, 이 프로젝트에서 가장 오래 고민했던 부분이 무엇이었는지 선명하게 드러났다. 명령어 하나를 실행하는 ALU보다 어려웠던 것은 **여러 명령어가 동시에 파이프라인에 들어와 있을 때 어떤 레지스터 값을 읽어야 하는지, 그리고 언제 다음 단계로 진행해도 되는지** 결정하는 일이었다.

이 글은 **2024년에 구현한 내용을 원본 설계 보고서와 Verilog 코드, 테스트 결과를 바탕으로 2026년 11월에 다시 정리한 기록**이다. 프로젝트 기간과 글을 작성한 시점은 구분했다.

## IF·ID·EX·MEM·WB를 연결한 전체 구조

이 프로세서는 **Instruction Fetch(IF) → Instruction Decode(ID) → Execution(EX) → Memory Access(MEM) → Writeback(WB)** 순서로 명령어를 실행하도록 구성했다. 하지만 실제 설계에서는 단계를 다섯 개로 구분하는 것보다 각 단계 사이에 어떤 값과 제어 신호를 저장할 것인지가 더 중요했다.

{{figure /figures/journals/risc-five-stage-hazards.svg | 2024년 RISC TOY 설계 보고서를 바탕으로 다시 그린 데이터 경로다. PC·Instruction Memory·Register File·ALU·Data Memory·Writeback을 연결하고, Forwarding과 Stall 제어가 개입하는 위치를 표시했다.}}

각 단계의 실제 역할은 다음과 같다.

| 단계 | 구현 내용 | 주요 신호 |
| --- | --- | --- |
| IF | PC를 4씩 증가시키거나 분기 주소로 변경하고, 명령어를 읽어옴 | `PC`, `IREQ`, `IADDR`, `INST_M` |
| ID | 명령어를 저장하고 Register File의 읽기 주소와 제어 신호를 결정 | `INST`, `STORE`, `rb_ADDR_M`, `rc_ADDR_M` |
| EX | ALU 연산, Shift·Rotate, 메모리 주소 계산, 분기 조건 판단 | `op_EX`, `valB`, `valC`, `ALU_OUT_M`, `BRANCH` |
| MEM | ALU 결과와 메모리 제어 신호를 전달하고 Load·Store를 처리 | `dest_MEM`, `DREQ_MEM`, `DRW_MEM`, `MOUT_M` |
| WB | 계산·읽기 결과를 Register File에 기록할 시점과 경로를 제어 | `dest_WB`, `WEN_WB`, `*_MA` |

원본 코드에서 Opcode는 `INST[31:27]`, 한쪽 Source Register는 `INST[21:17]`, 다른 Source Register는 `INST[16:12]`, Destination Register는 `INST[26:22]`에 배치돼 있다. EX 단계에는 **17비트·22비트 Offset**, Shift 방식 선택 비트, 5비트 Shift Amount와 3비트 분기 조건도 함께 전달했다.

따라서 EX가 실행될 때 필요한 값은 단순히 두 Register의 데이터만이 아니었다. **명령어의 일부 필드와 목적지 주소, 메모리 접근·레지스터 기록 여부를 나타내는 제어 신호까지** 그 명령어와 같은 속도로 이동해야 했다.

## IF: PC를 증가시키는 일에도 Stall 조건이 필요했다

보통 명령어를 순서대로 실행한다면 `PC`는 4씩 증가한다. RISC TOY도 기본적으로 `PC + 4`를 다음 주소로 사용했다. Branch나 Jump가 발생하면 EX에서 계산한 `target`으로 변경해야 했다.

그런데 Load나 Branch 때문에 파이프라인이 정지한 동안 PC만 계속 증가한다면 아직 실행하지 않은 명령어를 건너뛰게 된다. 그래서 IF Pipe Register에서는 **`stall_MEM`과 `stall_ID`를 확인한 후 PC를 유지할지 결정**하도록 했다.

원본 코드의 핵심 부분을 정리하면 다음과 같다.

```verilog
if (start) begin
    if (!BRANCH) begin
        if (stall_MEM || stall_ID > 0)
            PC <= PC;
        else
            PC <= PC + 4;
    end else begin
        PC <= target;
    end
end else begin
    start <= 1'b1;
end
```

`start`는 Instruction Memory의 요청 신호인 `IREQ` 제어에도 쓰였다. IF에서는 메모리로부터 받은 `INSTR`을 곧바로 Decode에 넘기는 대신, 임시 값 `INST_M`을 거쳐 ID Pipe Register의 `INST`로 전달했다.

이때 **PC와 Instruction을 모두 같은 조건에서 멈추는 것**이 중요했다. 한쪽만 진행하면 주소는 다음 명령어를 가리키는데 Decode에는 이전 명령어가 들어가는 식으로 실행 순서가 어긋날 수 있기 때문이다.

## ID: Instruction Field와 Register File의 실제 타이밍

ID에서는 Instruction을 해석하고 Register File에서 읽을 두 주소를 결정했다. 이 과정에서도 명령어 종류에 따라 예외가 있었다. **Store 명령어 `ST`와 `STR`의 주소 선택 방식이 달랐다.**

일반적인 연산에서는 `rb`와 `rc`를 Source Register로 읽지만, Store에서는 메모리에 기록할 데이터를 읽기 위해 다른 필드를 사용해야 했다. 원본의 주소 선택 로직은 다음과 같다.

```verilog
rb_ADDR_M <= INST[21:17];

if (STORE)
    rc_ADDR_M <= INST[26:22];
else
    rc_ADDR_M <= INST[16:12];
```

이 구조를 이해해야 뒤에서 Store에 대한 Forwarding을 별도로 처리한 이유도 알 수 있다. Store는 주소를 계산하는 연산일 뿐 아니라 **메모리에 기록할 최신 데이터를 확보해야 하는 명령어**이기 때문이다.

또 하나의 핵심은 **Register File이 동기식으로 동작했다는 사실**이다. 읽기 주소를 설정하고 데이터를 얻는 과정이 이상적인 조합 논리처럼 즉시 끝나지 않았기 때문에, `valB_M`·`valC_M`을 거쳐 EX Pipe Register로 값을 전달할 때 클럭 경계를 고려해야 했다.

보고서에 적힌 `next_PC_ID` 처리와 나중에 설명할 Writeback 신호 재배치도 이 Register File 타이밍과 연결돼 있다.

## EX: 산술 연산부터 Shift·Branch·메모리 접근까지

실행 단계에서는 명령어의 Opcode를 기준으로 여러 연산을 구현했다. 원본 보고서의 코드를 기준으로 다음과 같은 계열이 포함돼 있었다.

| 명령어 계열 | 구현된 동작 |
| --- | --- |
| `ADDI`·`ANDI`·`ORI`·`MOVI` | Immediate를 사용하는 산술·논리·데이터 이동 |
| `ADD`·`SUB`·`NEG`·`NOT`·`AND`·`OR`·`XOR` | Register 피연산자를 이용한 연산 |
| `LSR`·`ASR`·`SHL`·`ROR` | Shift Amount 또는 Register 값을 이용한 Shift·Rotate |
| `BR`·`BRL`·`J`·`JL` | Branch 조건 판단, Target 주소 선택, Link 주소 전달 |
| `LD`·`LDR`·`ST`·`STR` | Data Memory 주소 계산 및 읽기·쓰기 |

특히 `ROR`에는 별도 연산자가 없어서 **입력 값을 두 번 이어 붙인 뒤 Shift하고 하위 32비트만 가져오는 방식**으로 Rotate Right를 구현했다.

```verilog
assign ROR_0 = {valB, valB} >> shamt;
assign ROR_1 = {valB, valB} >> valC[4:0];

// Shift 방식 선택 비트에 따라
// ROR_0[31:0] 또는 ROR_1[31:0]을 사용
```

Shift는 Immediate 값으로 할 수도 있고 다른 Register의 값으로 할 수도 있다. 결국 연산 자체보다 Opcode, Shift 방식, Operand와 비트 폭을 올바르게 조합하는 것이 중요했다.

EX의 결과는 `ALU_OUT_M`에 저장됐고, 동시에 **Register File을 쓸지, Data Memory에 접근할지, Branch로 PC를 바꿀지** 결정하는 제어 신호도 함께 설정했다.

## Data Hazard: 원본 코드에서 처리한 세 가지 경우

가장 중요한 구현 중 하나가 **Data Forwarding**이었다. 앞선 명령어의 결과가 Register File에 기록되기 전에 다음 명령어가 그 값을 사용할 수 있기 때문이다.

보고서에서는 이 상황을 세 종류로 구분했다.

| 경우 | 상황 | 해결 경로 |
| --- | --- | --- |
| Case 1 | 바로 앞 ALU 명령어의 결과를 현재 명령어가 사용 | MEM 단계의 `ALU_OUT_MEM`을 Forwarding |
| Case 2 | 한 명령어를 사이에 두고 앞선 ALU 결과를 사용 | WB 단계의 `ALU_OUT_WB`를 Forwarding |
| Case 3 | Load한 값을 뒤따르는 명령어가 사용 | 먼저 Stall한 후 Data Memory 결과 `MOUT`을 Forwarding |

{{figure /figures/journals/risc-hazard-control-timeline.svg | 실제 보고서의 세 가지 Data Hazard와 `stall_MEM`, `stall_ID` 제어를 따로 정리했다. ALU 결과의 MEM·WB Forwarding과 Load 이후 Forwarding은 데이터가 준비되는 시점이 다르다.}}

### Case 1: 바로 앞 ALU 결과를 가져오기

예를 들어 다음과 같은 명령어가 연속으로 실행된다고 하자.

```text
ADD R1, R2, R3
ADD R3, R1, R2
```

두 번째 명령어가 R1을 읽는 순간 첫 번째 명령어의 결과가 Register File에 기록되지 않았다면, 오래된 값을 읽을 수 있다. 이때는 **MEM에 있는 첫 번째 명령어의 계산 결과를 EX 입력으로 전달**하도록 했다.

### Case 2: 두 단계 앞 명령어의 결과를 가져오기

첫 번째 명령어와 현재 명령어 사이에 다른 명령어가 한 개 있는 경우도 처리해야 했다. 이때 결과를 만드는 명령어는 이미 WB에 도달했을 수 있으므로 MEM만 비교해서는 부족하다.

그래서 `dest_WB`를 현재 Source Register 주소와 비교하고, 조건이 맞으면 **WB 단계의 `ALU_OUT_WB` 값을 사용하도록 했다.**

### Case 3: Load 결과는 곧바로 Forwarding할 수 없었다

`LDR R1, ...` 다음에 `ADD R3, R1, R2`가 있다면 조금 다르다. ALU가 계산한 것은 메모리 주소이지, 메모리에서 실제로 읽은 R1의 값이 아니기 때문이다.

따라서 **Load 결과가 준비될 때까지 Stall한 다음 `MOUT`을 Forwarding**하는 방식을 사용했다. ALU 결과가 존재한다는 이유만으로 그대로 전달하면 주소를 데이터로 사용하는 오류가 발생할 수 있었다.

### 실제 Forwarding 선택식

보고서에 남은 `valB` 선택식은 다음 순서로 동작하도록 작성됐다.

```verilog
assign valB =
    (dest_MEM == rb_ADDR) && (!WEN_MEM && !DREQ_MEM)
        ? ALU_OUT_MEM :
    (dest_WB  == rb_ADDR) && (!WEN_WB && !DREQ_MEM)
        ? ALU_OUT_WB :
    (dest_MEM == rb_ADDR) && (!DRW_MEM && DREQ_MEM)
        ? MOUT :
    valB_EX;
```

즉, MEM의 ALU 결과, WB의 ALU 결과, MEM의 Load 결과 순으로 조건을 확인하고, 해당하지 않으면 원래 읽어온 `valB_EX`를 사용한다. `valC`도 같은 방식으로 처리했고, Store가 메모리에 기록할 데이터인 **`DWDATA`도 별도로 Forwarding**했다.

여기서 주의할 점이 하나 있다. **위 코드는 보고서에 남은 실제 식을 그대로 정리한 것**이다. WB 결과를 선택하는 두 번째 분기에서도 `DREQ_MEM`을 검사하고 있는데, 이는 현재 MEM 명령어와 WB 명령어가 서로 다른 메모리 제어 상태를 가질 때 추가 검토가 필요한 부분이다. 과거 코드를 임의로 수정해 완전한 회로였다고 소개하기보다, 실제 구현과 추가로 확인할 조건을 구분해 두었다.

## Load-use Stall: `stall_MEM`으로 1사이클 유지

Forwarding을 구현해도 **Load 직후 데이터 사용**은 별도의 Stall이 필요했다. 메모리에서 데이터를 읽기 전에 다음 연산이 진행되면 아직 준비되지 않은 값을 사용하기 때문이다.

원본에서는 Load가 MEM에 있고, 그 Destination Register를 뒤따르는 명령어가 Source로 사용한다면 `stall_MEM`을 1로 설정했다. 개념적으로 정리하면 다음 조건이다.

```verilog
load_read = !DRW_MEM && DREQ_MEM;

if (load_read &&
    ((dest_MEM == rb_ADDR) ||
     (dest_MEM == rc_ADDR) ||
     (store_instruction && dest_MEM == dest_EX))) begin
    stall_MEM <= 1'b1;
end
```

이 코드는 실제 보고서의 조건을 읽기 쉽게 줄인 것으로, 원본에는 Reset과 Stall 해제 로직이 더 있다. 중요한 것은 **`stall_MEM`이 단순한 대기 표시가 아니라 파이프라인 레지스터의 갱신 여부를 제어하는 신호**였다는 점이다.

`stall_MEM == 1`일 때 IF와 ID, EX 쪽의 관련 레지스터는 현재 값을 유지했다. MEM Pipe Register에서도 상태를 유지하고 불필요한 Register File 쓰기가 발생하지 않도록 `WEN_MEM`을 조정했다. 한 사이클 뒤에 Stall을 해제하면 필요한 Load 결과를 전달받아 연산을 계속 진행할 수 있었다.

또한 조건에는 **`ST`·`STR`에 대한 예외적인 의존성 검사**가 포함됐다. Store가 Load 결과를 메모리에 기록하려는 상황에서는 주소 계산이 끝났더라도 실제 Write Data가 최신 값이어야 하기 때문이다.

## Branch·Jump: `stall_ID`를 이용한 2사이클 정지

분기 명령어를 처리할 때는 값의 의존성보다 **어느 Instruction을 다음에 실행할 것인가**가 문제였다.

RISC TOY에서 Control Transfer에 해당하는 Opcode는 다음과 같았다.

| Opcode | 명령어 |
| --- | --- |
| 15 | `BR` |
| 16 | `BRL` |
| 17 | `J` |
| 18 | `JL` |

원본에서는 `INST`가 아닌 **`INST_M[31:27]`을 이용해 Branch·Jump를 조기에 감지**했다. Decode Pipe Register에 저장되기 전 명령어를 확인해야 잘못된 순차 실행이 더 진행되는 것을 막을 수 있었기 때문이다.

`stall_ID`는 **1 → 2 → 0**으로 상태를 변경하면서 두 사이클 동안 IF·ID 쪽 진행을 막았다.

```verilog
if (stall_ID == 2'd2)
    stall_ID <= 2'd0;
else if (stall_ID == 2'd1)
    stall_ID <= 2'd2;
else if (INST_M[31:27] == 5'd15 ||
         INST_M[31:27] == 5'd16 ||
         INST_M[31:27] == 5'd17 ||
         INST_M[31:27] == 5'd18)
    stall_ID <= 2'd1;
```

EX에서는 Branch Condition에 따라 `target`을 계산했다. 원본의 분기 조건에는 Never, Always, Zero, Nonzero, Plus, Minus가 포함됐고, `BRL`·`JL`에서는 Link 주소를 Register에 기록하도록 설계했다.

보고서는 분기 대상 Instruction을 가져오는 데 걸리는 지연을 **3사이클**로 설명한다. 반면 `stall_ID`로 명시적으로 유지한 상태는 **두 사이클**이다. 두 숫자는 같은 의미가 아니며, 하나는 분기 대상의 도착 지연이고 다른 하나는 구현한 Stall 단계라는 점을 구분해야 한다.

## Writeback: 동기식 Register File 때문에 바꾼 데이터 경로

원본 보고서를 다시 살펴보면서 특히 중요하게 느낀 부분은 **WB 단계의 타이밍을 별도로 조정했다는 사실**이다.

Register File이 동기식으로 동작하다 보니 최종 WB Pipe Register에 저장된 값을 그대로 Register File 쓰기 입력에 연결하면, 다음 명령어가 그 Register의 값을 읽어오는 시점보다 쓰기가 늦어지는 문제가 생겼다.

그래서 보고서의 Writeback 부분에서는 `*_MA` 신호를 별도로 구성했다.

```verilog
ALU_OUT_MA <= ALU_OUT_MEM;
dest_MA    <= dest_MEM;
WEN_MA     <= WEN_MEM;
MOUT_MA    <= MOUT_M;
op_MA      <= op_MEM;
```

즉, **Memory Access 단계의 결과와 제어 정보를 사용해 Register File에 기록할 값을 더 적절한 시점에 준비**했다. 이것은 단순히 5단계 파이프라인의 순서를 설명하는 것만으로는 알 수 없는 실제 통합 문제였다.

모듈이 클럭을 기준으로 언제 입력을 받아들이고 결과를 내놓는지 이해해야 데이터 경로를 제대로 연결할 수 있었다.

## 직접 구성한 Instruction Testbench와 결과

보고서 마지막에는 **PC 0부터 PC 380까지** 이어지는 명령어 테스트와 레지스터별 예상 결과가 기록돼 있다. 초기 Register 값을 준비하고 Immediate 연산, 일반 ALU, Shift·Rotate, Load·Store, Branch·Jump를 함께 넣은 시퀀스였다.

다음은 당시 테스트 목록에서 추린 대표 사례다. **새로 실행해 측정한 값이 아니라 원본 테스트 계획에 적힌 기대 결과**다.

| 테스트 내용 | 보고서의 기대 결과 | 확인한 경로 |
| --- | --- | --- |
| `MOVI R1, 1` 이후 `ADDI R0, R1, 32` | `R0 = 33` | Immediate 연산과 데이터 의존성 |
| 초기 `R7 = 7`, `R8 = 8`에서 `ADD R6, R7, R8` | `R6 = 15` | ALU 계산·Writeback |
| `LD R21, R31, 512` 후 `ADDI R22, R21, 57` | `R21 = -308`, `R22 = -251` | Load-use Stall과 데이터 전달 |
| `LD R0, R31, 1924` → `ST R0, R31, 1928` → `LD R1, R31, 1928` | `R0 = 154`, `R1 = 154` | Load·Store·다시 읽기 |
| PC 348 부근의 `J`·`JL`·`BR`·`BRL` 테스트 | 순차 진행과 **PC 0으로 분기**하는 경우 비교 | Control Hazard와 PC 변경 |

보고서에는 **분기하지 않고 진행했을 때의 Register 파형과 PC가 0으로 돌아갔을 때의 파형**도 들어 있다. 각 Register의 값이 실행 중 어떻게 변했는지 볼 수 있는 실제 시뮬레이션 자료다.

명령어 종류와 의존성에 대한 테스트를 만들고 파형으로 확인했다는 점은 구현 결과로 남길 만하다. 다만 이 파형만으로 모든 명령어 조합을 형식적으로 검증했다고 할 수는 없다. 클럭 주파수, IPC, FPGA 리소스 사용량처럼 원본 자료에 없는 수치는 덧붙이지 않았다.

현재 코드에 대해 더 깊이 검증한다면 **동시에 두 Source Register가 각각 다른 단계의 결과에 의존하는 경우**, Load 결과를 Store 데이터로 사용하는 경우, Branch 도중 Load Stall이 겹치는 경우, 그리고 MEM·WB 제어 신호가 다른 경우의 Forwarding을 우선 확인하고 싶다. 이들은 원본 RTL을 읽으며 도출한 추가 검토 조건이지, 2024년에 모두 테스트했다고 주장하는 목록은 아니다.

## 구현을 마치고 남은 것

이 프로젝트에서는 단순히 RISC Instruction 몇 개를 구현한 것이 아니라 **PC·명령어 인출·동기식 Register File·ALU·Data Memory·Writeback을 하나의 파이프라인으로 연결**했다. 그리고 실행 순서가 어긋나는 상황을 처리하기 위해 **MEM/WB Forwarding, Load-use 1사이클 Stall, Branch·Jump 2사이클 Stall**을 구현했다. 마지막으로 직접 만든 Instruction 시퀀스와 레지스터 파형으로 동작을 확인했다.

당시에는 명령어 하나가 정상적으로 실행되더라도 다음 명령어와 겹치기 시작하면 예상하지 못한 문제가 생겼다. 그래서 **데이터가 언제 만들어지고, 어느 단계에 남아 있으며, 지금 실행 중인 명령어가 그 값을 읽어도 되는지**를 끝까지 추적해야 했다.

이후 FPGA Systolic Array나 CNN 가속기에서 Processing Element와 버퍼의 데이터 이동 시점을 설계할 때도 같은 고민이 이어졌다. RISC TOY에서는 그 문제가 클럭 하나와 Register 하나의 차이로 드러났다.

## 함께 읽을 프로젝트

- [FPGA Systolic Array 행렬곱 가속기](/projects/fpga-systolic-array-matrix-multiplication/)
- [Zynq Bit-Shift CNN 가속기](/projects/bit-shift-cnn-accelerator-zynq/)
- [FreeRTOS 멀티보드 Mini-Desktop](/projects/freertos-multiboard-mini-desktop/)
