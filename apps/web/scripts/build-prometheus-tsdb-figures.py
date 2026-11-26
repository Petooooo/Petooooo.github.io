#!/usr/bin/env python3
"""Generate TSDB teaching diagrams and check a bounded replay model."""
from pathlib import Path
import html,json,itertools,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];D=R/'public/figures/journals';L={}
B='#e3edf6';G='#e0eee4';A='#f4e8ce';F='#f6dfda';INK='#253c51';M='#5e7387'
def t(x,y,e,k=None,s=20,w=500,a='start',c=INK):
 L.setdefault(e,k if k is not None else e)
 return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{s}" font-weight="{w}" text-anchor="{a}" fill="{c}">{html.escape(e)}</text>'
def r(x,y,w,h,fill=B,stroke='#a9bbc9'):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}"/>'
def p(d,dash=False):
 return f'<path d="{d}" fill="none" stroke="#7793a8" stroke-width="2" marker-end="url(#a)"'+(' stroke-dasharray="6 4"' if dash else '')+'/>'
def n(x,y,w,h,e,k,sub=None,ks=None,c=B):
 v=r(x,y,w,h,c)+t(x+w/2,y+(29 if sub else h/2+7),e,k,21,700,'middle')
 if sub:v+=t(x+w/2,y+54,sub,ks,16,500,'middle',M)
 return v
def fig(name,e,k,sub,ks,b,h):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,'Teaching model · not historical measurements','설명용 모델 · 당시 실측값 아님',14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# JSON-lines toy model, not the Prometheus WAL format.
def replay(block,raw,cutoff):
 refs=set();head={};incomplete=False
 for line in raw.splitlines(keepends=True):
  if not line.endswith('\n'):
   incomplete=True;break
  rec=json.loads(line)
  if rec['kind']=='series':refs.add(rec['ref']);continue
  if rec['ref'] not in refs:raise ValueError('unknown series')
  if rec['time']>=cutoff:head[(rec['ref'],rec['time'])]=rec['value']
 return {**block,**head},incomplete
block={(1,0):10,(1,1):11}
records=[{'kind':'series','ref':1}]+[{'kind':'sample','ref':1,'time':i,'value':10+i} for i in (1,2,3)]
raw=''.join(json.dumps(x)+'\n' for x in records)+'{"kind":'
out,tail=replay(block,raw,2)
assert out=={(1,i):10+i for i in range(4)} and tail
assert replay(block,'',2)==(block,False)
try:replay(block,json.dumps(records[-1])+'\n',2)
except ValueError:pass
else:raise AssertionError('unknown reference accepted')
assert len(list(itertools.product(range(10),range(4),range(5))))==200
assert 10*4*5*1000==200000
assert 32+8+7==47 and 47+4>50
print('PASS: replay cutoff, incomplete tail, log removal, unknown series, cardinality and storage arithmetic')
# 01
v=n(345,115,430,76,'Scraped samples','Scrape 샘플','Metric name + labels + time','메트릭 이름 + 라벨 + 시각')
v+=n(40,250,500,78,'Head series and active chunks','Head 시계열과 활성 Chunk','Recent mutable state','최근 변경 가능한 상태',G)+n(580,250,500,78,'Write-ahead log','Write-ahead Log','Series definitions and samples','시계열 정의와 샘플',A)
v+=p('M560 191V220H290V250')+p('M560 220H830V250')
v+=n(40,390,500,78,'Memory-mapped Head chunks','mmap Head Chunk','chunks_head/','chunks_head/')+p('M290 328V390')
v+=n(580,390,500,78,'Persistent TSDB blocks','영속 TSDB Block','Chunks / index / metadata','Chunk / Index / 메타데이터',G)+p('M540 429H580')
v+=t(40,515,'The WAL supports recovery; it is not the historical query index.','WAL은 복구용 기록이며 과거 데이터의 조회 Index가 아니다.',20,650)
fig('tsdb-01-ingest.svg','Recent state and persistent blocks','최근 상태와 영속 Block','Simplified server-mode ingestion; not an execution-order trace','Server Mode 수집 단순화 · 실제 실행 순서 기록 아님',v,565)
# 02
v=t(40,132,'Already compacted','이미 Block에 반영',21,700)+t(580,132,'Retained record stream','남은 기록',21,700)
v+=n(40,155,500,78,'Block: t = 0, 1','Block: t = 0, 1','Values 10, 11','값 10, 11',G)+n(580,155,500,78,'Series definition + samples','시계열 정의 + 샘플','t = 1, 2, 3 + incomplete tail','t = 1, 2, 3 + 불완전한 끝부분',A)
v+=p('M290 233V270H560V300')+p('M830 233V270H560')
v+=n(260,300,600,78,'Replay with cutoff t = 2','t = 2를 경계로 Replay','Skip t = 1; report incomplete tail','t = 1 제외 · 불완전한 끝부분 보고')
v+=p('M560 378V420')+n(40,420,1040,76,'Recovered view: 10, 11, 12, 13','복구한 조회 결과: 10, 11, 12, 13','Block data + reconstructed recent samples','Block 데이터 + 복원한 최근 샘플',G)
v+=t(40,545,'Without the log, this model retains only 10 and 11.','이 모델에서 Log가 없으면 10과 11만 남는다.',20,650)
fig('tsdb-02-replay.svg','Restart replay and time boundary','재시작 Replay와 시간 경계','Toy record model; not Prometheus binary WAL or repair behavior','간단한 기록 모델 · 실제 WAL 형식 및 복구 구현 아님',v,595)
# 03
for i,(e,k,sub,ks) in enumerate([('Before compaction','Compaction 이전','Source A + Source B','원본 A + 원본 B'),('During compaction','Compaction 진행','Sources remain + output grows','원본 유지 + 출력 증가'),('After successful commit','성공적인 완료 이후','New block; old sources retired','새 Block · 이전 원본 정리')]):
 y=115+i*142;v=(v if i else '')+t(40,y+27,e,k,21,700)+t(40,y+54,sub,ks,16,c=M)
 for j,(name,c) in enumerate([('Source A',B),('Source B',B),('New block',G)]):
  if (i==0 and j==2) or (i==2 and j<2):continue
  v+=n(450+j*210,y,195,68,name,{'Source A':'원본 A','Source B':'원본 B','New block':'새 Block'}[name],c=c)
v+=t(40,568,'Peak space includes overlapping input and output; WAL has its own lifecycle.','최대 사용량에는 입력과 출력이 겹친다. WAL의 생명주기는 별개다.',19,650)
fig('tsdb-03-compaction.svg','Compaction can temporarily increase disk usage','Compaction 중 디스크 사용량이 증가할 수 있다','Conceptual coexistence, not a measured timeline','원본과 결과가 공존하는 개념도 · 실측 시계열 아님',v,620)
# 04 budget
v=t(40,130,'Hypothetical 50 GiB filesystem','가상의 50 GiB 파일시스템',22,700)
x=40
for val,e,k,c in [(32,'Blocks','Block',B),(8,'WAL / Head','WAL / Head',A),(7,'Output','출력',G),(3,'Free','여유',F)]:
 w=1040*val/50;v+=r(x,155,w,65,c)+t(x+w/2,181,e,k,15,700,'middle')+t(x+w/2,202,str(val),s=16,w=700,a='middle');x+=w
v+=t(40,255,'47 GiB used; another 4 GiB exceeds the 50 GiB budget.','47 GiB 사용 · 4 GiB 추가 요청은 50 GiB 예산 초과.',20,650)
v+=t(40,332,'Series identities: possible combinations','시계열 식별자: 가능한 조합',22,700)
v+=n(40,360,500,80,'10 × 4 × 5 = 200','10 × 4 × 5 = 200','Host × operation × status','Host × Operation × Status')
v+=n(580,360,500,80,'200 × 1000 = 200,000','200 × 1000 = 200,000','Add request-ID values','Request ID 값 추가',A)
v+=t(40,490,'Cardinality is a possible upper bound, not a measured active-series count.','가능한 조합의 상한이며 실제 활성 시계열 수는 아니다.',19,650)
fig('tsdb-04-budget.svg','Disk headroom and label cardinality','디스크 여유 공간과 Label Cardinality','Independent hypothetical calculations; no historical usage inferred','독립적인 가상 계산 · 당시 사용량 추정 아님',v,540)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'4 native SVGs; {len(L)} labels')
