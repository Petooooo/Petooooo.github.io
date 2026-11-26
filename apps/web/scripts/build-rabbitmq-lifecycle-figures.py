#!/usr/bin/env python3
"""Build AMQP lifecycle figures; verify simplified delivery and ownership models."""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
from collections import deque
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
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,'Conceptual example · not a historical packet trace','설명용 예시 · 당시 패킷 기록 아님',14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# MODEL_START
def negotiate(a,b):return max(a,b) if min(a,b)==0 else min(a,b)
assert [negotiate(a,b) for a,b in [(86400,60),(0,60),(60,0),(0,0),(30,60)]]==[60,60,60,0,30]
class Broker:
 def __init__(self,items,limit=2):
  self.ready=deque(items);self.limit=limit;self.channels={}
 def open(self,c):assert c not in self.channels;self.channels[c]=[0,{}]
 def take(self,c):
  seq,held=self.channels[c]
  if len(held)>=self.limit or not self.ready:return None
  seq+=1;self.channels[c][0]=seq;held[seq]=self.ready.popleft()
  return (c,seq,held[seq])
 def ack(self,c,delivery):
  owner,tag,job=delivery
  if c!=owner or c not in self.channels or self.channels[c][1].get(tag)!=job:raise ValueError('stale delivery')
  del self.channels[c][1][tag]
 def close(self,c):
  _,held=self.channels.pop(c);self.ready.extend(held.values())
b=Broker(['a','b','c']);b.open('old');b.open('other')
a=b.take('old');job_b=b.take('old');assert b.take('old') is None
b.ack('old',a);c=b.take('old');assert c[1]==3
try:b.ack('other',job_b)
except ValueError:pass
else:raise AssertionError('wrong channel accepted')
b.close('old');assert sorted(b.ready)==['b','c']
b.open('new');new1=b.take('new');new2=b.take('new')
assert [new1[1],new2[1]]==[1,2] and {new1[2],new2[2]}=={'b','c'}
assert job_b[2]=='b' # local reference remains even after broker close
try:b.ack('new',job_b)
except ValueError:pass
else:raise AssertionError('stale ack accepted')
class Job:
 def __init__(self):self.token=0;self.state='pending';self.artifacts={};self.accepted=None
 def claim(self):
  assert self.state=='pending';self.token+=1;self.state='claimed';return self.token
 def expire(self,token):
  if self.state=='claimed' and token==self.token:self.state='pending';return True
  return False
 def artifact(self,token):self.artifacts[token]=f'artifact-{token}'
 def complete(self,token):
  if self.state!='claimed' or token!=self.token or token not in self.artifacts:return False
  self.accepted=self.artifacts[token];self.state='complete';return True
# Early acknowledgement without a recovery owner.
early=Broker(['job']);early.open('a');early.ack('a',early.take('a'));early.close('a')
assert not early.ready
# Crash after durable claim, before or after ack; replayed command must not claim again.
for ack_before_crash in (False,True):
 j=Job();q=Broker(['job']);q.open('a');delivery=q.take('a');token=j.claim()
 if ack_before_crash:q.ack('a',delivery)
 q.close('a');assert bool(q.ready)==(not ack_before_crash) and j.state=='claimed'
 assert j.expire(token);next_token=j.claim();assert next_token!=token
 j.artifact(token);j.artifact(next_token)
 assert not j.complete(token) and j.complete(next_token) and not j.complete(next_token)
 assert j.accepted=='artifact-2'
# Shovel confirm/ack ambiguity: illustrative source redelivery creates two copies.
source=Broker(['m']);source.open('s');d=source.take('s');destination=[d[2]]
source.close('s');source.open('s2');d2=source.take('s2');destination.append(d2[2]);source.ack('s2',d2)
assert destination==['m','m'] and not source.ready
print('PASS: 5 heartbeat negotiation examples; delivery credit, wrong-channel and stale Ack rejection; claim-before/after-Ack failure windows, lease replacement, stale completion and duplicate completion; Shovel duplicate window')
# MODEL_END
# 01 shovel
v=t(40,132,'Source broker','Source Broker',21,700)+t(420,132,'Shovel','Shovel',21,700)+t(790,132,'Destination broker','Destination Broker',21,700)
v+=n(40,155,290,76,'Unacked delivery','Unacked Delivery','Message M','메시지 M')+n(405,155,290,76,'Publish M','M 발행')+n(770,155,310,76,'Accept publication','발행 수락','Message M','메시지 M',G)+p('M330 193H405')+p('M695 193H770')
v+=n(405,280,290,76,'Confirm received','Confirm 수신')+p('M925 231V318H695')
v+=n(40,280,290,76,'Source Ack','Source Ack','Not yet received','아직 수신 전',A)+p('M405 318H330',True)
v+=r(40,400,1040,104,F,'#d1a69d')+t(60,433,'Failure window: source connection closes before Ack arrives.','실패 구간: Ack 도착 전에 Source 연결 종료.',21,700)+t(60,465,'Redelivery + republish can create a second destination copy.','재전달 후 다시 발행하면 Destination에 복제본이 추가될 수 있다.',19,650)
fig('amqp-01-shovel.svg','Shovel on-confirm: two acknowledgement boundaries','Shovel on-confirm: 두 확인 경계','Illustrative AMQP transfer; message identity is stable','가상 AMQP 이전 · 메시지 식별자는 유지',v,555)
# 02
v=n(40,115,1040,70,'TCP connection generation A','TCP Connection Generation A')
v+=n(40,240,500,82,'Channel A1','Channel A1','Delivery tag 1 / job X','Delivery Tag 1 / Job X',G)+n(580,240,500,82,'Channel A2','Channel A2','Delivery tag 1 / job Y','Delivery Tag 1 / Job Y')+p('M560 185V211H290V240')+p('M560 211H830V240')
v+=r(40,365,1040,58,F,'#d1a69d')+t(60,401,'Connection closes: both channels are lost.','Connection 종료: 두 Channel 모두 사라진다.',20,700)
v+=n(40,465,500,82,'New generation B / channel B1','새 Generation B / Channel B1','Tag 1 may be reused','Tag 1 재사용 가능',G)+n(580,465,500,82,'Old worker callback','기존 Worker Callback','Reject old delivery context','이전 Delivery 문맥 거부',A)
v+=t(40,600,'Delivery tags are not globally unique job identifiers.','Delivery Tag는 전역 고유 Job 식별자가 아니다.',20,650)
fig('amqp-02-channels.svg','Connection lifetime and channel-scoped tags','Connection 생명주기와 Channel별 Tag','Illustrative channel identities, not observed connection IDs','가상 Channel 식별자 · 실제 Connection ID 아님',v,650)
# 03
v=n(40,115,500,76,'Server proposal: 86400 s','서버 제안: 86400초')+n(580,115,500,76,'Client proposal: 60 s','Client 제안: 60초')
v+=p('M290 191V219H560V250')+p('M830 191V219H560')
v+=n(260,250,600,76,'Documented algorithm: 60 s','공개 협상 알고리즘: 60초','Pika can override the proposal','Pika는 제안값을 덮어쓸 수 있음',A)
v+=t(40,375,'Heartbeat traffic interval (illustrative)','Heartbeat 전송 간격 (예시)',21,700)
v+=p('M100 423H1020')
for i,label in enumerate(['0 s','30 s','60 s','90 s']):
 x=100+i*290;v+=f'<circle cx="{x}" cy="423" r="7" fill="#79a58b" stroke="#5e7387"/>'+t(x,454,label,s=18,w=650,a='middle')
v+=r(40,500,1040,74,'#f2f6fa','#c4d3df')+t(60,530,'Delivery age / application runtime: separate clock','Delivery 경과 시간 / 앱 실행 시간: 별도 기준',20,700)+t(60,555,'A live connection can carry a long unacknowledged delivery.','연결이 살아 있어도 오래된 Unacked Delivery가 남을 수 있다.',17,c=M)
fig('amqp-03-heartbeat.svg','Heartbeat is not a job execution timeout','Heartbeat는 작업 실행 기한이 아니다','Negotiation example; not the historical Pika negotiated value','협상 예시 · 당시 Pika 협상값 아님',v,625)
# 04
v=t(40,132,'Event','이벤트',21,700)+t(455,132,'Outstanding deliveries','미확인 Delivery',21,700)+t(870,132,'Free credit','남은 Credit',21,700)
for i,(e,k,a,ak,c) in enumerate([('Initial','초기','None','없음','2'),('Deliver A, B','A, B 전달','A, B','A, B','0'),('Ack A','A Ack','B','B','1'),('Deliver C','C 전달','B, C','B, C','0'),('Channel closes','Channel 종료','Requeue B, C','B, C 재등록','—')]):
 y=151+i*69;v+=r(40,y,1040,60,F if i==4 else '#f2f6fa','#c4d3df')+t(60,y+38,e,k,20,700)+t(455,y+38,a,ak,20,650)+t(870,y+38,c,s=21,w=700)
v+=t(40,545,'Old local work may continue after its delivery credit disappears.','Delivery Credit이 사라진 뒤에도 기존 작업은 계속 실행될 수 있다.',20,650)
fig('amqp-04-prefetch.svg','Prefetch 2: delivery credit accounting','Prefetch 2: Delivery Credit 계산','Verified in-memory model; not a broker throughput experiment','검증한 메모리 모델 · Broker 처리량 실험 아님',v,595)
# 05
v=n(40,115,500,76,'Attempt A / token 1','Attempt A / Token 1','Durable claim then Ack','영속 Claim 이후 Ack')+n(580,115,500,76,'Lease expires','Lease 만료','Local work may survive','로컬 작업이 살아 있을 수 있음',A)+p('M540 153H580')
v+=n(580,250,500,76,'Attempt B / token 2','Attempt B / Token 2','New claim','새 Claim',G)+p('M830 191V250')
v+=n(40,250,500,76,'A completes late','A의 늦은 완료','Artifact A / token 1','Artifact A / Token 1',A)+p('M290 191V250',True)
v+=n(40,390,500,76,'Reject stale token','이전 Token 거부','Do not change selected result','선택된 결과 변경 금지',F)+n(580,390,500,76,'Accept current token','현재 Token 수락','Select artifact B once','Artifact B 한 번 선택',G)+p('M290 326V390')+p('M830 326V390')
v+=t(40,515,'External side effects need their own enforcement boundary.','외부 Side Effect에도 별도 소유권 검증이 필요하다.',20,650)
fig('amqp-05-fencing.svg','Lease replacement and completion fencing','Lease 교체와 완료 검증','Atomic state model; not a distributed transaction test','원자적 상태 모델 · 분산 트랜잭션 실험 아님',v,565)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'5 native SVGs; {len(L)} labels')
