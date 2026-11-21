2024년 학부 프로젝트에서 TensorFlow Lite Micro(TFLM)의 메모리 배치 결과를 처음 들여다봤을 때, 이미 꽤 합리적인 설계라고 생각했다. Greedy Memory Planner는 텐서마다 메모리를 따로 잡아두는 대신, **Lifetime이 겹치지 않는 버퍼끼리 같은 공간을 재사용**하고 있었다. 텐서의 크기가 큰 순서대로 배치하면서 빈 공간도 찾았다.

그런데 Convolution의 실행 과정을 생각하다 보니 다른 질문이 생겼다. **입력 텐서가 아직 살아 있다는 사실과, 그 안의 모든 바이트를 앞으로 다시 읽어야 한다는 사실은 같은 말일까?**

Convolution은 입력을 한꺼번에 읽고 출력을 한꺼번에 만드는 연산이 아니다. 입력의 여러 위치를 차례로 참조하면서 출력을 채운다. 어떤 입력 영역은 마지막 읽기가 끝난 반면, 같은 텐서의 다른 영역은 다음 Window를 계산할 때 다시 필요할 수 있다. 이 차이를 메모리 플래너가 알 수 있다면 **Tensor 전체의 Lifetime보다 더 세밀한 단위로 공간을 재사용**할 수 있을 것이라고 생각했다.

그 아이디어를 실제 C++ 메모리 플래너에 반영한 것이 이 프로젝트다. 입력·출력 간에 허용되는 메모리 중복 범위를 **Conflict Data**로 표현하고, 그 관계를 이용해 **버퍼 배치 순서와 Offset 결정 알고리즘**을 바꿨다. 이후 TFLM에 통합하여 직접 만든 버퍼 테스트와 Person Detect, Tiny U-Net 모델에서 Peak Memory Usage를 비교했다.

이 글은 2024년 당시의 **8쪽 프로젝트 보고서, 실제 메모리 배치 출력 이미지, 구현 과정에 관한 대화 기록**을 다시 검토해 2026년 11월에 정리한 회고다. 프로젝트 수행 기간과 게시 시점은 다르다.

## 처음부터 메모리를 새로 관리하려던 것은 아니었다

기존 Greedy Memory Planner의 동작을 정확히 이해하는 일이 출발점이었다. 구현을 분석하면서 버퍼의 크기와 활성 구간을 받는 `AddBuffer()`, 필요한 시점에 배치 결과를 계산하는 `GetOffsetForBuffer()`, 내부 계산 함수인 `CalculateOffsetsIfNeeded()` 등을 따라갔다. 각 버퍼의 **Size, Lifetime, Offset**도 출력해 어떤 순서로 배치되는지 확인했다.

기존 플래너가 해결하는 문제는 명확했다. 서로 다른 시점에 사용하는 두 텐서라면 같은 메모리 주소를 사용해도 된다. 하지만 **동시에 활성 상태인 버퍼끼리는 기본적으로 중복을 허용하지 않는다.** 플래너가 알고 있는 정보가 텐서 단위의 크기와 생존 기간뿐이라면 안전한 판단이다.

문제는 그 판단이 실제 연산의 세부 실행 순서까지 반영하지 못한다는 점이었다.

| 판단 기준 | 확인할 수 있는 것 | 놓칠 수 있는 것 |
| --- | --- | --- |
| 텐서의 Lifetime | 두 버퍼가 동시에 필요한 시점이 있는가 | 텐서 내부에서 이미 마지막 읽기가 끝난 영역 |
| 메모리 Size·Offset | 각 버퍼가 차지하는 주소 범위 | 그 범위를 연산 도중 언제까지 보존해야 하는가 |
| Operator의 실제 접근 순서 | 입력의 마지막 Read와 출력의 첫 Write 시점 | 분석하지 않은 다른 Consumer의 의존성 |

**기존 방식도 이미 Lifetime 기반 메모리 재사용을 하고 있었다.** 우리가 하려던 일은 거기에 더해, *같은 Operator가 실행되는 동안* 입력의 일부와 출력의 일부를 안전하게 겹쳐 배치할 수 있는 조건을 찾는 것이었다.

## 왜 Convolution의 입력과 출력이 겹칠 수 있을까?

Convolution은 Kernel이 입력을 이동하며 계산한다. 한 번 사용된 입력 픽셀이라고 해서 반드시 불필요해지는 것은 아니다. 이웃한 출력 픽셀을 만들 때 같은 입력이 다시 사용될 수 있기 때문이다.

반대로 **해당 입력 위치를 참조하는 마지막 Window까지 처리했다면**, 그 위치의 원래 값을 앞으로 다시 읽을 이유가 없을 수 있다. 그때부터는 출력 데이터를 그 주소에 기록해도 계산 결과가 달라지지 않는 것이다.

2024년 보고서의 그림 5에서는 Convolution을 진행할수록 사용이 끝난 영역이 생기는 과정을 색으로 구분했다. 그림 6과 7에서는 그 생각을 실제 메모리 배치로 옮기면서, **허용되는 중복과 허용되지 않는 중복**을 나란히 설명했다.

{{figure /figures/journals/tflm-convolution-last-use.svg | Convolution의 Window가 이동하면서 입력 텐서 안에 마지막 Read를 마친 영역과 아직 사용해야 할 영역이 함께 존재하게 되는 과정을 그렸다. 원본 보고서 그림 5의 원리를 나타낸 개념도이며 특정 Kernel의 실제 실행 파형은 아니다.}}

{{figure /figures/redrawn/tflm-lifetime.svg | 입력 텐서 A와 출력 텐서 B가 시간상 함께 존재하더라도 일부 메모리 공간을 재사용할 수 있다는 원본 보고서의 개념도다. 표시된 L은 실제 연산의 입력 읽기 순서에서 도출해야 하는 배치 제약이다.}}

핵심은 **입력을 읽기 전에 출력을 써서 덮어쓰면 안 된다**는 것이다. 하나의 물리 주소가 입력 A와 출력 B에 모두 속한다면 다음 조건이 필요하다.

```text
같은 물리 주소를 입력 A와 출력 B가 공유할 때

입력 A의 마지막 Read 시점
           <
출력 B가 그 주소를 처음 덮어쓰는 Write 시점

그리고 다른 활성 Consumer가 그 입력 값을 더는 요구하지 않아야 한다.
```

이는 Tensor Lifetime만으로 알 수 있는 정보가 아니다. **실제로 어떤 순서로 연산하고 메모리에 접근하는지**가 필요하다.

### Kernel Size와 Stride만으로 바로 결정할 수 없는 이유

Convolution을 분석하려면 입력·출력의 Shape와 Layout, Kernel Size, Stride, Padding뿐 아니라 **Window를 처리하는 순서**도 알아야 한다. 예를 들어 위쪽 입력 행을 이미 한 번 사용했더라도, 다음 출력 행을 계산할 때 그 행이 다시 필요할 수 있다.

동일한 Convolution이라도 최적화된 Kernel이 Tile 단위로 입력을 읽거나 SIMD 명령으로 여러 데이터를 미리 가져온다면 Last Read 시점이 달라질 수 있다. 다른 연산이 같은 입력을 나중에 다시 사용하는 그래프라면 그 의존성도 보호해야 한다.

그래서 **겹칠 수 있는 바이트를 최대한 많이 찾는 일보다 정확히 어디까지 안전한지 정하는 일이 먼저**였다.

## Conflict Data는 무엇을 의미했나

프로젝트에서 사용한 Conflict Data는 이름과 달리 단순히 두 텐서가 충돌하는지 표시하는 Boolean이 아니다. **입력·출력 버퍼가 어떤 상대 위치에서 겹쳐도 되는지**를 플래너에 알려주는 정보다.

보고서에서는 입력 텐서 A와 출력 텐서 B의 관계를 다음처럼 정의했다.

```cpp
// 2024년 프로젝트에서 사용한 데이터 표현
// { Input Tensor ID, Output Tensor ID, signed overlap boundary }
{ A, B, -L }
```

본문의 수학적 표현으로는 `Conflict[A, B] = [-L, K]`이다. 여기서 `K`는 입력 텐서 A의 크기이며, `L`은 아직 보호해야 하는 입력 영역을 침범하지 않도록 배치 위치를 제한하는 경계다. 보고서에서는 **입력 크기 K를 플래너가 이미 알고 있으므로 따로 저장하지 않고 -L만 기록**했다.

중요한 것은 `L`이 상수가 아니라는 사실이다. 같은 텐서라도 연산의 접근 순서와 메모리 Layout이 달라지면 안전한 경계가 달라진다. Conflict Data를 입력하기 전에 그 관계를 분석해야 했다.

{{figure /figures/journals/tflm-conflict-extraction.svg | 모델에서 Input·Output Tensor의 ID와 Size를 확인하고, Operator의 마지막 입력 Read와 첫 출력 Write를 비교해 허용 범위를 구한 뒤, Conflict Data 배열로 정리하는 흐름이다. Compiler Profiling 자동화는 당시 구현 기능이 아니라 후속 과제로 구분했다.}}

## 실제 Conflict Data를 어떻게 구했나

이 부분은 내가 과거에 따로 설명하면서도 반드시 구분했던 작업이다. **실험에 사용한 모델별 Conflict Data는 팀원이 직접 계산해 배열로 구성했다.** 나는 이를 기반으로 작동하는 **C++ Planner의 Buffer Ordering, Offset Allocation과 TFLM 통합**을 맡았다.

수동 분석이 어떤 원리로 이루어지는지는 다음 순서로 이해할 수 있다.

### 1. 모델에서 Input·Output 관계와 버퍼 정보를 확인한다

먼저 모델의 Operator 목록과 입력·출력 Tensor ID를 확인한다. 예컨대 어떤 Convolution이 A를 입력으로 읽고 B를 출력으로 생성한다면, 해당 Pair에 대해 추가적인 메모리 재사용 기회가 있는지 분석할 수 있다.

동시에 두 Tensor의 Size와 Lifetime, 다른 Consumer가 있는지도 알아야 한다. 모델 그래프에 Branch가 있거나 입력 데이터를 이후 연산에서 다시 읽는다면, 한 Operator만 보고 안전한 영역을 결정할 수는 없다.

### 2. 입력의 마지막 Read와 출력의 Write 순서를 비교한다

Convolution의 Kernel이 입력의 어떤 영역을 언제 마지막으로 사용하는지 살핀다. 출력이 증가하는 방향으로 기록된다고 해도 **입력의 마지막 사용 시점은 그와 일치하지 않을 수 있다.** Sliding Window에서 동일한 입력이 여러 출력에 기여하기 때문이다.

안전한 중복은 **출력 데이터가 어떤 주소를 덮어쓸 때 그 주소의 입력이 이미 마지막 Read를 마친 경우**에만 가능하다. 아직 사용할 입력 영역까지 덮어쓰면 값이 손상된다.

### 3. 중복이 불가능한 상대 위치를 경계로 표현한다

마지막 사용 시점과 출력의 기록 순서를 비교해, 출력 B를 입력 A보다 어디에 배치할 수 있는지 결정한다. 보고서는 그 상대 위치의 제약을 `-L`과 입력 전체 크기 `K`로 설명한다.

이때 실제 모델마다 `L`이 달라질 수 있다. 무턱대고 두 버퍼를 가능한 한 많이 겹치게 만드는 방식이 아니라, **해당 Pair에 대해 허용된 배치만 플래너가 시도하도록 경계값을 전달**하는 것이다.

### 4. 텐서 ID와 경계를 정적 배열로 기록한다

실험에서는 분석한 관계를 `{ Input ID, Output ID, -L }` 항목으로 작성해 모델별로 전달했다. 나중에 TFLM을 연결할 때는 `conflict.h`처럼 프로젝트에 포함된 Header에 데이터를 보관하고, Interpreter 초기화 시 그 배열과 개수를 넘겨주는 방식도 검토·적용했다.

**Compiler Profiling으로 Conflict Data를 자동 추출하는 프로그램을 완성했던 것은 아니다.** 논문의 마지막에서도 자동 추출과 Operator별 정확성 검증은 후속 연구로 남겨뒀다. 추후에 자동화한다면 실제 Kernel의 Read/Write를 분석해 같은 조건을 구하고, 그 결과가 올바른지를 검사해야 한다.

### 5. 배치 결과와 실제 연산의 정확성을 따로 확인한다

Conflict Data를 적용한 뒤에는 메모리 배치 결과가 의도한 대로 겹치는지 확인해야 한다. 하지만 Offset이 줄었다는 사실만으로 연산이 올바르다고 결론 내릴 수는 없다. 실제 In-place 업데이트를 적용했을 때 **기존 Planner의 추론 결과와 동일한지**도 확인해야 한다.

나중에 프로젝트를 다시 정리하면서 기억에 남았던 오류도 있었다. 겹침 경계를 너무 공격적으로 설정해 아직 사용해야 하는 입력 영역까지 출력이 덮어쓰면서 실행이 정상적으로 이루어지지 않았고, **안전한 범위를 다시 확인해 경계를 조정**했다. 다만 이러한 개별 문제 해결과 모든 Kernel·모델에 대한 체계적인 정합성 검증은 다르다. 당시 후자까지 완료했다고 소개하지는 않는다.

## 기존 Greedy Planner에서 확인한 Offset 탐색

원래 Planner는 버퍼의 크기와 Lifetime을 등록받은 다음, **동시에 존재하는 버퍼의 메모리 구간을 피해 가능한 한 낮은 Offset**을 찾는다.

보고서에는 `NextSimultaneouslyActiveBuffer()`를 이용해 현재 버퍼와 활성 기간이 겹치는 기존 버퍼를 찾고, `Prior Entry`와 `Next Entry` 사이의 `Gap`이 충분한지 확인하는 과정이 정리돼 있다.

```text
Candidate Offset을 0에서 시작

현재 버퍼와 동시에 존재하는 기존 버퍼를 확인
    ├─ Gap이 충분하면 Candidate Offset에 배치
    └─ 부족하면 기존 버퍼의 끝으로 Candidate Offset 이동

다음 후보에서도 같은 과정 반복
```

이 방식은 해당 텐서들이 같은 시점에 활성 상태일 때 **메모리 공간 자체도 겹치면 안 된다**고 가정한다. Conflict Data를 활용하려면 그 전제를 일부 관계에서만 완화할 방법이 필요했다.

## 첫 번째 수정: 출력부터 배치하는 Reverse BFS

기존 Greedy Planner의 큰 버퍼 우선 배치 전략을 전부 버리지는 않았다. **Conflict 정보가 없는 Online Buffer는 크기가 큰 순서대로 먼저 배치**하고, Conflict 관계가 존재하는 Online Buffer에 별도의 배치 순서를 적용했다. Offline Buffer를 다루는 기본 흐름도 유지했다.

직접 만든 버퍼 테스트에서는 **0, 1, 5, 7번이 Non-Conflict Buffer**, **2, 3, 4, 6번이 Conflict Buffer**로 분류됐다. Conflict Buffer 사이의 연결 관계는 출력에서 입력 방향으로 거슬러 올라가도록 정리했다.

보고서의 예시 그래프에는 `A → B`, `B → C`, `C → E`, `D → E` 관계가 있다. 가장 뒤의 출력 E를 Root로 삼고 **BFS로 가까운 Level부터 순회**한다. 같은 Level에서는 Size가 큰 버퍼를 우선했다.

{{figure /figures/redrawn/tflm-conflict-graph.svg | E를 Root로 하는 역방향 Conflict Graph다. 입력을 먼저 놓는 대신 출력을 낮은 Offset에 배치하고, 이후 입력을 Conflict 경계에 맞추기 위해 BFS를 사용했다.}}

### 왜 하필 출력부터 배치했을까?

이 질문이 당시 알고리즘을 설계하면서 중요했다.

메모리 플래너는 기본적으로 Offset 0에서 출발해 빈 공간을 찾는다. 먼저 출력 버퍼를 낮은 주소에 배치한다면, 그 출력에 대응하는 입력 버퍼를 나중에 넣을 때 **출력 버퍼의 전체 크기 대신 허용된 L 경계만큼 이동**시키는 선택지가 생긴다.

반대로 입력을 먼저 큰 버퍼로 배치하면, 그 입력과 출력을 나중에 맞추는 과정에서 빈 공간을 효율적으로 찾지 못할 수 있다. 그래서 Output에서 Input으로 이동하는 BFS가 자연스러웠다.

물론 BFS가 전역 최적해를 찾아준다는 보장은 없다. Conflict 관계가 적거나 버퍼의 크기 분포가 다르면 기존 Greedy 순서보다 불리할 수도 있다. **실제 배치 기회를 늘리기 위해 고른 휴리스틱**이라는 것이 정확한 설명이다.

## 두 번째 수정: Conflict를 고려한 Candidate Offset

배치 순서를 바꾼 것만으로 충분하지 않았다. 기존 알고리즘이 겹침을 아예 허용하지 않으면 아무리 출력을 먼저 배치해도 입력은 여전히 그 뒤에 놓일 것이기 때문이다.

그래서 **Candidate Offset을 갱신하는 부분**을 수정했다.

```text
기존:
    Candidate Offset = Offset(B) + Size(B)

Conflict 관계가 허용될 때:
    Candidate Offset = Offset(B) + L
```

여기서 B는 이미 배치한 Output Tensor이고, 새로 배치하려는 것은 그와 관계된 Input Tensor A다. 두 번째 방식은 출력의 끝까지 무조건 건너뛰지 않고 **안전한 겹침 경계를 이용해 입력을 일부 중첩 배치할 수 있게** 한다.

{{figure /figures/redrawn/tflm-offset.svg | 기존 Planner가 Next Entry의 끝으로 이동하는 방식과, Conflict 경계 L을 이용해 더 낮은 Candidate Offset을 고려하는 방식을 비교한 그림이다. 실제 Offset은 전체 활성 버퍼의 제약을 함께 고려해야 한다.}}

단, 다른 활성 버퍼와의 충돌까지 허용한 것은 아니다. 현재 입력과 특별한 Conflict 관계가 없는 버퍼라면 기존처럼 함께 메모리를 점유하지 않도록 배치해야 했다. **정렬과 Gap 탐색을 모두 수정해야** 원래 의도한 결과가 나왔다.

보고서의 구성 버퍼 테스트를 보면 **3–4번, 4–6번 버퍼는 허용된 중복 배치**를 이용했다. 반면 **2–3번은 다른 형태로 배치하는 편이 더 유리**했다. 모든 Conflict 관계를 억지로 겹치는 것이 아니라, 조건을 만족하면서 낮은 Peak를 찾도록 한 것이다.

## TFLM에 통합하고 실제 모델로 확장하기

처음에는 모델을 통째로 실행하는 대신, 내가 만든 버퍼 목록에서 두 Planner가 내놓는 **Offset과 최대 사용 주소**부터 비교했다. 수동 버퍼 테스트에서 기본 정렬·배치 동작이 확인되면 실제 TFLM의 Interpreter 경로에 넣어 더 복잡한 그래프에서도 같은 로직이 동작하는지 확인했다.

이를 위해 C++ Planner가 Conflict Data 배열을 받을 수 있도록 만들고, Interpreter 초기화 시 **Conflict Data와 항목 개수**를 함께 넘기도록 연결했다. 모델마다 다른 관계를 전달하더라도 Planner의 일반적인 배치 알고리즘을 다시 수정할 필요는 없도록 한 것이다.

이 과정에서는 모델과 라이브러리의 호환성 문제도 있었다. Tiny U-Net에는 여러 Operator가 들어 있고, 당시 환경에서는 필요한 Operator 등록이나 버전 지원이 맞지 않아 `AllocateTensors()`에서 오류가 발생하기도 했다. 이런 런타임 연동 문제는 메모리 플래닝 수치와 별개로 해결해야 하는 문제였다.

## 실험에서 확인한 결과

당시 보고서는 **실제 메모리 플래너가 계산한 Peak Buffer 사용량**을 비교했다. MCU 전체 RAM 사용량, 추론 시간 또는 에너지 소모를 측정한 표는 아니다.

| 대상 | Greedy Planner | Conflict Based Planner | 절약한 메모리 | 보고서에 적힌 감소율 |
| --- | ---: | ---: | ---: | ---: |
| 구성한 버퍼 테스트 | 4,101 bytes | 3,585 bytes | 516 bytes | 12.58% |
| Person Detect | 55,296 bytes | 39,636 bytes | 15,660 bytes | 28.33% |
| Tiny U-Net | 230,416 bytes | 198,120 bytes | 32,296 bytes | 14.06% |

Person Detect에서는 전체 크기에 비해 중복 배치의 이점이 컸고, Tiny U-Net에서는 더 많은 메모리를 절약했지만 원래 버퍼 크기와 활성 기간이 길어 **비율로 본 개선폭은 상대적으로 작았다.**

참고로 **보고서에 기재된 감소율과 Byte 값으로 다시 계산한 감소율에는 작은 차이가 있다.** Person Detect는 Byte 기준 약 28.32%, Tiny U-Net은 약 14.02%다. 위 표의 28.33%, 14.06%는 원본 보고서의 표기를 유지한 것이다.

이 결과를 해석할 때 가장 중요한 점은 **버퍼를 압축한 것이 아니라, 같은 바이트를 다른 시점에 사용하도록 배치 전략을 바꾼 것**이라는 사실이다.

## 메모리 사용량보다 먼저 지켜야 할 것

이 프로젝트에서 **Conflict 정보를 실제 C++ Planner의 배치 순서와 Offset 계산에 연결했고, TFLM에 통합해 두 모델의 Peak Allocation을 낮춘 것**은 분명한 구현 성과다.

동시에 가장 큰 숙제도 남겼다. **안전한 Conflict 경계를 누가 어떻게 증명할 것인가?** 수동으로 계산하는 방식은 실험 모델을 바꾸거나 Operator의 내부 구현이 달라질 때마다 다시 확인해야 한다. 특히 최적화된 Kernel의 실제 메모리 접근 패턴이 달라지면 기존 경계를 그대로 쓸 수 없다.

그래서 당시 결론에서도 두 가지 발전 방향을 제시했다. 하나는 **Compiler Profiling이나 연산 접근 분석을 통해 Conflict Data를 자동 생성**하는 것이고, 다른 하나는 고정된 BFS 순서에만 의존하지 않고 각 배치 후보가 전체 Peak를 얼마나 증가시키는지 평가하는 방식이다. 여기에 기존 Planner와 개선 Planner의 **추론 결과 동등성 검증**을 함께 넣어야 진정으로 안전한 재사용이라고 말할 수 있다.

돌이켜 보면 이 프로젝트에서 다룬 것은 그저 버퍼 크기를 줄이는 문제가 아니었다. **이미 읽기를 마친 데이터와 앞으로도 읽어야 할 데이터를 구분해, 실제 실행 순서를 메모리 할당 정책에 반영한 것**이었다. 이 차이를 코드로 구현하고 배치 결과로 확인한 경험이 가장 크게 남았다.

## 원본 자료와 참고 문헌

- 2024년 경희대학교 학부 프로젝트 보고서, *Memory Management through Lifecycle Analysis in TFLite Micro for Resource-Constrained Devices*. 그림 1~26과 실제 Buffer 출력·실험 결과를 기준으로 재구성했다. 원본 보고서의 개인 식별 정보와 캡처 파일은 이 페이지에 직접 게시하지 않았다.
- R. David 외, [*TensorFlow Lite Micro: Embedded Machine Learning on TinyML Systems*](https://arxiv.org/abs/2010.08678)
- [TensorFlow Lite Micro 소스 저장소](https://github.com/tensorflow/tflite-micro)

## 원본 실험 화면 아카이브 — 보고서 그림 10~26

최종 절감률만으로는 당시의 메모리 배치가 실제로 어떻게 달라졌는지 알기 어렵다. 원본 보고서에는 버퍼를 등록한 코드부터 정렬 로그, 수동으로 계산한 Conflict Data, 텐서들이 겹치는 모습을 색으로 표시한 콘솔 화면까지 남아 있었다. 아래에는 **그림 10~26의 원본 이미지 17개를 빠짐없이** 실었다.

여기에서 사용하는 SVG는 원본 JPEG를 그대로 담는 **보존용 컨테이너**다. 원본 이미지의 모양과 글자·색상·배치를 바꾸지 않았지만, 내부까지 벡터로 변환한 것은 아니다. 각 그림을 열면 원본 해상도로 확인할 수 있다. **폭이 작은 원본 캡처는 본문에 맞춰 억지로 확대하지 않고 원본 픽셀 너비로 표시한다.** 큰 그림은 화면에 맞춰 축소될 수 있으며, 누르면 원본 크기로 열린다. SVG 컨테이너에 담았다고 원본에 없던 디테일이 생기지는 않는다. 그 뒤에 나오는 벡터 도식은 이 자료를 이해하기 쉽게 따로 재구성한 분석용 그림이다.

### 직접 구성한 버퍼 테스트 — 그림 10~16

{{figure /figures/journals/tflm-source-figure-10.svg | 원본 그림 10. 직접 구성한 실험의 버퍼 8개를 등록한 코드다. Size와 First/Last Use를 원본 그대로 보존했다.}}

{{figure /figures/journals/tflm-source-figure-11.svg | 원본 그림 11. 기존·개선 플래너가 최종 Offset을 계산하기 전의 버퍼 출력 결과다.}}

{{figure /figures/journals/tflm-source-figure-12.svg | 원본 그림 12. 기존 Greedy Planner가 버퍼를 크기 중심으로 정렬한 순서와 실제 Offset이 담겨 있다.}}

{{figure /figures/journals/tflm-source-figure-13.svg | 원본 그림 13. 기존 방식의 주소 배치가 콘솔 문자로 그려진 원본이다. 계획상 Peak는 4,101 bytes였다.}}

{{figure /figures/journals/tflm-source-figure-14.svg | 원본 그림 14. (2,3,−256), (3,4,−256), (4,6,−256) 관계를 등록한 실제 코드 화면이다.}}

{{figure /figures/journals/tflm-source-figure-15.svg | 원본 그림 15. 개선 Planner가 결정한 배치 순서와 각 버퍼의 Offset·Lifetime이 출력된 결과다.}}

{{figure /figures/journals/tflm-source-figure-16.svg | 원본 그림 16. 중복 주소가 허용된 결과를 콘솔 문자와 ! 표시로 확인할 수 있다. Peak는 3,585 bytes였다.}}

작은 구성이라서 배치 전략의 차이가 선명하다. 기존 Greedy Planner는 **4,101 bytes**, 개선 Planner는 **3,585 bytes**를 사용했다. 아래 분석용 SVG에서는 이 원본 로그에 기록된 Size·Lifetime·Offset을 그대로 이용해 각 버퍼의 위치를 다시 그렸다.

### Person Detect — 그림 17~21

{{figure /figures/journals/tflm-source-figure-17.svg | 원본 그림 17. Person Detect의 기존 Greedy Planner가 계산한 버퍼 배치 순서·Offset 목록이다.}}

{{figure /figures/journals/tflm-source-figure-18.svg | 원본 그림 18. Person Detect의 기존 배치 결과다. 각 색의 텐서가 시간·주소 공간을 차지하는 실제 화면으로, Peak는 55,296 bytes였다.}}

{{figure /figures/journals/tflm-source-figure-19.svg | 원본 그림 19. Person Detect에 대해 팀원이 수동으로 계산해 전달했던 Conflict Data 배열이다.}}

{{figure /figures/journals/tflm-source-figure-20.svg | 원본 그림 20. Non-Conflict Online Buffer와 BFS로 정렬한 Conflict Buffer가 구분되는 실제 로그다.}}

{{figure /figures/journals/tflm-source-figure-21.svg | 원본 그림 21. Conflict Data를 적용한 뒤 실제로 출력된 다색 배치 화면이다. 계획상 Peak는 39,636 bytes로 감소했다.}}

두 메모리 배치 화면을 비교하면 무엇이 바뀌었는지 더 분명하게 보인다. **55,296 bytes에서 39,636 bytes**로 줄어든 것은 버퍼의 내용을 압축해서가 아니라, 수동으로 전달한 Conflict 경계에 따라 같은 메모리 주소를 다른 데이터가 재사용하도록 했기 때문이다.

### Tiny U-Net — 그림 22~26

{{figure /figures/journals/tflm-source-figure-22.svg | 원본 그림 22. Tiny U-Net에서 Size 순으로 배치한 기존 플래너의 긴 버퍼·Offset 목록이다.}}

{{figure /figures/journals/tflm-source-figure-23.svg | 원본 그림 23. 큰 버퍼와 긴 Lifetime이 드러나는 Tiny U-Net의 기존 메모리 배치 화면이다. Peak는 230,416 bytes였다.}}

{{figure /figures/journals/tflm-source-figure-24.svg | 원본 그림 24. Tiny U-Net에 전달한 수동 Conflict Data 목록을 원본 화면 그대로 보존했다.}}

{{figure /figures/journals/tflm-source-figure-25.svg | 원본 그림 25. 일반 버퍼와 Conflict BFS 대상 버퍼의 순서가 나뉜 개선 Planner 로그다.}}

{{figure /figures/journals/tflm-source-figure-26.svg | 원본 그림 26. 큰 버퍼 주변에 허용된 중복이 적용된 최종 배치 화면이다. 계획상 Peak는 198,120 bytes였다.}}

Tiny U-Net은 큰 버퍼와 긴 Lifetime 때문에 배치가 더 복잡했다. 원본 화면에는 **230,416 bytes에서 198,120 bytes**로 감소한 결과가 남아 있다. 다만 이 화면만으로 모든 Operator의 In-place 연산이 항상 정확하다는 것을 증명할 수는 없다.

---

## 분석용 벡터 SVG: 모델별 결과 비교

원본 보고서에는 버퍼 구성부터 정렬 순서, Offset 출력, 모델별 Memory Allocation Plan까지 많은 결과 그림이 있다. 기존 글에서는 최종 수치만 남아 있었지만, 이 실험에서 중요한 것은 **어떤 배치가 실제로 달라졌는지**다.

원본 화면은 위에 보존했다. 아래의 별도 분석용 벡터 SVG는 보고서의 그림 10~26과 수치 결과를 바탕으로 결과를 비교하기 쉽게 다시 구성했다. **원본 콘솔 화면을 그대로 재실행한 캡처가 아니라, 확인된 수치·배치 단계의 벡터 재구성**이다. 개별 버퍼의 길이나 Offset은 모두 기계적으로 추출할 수 없었으므로, 색으로 표시한 배치 패턴은 구조를 설명하는 용도로 사용했다.

### 1. 직접 구성한 버퍼 테스트

{{figure /figures/journals/tflm-result-constructed-baseline.svg | 원본 그림 10~13의 기존 Greedy Memory Planner 결과다. 직접 만든 버퍼 세트에서 Peak Memory Usage가 4,101 bytes로 나타났다.}}

{{figure /figures/journals/tflm-result-constructed-optimized.svg | 원본 그림 14~16의 Conflict Based Planner 결과다. 0·1·5·7번 버퍼를 먼저 배치하고, 2·3·4·6번을 BFS 순서로 처리해 Peak를 3,585 bytes로 줄였다.}}

이 실험의 역할은 단순히 절감률을 구하는 것이 아니었다. **기존에 겹칠 수 없었던 버퍼가 실제로 의도한 관계로 배치되는지** 확인해야 했다. 작은 구성이라 서로 다른 배치의 차이를 눈으로 비교하기에 적합했다.

### 2. Person Detect

{{figure /figures/journals/tflm-result-person-detect-baseline.svg | 보고서 그림 17~18의 Person Detect Greedy Planner 결과다. 기존 방식의 Peak Buffer Usage는 55,296 bytes였다.}}

{{figure /figures/journals/tflm-result-person-detect-optimized.svg | 그림 19~21에 대응하는 개선 결과다. 수동으로 구성한 Conflict Data를 적용해 Peak가 39,636 bytes로 줄었고, 총 15,660 bytes를 절약했다.}}

원래 배치에서는 큰 버퍼가 먼저 배치되고 다른 버퍼가 빈 공간을 찾았다. 수정한 Planner에서는 Non-Conflict 버퍼를 정렬한 뒤 Conflict 관계가 있는 버퍼들을 따라가며 더 낮은 Offset을 사용할 수 있는 곳을 찾았다.

**큰 감소율이 나온 이유는 단순히 모델이 작아서가 아니라, 해당 버퍼 그래프에서 활용할 수 있는 중복 배치의 비중이 상대적으로 컸기 때문**이라고 해석할 수 있다.

### 3. Tiny U-Net

{{figure /figures/journals/tflm-result-tiny-unet-baseline.svg | 원본 그림 22~23에 나온 Tiny U-Net의 Greedy Planner 결과다. 큰 버퍼와 긴 Lifetime의 영향으로 Peak가 230,416 bytes까지 높아졌다.}}

{{figure /figures/journals/tflm-result-tiny-unet-optimized.svg | 원본 그림 24~26의 Conflict Based 결과를 바탕으로 구성했다. Peak는 198,120 bytes로 감소했고, 32,296 bytes를 절약했다.}}

Tiny U-Net에는 크기가 큰 버퍼와 Lifetime이 긴 버퍼가 더 많이 나타났다. 그만큼 배치 제약이 복잡했지만, Output-first BFS와 Conflict 기반 Offset 갱신을 적용한 뒤에도 메모리를 줄일 수 있었다.

절약한 Byte 수는 Person Detect보다 컸지만 **원래 Peak 자체가 더 컸으므로 감소율은 작았다.** 이러한 차이는 모델의 그래프와 Tensor Size·Lifetime에 따라 최적화 효과가 달라질 수 있다는 것을 보여준다.

### 4. 세 실험의 Peak Memory 비교

{{figure /figures/journals/tflm-result-peak-summary.svg | 원본 보고서에 기재된 Byte 수치를 기준으로 세 실험의 Before·After를 비교한 그래프다. 각 실험 안에서는 같은 축척을 사용했고, 원본 감소율은 별도로 표시했다.}}

## 분석용 벡터 SVG: 원본 수치로 재구성한 배치

감소율만 보여주면 그 숫자가 어떤 과정을 거쳐 나왔는지 알기 어렵다. 직접 만든 버퍼 실험은 다행히 원본 보고서에 각 버퍼의 **크기, 활성 구간, 최종 Offset**이 모두 남아 있다. 그래서 이번에는 임의로 막대의 길이를 맞추지 않고, 실제로 기록된 주소와 활성 구간을 기준으로 메모리 배치를 다시 그렸다.

Person Detect와 Tiny U-Net도 수동으로 작성했던 Conflict Data 배열을 원본에서 확인했다. 다만 두 모델의 모든 버퍼 Offset을 현재 완전한 기계 판독 데이터로 확보한 것은 아니다. 앞에서 보여준 모델별 결과 그림은 실제 Peak 수치와 배치 양상을 설명하는 재구성이고, 아래의 구성 버퍼 테스트처럼 개별 Offset까지 복원한 결과와는 구분했다.

### 구성한 버퍼 실험 — 원본 그림 10~16

{{figure /figures/journals/tflm-report-figure-10.svg | 원본 그림 10. 테스트에 사용한 여덟 개의 AddBuffer 호출을 Size와 First/Last Use까지 그대로 옮겼다. 임의로 새 버퍼를 만든 것이 아니다.}}

{{figure /figures/journals/tflm-report-figure-11.svg | 원본 그림 11. 플래너 비교 이전에 출력한 초기 버퍼 목록이다. 여기에 적힌 Offset은 각 플래너가 최종으로 계산한 배치와 구분해야 한다.}}

{{figure /figures/journals/tflm-report-figure-12.svg | 원본 그림 12. 기존 Greedy Planner의 정렬 순서와 실제 Offset이다. 7, 4, 6, 5번 버퍼를 먼저 배치했으며, 전체 Size의 합계가 아니라 가장 높은 끝 주소가 Peak를 결정한다.}}

{{figure /figures/journals/tflm-report-figure-13.svg | 원본 그림 13의 배치 정보를 정확한 Size·Offset·Lifetime으로 다시 그렸다. 가로축은 실제 Byte 주소이고 세로축은 버퍼 활성 시점이다. 기존 방식의 Peak는 4,101 bytes다.}}

{{figure /figures/journals/tflm-report-figure-14.svg | 원본 그림 14. 직접 구성한 테스트에서 사용한 Conflict Data는 (2,3,−256), (3,4,−256), (4,6,−256) 세 관계다.}}

{{figure /figures/journals/tflm-report-figure-15.svg | 원본 그림 15. 개선 Planner가 결정한 배치 순서는 7, 5, 1, 0, 6, 4, 3, 2다. Non-Conflict Buffer를 먼저 처리하고, Conflict 관계를 갖는 버퍼를 역방향으로 따라간다.}}

{{figure /figures/journals/tflm-report-figure-16.svg | 원본 그림 16의 실제 Offset으로 다시 그린 배치다. 3번 [2564,3585)과 4번 [2308,3333), 4번과 6번 [2052,3076)은 주소가 일부 겹친다. 2번과 3번은 굳이 중복 배치하지 않았다. Peak는 3,585 bytes다. 이 그림은 계획된 주소 공유를 보여주며, 실제 연산 정확성의 증명과는 구분해야 한다.}}

여기서 흥미로운 것은 **메모리를 재사용할 수 있다고 해서 모든 버퍼를 억지로 겹치게 하지 않았다는 점**이다. 3–4번과 4–6번은 허용된 영역을 공유했지만, 2–3번은 다른 위치에 놓는 편이 결과적으로 유리했다. 배치 순서와 Conflict 범위를 모두 고려해야 했던 이유가 실제 수치에 드러난다.

### 실제 모델에 전달한 Conflict Data — 원본 그림 19와 24

{{figure /figures/journals/tflm-report-figure-19.svg | 원본 그림 19의 Person Detect Conflict Data 31개 항목을 다시 작성했다. 경계가 0인 관계도 제외하지 않았다. 팀원이 계산해 전달한 모델별 데이터이며, 자동 프로파일러가 생성한 결과는 아니다.}}

{{figure /figures/journals/tflm-report-figure-24.svg | 원본 그림 24의 Tiny U-Net Conflict Data 44개 항목이다. 큰 음수 경계와 일반적인 인접 관계 외의 Pair도 보여, Size와 Lifetime 정보만으로 안전한 메모리 중복을 정할 수 없다는 점을 드러낸다.}}

원본 보고서에는 이 밖에도 두 모델의 버퍼 출력과 긴 메모리 배치 화면(그림 17~18, 20~23, 25~26)이 있다. 앞쪽의 실험 결과 SVG는 그 자료를 참고한 요약이지만, 정확하게 판독되지 않은 개별 Offset을 새로 만들어 넣지는 않았다. **수치까지 다시 계산할 수 있는 결과와, 원본 화면의 경향을 설명한 그림을 구분하는 것**이 기록으로서 더 중요하다고 생각한다.
