#!/usr/bin/env python3
"""Native vector explanations of Langfuse's documented v3→v4 migration.
No private topology, logs, operational configuration, measured throughput or
timing is encoded. The existing evidence timeline is retained separately.
"""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'apps/web/public/figures/journals'
LO={}
def tx(x,y,e,k=None,sz=20,wt=500,anchor='start',color='#26394b'):
    LO.setdefault(e,e if k is None else k)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{sz}" font-weight="{wt}" text-anchor="{anchor}" fill="{color}">{html.escape(e)}</text>'
def box(x,y,w,h,fill='#f2f6fa',stroke='#b6c9d7',rx=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
def path(d,c='#7892a7',arrow=True,dash=False):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.4"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="7 5"' if dash else '')+'/>'
def node(x,y,w,h,e,k,sub,ksub,fill='#edf4fa'):
    return box(x,y,w,h,fill)+tx(x+w/2,y+30,e,k,22,700,'middle')+tx(x+w/2,y+58,sub,ksub,16,500,'middle')
def fig(name,e,k,sub,ksub,b,h):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7892a7"/></marker></defs>'
    s+=box(1,1,1118,h-2,'#fff','#c9d7e1',13)+box(24,27,6,49,'#28608d','#28608d',2)+tx(44,51,e,k,28,750)+tx(44,82,sub,ksub,17,color='#61758b')+path('M40 105H1080','#dce5ed',False)
    s+=b+path(f'M40 {h-38}H1080','#dce5ed',False)+tx(44,h-13,'Conceptual explanation of public migration semantics','공개 마이그레이션 동작을 설명한 개념도',14,color='#61758b')+'</svg>\n'
    p=DIR/(name+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
# Data transformation DAG: not a private cluster.
b=tx(48,143,'Legacy data','기존 데이터',20,700)+tx(422,143,'Temporary rewrite','임시 재정렬',20,700)+tx(840,143,'v4 event model','v4 이벤트 모델',20,700)
b+=node(48,167,265,81,'traces','traces','Trace-level attributes','Trace 단위 속성')
b+=node(48,300,265,81,'observations','observations','Child observations','하위 Observation')
b+=node(48,433,265,81,'Dataset run items','Dataset Run Item','Experiment relations','실험 관계')
b+=node(385,300,335,81,'Sorting scratch table','정렬용 임시 테이블','Project / trace / observation','Project / Trace / Observation','#fff3df')
b+=box(805,167,267,347,'#e8f4ed','#a5c5b1',9)+tx(938,205,'events_full','events_full',24,750,'middle')
for y,e,k,sub,ksub in [(227,'1 · Root spans','1 · Root Span','Virtual root for traces','Trace의 가상 Root'),(320,'3 · Child events','3 · 하위 Event','Join with trace fields','Trace 속성을 결합'),(413,'4 · Enrichment','4 · 실험 정보 보강','Experiment metadata','실험 메타데이터')]:
    b+=node(821,y,235,78,e,k,sub,ksub,'#fff')
b+=path('M313 207H755V266H821')+path('M313 340H385')+tx(348,324,'2','2',19,700,'middle')
b+=path('M720 340H821')+path('M313 231H350V283H770V359H821',dash=True)+path('M313 473H335V526H755V452H821')
b+=box(385,417,335,97,'#f4f6f9','#c7d4e0')+tx(405,449,'5 · Remove scratch','5 · 임시 테이블 정리',21,700)+tx(405,479,'After validation, separately gated','검증 후 별도 조건으로 실행',17)
b+=path('M552 381V417',dash=True)
fig('langfuse-v4-01-data-rewrite','A backfill changes the data model','백필을 통해 데이터 모델을 전환한다','Numbering refers to the five background migrations, not the upgrade guide sections','번호는 업그레이드 문서의 절이 아닌 백그라운드 마이그레이션 단계',b,572)
# Logical time coverage. Explicitly not a historical trace.
b=tx(48,145,'Illustrative coverage of old and new ingestion','기존·신규 데이터의 가상 커버리지',22,700)
x0,x1,x2,x3=235,480,700,1045
for x,e,k in [(x1,'Dual write active','Dual Write 시작'),(x2,'Backfill cutoff','백필 기준점')]:
    b+=path(f'M{x} 175V464','#a1b5c4',False,True)+tx(x,169,e,k,17,600,'middle')
b+=tx(48,229,'Historical copy','과거 데이터 복사',19,700)+box(x0,203,x2-x0,42,'#bed5e8','#a5becf',3)
b+=tx((x0+x2)/2,231,'Data before cutoff','기준점 이전 데이터',18,700,'middle')
b+=tx(48,298,'New write path','신규 기록 경로',19,700)+box(x1,272,x3-x1,42,'#b8dccc','#9ebfac',3)
b+=tx((x1+x3)/2,300,'Writes already reaching v4','v4에 이미 도달하는 기록',18,700,'middle')
b+=box(x1,343,x2-x1,50,'#dceee6','#9ebfac',3)+tx((x1+x2)/2,373,'Overlap','중첩 구간',18,700,'middle')
b+=tx(48,433,'Unsafe ordering','위험한 순서',19,700)+box(x0,407,x1-x0,41,'#bed5e8','#a5becf',3)+box(x1,407,x2-x1,41,'#f1ccc3','#c98d7c',3)+box(x2,407,x3-x2,41,'#b8dccc','#9ebfac',3)
b+=tx((x1+x2)/2,433,'Possible gap','누락 가능 구간',19,700,'middle','#973f32')
b+=tx(x1,470,'Cutoff first','백필 기준점 먼저',15,600,'middle')+tx(x2,470,'New path later','신규 경로 나중',15,600,'middle')
b+=tx(48,496,'Coverage matters more than the calendar order of deployments.','배포 날짜의 순서보다 데이터가 끊김 없이 포함되는지가 중요하다.',18,650)
fig('langfuse-v4-02-coverage','Why the backfill cutoff matters','백필 기준점이 중요한 이유','Logical time only; no actual timestamps, traffic volumes or cutover schedule','논리적 시간축 · 실제 시각, 트래픽, 전환 일정 아님',b,545)
# Layered validation: different evidence, different conclusions.
b=''
rows=[
 ('Request','요청','Timeout / success','Timeout / 성공','Response lifetime','응답 대기 시간'),
 ('Durable job','영속 작업','Phase + chunk counters','Phase + 청크 카운터','Recorded progress','기록된 작업 진행률'),
 ('Data engine','데이터 엔진','Writable replicas + capacity','쓰기 가능 Replica + 용량','Ability to write','쓰기 가능 여부'),
 ('Read model','조회 모델','Historical hierarchy + fields','과거 계층 구조 + 속성','Usability of sampled data','표본 데이터 사용 가능 여부'),
 ('New ingestion','신규 수집','New record → query','신규 기록 → 조회','End-to-end sampled path','표본 End-to-end 경로'),
]
b+=tx(54,143,'Layer','계층',18,700)+tx(290,143,'Evidence to examine','확인할 증거',18,700)+tx(737,143,'Meaning','판단 범위',18,700)
for i,(e,k,ev,kev,m,km) in enumerate(rows):
    y=161+i*62;b+=box(48,y,1024,54,'#f0f5f9' if i%2==0 else '#fff','#dbe4eb',3)+tx(64,y+33,e,k,20,700)+tx(290,y+33,ev,kev,19)+tx(737,y+33,m,km,18)
b+=box(48,493,1024,70,'#e8f4ed','#a6c6b4')+tx(68,522,'None of these alone proves complete historical parity.','어느 하나만으로 전체 과거 데이터의 정합성을 증명할 수 없다.',20,700)+tx(68,547,'Cleanup is a separate milestone after the applicable checks.','임시 구조의 정리는 필요한 검증 이후의 별도 단계다.',17)
fig('langfuse-v4-03-validation','Migration success has several evidence boundaries','마이그레이션 성공을 판단하는 여러 증거','Suggested validation matrix; not a record of every test performed','검증을 위한 판단 기준 · 모든 항목을 실행했다는 기록은 아님',b,611)
p=ROOT/'apps/web/i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
for k,v in LO.items():
    if k not in d:d[k]=v
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Generated three native SVGs; labels',len(LO))
