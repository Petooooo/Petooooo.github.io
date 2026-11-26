#!/usr/bin/env python3
"""Generate runtime-storage diagrams and verify path identity in a temporary tree."""
from pathlib import Path
import html,json,os,tempfile,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Conceptual example · not a historical node inventory','설명용 예시 · 당시 노드 구성의 실측값 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Real, bounded filesystem experiment. No mount or privileged operation.
with tempfile.TemporaryDirectory(prefix='runtime-path-example-') as tmp:
 root=Path(tmp);data=root/'data';data.mkdir();f=data/'layer';f.write_bytes(b'original')
 alias=root/'alias';alias.symlink_to('data',target_is_directory=True)
 original=(f.stat().st_dev,f.stat().st_ino)
 assert (alias/'layer').read_bytes()==b'original'
 assert ((alias/'layer').stat().st_dev,(alias/'layer').stat().st_ino)==original
 hard=data/'second';os.link(f,hard)
 assert hard.stat().st_ino==original[1] and f.stat().st_nlink==2
 with (alias/'layer').open('rb') as opened:
  data.rename(root/'old-data')
  assert alias.is_symlink() and not alias.exists()
  try:(alias/'layer').read_bytes()
  except FileNotFoundError:pass
  else:raise AssertionError('expected dangling lookup')
  data.mkdir();(data/'layer').write_bytes(b'replacement')
  new=( (alias/'layer').stat().st_dev,(alias/'layer').stat().st_ino )
  assert new!=original
  assert (alias/'layer').read_bytes()==b'replacement'
  assert (os.fstat(opened.fileno()).st_dev,os.fstat(opened.fileno()).st_ino)==original
  assert opened.read()==b'original'
 print('PASS: resolved identity, hard-link count 2, dangling lookup ENOENT, recreated target differs, open descriptor retains original data')
# 01: independent storage owners.
v=r(40,115,510,310,'#f2f6fa','#c4d3df')+t(60,147,'containerd persistent root','containerd 영속 Root',22,700)
v+=n(60,168,470,70,'Content blobs','Content Blob','Compressed image data','압축된 이미지 데이터')+n(60,252,470,70,'Snapshotter','Snapshotter','Applied layers and writable data','적용 Layer와 쓰기 데이터',G)+n(60,336,470,70,'Metadata databases','메타데이터 DB','Image and snapshot references','Image 및 Snapshot 참조',G)
v+=r(590,115,490,310,'#f2f6fa','#c4d3df')+t(610,147,'Runtime and other owners','런타임과 별도 관리 영역',22,700)
v+=n(610,168,450,70,'containerd state','containerd State','Sockets, task state, mounts','Socket, Task 상태, Mount',A)+n(610,252,450,70,'Kubelet root','Kubelet Root','Pod state and mount targets','Pod 상태와 Mount Target')+n(610,336,450,70,'Volume data','Volume 데이터','CSI / local-path / hostPath','CSI / local-path / hostPath',A)
v+=t(40,470,'A copied blob store is not a complete snapshot graph or volume backup.','Blob 복사만으로 Snapshot 관계와 Volume 백업이 완성되지 않는다.',20,650)
fig('runtime-01-storage-domains.svg','Storage belongs to different runtime owners','런타임 저장 영역의 관리 주체','Persistent root and transient state must not be conflated','영속 Root와 일시적 State는 구분해야 한다',v,522)
# 02 K3s path derivation
v=n(345,115,430,76,'K3s configuration','K3s 설정','data-dir: /data/k3s','data-dir: /data/k3s',G)
v+=n(40,254,490,80,'Embedded root','Embedded Root','/data/k3s/agent/containerd','/data/k3s/agent/containerd')+n(590,254,490,80,'Generated configuration','생성된 설정','agent/etc/containerd/config.toml','agent/etc/containerd/config.toml')
v+=p('M560 191V222H285V254')+p('M560 222H835V254')
v+=n(40,390,490,78,'Runtime state / socket','Runtime State / Socket','Inspect effective release settings','실제 버전의 설정 확인',A)+n(590,390,490,78,'Kubelet / server data','Kubelet / Server 데이터','Separate paths and role scope','별도 경로와 노드 역할',A)
v+=p('M835 334V360H285V390',True,True)+p('M560 191H1095V430H1080',True,True)
v+=t(40,515,'Supported K3s flags are not identical to containerd daemon options.','K3s가 지원하는 옵션과 containerd Daemon 옵션은 동일하지 않다.',20,650)
fig('runtime-02-config.svg','K3s configuration and derived paths','K3s 설정과 파생 경로','Illustrative data-dir; inspect the installed release and generated settings','data-dir 예시 · 설치 버전과 생성된 설정 확인',v,565)
# 03 path techniques and wrong backing filesystem
v=t(40,130,'Method','접근 방식',21,700)+t(340,130,'Lookup / attachment','조회 및 연결',21,700)+t(790,130,'Target storage','대상 저장소',21,700)
for i,(e,k,a,ak,sub,ks,c) in enumerate([
 ('Explicit path','명시적 경로','Configured new path','설정한 새 경로','/data/runtime','/data/runtime',G),
 ('Symbolic link','Symbolic Link','Resolve stored pathname','저장된 경로 문자열 해석','alias → /data/runtime','alias → /data/runtime',B),
 ('Bind mount','Bind Mount','Attach existing subtree','기존 하위 트리 연결','Mount namespace entry','Mount Namespace 항목',A)]):
 y=155+i*105
 v+=n(40,y,270,78,e,k)+p(f'M310 {y+39}H340')+n(340,y,420,78,a,ak,sub,ks,c)+p(f'M760 {y+39}H790')+n(790,y,290,78,'Data filesystem','데이터 파일시스템',c=G)
v+=r(40,480,1040,80,F,'#d1a69d')+t(60,511,'If the data mount is absent, a path may resolve on the system disk.','데이터 Mount가 없으면 경로가 시스템 디스크로 해석될 수 있다.',21,700)+t(60,539,'Verify the backing mount identity, not just existence of the directory.','디렉터리 존재 여부가 아니라 실제 Mount 식별 정보를 확인한다.',17,c=M)
fig('runtime-03-paths.svg','Path redirection does not move data by itself','경로 변경 자체가 데이터를 이전하는 것은 아니다','Configuration, symbolic links and bind attachments','설정, Symbolic Link, Bind 연결 비교',v,610)
# 04 actual path experiment
v=t(40,132,'Step','단계',21,700)+t(385,132,'New lookup via alias','alias를 통한 새 조회',21,700)+t(770,132,'Original open FD','기존 열린 FD',21,700)
for i,(e,k,a,ak,b,bk,c) in enumerate([
 ('1. Link to data','1. data 연결','Reads original','원래 데이터 읽기','Original inode','기존 Inode',G),
 ('2. Rename target','2. 대상 이름 변경','ENOENT (dangling)','ENOENT (Dangling)','Original inode retained','기존 Inode 유지',F),
 ('3. Recreate target','3. 대상 재생성','Reads replacement','새 데이터 읽기','Still reads original','여전히 원래 데이터 읽기',A)]):
 y=155+i*92
 v+=r(40,y,1040,78,'#f2f6fa','#c4d3df',5)+r(367,y+5,370,68,c,'#c4d3df',4)+t(55,y+46,e,k,20,700)+t(385,y+46,a,ak,20,650)+t(770,y+46,b,bk,19,650)
v+=n(40,457,1040,79,'Hard link check: same inode, link count = 2','Hard Link 검증: 동일 Inode, Link Count = 2','Symbolic link lookup and open file identity are different','Symbolic Link 조회와 열린 파일의 식별자는 다르다',G)
fig('runtime-04-path-experiment.svg','A pathname can lead to a different object','같은 경로가 다른 객체를 가리킬 수 있다','Actual temporary-directory experiment · no bind mounts created','실제 임시 디렉터리 실험 · Bind Mount 생성 없음',v,585,('All identity and byte-read checks passed','식별자 및 데이터 읽기 검증 통과'))
# 05 staged cutover including mount failure gate and rollback.
v=t(40,130,'Proposed gate','제안하는 검증 단계',21,700)+t(620,130,'Evidence before proceeding','다음 단계에 필요한 증거',21,700)
rows=[('Inventory and backup','목록 및 백업','Role / unique data / quorum','역할 / 고유 데이터 / Quorum'),('Quiesce actual writers','실제 Writer 정지','Tasks, shims and mounts checked','Task, Shim, Mount 확인'),('Copy consistent storage','일관된 저장소 복사','Metadata + content + attributes','메타데이터 + 콘텐츠 + 속성'),('Validate data mount','데이터 Mount 검증','Expected device and path','의도한 장치와 경로'),('Start and verify workload','기동 및 워크로드 검증','Snapshot creation / volume data','Snapshot 생성 / Volume 데이터')]
for i,(e,k,a,ak) in enumerate(rows):
 y=151+i*81
 v+=n(40,y,510,65,e,k,c=G if i>=3 else B)+p(f'M550 {y+32}H610')+n(610,y,470,65,a,ak,c=A if i==3 else B)
 if i<4:v+=p(f'M295 {y+65}V{y+81}')
v+=r(40,579,1040,70,F,'#d1a69d')+t(60,608,'Failure: stop before accepting new writes; preserve a consistent authoritative copy.','실패 시 새 쓰기 전에 중단하고 일관된 기준 데이터를 보존한다.',19,650)+t(60,633,'After new writes, rollback requires reconciliation of newer state.','새 쓰기가 발생했다면 Rollback 전에 최신 상태를 조정해야 한다.',17,c=M)
fig('runtime-05-cutover.svg','Migration is a sequence of validation gates','저장 공간 이전은 단계별 검증 과정이다','Proposed maintenance plan, not a completed historical procedure','제안하는 유지보수 계획 · 당시 완료 절차 아님',v,699)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'5 native SVGs; {len(L)} labels')
