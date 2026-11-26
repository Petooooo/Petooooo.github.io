#!/usr/bin/env python3
"""Longhorn V1 explanatory figures and bounded sparse-block model."""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];D=R/'public/figures/journals';L={}
INK='#253c51';M='#5e7387';B='#e3edf6';G='#e0eee4';A='#f4e8ce';F='#f6dfda'
def t(x,y,e,k=None,s=20,w=500,a='start',c=INK):
 L.setdefault(e,k if k is not None else e)
 return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{s}" font-weight="{w}" text-anchor="{a}" fill="{c}">{html.escape(e)}</text>'
def r(x,y,w,h,fill=B,stroke='#a9bbc9',rx=7):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def p(d,arrow=True,dash=False):
 return f'<path d="{d}" fill="none" stroke="#7793a8" stroke-width="2"'+(' marker-end="url(#a)"' if arrow else '')+(' stroke-dasharray="6 4"' if dash else '')+'/>'
def n(x,y,w,h,e,k,sub=None,ks=None,c=B):
 b=r(x,y,w,h,c)+t(x+w/2,y+(29 if sub else h/2+7),e,k,21,700,'middle')
 if sub:b+=t(x+w/2,y+54,sub,ks,16,500,'middle',M)
 return b
def fig(name,e,k,sub,ks,b,h,footer=('Conceptual V1 model · not a historical volume inventory','V1 설명용 모델 · 당시 Volume 구성 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Pure sparse-block lookup; not the Longhorn image format or purge implementation.
base={0:'A',1:'B',2:'C'};mid={1:'B1'};head={2:'C2'}
def visible(layers):
 out={}
 for layer in layers:out.update(layer)
 return tuple(out[i] for i in range(3))
assert visible([base,mid,head])==('A','B1','C2')
assert visible([base,head])==('A','B','C2')
merged={**mid,**head}
assert visible([base,merged])==visible([base,mid,head])
# Also verify newer writes always win over a coalesced older block.
for mask1 in range(8):
 for mask2 in range(8):
  old={i:f'old{i}' for i in range(3) if mask1>>i&1}
  new={i:f'new{i}' for i in range(3) if mask2>>i&1}
  assert visible([base,old,new])==visible([base,{**old,**new}])
assert round(4*1024**2/100/3600,2)==11.65
assert round(4*1024**2/50/3600,2)==23.30
print('PASS: sparse lookup, unsafe deletion counterexample, coalescing, 64 layer pairs, rebuild-time arithmetic')
# 01: data path and control ownership
v=n(40,115,330,75,'Longhorn Manager','Longhorn Manager','Reconcile custom resources','Custom Resource 조정',A)
v+=n(40,250,330,75,'Instance Manager','Instance Manager','Supervise local processes','로컬 Process 관리',A)+p('M205 190V250',True,True)
v+=n(470,115,610,75,'Application / filesystem','애플리케이션 / 파일시스템','Volume frontend','Volume Frontend')+n(470,250,610,75,'Engine process','Engine Process','Coordinate replicated I/O','복제 I/O 조정',G)+p('M775 190V250')
v+=p('M370 288H470',True,True)
v+=n(470,390,290,76,'Replica A (RW)','Replica A (RW)','Participating copy','I/O 참여 복제본',G)+n(790,390,290,76,'Replica B (RW)','Replica B (RW)','Participating copy','I/O 참여 복제본',G)
v+=p('M775 325V355H615V390')+p('M775 355H935V390')
v+=n(470,520,290,72,'Disk files A','Disk File A','Head and snapshots','Head 및 Snapshot')+n(790,520,290,72,'Disk files B','Disk File B','Head and snapshots','Head 및 Snapshot')+p('M615 466V520')+p('M935 466V520')
v+=r(40,390,330,202,'#f2f6fa','#c4d3df')+t(60,425,'Dashed: supervision','점선: Process 관리',19,700)+t(60,461,'Solid: I/O path','실선: I/O 경로',19,700)+t(60,505,'Each replica also has','각 Replica에도',17)+t(60,529,'a local process owner.','로컬 관리 주체가 있다.',17)
fig('lh-01-engine-path.svg','Engine, replicas and process supervision','Engine, Replica와 Process 관리','Illustrative V1 single-writer block volume','V1 단일 Writer 블록 Volume 예시',v,645)
# 02: independent axes
v=t(40,130,'State dimension','상태 항목',21,700)+t(395,130,'Examples','예시',21,700)
rows=[('Volume robustness','Volume Robustness','Healthy / Degraded / Faulted','Healthy / Degraded / Faulted'),('Attachment','Attachment','Attached / Detached / Detaching','Attached / Detached / Detaching'),('Process lifecycle','Process 생명주기','Running / Stopping / Stopped','Running / Stopping / Stopped'),('Engine replica mode','Engine Replica Mode','RW / WO / ERR','RW / WO / ERR')]
for i,(e,k,a,ak) in enumerate(rows):
 y=151+i*71;v+=r(40,y,1040,62,'#f2f6fa','#c4d3df',5)+t(55,y+39,e,k,20,700)+t(395,y+39,a,ak,20,600)
v+=t(40,475,'Example: desired count = 2, active engine','예시: 목표 2개, 활성 Engine',21,700)
v+=n(40,495,500,78,'Replica A: RW','Replica A: RW','Usable read/write source','읽기·쓰기 가능한 원본',G)+n(580,495,500,78,'Replica B: WO','Replica B: WO','Rebuild not yet complete','재구축 미완료',A)
v+=t(40,620,'An object count is not a count of current, usable copies.','객체 수가 최신 상태의 사용 가능한 복제본 수는 아니다.',19,650)
fig('lh-02-state-dimensions.svg','Separate state dimensions','서로 다른 상태 항목','Illustrative states, not an observed mode map','상태 예시 · 실제 Engine Mode 기록 아님',v,668)
# 03: actual tested model
v=t(40,130,'Layer / lookup order','Layer 및 조회 순서',21,700)
for j in range(3):v+=t(500+j*185,130,f'Block {j}',f'블록 {j}',20,700,'middle')
for i,(e,k,vals) in enumerate([('Writable head','쓰기 Head',('—','—','C2')),('Snapshot layer','Snapshot Layer',('—','B1','—')),('Base layer','Base Layer',('A','B','C'))]):
 y=151+i*81;v+=r(40,y,1040,67,'#f2f6fa','#c4d3df',5)+t(60,y+42,e,k,21,700)
 for j,val in enumerate(vals):
  v+=r(425+j*185,y+7,150,53,G if val!='—' else '#fff','#c4d3df',4)+t(500+j*185,y+42,val,s=21,w=700,a='middle')
v+=n(40,415,1040,70,'Visible blocks: A, B1, C2','읽기 결과: A, B1, C2',c=G)
v+=n(40,520,500,76,'Drop middle layer','중간 Layer 제거','Wrong result: A, B, C2','잘못된 결과: A, B, C2',F)+n(580,520,500,76,'Preserve unshadowed blocks','덮이지 않은 블록 보존','Correct result: A, B1, C2','올바른 결과: A, B1, C2',G)
fig('lh-03-snapshot-chain.svg','Sparse snapshot dependencies','Sparse Snapshot 의존 관계','Simplified in-memory lookup and coalescing model','메모리 내 조회 및 병합 개념 모델',v,650,('64 layer pairs verified · no Longhorn image manipulation','Layer 조합 64개 검증 · 실제 Longhorn Image 조작 없음'))
# 04 rebuild and hypothetical time
v=t(40,130,'Rebuild gate','재구축 단계',21,700)+t(600,130,'What must be true','필요한 조건',21,700)
for i,(e,k,a,ak) in enumerate([('Eligible source and destination','정상 원본 및 적절한 대상','Capacity and scheduling','용량 및 스케줄링'),('Attach for offline rebuild','Offline Rebuild용 Attach','Detached degraded volume','Detached Degraded Volume'),('Add target in WO mode','WO Mode 대상 추가','Establish snapshot reference','Snapshot 기준점 설정'),('Synchronize snapshot data','Snapshot 데이터 동기화','Coordinate concurrent writes','동시 쓰기 조정'),('Promote to RW after success','성공 후 RW로 전환','Verify usable replica set','사용 가능한 Replica 확인')]):
 y=151+i*75;v+=n(40,y,510,62,e,k,c=G if i==4 else B)+p(f'M550 {y+31}H580')+n(580,y,500,62,a,ak)
 if i<4:v+=p(f'M295 {y+62}V{y+75}')
v+=r(40,552,1040,92,A,'#c4aa77')+t(60,581,'Illustrative transfer of 4 TiB','가상의 4 TiB 전송',20,700)+t(60,618,'100 MiB/s ≈ 11.65 h','100 MiB/s ≈ 11.65시간',20,650)+t(580,618,'50 MiB/s ≈ 23.30 h','50 MiB/s ≈ 23.30시간',20,650)
fig('lh-04-rebuild.svg','Rebuilding is not just a setting','설정 활성화와 실제 재구축은 다르다','Simplified V1 sequence; transfer time is a hypothetical lower-bound example','V1 절차 단순화 · 전송 시간은 가상 계산 예시',v,694)
# 05 teardown evidence separated from historical errors.
v=t(40,130,'Ownership boundary','관리 주체의 경계',21,700)+t(600,130,'Evidence to verify','확인할 증거',21,700)
rows=[('Consumer / writer','사용자 / Writer','Quiescence and fencing','쓰기 중단 및 차단'),('CSI publication / staging','CSI Publication / Staging','Mount and device references','Mount 및 장치 참조'),('Attachment reconciliation','Attachment 상태 조정','Request and ticket ownership','요청과 Ticket의 관리 주체'),('Instance lifecycle','Instance 생명주기','Process exit and socket owners','Process 종료 및 Socket 사용 주체'),('Safe reattachment','안전한 재연결','Replica set and application data','Replica 구성 및 앱 데이터')]
for i,(e,k,a,ak) in enumerate(rows):
 y=151+i*72;v+=n(40,y,510,61,e,k)+p(f'M550 {y+30}H580')+n(580,y,500,61,a,ak,c=G if i==4 else B)
v+=r(40,532,1040,106,F,'#d1a69d')+t(60,562,'Recorded separately','별도 기록',21,700)+t(60,591,'Unregister rejected: stopping, not stopped','Unregister 거부: stopping 상태',19,650)+t(60,618,'Later observations: port in use; busy globalmount','이후 별도 관측: Port 사용 중, Busy globalmount',18,c=M)
fig('lh-05-detach-gates.svg','Detachment requires ownership evidence','Detach에는 사용 주체의 증거가 필요하다','Evidence boundaries; not a universal CSI operation order','검증 경계 · 모든 CSI의 고정 순서 아님',v,688)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'5 native SVGs; {len(L)} labels')
