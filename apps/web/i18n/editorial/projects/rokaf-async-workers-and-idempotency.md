RabbitMQ에는 작업이 하나 있었다. 이미 Worker가 메시지를 가져가 파일 변환을 진행하고 있었다. 그런데 어느 순간 같은 메시지가 다시 Ready로 돌아왔고, 다른 Worker가 똑같은 작업을 가져갈 수 있는 상태가 됐다.

처음에는 이해가 되지 않았다. 기존 Worker가 죽지도 않았는데 왜 RabbitMQ는 그 작업을 다시 배달하는 걸까. 로그와 작업 상태를 나눠 보니 이유가 조금씩 보였다. **Broker가 더 이상 그 Worker를 메시지의 소유자로 인정하지 않는 시점과, 실제 파일 변환 프로세스가 종료되는 시점은 다를 수 있었다.**

2026년 3월, 폐쇄망 K3s 환경에서 RabbitMQ를 운영하며 경험한 일이다. 그전에 Shovel을 이용해 기존 RabbitMQ의 메시지를 다른 Broker로 이전한 적도 있었고, 6월에는 문서 처리 Worker의 실행 모델을 다시 설계했다.

서로 이어지는 고민이기는 하지만 하나의 장애를 처음부터 끝까지 해결한 사건은 아니다. Shovel 이전은 실제로 성공했고, 3월의 연결 끊김은 최종 근본 원인을 확인하지 못했다. 6월의 Worker 개편은 별도 로컬 테스트에서 검증됐다. 이 차이를 유지하면서 기록을 남기려 한다. 내부 주소, Queue와 Virtual Host의 실제 이름, 인증 정보나 노드 구성은 옮기지 않았다.

## Shovel로 메시지를 이전한 일

3월 초에는 기존 RabbitMQ에서 새로운 RabbitMQ로 메시지를 옮겨야 했다. 단순히 서버에 새 Queue를 만드는 것만으로 기존 작업이 함께 이동하는 것은 아니었다. 그래서 RabbitMQ의 Shovel을 사용했다.

Shovel은 기존 Broker의 Queue에서 메시지를 꺼내 다른 Broker에 발행하는 방식으로 동작한다. 당시에는 대응되는 Source와 Destination Queue를 설정했고, `on-confirm` Ack 모드를 사용했다. 이 모드는 Destination에서 발행을 Confirm한 뒤 Source 메시지를 Ack한다.

Shovel이 Running 상태인 것을 확인했고, 오래된 Queue의 메시지 수가 줄어드는 동안 새 Queue의 메시지 수가 증가하는 것도 관측했다. 그래서 메시지 이전이 성공했다고 판단했다. 이후에는 애플리케이션을 새로운 RabbitMQ의 Kubernetes Service 주소로 연결하려 했다.

다만 이것은 **메시지를 이전한 결과**다. 이미 처리 중인 Worker의 상태나 DB 기록, 파일 변환 결과까지 Shovel이 옮기는 것은 아니다. 실제 이전된 메시지를 ID 단위로 모두 대조하거나, 중복된 업무 결과까지 검증했다는 기록도 없다.

Shovel이 정상 동작했다는 사실과, 이후 Consumer가 몇 시간 동안 안정적으로 작업한다는 사실은 서로 다른 질문이었다.

## HTTP 프록시를 거치지 않았는데도 연결이 끊겼다

Shovel 이전을 마친 뒤에는 `Connection reset by peer`가 계속 문제가 됐다.

당시 Worker는 Kubernetes 내부에서 RabbitMQ Service 이름으로 직접 접속하고 있었다. Nginx나 Traefik 같은 웹 Reverse Proxy를 통과하지 않는 경로였다. 따라서 웹 프록시의 Timeout이나 WebSocket Upgrade 문제만으로 설명할 수는 없었다.

문서 변환은 짧게는 약 **500초**, 길게는 **3시간**까지 걸릴 수 있었다. 처음 사용한 Worker 구조에서는 변환 작업이 끝나야 Ack를 보냈다. 그동안 메시지는 계속 Unacked 상태였고, RabbitMQ 연결도 유지돼야 했다.

Broker 로그를 살펴보다가 다음 문구를 확인했다.

`missed heartbeats from client, timeout: 60s`

일부 연결은 약 3분 동안 유지되다가 종료됐다고 기록돼 있었다. 처음에는 Client에서 Heartbeat와 `blocked_connection_timeout`을 따로 지정하지 않았고, 이후에는 연결의 I/O Loop나 Heartbeat 처리를 긴 변환 작업과 분리하는 방식도 검토하고 시도했다. 하지만 연결 끊김은 계속됐다.

서버 쪽 Heartbeat를 `86400`초로 크게 설정했거나 설정된 값을 확인한 뒤에도 상황이 달라지지 않았다. 하루 동안 작업을 기다리도록 설정하면 해결될 것 같았지만, 실제로는 그렇지 않았다.

여기서 설정 하나만 보고 단정해서는 안 되는 이유가 있었다. **AMQP Heartbeat는 Client와 Server 사이에서 협상되는 값이다.** 서버의 설정값이 86400이라고 해서 문제가 발생한 연결에서 실제로 그 값이 사용됐다는 뜻은 아니다. 로그에는 60초가 남아 있었고, 당시에는 실패한 Connection의 협상된 값을 직접 확인해 둘 만큼의 증거를 확보하지 못했다.

`consumer_timeout`이 `1800000`밀리초, 즉 30분으로 보였던 기록도 별도로 있었다. 그러나 이것은 Consumer가 Delivery Ack를 오래 보내지 않는 경우에 관한 제한이다. 연결 유지 여부를 확인하는 Heartbeat와는 다르다. `missed heartbeats ... 60s`를 30분짜리 Ack Timeout으로 해석하면 장애를 잘못 추적하게 된다.

Heartbeat 협상, Worker 내부 I/O 처리, 네트워크 Idle Timeout 등 여러 가능성을 살펴봤지만 3월 연결 끊김의 정확한 근본 원인이나 영구적인 해결 결과는 기록으로 확인할 수 없다.

## 더 심각한 문제는 한 작업을 둘이 처리한다는 것이었다

연결이 끊기는 문제 자체도 불편했지만, 더 위험한 상황은 그 이후에 나타났다.

RabbitMQ는 Consumer와 연결이 사라지면 Ack되지 않은 Delivery를 다시 Queue에 넣고 다른 Consumer에게 전달할 수 있다. 그런데 메시지를 받았던 Worker의 Python 함수는 연결 상태와 별개로 계속 변환을 수행할 수 있다.

실제로 기존 Worker가 작업 중인데 메시지가 Ready로 돌아오는 현상을 확인했다. 이때 다른 Worker가 같은 메시지를 가져가면 한 사용자의 파일 변환을 동시에 두 번 실행할 수 있다.

{{figure /figures/journals/rabbitmq-two-owners-timeline.svg | Broker가 연결 끊김 후 메시지를 다시 배달하는 시점과 기존 Worker가 변환을 계속하는 구간을 나란히 놓았다. 시간은 측정값이 아니라 관측한 중복 처리 위험을 설명하기 위한 개념도다.}}

여기서 문제는 CPU가 낭비되는 데 그치지 않는다. 두 Worker가 각각 결과 파일을 생성해 MinIO에 저장하거나 DB의 작업 상태를 갱신할 수도 있다. 뒤늦게 끝난 첫 번째 Worker가 두 번째 Worker의 완료 상태를 덮어쓰는 상황도 생각해야 한다.

Heartbeat를 길게 설정하는 것은 Connection이 끊기는 빈도에 영향을 줄 수 있어도 **결과를 저장한 직후 Ack 전에 Worker가 죽는 실패 구간**을 없애지는 못한다. Broker 연결이 안정적인지와 사용자 요청 하나에 결과가 하나만 남는지는 다른 문제였다.

## Ack 시점을 앞당기는 것만으로는 부족했다

처음의 구조는 처리 완료 후 Ack하는 방식이었다. Worker가 중간에 죽으면 RabbitMQ가 메시지를 다시 배달할 수 있다는 장점이 있다. 하지만 긴 변환 작업 전체를 하나의 AMQP Delivery와 Connection에 의존하게 만든다. 실제 작업은 살아 있는데 Connection만 끊기면 중복 실행을 막기 어렵다.

그렇다고 메시지를 받자마자 Ack해도 될까. Ack를 먼저 보내고 Worker가 아무것도 저장하지 못한 채 죽으면 RabbitMQ는 이미 완료한 Delivery를 다시 보내지 않는다. 이번에는 작업이 사라질 가능성이 생긴다.

그래서 6월에 설계한 새로운 모델에서는 단순히 Ack를 빠르게 보내는 대신 **영속 상태에 작업의 소유권을 먼저 남기는 것**부터 시작했다.

Job Service가 현재 Stage를 확인하고, Worker가 해당 Stage를 Claim하도록 했다. Claim에는 Job, Stage, Attempt, Lease 같은 정보가 연결된다. Claim이 DB에 안전하게 기록된 다음 RabbitMQ에 Ack한다. 그 뒤 Worker는 오래 걸리는 변환을 수행한다.

작업 도중에는 Heartbeat나 Lease 갱신을 통해 진행 상태를 남길 수 있다. Worker가 중단되면 RabbitMQ는 이미 Ack된 메시지를 다시 보내지 않으므로 Job Service가 Stale Lease를 찾아 새 Attempt를 허용해야 한다.

| 실행 단계 | RabbitMQ가 아는 것 | Job Service가 확인할 것 |
| --- | --- | --- |
| 메시지 수신 | Ack되지 않은 Delivery | Stage가 아직 Pending인지 |
| Claim 저장 | Ack 전이라면 Delivery 유지 | 현재 Stage의 소유자와 Attempt |
| Claim 후 Ack | 메시지 전달 완료 | 실제 변환은 아직 완료되지 않음 |
| 장시간 처리 | 작업 결과를 Broker가 추적하지 않음 | Lease와 Worker 진행 상태 |
| Worker 중단 | Ack한 명령은 자동 재전달하지 않음 | 만료된 Lease를 조정하고 재시도 |
| 결과 저장·완료 이벤트 | Ack만으로 결과 존재를 알 수 없음 | 현재 Stage 및 산출물의 정합성 |

{{figure /figures/journals/rabbitmq-ack-claim-failure-windows.svg | 기존의 처리 완료 후 Ack 방식과 Claim 후 Ack 모델이 실패 시점에 따라 어떤 책임을 지는지 비교했다. 새로운 방식은 Ack만 바꾼 것이 아니라 Lease와 복구 주체를 함께 바꾼 것이다.}}

이 설계에서는 Claim의 동시성도 중요하다. 두 Worker가 Pending 상태를 읽었다고 해서 둘 다 자신이 소유자라고 주장해서는 안 된다. 조건부 갱신이나 원자적 Claim이 필요하다.

이전 Worker가 뒤늦게 완료 이벤트를 보낸다면 현재 Stage와 Attempt를 확인해 오래된 결과를 무시할 수 있어야 한다. 새로운 Worker가 작업을 다시 시작했는데 과거 Worker가 최종 상태를 덮어쓰면 Lease를 도입한 의미가 없다.

## 메시지는 여러 번 도착해도 Job은 하나여야 했다

사용자가 요청한 파일 변환 하나를 식별하는 ID는 RabbitMQ Delivery가 다시 발생했다고 바뀌어서는 안 된다. Job ID와 Stage ID는 안정적으로 유지하고, 각 처리 시도를 Attempt로 구분하는 편이 맞았다.

이 문제는 PostgreSQL, MinIO, RabbitMQ 사이의 경계에서 더 복잡해졌다. 이 세 시스템의 상태는 하나의 트랜잭션으로 동시에 Commit할 수 없다.

Worker가 파일을 MinIO에 저장한 직후 완료 이벤트를 보내기 전에 죽을 수 있다. 반대로 DB에는 완료라고 적혔는데 결과 파일이 존재하지 않을 수도 있다. 새로운 Attempt가 무조건 파일을 다시 만들면 중복된 결과가 남는다.

그래서 안정적인 결과 파일 Key와 작업 ID를 사용하고, 기존 산출물을 조회하며, Stage 진행 상태와 실제 파일의 존재를 대조하는 Reconciliation이 필요했다.

Retry와 Backoff, 최대 시도 횟수, 실패 상태도 같은 맥락이다. 6월 로컬 테스트에서는 Claim과 Stale Lease, Retry·Backoff, 논리적인 Dead-letter 상태를 다뤘다. 하지만 RabbitMQ의 **물리적인 DLX/DLQ 구성은 Helm 설치 과정에서 Queue 선언 충돌이 발생해 모든 환경에서 기본 활성화된 것은 아니었다.** DB에서 실패 상태를 관리하는 것과 RabbitMQ에 실제 DLQ가 설치된 것은 구분해야 한다.

## 무엇을 실제로 검증했을까

6월에 진행한 Worker 재설계는 개념적인 제안에서 끝나지 않았다. 남아 있는 작업 기록에는 Claim, 중복 명령, 오래된 이벤트 처리, Lease 만료 조정, 제한된 재시도에 대한 테스트가 있다.

또한 PDF·DOCX·HWPX 경로별 E2E Smoke Test와 별도 격리 환경에서의 Helm 설치 리허설이 통과한 결과도 남아 있다. 이 정도는 특정 테스트 조건에서 새 실행 모델이 동작했다는 근거로 쓸 수 있다.

그러나 **3월의 Connection Reset이 이 설계로 완전히 해결됐다는 뜻은 아니다.** 실제 운영 환경의 모든 Race Condition이 사라졌다는 증거도 없고, 성능이 몇 퍼센트 향상됐다는 수치도 없다.

내가 더 중요하게 보고 싶은 실패 테스트는 구체적이다. Claim과 Ack 직후 Worker를 죽였을 때 같은 Job을 복구할 수 있는가. 결과 파일을 저장한 뒤 완료 이벤트 전에 중단해도 중복 산출물을 만들지 않는가. 같은 명령이나 오래된 완료 이벤트를 다시 받아도 Stage가 잘못 넘어가지 않는가. Retry 한도에 도달하면 작업이 사라지는 대신 확인 가능한 실패 상태로 남는가.

일부는 로컬 테스트에서 다뤘지만, 이 목록 모두에 대해 실제 운영 환경에서 동일한 장애 주입을 마쳤다고 쓰지는 않는다.

## Shovel이 옮긴 것과 Job Service가 옮긴 것

돌아보면 Shovel 이전과 Worker 재설계는 비슷한 단어로 설명할 수 있어도 본질은 달랐다.

Shovel은 기존 RabbitMQ에서 새 RabbitMQ로 **메시지**를 옮겼다. `on-confirm`은 Destination 발행을 확인한 뒤 Source를 Ack하는 경계다. 메시지 이전 성공이 문서 변환의 정확히 한 번 실행을 보장하는 것은 아니다.

6월의 구조가 바꾼 것은 **오래 실행되는 작업의 책임**이었다. RabbitMQ 메시지는 전달을 위한 수단으로 남기고, 사용자가 요청한 Job과 Stage, Attempt, Lease, 결과 파일의 상태를 별도로 영속화했다.

내가 가장 오래 기억하는 장면은 Worker가 아직 변환 중인데 큐에서 같은 메시지가 다시 Ready로 보이던 순간이다. 그때부터는 RabbitMQ가 메시지를 몇 번 배달했는지만 확인해서는 안 됐다.

이후 작업 상태 설계에서는 AMQP Delivery와 논리적 Job을 따로 다뤘다. 메시지가 다시 전달되더라도 이미 진행 중인 작업과 결과 저장 주체를 영속 상태에서 확인하도록 하는 것이 목표였다.

## 함께 읽을 기록

- [K3s 플랫폼 운영 기록](/projects/independent-on-premises-k3s-platform-engineering/)
- [데이터베이스와 마이그레이션 상태 관리](/projects/rokaf-database-ha-and-langfuse-migrations/)

## 참고 문서

- [RabbitMQ — Heartbeat 협상과 Timeout](https://www.rabbitmq.com/docs/heartbeats)
- [RabbitMQ — Consumer Ack와 Publisher Confirm](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ — Consumer Ack Timeout](https://www.rabbitmq.com/docs/consumers)
- [RabbitMQ — Shovel](https://www.rabbitmq.com/docs/shovel)
- [RabbitMQ — Shovel의 Ack 모드](https://www.rabbitmq.com/docs/shovel-dynamic)