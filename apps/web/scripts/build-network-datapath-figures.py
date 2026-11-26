#!/usr/bin/env python3
"""Generate sanitized datapath diagrams and run bounded tuple/flock checks."""
from pathlib import Path
import html,json,fcntl,os,tempfile,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Conceptual example · not an incident packet capture','설명용 예시 · 당시 패킷 캡처 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# A tuple-level model, not a packet or kernel NAT implementation.
C=('192.0.2.10',40000);S=('198.51.100.53',53);E=('203.0.113.20',8053);N=('192.0.2.101',41000)
def binding(snat=None):
 original=(C,S,'UDP');translated=(snat or C,E,'UDP')
 reply=(translated[1],translated[0],'UDP')
 def restore(packet):
  if packet!=reply:raise ValueError('unrelated tuple')
  return (S,C,'UDP')
 assert restore(reply)==(original[1],original[0],'UDP')
 try:restore((('203.0.113.21',8053),translated[0],'UDP'))
 except ValueError:pass
 else:raise AssertionError('unrelated reply accepted')
 return original,translated,reply,restore(reply)
direct=binding();masq=binding(N)
assert direct[1][0]==C and masq[1][0]==N
assert 14+20+8+8==50 and 1500-50==1450
# Actual file locks, isolated from xtables and all production state.
def blocked(fd):
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:return True
 fcntl.flock(fd,fcntl.LOCK_UN);return False
with tempfile.TemporaryDirectory(prefix='portfolio-flock-') as tmp:
 name=Path(tmp)/'example.lock';fds=[]
 def op():
  fd=os.open(name,os.O_RDWR|os.O_CREAT,0o600);fds.append(fd);return fd
 try:
  a,b=op(),op();assert os.fstat(a).st_ino==os.fstat(b).st_ino
  fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB);assert blocked(b)
  name.unlink();c,d=op(),op();assert os.fstat(a).st_ino!=os.fstat(c).st_ino
  fcntl.flock(c,fcntl.LOCK_EX|fcntl.LOCK_NB);assert blocked(b) and blocked(d)
  fcntl.flock(a,fcntl.LOCK_UN);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB);assert blocked(d)
 finally:
  for fd in fds:os.close(fd)
print('PASS: DNAT round trip, DNAT+SNAT round trip, unrelated reply rejection, IPv4 MTU arithmetic, original and recreated inode flock checks')
# 01 namespace and forwarding
v=r(40,115,490,138,'#f2f6fa','#c4d3df')+t(60,146,'Pod A namespace','Pod A Namespace',22,700)+n(60,165,450,65,'eth0 / veth end','eth0 / veth 한쪽','Socket and routing state','Socket 및 Route 상태')
v+=r(590,115,490,138,'#f2f6fa','#c4d3df')+t(610,146,'Pod B namespace','Pod B Namespace',22,700)+n(610,165,450,65,'eth0 / veth end','eth0 / veth 한쪽','Same-subnet destination','동일 서브넷 목적지')
v+=r(40,300,1040,295,'#f2f6fa','#c4d3df')+t(60,335,'Host network namespace','Host Network Namespace',23,700)
v+=n(60,355,450,64,'Host veth A','Host veth A')+n(610,355,450,64,'Host veth B','Host veth B')+p('M285 253V355')+p('M835 355V253')
v+=n(60,470,450,78,'Linux bridge','Linux Bridge','Local switching / gateway','로컬 스위칭 / Gateway',G)+n(610,470,450,78,'IP forwarding path','IP 전달 경로','Route to remote subnet','원격 서브넷 Route',A)
v+=p('M285 419V470')+p('M510 509H610')+p('M420 470V445H835V419')
v+=t(40,630,'Bridge filtering depends on the active configuration; veth is not a physical NIC.','Bridge 필터링은 설정에 따라 다르며 veth는 물리 NIC가 아니다.',19,650)
fig('datapath-01-namespace.svg','Pod network namespaces and host forwarding','Pod Network Namespace와 Host 전달 경로','Illustrative bridge-based CNI wiring','Bridge 기반 CNI의 가상 연결 구조',v,677)
# 02 vxlan headers
v=n(40,115,490,75,'Source node VTEP','출발 노드 VTEP','192.0.2.101','192.0.2.101')+n(590,115,490,75,'Destination node VTEP','수신 노드 VTEP','192.0.2.102','192.0.2.102')+p('M530 152H590')
v+=t(40,235,'Encapsulated packet on the underlay','Underlay에서 캡슐화된 패킷',22,700)
parts=[('Outer IP','외부 IP','20 B',B,175),('UDP','UDP','8 B',B,115),('VXLAN','VXLAN','8 B',B,125),('Inner Ethernet','내부 Ethernet','14 B',A,200),('Inner IP + data','내부 IP + 데이터','≤ 1450 B',G,425)]
x=40
for e,k,sub,c,w in parts:
 v+=n(x,258,w,80,e,k,sub,sub,c);x+=w
v+=t(40,380,'Outer: 192.0.2.101 → 192.0.2.102','외부: 192.0.2.101 → 192.0.2.102',21,650)+t(40,414,'Inner: 192.0.2.10 → 203.0.113.20','내부: 192.0.2.10 → 203.0.113.20',21,650)
v+=n(40,452,1040,75,'1500 − (20 + 8 + 8 + 14) = 1450 bytes','1500 − (20 + 8 + 8 + 14) = 1450바이트','Header boxes are schematic, not to scale','헤더 그림의 폭은 실제 바이트 비율과 다름',A)
v+=t(40,568,'Route → neighbor → FDB → remote underlay endpoint','Route → Neighbor → FDB → 원격 Underlay Endpoint',20,650)
fig('datapath-02-vxlan.svg','VXLAN: inner and outer addresses','VXLAN: 내부 주소와 외부 주소','Plain IPv4 underlay example; no optional headers','IPv4 Underlay 예시 · 추가 헤더 제외',v,617)
# 03 four rows with source/dest highlighted.
def fmt(a):return f'{a[0]}:{a[1]}'
v=t(40,132,'Observation point','관측 지점',21,700)+t(400,132,'Source tuple','출발 Tuple',21,700)+t(760,132,'Destination tuple','목적지 Tuple',21,700)
for i,(label,klab,flow) in enumerate(zip(['1. Client request','2. After DNAT','3. Backend reply','4. Reverse DNAT'],['1. Client 요청','2. DNAT 이후','3. Backend 응답','4. 역방향 DNAT'],direct)):
 y=154+i*81
 v+=r(40,y,1040,69,'#f2f6fa','#c4d3df',5)
 if i==1:v+=r(742,y+6,328,57,A,'#c4aa77',4)
 if i==3:v+=r(382,y+6,340,57,G,'#a5bda9',4)
 v+=t(56,y+43,label,klab,20,700)+t(400,y+43,fmt(flow[0]),s=22,w=650)+t(760,y+43,fmt(flow[1]),s=22,w=650)
v+=t(40,514,'Protocol: UDP · illustrative targetPort differs from Service port','프로토콜: UDP · Target Port와 Service Port가 다른 예시',19,650)
fig('datapath-03-tuples.svg','One Service exchange, four packet tuples','한 번의 Service 통신에서 나타나는 네 가지 Tuple','Documentation-only IP addresses; no source NAT in this example','문서용 IP 주소 · 이 예제에는 SNAT 없음',v,563)
# 04 CT states + SNAT
v=t(40,131,'Mode','변환 방식',21,700)+t(300,131,'Original direction / backend sees','Original 방향 / Backend 관측',20,700)+t(760,131,'Reply direction','Reply 방향',21,700)
for i,(e,k,flows) in enumerate([('DNAT only','DNAT만 적용',direct),('DNAT + SNAT','DNAT + SNAT',masq)]):
 y=155+i*168
 v+=r(40,y,1040,151,'#f2f6fa','#c4d3df')
 v+=t(55,y+33,e,k,21,700)+t(300,y+31,fmt(flows[0][0])+' →',s=18)+t(300,y+54,fmt(flows[0][1]),s=18)+t(300,y+83,'Backend sees:','Backend 관측:',17,650)+t(300,y+106,fmt(flows[1][0])+' →',s=18)+t(300,y+129,fmt(flows[1][1]),s=18)
 v+=t(760,y+31,fmt(flows[2][0])+' →',s=18)+t(760,y+54,fmt(flows[2][1]),s=18)+t(760,y+83,'Client receives:','Client 수신:',17,650)+t(760,y+106,fmt(flows[3][0])+' →',s=18)+t(760,y+129,fmt(flows[3][1]),s=18)
v+=t(40,526,'Both round trips restore the original Service peer and client destination.','두 왕복 예제 모두 원래 Service 상대와 Client 목적지를 복원한다.',19,650)
fig('datapath-04-conntrack.svg','Stateful NAT bindings and reverse translation','Stateful NAT Binding과 역변환','Synthetic tuple checks; not an actual conntrack table','가상의 Tuple 검증 · 실제 Conntrack Table 아님',v,576,('Two round trips and unrelated-reply rejection checked','왕복 변환 두 가지 및 무관한 응답 거부 검증'))
# 05 hook branches
v=n(40,115,500,70,'Incoming IPv4 packet','수신 IPv4 패킷')+n(580,115,500,70,'Local process','로컬 프로세스')
v+=n(40,232,500,78,'PREROUTING','PREROUTING','Conntrack, possible DNAT','Conntrack 및 가능한 DNAT',A)+p('M290 185V232')
v+=n(580,232,500,78,'OUTPUT','OUTPUT','Local filtering / possible DNAT','로컬 필터 및 가능한 DNAT',A)+p('M830 185V232')
v+=n(40,355,500,75,'Route decision','Route 결정','After destination translation','목적지 변환 이후')+p('M290 310V355')
v+=n(580,355,500,75,'Route reconsideration','Route 재결정','If destination changes','목적지 변경 시')+p('M830 310V355')
v+=n(40,482,240,75,'INPUT','INPUT','Local destination','로컬 목적지',G)+n(320,482,220,75,'FORWARD','FORWARD','Transit filtering','전달 필터',A)+p('M290 430V455H160V482')+p('M290 455H430V482')
v+=n(580,482,500,75,'POSTROUTING','POSTROUTING','Possible source NAT','가능한 SNAT',G)+p('M830 430V482')+p('M540 519H580')
v+=t(40,600,'Local delivery and forwarded traffic do not traverse the same hooks.','로컬 수신과 전달 트래픽은 같은 Hook을 모두 통과하지 않는다.',19,650)
fig('datapath-05-hooks.svg','Netfilter hooks follow the packet path','패킷 경로에 따른 Netfilter Hook','Simplified routed IPv4 path; excludes bridge and XDP paths','단순화한 IPv4 Routing 경로 · Bridge와 XDP 생략',v,650)
# 06 executed flock test
v=t(40,132,'Step','단계',21,700)+t(360,132,'Original inode A','기존 Inode A',21,700)+t(750,132,'Recreated inode B','다시 만든 Inode B',21,700)
rows=[('1. Two independent opens','1. 독립 open 두 개','First holds; second blocked','첫 FD 잠금 · 두 번째 실패','Not created','생성 전'),('2. Unlink and recreate','2. 이름 삭제 후 재생성','First lock remains held','첫 잠금 유지','New lock succeeds','새 잠금 성공'),('3. Independent lock attempt','3. 별도 잠금 시도','Second remains blocked','두 번째 여전히 실패','Other open blocked','별도 open 잠금 실패'),('4. Release original lock','4. 원래 잠금 해제','Second now succeeds','두 번째 잠금 성공','Still independently held','별개 잠금 유지')]
for i,(e,k,a,ak,b,bk) in enumerate(rows):
 y=155+i*77
 v+=r(40,y,1040,66,'#f2f6fa','#c4d3df',5)+t(55,y+41,e,k,18,700)+t(360,y+41,a,ak,18,600)+t(750,y+41,b,bk,18,600)
v+=r(40,491,1040,64,F,'#d1a69d')+t(60,530,'Same pathname does not guarantee the same inode or lock domain.','같은 파일 이름이 동일한 Inode 또는 잠금 영역을 보장하지 않는다.',20,650)
fig('datapath-06-lock.svg','Unlinking a lock file can split the lock domain','Lock 파일 삭제로 잠금 영역이 분리될 수 있다','Actual temporary-file flock experiment; no real xtables lock accessed','실제 임시 파일 flock 실험 · 운영 xtables Lock 접근 없음',v,607,('All contention and release assertions passed','잠금 경합 및 해제 검증 통과'))
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs; {len(L)} labels')
