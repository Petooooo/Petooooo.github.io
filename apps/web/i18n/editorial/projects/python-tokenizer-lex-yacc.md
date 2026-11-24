2023년 10–11월에는 C와 Lex/Yacc를 이용해 Python 코드의 Tokenizer와 Syntax Analyzer를 만들었다. PyTokenizer라는 이름의 프로젝트였고 전체 개발을 맡았다. 소스 코드에 적혀 있는 문자들을 어떻게 의미 있는 단위로 나누고, 그렇게 나눈 단위들이 하나의 문장을 이루는지 판단하는 것이 목적이었다.

당시 프로젝트를 다시 정리하면서 가장 아쉬웠던 것은 Lex와 Yacc의 원본 파일 및 실행 로그를 확보하지 못했다는 점이다. 남아 있는 이력에는 사용한 언어와 도구, 개발 범위와 목적이 기록되어 있다. 정확한 Grammar를 기억하는 것처럼 쓰기보다는 작은 대입문 분석기를 별도로 구현하여 실제로 Token을 생성하고 Parser를 동작시켜 보았다. 아래에서 다루는 재현 모델은 2026년 11월에 작성한 Python 코드이며, 2023년에 만든 C 프로그램 자체는 아니다.

## 소스 코드에서 Token을 얻기까지

{{figure /figures/journals/pytokenizer-lex-yacc.svg | Lex에서 문자를 Token으로 구분하고 Yacc에서 Token의 문법 구조를 확인한다. 당시 사용한 도구의 역할을 나타낸 개념도다.}}

코드가 처음 입력될 때에는 그저 문자열이다. Lexer는 각 문자열이 식별자인지, 숫자인지, 연산자인지 구분한다. 그 결과를 받는 Parser는 Token의 종류와 순서를 가지고 문법 구조를 판단한다. 예를 들어 total이라는 문자열이 NAME이라는 사실과 그것이 대입문의 왼쪽에 올 수 있다는 사실은 서로 다른 단계에서 다루게 된다.

```python
total = 2 + 3 * 4
```

위 대입문을 재현 Scanner에 입력하면 다음과 같이 나뉜다. Token의 종류와 실제 매치된 문자열인 Lexeme, 소스에서 시작한 위치를 각각 구분했다.

{{figure /figures/journals/pytokenizer-01-token-stream.svg | 재현 Scanner가 대입문에서 반환한 Token 일곱 개와 EOF, 각 Token의 시작 열. 아래는 최장 매치와 규칙 순서의 차이를 보여준다.}}

| Token | Lexeme | 시작 열 |
| --- | --- | ---: |
| NAME | total | 1 |
| ASSIGN | = | 7 |
| NUMBER | 2 | 9 |
| PLUS | + | 11 |
| NUMBER | 3 | 13 |
| STAR | * | 15 |
| NUMBER | 4 | 17 |
| EOF | — | 18 |

이번 Scanner는 ASCII 기반의 식별자와 정수, 일부 연산자와 공백만 인식한다. 같은 위치에서 여러 규칙이 매치되면 가장 긴 문자열을 선택하고, 길이가 같으면 먼저 정의된 규칙을 적용했다. 이는 Flex의 입력 매치 규칙을 직접 구현한 것이다. 대입문 Grammar에서는 사용하지 않지만 어휘 분석의 경계를 확인하기 위해 if와 ==도 Token으로 인식하도록 했다.

이 부분을 Lex 문법으로 표현하면 다음과 같은 형태가 된다.

```text
%%
"if"                     { return IF; }
[a-zA-Z_][a-zA-Z_0-9]*   { return NAME; }
[0-9]+                   { return NUMBER; }
"=="                     { return EQ; }
"="                      { return ASSIGN; }
[ \t]+                   { /* skip */ }
%%
```

당시 원본의 발췌가 아니라 설명용 코드다. 실제 Lex 파일을 완성하려면 Token 선언 및 다른 연산자, 위치 정보, 오류 처리까지 추가해야 한다. 이번 모델은 Token Stream을 먼저 모두 생성한 뒤 Parser에 전달한다는 점에서도 필요할 때마다 Token을 요청하는 일반적인 Yacc 구성과는 차이가 있다.

ifx를 입력하면 예약어 규칙은 앞의 두 글자까지만 매치하지만 식별자 규칙은 세 글자를 전부 읽으므로 NAME이 된다. 반면 if는 두 규칙이 모두 같은 길이만큼 매치하므로 먼저 선언한 예약어 규칙이 선택된다. ==는 ASSIGN 두 개가 아니라 EQ 하나가 된다. 규칙의 순서가 항상 최우선인 것은 아니다. 우선 매치 길이를 비교하고 길이가 같은 경우에만 순서를 고려한다.

C에서 Lex와 Yacc를 연결할 때에는 일반적으로 yyparse가 yylex를 호출하여 Token을 받는다. Lexer가 반환하는 Token 번호는 Parser의 정의와 일치해야 하므로 Yacc가 생성한 헤더를 사용하는 것이 자연스럽다. 이름이나 숫자처럼 실제 값도 전달하려면 yylval을 사용하고, 필요하면 줄과 열의 위치도 보존한다. Scanner 내부에서 재사용하는 문자열 버퍼를 그대로 가리키는 포인터를 장기간 보관한다면 수명 문제가 발생할 수 있다. 이 부분은 도구를 연결할 때 검토할 설계 사항이지 당시 구현이 정확히 어떤 방식이었는지를 단정하는 것은 아니다.

## 연산자 우선순위를 Grammar에 표현하기

재현 예제의 Grammar는 다음과 같이 구성했다. 내부 테이블 생성을 위한 Augmented Start Rule을 제외하면 Production은 여덟 개다.

```text
stmt   : NAME ASSIGN expr ;
expr   : expr PLUS term | term ;
term   : term STAR factor | factor ;
factor : NUMBER | NAME | LPAREN expr RPAREN ;
```

expr에서는 덧셈을, term에서는 곱셈을 처리하도록 계층을 나누었다. factor는 숫자와 이름, 괄호로 묶은 expr을 표현한다. 이렇게 구성하면 곱셈이 term 안에서 먼저 결합한 뒤 덧셈의 일부가 된다. 반복된 덧셈이나 곱셈은 왼쪽 재귀를 사용해 왼쪽부터 결합하도록 표현할 수 있다.

expr 하나에 덧셈과 곱셈을 모두 정의하는 방법도 있다. 하지만 expr PLUS expr과 expr STAR expr만 두면 입력에 따라 두 가지 이상의 결합 구조가 가능하다. 앞의 덧셈을 Reduce할지 다음 곱셈을 Shift할지 모호해지는 상황이다. Yacc의 연산자 우선순위와 결합 방향 선언으로 해결할 수도 있지만 여기서는 Grammar의 계층 자체가 결합 구조를 나타내도록 했다.

{{figure /figures/journals/pytokenizer-03-precedence.svg | 두 대입문의 실제 재현 Parsing 결과에서 Expression 부분만 비교했다. 괄호가 없으면 곱셈이 먼저 결합하고 괄호를 사용하면 구조가 달라진다.}}

실제로 재현 Parser가 반환한 구조를 읽기 쉽게 표현하면 다음과 같다.

```text
total = 2 + 3 * 4
(assign total (+ 2 (* 3 4)))

total = (2 + 3) * 4
(assign total (* (+ 2 3) 4))
```

숫자를 계산한 결과가 아니라 어떤 연산이 어떤 연산의 피연산자가 되는지를 확인한 것이다. 위 표현은 Semantic Tree를 간략하게 옮긴 것이며 모든 Grammar 노드를 포함하는 Derivation Tree는 아니다. 당시 PyTokenizer가 실제로 AST까지 구성했는지, 구문이 맞는지만 출력했는지는 남은 자료로 확인할 수 없다.

## Shift와 Reduce가 실제로 일어나는 순서

예제 입력의 구조가 왜 이렇게 결정되는지 보기 위해 재현 모델에서는 Grammar로부터 직접 SLR(1) 테이블을 만들었다. LR(0) Item은 Production 오른쪽에 점을 찍어 현재 어느 부분까지 인식했는지를 나타낸다. 점 다음에 Nonterminal이 있다면 해당 Nonterminal의 Production을 Closure에 추가하고, 특정 Symbol을 인식했을 때 점을 앞으로 옮겨 GOTO 상태를 계산한다. Augmented Start Rule에서 출발해 도달할 수 있는 Item Set을 각각의 Parser State로 삼았다.

Production의 끝까지 인식한 Item은 왼쪽 Nonterminal의 FOLLOW 집합에 해당하는 Lookahead에서 Reduce할 수 있다. Terminal에 대한 상태 전이는 Shift, Nonterminal에 대한 전이는 GOTO에 기록한다. 같은 ACTION 테이블 칸에 서로 다른 동작이 들어가려고 하면 충돌로 처리한다.

이번 Grammar에서는 실제로 **16개의 상태가 생성됐고 테이블 충돌은 0개**였다. 재현 방식은 SLR이며 Yacc에서 일반적으로 사용하는 LALR(1)과 테이블 생성 방식이 다르다. 따라서 여기에서 나오는 상태 번호와 상태 개수를 원래 Yacc 프로그램의 것으로 보면 안 된다.

{{figure /figures/journals/pytokenizer-02-shift-reduce.svg | 재현 SLR Parser에서 기록한 17개 동작 전체. 상태 번호는 이번에 생성한 테이블의 값이지 당시 Yacc의 상태 번호가 아니다.}}

대입문 하나를 분석할 때 실제로 17번의 동작이 일어났다. 처음 세 단계에서는 NAME, ASSIGN, NUMBER를 읽어 Shift한다. 그다음 PLUS를 Lookahead로 두고 NUMBER를 factor로, factor를 term으로, term을 expr로 Reduce한다. 이 세 단계 동안 PLUS는 아직 소비되지 않는다.

PLUS와 다음 NUMBER를 읽고 나면 11번째 동작에서 STAR를 Shift한다. 아직 앞의 덧셈 전체를 Reduce하지 않은 채로 곱셈을 완성하는 것이다. 14번째 단계에서 term STAR factor를 term으로 Reduce하고, 15번째에서 덧셈을, 16번째에서 대입문을 완성한다. 17번째 단계에서 stmt와 EOF를 확인하고 입력을 허용한다.

Shift는 입력을 읽고 다음 상태를 Stack에 추가하는 동작이다. Reduce는 Production 오른쪽에 있는 Symbol 및 상태를 Stack에서 꺼낸 뒤 왼쪽 Nonterminal로 바꾸고 GOTO 상태를 넣는 동작이다. 필요하다면 이 과정에서 Semantic Value를 구성할 수도 있다. Reduce 자체로 Lookahead를 소비하지 않기 때문에 읽은 Token의 개수와 Parser 동작 횟수가 같을 필요는 없다.

## Python의 들여쓰기는 공백 처리 이상의 문제다

대입문 하나를 분석할 때에는 공백을 전부 건너뛰어도 괜찮지만, Python의 실제 문법에서는 그렇지 않다. 중괄호 없이 들여쓰기로 블록의 경계를 나타내므로 Lexer에서 공백을 어떻게 Token으로 처리할 것인지가 중요하다.

```python
if ready:
    if valid:
        total = 1
    total = 2
total = 3
```

들여쓰기 Stack을 0으로 초기화한 뒤 더 깊게 들어가면 새로운 깊이를 Push하고 INDENT를 생성한다. 깊이가 줄어들면 기존 Stack에서 해당 깊이에 도달할 때까지 Pop하면서 DEDENT를 생성한다. 이전에 없던 깊이로 줄어들면 들여쓰기 오류다. 빈 줄이나 주석만 있는 줄, 괄호 안에서 이어지는 줄은 별도로 처리해야 하고 Tab과 물리적인 줄·논리적인 줄의 구분도 고려해야 한다.

{{figure /figures/journals/pytokenizer-04-indentation.svg | Python 표준 Tokenizer에서 확인한 2–5행의 INDENT·DEDENT와 들여쓰기 Stack. 재현 Grammar는 블록 구문을 처리하지 않는다.}}

위 코드는 Python 표준 라이브러리의 tokenize로 확인했다. 2, 3행에서 INDENT가 나오고 4, 5행에서 DEDENT가 나온다. 이 예시는 Python 형태의 Lexer에서 왜 상태를 기억해야 하는지 보여준다. 이번 대입문 SLR 모델은 블록 문법을 지원하지 않으며, 당시 PyTokenizer가 들여쓰기를 어느 범위까지 처리했는지도 확인된 자료는 없다.

## 정상 입력과 두 종류의 오류

정상적인 코드만 분석하는 경우에는 어휘 분석과 구문 분석이 제대로 분리되었는지 확인하기 어렵다. Token으로는 모두 읽을 수 있는데 문법에 맞지 않는 경우와, 아예 Scanner가 인식하지 못하는 문자가 들어오는 경우를 나누어 검사했다.

{{figure /figures/journals/pytokenizer-05-tests.svg | 재현 모델의 테스트 10개 실행 결과. 허용 4개, 구문 오류 5개, 어휘 오류 1개가 기대값과 일치했다. 2023년 원본 프로그램의 시험 결과는 아니다.}}

| 입력 | 기대값 및 실행 결과 |
| --- | --- |
| total = 2 + 3 * 4 | 허용 |
| total = (2 + 3) * 4 | 허용 |
| ifx = 7 | 허용 |
| x = y + 2 | 허용 |
| x = 1 + | 구문 오류 |
| x = * 2 | 구문 오류 |
| x == 1 | 구문 오류 |
| if = 1 | 구문 오류 |
| x = (2 + 3 | 구문 오류 |
| x = 2 @ 3 | 이 부분집합의 어휘 오류 |

x = 1 +는 모든 Token을 올바르게 읽을 수 있다. 하지만 Parser가 피연산자를 기다리는 상태에서 EOF가 나오므로 구문 오류다. x == 1 역시 EQ라는 정상적인 Token을 생성하지만 대입문에서는 ASSIGN을 기대하므로 허용하지 않는다. 마지막 입력의 @는 이번 Scanner의 규칙에 없으므로 어휘 오류로 처리한다. 실제 Python에서 @는 행렬곱 연산자이므로 이 결과를 Python 전체의 문법 판단으로 해석하면 안 된다.

열 가지 테스트 모두 기대했던 분류 결과와 일치했다. 최장 매치 예제의 네 Token, 두 Expression Tree, 테이블 충돌 여부, 들여쓰기 이벤트도 별도로 검증했다. 재현 코드는 [포트폴리오 저장소의 스크립트](https://github.com/Petooooo/Petooooo.github.io/blob/main/apps/web/scripts/build-pytokenizer-figures.py)에 남겼다. 저장소에서 Python 3로 실행하면 전체 Trace와 테스트 결과를 출력하고 분석용 도식 다섯 개를 다시 생성할 수 있다. 이 예제를 실행하는 데 Lex나 Yacc 바이너리는 필요하지 않다.

## 당시 구현을 돌아보며

2023년 프로젝트에서 C와 Lex/Yacc로 Python 코드를 Token으로 구분하고 구문을 분석하는 프로그램을 구현했다는 것은 기록으로 확인할 수 있다. 다만 정확한 Grammar의 범위와 Parser 상태 개수, 오류 복구 방식, 실제 출력 및 처리 성능까지 확인할 자료는 없다. 이번 재현 예제의 결과를 당시 프로그램의 시험 결과로 대체하지 않은 이유다.

지금 다시 구현한다면 우선 Lexer와 Parser 사이의 약속부터 명확히 정하고 싶다. Token 번호와 Semantic Value의 소유권, 소스의 위치 정보 등을 일관되게 전달하고 예약어와 식별자가 겹치는 경우나 연산자 경계부터 테스트할 것이다. 지원하는 문법의 범위를 정한 뒤 정상·비정상 입력을 함께 검사하는 것이 중요하다. 오류가 발생했을 때 어느 문자를 인식하지 못했는지, 어떤 Token을 기대했는지 구분해서 진단하고 오류 복구 과정과 정상적인 Parse 결과도 별도로 다뤄야 한다.

결국 이 프로젝트의 핵심은 소스 문자열을 어떤 표현으로 바꾸고 그 표현을 다음 단계에서 어떻게 사용할 것인지에 있었다. Lexer가 문장의 구조까지 전부 판단하게 만들거나 Parser가 다시 원래 문자열의 경계를 찾도록 만드는 대신, 두 단계의 역할을 명확히 하면 문법을 바꾸거나 기능을 추가할 때 어느 부분을 수정해야 하는지 파악하기 쉬워진다.

## 참고 자료 및 관련 프로젝트

- 프로젝트 CV, PyTokenizer 항목(2023년 10–11월): 개발 범위, 사용 언어와 프로젝트 설명.
- [Flex 매치 규칙](https://westes.github.io/flex/manual/Matching.html)
- [GNU Bison Parser Algorithm](https://www.gnu.org/software/bison/manual/html_node/Algorithm.html)
- [Python 3.12 언어 레퍼런스: Lexical Analysis](https://docs.python.org/3.12/reference/lexical_analysis.html)
- [FreeRTOS 멀티보드 Mini-Desktop](/projects/freertos-multiboard-mini-desktop/)
- [5단계 파이프라인 RISC CPU](/projects/risc-cpu-five-stage-pipeline/)
