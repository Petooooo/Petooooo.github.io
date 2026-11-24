> **2026년 11월 · 비식별화된 운영 기록.** 노드당 기본 Pod 제한에 가까워지면서 추가 Pod가 계속 Pending 상태에 머무는 문제를 경험했다. kubelet의 제한을 110개에서 220개로 높여 당장의 문제를 해결했다. 아래 주소 대역은 설계 설명에 사용한 K3s 공개 기본값이며, 실제 운영망의 주소 목록이 아니다.

## CPU 코어나 메모리로 표현되지 않는 자원

폐쇄망 K3s 플랫폼을 운영하던 중, 한 노드의 Pod 수가 약 103개에 이르자 추가 Pod가 계속 Pending 상태로 남는 문제가 생겼다. 일반적으로는 CPU나 메모리 requests부터 살펴보게 되지만, 이번에는 노드에 올라갈 수 있는 Pod의 개수 자체가 제약으로 작용하고 있다는 점에 주목했다.

물론 103개라는 수치만으로 원인을 확정할 수는 없다. 제한이 110개라면 명목상 7개의 슬롯이 남아 있기 때문이다. 관측한 개수에 생성 중이거나 종료 중인 Pod가 포함되지 않았을 수도 있고, 여러 워크로드가 남은 슬롯을 두고 경쟁했거나 affinity, taint, 자원 requests로 인해 다른 노드에 배치할 수 없었을 수도 있다. 당시의 스케줄러 이벤트와 자원 상태를 함께 보존한 기록은 없다. 다만 실제로 `maxPods`를 220으로 높인 이후 겪고 있던 Pending 문제는 해결됐다.

이번 작업에서 중요했던 것은 YAML 한 줄을 추가하는 방법보다, 어떤 제약을 완화하고 다른 제약은 어떻게 유지할 것인지에 대한 판단이었다.

## 스케줄링과 IP 할당은 서로 다른 단계다

{{figure /figures/journals/pod-density-01-admission.svg | 스케줄링에 성공했다고 해서 Pod 샌드박스를 반드시 생성할 수 있는 것은 아니다.}}

kubelet은 노드가 수용할 수 있는 Pod 수를 Node 오브젝트에 보고한다. 스케줄러는 이 슬롯과 함께 CPU, 메모리, 확장 자원, 배치 정책을 고려한다. `maxPods`는 컨테이너 수가 아니라 Pod 수를 제한한다. `podsPerCore`를 양수로 설정했다면 CPU 코어 수와 그 값을 곱한 상한도 함께 적용된다. 0이면 이 추가 제약을 사용하지 않는다. 따라서 설정 파일에 적힌 숫자보다 실제 Node의 allocatable Pod 수를 확인하는 것이 중요하다. 개수 제한에 걸리면 `Too many pods`라는 스케줄링 이벤트가 발생할 수 있다. 반면 노드에 배치된 이후에도 kubelet과 컨테이너 런타임은 샌드박스를 생성해야 한다. 일반적인 Flannel과 host-local IPAM 구성에서는 이 과정에서 노드 서브넷으로부터 Pod IP를 할당한다. 여기서 주소가 부족하면 배치 이후 `FailedCreatePodSandBox`가 발생할 수 있다.

`maxPods`를 높인다고 노드의 IP 공간이 넓어지거나 메모리가 늘어나지는 않는다. 반대로 CIDR을 넓게 잡는다고 스케줄러가 허용하는 Pod 개수가 자동으로 늘어나는 것도 아니다.

같은 문제가 다시 발생한다면 설정을 변경하기 전에 다음 정보를 확보하려 한다.

```bash
kubectl get nodes -o custom-columns='NODE:.metadata.name,PODS:.status.allocatable.pods,CIDR:.spec.podCIDR'
kubectl describe node <node>
kubectl describe pod <pending-pod> -n <namespace>
kubectl get events -A --field-selector reason=FailedScheduling
kubectl get events -A --field-selector reason=FailedCreatePodSandBox
```

노드의 `Non-terminated Pods`, Pending Pod에 노드가 이미 할당됐는지 여부, 관련 이벤트, 실제 IPAM 할당 범위를 함께 확인하면 실패 지점을 좁힐 수 있다. 위 명령은 재발 시 증거를 확보하기 위한 절차이지, 당시 보존한 로그가 아니다.

## 왜 220개로 결정했는가

kubelet drop-in 설정을 작성하여 다음 값을 적용했다.

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
maxPods: 220
```

K3s는 v1.32 계열부터 kubelet drop-in 설정을 지원한다. 구체적인 지원 여부는 K3s 패치 버전에 따라 확인해야 한다. 공식 문서의 기본 경로는 `<data-dir>/agent/etc/kubelet.conf.d/`이다. 실제 환경에서는 설치 구성에 맞는 로컬 경로를 사용했으므로, 다른 환경에 재현할 때는 이름이 비슷한 디렉터리를 그대로 사용하는 대신 유효한 `--config-dir`과 우선 적용되는 CLI 인자가 있는지 확인해야 한다. Node의 상태를 직접 수정하는 방식이 아니라 각 노드의 kubelet 설정으로 관리한다. 다시 적용한다면 먼저 `k3s`와 `k3s-agent` 중 해당 노드의 서비스가 무엇인지, 실제로 읽는 설정 경로와 CLI 인자의 우선순위가 어떤지 확인할 것이다. Drop-in을 지원하지 않는 버전이라면 K3s의 `kubelet-arg`에 `max-pods=220`을 전달하는 방법도 있다. 노드 한 대에서 변경을 검증하고, quorum과 스토리지·워크로드 제약을 점검한 뒤 계획된 재시작을 수행한다. Ready 상태와 실제 allocatable 수를 확인한 후 다음 노드로 넘어가는 것이 좋다. 이는 재현을 위한 절차이며 당시 전 노드에 동일하게 적용했다는 기록은 아니다.

```bash
kubectl get node <node> -o jsonpath='{.status.capacity.pods}{"\n"}{.status.allocatable.pods}{"\n"}'
kubectl get --raw /api/v1/nodes/<node>/proxy/configz
```

두 번째 명령은 API 서버를 통한 kubelet 설정 조회 권한이 있는 경우에만 사용할 수 있다. 조회 결과에는 운영 설정이 포함될 수 있으므로 그대로 공개하는 용도로 사용하지 않는다.

{{figure /figures/journals/pod-density-02-budget.svg | 보고된 약 103개를 기준으로 계산한 수용량 비교. 변경 이후 실제 사용률이나 성능 측정값은 아니다.}}

| 항목 | 변경 전 | 변경 후 |
| --- | ---: | ---: |
| Pod 제한 | 110 | 220 |
| 비교 기준 Pod 수 | 103 | 103 |
| 남은 명목 슬롯 | 7 | 117 |
| 비교 기준 사용률 | 93.6% | 46.8% |

두 배 늘어난 것은 설정상 수용량이지, 실제 처리량이 아니다. Kubernetes v1.32의 대규모 클러스터 가이드에서도 노드당 110개를 확장성 기준으로 제시한다. 설정값을 그보다 크게 지정할 수 있다는 사실이 해당 밀집도에서 운영 안정성까지 검증됐다는 뜻은 아니다. 220개는 항상 채워야 하는 목표치가 아니라 배치 가능한 상한으로 판단했다.

## IP 주소에도 별도의 예산이 있다

K3s의 기본 IPv4 구성처럼 클러스터 Pod CIDR이 `/16`, 노드 CIDR이 `/24`라고 가정하면 노드 하나에 256개의 주소가 할당된다. 네트워크, 브로드캐스트, 게이트웨이 주소를 제외하는 일반적인 브리지/IPAM 예시에서는 약 253개가 Pod에 사용 가능하다. 실제 할당 범위는 CNI 구성에서 확인해야 하며, hostNetwork Pod는 스케줄링 슬롯을 사용하지만 일반적으로 이 풀에서 별도의 주소를 할당받지 않는다.

| maxPods | 최대 배치 시 예시 IP 여유 |
| ---: | ---: |
| 200 | 53개 |
| 220 | 33개 |
| 240 | 13개 |
| 250 | 3개 |

IP를 남긴다고 네트워크 성능이 좋아지는 것은 아니다. 남겨둔 주소는 스케줄러가 계산하는 Pod 수와 CNI가 실제로 관리하는 할당 수 사이의 차이에 대응한다. 스케줄러 입장에서는 Pod가 삭제됐더라도 샌드박스의 네트워크 정리가 끝나지 않았을 수 있다. CNI 삭제 요청이 실패해 로컬에 할당 기록이 남는 경우도 있다. 주소 공간이 거의 가득 찬 상황에서는 이 정도의 불일치만으로도 배치에는 성공했지만 샌드박스 생성에는 계속 실패할 수 있다. 물론 IP 누수가 지속된다면 CIDR을 크게 만드는 것이 아니라 원인을 해결해야 한다.

33개를 남겨야 한다는 규칙이 있는 것은 아니다. 선택한 상한과 예시 주소 공간의 차이일 뿐이다. 주소를 할당하지 않았다고 그 주소만큼의 Pod 처리 비용이 발생하는 것은 아니지만, 그만큼 주소 공간을 여유분으로 확보하게 된다. 실제 여유 IP 수는 IP를 사용하는 샌드박스 수, hostNetwork Pod, 남아 있는 할당 기록에 따라 달라진다. 두 제한을 정확히 같은 값에 맞추기보다 분리해 두는 쪽을 택했다.

## 밀집도가 높아지면 장애 복구의 조건도 바뀐다

서버에 충분한 메모리가 남아 있더라도 Pod 수가 많아지면 kubelet과 런타임의 상태 관리, Probe, PID와 파일 디스크립터, 네트워크 인터페이스, 연결 추적, 모니터링 대상 등이 증가할 수 있다. 실제 부하는 컨테이너와 트래픽 특성에 따라 달라지며, 제한값을 두 배로 높였다고 이러한 부하까지 즉시 두 배가 되는 것은 아니다.

더 중요하게 본 것은 노드 하나가 장애를 일으켰을 때 다른 노드가 그 워크로드를 수용할 수 있는지였다. 가령 동일한 노드 4대에 각각 180개의 Pod가 있고 상한이 220개라면, 한 노드가 사라졌을 때 남은 세 노드에는 총 120개의 슬롯만 남는다. 기존 180개를 모두 받아들이기에는 부족하다. 이는 Pod 슬롯만 고려한 가상의 계산이다.

{{figure /figures/journals/pod-density-04-recovery.svg | 동일한 노드 4대를 가정한 N-1 복구 용량 계산. 한 노드에서 이동해야 할 Pod 180개에 비해 나머지 슬롯이 120개뿐이어서 60개가 부족하다. 실제 운영망이나 복구 시험 결과가 아니다.}}

노드가 N대이고 각 노드의 상한이 C라면, 모든 워크로드를 자유롭게 재배치할 수 있다는 가정에서 노드 한 대의 장애를 감당하려면 전체 수요가 (N − 1) × C 이하여야 한다. 4대에 각각 220개라면 총 660개, 균등 배치 시 노드당 165개가 슬롯만 고려한 상한이다. 예시의 720개는 장애 이후 60개를 수용하지 못한다. 실제로는 생존 노드에서 실행해야 하는 시스템 Pod도 이 예산 안에 들어가고, 특정 GPU나 디스크에 종속된 워크로드는 옮길 수 있는 용량을 더 줄인다. 실제 복구에서는 자원 requests, affinity, GPU, 로컬 스토리지, 자발적 중단 시 PDB, 볼륨 재연결 등의 조건이 추가된다.

노드별 `maxPods`를 통일하면 설정 관리는 단순해질 수 있지만, 워크로드 배치 정책까지 동일해져야 하는 것은 아니다. 일반 연산, GPU, 스토리지 노드의 역할은 requests, label, affinity, taint, topology spread 등을 사용해 구분하는 것이 적절하다. Pod 개수 제한으로 자원 격리까지 대신하려 하기보다는, 실제 Pod 점유율과 IP 할당 상태, kubelet 처리 지연, conntrack, 메모리·디스크 압박, 워크로드 교체가 많은 상황의 복구 여유를 각각 살펴보는 것이 좋다.

## 이번에는 CIDR까지 변경하지 않았다

{{figure /figures/journals/pod-density-03-cidr.svg | 주소 할당 구조의 예시이며 실제 운영망의 토폴로지가 아니다.}}

| 고정된 /16 내 노드 CIDR | 노드당 전체 주소 | 이론상 노드 블록 수 |
| --- | ---: | ---: |
| /24 | 256 | 256 |
| /23 | 512 | 128 |
| /22 | 1,024 | 64 |

소수의 고사양 물리 서버로 구성된 환경이라면 초기 설계에서 노드 CIDR을 크게 잡는 것도 합리적이다. CIDR 크기 자체가 네트워크 성능을 떨어뜨리지는 않는다. 대신 할당 가능한 노드 블록 수가 감소하며, 예약한 주소 공간이나 다른 네트워크와의 중복 여부를 검토해야 한다. 클러스터 CIDR 자체를 넓히는 것은 별도의 문제다. 표의 주소 개수는 IPv4 서브넷의 이론적인 크기이지 실제 CNI가 보장하는 할당량은 아니다. 예를 들어 K3s의 공개 기본값인 `10.42.0.0/16`을 `/15`로 넓히면 기본 Service CIDR `10.43.0.0/16`과 겹친다.

이미 운영 중인 클러스터에서는 `node-cidr-mask-size-ipv4=22`를 설정하는 것만으로 기존 노드의 CIDR이 확장되지 않는다. Node에 기록된 PodCIDR, CNI 할당 정보, 라우팅, 실행 중인 샌드박스가 이미 기존 대역에 연결돼 있다. 기존 `/24`와 신규 `/22`는 같은 주소 범위를 포함할 수 있으므로 노드를 순서대로 삭제하고 재등록하면 충돌이 없을 것이라고 단정해서는 안 된다.

실제로 더 넓은 노드 CIDR이 필요해진다면 동일한 K3s 및 CNI 버전에서 계획된 교체 또는 유지보수 마이그레이션을 먼저 검증할 생각이다. 기존 주소 공간과 중복 여부를 확인하고, 제어면 데이터와 애플리케이션 데이터를 별도로 백업하며, 스토리지와 quorum 조건을 검토한 뒤 중복 없는 주소 배치를 준비해야 한다. 검증된 계획에 따라 노드를 재구성하거나 이전한 뒤에는 DNS, 노드 간 Pod 통신, Service 접근, Stateful 서비스 복구를 확인하고 나서 Pod 제한을 추가로 높이는 것이 적절하다. 이번 문제 해결 과정에서 실제 CIDR 마이그레이션을 수행한 것은 아니다.

## 해결 결과와 앞으로 확인할 지표

이번 작업에서는 Pod 제한을 110개에서 220개로 변경한 이후 당장 겪고 있던 Pending 문제가 해결됐다. 이후에는 실제 적용된 kubelet 설정과 Node의 allocatable Pod 수를 확인하고, 워크로드 증가에 따라 Pending 상태와 IP 할당 실패, 장애 복구 여유를 관찰할 필요가 있다. 220개를 모두 채운 상태의 부하 시험, 처리량 개선 수치, 전 노드 일괄 적용 또는 무중단 마이그레이션을 검증했다고 기록하지는 않는다.

이번 결정은 의도적으로 범위를 좁힌 변경이었다. 문제를 일으키는 제한부터 완화하되 기존 네트워크는 유지하고, 더 큰 주소 공간이 필요한 상황에 대해서는 별도의 설계 옵션으로 남겨 두었다. 앞선 K3s 운영 경험들과 마찬가지로, 하나의 클러스터 수용량처럼 보이는 것도 실제로는 서로 다른 여러 제약이 함께 성립해야 하는 문제였다.

## 관련 글

- [온프레미스 K3s 플랫폼 설계 및 운영](/projects/independent-on-premises-k3s-platform-engineering/) — 전체 플랫폼과 운영 책임의 맥락.
- [K3s 네트워킹: Pod IP 라우팅과 ClusterIP Service](/projects/rokaf-k3s-cni-service-datapath/) — 주소 할당 이후의 엔드포인트 라우팅과 Service 주소 변환을 구분한 글.
- [K3s 내부 서비스 주소 및 TLS 표준화](/projects/rokaf-gitops-domain-tls-standardization/) — 워크로드 실행 이후 DNS, VIP, TLS를 통해 서비스에 접근하는 별도의 경계.
- [GPU 배치와 수용량](/projects/rokaf-gpu-scheduling-and-capacity/) — 단순 합산 자원량으로 설명할 수 없는 배치 및 장애 복구 제약.

## 참고 자료

- [K3s Configuration Options](https://docs.k3s.io/installation/configuration)
- [Kubernetes Kubelet Configuration](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)
- [Kubernetes v1.32 대규모 클러스터 고려사항](https://v1-32.docs.kubernetes.io/docs/setup/best-practices/cluster-large/)
- [CNI host-local IPAM](https://www.cni.dev/plugins/current/ipam/host-local/)
- [KubeletConfiguration v1beta1 (Kubernetes v1.32)](https://v1-32.docs.kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)
- [K3s Server 설정과 공개 네트워크 기본값](https://docs.k3s.io/cli/server)
