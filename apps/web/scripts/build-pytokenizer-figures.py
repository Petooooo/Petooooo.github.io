#!/usr/bin/env python3
"""Reproducible PyTokenizer article companion, November 2026.

NOT the 2023 project source. A small SLR(1) model illustrates Lex-style
longest-match scanning and Yacc-style bottom-up recognition. No dependencies.
The example only accepts one assignment containing +, *, names, integers
and parentheses. It does not implement Python or claim CPython compatibility.
"""
from collections import deque
from pathlib import Path
import re, json, io, tokenize, token, html, xml.etree.ElementTree as ET

GRAMMAR=[
    ('START',('stmt',)),
    ('stmt',('NAME','ASSIGN','expr')),
    ('expr',('expr','PLUS','term')),
    ('expr',('term',)),
    ('term',('term','STAR','factor')),
    ('term',('factor',)),
    ('factor',('NUMBER',)),
    ('factor',('NAME',)),
    ('factor',('LPAREN','expr','RPAREN')),
]
NONTERM={lhs for lhs,rhs in GRAMMAR}
TERM={x for _,rhs in GRAMMAR for x in rhs if x not in NONTERM}|{'EOF'}
# No nullable productions: FIRST only needs the first RHS symbol.
FIRST={x:{x} for x in TERM}
FIRST.update({x:set() for x in NONTERM})
FOLLOW={x:set() for x in NONTERM};FOLLOW['START'].add('EOF')
while True:
    changed=False
    for lhs,rhs in GRAMMAR:
        before=len(FIRST[lhs]);FIRST[lhs]|=FIRST[rhs[0]]
        changed|=len(FIRST[lhs])!=before
    if not changed:break
while True:
    changed=False
    for lhs,rhs in GRAMMAR:
        for i,x in enumerate(rhs):
            if x not in NONTERM:continue
            before=len(FOLLOW[x])
            FOLLOW[x]|=FIRST[rhs[i+1]] if i+1<len(rhs) else FOLLOW[lhs]
            changed|=len(FOLLOW[x])!=before
    if not changed:break
def closure(items):
    result=set(items)
    while True:
        nxt=set(result)
        for n,dot in result:
            rhs=GRAMMAR[n][1]
            if dot<len(rhs) and rhs[dot] in NONTERM:
                nxt.update((i,0) for i,(lhs,_) in enumerate(GRAMMAR) if lhs==rhs[dot])
        if nxt==result:return frozenset(nxt)
        result=nxt
def goto(items,x):
    return closure((n,d+1) for n,d in items if d<len(GRAMMAR[n][1]) and GRAMMAR[n][1][d]==x)
STATES=[closure([(0,0)])];trans={}
for i,state in enumerate(STATES):
    symbols=sorted({GRAMMAR[n][1][d] for n,d in state if d<len(GRAMMAR[n][1])})
    for x in symbols:
        target=goto(state,x)
        if target not in STATES:STATES.append(target)
        trans[i,x]=STATES.index(target)
ACTION={};GOTO={}
def put(key,value):
    if key in ACTION and ACTION[key]!=value:raise AssertionError(('SLR conflict',key,ACTION[key],value))
    ACTION[key]=value
for (i,x),j in trans.items():
    if x in NONTERM:GOTO[i,x]=j
    else:put((i,x),('shift',j))
for i,state in enumerate(STATES):
    for n,d in sorted(state):
        lhs,rhs=GRAMMAR[n]
        if d==len(rhs):
            if n==0:put((i,'EOF'),('accept',0))
            else:
                for la in FOLLOW[lhs]:put((i,la),('reduce',n))
RULES=[
    ('WS',r'[ \t]+'),('IF',r'if'),('EQ',r'=='),('ASSIGN',r'='),
    ('NAME',r'[A-Za-z_][A-Za-z_0-9]*'),('NUMBER',r'[0-9]+'),
    ('PLUS',r'\+'),('STAR',r'\*'),('LPAREN',r'\('),('RPAREN',r'\)'),
]
RULES=[(n,re.compile(p)) for n,p in RULES]
def scan(source):
    out=[];pos=0
    while pos<len(source):
        matches=[(m.end()-pos,-i,n,m.group()) for i,(n,r) in enumerate(RULES) if (m:=r.match(source,pos))]
        if not matches:raise ValueError(f'lexical error at column {pos+1}: {source[pos]!r}')
        size,_,n,s=max(matches);assert size>0
        if n!='WS':out.append((n,s,pos+1))
        pos+=size
    return out+[('EOF','',pos+1)]
def parse(source):
    try:tokens=scan(source)
    except ValueError as e:return {'status':'lexical error','error':str(e),'trace':[]}
    states=[0];symbols=[];values=[];i=0;trace=[]
    while True:
        n,s,col=tokens[i]
        action=ACTION.get((states[-1],n))
        row={'state':states[-1],'stack':' '.join(symbols) or '—','lookahead':n,'action':'error','detail':''}
        if not action:
            row['detail']=f'column {col}'
            trace.append(row)
            return {'status':'syntax error','error':f'column {col}: {n}','trace':trace}
        kind,arg=action;row['action']=kind
        if kind=='shift':
            row['detail']=f's{arg}';states.append(arg);symbols.append(n);values.append(s);i+=1
        elif kind=='reduce':
            lhs,rhs=GRAMMAR[arg];k=len(rhs);v=values[-k:]
            row['detail']=f'{lhs} → '+ ' '.join(rhs)
            if lhs=='stmt':node=('assign',v[0],v[2])
            elif len(rhs)==1:node=v[0]
            elif rhs[0]=='LPAREN':node=v[1]
            else:node=(v[1],v[0],v[2])
            del states[-k:];del symbols[-k:];del values[-k:]
            states.append(GOTO[states[-1],lhs]);symbols.append(lhs);values.append(node)
        else:
            row['detail']='START';trace.append(row)
            return {'status':'accepted','tree':values[-1],'trace':trace}
        trace.append(row)
EXAMPLE='total = 2 + 3 * 4'
CASES=[
    (EXAMPLE,'accepted'),('total = (2 + 3) * 4','accepted'),
    ('ifx = 7','accepted'),('x = y + 2','accepted'),
    ('x = 1 +','syntax error'),('x = * 2','syntax error'),
    ('x == 1','syntax error'),('if = 1','syntax error'),
    ('x = (2 + 3','syntax error'),('x = 2 @ 3','lexical error'),
]
def verify():
    assert [n for n,_,_ in scan('if ifx == =')]==['IF','NAME','EQ','ASSIGN','EOF']
    for source,want in CASES:
        result=parse(source);assert result['status']==want,(source,result)
    assert parse(EXAMPLE)['tree']==('assign','total',('+','2',('*','3','4')))
    assert parse('total = (2 + 3) * 4')['tree']==('assign','total',('*',('+','2','3'),'4'))
    return [dict(source=s,expected=e,actual=parse(s)['status']) for s,e in CASES]
# Use the standard-library Python tokenizer only as a reference for indentation.
INDENT_SOURCE='if ready:\n    if valid:\n        total = 1\n    total = 2\ntotal = 3\n'
def indent_events():
    return [(token.tok_name[t.type],t.start[0],len(t.string)) for t in tokenize.generate_tokens(io.StringIO(INDENT_SOURCE).readline) if t.type in (token.INDENT,token.DEDENT)]
ROOT=Path(__file__).resolve().parents[3];DIR=ROOT/'apps/web/public/figures/journals'
LO={}
def tx(x,y,en,ko=None,size=20,weight=500,anchor='start',color='#24384b'):
    LO.setdefault(en,en if ko is None else ko)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(en)}</text>'
def rect(x,y,w,h,fill='#fff',stroke='none',r=5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
def line(x,y,X,Y,c='#7893aa',sw=2):
    return f'<path d="M{x} {y}L{X} {Y}" stroke="{c}" stroke-width="{sw}" fill="none"/>'
def fig(slug,title,ko,sub,ksub,body,h):
    LO.setdefault(title,ko)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(title)}">'
    s+=rect(1,1,1118,h-2,'#fff','#d1dce6',12)+rect(25,26,6,50,'#2b608d')+tx(44,52,title,ko,28,750)+tx(44,82,sub,ksub,17,color='#61758b')+line(40,105,1080,105,'#dce5ed',1)
    s+=body+line(40,h-38,1080,h-38,'#dce5ed',1)+tx(44,h-13,'Reproducible 2026 companion · not an archived 2023 output','2026년 재현 예제 · 2023년 실행 결과 아님',14,color='#61758b')+'</svg>\n'
    p=DIR/(slug+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
def figures():
    results=verify();parsed=parse(EXAMPLE)
    # Token stream, exact lexemes and 1-based columns.
    b=rect(48,132,1024,70,'#f2f6fa','#c7d7e4',7)+tx(68,160,'Input','입력',16,700)+tx(68,188,EXAMPLE,size=24,weight=700)
    ts=scan(EXAMPLE);cw=122
    for i,(n,s,col) in enumerate(ts):
        x=48+i*129
        b+=rect(x,239,cw,104,'#e9f3fa','#9cb9cd',7)+tx(x+cw/2,268,n,size=17,weight=700,anchor='middle')+tx(x+cw/2,301,s or '∅',size=22,anchor='middle')+tx(x+cw/2,328,f'col {col}',f'열 {col}',15,anchor='middle',color='#61758b')
    b+=tx(48,385,'Longest match first; rule order breaks ties','가장 긴 매치 우선 · 길이가 같으면 규칙 순서',21,700)
    for x,text,n,ko in [(48,'if','IF','예약어'),(303,'ifx','NAME','식별자'),(558,'==','EQ','비교 연산자'),(813,'=','ASSIGN','대입 연산자')]:
        b+=rect(x,407,242,78,'#f4f8fa','#ccd9e3',6)+tx(x+14,435,text+' → '+n,size=22,weight=700)+tx(x+14,463,{'IF':'Keyword','NAME':'Identifier','EQ':'Comparison operator','ASSIGN':'Assignment operator'}[n],ko,16)
    fig('pytokenizer-01-token-stream','Lexeme, token class and source position','Lexeme, Token 종류와 소스 위치','Exact output from the companion scanner, with 1-based columns','재현 Scanner의 실제 출력 · 열 번호는 1부터 시작',b,540)
    # Trace every action, not only selected reductions. Group state/stack and lookahead.
    tr=parsed['trace'];y0=159;dy=35
    b=tx(48,140,'Step','단계',16,700)+tx(114,140,'State','상태',16,700)+tx(200,140,'Symbol stack before action','동작 전 Symbol Stack',16,700)+tx(650,140,'Lookahead','Lookahead',16,700)+tx(798,140,'Action / production','동작 / Production',16,700)
    for i,r in enumerate(tr):
        y=y0+i*dy;fill={'shift':'#edf4fa','reduce':'#edf7f1','accept':'#d8eadf','error':'#f7e3df'}[r['action']]
        b+=rect(45,y-2,1030,32,fill,r=2)+tx(54,y+21,str(i+1),size=16)+tx(122,y+21,str(r['state']),size=16)+tx(200,y+21,r['stack'],size=15)+tx(650,y+21,r['lookahead'],size=15)
        display={'shift':'Shift','reduce':'Reduce','accept':'Accept'}[r['action']]
        ko={'shift':'Shift','reduce':'Reduce','accept':'Accept'}[r['action']]
        b+=tx(798,y+21,display+' '+r['detail'],ko+' '+r['detail'],15,650)
    fig('pytokenizer-02-shift-reduce','Bottom-up parsing of one assignment','대입문 하나의 Bottom-up Parsing',f'{len(STATES)} generated SLR states · {len(tr)} recorded actions · zero table conflicts',f'생성된 SLR 상태 {len(STATES)}개 · 동작 {len(tr)}개 · 테이블 충돌 0개',b,y0+len(tr)*dy+47)
    # Exact structural trees, two forms of the expression.
    b=''
    def tree(x,y,paren=False):
        # Tree abstracted from the actual tuple; no numeric evaluation.
        title='(2 + 3) * 4' if paren else '2 + 3 * 4'
        b=rect(x,130,500,350,'#f5f8fb','#c9d7e2',8)+tx(x+250,165,title,size=23,weight=700,anchor='middle')
        points=[(x+250,220,'*' if paren else '+'),(x+125,302,'+' if paren else '2'),(x+375,302,'4' if paren else '*')]
        points += [(x+65,390,'2'),(x+185,390,'3')] if paren else [(x+315,390,'3'),(x+435,390,'4')]
        for a,z in [(0,1),(0,2),(1,3),(1,4)] if paren else [(0,1),(0,2),(2,3),(2,4)]:
            b+=line(points[a][0],points[a][1],points[z][0],points[z][1])
        for xx,yy,v in points:
            b+=rect(xx-28,yy-24,56,48,'#d9eaf6' if v in ('+','*') else '#fff','#91adc5',7)+tx(xx,yy+8,v,size=26,weight=700,anchor='middle')
        b+=tx(x+250,457,'Parentheses change the grouping' if paren else 'Multiplication is nested under addition','괄호가 결합 구조를 바꿈' if paren else '덧셈 아래에 곱셈이 결합됨',17,anchor='middle')
        return b
    b=tree(48,130)+tree(572,130,True)
    fig('pytokenizer-03-precedence','Grammar structure determines precedence','Grammar 구조가 연산자 우선순위를 결정한다','Expression trees extracted from the two successful companion parses','성공한 두 재현 Parsing 결과의 Expression Tree',b,530)
    # Indentation reference: the stack is calculated from Python tokenize events.
    events=indent_events();assert events==[('INDENT',2,4),('INDENT',3,8),('DEDENT',4,0),('DEDENT',5,0)],events
    b=tx(48,143,'Reference Python source','Python 참조 입력',20,700)+tx(650,143,'Indentation stack / emitted token','들여쓰기 Stack / 생성 Token',20,700)
    lines=INDENT_SOURCE.splitlines()
    stack=['[0]','[0, 4]','[0, 4, 8]','[0, 4]','[0]']
    names=['—','INDENT','INDENT','DEDENT','DEDENT']
    for i,s in enumerate(lines):
        y=166+i*65
        b+=rect(48,y,1024,54,'#f4f8fb' if i%2==0 else '#fff','#dce5ed',3)+tx(62,y+34,str(i+1),size=17,color='#61758b')
        spaces=len(s)-len(s.lstrip())
        b+=tx(96+spaces*19,y+34,s.lstrip(),size=21,weight=600)
        b+=tx(650,y+34,stack[i],size=20)+tx(910,y+34,names[i],size=18,weight=700)
    b+=tx(48,518,'Python tokenize reference; block syntax is not supported by the companion SLR grammar.','Python tokenize 참조 · 재현 SLR Grammar는 Block 구문을 지원하지 않음',18,700)
    fig('pytokenizer-04-indentation','Python indentation changes the token stream','Python 들여쓰기가 Token Stream을 바꾼다','Reference tokenizer events; stack levels follow source indentation','참조 Tokenizer 결과 · 소스 들여쓰기 깊이에 따른 Stack',b,574)
    # Test cases, exact classification (not historical results).
    b=tx(48,143,'Input','입력',19,700)+tx(690,143,'Observed result','실행 결과',19,700)+tx(970,143,'Match','일치',19,700)
    for i,r in enumerate(results):
        y=164+i*44;actual=r['actual']
        b+=rect(48,y,1024,39,'#edf7f1' if actual=='accepted' else '#faf0ea',r=3)+tx(63,y+26,r['source'],size=20)
        b+=tx(690,y+26,actual,{'accepted':'허용','syntax error':'구문 오류','lexical error':'어휘 오류'}[actual],19,700)+tx(987,y+26,'✓',size=20,weight=700,anchor='middle')
    fig('pytokenizer-05-tests','Accepted input and two kinds of rejection','정상 입력과 두 종류의 오류','Ten asserted cases executed by the companion scanner and SLR parser','재현 Scanner와 SLR Parser에서 실행한 테스트 10개',b,654)
    p=ROOT/'apps/web/i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
    for k,v in LO.items():
        if k not in d:d[k]=v
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':
    cases=verify();p=parse(EXAMPLE)
    print(json.dumps({'states':len(STATES),'conflicts':0,'tokens':scan(EXAMPLE),'trace':p['trace'],'tree':p['tree'],'cases':cases,'indent_events':indent_events()},ensure_ascii=False,indent=2))
    figures()
