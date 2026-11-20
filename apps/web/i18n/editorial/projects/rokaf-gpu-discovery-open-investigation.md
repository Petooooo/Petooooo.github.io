GPU 서버에 GPU Operator를 설치하던 중 로그에 `no nfd label found`라는 메시지가 나타났다. 장치는 분명 있는 서버였는데, Operator가 기대하는 노드 정보를 찾지 못하고 있었다. 설정을 다시 보니 `nfd.enabled=false`가 들어가 있었다.

처음에는 GPU가 Kubernetes에서 보이지 않는 문제를 하나로 생각하기 쉬웠다. 하지만 그 로그는 적어도 **Operator가 노드를 어떤 종류의 장비로 판단할 수 있는가**에 관한 문제였다. 모델 Pod가 GPU를 할당받을 수 있는지, 할당받은 GPU로 실제 추론을 수행할 수 있는지까지 한꺼번에 답해주지는 않았다.

한때는 GPU Operator만 올리면 드라이버부터 장치 인식, 스케줄링까지 하나의 기능처럼 이어질 거라 생각했다. 실제로는 여러 구성 요소가 각각 다른 값을 만들고 있었다. 무엇이 누락됐는지 알려면 'GPU가 없다'는 말 대신 그 값이 **어느 단계에서 사라졌는지**를 찾아야 했다.

## NFD 비활성화와 노드 라벨

당시 사용한 `nfd.enabled=false`는 GPU Operator가 자체적으로 Node Feature Discovery(NFD)를 배포하지 않도록 하는 설정이었다. 이미 클러스터에 NFD가 따로 설치돼 있다면 합리적인 선택일 수 있다. 반대로 별도의 NFD도 없거나 GPU 노드에 필요한 하드웨어 정보를 게시하지 않는다면 Operator가 기대하는 라벨을 찾지 못할 수 있다.

따라서 내가 확인해야 할 것은 단순히 Helm 값을 `true`로 바꾸는 일이 아니었다. **다른 곳에서 NFD를 운영하고 있는지, 실제 GPU 노드에서 탐지가 수행되고 있는지, 탐지된 라벨이 Node 객체에 반영됐는지**가 먼저였다. NFD Pod가 있다는 사실과 그 Pod가 해당 노드의 GPU 특성을 올바르게 기록했다는 사실도 다르다.

여기에서 이름이 비슷한 두 요소를 구분할 필요가 있었다. NFD는 PCI 장치 같은 노드 하드웨어의 특징을 발견하고, GPU Feature Discovery(GFD)는 GPU의 제품 정보와 특성 같은 추가 메타데이터를 제공한다. GPU Operator가 어떤 노드에 구성 요소를 배포할지 판단하는 데 필요한 라벨과, 관리자가 워크로드 배치에 사용하는 GPU 특성 라벨은 역할이 같지 않다.

`no nfd label found`는 이 탐지·선택 단계에 문제가 있을 수 있다는 **직접적인 단서**다. 그러나 당시 기록만으로 NFD 하나의 설정을 바꾸면 모든 GPU 노드의 문제가 해결됐다고 말할 수는 없다. 라벨이 비어 있던 원인과 이후 GPU 리소스가 실제로 어떻게 등록됐는지는 추가 검증이 필요했다.

## 장치가 보인다는 것과 요청 가능한 자원이라는 것

GPU를 Kubernetes에서 사용하기까지는 여러 곳을 통과한다. 호스트 운영체제와 NVIDIA 드라이버가 장치를 인식해야 하고, 컨테이너 런타임이 필요한 장치 인터페이스를 제공해야 한다. Node Label을 기록하는 탐지 구성 요소와 Kubernetes에 GPU 확장 리소스를 등록하는 Device Plugin도 구분해야 한다.

특히 중요하게 봐야 할 부분은 **Node Label과 `status.allocatable`의 차이**다. 라벨은 노드에 어떤 장치나 기능이 있는지 설명하는 메타데이터다. 반면 Device Plugin과 kubelet이 등록하는 `nvidia.com/gpu` 같은 확장 리소스는 스케줄러가 Pod의 GPU 요청을 계산할 때 사용하는 값이다.

라벨이 보인다고 자동으로 GPU가 할당 가능한 것은 아니다. 반대로 어떤 종류의 GPU 특성 라벨이 기대와 다르다고 해서 반드시 `nvidia.com/gpu` 수량도 0이라고 단정할 수는 없다. 두 값을 실제로 비교해야 한다.

당시 가장 필요한 점검은 아래처럼 서로 다른 질문을 분리하는 일이었다.

| 확인할 곳 | 질문 | 결과가 의미하는 범위 |
| --- | --- | --- |
| 호스트·드라이버 | 호스트에서 GPU가 인식되는가 | 장치와 드라이버 연결 |
| NFD·GFD | 기대한 Node Label이 있는가 | 하드웨어·GPU 메타데이터 |
| Device Plugin·kubelet | `nvidia.com/gpu`가 `allocatable`에 있는가 | 스케줄러가 계산할 확장 리소스 |
| Scheduler | 요청 수량과 Affinity·Taint 조건이 맞는가 | Pod를 배치할 수 있는가 |
| Pod·모델 프로세스 | 장치 초기화와 실제 모델 실행이 성공하는가 | 애플리케이션이 GPU를 사용할 수 있는가 |

이것은 **확인한 결과를 모두 체크한 표가 아니라**, 다음 검증에서 어느 경계의 증거가 필요한지 구분한 표다. 로그 하나에서 모든 단계의 결과를 추정하지 않으려는 목적이었다.

{{figure /figures/journals/gpu-discovery-investigation.svg | 실제 관측된 것은 NFD 라벨을 찾지 못한 상태다. GPU의 Allocatable 등록 여부와 Pod 배치·실행은 각각 다른 증거로 확인해야 한다. 그림은 실제 노드 구성이 아니라 조사 순서를 나타낸다.}}

## GPU Pod Pending 진단

라벨과 확장 리소스가 갖춰졌더라도 Pod가 반드시 GPU 노드에 배치되지는 않는다. Pod가 요청한 GPU 리소스 이름과 수량이 실제로 등록된 것과 일치해야 하고, `nodeSelector`와 `nodeAffinity`, Taint·Toleration, 나머지 CPU·메모리 조건까지 함께 만족해야 한다.

이럴 때 익숙한 GPU 노드 이름을 Selector에 박아 넣으면 한 워크로드를 일단 배치할 수는 있다. 그러나 그 방식이 다른 GPU 노드의 라벨 문제를 해결하거나, 장애 시 다른 노드에 옮길 수 있는 선택지를 늘려주는 것은 아니다. 운영 중에는 임시 우회인지 정상적인 배치 정책인지 구분할 필요가 있었다.

`kubectl describe pod`의 스케줄링 이벤트와 실제 Node의 `status.allocatable`을 먼저 비교하고, 그다음에야 GPU Operator나 드라이버로 시선을 돌리는 편이 합리적이었다. 아직 Pod가 배치되지 않았다면 모델 서버의 CUDA 초기화 오류를 찾을 수도 없다.

반대로 Pod가 Running이 됐다 해도 마지막 확인은 남는다. 장치가 컨테이너에 전달됐는지, CUDA와 프레임워크가 장치를 초기화하는지, 모델의 Weight·KV Cache·임시 버퍼를 VRAM에 올릴 수 있는지 따로 확인해야 한다. 배치 성공과 추론 성공은 같은 말이 아니었다.

## GPU 모니터링에서도 비슷한 착시가 있었다

이와 별개로 DCGM Exporter의 배치를 조사했던 경험도 있다. GPU가 없는 노드에 Exporter가 배치돼 `ContainerCreating`에서 더 진행하지 못했던 경우가 있었고, 다른 시점에는 특정 GPU 노드에만 고정돼 나머지 GPU 노드에서 메트릭을 받지 못했다. 그 노드의 Exporter 주소로 직접 요청했을 때 연결이 거부되기도 했다.

여기에서 Exporter가 실행 중이라는 사실은 GPU 리소스가 Kubernetes에 정상 등록됐다는 증거가 아니다. 반대로 DCGM 메트릭이 보이지 않는다고 GPU 장치 자체가 사라졌다는 뜻도 아니다. 모니터링 Pod의 배치와 Device Plugin의 등록, 모델 Pod의 실행은 연결돼 있지만 다른 일이다.

이 문제를 겪으면서 노드 이름 하나에 의존하는 배치보다, 검증된 GPU 역할 라벨과 실제 장치 존재 여부를 기준으로 Exporter 범위를 정하는 편이 낫겠다고 생각했다. 이 또한 모든 노드를 대상으로 한 최종 배포 검증을 마쳤다는 뜻은 아니다. 구체적인 관측은 [Prometheus와 DCGM Exporter 기록](/projects/rokaf-observability-and-failure-evidence/)에 따로 정리했다.

## Time-slicing을 바꿀 시점은 더 뒤에 있었다

한편 GPU를 여러 모델이 공유하도록 Time-slicing을 구성하고, MIG를 대안으로 검토한 작업도 있었다. 하지만 Time-slicing의 논리적인 GPU 슬롯 수를 늘린다고, 등록되지 않은 GPU가 자동으로 발견되지는 않는다. MIG도 지원 하드웨어에서 자원을 분할하는 정책이지 NFD 라벨 오류를 고치는 방법은 아니다.

이 둘을 섞으면 증상을 더 복잡하게 만들 수 있다. 스케줄러에 GPU가 보이기 전에는 탐지와 등록을 확인해야 한다. 스케줄러가 배치한 다음에는 모델이 VRAM과 응답시간 요구를 만족하는지 평가해야 한다. 논리 슬롯 수가 늘어도 물리 VRAM이 늘어나지는 않기 때문이다.

따라서 이 글에서 다루는 것은 **GPU를 발견하고 할당하는 경계**다. 실제 Time-slicing과 MIG의 차이, 메모리 경쟁과 가용 용량에 대해서는 [GPU 공유·용량 설계 기록](/projects/rokaf-gpu-scheduling-and-capacity/)에서 따로 다뤘다.

## 노드 라벨과 GPU 할당 추가 검증

다시 같은 오류를 본다면 먼저 설치된 GPU Operator 설정과 별도 NFD 유무, 해당 GPU 노드의 라벨을 같은 시점에 기록할 것이다. 이어 Device Plugin 상태와 Node의 `capacity`·`allocatable`을 비교하고, 최소한의 GPU 요청을 가진 테스트 Pod를 배치해 실제 초기화 결과까지 확인할 것이다.

GPU Operator에서 `no nfd label found`를 확인했고, 당시 설정에는 `nfd.enabled=false`가 있었다. GPU 할당과 DCGM Exporter 배치도 함께 다뤘지만, NFD 라벨 오류의 복구 여부를 최종 검증할 로그는 남아 있지 않다. 같은 문제가 재발하면 Node Label, Device Plugin, `status.allocatable`, 실제 GPU Pod 초기화 결과를 한 시점에 모아 비교할 것이다.

## 관련 자료

- [NVIDIA GPU Operator 설치와 NFD 설정](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)
- [NVIDIA GPU Operator 문제 해결](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/troubleshooting.html)
- [GPU Time-slicing과 MIG의 차이](/projects/rokaf-gpu-scheduling-and-capacity/)
- [DCGM Exporter 배치·관측 문제](/projects/rokaf-observability-and-failure-evidence/)
