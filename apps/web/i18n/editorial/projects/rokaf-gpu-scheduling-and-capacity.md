GPU를 여러 서비스가 나눠 사용하도록 설정하면서 처음에는 사용률 그래프를 자주 보았다. GPU 사용률이 낮으면 여유가 있다는 생각이 들기 때문이다. 하지만 실제 모델 서버를 운영할 때는 사용률이 낮아 보여도 VRAM이 이미 대부분 점유돼 있을 수 있었다. 새로운 모델은 연산을 시작하기 전에 메모리 부족으로 실패할 수도 있다.

이런 상황에서 Kubernetes가 GPU 리소스를 몇 개 노출하는지만 보고 서비스 수용량을 판단하는 것은 위험했다. 나는 실제로 Time-slicing을 구성하면서 **스케줄러가 배치할 수 있는 자원**과 **모델이 메모리와 지연시간 조건 안에서 쓸 수 있는 자원**을 나눠 생각하려 했다.

## 논리 GPU 슬롯을 늘린다는 의미

NVIDIA Device Plugin은 GPU를 Kubernetes의 확장 리소스로 노출한다. 일반적인 GPU 전체 할당에서는 Pod가 물리 장치의 자원을 독점적으로 사용하도록 배치한다.

Time-slicing을 활성화하면 하나의 물리 GPU를 여러 개의 논리적인 할당 슬롯처럼 광고할 수 있다. 스케줄러가 배치할 수 있는 Pod 수가 늘어날 수 있다는 의미다. 하지만 물리 GPU의 SM 수나 VRAM 용량이 늘어난 것은 아니다.

이 부분이 특히 중요했다. **Time-slicing의 Replica 수를 늘린다고 각 Pod에 VRAM이 일정 비율로 보장되는 것은 아니다.** GPU의 물리 메모리는 여전히 공유되며, 실행 시간과 메모리 대역폭 경쟁도 발생할 수 있다.

{{figure /figures/journals/gpu-capacity-tradeoffs.svg | GPU 전체 할당, Time-slicing, 지원 GPU의 MIG는 물리 자원을 서로 다르게 나눈다. 슬롯 수가 늘어나는 것과 하드웨어 분할은 같은 개념이 아니다.}}

## 같은 GPU를 쓰는 세 가지 방식

### GPU 전체 할당

하나의 워크로드가 장치 할당을 독점하면 다른 워크로드와 같은 GPU를 Time-slicing 방식으로 공유하지 않는다. 큰 모델의 Weight와 KV Cache를 올리거나 예측하기 어려운 메모리 증가가 있는 경우에 단순한 선택이다.

대신 GPU의 연산 자원이 많이 남아도 다른 모델을 함께 배치하기 어려울 수 있다. 독점 할당이라고 해서 드라이버 오류나 호스트 장애까지 사라지는 것은 아니다.

### Time-slicing

Time-slicing은 여러 워크로드가 하나의 물리 GPU를 번갈아 사용하도록 만든다. 작은 모델이 많고 실행 시간이 짧다면 장치 활용도를 높일 수 있다.

그러나 두 모델이 동시에 VRAM을 많이 사용하려고 하면 메모리 부족이 발생할 수 있다. 둘 다 메모리에 들어가더라도 실행 경쟁으로 응답 시간의 긴 꼬리, 즉 Tail Latency가 늘 수 있다. 그래서 Time-slicing의 효과는 광고한 논리 Replica 수가 아니라 **어떤 워크로드들이 함께 실행되느냐**에 달려 있다.

### MIG

MIG는 지원되는 NVIDIA GPU에서 컴퓨트와 메모리 자원을 하드웨어 인스턴스로 분할하는 방식이다. Time-slicing과 달리 인스턴스별 메모리 자원이 나뉘기 때문에 격리 측면에서 더 예측 가능한 조건을 제공한다.

다만 모든 GPU가 MIG를 지원하는 것은 아니고, 사용할 수 있는 Profile에도 크기 제한이 있다. 모델이 특정 Profile의 메모리를 넘으면 다른 논리 슬롯을 요청한다고 해결되지는 않는다. Profile과 수요가 맞지 않으면 일부 용량을 제대로 활용하지 못할 수도 있다.

내가 실제로 구성한 것은 Time-slicing이고, MIG는 **지원 하드웨어를 전제로 비교·검토한 대안**이다. 세 방식을 모두 실제 클러스터에서 같은 조건으로 벤치마크했다고 표현하지 않는다.

| 고민 | 우선 살펴볼 방식 |
| --- | --- |
| Weight와 KV Cache가 큰 모델 | GPU 전체 할당 |
| 작고 간헐적으로 실행되는 여러 모델 | Time-slicing |
| 서로 다른 사용자의 강한 자원 격리 요구 | 지원 GPU에서 MIG |
| GPU 노드 장애 뒤에도 서비스 지속 | 남은 장치의 여유 용량과 배치 가능성 우선 검증 |

## 배치 성공과 모델 실행 성공 사이

스케줄러가 Pod를 Running 상태로 만들었다고 해서 모델 서버가 성공적으로 시작되는 것은 아니다. GPU Driver와 Runtime이 장치를 인식해야 하고, Device Plugin이 적절한 리소스를 광고해야 한다. Pod에 장치가 전달된 뒤에도 모델의 Weight, KV Cache와 실행 버퍼가 VRAM에 들어가야 한다.

이 과정에서 GPU Operator와 Node Feature Discovery의 라벨이 예상과 다르게 나타나던 문제도 있었다. 리소스가 등록되지 않은 문제를 Time-slicing으로 해결할 수는 없다. 장치 발견과 스케줄링 문제는 [GPU 리소스 조사 기록](/projects/rokaf-gpu-discovery-open-investigation/)에 따로 남겼다.

한 노드에만 Selector를 고정하면 특정 워크로드가 당장 실행될 수는 있다. 그러나 그것이 전체 GPU 자원 모델이 정상이라는 증거는 아니며, 장애가 발생했을 때 선택할 다른 노드를 줄일 수도 있다.

## GPU VRAM·간섭·지연시간 비교

Time-slicing을 적용했다면 나는 네 가지를 함께 보고 싶었다.

첫째는 **상주 메모리**다. 모델 파일 크기뿐 아니라 최대 실행 버퍼와 Cache가 얼마나 커지는지도 확인해야 한다.

둘째는 **연산과 메모리 대역폭의 경쟁**이다. 혼자 실행할 때와 다른 모델과 함께 실행할 때 서비스가 어떻게 달라지는지 비교해야 한다.

셋째는 **실제 요청의 지연시간과 오류**다. 평균 GPU 사용률보다는 p95·p99 지연시간, 초기화 실패, OOM이 더 중요할 수 있다.

넷째는 **장애 시 여유 용량**이다. GPU 노드 하나가 없어져도 남은 장치가 추가 모델을 올리고 요청을 감당할 수 있는지 확인해야 한다.

이것들은 검증에 사용할 기준이다. 실제 군 환경에서 세 정책을 통제된 조건으로 비교한 지연시간·처리량 수치가 남아 있는 것은 아니므로, 특정 방식이 몇 퍼센트 빠르다는 결과를 만들어 넣지는 않는다.

## GPU Failover 용량과 처리량

GPU 서비스의 Replica가 여러 개라면 하나가 중단돼도 접속 주소는 유지될 수 있다. 하지만 남은 Replica가 같은 요청량을 처리할 만큼 여유가 있는지는 또 다른 문제다.

예를 들어 장애 뒤 남은 GPU가 이미 VRAM 대부분을 사용하고 있다면 Pod를 추가 배치하는 것조차 불가능할 수 있다. Pod를 배치할 수 있어도 Queue가 길어지고 Tail Latency가 늘 수 있다. 이때는 과도한 요청을 거부할지, 더 느린 응답을 허용할지 서비스 수준에서 결정해야 한다.

실제로 적용한 것은 Time-slicing이며, MIG는 지원 하드웨어를 전제로 비교한 방식이다. 각 정책의 적합성을 판단하려면 혼합 워크로드의 최대 VRAM 사용량, 동시 실행 간섭, 지연시간과 노드 장애 후 남는 용량을 측정해야 한다. 그런 비교 벤치마크 수치가 이 기록에 포함돼 있지는 않다.

## 관련 자료

- [NVIDIA GPU Operator의 Time-slicing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
- [NVIDIA MIG 가이드](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/latest/introduction.html)
- [GPU 리소스 발견 조사](/projects/rokaf-gpu-discovery-open-investigation/)
- [DCGM Exporter와 메트릭 누락](/projects/rokaf-observability-and-failure-evidence/)
