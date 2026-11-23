> **2024년 경희대학교 전자공학 졸업 팀 프로젝트.** 2026년 11월에 당시 포스터 *Bit-Shift-Based CNN Accelerator: A Compact and Energy-Efficient Solution*와 제출했던 프로젝트 이력 자료를 바탕으로 정리했다. 나는 **PS 소프트웨어 전체와 PL 아키텍처·타이밍 설계, Systolic Array 및 WS/IS Dataflow**를 주도했고, **양자화 CNN 학습과 곱셈기·Shift 기반 행렬곱 가속기 구현**을 맡았다. **BRAM 데이터 경로는 팀원과 공동 설계**했다. 모바일 앱과 통신 서버도 프로젝트 이력에 남아 있다. 아래 실험 수치는 팀 포스터를 기준으로 하며, 글의 프로젝트 날짜는 실제 수행 시기를 나타낸다.

우리 팀은 CNN 추론 연산을 FPGA에서 어떻게 더 작은 자원으로 구현할 수 있을지 고민했다. 합성곱에는 곱셈과 누산이 반복해서 등장한다. 작은 FPGA에서 모든 곱셈을 일반적인 곱셈기로 처리하면 연산기 자체가 차지하는 자원도 무시하기 어려웠다.

우리가 선택한 접근은 **학습한 가중치를 2의 거듭제곱 형태로 양자화하고, 추론 시 곱셈을 시프트와 부호 처리로 바꾸는 것**이었다. 그러나 곱셈을 시프트로 바꾸는 아이디어 하나만으로 가속기가 완성되지는 않는다. 데이터가 어느 순서로 들어오고, BRAM을 어떻게 사용하고, PS와 PL이 어떤 연산을 나눠 맡는지까지 함께 결정해야 했다.

포스터의 Custom Net은 28×28 입력에서 시작해 C1(`4 @ 25×25`), S1(`4 @ 12×12`), C2(`8 @ 9×9`), S2(`8 @ 4×4`), C3(`16`), 10개 Class 출력으로 이어진다. Layer마다 Feature Map과 Channel 수가 달라지므로 단순히 곱셈기만 바꾸는 것으로 가속기가 완성되지는 않는다.

{{figure /figures/journals/cnn-poster-01-custom-net.svg | 원본 Custom Net의 순서와 Feature Map 크기를 유지했다. 회색 Layer 묶음은 새로 그린 벡터 구조도이며 원본 캡처는 아니다.}}

## 연산을 줄이기보다 연산의 표현을 바꾸기

CNN에서 임의의 가중치 `w`를 입력 `x`와 곱한다면 일반적인 곱셈 연산이 필요하다. 그러나 가중치를 부호가 있는 `2^p` 형태로 제한하면 곱셈의 일부를 비트 시프트와 부호 처리로 나타낼 수 있다.

문제는 모델의 정확도다. 학습된 실수 가중치를 갑자기 제한된 값으로 바꾸면 추론 정확도가 떨어질 수 있다. 우리 팀은 이를 다루기 위해 INQ(Incremental Network Quantization)와 STE(Straight-Through Estimator)를 이용했다.

INQ는 학습 과정에서 가중치를 단계적으로 양자화하는 접근이고, STE는 미분하기 어려운 양자화 연산을 통과해 학습을 이어가도록 돕는 방법이다. 두 알고리즘을 새로 발명한 것은 아니다. 기존 방법을 프로젝트의 가중치 표현과 하드웨어 연산 구조에 적용했다.

포스터에는 입력과 가중치 표현을 FP32에서 각각 INT8 입력과 INT4 가중치 쪽으로 줄이는 과정이 설명돼 있다. 이때 양자화 결과를 하드웨어가 다룰 수 있는 형식으로 만드는 것이 학습과 회로를 연결하는 출발점이었다.

{{figure /figures/redrawn/cnn-quantization.svg | 2의 거듭제곱 기반 가중치 양자화와 INQ·STE의 역할을 정리한 그림이다. 2024년 팀 포스터를 바탕으로 다시 그렸다.}}

## Zynq의 PS와 PL에 일을 나누다

우리는 Zynq의 Processing System(PS)과 Programmable Logic(PL)을 함께 사용했다. PS에서는 CNN 입력을 정리하고 IM2COL 변환, ReLU, Max Pooling 같은 지원 연산을 처리했다. PL에는 반복적인 합성곱 연산을 위한 PE 배열과 BRAM, 데이터를 이동시키는 Controller를 배치했다.

{{figure /figures/redrawn/cnn-pspl.svg | PS 소프트웨어와 PL의 PE 배열·BRAM·제어부가 어떻게 나뉘는지 나타낸 팀 설계도다.}}

원본 Full Architecture에는 오른쪽 FP32 Input·Weight에서 왼쪽 INT8 Input·INT4 Weight로 이어지는 Power-of-2 Quantization이 보인다. 아래에는 PS의 IM2COL·ReLU·Pooling과 PL의 Input/Output BRAM 각 16개, FSM·Controller, PE Array가 그려져 있다. 배열 표기는 `1×16 IS`와 `4×16 WS`다. 그림만으로 Cycle Timing까지 알아낼 수 있는 것은 아니다.

{{figure /figures/journals/cnn-poster-02-ps-pl-architecture.svg | PS·PL 분할, BRAM 개수, 두 PE 배열, Training 방향을 원본에 맞춰 다시 그렸다. 세부 배선은 단순화했다.}}

포스터에 제시된 구조에는 입력 BRAM 뱅크 16개와 출력 BRAM 뱅크 16개가 등장한다. PE 배열은 Input-stationary(IS) `1 × 16`과 Weight-stationary(WS) `4 × 16` 형태로 설명됐다.

이 숫자 자체보다 중요한 것은 데이터의 재사용 방식이었다. 한 번 가져온 입력이나 가중치를 가능한 오래 이용하려면 어느 값을 PE 안에 머물게 하고 어느 값을 배열을 따라 흘릴지 정해야 한다. 연산기를 더 넣는다고 그 연산기에 필요한 데이터가 저절로 공급되는 것은 아니다.

PS와 PL 사이의 제어·데이터 이동도 성능에 영향을 준다. 포스터에는 AXI4-Lite 연결과 BRAM Controller, FSM 등이 나타나 있지만, 포스터 한 장만으로 모든 사이클의 실행 스케줄과 각 모드의 선택 기준까지 재구성할 수 있는 것은 아니다.

## Systolic Array 데이터 흐름

IM2COL은 합성곱의 입력 패치를 행렬 곱에 맞는 형태로 바꾼다. 그다음에는 PE가 입력값과 가중치, Partial Sum을 일정한 규칙으로 처리해야 한다.

{{figure /figures/redrawn/cnn-dataflow.svg | 합성곱 입력을 변환하고 PE 배열에 공급하는 데이터 흐름을 나타낸 팀 설계 그림이다.}}

IM2COL 그림에는 차원 관계가 분명하게 적혀 있다. M은 Output Channel, K는 Kernel Width × Kernel Height × Input Channel, N은 Output Width × Output Height다. Kernel을 M×K로 Packing하고 Input Patch를 K×N으로 펼치면 결과가 M×N 형태가 된다. 이 과정에서 Patch를 준비하고 PL에 공급하는 비용도 남는다.

{{figure /figures/journals/cnn-poster-05-im2col-mkn.svg | 원본의 M×K × K×N = M×N 관계를 유지했다. Matrix 색상은 재배치를 설명하기 위한 것이다.}}

WS 구조에서는 가중치를 상대적으로 오래 유지하고 입력과 누산 값을 이동시키는 방식에 집중한다. IS 구조에서는 입력 재사용에 초점을 둔다. 어느 쪽이 유리한지는 입력 크기와 연산량뿐 아니라 메모리에서 가져와야 하는 데이터의 양에도 좌우된다.

내가 특히 많이 다뤘던 영역은 PS의 소프트웨어 전체, PL의 아키텍처와 타이밍 설계, Systolic Array 가속기와 WS/IS Dataflow였다. BRAM을 이용하는 데이터 경로는 팀원과 공동으로 설계했다. 양자화 CNN 학습과 곱셈기 기반·시프트 기반 행렬 곱 가속기를 각각 구현해 비교한 작업도 담당했다. 원래 포트폴리오에는 모바일 애플리케이션과 통신 서버 개발도 기록돼 있다.

{{figure /figures/redrawn/cnn-pe.svg | PE 내부에서 비트 시프트·부호 처리와 Partial Sum 누산을 어떻게 나눠 생각했는지 보여주는 회로 개념도다.}}

이 경험을 개인 프로젝트 하나로 표현하고 싶지는 않다. 팀이 함께 구축한 아키텍처와 평가 결과 위에서 각자 다른 부분을 맡았으며, 특히 BRAM 경로는 공동 작업이었다.

## FPGA 자원·정확도·처리 시간 비교

FPGA Implementation에는 Vivado 배치 화면과 두 개의 Utilization 표가 있다. 작은 배치 스크린샷을 확대하는 대신 원본에서 읽을 수 있는 수치를 따로 그렸다. 전체 Capacity는 LUT 53,200개, FF 106,400개, BRAM 140개이며, 36.5% 감소라는 결과는 LUT 사용량 비교에 해당한다. BRAM 사용량은 두 구현 모두 34개다.

{{figure /figures/journals/cnn-poster-11-fpga-resources.svg | 원본 Vivado 표에 기록된 Resource 수치를 재구성했다. 원래 Placement 화면까지 정확히 복원한 그림은 아니다.}}

최종 포스터에는 자원 사용량과 정확도, 처리 시간이 각각 제시돼 있다. 다만 **세 비교의 기준은 서로 같지 않다**는 점부터 확인해야 한다.

{{figure /figures/redrawn/cnn-results.svg | 팀 포스터의 FPGA 자원 사용량, Top-1 정확도, PS 단독과 PS+PL 실행 시간을 서로 다른 비교 기준으로 다시 그렸다.}}

먼저 FPGA 자원 사용량은 시프트 기반 가속기와 곱셈기 기반 가속기를 비교한다.

| 리소스 | 시프트 기반 | 곱셈기 기반 |
| --- | ---: | ---: |
| LUT | 12,603 | 19,833 |
| Flip-flop | 8,786 | 11,114 |
| BRAM | 34 | 34 |

포스터에서는 면적 감소를 36.5%로 제시했다. 위의 LUT 수치로 계산한 감소율이 약 36.5%이므로, 이를 모든 하드웨어 자원이나 실제 칩 면적이 일괄적으로 줄었다는 뜻으로 설명하기보다는 **LUT 사용량이 약 36.5% 감소했다**고 표현하는 편이 정확하다. BRAM은 두 구현에서 동일하게 34개다.

Accuracy 그래프에는 DenseNet·MobileNet·ResNet·LeNet 결과까지 함께 있다. 그렇다고 이들을 모두 같은 조건의 대조군처럼 해석할 수는 없다. 실제 우리 모델과 연결해서 읽어야 할 값은 Traditional Model 97.3%, Our Model 96.7%이며 차이는 0.6%포인트다.

{{figure /figures/journals/cnn-poster-12-top1-accuracy.svg | 원본 Accuracy 그래프에 나온 아홉 값을 모두 옮겼다. 직접 비교에는 Traditional·Our Model 두 값을 사용했다.}}

정확도 비교에서는 기존 모델의 Top-1 정확도가 **97.3%**, 시프트 기반 양자화 모델은 **96.7%** (Top-1)로 제시됐다. 두 결과의 차이는 **0.6%포인트**다. 다만 포스터만으로 데이터셋과 평가 프로토콜을 다른 환경에까지 일반화할 수는 없다.

처리 시간은 **PS(CPU) 단독 15.9ms**와 **PS+PL 8.83ms**를 비교한 결과다. 포스터에서 PS는 667MHz 듀얼 코어 ARM Cortex-A9로 설명돼 있다. 여기서 측정한 것은 전체 실행 구조의 차이이므로, 이 수치를 곧바로 “시프트 연산이 일반 곱셈보다 얼마만큼 빠르다”는 독립 실험으로 해석해서는 안 된다.

제목에 Energy-efficient라는 표현이 들어가지만, 포스터에는 전력과 에너지 소비를 직접 측정해 비교한 수치가 없다. 자원 사용량 감소와 실제 전력 절감을 같은 실험 결과처럼 쓰지 않으려 한다.

## 포스터의 세부 그림을 다시 살펴보면

기존 글에서는 대표 그림 몇 개에 내용을 너무 많이 압축했다. 원본에 있는 Weight 예시, 학습 과정, Buffer와 PE 연결, 실행 결과를 각각 다시 살펴봤다. **작은 이미지를 억지로 확대하지 않고** 확인 가능한 정보로 다시 그린 벡터 도식이다. 원본 캡처나 새 실험을 수행한 결과처럼 보이게 하지는 않았다.

### Weight를 Shift로 표현해 보면

{{figure /figures/journals/cnn-poster-07-weight-cells.svg | 원본 3×3 Weight 예시를 옮겼다. Fixed-Point Scale까지 명시된 비트 단위 연산 명세는 아니다.}}

### 양자화해도 학습을 이어갈 수 있었던 이유

{{figure /figures/journals/cnn-poster-08-ste-training.svg | 원본 STE 그림의 Forward Quantization과 Backward Gradient를 나눠 그렸다. 기존 방법을 적용한 것이다.}}

### Weight를 한 번에 모두 고정하지 않았다

{{figure /figures/journals/cnn-poster-09-inq-stages.svg | INQ의 단계적인 양자화 원리를 재구성했다. 정확한 Weight Index 선택 순서는 원본에 없으므로 Cell 색상은 예시다.}}

### PE 주변의 Buffer는 어떻게 연결되는가

{{figure /figures/journals/cnn-poster-03-systolic-buffers.svg | Weight·Activation·Accumulation Buffer와 PE Grid의 상대적 관계를 유지했다. 실제 RTL을 복제한 것은 아니다.}}

### WS와 IS에서 무엇을 오래 보관할까

{{figure /figures/journals/cnn-poster-04-ws-is-dataflow.svg | 포스터의 4×16 WS와 1×16 IS 표기를 사용했다. PE Cell은 일부만 나타냈으며 Cycle별 스케줄은 검증되지 않았다.}}

### Single PE 안쪽으로 들어가 보면

{{figure /figures/journals/cnn-poster-06-single-pe.svg | 원본의 Input·Weight·Shift·Partial Sum 누산을 나눠 그렸다. Shift로 바꿔도 Accumulation은 필요하다.}}

### 여러 Data Path의 결과를 BRAM으로 모으다

{{figure /figures/journals/cnn-poster-10-output-bram-dataflow.svg | 포스터의 DP1–DP8과 Output BRAM0–15를 기준으로 재구성했다. 기록되지 않은 Clock Timing은 만들지 않았다.}}

### 실행 시간은 정확히 무엇을 비교했나

{{figure /figures/journals/cnn-poster-13-runtime-table.svg | 원본의 PS Only 15.9ms와 PS+PL 8.83ms를 재현했다. Shift와 Multiply 연산기만 따로 비교한 시간은 아니다.}}

## 모델 표현에서 메모리 경로까지

이 프로젝트의 핵심은 곱셈기를 시프트 연산기로 바꾼 사실 자체보다, **신경망의 값 표현과 메모리·데이터 경로·회로 설계를 함께 조정했던 과정**에 있었다.

양자화로 연산을 단순화해도 메모리에서 값을 제시간에 공급하지 못하면 PE가 쉬게 된다. PE 배열을 병렬로 늘려도 PS에서 입력을 변환하고 제어하는 비용이 남는다. 자원 사용량이 줄어도 정확도나 전체 처리 시간이 목표에 못 미치면 좋은 가속기라고 말하기 어렵다.

팀 프로젝트에서는 가중치 양자화와 시프트 기반 합성곱, PS·PL 기능 분할과 데이터 흐름을 함께 설계했다. 평가 결과는 연산기 자원, 추론 정확도, 처리 시간을 구분해 해석해야 했으며, 특히 **PE 배열의 처리량과 메모리 공급 속도 사이의 균형**이 구현의 중요한 부분이었다.

## 참고 자료

- 2024년 경희대학교 전자공학 졸업 팀 포스터, *Bit-Shift-Based CNN Accelerator: A Compact and Energy-Efficient Solution*
- M. Elhoushi 외, *DeepShift: Towards Multiplication-Less Neural Networks* (2021)
- A. Zhou 외, *Incremental Network Quantization* (2017)
- S.-S. Park, K.-S. Chung, *CONNA: Configurable Matrix Multiplication Engine for Neural Network Acceleration* (2022)
