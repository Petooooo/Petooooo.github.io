> **2024년 4–5월에 Verilog로 개발했던 FPGA Systolic Array 프로젝트를 다시 정리했다.** 당시 프로젝트 이력에는 행렬곱 연산기를 전체 개발했고, IM2COL을 통해 Convolution 연산에도 활용하려 했다고 기록돼 있다. 다만 현재 남아 있는 자료에서 원본 RTL, Testbench 파형, 합성 결과표와 Benchmark 조건을 확인할 수는 없었다. 아래의 숫자와 Cycle 그림은 **이번에 따로 계산하고 검증한 2×2 예제**다. 당시 FPGA에서 캡처한 실행 결과는 아니다.

처음에는 행렬곱을 여러 Processing Element(PE)에 나눠 맡기면 된다고 생각하기 쉬웠다. 행렬의 Row와 Column을 곱한 다음 더해 나가는 연산 자체는 어렵지 않다. 그런데 실제로 회로를 구성하려고 보면 그다음 질문이 따라온다. **어느 클럭에, 어떤 값 두 개가, 어느 PE에 도착해야 할까?**

소프트웨어에서는 배열의 Index를 맞춰 읽으면 되는 일이지만, RTL에서는 입력값을 이동시키는 경로와 각 연산의 시점을 직접 정해야 한다. 이때부터는 행렬곱의 수식보다 **데이터가 움직이는 순서**를 이해하는 일이 더 중요해졌다.

## 행렬곱을 클럭 단위로 생각하기 시작했다

행렬곱의 원리는 C[i,j] = Σ A[i,k] × B[k,j]로 표현할 수 있다. 결과 행렬의 각 원소는 A의 한 Row와 B의 한 Column을 내적해 얻는다. CPU에서는 반복문과 Index가 이 과정을 대신 처리하지만, Systolic Array에서는 해당 Operand가 실제 연산기로 전달되어야 한다.

이 차이를 설명하려고 작은 행렬 두 개를 놓았다. 아래 계산은 당시 기록된 입력 데이터가 아니라 지금 만든 Reference Example이다.

{{figure /figures/journals/fpga-systolic-01-matmul-example.svg | A=[[1,2],[3,4]], B=[[5,6],[7,8]]를 곱하면 C=[[19,22],[43,50]]이 된다. 새로 작성한 Python Reference Model로 네 결과를 확인했다. 실제 2024년 Test Vector는 아니다.}}

2×2 행렬곱은 결과가 네 개이고, 각 결과를 만드는 데 곱셈과 누산이 두 번씩 필요하다. 전체로 보면 여덟 번의 Multiply-Accumulate(MAC) 연산이 생긴다. Systolic Array가 이 연산 횟수를 없애주는 것은 아니다. 여러 PE가 각자의 결과를 만들면서 **입력값을 인접 PE로 전달해 재사용**하도록 구성하는 데 의미가 있다.

## PE에 무엇을 남기고 무엇을 전달할까

Systolic Array에도 여러 Dataflow가 있다. 설명용 예제에서는 **Output-Stationary** 방식을 사용했다. PE(i,j)가 자신이 담당하는 C[i,j]의 Partial Sum을 내부에 유지하고, A는 오른쪽으로, B는 아래쪽으로 전달한다고 가정했다.

이것은 구조를 이해하기 위한 Reference Architecture다. **2024년 프로젝트의 실제 PE 개수가 2×2였다거나 당시에도 같은 Dataflow를 사용했다고 확인한 것은 아니다.**

{{figure /figures/journals/fpga-systolic-02-pe-grid.svg | A가 오른쪽으로, B가 아래쪽으로 이동하고 PE별 Partial Sum은 제자리에 남는 2×2 Output-Stationary 예시다. 실제 FPGA Floorplan이나 원본 회로도가 아니다.}}

이렇게 보면 PE의 역할은 크게 세 가지다. 입력된 A와 B를 연산하고, 결과를 Accumulator에 누적하고, 다음 PE가 쓸 수 있도록 Operand를 전달한다. 곱셈만 잘 구현해서는 충분하지 않다. 값이 한 칸씩 이동할 때 그것을 Register에 저장할지, 어떤 조건에서 Accumulator를 갱신할지, 결과가 언제 Valid인지까지 정해야 한다.

{{figure /figures/journals/fpga-systolic-03-pe-anatomy.svg | A·B Register, Multiply, Accumulator, Output Valid의 관계를 단순화한 PE 개념도다. 원본 RTL의 비트 폭이나 실제 Register 배치를 복원한 것은 아니다.}}

특히 고정 소수점이나 정수 기반 회로라면 부호 처리, Accumulator 폭, Overflow도 중요해진다. Reset 때 누적값을 어떻게 초기화할지, 유효하지 않은 입력에서 덧셈이 일어나지 않도록 어떻게 막을지도 확인해야 한다. 다만 그 당시의 구체적인 비트 폭과 제어 신호를 확인할 자료가 없으므로, 이 글에 실제 구현값처럼 적지는 않았다.

## Input Skew가 필요한 이유

이제 중요한 건 두 Operand가 **같은 k에 해당하는 값으로** 만나도록 만드는 것이다. 예를 들어 PE(0,1)에는 A의 첫 번째 Row가 오른쪽으로 전달되어 도착하고, B의 두 번째 Column은 위에서 내려온다. 두 값이 그냥 같은 시점에 들어오는 것처럼 생각하면 서로 다른 k의 값이 곱해질 수 있다.

설명용 구조에서는 A의 Row i와 B의 Column j를 각각 i, j Slot만큼 늦춰 입력한다고 가정했다. 값이 PE를 한 칸 지날 때마다 한 Slot씩 이동하면, A[i,k]와 B[k,j]는 다음 시점에 같은 PE에서 만난다.

**logical t = i + j + k**

이때의 t는 **논리적 MAC Slot**이다. 실제 Verilog에 Pipeline Register가 더 있다면 Clock Edge 기준으로 지연이 추가될 수 있다.

{{figure /figures/journals/fpga-systolic-04-skew-streams.svg | 2×2 예제에서 왼쪽 A 입력과 위쪽 B 입력을 어느 Slot에 넣는지 계산한 표다. 빈 칸은 새 입력이 없다는 뜻이며 배열 내부 PE가 모두 쉬는 것은 아니다.}}

t=0에는 A[0,0]과 B[0,0]만 경계에 들어온다. t=1에는 A[0,1], A[1,0], B[1,0], B[0,1]이 각자의 입력 경계로 들어온다. 두 번째 Row와 Column의 시작을 늦춘 이유는 같은 연산 항끼리 만나게 하기 위해서다.

결국 Systolic Array는 **데이터를 많이 동시에 넣는 회로**가 아니라, 데이터가 필요한 위치에 **올바른 시점에 도착하도록 배치하는 회로**라는 생각이 들었다.

## 한 단계씩 따라가 보면 Wavefront가 보인다

이 입력 순서를 바탕으로 PE들의 누적값을 직접 계산했다.

{{figure /figures/journals/fpga-systolic-05-wavefront-steps.svg | t=0부터 t=3까지 각 PE가 수행한 곱셈과 누적값을 표시했다. Python 계산 결과를 시각화한 것으로 원본 FPGA 시뮬레이션 파형은 아니다.}}

| 논리적 단계 | 수행된 MAC | 해당 단계의 누적값 |
| --- | --- | --- |
| t=0 | PE00: 1×5 | C00=5 |
| t=1 | PE00: 2×7, PE01: 1×6, PE10: 3×5 | C00=19, C01=6, C10=15 |
| t=2 | PE01: 2×8, PE10: 4×7, PE11: 3×6 | C01=22, C10=43, C11=18 |
| t=3 | PE11: 4×8 | C11=50 |

전체를 보면 Wavefront가 왼쪽 위에서 오른쪽 아래로 이동하는 형태가 된다. PE00의 결과는 일찍 완성되지만 PE11은 마지막 Slot까지 기다려야 한다. 배열 안에서 여러 PE가 병렬로 움직이더라도 **모든 Output이 같은 순간에 완성되는 것은 아니다.**

## 결과값뿐 아니라 Output Valid도 맞아야 한다

{{figure /figures/journals/fpga-systolic-06-valid-timeline.svg | PE별로 k=0, k=1에 해당하는 두 번의 연산이 언제 일어나고 어느 단계에 최종값이 만들어지는지 표시했다. 실제 RTL Pipeline Latency는 포함하지 않았다.}}

이 예제에서 PE00의 최종값 19는 t=1에, PE01과 PE10의 최종값은 t=2에, 마지막 PE11의 최종값 50은 t=3에 만들어진다. 누적 중간값을 최종 결과로 착각해 읽지 않으려면 Valid Signal이나 결과 수집 규칙이 필요하다.

FPGA에서 구현할 때는 새로운 Tile이 들어올 때 Accumulator를 초기화하는 시점, 입력이 유효한 Cycle, Pipeline이 채워지기 전의 구간과 모든 결과를 회수하는 시점을 함께 고려해야 한다. 실제 구현 방식은 Counter나 FSM, Valid Propagation 등으로 다르게 구성할 수 있다.

내가 당시 사용한 정확한 RTL 제어 구조와 파형은 현재 확인할 수 없다. 다만 **데이터 이동과 연산 시점을 맞추는 일이 왜 중요한지**는 이런 작은 예제만으로도 충분히 설명할 수 있다.

## Delay 하나가 빠지면 연산식 자체가 달라진다

입력이 조금만 잘못 정렬되어도 문제가 생긴다. 예를 들어 t=1에 PE(0,1)은 A[0,0]=1과 B[0,1]=6을 받아 1×6=6을 계산해야 한다. 그런데 B의 두 번째 Column에 필요한 Delay를 빼버리면, A[0,0]이 도착했을 때 B[1,1]=8이 들어와 1×8=8을 계산하는 상황을 만들 수 있다.

{{figure /figures/journals/fpga-systolic-07-skew-counterexample.svg | 정상적인 Operand Pairing과 의도적으로 Skew를 누락한 반례를 비교했다. 2024년에 실제로 발생한 오류를 재현한 것이 아니라 타이밍 오류의 의미를 설명한 예제다.}}

이 경우 곱셈기 자체는 틀리지 않았다. 1×8=8은 맞는 계산이다. 하지만 **곱해야 할 두 값을 잘못 선택했기 때문에** 행렬곱 결과가 틀어지는 것이다.

그래서 회로를 검증할 때도 기대한 숫자가 나왔는지만 보는 것은 부족하다. 그 결과가 어느 Output Element에 해당하는지, 어느 Clock에 Valid가 되었는지까지 확인해야 한다.

## Convolution을 IM2COL로 바꾸는 이유

2024년 프로젝트 이력에는 이 Systolic Array를 Convolution에 활용하려고 **IM2COL**을 사용했다는 설명이 남아 있다. Convolution은 이미지에서 작은 Patch를 반복해서 가져와 Kernel과 곱하는 연산이다. Patch를 Column으로 펼치고 Kernel을 Row로 펼치면 이 반복 작업을 행렬곱으로 나타낼 수 있다.

단순한 예로, 3×3 이미지를 2×2 Kernel과 곱하는 경우를 다시 계산했다.

{{figure /figures/journals/fpga-systolic-08-im2col-example.svg | 새로 만든 3×3 입력 이미지와 2×2 Kernel을 IM2COL의 4×4 Patch Matrix로 변환한 예제다. 출력 네 개는 모두 −4로 계산되며, 당시 사용한 CNN 데이터나 실제 BRAM 배치를 나타내지는 않는다.}}

예제에서는 네 개의 Patch를 만들고, 각각을 길이 4의 Column으로 펼친다. 그 결과 1×4 Kernel Row와 4×4 Patch Matrix를 곱해 네 Output을 얻는다. **Convolution의 행렬곱 부분을 규칙적인 PE Array에 맡길 수 있게 되는 것**이다.

하지만 IM2COL도 비용 없이 되는 일이 아니다. Patch를 펼칠 때 중복 데이터가 생길 수 있고, 그 데이터를 어디에 보관해 어떤 순서로 PE에 공급할지 결정해야 한다. Systolic Array의 연산 능력만큼이나 Input Buffer와 데이터 공급 경로가 중요한 이유다.

같은 해 하반기에 진행한 [Zynq Bit-Shift CNN Accelerator](/projects/bit-shift-cnn-accelerator-zynq/)에서는 이 문제를 더 큰 시스템 안에서 다뤘다. 거기에는 Quantized Weight, PS·PL 기능 분할, BRAM Controller, 실제 CNN 지원 연산까지 포함됐다. 두 프로젝트는 이어지는 경험이지만 **성능 측정값과 아키텍처가 같은 하나의 프로젝트는 아니다.**

## 당시 기록과 지금 검증한 내용을 구분했다

{{figure /figures/journals/fpga-systolic-09-evidence-boundaries.svg | 2024년 포트폴리오에서 확인되는 사실, 이번에 계산해 검증한 설명용 예제, 확보하지 못한 원본 자료를 구분했다.}}

내가 보관한 2024년 포트폴리오에는 이 작업이 **Systolic Array Calculator on FPGA Board**, 수행 기간 **4–5월**, 개발 범위 **전체 개발**, 언어 **Verilog**로 기록되어 있다. Convolution을 IM2COL로 바꿔 연산했다는 설명도 남아 있다.

다만 과거의 한 프로젝트 소개에는 특정 행렬곱에서 GPU보다 효율적이거나 빠르게 동작했다는 취지의 표현이 있지만, 그때 비교한 GPU 종류와 행렬 크기, 데이터 전송 비용, 클럭, 반복 측정 결과가 현재 자료에 없다. 그래서 이 글에서는 **GPU 대비 몇 배 빠르다**는 식의 성능 수치를 만들지 않았다.

마찬가지로 초기 FPGA 구현의 정확한 PE 크기, Bit Width, LUT 사용량, 원본 Testbench 파형이 남아 있다고 주장하지도 않는다. 위쪽의 2×2 행렬과 그 연산 순서는 지금 작성한 Python 코드로 검증했고, IM2COL 예제도 직접 계산했다. 이 검증은 **그림에 들어간 새 수치의 정확성**을 보여줄 뿐, 당시 FPGA의 모든 RTL 동작까지 증명하는 것은 아니다.

## 결국 배운 건 연산보다 데이터의 시점이었다

행렬곱을 수식으로 보면 무엇을 곱하고 더할지 이미 정해져 있다. 하지만 그것을 FPGA의 PE Array에 배치하는 순간 각 값은 **언제, 어디로 이동해야 하는지**가 함께 결정되어야 한다. 수식을 맞게 구현해도 Input Skew나 Output Valid가 틀리면 전체 연산은 틀어질 수 있다.

이 경험이 이후 CNN 가속기의 설계로 이어졌을 때는 PE를 더 많이 만드는 것만큼, **각 PE를 쉬지 않고 동작시킬 만큼 데이터를 안정적으로 공급하는 구조**를 생각하게 됐다. 지금 돌아보면 처음 행렬곱을 회로로 옮기며 얻은 가장 중요한 감각은 그 부분이었다.

**참고 자료:** 2024년 개인 프로젝트·CV 기록, *Systolic Array Calculator on FPGA Board*; [Zynq Bit-Shift CNN Accelerator](/projects/bit-shift-cnn-accelerator-zynq/); N. P. Jouppi 외, [*In-Datacenter Performance Analysis of a Tensor Processing Unit*](https://research.google/pubs/in-datacenter-performance-analysis-of-a-tensor-processing-unit/) (2017, Systolic Array의 배경 자료로 참고).

*이번에 추가한 SVG 9개는 수치가 검증된 설명용 벡터 도식이다. 2024년의 원본 RTL·파형·Synthesis Report·Benchmark 결과를 복원한 것처럼 표현하지 않았다.*
