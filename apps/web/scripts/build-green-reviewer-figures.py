#!/usr/bin/env python3
"""Green Reviewer analytical figures, grounded in public source commit
2a3f1328e1beb083aa2de33d0fd4d02bc53c07a6. All numerical examples are synthetic.
Original screenshot copies are managed separately; this generator draws only
explanatory vectors, not substitute UI captures.
"""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]; DIR=ROOT/'apps/web/public/figures/journals'; LO={}
def t(x,y,en,ko=None,size=19,weight=500,anchor='start',color='#24384b'):
    LO.setdefault(en,ko or en)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(en)}</text>'
def r(x,y,w,h,fill='#fff',stroke='none',rx=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
def line(x,y,X,Y,arrow=True,c='#7390a5'):
    return f'<path d="M{x} {y}L{X} {Y}" stroke="{c}" stroke-width="2" fill="none"'+(' marker-end="url(#a)"' if arrow else '')+'/>'
def node(x,y,w,h,en,ko,sub,ksub,fill='#eef4f8'):
    return r(x,y,w,h,fill,'#adc0cf',8)+t(x+w/2,y+31,en,ko,21,700,'middle')+t(x+w/2,y+58,sub,ksub,16,500,'middle')
def fig(name,title,ko,sub,ksub,b,h):
    LO.setdefault(title,ko)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(title)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7390a5"/></marker></defs>'
    s+=r(1,1,1118,h-2,'#fff','#d0dce6',12)+r(24,26,6,51,'#286a57',rx=2)+t(44,52,title,ko,27,750)+t(44,82,sub,ksub,17,color='#61758b')+line(40,105,1080,105,False,'#dce5ed')+b
    s+=line(40,h-38,1080,h-38,False,'#dce5ed')+t(44,h-13,'Source-derived explanation · 2023 project, not live telemetry','2023년 소스 기반 설명 · 실시간 운영 지표 아님',14,color='#61758b')+'</svg>\n'
    p=DIR/(name+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
# Architecture: actual distinct pathways, not every connection in a single chain.
b=node(45,150,210,90,'Flutter','Flutter','Web / mobile','웹 / 모바일')+node(310,150,220,90,'FacadeServer','FacadeServer','Public API boundary','클라이언트 API 경계')+node(585,150,235,90,'ConversionServer','ConversionServer','Search + aggregation','검색 변환 + 집계')+node(585,300,235,90,'DatabaseServer','DatabaseServer','SQL access','SQL 접근')+node(875,300,200,90,'MySQL','MySQL','Three tables','테이블 3개','#e8f3ee')
b+=line(255,195,310,195)+line(530,195,585,195)+line(703,240,703,300)+line(820,345,875,345)
b+=f'<path d="M420 240V345H585" stroke="#7390a5" stroke-width="2" fill="none" marker-end="url(#a)"/>'+t(434,329,'Review reads','리뷰 조회',16)
b+=node(45,438,210,80,'Python crawler','Python Crawler','Shopping metadata','상품 정보')+node(310,438,220,80,'JSON files','JSON 파일','Category / product ID','카테고리 / 상품 ID')+node(585,438,235,80,'JSON uploader','JSON Uploader','Initial catalog import','상품 초기 적재')
b+=line(255,478,310,478)+line(530,478,585,478)+f'<path d="M820 478H975V390" stroke="#7390a5" stroke-width="2" fill="none" marker-end="url(#a)"/>'
fig('green-reviewer-01-architecture','Two data paths through the application','서비스의 두 가지 데이터 경로','Interactive requests above; separate catalog ingestion below','위는 사용자 요청 경로 · 아래는 별도의 상품 적재 경로',b,577)
# DP from the exact recurrence; ASCII example for legibility.
a,bword='cup','cups'
D=[[0]*(len(bword)+1) for _ in range(len(a)+1)]
for i in range(len(a)+1):D[i][0]=i
for j in range(len(bword)+1):D[0][j]=j
for i in range(1,len(a)+1):
 for j in range(1,len(bword)+1):D[i][j]=min(D[i-1][j]+1,D[i][j-1]+1,D[i-1][j-1]+(a[i-1]!=bword[j-1]))
assert D[-1][-1]==1
b=t(48,145,'Search word: cup','검색어: cup',20,700)+t(48,177,'Candidate: cups','후보: cups',20)
for j,c in enumerate(['∅']+list(bword)):b+=t(148+78*j,222,c,size=21,anchor='middle',weight=700)
for i,c in enumerate(['∅']+list(a)):
    b+=t(58,270+i*60,c,size=20,weight=700)
    for j,v in enumerate(D[i]):
        x=113+j*78;y=239+i*60
        b+=r(x,y,70,53,'#c8e3d3' if i==len(a) and j==len(bword) else '#f2f6f9','#c6d5e1',3)+t(x+35,y+34,str(v),size=22,anchor='middle',weight=700)
b+=node(580,180,485,88,'Edit distance = 1','편집 거리 = 1','Insert one character','문자 하나 삽입')
b+=node(580,291,485,88,'Similarity = 1 − 1/4 = 0.75','유사도 = 1 − 1/4 = 0.75','Normalized by the longer string','더 긴 문자열 길이로 정규화','#e8f3ee')
b+=t(580,426,'Pick the highest strictly positive similarity.','양수인 유사도 중 가장 높은 후보를 선택한다.',18,650)
b+=t(580,455,'A tie keeps the earlier candidate.','동점이면 먼저 확인한 후보가 유지된다.',18)
fig('green-reviewer-02-search','Mapping a search word to a catalog keyword','검색어를 상품 카테고리로 변환','Illustrative matrix using the original Transformer recurrence','원본 Transformer 점화식을 사용한 설명용 행렬',b,540)
# ERD actual columns, public safe fields only.
b=node(386,155,348,82,'itemTable','itemTable','PK id · category · product metadata','PK id · 카테고리 · 상품 정보','#e8f3ee')
b+=r(386,255,348,108,'#f3f7fa','#c5d2df',6)+t(406,284,'Stored aggregate','저장된 집계값',20,700)+t(406,314,'reviewer · checklists',size=20)+t(406,343,'Count + four sums','리뷰 수 + 네 가지 합계',17)
b+=node(48,421,330,89,'detailpicTable','detailpicTable','FK_itemTable → itemTable.id','FK_itemTable → itemTable.id')
b+=node(742,421,330,89,'reviewTable','reviewTable','FK_itemTable → itemTable.id','FK_itemTable → itemTable.id')
b+=f'<path d="M386 196H213V421M734 196H907V421" fill="none" stroke="#7390a5" stroke-width="2" marker-end="url(#a)"/>'
b+=t(232,273,'1 : many','1 : 다수',18)+t(925,273,'1 : many','1 : 다수',18)
b+=t(213,539,'Image URLs','상세 이미지 URL',18,anchor='middle')+t(907,539,'Four flags + review text','네 가지 체크 + 리뷰 내용',18,anchor='middle')
fig('green-reviewer-03-data','Product identity and review aggregates','상품 식별자와 리뷰 집계','Three tables in the retained MySQL initialization SQL','원본 MySQL 초기화 SQL의 테이블 세 개',b,594)
# Score and donuts use the same counts but different denominators.
S=[4,3,2,1];n=5;total=sum(S);risk=total/(4*n)
assert risk==.5
b=t(48,144,'Hypothetical product · 5 reviews','가상 상품 · 리뷰 5개',22,700)
for i,(en,ko,c) in enumerate([('No proof','증거 불충분','#76b6a2'),('Improper label','부적절한 인증 라벨','#e7ae69'),('Vague claim','애매모호한 주장','#98a9d8'),('False claim','거짓말','#d8c970')]):
    y=169+i*56;b+=t(48,y+24,en,ko,19)+r(290,y,250,32,'#edf1f5',rx=3)+r(290,y,S[i]*50,32,c,rx=3)+t(555,y+23,str(S[i]),size=20,weight=700)
b+=t(48,417,'Card score = 10 / (4 × 5) = 0.50','카드 점수 = 10 / (4 × 5) = 0.50',22,700)
x=48;y=451;W=1024
for start,end,c in [(0,.25,'#85bd9c'),(.25,.6,'#eac66e'),(.6,1,'#d8837a')]: b+=r(x+W*start,y,W*(end-start),38,c,rx=0)
for v in [0,.25,.6,1]:b+=t(x+W*v,y+62,f'{v:g}',size=17,anchor='middle')
b+=line(x+.5*W,y-16,x+.5*W,y+38,False,'#24384b')+t(x+.5*W,y-23,'0.50',size=19,weight=700,anchor='middle')
b+=r(650,150,421,234,'#f4f8fb','#c8d6e1',8)+t(670,184,'Donut chart denominator','도넛 차트의 분모',21,700)+t(670,218,'Sum of selected flags = 10','선택된 체크 합계 = 10',18)+t(670,250,'40% · 30% · 20% · 10%',size=24,weight=700)
b+=t(670,294,'Different from the card score.','카드 점수와 다른 값이다.',18)+t(670,326,'No reviews → grey; no flags → empty donut.','리뷰 없음 → 회색 · 체크 없음 → 빈 도넛',16)
fig('green-reviewer-04-score','Two visual encodings of the same review counts','같은 리뷰 집계의 두 가지 시각화','Synthetic example from fetchProducts and DonutChart','fetchProducts와 DonutChart의 계산을 적용한 가상 예시',b,565)
# Write pipeline and lost update scenario.
b=t(48,143,'Recorded write path','원본 리뷰 등록 경로',22,700)
for i,(en,ko,sub,ksub) in enumerate([('Read old sums','기존 합계 조회','Product detail','상품 상세'),('Insert review','리뷰 삽입','Review row','리뷰 행'),('Count reviews','리뷰 수 조회','COUNT(*)','COUNT(*)'),('Update product','상품 집계 갱신','New sums + count','새 합계 + 리뷰 수')]):
 x=48+260*i;b+=node(x,167,234,84,en,ko,sub,ksub)
 if i<3:b+=line(x+234,209,x+260,209)
b+=t(48,310,'Hypothetical concurrent writers','가상의 동시 등록',22,700)
b+=node(48,334,235,85,'A reads S = 3','A: S = 3 조회','Adds one flag','체크 하나 추가')+node(48,444,235,85,'B reads S = 3','B: S = 3 조회','Adds one flag','체크 하나 추가')
b+=node(370,334,250,85,'A writes S = 4','A: S = 4 저장','After its insert','리뷰 삽입 이후')+node(370,444,250,85,'B writes S = 4','B: S = 4 저장','Stale initial sum','오래된 초기 합계')
b+=line(283,376,370,376)+line(283,486,370,486)
b+=r(700,350,372,160,'#f7e8e1','#ccab99',8)+t(720,386,'Expected sum: 5','기대 합계: 5',24,700)+t(720,428,'Possible stored sum: 4','저장 가능 합계: 4',24,700)+t(720,473,'Use an atomic DB transaction.','DB 트랜잭션으로 원자적 처리 필요',18)
b+=line(620,376,700,393)+line(620,486,700,463)
fig('green-reviewer-05-review-update','Review writes and aggregate consistency','리뷰 등록과 집계 일관성','Original multi-request sequence; illustrative lost-update scenario','원본 다중 요청 순서 · 갱신 손실 가상 예시',b,580)
p=ROOT/'apps/web/i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
for k,v in LO.items():
 if k not in d:d[k]=v
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Five source-derived SVGs generated; labels:',len(LO))
