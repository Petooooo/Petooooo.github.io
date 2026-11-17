GPU가 장착된 서버인데 Kubernetes에서는 예상한 GPU 리소스가 보이지 않았다. 처음에는 GPU Operator를 설치했으니 자동으로 해결될 문제라고 생각하기 쉬웠다. 하지만 조사하면서 **장치가 실제로 존재한다는 사실과 스케줄러가 그 장치를 자원으로 인식한다는 사실은 다르다**는 점을 확인했다.

당시 GPU Operator와 Node Feature Discovery에서 기대한 라벨이 보이지 않는 문제가 있었다. 어떤 설정에서는 NFD가 비활성화돼 있었고, Operator가 관련 라벨을 찾지 못한다는 로그도 확인했다. 그렇다고 모든 GPU 배치 실패를 단순히 NFD 하나의 문제로 결론 낼 수는 없었다.

## GPU가 Kubernetes에 보이기까지

먼저 호스트 운영체제가 GPU를 인식하고 드라이버가 장치와 통신할 수 있어야 한다. 컨테이너 런타임이 장치에 접근할 수 있는지도 별도의 조건이다.

그다음 GPU Operator와 관련 컴포넌트가 노드의 특성을 파악하고 라벨을 붙인다. Device Plugin은 Kubernetes에 사용 가능한 GPU 확장 리소스를 등록한다. 스케줄러는 그 리소스 요청과 Node Selector, Affinity, Taint·Toleration 조건을 함께 고려해 Pod를 배치한다.

마지막으로 실제 모델 프로세스가 GPU 초기화에 성공하고 VRAM 안에 들어가야 한다.

{{figure /figures/journals/gpu-discovery-investigation.svg | 물리 장치 인식부터 Node Feature Discovery, Device Plugin의 리소스 등록, 스케줄러의 배치까지 서로 다른 검증 단계가 있다. 실제 클러스터 구성도는 아니다.}}

여기에서 혼동하기 쉬운 것이 **Node Label과 Allocatable 리소스**다. 라벨은 노드의 특성을 설명하는 메타데이터이고, Allocatable은 스케줄러가 실제 할당 가능한 자원으로 계산하는 값이다. 라벨이 없다고 언제나 GPU 리소스도 없는 것은 아니며, 라벨이 있다고 모델을 실행할 수 있는 것도 아니다.

## Pod 하나만 보고 판단하지 않았다

GPU Operator Pod가 Running이라고 해서 드라이버, NFD, Device Plugin이 모두 정상일 필요는 없다. Device Plugin이 실행 중이어도 모든 GPU 노드에 리소스가 예상대로 등록됐는지 따로 확인해야 한다.

반대로 모델 Pod가 Pending이라면 Driver가 고장 났다고 바로 판단할 수도 없다. GPU 자원이 정상적으로 광고됐더라도 해당 Pod의 Node Selector나 Taint 조건이 맞지 않을 수 있다.

나는 이 문제를 조사할 때 다음 증거를 분리하고 싶었다.

| 단계 | 확인할 내용 |
| --- | --- |
| 호스트 | GPU와 드라이버가 인식되는가 |
| 컨테이너 런타임 | 컨테이너에서 장치 인터페이스에 접근하는가 |
| NFD·Operator | 기대한 Node Label이 등록됐는가 |
| Device Plugin | GPU 확장 리소스가 Allocatable에 표시되는가 |
| Scheduler | Pod 요청과 Node Selector·Affinity 조건이 일치하는가 |
| 애플리케이션 | 모델이 VRAM에 올라가고 실제 추론을 수행하는가 |

이 표는 원인을 확정한 결과가 아니라 가설을 하나씩 반증하기 위한 점검 순서다. 어느 단계에서 값이 달라지는지 확인해야 그다음 조치를 좁힐 수 있다.

## 잠깐 동작하게 만드는 것과 정상화하는 것은 다르다

한 GPU 노드에만 Selector를 고정하면 일단 모델이 실행될 수 있다. 하지만 다른 GPU 노드가 왜 선택되지 않았는지 알 수 없는 상태라면 해결되지 않은 문제가 남는다.

Time-slicing은 스케줄러에 더 많은 논리 GPU 슬롯을 제공할 수 있지만, 장치가 애초에 등록되지 않은 문제를 해결하지는 않는다. MIG도 지원 GPU에서 자원을 분할하는 정책일 뿐 NFD나 Device Plugin의 등록 실패를 대신 고쳐주지 않는다.

따라서 GPU 스케줄링의 임시 우회와, **노드 특성과 실제 가용 자원이 일치하도록 만드는 근본 수정**을 구분해야 했다. 임시 우회는 가용한 대체 노드 수를 줄일 수도 있기 때문이다.

## 아직 확인하지 못한 부분

기록으로 확인되는 것은 예상한 GPU 라벨 또는 Feature가 나타나지 않았던 현상과 그에 대한 조사다. 하지만 모든 노드의 실패 원인을 한 가지로 확정하거나 GPU 공유 설정 전체를 최종 배포·검증했다는 자료는 없다. 특정 변경으로 처리량이 얼마나 개선됐다는 벤치마크도 남아 있지 않다.

다시 같은 문제를 만난다면 호스트 장치 인식, Operator와 Device Plugin, Node Label, Allocatable, Pod 배치 결과를 같은 시점에서 수집하고 싶다. 그런 다음 최소한의 GPU 워크로드를 실행해 실제 장치 초기화와 메모리 사용까지 확인할 것이다.

GPU가 있다는 사실은 시작점일 뿐이다. **그 장치를 Kubernetes가 올바른 자원으로 표현하고, 애플리케이션이 실제로 사용할 수 있어야** 운영 가능한 GPU 플랫폼이라고 말할 수 있다.

## 관련 기록

- [GPU Time-slicing과 MIG 비교](/projects/rokaf-gpu-scheduling-and-capacity/)
- [DCGM Exporter의 배치·관측 문제](/projects/rokaf-observability-and-failure-evidence/)
- [K3s 플랫폼 전체 기록](/projects/independent-on-premises-k3s-platform-engineering/)
