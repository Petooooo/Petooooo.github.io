#!/usr/bin/env python3
"""Generate explanatory SVGs and execute bounded synthetic examples, not runtime tests."""
from pathlib import Path
import html,json,hashlib,tarfile,gzip,io,tempfile
import xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Explanatory model · not a captured runtime trace','설명용 모델 · 실제 실행 Trace 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#ffffff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def archive(name,data):
 buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as tar:
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;tar.addfile(info,io.BytesIO(data))
 return buf.getvalue()
a,b=archive('config.txt',b'base\n'),archive('config.txt',b'changed\n')
d0,d1=sha(a),sha(b);compressed=sha(gzip.compress(a,mtime=0));chain=lambda x,y:sha((x+' '+y).encode())
assert compressed!=d0 and chain(d0,d1)!=chain(d1,d0) and chain(d0,d1)==chain(sha(archive('config.txt',b'base\n')),sha(archive('config.txt',b'changed\n')))
# 01: content to snapshots. Horizontal rows separate the two storage domains.
v=r(40,115,1040,170,'#f2f6fa','#c5d6e2')+t(60,147,'Content store','Content Store',22,700)
v+=n(60,170,265,83,'Manifest','Manifest','Ordered descriptors','순서가 있는 Descriptor')+n(410,170,290,83,'Image config','Image Config','Ordered DiffIDs','순서가 있는 DiffID')+n(780,170,280,83,'Layer blobs','Layer Blob','Content digests','콘텐츠 Digest')
v+=p('M325 210H410')+p('M193 170V159H920V170')
v+=t(40,328,'Unpack: apply layer contents in order','Unpack: Layer 변경 내용을 순서대로 적용',22,700)
v+=p('M920 285V343H190V370')
v+=n(40,370,300,82,'Committed base','Committed Base','Apply D0, then commit','D0 적용 후 Commit',G)+n(410,370,300,82,'Committed top','Committed Top','Apply D1 on base','Base 위에 D1 적용',G)+n(780,370,300,82,'Active snapshot','Active Snapshot','Container writable state','컨테이너 쓰기 상태',A)
v+=p('M340 411H410')+p('M710 411H780')
v+=t(40,500,'Blob digest, DiffID, ChainID and local directory ID are distinct.','Blob Digest, DiffID, ChainID와 로컬 디렉터리 ID는 서로 다르다.',20,650)
fig('overlay-01-content-flow.svg','From OCI content to a writable root filesystem','OCI 콘텐츠에서 쓰기 가능한 Root Filesystem까지','Logical content references above; applied filesystem states below','위는 콘텐츠 참조, 아래는 적용된 파일시스템 상태',v,551)
# 02: layered cross section with sidecar workdir
v=n(185,115,750,70,'Merged mount','Merged Mount','Container-visible namespace','컨테이너에서 보이는 파일 이름 공간',G)
for y,fill,lab,klab,sub,ks in [(236,A,'upperdir','upperdir','Writable changes for this container','컨테이너 전용 변경 내용'),(352,B,'lowerdir: top layer','lowerdir: 상위 Layer','Shared committed changes','공유된 Committed 변경 내용'),(468,B,'lowerdir: base layer','lowerdir: Base Layer','Older shared changes','이전의 공유 변경 내용')]:
 v+=f'<polygon points="45,{y+22} 655,{y+22} 730,{y-5} 120,{y-5}" fill="{fill}" stroke="#98aebd"/>'+r(45,y+22,610,75,fill,'#98aebd',0)+f'<polygon points="655,{y+22} 730,{y-5} 730,{y+70} 655,{y+97}" fill="#c6d7e4" stroke="#98aebd"/>'
 v+=t(65,y+53,lab,klab,23,700)+t(65,y+78,sub,ks,18,c=M)
v+=p('M360 236V185')+n(810,258,270,75,'workdir','workdir','Private scratch space','내부 작업 공간',A)+p('M810 295H730',False,True)
v+=t(795,377,'Same filesystem','같은 파일시스템',19,700)+t(795,402,'as upperdir','upperdir과 동일',17,c=M)+t(795,455,'Lookup priority','조회 우선순위',19,700)+t(795,481,'Upper, then ordered lower','Upper, 순서대로 Lower',17,c=M)
v+=t(45,604,'Workdir is not a visible layer; lower layers remain shared.','Workdir은 보이는 Layer가 아니며 Lower Layer는 공유 상태로 남는다.',19,600)
fig('overlay-02-layer-layout.svg','OverlayFS layer cross-section','OverlayFS 계층 단면','Conventional writable overlay; not every snapshot uses this mount form','일반적인 쓰기 가능 Overlay · 모든 Snapshot이 이 형태는 아님',v,650)
# 03: minimal precedence model; no kernel mount.
lower={'config.txt':b'base'};upper={};WHITEOUT=object()
def lookup(name):
 val=upper.get(name,lower.get(name));return None if val is WHITEOUT else val
assert lookup('config.txt')==b'base' and not upper
upper['config.txt']=lookup('config.txt');upper['config.txt']=b'edited'
assert lookup('config.txt')==b'edited' and lower['config.txt']==b'base'
upper['config.txt']=WHITEOUT
assert lookup('config.txt') is None and lower['config.txt']==b'base'
v=''
for i,(head,kh,up,ku,merged,km,fill) in enumerate([('1. Read','1. 읽기','No upper entry','Upper 항목 없음','config.txt: base','config.txt: base',B),('2. Modify','2. 수정','config.txt: edited','config.txt: edited','config.txt: edited','config.txt: edited',G),('3. Delete','3. 삭제','Whiteout marker','Whiteout 표시','Name hidden','파일 이름 숨김',F)]):
 x=40+355*i
 v+=r(x,115,330,350,'#f7f9fb','#c8d6e1')+t(x+165,149,head,kh,22,750,'middle')
 v+=n(x+15,175,300,75,'Merged view','Merged View',merged,km,fill)
 v+=n(x+15,278,300,75,'Upper layer','Upper Layer',up,ku,A)
 v+=n(x+15,381,300,65,'Lower: config.txt','Lower: config.txt','base','base',B)
 if i!=0:v+=p(f'M{x+165} 278V250')
 if i==0:v+=p(f'M{x+15} 413H{x+6}V211H{x+15}')
 if i==1:v+=p(f'M{x+165} 381V353',True,True)
v+=t(40,511,'The original lower file is unchanged in all three states.','세 상태에서 Lower의 원본 파일은 변경되지 않는다.',20,700)
fig('overlay-03-copy-up-whiteout.svg','Copy-up and deletion across layers','계층 간 Copy-up과 삭제','Synthetic lookup model: full data copy-up, then a whiteout','가상 조회 모델 · 전체 데이터 Copy-up 후 Whiteout',v,560,('Three model assertions passed · no kernel mount','모델 검증 3단계 통과 · 커널 Mount 없음'))
# 04: actual ordinary stat on a disposable directory and unchanged model metadata
with tempfile.TemporaryDirectory(prefix='overlay-example-') as temp:
 root=Path(temp);parent=root/'parent-a'/'fs';parent.mkdir(parents=True);other=root/'parent-b'/'fs';other.mkdir(parents=True)
 meta={'child-a':'parent-a','child-b':'parent-a','child-c':'parent-b'};before=dict(meta)
 def stat_child(key):return (root/meta[key]/'fs').stat()
 assert stat_child('child-a') and stat_child('child-b')
 parent.rmdir()
 failed=0
 for child in ('child-a','child-b'):
  try:stat_child(child)
  except FileNotFoundError:failed+=1
 assert failed==2 and stat_child('child-c') and meta==before
v=t(40,130,'Logical metadata','논리적 메타데이터',22,700)+t(770,130,'Physical directories','실제 디렉터리',22,700)
v+=n(40,157,290,76,'Active child A','Active Child A','parent = P','parent = P')+n(40,266,290,76,'Active child B','Active Child B','parent = P','parent = P')+n(420,206,285,83,'Committed P','Committed P','Resolved storage ID','확인된 Storage ID',G)
v+=p('M330 195H375V233H420')+p('M330 304H375V262H420')
v+=n(770,206,310,83,'P / fs missing','P / fs 누락','stat → ENOENT','stat → ENOENT',F)+p('M705 248H770',True,True)
v+=n(40,405,290,76,'Active child C','Active Child C','parent = Q','parent = Q')+n(420,405,285,76,'Committed Q','Committed Q','Independent parent','독립적인 부모',G)+n(770,405,310,76,'Q / fs exists','Q / fs 존재','stat succeeds','stat 성공',G)
v+=p('M330 443H420')+p('M705 443H770')
v+=t(40,535,'Two dependent lookups failed; the independent parent and metadata remained intact.','두 의존 조회는 실패했지만 독립 부모와 메타데이터는 그대로 남았다.',19,650)
fig('overlay-04-parent-dependency.svg','Snapshot references versus backing paths','Snapshot 참조와 실제 저장 경로','A disposable directory experiment with synthetic metadata','가상 메타데이터와 임시 디렉터리를 이용한 실험',v,585,('Actual stat experiment; no containerd state was accessed','실제 stat 예제 · containerd 운영 상태에 접근하지 않음'))
# 05: stages / evidence
v=''
stages=[('Resolve image','이미지 확인','Manifest / identity','Manifest / 식별자'),('Fetch / reuse blobs','Blob 다운로드 / 재사용','Content availability','콘텐츠 확보'),('Unpack / reuse chain','Unpack / 체인 재사용','Committed snapshots','Committed Snapshot'),('Prepare active snapshot','Active Snapshot 준비','Parent stat failure','부모 stat 오류'),('Mount root filesystem','Root Filesystem Mount','Usable mount view','사용 가능한 Mount'),('Start process','프로세스 실행','Runtime / app startup','런타임 및 앱 시작')]
for i,(e,k,sub,ks) in enumerate(stages):
 y=116+i*82
 v+=n(40,y,450,66,e,k,sub,ks,F if i==3 else B)
 if i<5:v+=p(f'M265 {y+66}V{y+82}')
v+=r(540,360,540,105,F,'#d0a198')+t(560,391,'Observed error boundary','관측된 오류 경계',22,750)+t(560,422,'Parent directory lookup failed','부모 디렉터리 조회 실패',19,650)+t(560,447,'No proof of later application startup','이후 앱 실행 성공 여부는 미확인',17,c=M)+p('M490 395H540',True,True)
v+=t(540,155,'Separate evidence','별도로 확인할 증거',22,700)
for y,e,k in [(197,'Content present ≠ snapshot usable','콘텐츠 존재 ≠ Snapshot 사용 가능'),(231,'Commit output ≠ process running','Commit 출력 ≠ 프로세스 실행'),(265,'Process running ≠ volume verified','프로세스 실행 ≠ Volume 검증')]:
 v+=t(540,y,e,k,19,600)
fig('overlay-05-creation-boundary.svg','Container creation failure boundaries','컨테이너 생성의 실패 경계','Logical stages, not a fixed CRI call sequence','논리적 단계 · 고정된 CRI 호출 순서는 아님',v,655)
# 06: data class matrix
v=t(40,132,'Data class','데이터 종류',20,700)+t(340,132,'Recovery responsibility','복구 책임',20,700)+t(740,132,'Required evidence','필요한 증거',20,700)
for i,(e,k,a,ak,c,ck,fill) in enumerate([
 ('Content blobs','Content Blob','Recover trusted artifact','신뢰할 수 있는 이미지 확보','Expected digest available','의도한 Digest 확보',B),
 ('Committed snapshot','Committed Snapshot','Reconstruct applied layers','적용된 Layer 재구성','Usable parent chain','사용 가능한 Parent Chain',G),
 ('Active writable layer','Active Writable Layer','Preserve unique changes','고유 변경 내용 보존','Rootfs state checked','Rootfs 상태 확인',A),
 ('Persistent volume','영속 Volume','Separate storage lifecycle','별도의 스토리지 생명주기','Mount and data verified','Mount 및 데이터 검증',A)]):
 y=153+i*89
 v+=r(40,y,1040,75,fill,'#c0d0dd')+t(55,y+43,e,k,20,700)+t(340,y+43,a,ak,18,550)+t(740,y+43,c,ck,18,550)
v+=t(40,547,'Do not recreate a missing layer as an empty directory or delete live references.','누락된 Layer를 빈 디렉터리로 대신하거나 사용 중인 참조를 삭제해서는 안 된다.',19,650)
fig('overlay-06-recovery-boundaries.svg','Image recovery is not persistent-data recovery','이미지 복구와 영속 데이터 복구는 별개','Recovery checks depend on who owns the data','데이터 소유 영역마다 복구 검증 기준이 다름',v,595)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs; deterministic digest/chain checks, 3 lookup states, 2 ENOENT cases and independent parent verified; {len(L)} labels')
