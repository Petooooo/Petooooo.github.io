친환경이라고 소개된 상품을 보더라도 실제로 어떤 근거에서 친환경 제품이라고 하는지 알기 어려울 때가 있다. 2023년 9–12월에 개발한 Green Reviewer(그린리버)는 이러한 문제에서 출발했다. 상품 정보와 함께 소비자가 작성한 리뷰를 확인할 수 있도록 하고, 단순한 별점보다는 소비자가 어떤 유형의 문제를 지적했는지 보여주는 웹·모바일 서비스를 만들었다. 웹, 모바일 앱과 백엔드 개발을 모두 맡았다.

다행히 당시 코드와 실행 화면이 [공개 저장소](https://github.com/Petooooo/green-reviewer/tree/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6)에 남아 있다. 이를 바탕으로 실제로 구현했던 구조와 그 당시의 선택을 다시 살펴봤다. 아래 화면은 2023년 프로젝트 기록이며, 현재의 상품 평가나 서비스 운영 상태를 나타내는 것은 아니다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-1.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록."><img src="/figures/green-reviewer/web-1.webp" alt="웹 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록.</figcaption></figure>

## 사용자의 요청과 상품 수집 경로를 분리하기

Flutter로 화면을 만드는 것만으로 끝나는 프로젝트는 아니었다. 서버에는 Node.js와 Express를 사용했고, 역할에 따라 세 개의 서버를 구분했다. 상품 정보를 확보하고 DB에 넣는 과정은 별도의 Python 코드로 구성했다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/project-architecture.jpg" target="_blank" rel="noopener noreferrer" aria-label="원본 저장소에 남아 있는 2023년 아키텍처 그림. 당시의 클라이언트, 서버, 상품 수집 및 적재 구성을 보여준다."><img src="/figures/green-reviewer/project-architecture.jpg" alt="원본 저장소에 남아 있는 2023년 아키텍처 그림. 당시의 클라이언트, 서버, 상품 수집 및 적재 구성을 보여준다." width="4120" height="2030" loading="lazy" decoding="async" /></a><figcaption>원본 저장소에 남아 있는 2023년 아키텍처 그림. 당시의 클라이언트, 서버, 상품 수집 및 적재 구성을 보여준다.</figcaption></figure>

{{figure /figures/journals/green-reviewer-01-architecture.svg | 사용자 요청과 상품 적재는 별도의 경로로 진행된다. 리뷰 조회는 ConversionServer를 거치지 않는다.}}

| 구성 요소 | 원본 코드에서 확인한 역할 |
| --- | --- |
| Flutter/Dart | 상품 목록, 검색, 상세 정보와 리뷰 화면, 체크리스트 시각화 |
| FacadeServer | 클라이언트가 접근하는 API 경계 및 요청 전달 |
| ConversionServer | 검색어 변환, 상세 데이터 결합, 리뷰 등록·삭제 조정 |
| DatabaseServer | SQL을 이용한 상품·이미지·리뷰 데이터 접근 |
| MySQL | 상품, 상세 이미지 URL, 리뷰와 집계값 저장 |
| Python Crawler 및 JSON Uploader | 상품 카탈로그 수집 및 초기 적재 |

FacadeServer에서 검색, 검색 결과 수, 상세 정보, 리뷰 등록과 삭제 요청은 ConversionServer에 전달한다. 반면 리뷰 목록을 가져오는 요청은 바로 DatabaseServer로 전달한다. 모든 요청에 데이터 변환이 필요한 것은 아니기 때문이다. 여러 결과를 조합하거나 별도의 처리가 필요한 경우 ConversionServer를 거치도록 했다는 점이 당시 구조에서 눈에 띈다.

상품 카탈로그를 준비하는 과정은 사용자 요청과 분리했다. Crawler는 '친환경'을 붙인 검색어로 네이버 쇼핑 API에서 상품 목록을 얻은 뒤, 추가 정보가 필요한 경우 Selenium으로 상세 정보를 수집했다. 카테고리와 상품 ID에 따라 JSON 파일을 보관하고, 별도의 Uploader로 상품과 상세 이미지 URL을 MySQL에 적재했다. 초기 리뷰 수와 체크리스트 합계는 모두 0으로 설정했다. 코드와 원본 아키텍처 그림에는 이와 같은 흐름이 남아 있지만, 별도의 주기적인 수집 시스템까지 운영했다는 근거는 없다. 이번에는 외부 사이트에 대해 Crawler를 다시 실행하지 않았다.

이렇게 확보한 상품은 쇼핑 정보와 판매자의 마케팅 문구를 바탕으로 가져온 것이지 친환경 인증이 검증된 상품 목록이 아니다. 리뷰를 통해 소비자가 제기한 문제를 정리하는 것이 서비스의 역할이었으며, 실제로 특정 상품의 친환경 여부나 그린워싱 여부를 판정하는 기관을 대신할 수는 없다.

## 입력한 검색어를 카테고리로 변환하기

상품 데이터는 키워드별로 구성되어 있었다. 사용자가 입력한 검색어와 DB에 있는 카테고리가 반드시 정확히 일치하는 것은 아니므로, ConversionServer에서 검색어를 카테고리로 변환했다. DatabaseServer에서 키워드 목록을 조회한 뒤 Transformer 클래스에서 각각의 문자열과 입력 검색어 사이의 Levenshtein 거리를 계산한다.

원본 구현에서는 두 문자열의 길이가 각각 m, n이라면 2차원 배열을 만들고 첫 행과 첫 열을 삽입·삭제에 필요한 횟수로 초기화한다. 나머지 각 칸에서는 삭제, 삽입, 치환 중 비용이 가장 작은 경우를 선택한다.

```text
D[i,0] = i
D[0,j] = j
D[i,j] = min(D[i-1,j] + 1,
             D[i,j-1] + 1,
             D[i-1,j-1] + cost)
같은 문자이면 cost = 0, 다르면 1
similarity = 1 - D[m,n] / max(m,n)
```

{{figure /figures/journals/green-reviewer-02-search.svg | Transformer의 점화식으로 cup에서 cups까지의 편집 거리 행렬을 계산했다. 검색어는 설명용 예시다.}}

유사도의 초기 최댓값은 0이다. 현재 최댓값보다 더 큰 유사도를 가진 후보가 나오면 그 키워드를 저장한다. 값이 같을 때에는 앞서 확인한 후보가 그대로 남는다. 예를 들어 cup과 cups는 문자 하나를 삽입하면 같아지므로 편집 거리가 1이고, 정규화한 유사도는 0.75다. 실제 카탈로그의 검색 결과가 아니라 원본 계산을 이해하기 위한 예시다.

별도의 검색 엔진 없이 어느 정도의 철자 차이를 처리할 수 있지만, 문자열이 비슷하다고 해서 의미까지 비슷한 것은 아니다. 후보 하나를 비교할 때 시간과 공간 복잡도는 O(mn)이고 JavaScript 문자열 단위로 비교하므로 한국어 형태소나 의미를 해석하는 것도 아니다. 0보다 큰 유사도 중 최댓값을 고르는 구조라 최소 관련성을 별도로 판단하지 않고, 동점일 때 후보의 순서에도 영향을 받는다. 다시 구현한다면 정확한 일치와 유사한 표현을 먼저 구분하고 후보를 여러 개 제시하는 방식도 고려하고 싶다.

키워드가 정해지면 ConversionServer에서 페이지와 크기를 함께 DatabaseServer에 전달한다. DB 서버에서는 해당 키워드의 상품을 조회한 뒤 결과 배열의 `(page - 1) * size`부터 페이지에 해당하는 데이터를 가져온다. 실제 코드는 1부터 시작하는 페이지 번호를 사용하고 있어, 0부터 시작한다고 적힌 일부 옛 API 설명과는 차이가 있다. 검색 결과 수는 별도 API로 구한다. 현재라면 모든 행을 가져온 뒤 잘라내기보다는 SQL에서 정렬과 페이지 구간을 결정하고 범위를 검사하는 편이 낫다고 생각한다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-2.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면."><img src="/figures/green-reviewer/web-2.webp" alt="웹 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면.</figcaption></figure>

<div class="green-reviewer-mobile-grid">
<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-1.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록."><img src="/figures/green-reviewer/app-1.webp" alt="모바일 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 1 — 리뷰 집계 색상과 상품 정보가 함께 표시된 상품 목록.</figcaption></figure>
<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-2.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면."><img src="/figures/green-reviewer/app-2.webp" alt="모바일 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 2 — 동일한 상품 카드 구조를 사용한 또 다른 목록·검색 화면.</figcaption></figure>
</div>

## 같은 상품을 목록과 상세 페이지에서 다루기

MySQL 초기화 SQL에는 세 개의 테이블이 정의되어 있다. itemTable에는 상품의 기본 정보와 판매 페이지, 리뷰 수 및 체크리스트 합계가 저장되고, detailpicTable에는 상세 이미지 URL, reviewTable에는 리뷰 내용과 네 가지 체크 여부가 저장된다. 상세 이미지와 리뷰는 각각 상품 ID를 외래 키로 가진다.

{{figure /figures/journals/green-reviewer-03-data.svg | 원본 MySQL 초기화 SQL의 세 테이블은 상품 ID를 기준으로 연결된다. itemTable에는 체크리스트 합계도 저장한다.}}

상품 상세 API에서도 ConversionServer의 역할이 드러난다. DatabaseServer의 상품 정보와 상세 이미지 API를 각각 호출한 다음, 이미지 목록을 상품 정보에 붙여 한 번에 반환한다. 앱과 웹에서 각각 두 개의 응답을 조합할 필요가 없도록 구성한 것이다.

Flutter에서는 ChangeNotifier를 상속하는 GlobalStore에 선택한 상품, 상품과 리뷰의 페이지 번호, 체크리스트 합계, 대화상자와 관련된 상태를 두었다. Provider와 비동기 HTTP 요청을 이용했고, 상세 정보와 리뷰 조회에는 FutureBuilder를 사용하여 로딩과 오류 상태도 표시했다. 상품 정보에서 원본 판매 페이지의 URL을 받아 구매 페이지로 이동할 수 있도록 했다.

앱과 웹의 코드를 별도로 만들지는 않았다. 원본 Dart 코드에는 화면 폭 800 논리 픽셀을 기준으로 레이아웃, 이미지와 글자 크기, 도넛 차트의 크기를 조정하는 분기가 여러 곳에 있다. 같은 데이터를 사용하면서 화면의 폭에 따라 배치를 달리하는 방식이었다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-3.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능."><img src="/figures/green-reviewer/web-3.webp" alt="웹 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능.</figcaption></figure>

<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-3.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능."><img src="/figures/green-reviewer/app-3.webp" alt="모바일 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 3 — 상품 상세 정보, 판매처와 원본 판매 페이지 이동 기능.</figcaption></figure>

다만 당시 코드의 데이터 계약에는 아쉬운 점도 있다. DatabaseServer가 JSON으로 직렬화한 문자열을 다시 JSON 응답으로 보내는 곳이 있고, 다른 API는 객체나 문자열을 그대로 반환한다. 그래서 ConversionServer나 Flutter에서도 JSON을 두 번 이상 파싱하는 코드가 남아 있다. 응답 형식을 명확히 하나로 정의하고 오류 응답의 구조도 일관되게 설계했다면, 서버 구현과 화면 사이의 불필요한 결합을 줄일 수 있었을 것이다.

## 리뷰의 내용을 두 가지 방식으로 시각화하기

리뷰에는 네 가지 그린워싱 유형을 선택할 수 있도록 했다. 앱의 설명 화면에 남아 있는 분류는 증거 불충분, 부적절한 인증 라벨, 애매모호한 주장, 거짓말이다. 사용자는 여러 항목을 동시에 체크하고 자유롭게 리뷰 내용을 작성할 수 있다. 따라서 한 리뷰가 반드시 하나의 유형에만 속하는 구조는 아니다.

상품 목록에서 색상을 정하는 코드는 Flutter의 fetchProducts 함수에 남아 있다. 리뷰 수를 N, 네 항목의 누적 체크 수를 S1부터 S4라고 두면 다음과 같이 계산한다.

```text
N = 0                  → 회색 (리뷰 없음)
r = (S1+S2+S3+S4)/(4N)  (N > 0)

r < 0.25               → 초록색
0.25 <= r < 0.60       → 노란색
r >= 0.60              → 빨간색
```

각 체크 값이 0 또는 1이고 집계가 원본 리뷰와 일치한다면, 전체 리뷰가 선택할 수 있는 네 가지 항목 중 실제로 선택된 비율이다. 적어도 하나의 문제를 지적한 사람의 비율과는 다르며 그린워싱일 확률을 추정한 값도 아니다. 0.25와 0.60이 실제 검증 데이터로 보정된 경계라는 근거는 없다.

상세 화면에서 사용하는 DonutChart는 또 다른 분모를 사용한다. fl_chart의 각 Section에 0이 아닌 체크 수를 값으로 넣고, 선택 시 해당 항목의 개수를 표시하도록 했다. 네 가지 체크 수가 모두 0이면 도넛 차트를 표시하지 않는다. 도넛에서 각 영역이 차지하는 비중은 전체 리뷰 수가 아니라 선택된 체크 수의 합을 기준으로 결정된다.

{{figure /figures/journals/green-reviewer-04-score.svg | 가상 리뷰 5개에서 카드 점수는 0.50, 도넛의 비중은 40%, 30%, 20%, 10%다. 각각 사용하는 분모가 다르다.}}

리뷰가 5개이고 체크 수가 [4, 3, 2, 1]인 가상의 상품을 생각해 보면 카드 점수는 10/20 = 0.50이므로 노란색이다. 반면 도넛에서는 각각 40%, 30%, 20%, 10%를 차지한다. 같은 집계값을 이용하더라도 서로 다른 정보를 보여주는 것이다. 리뷰 한 개가 있는 상품과 리뷰 수백 개가 있는 상품이 같은 도넛 형태를 가질 수도 있다. 리뷰 자체가 없는 경우와 리뷰는 있지만 체크가 하나도 없는 경우도 구분해야 한다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-4.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트."><img src="/figures/green-reviewer/web-4.webp" alt="웹 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트.</figcaption></figure>

<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-4.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트."><img src="/figures/green-reviewer/app-4.webp" alt="모바일 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 4 — 네 가지 체크리스트 유형과 리뷰 분포를 표시하는 도넛 차트.</figcaption></figure>

지금 다시 화면을 설계한다면 전체 리뷰 수와 문제를 하나 이상 지적한 리뷰 수, 각 유형의 개수를 함께 보여주고 싶다. 리뷰가 없다는 사실을 문제가 없다는 뜻으로 받아들이지 않도록 구분하는 것이 중요하다. 실제 상품을 평가하는 서비스라면 신고 검토와 근거 확인, 이의 제기와 같은 절차도 필요하다. 사용자 리뷰의 집계와 검증된 친환경성은 다른 문제이기 때문이다.

## 상품에 집계값을 저장했을 때의 장단점

리뷰가 작성될 때마다 목록에서 모든 리뷰를 다시 계산하기보다는, itemTable에 리뷰 수와 네 가지 합계를 저장하는 방식으로 구현했다. 처음 상품을 적재할 때는 모두 0으로 설정한다. 리뷰 작성 요청이 들어오면 ConversionServer에서 기존 합계를 조회하고 새 리뷰의 네 가지 값을 더한다. 이후 리뷰 행을 삽입하고 다시 리뷰 수를 조회한 다음 상품의 집계값을 갱신한다.

{{figure /figures/journals/green-reviewer-05-review-update.svg | 원본 등록 로직은 네 번의 요청으로 구성된다. 아래 동시 등록 예시는 가능한 갱신 손실을 설명하며 실제 장애 기록은 아니다.}}

리뷰 삭제 시에는 기존 합계와 삭제 대상 리뷰의 체크 여부를 가져오고 당시의 삭제 확인 절차를 거쳐 리뷰를 제거한다. 이후 감소한 합계와 리뷰 수를 상품에 반영한다. 상품 목록을 조회할 때마다 리뷰 행 전체를 읽고 합산할 필요가 없다는 장점이 있었다.

다만 이 과정은 하나의 DB Transaction이 아닌 별도의 HTTP 요청 여러 개로 진행된다. 예를 들어 두 사용자가 동시에 기존 합계 3을 읽고 각각 1을 더한다면 실제 합계는 5여야 하지만 둘 다 4를 저장할 수 있다. 리뷰 삽입 이후 상품 정보 갱신 전에 요청이 실패할 때도 집계가 달라질 수 있다. 당시 발생했던 장애 기록을 확인한 것은 아니며, 원본 코드에서 파악할 수 있는 일관성 문제다. 지금이라면 DatabaseServer에서 한 트랜잭션으로 묶고 행 잠금이나 원자적인 증감 연산을 적용할 것이다. 또는 원본 리뷰를 기준으로 직접 집계하여 중복된 상태를 보관하지 않는 것도 방법이다. 재시도 시 리뷰가 두 번 삽입되지 않게 하는 문제나 상품과 리뷰 사이의 관계 확인도 함께 고려해야 한다.

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-5.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자."><img src="/figures/green-reviewer/web-5.webp" alt="웹 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자.</figcaption></figure>

<figure class="project-concept-figure green-reviewer-web"><a href="/figures/green-reviewer/web-6.webp" target="_blank" rel="noopener noreferrer" aria-label="웹 원본 화면 6 — 리뷰 삭제 확인 대화상자."><img src="/figures/green-reviewer/web-6.webp" alt="웹 원본 화면 6 — 리뷰 삭제 확인 대화상자." width="3680" height="2382" loading="lazy" decoding="async" /></a><figcaption>웹 원본 화면 6 — 리뷰 삭제 확인 대화상자.</figcaption></figure>

<div class="green-reviewer-mobile-grid">
<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-5.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자."><img src="/figures/green-reviewer/app-5.webp" alt="모바일 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 5 — 체크리스트 선택과 자유 서술을 함께 입력하는 리뷰 작성 대화상자.</figcaption></figure>
<figure class="project-concept-figure green-reviewer-mobile"><a href="/figures/green-reviewer/app-6.webp" target="_blank" rel="noopener noreferrer" aria-label="모바일 원본 화면 6 — 리뷰 삭제 확인 대화상자."><img src="/figures/green-reviewer/app-6.webp" alt="모바일 원본 화면 6 — 리뷰 삭제 확인 대화상자." width="1235" height="2646" loading="lazy" decoding="async" /></a><figcaption>모바일 원본 화면 6 — 리뷰 삭제 확인 대화상자.</figcaption></figure>
</div>

위 화면은 당시 작성과 삭제 기능을 구현한 기록이다. 하지만 옛 삭제 확인 방식이나 SQL 문자열을 조합하는 코드는 현재 운영 서비스의 보안 기준에 맞는 방식은 아니다. 다시 만들 때에는 파라미터화된 SQL, 적절한 인증과 비밀번호 해싱, 입력 검사와 요청 제한을 적용하고 외부에서 접근할 수 있는 경계는 FacadeServer로 한정할 것이다. 이번 회고 과정에서 원래 서버 코드를 수정한 것은 아니다.

## Docker를 이용한 서버 구성

공개 저장소의 Compose 파일에는 MySQL 8.1.0과 버전 1.3의 세 서버 이미지가 정의되어 있다. DB 초기화 SQL을 컨테이너에 마운트하고, 각 서비스는 별도의 환경 설정 예시 파일을 통해 필요한 설정을 관리한다. Flutter를 Chrome에서 실행하는 방법과 모바일 앱, 당시 배포에 관한 안내도 남아 있다. AWS와 Docker는 원본 아키텍처 및 사용 기술 목록에서 확인할 수 있다.

Compose는 서버를 재현하기 위한 구성이지 운영 안정성이 검증된 배포 방식이라는 뜻은 아니다. 당시에는 DB와 내부 서비스의 포트도 외부에 노출하도록 설정했고, 실행 순서만으로 DB의 준비 여부를 보장할 수는 없었다. 다시 배포한다면 내부 서비스는 별도의 네트워크 안에 두고 비밀정보 관리, Health Check, 데이터 보존, 마이그레이션과 서비스 간 오류 처리까지 고려할 것이다. 이번에는 원래 공개 주소나 APK, DB를 다시 실행하지 않았다.

Green Reviewer는 화면을 구현하는 것과 데이터를 서비스 형태로 제공하는 일이 어떻게 연결되는지 경험할 수 있었던 프로젝트였다. 상품의 식별자와 수집 방식, API 응답, 리뷰 집계가 일관되어야 화면의 숫자도 의미를 가진다. 이후 더 큰 규모의 시스템을 구성할 때에도 사용자가 보는 결과와 그 결과를 책임지는 구성 요소가 무엇인지 구분해야 한다는 점은 달라지지 않았다.

## 원본 자료와 그림

[Green Reviewer 공개 저장소](https://github.com/Petooooo/green-reviewer/tree/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6)에 당시 구현이 남아 있다. 이 글의 웹 화면 6장과 모바일 화면 6장은 각각 Image/Web과 Image/App의 원본 PNG를 무손실 WebP로 옮긴 것이다. 웹 3680 × 2382, 모바일 1235 × 2646의 해상도와 디코딩한 RGBA 픽셀을 그대로 보존했다. 4120 × 2030 원본 아키텍처 JPEG는 바이트를 변경하지 않고 사용했다. 모든 그림은 클릭하면 원본 크기로 열리며 UI에 적힌 한국어도 원본 그대로 유지했다. [이미지 출처 및 해시 기록](/figures/green-reviewer/source-manifest.json)과 [원본 라이선스](/figures/green-reviewer/LICENSE.txt)를 함께 보관했다. 새로 그린 분석용 SVG 다섯 개는 실제 소스를 바탕으로 한 설명도이며 새로운 실행 화면이나 실측 성능 자료는 아니다.

- [Flutter 클라이언트 원본](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Client/green_reviewer/lib/main.dart)
- [FacadeServer](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/FacadeServer/facadeserver.js)
- [ConversionServer](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/ConversionServer/conversionserver.js)
- [DatabaseServer](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/DatabaseServer/databaseserver.js)
- [MySQL 스키마](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/Database/init_db/mysql.sql)
- [Crawler](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/WebCrawler/WebCrawler.py)와 [JSON Uploader](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/jsonUploader/jsonUploader.py)
- [Docker Compose 구성](https://github.com/Petooooo/green-reviewer/blob/2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6/Server/docker-compose.yaml)

## 관련 프로젝트

- [Lex/Yacc 기반 PyTokenizer](/projects/python-tokenizer-lex-yacc/)
- [FreeRTOS 멀티보드 Mini-Desktop](/projects/freertos-multiboard-mini-desktop/)
- [온프레미스 K3s 플랫폼 구축·운영](/projects/independent-on-premises-k3s-platform-engineering/)
