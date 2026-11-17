Grafana에서 호스트 상태를 확인하려고 했는데, 늘 보이던 그래프가 비어 있었다. 처음에는 node-exporter를 의심했다. 하지만 Kubernetes에는 DaemonSet과 Service가 그대로 있었고, 다른 한편으로 Prometheus 로그에는 WAL 파일을 기록하지 못했다는 오류가 남아 있었다.

이 장면이 기억에 남는 이유는 단순하다. **모니터링이 동작하지 않을 때 가장 먼저 확인하고 싶은 곳도 모니터링 화면**이기 때문이다. 화면이 비어 있다는 사실은 분명한데, 그 빈 화면은 원인을 말해주지 않았다.

GPU 메트릭에서도 비슷한 일을 겪었다. 한 GPU 노드에서는 DCGM Exporter가 실행되고 있었지만 다른 GPU 노드에는 없었다. 겉모습은 비슷한 두 문제였지만 손봐야 할 계층은 달랐다.

폐쇄망 K3s 환경에서 Prometheus와 Grafana, node-exporter, GPU Operator의 DCGM Exporter, Elasticsearch·Logstash·Kibana 기반 로그 수집 체계를 운영하며 내게 남은 질문은 하나였다. **값이 없을 때, 정확히 어디에서 관측이 끊겼는가?**

## 빈 그래프를 보면 무엇부터 의심해야 할까

메트릭이 화면에 도달하기까지는 여러 단계를 거친다. 장치나 호스트에서 값을 읽어야 하고, Exporter가 이를 노출해야 한다. Prometheus가 수집 대상을 발견해 Scrape하고, 수집한 값을 저장한 뒤, Grafana가 올바른 쿼리로 조회해야 한다.

이 중 어느 단계가 실패해도 결과는 비슷해 보인다. 그래서 처음부터 Grafana 쿼리만 바꾸거나 Pod를 재시작하면 실제 원인을 놓치기 쉽다.

- **생산:** Exporter가 의도한 노드에서 실행 중이고 실제로 메트릭을 내보내는가?
- **발견과 수집:** Prometheus가 ServiceMonitor를 선택해 Target을 만들었으며 Scrape 결과가 정상인가?
- **저장:** Prometheus의 TSDB가 새 샘플을 받아 기록할 수 있는가?
- **조회:** Grafana의 Data source와 라벨 조건이 저장된 시계열을 정확히 가리키는가?

`Target` 목록에 대상이 없다면 발견 규칙을 살펴야 한다. Target은 `UP`인데 패널만 비어 있다면 쿼리와 시계열 라벨을 비교해야 한다. Prometheus가 기록 자체에 실패하고 있다면 앞선 두 문제와도 접근 방법이 달라진다.

{{figure /figures/journals/observability-evidence-matrix.svg | 메트릭이 사라졌을 때 확인할 계층을 나눴다. 색을 채운 항목은 기록에서 관측한 사실이고, 나머지는 추가로 확인할 진단 단계다.}}

## Prometheus의 WAL이 가득 찼던 날

Prometheus 로그에 남았던 오류는 비교적 명확했다.

> `/prometheus/wal/…: no space left on device`

세그먼트 식별자는 제외했지만, 오류가 의미하는 바는 분명하다. Prometheus가 자신의 데이터 경로에 파일을 쓰려다 저장 공간 부족에 부딪혔다는 것이다.

비슷한 시기에 Grafana에서 node-exporter 메트릭이 보이지 않았다. DaemonSet과 Service는 존재했다. 그러나 **메트릭을 노출하는 프로세스가 살아 있는 것과 그 메트릭이 저장되고 있다는 것은 다른 사실**이다. node-exporter가 값을 내보낸다 해도 Prometheus의 쓰기 경로가 막혀 있다면 새로운 샘플은 정상적인 시계열로 남지 못할 수 있다.

이 둘이 시간상 겹쳤다는 사실은 중요하다. 다만 모든 누락이 WAL 공간 부족 하나에서 시작됐는지, 다른 Scrape 문제가 함께 있었는지까지 확인한 것은 아니다. 이 글에서도 그 둘을 하나의 확정된 인과관계로 묶지 않는다.

### 보관 기간을 줄인다고 모든 공간 문제가 끝나지는 않는다

처음에는 메트릭 보관 기간만 적당히 잡으면 된다고 생각하기 쉽다. 하지만 Prometheus의 디스크에는 과거 TSDB 블록만 있는 것이 아니다. 최근 기록을 복구하기 위한 WAL, Head 데이터, 블록 Compaction 과정에 필요한 임시 공간도 있다.

과거 블록을 지울 수 있다고 해도 그 순간 WAL과 Compaction이 필요로 하는 공간이 자동으로 확보되는 것은 아니다. 보관 정책만이 아니라 **활성 쓰기 경로에 남겨둘 여유 용량**을 별도로 생각해야 했다.

{{figure /figures/journals/prometheus-wal-visibility-gap.svg | 위쪽은 Prometheus 디스크 공간을 계획할 때 구분할 영역이다. 아래쪽은 0으로 측정된 샘플과 값 자체가 없는 구간의 차이다. 그림의 크기와 점은 당시 측정값이 아니다.}}

빈 그래프에서 주의할 것이 하나 더 있다. **샘플이 없다는 것과 샘플의 값이 0이라는 것은 같지 않다.** 시계열이 오래돼 현재 쿼리에서 빠질 수도 있다. 이를 “그 시간에는 CPU 사용률이 0이었다”고 읽으면 모니터링 장애가 정상 상태로 둔갑한다.

WAL 파일을 곧바로 지우는 일도 조심해야 한다. 아직 블록으로 완전히 반영되지 않은 기록을 잃을 수 있기 때문이다. 실제 조치에 앞서 파일시스템과 PVC 사용량, WAL·Head·블록이 차지하는 공간, Prometheus 로그와 Target 상태를 함께 살피는 편이 낫다.

당시 검토한 방향은 공간 사용량 파악, 보관 정책과 수집 부하 조정, 필요 용량 확보였다. 남아 있는 기록으로는 어느 변경이 최종 반영됐는지, 얼마나 많은 데이터를 복구했는지, 사후 검증을 모두 마쳤는지까지 단정할 수 없다. 따라서 이는 **복구를 판단하기 위한 절차**이지 성공을 확인한 회고는 아니다.

## GPU가 있는데 GPU 메트릭이 보이지 않을 때

DCGM Exporter 문제는 Prometheus 저장 공간 문제와 달리 수집의 출발점에서 생겼다.

한때는 GPU가 없는 노드에도 Exporter Pod가 배치돼 `ContainerCreating`에서 더 진행하지 못했다. DaemonSet이라는 이름 때문에 모든 노드에 Pod가 생기는 것이 정상처럼 보일 수 있지만, GPU Exporter는 해당 장치를 사용할 수 있는 노드에 배치돼야 한다.

다른 시기에는 정반대였다. 한 GPU 노드에서는 Exporter가 동작했으나 다른 GPU 노드에는 없었다. 누락된 호스트의 예상 엔드포인트에 직접 접속했을 때 연결이 거부됐고, DaemonSet을 살펴보니 `nodeSelector`가 첫 번째 GPU 노드에 고정돼 있었다.

앞의 사례는 **배치 범위가 너무 넓었던 것**, 뒤의 사례는 **범위가 너무 좁았던 것**이다. Grafana에서는 둘 다 GPU 그래프 누락으로 보일 수 있다.

{{figure /figures/journals/dcgm-exporter-placement-coverage.svg | 같은 GPU 모니터링 요구에도 배치 정책에 따라 다른 문제가 생긴다. 마지막 행은 GPU 역할 기반 선택이라는 설계 방향이며, 실제 전체 노드 적용 결과는 아니다.}}

특정 호스트 이름으로 고정한 설정은 처음 만들 때 편하다. 하지만 GPU 노드가 하나 더 생기면 그 노드의 메트릭은 조용히 빠진다. 그래서 노드 이름보다 **GPU 역할을 표현하는 라벨**을 기준으로 Exporter를 배치하는 편이 관리하기 좋겠다고 판단했다.

GPU Operator가 생성한 DaemonSet을 직접 수정하면 변경 내용이 다시 조정될 수 있다. 가능하면 GPU Operator의 Helm Values나 `ClusterPolicy`에서 Affinity와 Toleration을 관리해야 한다. 그 방향을 검토했다는 기록은 있지만, 모든 GPU 노드에 최종 정책을 적용하고 검증했다는 자료까지 확보한 것은 아니다.

### Pod가 떠도 수집이 완성된 것은 아니다

GPU 노드에 Pod를 올렸다고 문제가 끝나는 것도 아니다.

| 확인 위치 | 실제로 봐야 할 것 |
| --- | --- |
| GPU 노드 | 드라이버와 장치가 인식되는지 |
| DaemonSet | 대상 GPU 노드마다 Exporter Pod가 있는지 |
| Exporter | `/metrics`에서 필요한 DCGM 메트릭이 반환되는지 |
| Prometheus Operator | ServiceMonitor가 선택되고 실제 Target이 생성되는지 |
| Prometheus | Target이 `UP`이고 최신 시계열을 조회할 수 있는지 |
| Grafana | Data source, 라벨, 시간 범위가 실제 시계열과 일치하는지 |

검토한 설정 중에는 DCGM Exporter의 ServiceMonitor가 비활성화된 경우도 있었다. Exporter가 실행 중이어도 수집 대상 등록이 안 되면 Prometheus의 데이터는 늘지 않는다. 별도 조사에서 `nfd.enabled: false`로 인한 Node Feature Discovery 라벨 문제도 접했다. 그러나 이를 모든 GPU 메트릭 누락의 원인으로 묶어 말할 수는 없다.

## GPU 사용률이 알려주지 않는 것

GPU 메트릭은 사용률과 온도, 메모리 사용량 같은 질문에는 도움이 된다. 그렇지만 그래프만으로 여러 워크로드가 얼마나 공정하게 자원을 나눠 쓰는지 증명하기는 어렵다.

Time-slicing은 물리 GPU와 VRAM을 공유한다. MIG는 지원 GPU에서 자원을 하드웨어 수준으로 분할하는 다른 방식이다. 어떤 단위로 수집한 메트릭인지—물리 장치인지, MIG 인스턴스인지, 컨테이너나 워크로드인지—확인하지 않으면 한 GPU의 사용률을 그대로 사용자별 점유율로 읽는 오류가 생긴다.

이 고민은 [GPU 공유와 용량 설계](/projects/rokaf-gpu-scheduling-and-capacity/)에 따로 정리했다. GPU가 스케줄러에 노출되지 않는 문제도 [GPU 리소스 발견 조사](/projects/rokaf-gpu-discovery-open-investigation/)에서 다뤘다.

## 로그와 메트릭 사이에서 놓치기 쉬운 것

Prometheus와 Grafana 외에도 Elasticsearch·Logstash·Kibana로 로그를 모았다. 이후 Loki나 데이터베이스 관측성 도구도 검토했다. 그러나 로그 수집 시스템이 있다는 이유만으로 모든 서비스의 요청 흐름을 추적할 수 있다고 말할 수는 없다.

메트릭은 자원 사용이나 오류율의 변화를 파악하는 데 좋다. 로그는 특정 시점의 실패 메시지를 남긴다. 분산 트레이스는 계측된 요청이 어떤 서비스를 거쳤는지 연결해줄 수 있지만, 실제로 Trace를 생성하고 전달하도록 설정한 경로에 한정된다.

**어느 계층을, 어떤 해상도로, 어느 기간 동안 관측할 수 있는지**를 빼고 “관측 가능하다”고 말하면 도구가 설치돼 있다는 이야기만 남기 쉽다.

## 다음 장애를 위해 남긴 기준

남아 있는 기록으로 확인할 수 있는 사실은 명확하다. Prometheus는 WAL 쓰기에서 공간 부족 오류를 냈다. node-exporter 메트릭은 Grafana에서 보이지 않았지만 관련 Kubernetes 리소스는 남아 있었다. DCGM Exporter는 잘못된 노드 집합에 배치되거나 한 GPU 노드에만 고정돼 관측 범위를 벗어난 사례가 있었다.

반대로 **전체 메트릭 누락의 단일 원인, WAL 복구 후 손실 범위, 최종 ServiceMonitor 설정, GPU 전체 노드의 영구적인 수집 정상화, 알림 시스템의 효과**는 충분히 검증됐다고 말할 수 없다.

다음에 비슷한 상황이 온다면 대시보드 대신 수집 경로를 따라가고 싶다. Exporter가 있는가, 직접 응답하는가, Target이 발견되는가, 샘플이 저장되는가, Grafana가 그 값을 제대로 요청하는가. 모니터링이 고장 나더라도 이 질문에 답할 수 있는 로그와 호스트 상태 확인 수단은 남겨둬야 한다.

빈 화면은 실패가 발생했다는 사실을 알려줄 뿐이다. **어디에서 관측이 끊겼는지는 따로 증명해야 한다.**

## 참고 자료

- [Prometheus 로컬 스토리지와 WAL](https://prometheus.io/docs/prometheus/latest/storage/)
- [Prometheus 시계열 Staleness](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Prometheus Operator의 ServiceMonitor](https://prometheus-operator.dev/docs/platform/troubleshooting/)
- [NVIDIA DCGM Exporter](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html)
- [온프레미스 K3s 운영 기록](/projects/independent-on-premises-k3s-platform-engineering/)
