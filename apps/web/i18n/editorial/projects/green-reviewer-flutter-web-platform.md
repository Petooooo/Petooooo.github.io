2023년 9~12월에는 **Green Reviewer(그린리버)** 프로젝트로 웹·모바일 서비스를 개발했다. 친환경 제품이라고 소개된 상품을 사용자가 리뷰와 관련 정보를 통해 살펴볼 수 있게 하는 프로젝트였다. 당시 관심사는 그린워싱이었다. 소비자가 마케팅 문구만 보지 않고 실제 사용 경험과 제품 정보를 비교할 수 있도록 돕는 서비스가 필요하다고 생각했다.

이 프로젝트에서는 **Flutter/Dart 클라이언트와 Node.js 기반 웹·서버 구성 요소**를 개발했다. 현재도 [공개 GitHub 저장소](https://github.com/Petooooo/green-reviewer)에서 클라이언트와 서버 폴더, 실행 방법을 확인할 수 있다.

2023년 프로젝트를 2026년 11월에 다시 정리한 글이며, 아래 날짜는 실제 개발 당시를 가리킨다.

## 모바일과 웹을 하나의 서비스로 구성하기

클라이언트는 **Flutter와 Dart**로 구현했다. 모바일 화면과 웹 화면에서 상품 정보와 리뷰를 보여주기 위해 서버에서 필요한 데이터를 받아오도록 했다.

상품·리뷰를 보여주는 화면을 만들 때는 디자인뿐 아니라 데이터 구조도 함께 생각해야 했다. 클라이언트가 데이터베이스의 테이블이나 접속 정보를 직접 알기보다, 서버에서 필요한 내용을 정리한 API 응답을 받는 구조가 관리하기 편했다.

{{figure /figures/journals/green-reviewer-client-backend.svg | Green Reviewer의 Flutter 웹·모바일 클라이언트와 Node.js·Express 서버, SQL 데이터 저장소의 역할을 구분한 개념도다.}}

## Node.js 서버와 데이터 저장

서버에는 **Node.js·Express**를 사용했다. 공개 저장소에는 클라이언트와 별개로 Server 디렉터리가 있고, Database와 DatabaseServer, FacadeServer, ConversionServer 등의 구성도 기록돼 있다.

이 구조에서는 외부 요청을 받는 부분과 데이터를 다루는 부분을 구분해야 했다. 화면에 보여줄 내용을 전달하는 API와 실제 데이터 저장·변환을 담당하는 코드를 한곳에 섞지 않는 방식이었다.

## Docker로 실행 가능한 서버 구성

프로젝트 README에는 **Docker Compose로 서버를 실행하는 방법**과 Flutter 클라이언트를 실행하는 과정이 남아 있다. 환경별 DB 접속 정보와 서비스 연결 설정을 분리하도록 안내한 점도 확인할 수 있다.

당시 사용한 기술에는 Docker와 AWS도 포함된다. 다만 그 사실만으로 현재 서비스가 상시 운영되고 있다거나 특정 가용성 수치를 달성했다고 말하지는 않는다. 이 글은 당시 구현한 애플리케이션을 정리하는 기록이다.

## 구현 결과

| 영역 | 구현 내용 |
| --- | --- |
| 클라이언트 | Flutter·Dart 기반 웹·모바일 화면 |
| 서버 | Node.js·Express 기반 API·서버 구성 |
| 데이터 | SQL 기반 저장소와 별도 데이터 처리 구성 요소 |
| 실행 환경 | Docker Compose 기반 서버 실행 방식 |
| 소스 관리 | 클라이언트·서버 코드와 설치 문서 공개 |

**화면과 API, 데이터 저장소까지 연결한 실제 웹·모바일 프로젝트**라는 점에서 남겨둘 가치가 있다. 이후 K3s 환경에서 여러 서비스를 구축할 때는 규모가 훨씬 커졌지만, 사용자의 요청이 어디로 전달되고 어떤 구성 요소가 결과를 책임지는지 구분해야 한다는 문제는 같았다.

## 관련 프로젝트

- [Green Reviewer 공개 GitHub 저장소](https://github.com/Petooooo/green-reviewer)
- [Lex/Yacc 기반 PyTokenizer](/projects/python-tokenizer-lex-yacc/)
- [온프레미스 K3s 플랫폼 구축·운영](/projects/independent-on-premises-k3s-platform-engineering/)
