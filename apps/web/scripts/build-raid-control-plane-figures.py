#!/usr/bin/env python3
"""Generate RAID and consensus diagrams with bounded algebraic checks."""
from pathlib import Path
import html,json,itertools,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Conceptual model · not a historical device inventory','설명용 모델 · 당시 장치 구성의 실측값 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Known erasure reconstruction; no actual RAID devices involved.
def xor(a,b):
 assert len(a)==len(b)
 return bytes(x^y for x,y in zip(a,b))
a=bytes((i*17+3)%256 for i in range(4096));b=bytes((i*31+7)%256 for i in range(4096));stripe=[a,b,xor(a,b)]
def recover(parts):
 missing=[i for i,x in enumerate(parts) if x is None]
 if len(missing)!=1:raise ValueError('exactly one known erasure required')
 out=list(parts);known=[x for x in out if x is not None];out[missing[0]]=xor(*known)
 return out
for i in range(3):
 parts=list(stripe);parts[i]=None;assert recover(parts)==stripe
try:recover([None,None,stripe[2]])
except ValueError:pass
else:raise AssertionError('two erasures accepted')
damaged=bytes([a[0]^1])+a[1:];assert xor(damaged,b)!=stripe[2]
counts={}
for N in (3,4,5):
 q=N//2+1;good=[];total=0
 for bits in itertools.product((False,True),repeat=N):
  total+=1;available=sum(bits)
  eligible=available>=q
  assert eligible==(2*available>N)
  if eligible:good.append(N-available)
 assert max(good)==N-q
 counts[N]=total
assert sum(counts.values())==56
print('PASS: 3 single-block reconstructions, two-erasure rejection, altered-block mismatch, 56 majority-subset checks')
# 01 local and distributed domains.
v=r(40,115,510,385,'#f2f6fa','#c4d3df')+t(60,148,'Local storage domain','로컬 저장 영역',22,700)
v+=n(60,170,215,67,'Member disk A','구성 디스크 A')+n(315,170,215,67,'Member disk B','구성 디스크 B')
v+=n(60,275,470,75,'MD block device','MD Block Device','Logical blocks / redundancy','논리 블록 / 중복성',G)+p('M167 237V255H295V275')+p('M422 237V255H295')
v+=n(60,400,470,75,'Filesystem and WAL','파일시스템과 WAL','Durable write path','영속 쓰기 경로',A)+p('M295 350V400')
v+=r(590,115,490,385,'#f2f6fa','#c4d3df')+t(610,148,'Consensus domain','합의 영역',22,700)
v+=n(610,170,450,75,'Voting member','투표 멤버','One vote, not one vote per disk','디스크 수와 관계없이 하나의 Vote',G)
v+=n(610,280,450,75,'Raft majority','Raft 과반수','Reachable voting members','통신 가능한 투표 멤버')+p('M835 245V280')
v+=n(610,400,450,75,'Kubernetes API','Kubernetes API','State access and reconciliation','상태 접근 및 Reconciliation')+p('M835 355V400')
v+=p('M530 437H570V207H610',True,True)
v+=t(40,548,'Local redundancy and cluster availability have different failure boundaries.','로컬 중복성과 클러스터 가용성은 장애 경계가 다르다.',20,650)
fig('raid-01-layer-boundaries.svg','Storage redundancy versus consensus','저장장치 중복성과 클러스터 합의','Illustrative layers; dashed path is a dependency, not proven incident causality','가상 계층 · 점선은 의존성이지 당시 인과관계가 아님',v,598)
# 02 mirror and stripe.
v=t(40,135,'Two-way mirror','두 장치 Mirror',22,700)
v+=n(40,155,500,76,'Disk A: data X','디스크 A: 데이터 X',c=G)+n(580,155,500,76,'Disk B: copy of X','디스크 B: X의 복사본',c=G)
v+=t(40,273,'Three-member single-parity stripe','세 장치의 단일 Parity Stripe',22,700)
for i,(e,k,c) in enumerate([('A','A',B),('B','B',B),('P = A XOR B','P = A XOR B',G)]):
 v+=n(40+355*i,298,330,75,e,k,c=c)
v+=n(40,423,500,76,'A missing: P XOR B','A 누락: P XOR B','Reconstruct A','A 복원',G)+n(580,423,500,76,'Two blocks missing','두 블록 누락','Insufficient information','복원 정보 부족',F)
v+=t(40,550,'A parity mismatch alone cannot identify the incorrect member.','Parity 불일치만으로 잘못된 구성 장치를 특정할 수 없다.',20,650)
fig('raid-02-redundancy.svg','Mirroring and known-erasure recovery','Mirror와 누락 위치를 아는 복원','4096-byte deterministic XOR model; not a real MD array','4096바이트 XOR 모델 · 실제 MD Array 아님',v,602,('All 3 single erasures restored; two erasures rejected; altered block detected','단일 누락 3가지 복원 · 두 누락 거부 · 변경 블록 검출'))
# 03 state dimensions
v=t(40,131,'Array membership','배열 멤버 상태',21,700)+t(580,131,'Synchronization activity','동기화 작업 상태',21,700)
v+=n(40,155,500,76,'degraded = 0','degraded = 0','Expected active-member count','예상 활성 멤버 수 충족',G)+n(40,252,500,76,'degraded > 0','degraded > 0','Missing active members','활성 멤버 누락',A)
for i,(e,k,sub,ks) in enumerate([('idle','idle','No sync operation active','진행 중인 동기화 없음'),('recover','recover','Build a replacement','교체 장치 재구성'),('resync','resync','Re-establish redundancy','중복성 재구성'),('check','check','Check consistency','정합성 검사')]):
 v+=n(580,155+84*i,500,72,e,k,sub,ks)
v+=r(40,380,500,108,F,'#d1a69d')+t(60,411,'Important distinction','중요한 구분',21,700)+t(60,441,'idle can coexist with degraded > 0','idle과 degraded > 0은 공존 가능',19,650)+t(60,468,'A rebuild is not a filesystem audit.','Rebuild는 파일시스템 검증이 아니다.',17,c=M)
v+=t(40,542,'Inspect both dimensions and the underlying member errors.','두 상태와 구성 장치의 오류를 함께 확인한다.',20,650)
fig('raid-03-md-state.svg','MD membership and sync state','MD 멤버 및 동기화 상태','Independent observation dimensions, not a fixed transition sequence','독립적인 관측 항목 · 고정된 상태 전이 순서 아님',v,592)
# 04 errno matrix and possible propagation
v=n(40,115,330,78,'Block I/O error','Block I/O 오류','Device or array path','장치 또는 배열 경로',F)+n(395,115,330,78,'Filesystem policy','파일시스템 정책','Possible read-only mount','Read-only 전환 가능',A)+n(750,115,330,78,'Application write','애플리케이션 쓰기','Failure or delayed error','실패 또는 지연 오류')+p('M370 154H395',True,True)+p('M725 154H750',True,True)
v+=t(40,243,'Error category','오류 종류',21,700)+t(360,243,'What it indicates','의미하는 것',21,700)
for i,(e,k,a,ak) in enumerate([('EIO','EIO','Input/output error','입출력 오류'),('EROFS','EROFS','Read-only filesystem','읽기 전용 파일시스템'),('ENOSPC','ENOSPC','No space available','사용 가능한 공간 없음'),('EACCES','EACCES','Permission denied','접근 권한 거부')]):
 y=262+i*64;v+=r(40,y,1040,54,'#f2f6fa','#c4d3df',5)+t(55,y+34,e,k,21,700)+t(360,y+34,a,ak,20,600)
v+=t(40,557,'An application-level read-only state is a separate observation.','애플리케이션 수준의 Read-only 상태는 별도의 관측이다.',20,650)
fig('raid-04-filesystem.svg','From device errors to filesystem symptoms','장치 오류에서 파일시스템 증상까지','Possible propagation, not a recorded causal sequence','가능한 장애 전파 · 실제 인과관계 기록 아님',v,607)
# 05 quorum thresholds, plus logical stages.
v=t(40,132,'Voters','투표 멤버',21,700)+t(355,132,'Majority','과반수',21,700)+t(700,132,'Unavailable margin','장애 허용 수',21,700)
for i,N in enumerate((3,4,5)):
 y=154+i*76;q=N//2+1
 v+=r(40,y,1040,65,'#f2f6fa','#c4d3df',5)+t(55,y+41,str(N),s=23,w=750)
 for j in range(N):
  v+=f'<circle cx="{110+j*39}" cy="{y+32}" r="14" fill="{G if j<q else A}" stroke="#9eb3c2"/>'
 v+=t(355,y+41,str(q),s=23,w=750)+t(700,y+41,str(N-q),s=23,w=750)
v+=t(40,421,'Proposal to applied state (logical stages)','제안부터 상태 적용까지 (논리적 단계)',22,700)
for i,(e,k,c) in enumerate([('Proposal','제안',B),('Log replication','Log 복제',B),('Raft commit','Raft Commit',G),('Apply','Apply',G)]):
 x=40+265*i;v+=n(x,446,245,65,e,k,c=c)
 if i<3:v+=p(f'M{x+245} 478H{x+265}')
v+=t(40,557,'A numerical majority alone does not prove leadership or durable progress.','수치상 과반수만으로 Leader 선출이나 영속적인 진행을 보장하지 않는다.',19,650)
fig('raid-05-quorum.svg','Majority is independent of local RAID','과반수 조건과 로컬 RAID는 별개다','Stable voting configurations; illustrative member counts','안정적인 투표 구성 · 가상의 멤버 수',v,605,('56 voter subsets checked · no Raft protocol simulation','투표 조합 56개 검증 · Raft 프로토콜 시뮬레이션 아님'))
# 06 evidence gates
v=t(40,132,'Recovery layer','복구 계층',21,700)+t(605,132,'Evidence required','필요한 증거',21,700)
rows=[('Block device','Block Device','Member status / I/O errors','멤버 상태 / I/O 오류'),('Filesystem','파일시스템','Correct mount / writable state','올바른 Mount / 쓰기 상태'),('etcd','etcd','Membership / health / revision','Membership / Health / Revision'),('Kubernetes','Kubernetes','API and controller reconciliation','API 및 Controller Reconciliation'),('Application data','애플리케이션 데이터','Expected volume and data checks','의도한 Volume 및 데이터 검증')]
for i,(e,k,a,ak) in enumerate(rows):
 y=155+i*79;v+=n(40,y,500,65,e,k,c=G)+p(f'M540 {y+32}H580')+n(580,y,500,65,a,ak)
 if i<4:v+=p(f'M290 {y+65}V{y+79}')
v+=r(40,570,1040,69,A,'#c4aa77')+t(60,611,'An etcd snapshot is not an application-volume backup.','etcd Snapshot은 애플리케이션 Volume 백업이 아니다.',21,650)
fig('raid-06-recovery-gates.svg','Separate recovery checkpoints','복구 단계별 확인 기준','Proposed validation gates; no complete historical audit available','제안하는 검증 단계 · 당시 전체 검증 기록 없음',v,689)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs; {len(L)} labels')
