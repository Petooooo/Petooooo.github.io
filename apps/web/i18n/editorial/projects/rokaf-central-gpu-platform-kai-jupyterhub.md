온프레미스 GPU 서버를 여러 대 운영하다 보면 장비가 있다는 사실만으로는 충분하지 않다. 한쪽에서는 GPU가 남아 있는데 다른 쪽에서는 모델을 실행할 자원이 없다고 느낄 수 있다. 서비스마다 어느 서버에 배치할지 따로 관리하고, 사용자가 직접 실행 환경을 준비해야 한다면 클러스터가 있어도 자원은 흩어져 있는 셈이었다.

내가 구축하려던 것은 **GPU를 중앙에서 관리하고 필요한 곳에 제공하는 공용 연산 환경**이었다. 폐쇄망에 K3s 기반 GPU 클러스터를 구성해 운영했고, 여기에 **KAI Scheduler를 직접 반입·배포해 운영**했다. 사용자가 GPU 환경에 접근하는 경로로는 **JupyterHub를 구축해 실제 서비스로 운영**했다. GPU를 더 많이 보이게 만드는 설정을 넘어서, 여러 사용자의 작업을 하나의 플랫폼에서 다룰 수 있도록 만든 경험이었다.

## GPU를 개별 서버가 아닌 공용 자원으로 관리하기

사용자 입장에서 GPU가 필요할 때마다 특정 서버를 찾아 접속하고 실행 환경을 맞추는 방식은 오래 유지하기 어렵다. 새로운 작업이 생길 때마다 장비 배치를 다시 고민해야 하고, 어떤 사용자가 어느 서버의 자원을 얼마나 쓰고 있는지도 전체적으로 보기 힘들어진다.

K3s는 여러 서버를 하나의 Kubernetes 클러스터로 관리하는 기반이었다. GPU Operator와 Device Plugin을 통해 장치가 Kubernetes 리소스로 노출되면, 워크로드는 특정 GPU 서버를 직접 지정하는 대신 필요한 자원을 요청할 수 있다.

하지만 **GPU를 Kubernetes에 등록하는 일**과 **여러 작업에 GPU를 어떻게 배분할지 결정하는 일**은 다르다. 여기에 실험·개발을 위한 사용자 접속 환경까지 생각하면 또 다른 역할이 필요하다. 내가 KAI Scheduler와 JupyterHub를 도입한 이유도 그 역할을 분리하기 위해서였다.

{{figure /figures/journals/central-gpu-kai-jupyterhub.svg | JupyterHub는 사용자의 Notebook 세션을 제공하고, KAI Scheduler는 자신에게 지정된 AI 작업의 배치를 담당한다. 두 경로 모두 Kubernetes가 관리하는 GPU 자원 풀을 사용한다. 실제 서버 배치나 내부 네트워크 구성을 나타낸 그림은 아니다.}}

## KAI Scheduler 반입과 GPU 작업 배치

폐쇄망에서는 공개 인터넷에 있는 Helm Chart나 컨테이너 이미지를 그대로 가져다 실행할 수 없다. 필요한 소프트웨어와 이미지 의존성을 내부로 들여오고, 클러스터에서 실행할 수 있는 형태로 준비해야 한다. **KAI Scheduler도 이런 과정을 거쳐 실제 K3s 환경에 반입하고 배포해 운영했다.**

일반적인 Kubernetes Scheduler는 Pod가 요구한 리소스와 노드 조건을 바탕으로 배치를 결정한다. GPU 환경에서는 여기에 작업 우선순위와 대기열, 여러 작업이 공유하는 자원, 함께 실행해야 하는 작업 같은 조건이 중요해진다. KAI Scheduler는 이런 AI 워크로드의 배치를 관리하기 위해 도입한 별도 스케줄러다.

여기서 GPU Operator나 Device Plugin의 역할이 사라지는 것은 아니다. Device Plugin은 Kubernetes가 사용할 수 있는 GPU 리소스를 등록하고, Scheduler는 **어느 작업을 어느 자원에 배치할지** 판단한다. 실행된 Pod가 GPU를 정상적으로 사용하는지는 또 다른 단계다.

KAI가 지원하는 Queue, 공정 배분, 우선순위, Gang Scheduling 같은 기능도 이런 관점에서 살펴볼 수 있다. 다만 제품이 지원하는 기능과 내 클러스터에서 실제 적용한 정책은 구분해야 한다. 모든 Queue 정책이나 분산 학습의 Gang Scheduling을 운영 검증했다고 주장하기보다, **KAI를 도입해 중앙 GPU 스케줄링 체계를 실제로 운영한 작업**을 이 글의 중심에 두었다.

별도 스케줄러를 설치했다고 모든 Pod가 자동으로 그 스케줄러를 사용하는 것도 아니다. KAI로 배치하려는 워크로드는 그에 맞는 Scheduler와 Queue 설정을 사용해야 한다. Pending 상태의 GPU Pod를 볼 때도 Device Plugin의 리소스 등록, GPU 요청량, 선택된 Scheduler, Queue 상태를 각각 확인해야 한다.

## JupyterHub로 제공한 GPU 개발 환경

GPU를 배치하는 체계가 있어도 사용자가 이를 쉽게 활용할 수 있어야 한다. 모델을 실험하거나 데이터를 살펴보는 작업에는 터미널만 열어주는 것보다 Notebook 형태의 실행 환경이 편리할 때가 많다.

그래서 **JupyterHub를 구축해 운영했다.** 사용자는 JupyterHub를 통해 자신의 Notebook 실행 환경에 접근하고, 플랫폼은 그 세션을 Kubernetes 워크로드로 관리할 수 있다. 사용자마다 GPU 서버에 직접 접속해 실행 환경을 설치하도록 하는 대신, 공용 플랫폼이 Notebook 서비스를 제공하는 구조였다.

JupyterHub의 로그인 화면이 열린다고 Notebook 환경이 준비된 것은 아니다. 실제 사용자의 서버 Pod가 생성되고, 필요한 이미지와 CPU·메모리·GPU 리소스를 확보하고, 세션에 연결되어야 한다. Notebook 기동 오류가 생기면 JupyterHub의 사용자 세션과 Pod 상태, 이미지 Pull, GPU 리소스 할당을 나누어 확인해야 한다.

JupyterHub와 KAI Scheduler는 같은 시스템의 다른 역할이다. **JupyterHub는 사용자의 연산 환경을 제공하고, KAI는 자신에게 전달된 AI 작업의 배치를 결정한다.** 이 둘을 함께 운영하면서 GPU 자원을 중앙에서 제공하는 플랫폼을 구성했다.

JupyterHub의 모든 Single-user Pod를 KAI가 직접 배치했는지는 별도의 Pod 설정을 확인해야 하는 항목이다. KubeSpawner에서 Scheduler를 명시적으로 지정할 수 있지만, 그 가능성만으로 실제 모든 Notebook에 동일한 정책이 적용됐다고 적지는 않았다.

## Time-slicing과 중앙 스케줄링은 다른 계층이다

GPU 공유를 구성할 때 Time-slicing도 적용했다. 하나의 물리 GPU를 여러 워크로드가 사용할 수 있도록 논리적인 GPU 슬롯을 노출하는 방식이다. 작은 작업이 많은 환경에서는 GPU가 비어 있는 시간을 줄이는 데 도움이 될 수 있다.

그렇지만 논리 슬롯이 늘어난다고 실제 VRAM이 증가하는 것은 아니다. 같은 GPU를 사용하는 여러 프로세스가 메모리와 연산 자원을 두고 경쟁할 수 있고, Kubernetes가 Pod를 배치하는 데 성공해도 모델의 Weight와 실행 버퍼가 VRAM에 들어가지 않으면 실행할 수 없다.

따라서 세 가지를 구분해서 운영해야 했다.

| 구성 요소 | 담당하는 역할 |
| --- | --- |
| GPU Operator·Device Plugin | GPU를 Kubernetes에서 인식하고 할당 가능한 리소스로 제공 |
| KAI Scheduler | 지정된 AI 작업의 배치와 스케줄링 정책 관리 |
| JupyterHub | 사용자의 Notebook 실행 환경과 세션 제공 |
| Time-slicing | 하나의 물리 GPU를 여러 워크로드가 공유하는 할당 방식 |
| K3s 플랫폼 | 컨테이너 실행, 네트워크, 저장소와 공통 운영 환경 관리 |

GPU 전체 할당, Time-slicing, MIG의 차이와 메모리 경합 문제는 [GPU 공유 방식에 관한 별도 글](/projects/rokaf-gpu-scheduling-and-capacity/)에 자세히 정리했다. 이번 작업에서 중요한 것은 어느 한 공유 기술의 성능 비교가 아니라, **사용자와 워크로드가 GPU 자원에 접근하는 경로를 중앙에 모아 운영하게 됐다는 점**이었다.

## 폐쇄망에서 실제로 운영한다는 것

새 컴포넌트를 클러스터에 설치한 뒤 Running 상태가 됐다고 해서 GPU 플랫폼 운영이 끝나는 것은 아니다. 사용자가 Notebook을 시작할 수 있는지, 필요한 컨테이너 이미지가 내부에서 제공되는지, 작업이 요청한 GPU 자원이 Kubernetes에 등록되어 있는지 확인해야 한다.

특히 외부 인터넷 접근이 제한된 환경에서는 이미지 Pull에 실패한 Pod와 GPU 리소스를 확보하지 못한 Pod가 사용자에게 비슷한 기동 실패로 보일 수 있다. 같은 Pending 상태라도 Scheduler가 배치를 보류한 것인지, Pod는 배치됐지만 이미지와 실행 환경을 준비하지 못한 것인지 구분해야 한다.

운영할 때 구분한 지점은 다음과 같다.

| 사용자에게 보이는 상황 | 우선 확인할 계층 |
| --- | --- |
| Notebook 서버가 시작되지 않음 | JupyterHub 세션, 생성된 Pod, 이미지·스토리지·네트워크 |
| GPU를 요청한 Pod가 Pending | 리소스 요청량, Node Allocatable, Scheduler·Queue 상태 |
| Pod는 Running인데 CUDA 사용 실패 | GPU Device Plugin, 컨테이너 런타임, 장치 접근 |
| GPU 슬롯은 남았는데 모델 실행 실패 | 실제 VRAM 점유, 모델 크기와 실행 버퍼 |
| 일부 워크로드만 느려짐 | 공유 GPU의 자원 경합, 애플리케이션의 요청 특성 |

이것은 특정 날짜의 장애를 모두 해결했다는 목록이 아니라, 운영 중 다른 계층에서 발생할 수 있는 문제를 어떻게 나누어 보는지에 관한 기준이다. 여러 사용자가 하나의 자원 풀을 쓰게 되면서, GPU 개수만 보는 것보다 **실제로 작업이 시작되고 필요한 연산을 마치는가**를 확인하는 일이 중요해졌다.

## 구축과 운영 결과

이번 작업에서 직접 수행한 범위는 분명하다.

- **온프레미스 K3s 기반 GPU 클러스터를 구축하고 운영했다.**
- **KAI Scheduler를 폐쇄망에 반입해 배포하고 운영했다.**
- **JupyterHub를 구축하고 사용자용 Notebook 환경으로 운영했다.**
- **GPU Time-slicing을 구성**하고, 전체 GPU 할당 및 MIG와의 차이를 검토했다.
- GPU 장치 등록과 워크로드 배치, 사용자 환경, 이미지·네트워크 등 **공용 GPU 플랫폼에 필요한 운영 계층을 관리했다.**

이 경험의 중심 성과는 KAI Scheduler나 JupyterHub라는 제품을 각각 설치했다는 사실보다, **흩어져 있던 GPU 연산 자원을 중앙에서 관리하고 여러 사용자의 AI 작업에 제공하는 체계를 구축해 운영했다는 것**이다.

실제 Queue별 공정성 수치나 GPU 사용률 개선율, JupyterHub의 세부 리소스 프로필은 확인되지 않은 숫자와 설정을 만들어서 채우지 않았다. 그와 관계없이 중앙 GPU 플랫폼, KAI Scheduler, JupyterHub의 구축·운영 경험은 완료된 작업이다.

## 관련 기록과 참고 자료

- [Kubernetes GPU 공유: Time-slicing·MIG](/projects/rokaf-gpu-scheduling-and-capacity/)
- [GPU Operator·NFD 리소스 인식 조사](/projects/rokaf-gpu-discovery-open-investigation/)
- [온프레미스 K3s 플랫폼 구축과 운영](/projects/independent-on-premises-k3s-platform-engineering/)
- [폐쇄망 이미지 배포와 CI](/projects/rokaf-private-artifacts-and-ci/)
- [KAI Scheduler 공식 저장소](https://github.com/kai-scheduler/KAI-Scheduler)
- [KAI Scheduler Quickstart](https://github.com/kai-scheduler/KAI-Scheduler/blob/main/docs/quickstart/README.md)
- [Zero to JupyterHub: 사용자별 리소스 구성](https://z2jh.jupyter.org/en/latest/jupyterhub/customizing/user-resources.html)
