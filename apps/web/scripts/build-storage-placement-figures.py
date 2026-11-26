#!/usr/bin/env python3
"""Storage placement teaching figures; exhaustive small failure-domain models."""
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
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,'Teaching model · not historical topology or measurements','설명용 모델 · 실제 배치 및 측정값 아님',14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# MODEL_START
from itertools import combinations
def subsets(xs):
 for i in range(len(xs)+1):
  yield from map(frozenset,combinations(xs,i))
def survive(layout,failed):
 return {m for m,copies in layout.items() if any(node not in failed for node in copies)}
concentrated={'A':('X','X'),'B':('Y','Y')}
spread={'A':('X','Z'),'B':('Y','W')}
nodes=('X','Y','Z','W')
outcomes={}
for failed in subsets(nodes):
 a=survive(concentrated,failed);b=survive(spread,failed)
 assert a==({'A'} if 'X' not in failed else set())|({'B'} if 'Y' not in failed else set())
 assert b==({'A'} if not {'X','Z'}<=failed else set())|({'B'} if not {'Y','W'}<=failed else set())
 outcomes[failed]=(a,b)
assert outcomes[frozenset({'X'})]==({'B'},{'A','B'})
assert outcomes[frozenset({'X','Z'})][1]=={'B'}
assert sum(len(a)==2 for a,b in outcomes.values())==4
assert sum(len(b)==2 for a,b in outcomes.values())==9
shards=('U','U','V','V','T','T')
for failed in subsets(('U','V','T')):
 remaining=sum(node not in failed for node in shards)
 assert (remaining>=4)==(len(failed)<=1)
assert [100,100*2,100*2*2,100*6//4]==[100,200,400,150]
print('PASS: 32 mirror-placement cases, 8 erasure-placement cases, 4 capacity checks; both layouts counted over the same four candidate nodes')
# MODEL_END
# 01 interfaces
v=t(40,132,'Consumer-facing interface','사용자 접근 인터페이스',21,700)+t(650,132,'Examples of backing storage','하위 저장소 예시',21,700)
for i,(e,k,a,ak,b,bk) in enumerate([('Block','Block','Logical block addresses','논리 블록 주소','Local device / replicated device','로컬 장치 / 복제 장치'),('File','File','Paths and file operations','경로와 파일 연산','Filesystem / network file service','파일시스템 / 네트워크 파일 서비스'),('Object','Object','Bucket and key API','Bucket 및 Key API','Object server and its storage','Object Server 및 하위 저장소')]):
 y=155+i*105;v+=n(40,y,540,78,e,k,a,ak)+p(f'M580 {y+39}H630')+n(630,y,450,78,b,bk,c=G)
v+=r(40,495,1040,74,A,'#c4aa77')+t(60,525,'Interface does not determine durability or failure independence.','접근 인터페이스만으로 내구성과 장애 독립성을 알 수 없다.',21,700)+t(60,550,'Kubernetes volumeMode: Filesystem or Block','Kubernetes volumeMode: Filesystem 또는 Block',17,c=M)
fig('placement-01-interfaces.svg','Storage interfaces and protection','저장소 접근 방식과 데이터 보호','Access semantics are separate from replication','접근 방식과 복제는 별개의 문제',v,620)
# 02 binding
v=n(40,115,500,76,'Pending PVC / first consumer','Pending PVC / 첫 Consumer','WaitForFirstConsumer','WaitForFirstConsumer')+n(580,115,500,76,'Scheduler constraints','Scheduler 배치 조건','CPU / affinity / topology','CPU / Affinity / Topology')+p('M540 153H580')
v+=n(260,250,600,76,'Provision and bind local PV','Local PV 생성 및 Binding','Example: node X, local directory','예시: X 노드의 로컬 경로',G)+p('M830 191V220H560V250')
v+=p('M560 326V365H290V400')+p('M560 365H830V400')
v+=n(40,400,500,76,'New Pod on node X','X 노드의 새 Pod','Existing PV location matches','기존 PV 위치와 일치',G)+n(580,400,500,76,'New Pod on node Y','Y 노드의 새 Pod','Existing PV location conflicts','기존 PV 위치와 충돌',F)
v+=t(40,525,'A new provisioner setting does not relocate the bytes of a bound PV.','새 Provisioner 설정은 Bound PV의 데이터를 이전하지 않는다.',20,650)
fig('placement-02-binding.svg','Local storage binding and placement','로컬 저장소 Binding과 배치','Delayed provisioning is not migration','Provisioning 지연은 데이터 이전이 아니다',v,575)
# 03 comparable footprint
v=t(40,132,'Illustrative stored payload (GiB)','가상 저장 Payload (GiB)',21,700)
for i,(e,k,a,c) in enumerate([('One copy','사본 1개',100,B),('Two database copies','DB 사본 2개',200,G),('Two DB × two block copies','DB 2개 × Block 사본 2개',400,A),('4+2 coded shards','4+2 Erasure Shard',150,B)]):
 y=165+i*84;v+=t(40,y+29,e,k,19,650)+r(390,y,590*a/400,46,c)+t(405+590*a/400,y+29,str(a),s=20,w=750)
v+=t(40,530,'Payload factors: 1× / 2× / 4× / 1.5×','Payload 배수: 1× / 2× / 4× / 1.5×',20,700)+t(40,559,'Different protection contracts; not measured write amplification.','보호 조건이 다른 예시 · 실제 쓰기 증폭 측정값 아님',19,c=M)
fig('placement-03-capacity.svg','Stored-copy cost versus write amplification','사본 용량 비용과 쓰기 증폭','100 GiB baseline; metadata, snapshots and temporary space excluded','100 GiB 기준 · 메타데이터, Snapshot, 임시 공간 제외',v,609)
# 04 failure domains
for row,(e,k,layout) in enumerate([('Concentrated','집중 배치',('A A','B B','—','—')),('Spread','분산 배치',('A','B','A','B'))]):
 y=140+row*155;v=(v if row else '')+t(40,y+30,e,k,21,700)
 for j,(node,val) in enumerate(zip(nodes,layout)):
  x=300+j*195;v+=n(x,y,180,78,'Node '+node,node+' 노드',val,val,F if node=='X' else G)
 v+=t(300,y+108,'After X fails: '+('only B survives' if row==0 else 'A and B survive'),'X 장애 이후: '+('B만 생존' if row==0 else 'A와 B 생존'),19,650)
v+=t(40,475,'Separate erasure example: six shards, two on each node','별도 Erasure 예시: Shard 6개, 노드마다 2개',21,700)
for i,node in enumerate(('U','V','T')):
 v+=n(40+i*355,500,330,76,'Node '+node,node+' 노드','2 shards','Shard 2개',F if i==0 else G)
v+=t(40,625,'Lose one node: 4 remain; lose two nodes: 2 remain. Need 4 to reconstruct.','노드 1개 손실: 4개 잔존 · 2개 손실: 2개 잔존 · 복원에는 4개 필요',19,650)
fig('placement-04-domains.svg','Equal copy counts, unequal failure outcomes','같은 사본 수, 다른 장애 결과','Complete current copies and ideal known erasures; not a quorum simulation','최신 사본 및 이상적인 누락 모델 · Quorum 실험 아님',v,675)
# 05 recovery ownership
v=t(40,132,'Workload or storage owner','워크로드 / 저장소 주체',21,700)+t(600,132,'Evidence before calling recovery complete','복구 완료 전에 확인할 증거',21,700)
rows=[('Local / unreplicated','Local / 미복제','Restore source and backing path','복구 원본 및 실제 경로'),('Replicated block volume','복제 Block Volume','Usable replicas and client I/O','사용 가능한 Replica 및 앱 I/O'),('Database replica','DB Replica','Role, lag, parts or oplog state','Role, Lag, Part 또는 Oplog'),('Object erasure set','Object Erasure Set','Read / write quorum and integrity','읽기·쓰기 Quorum 및 무결성'),('Monitoring / search','모니터링 / 검색','Expected history or reindex source','과거 데이터 또는 재수집 원본')]
for i,(e,k,a,ak) in enumerate(rows):
 y=155+i*79;v+=n(40,y,500,65,e,k)+p(f'M540 {y+32}H580')+n(580,y,500,65,a,ak,c=G)
v+=r(40,570,1040,70,A,'#c4aa77')+t(60,611,'Independent, tested restore points are still required for protected data.','보호할 데이터에는 별도로 검증된 복구 지점이 필요하다.',21,650)
fig('placement-05-recovery.svg','Recovery contracts by workload','워크로드별 복구 기준','Different recovery owners need different evidence','복구 주체에 따라 필요한 증거가 다르다',v,690)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'5 native SVGs; {len(L)} labels')
