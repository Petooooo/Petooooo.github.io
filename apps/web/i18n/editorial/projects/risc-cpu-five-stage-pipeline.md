2024년 5~6월에는 Verilog로 **5단계 파이프라인 RISC CPU**를 만들었다. 2인 프로젝트였지만 데이터 경로와 제어 로직, 파이프라인의 의존성 처리까지 시스템 구현을 직접 맡았다. IF·ID·EX·MEM·WB로 단계를 나누는 것보다 어려웠던 부분은 여러 명령어가 동시에 실행될 때도 프로그램이 의도한 결과가 나와야 한다는 점이었다.

이 글은 당시 구현과 검증 내용을 2026년 11월에 정리한 회고 기록이다. 표시된 날짜는 프로젝트 수행 시기를 나타내며, 그때 이 글을 게시했다는 뜻은 아니다.

## 5단계 파이프라인과 데이터 경로

명령어는 **Instruction Fetch(IF) → Decode(ID) → Execute(EX) → Memory(MEM) → Writeback(WB)** 순서로 처리했다. 각 단계 사이에는 파이프라인 레지스터가 있고, 데이터뿐 아니라 목적지 레지스터 번호와 제어 신호도 다음 단계까지 정확히 전달돼야 했다.

명령어를 다섯 단계로 나누는 것만으로 처리량이 개선되지는 않는다. 앞선 명령어의 결과를 뒷명령어가 사용하거나 분기 때문에 실행 위치가 달라질 때, 파이프라인 제어가 그 변화에 맞게 동작해야 한다.

{{figure /figures/journals/risc-five-stage-hazards.svg | IF·ID·EX·MEM·WB의 실행 경로와 Forwarding, Stall, Control Hazard를 처리하는 위치를 나타낸 개념도다.}}

## Forwarding으로 데이터 의존성 처리

앞선 명령어가 계산한 값은 아직 레지스터에 기록되지 않았는데, 다음 명령어가 그 값을 사용하는 경우가 있다. 모든 명령어가 WB를 마칠 때까지 기다리면 파이프라인이 자주 멈춘다.

이를 해결하기 위해 **Forwarding 회로**를 구현했다. 현재 명령어의 Source Register와 앞선 명령어의 Destination Register를 비교하고, 필요한 경우 레지스터 파일 대신 이후 파이프라인 단계의 값을 연산 입력으로 선택하도록 했다.

결과값을 어느 단계에서 가져오는지뿐 아니라, 해당 명령어가 실제로 레지스터에 값을 쓰는지도 함께 확인해야 했다. Forwarding 대상이 아닌 명령어를 잘못 선택하면 연산 결과가 달라질 수 있기 때문이다.

## Load-use Hazard와 Stall

산술 연산 결과는 Forwarding으로 전달할 수 있지만, 메모리에서 읽어오는 Load 명령어의 결과는 그보다 늦게 준비될 수 있다.

Load 직후 결과를 사용하는 명령어가 들어오면 **Hazard Detection Unit에서 의존성을 감지하고 Stall**하도록 했다. 이때 필요한 명령어와 PC 상태는 유지하고, 아직 준비되지 않은 데이터를 사용하지 않도록 파이프라인을 제어했다.

Stall을 넣는 일도 단순히 한 클럭 멈추는 문제가 아니었다. 이후 단계에 이미 진행한 명령어를 다시 실행하거나, 제어 신호가 엉뚱한 명령어에 적용되지 않도록 상태를 맞춰야 했다.

## Branch·Jump와 Control Hazard

분기와 점프에서는 다음에 실행할 명령어 주소가 달라진다. 순서대로 Fetch된 명령어 중에는 분기 결과에 따라 실행되면 안 되는 명령어가 생길 수 있다.

PC 선택 로직과 파이프라인 제어를 구현하면서 **Branch·Jump에 따른 Control Hazard**를 처리했다. 데이터 의존성처럼 값을 기다리는 문제와 달리, 올바르지 않은 경로로 가져온 명령어를 어떻게 다루는지가 핵심이었다.

## 직접 만든 Testbench로 검증

긴 프로그램 하나를 실행해 최종 결과만 확인하기보다, 오류가 드러나기 쉬운 짧은 명령어 조합을 직접 만들었다.

| 검증 항목 | 확인한 내용 |
| --- | --- |
| 기본 산술 명령어 | Decode·Execute·Writeback 데이터 흐름 |
| 연속 데이터 의존성 | Forwarding 대상과 연산 입력 선택 |
| Load 직후 결과 사용 | Stall 발생과 재실행 순서 |
| Branch·Jump | PC 변경과 잘못된 경로 처리 |
| 혼합 명령어 시퀀스 | 파이프라인 단계 간 데이터·제어 신호 전달 |

이 프로젝트에서 **Forwarding과 Stall, Branch·Jump Hazard 처리까지 갖춘 RISC CPU를 구현하고 직접 작성한 Testbench로 동작을 검증**했다. 별도의 클럭 주파수나 IPC 측정값은 남아 있는 당시 자료에 없어 임의로 덧붙이지 않았다.

이후 Systolic Array나 CNN 가속기의 데이터 경로를 설계할 때도 어떤 값이 **어느 클럭에 도착하는지**를 먼저 생각하게 됐다. 파이프라인의 각 단계가 올바른 데이터를 받도록 만드는 경험은 하드웨어와 시스템을 이해하는 데 중요한 출발점이었다.

## 관련 프로젝트

- [FPGA Systolic Array 행렬곱 가속기](/projects/fpga-systolic-array-matrix-multiplication/)
- [Zynq Bit-Shift CNN 가속기](/projects/bit-shift-cnn-accelerator-zynq/)
- [FreeRTOS 멀티보드 Mini-Desktop](/projects/freertos-multiboard-mini-desktop/)
