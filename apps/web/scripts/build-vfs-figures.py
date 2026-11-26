#!/usr/bin/env python3
"""Generate VFS diagrams and verify disposable-file reference behavior."""
from pathlib import Path
import html,json,os,tempfile,errno,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Explanatory model · not a historical mount inventory','설명용 모델 · 당시 Mount 목록 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#ffffff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Actual OS calls: no mounts, no elevated permissions, no production files.
with tempfile.TemporaryDirectory(prefix='vfs-example-') as temp:
 a=Path(temp)/'a';b=Path(temp)/'b';a.write_bytes(b'ABCDEF')
 fd=os.open(a,os.O_RDONLY);dup=os.dup(fd);ind=os.open(a,os.O_RDONLY)
 live={fd,dup,ind}
 try:
  ino=os.fstat(fd).st_ino
  assert all(os.fstat(x).st_ino==ino for x in live)
  assert os.read(fd,2)==b'AB' and os.read(dup,2)==b'CD' and os.read(ind,2)==b'AB'
  assert os.lseek(fd,0,os.SEEK_CUR)==os.lseek(dup,0,os.SEEK_CUR)==4 and os.lseek(ind,0,os.SEEK_CUR)==2
  os.link(a,b);assert os.fstat(fd).st_nlink==2
  a.unlink();assert os.fstat(fd).st_nlink==1
  b.unlink();assert os.fstat(fd).st_nlink==0
  for name in (a,b):
   try:
    probe=os.open(name,os.O_RDONLY);os.close(probe);raise AssertionError('name still visible')
   except FileNotFoundError as e:assert e.errno==errno.ENOENT
  os.close(fd);live.remove(fd)
  assert os.read(dup,2)==b'EF'
  assert os.fstat(dup).st_nlink==0 and os.fstat(dup).st_ino==ino
 finally:
  for x in live:os.close(x)
print('PASS: shared and independent offsets 4/2; hard-link counts 2/1/0; two ENOENT opens; duplicate reads EF after original close')
# 01: reference graph, shared struct file, path pair, inode/superblock.
v=n(40,115,300,72,'Descriptor A','Descriptor A','Original open','최초 open')+n(410,115,300,72,'Descriptor B','Descriptor B','dup(A)','dup(A)')+n(780,115,300,72,'Descriptor C','Descriptor C','Independent open','별도 open')
v+=n(170,245,410,78,'File description 1','File 객체 1','Shared offset = 4','공유 Offset = 4',G)+n(720,245,360,78,'File description 2','File 객체 2','Independent offset = 2','독립 Offset = 2',G)
v+=p('M190 187V214H375V245')+p('M560 187V214H375')+p('M930 187V245')
v+=r(40,380,1040,125,'#f2f6fa','#b9cbd9')+t(60,408,'Equivalent paths: mount + dentry','동일한 Path 값: Mount + Dentry',20,700)
v+=n(75,423,400,61,'Mount object','Mount 객체')+n(645,423,400,61,'Dentry','Dentry')
v+=p('M375 323V350H560V380')+p('M900 323V350H560',False)
v+=n(75,568,400,70,'Superblock','Superblock','Filesystem instance','파일시스템 인스턴스')+n(645,568,400,70,'Inode','Inode','Same file object on filesystem','동일 파일시스템 객체')
v+=p('M275 484V568')+p('M845 484V568')+p('M645 603H475')
v+=t(40,680,'A file description retains a path; a descriptor is not a pathname.','File 객체는 Path를 참조한다. FD 자체가 파일 경로인 것은 아니다.',19,650)
fig('vfs-01-object-graph.svg','VFS objects and open-file references','VFS 객체와 열린 파일의 참조','Conceptual object graph with offsets from the disposable-file test','임시 파일 실험의 Offset을 사용한 객체 관계도',v,727)
# 02: observed results in sequence; read positions explicit.
v=t(40,128,'Read operation','읽기 동작',21,700)+t(460,128,'Returned bytes','반환 데이터',21,700)+t(755,128,'Position after read','읽은 뒤 위치',21,700)
for i,(e,k,ret,pos) in enumerate([('Original: read(2)','원본: read(2)','AB','2'),('Duplicate: read(2)','복제: read(2)','CD','4'),('Independent: read(2)','별도 open: read(2)','AB','2')]):
 y=150+i*58
 v+=r(40,y,1040,50,B if i<2 else G,'#c1d0dc',5)+t(56,y+32,e,k,19,600)+t(460,y+32,ret,ret,20,700)+t(755,y+32,pos,pos,20,700)
v+=t(40,360,'Name lifetime and open references','이름의 생명주기와 열린 참조',22,700)
for i,(e,k,sub,ks,fill) in enumerate([('Two names','이름 두 개','nlink = 2','nlink = 2',G),('First unlink','첫 unlink','nlink = 1','nlink = 1',A),('Last unlink','마지막 unlink','nlink = 0','nlink = 0',A),('Open FD remains','열린 FD 유지','Read EF after close(A)','A를 닫은 뒤 EF 읽기',G)]):
 x=40+i*265
 v+=n(x,384,245,78,e,k,sub,ks,fill)
 if i<3:v+=p(f'M{x+245} 423H{x+265}')
v+=r(40,495,1040,56,'#f6dfda','#d1a69d')+t(60,530,'New opens of both names fail with ENOENT; fstat on the duplicate still works.','두 이름의 새 open은 ENOENT, 복제 FD의 fstat은 성공한다.',19,650)
fig('vfs-02-reference-lifetime.svg','An unlinked file can remain open','이름을 삭제해도 열린 파일은 남을 수 있다','Actual six-byte test: ABCDEF, dup, independent open, link and unlink','실제 6바이트 실험: ABCDEF, dup, 별도 open, link와 unlink',v,600,('Verified with ordinary Linux file calls · no disk-space benchmark','Linux 파일 호출로 검증 · 디스크 공간 측정 아님'))
# 03: same backing tree, different attachment, covered dir and namespace.
v=r(40,115,490,310,'#f2f6fa','#bacddb')+t(60,149,'Host mount namespace','Host Mount Namespace',23,700)
v+=n(70,175,430,70,'Host root tree','Host Root Tree','/','/')+n(70,310,430,80,'Attachment H','Attachment H','/stage','/stage',G)+p('M285 245V310')
v+=r(590,115,490,310,'#f2f6fa','#bacddb')+t(610,149,'Workload mount namespace','Workload Mount Namespace',23,700)
v+=n(620,175,430,70,'Container root tree','Container Root Tree','/','/')+n(620,310,430,80,'Attachment W','Attachment W','/data','/data',G)+p('M835 245V310')
v+=n(300,487,520,78,'Shared filesystem subtree','공유 파일시스템 하위 트리','Same data; distinct attachment identities','동일 데이터 · 서로 다른 Mount 식별자',A)
v+=p('M285 390V455H430V487')+p('M835 390V455H690V487')
v+=t(40,610,'Propagation controls mount events, not ordinary file writes.','Propagation은 Mount 이벤트를 제어하며 일반 파일 쓰기와는 별개다.',20,650)
fig('vfs-03-mount-namespace.svg','A filesystem can have several mount views','하나의 파일시스템을 여러 Mount에서 바라보기','Illustrative namespaces and paths; no actual host mounts created','가상의 Namespace와 경로 · 실제 Host Mount 생성 없음',v,660)
# 04: operations change different relationships.
v=t(40,130,'Operation','작업',21,700)+t(265,130,'Relationship changed','변경하는 관계',21,700)+t(705,130,'Limit or remaining state','제약 또는 남는 상태',21,700)
rows=[('unlink','unlink','Remove a file name','파일 이름 제거','Open references may survive','열린 참조가 남을 수 있음',B),('rmdir','rmdir','Remove an empty directory','빈 디렉터리 제거','Mountpoint may return EBUSY','Mountpoint는 EBUSY 가능',F),('umount','umount','Detach mount attachment','Mount 연결 해제','Active refs / submounts may block','활성 참조 / 하위 Mount가 방해',A),('Lazy detach','Lazy Detach','Detach namespace view now','Namespace에서 즉시 분리','Reference cleanup deferred','참조 정리는 나중에 진행',A)]
for i,(e,k,a,ak,b,bk,c) in enumerate(rows):
 y=151+i*86
 v+=r(40,y,1040,74,c,'#c0d0dd')+t(58,y+43,e,k,21,700)+t(265,y+43,a,ak,19,550)+t(705,y+43,b,bk,17,550)
v+=r(40,510,1040,75,'#f6dfda','#d1a69d')+t(60,541,'Observed: rm → Device or resource busy','관측: rm → Device or resource busy',22,750)+t(60,568,'Exact mount holder and subsequent unmount result not established.','정확한 Mount 참조 주체 및 이후 Unmount 결과는 미확인.',18,c=M)
fig('vfs-04-operation-boundaries.svg','Name removal and mount detachment are different','이름 제거와 Mount 해제는 서로 다르다','Separate the operation from the errno before diagnosing','원인을 판단하기 전에 작업과 errno를 구분한다',v,635,('Historical rm error + conceptual operation comparison','실제 rm 오류와 작업별 개념 비교'))
# 05: storage hierarchy and two views.
v=n(345,115,430,75,'Filesystem volume','파일시스템 Volume','Driver-provided device','Driver에서 제공한 장치',A)
v+=n(345,240,430,75,'Node staging mount','Node Staging Mount','Staging target (globalmount)','Staging Target (globalmount)',G)+p('M560 190V240')
v+=n(40,370,470,76,'Pod target A','Pod Target A','NodePublishVolume','NodePublishVolume')+n(610,370,470,76,'Pod target B','Pod Target B','NodePublishVolume','NodePublishVolume')+p('M560 315V343H275V370')+p('M560 343H845V370')
v+=n(40,498,470,76,'Container A: /data','Container A: /data','Runtime mount view','Runtime Mount View',G)+n(610,498,470,76,'Container B: /data','Container B: /data','Runtime mount view','Runtime Mount View',G)+p('M275 446V498')+p('M845 446V498')
v+=t(40,617,'Multiple targets require a supported access mode; they are not replicas.','여러 Target에는 지원되는 Access Mode가 필요하며 복제본을 의미하지 않는다.',19,650)
fig('vfs-05-csi-mount-topology.svg','CSI staging and publication references','CSI Staging과 Publication 참조','Example: staged filesystem volume, where two consumers are permitted','Staging을 사용하는 파일시스템 Volume 예시 · 두 사용자 허용 가정',v,667)
# 06: teardown conditions not implied by rm error.
v=t(40,129,'Normal dependency order','일반적인 의존성 순서',22,700)+t(620,129,'Verification checkpoint','검증 지점',22,700)
for i,(e,k,sub,ks,a,ak) in enumerate([('Stop consuming workload','Volume 사용자 종료','Quiesce application I/O','애플리케이션 I/O 중단','No unintended writers','의도하지 않은 Writer 없음'),('NodeUnpublishVolume','NodeUnpublishVolume','Remove each target','각 Target 정리','Target references gone','Target 참조 해제 확인'),('NodeUnstageVolume','NodeUnstageVolume','After all publications removed','Publication 정리 후','Staging attachment removed','Staging 연결 해제 확인'),('ControllerUnpublishVolume','ControllerUnpublishVolume','Where attach is supported','Attach 지원 시','Driver detach reconciled','Driver Detach 상태 수렴')]):
 y=151+i*95
 v+=n(40,y,510,75,e,k,sub,ks,G)+p(f'M550 {y+37}H610')+n(610,y,470,75,a,ak)
 if i<3:v+=p(f'M295 {y+75}V{y+95}')
v+=r(40,545,1040,72,F,'#d1a69d')+t(60,575,'Historical evidence: directory removal returned EBUSY','당시 증거: 디렉터리 제거에서 EBUSY 발생',21,700)+t(60,600,'No preserved trace proving the above teardown or data recovery completed.','위 정리 단계 또는 데이터 복구 완료를 입증하는 기록 없음.',17,c=M)
fig('vfs-06-teardown-evidence.svg','Volume teardown follows reference dependencies','Volume 정리는 참조 의존성을 따라야 한다','Capability-dependent lifecycle; verify mount state separately from RPC success','Capability에 따른 생명주기 · RPC 성공과 실제 Mount 상태를 별도 검증',v,664)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs generated; {len(L)} unique labels; temporary file experiment passed')
