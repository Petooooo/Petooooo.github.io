#!/usr/bin/env python3
"""Generate disk I/O diagrams; run a tiny file replacement experiment."""
from pathlib import Path
import html,json,os,tempfile,hashlib,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Explanatory model · not a historical I/O trace','설명용 모델 · 당시 I/O Trace 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Actual ordinary filesystem operations, bounded to a disposable directory.
payload=bytes(range(256))*16
with tempfile.TemporaryDirectory(prefix='disk-io-example-') as tmp:
 root=Path(tmp);target=root/'target';staged=root/'staged';target.write_bytes(b'old')
 with target.open('rb') as previous:
  fd=os.open(staged,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  try:
   assert os.write(fd,payload)==4096
   assert staged.read_bytes()==payload
   os.fsync(fd)
  finally:os.close(fd)
  os.replace(staged,target)
  dfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(dfd)
  finally:os.close(dfd)
  assert target.read_bytes()==payload and previous.read()==b'old' and not staged.exists()
assert round(26122.88/1024,2)==25.51
assert 6400*4==100*256==25*1024
print('PASS: 4096-byte write, pre-fsync read, file fsync, rename, directory fsync, new bytes and old FD; throughput arithmetic verified')
# 01: observation quantities, no causal arrow.
v=r(40,120,500,226,'#f2f6fa','#c4d3df')+r(580,120,500,226,'#f2f6fa','#c4d3df')
v+=t(60,157,'Task write rate','태스크 쓰기량',23,700)+t(60,213,'26122.88',None,42,750)+t(60,246,'kB_wr/s (pidstat)','kB_wr/s (pidstat)',20,650)+t(60,281,'≈ 25.51 MiB/s under KiB convention','KiB 기준 약 25.51 MiB/s',18,c=M)+t(60,315,'One reported sample','보고된 단일 관측값',17,c=M)
v+=t(600,157,'Snapshot directory size','Snapshot 디렉터리 용량',23,700)+t(600,213,'≈ 19 GB',None,42,750)+t(600,246,'Reported occupied space','보고된 공간 점유량',20,650)+t(600,281,'No growth interval retained','용량 증가 구간 미확인',18,c=M)+t(600,315,'Not a write-rate measurement','쓰기 속도 측정값 아님',17,c=M)
v+=r(40,385,1040,83,A,'#d3bd8c')+t(60,417,'Missing evidence: synchronized workload, device latency and mount options','부족한 증거: 동일 시각의 워크로드, 장치 지연 및 Mount Option',20,650)+t(60,444,'No established causal link between these observations.','두 관측값 사이의 인과관계는 확인되지 않았다.',18,c=M)
fig('disk-io-01-observation.svg','February 24: rate versus occupied space','2월 24일: 쓰기량과 공간 점유량','Sanitized transcription of two reported observations','당시 보고된 관측값 두 개의 비식별화 기록',v,519,('Historical point observations · no reconstructed time series','실제 단일 관측값 · 시계열 재구성 없음'))
# 02: split write data and metadata, order depends on mode.
v=n(345,115,430,75,'Application write()','Application write()','File descriptor / VFS','File Descriptor / VFS')
v+=n(345,225,430,75,'Filesystem operation','파일시스템 작업','Data copy and metadata updates','데이터 복사와 메타데이터 갱신')+p('M560 190V225')
v+=n(40,355,490,80,'Dirty cached data','Dirty 캐시 데이터','Delayed allocation / writeback','Delayed Allocation / Writeback',A)+n(590,355,490,80,'Metadata transaction','메타데이터 Transaction','ext4 / JBD2','ext4 / JBD2',A)
v+=p('M560 300V328H285V355')+p('M560 328H835V355')
v+=n(40,490,490,75,'File data I/O','파일 데이터 I/O','Home blocks (ordered example)','최종 블록 (ordered 예시)',G)+n(590,490,490,75,'Journal + checkpoint I/O','Journal + Checkpoint I/O','Commit and later home writes','Commit과 이후 최종 위치 기록',G)+p('M285 435V490')+p('M835 435V490')
v+=n(345,625,430,68,'Block layer / device','Block Layer / 장치','Queues, cache and media','큐, 캐시 및 저장 매체')+p('M285 565V595H560V625')+p('M835 565V595H560')
fig('disk-io-02-buffered-path.svg','Buffered writes branch into data and metadata','Buffered Write의 데이터와 메타데이터 경로','Ordered-mode illustration; actual ordering depends on filesystem and flags','ordered 예시 · 실제 순서는 파일시스템과 Flag에 따라 달라짐',v,744)
# 03: explicit redirty edge
v=n(40,150,300,82,'Clean cached page','Clean 캐시 페이지','Matches written contents','기록된 내용과 일치',G)+n(410,150,300,82,'Dirty page','Dirty Page','Modified contents','변경된 내용',A)+n(780,150,300,82,'Writeback in flight','Writeback 진행 중','I/O outstanding','I/O 처리 중',B)
v+=p('M340 191H410')+p('M710 191H780')+t(375,137,'Write','쓰기',16,600,'middle')+t(745,137,'Submit','제출',16,600,'middle')
v+=n(780,340,300,82,'Redirtied','다시 Dirty','New change during I/O','I/O 중 새 변경',A)+p('M930 232V340')+t(946,286,'New write','새 쓰기',17,600)
v+=p('M780 381H560V232')+t(580,368,'More writeback needed','추가 Writeback 필요',17,600)
v+=p('M930 150V111H190V150')+t(560,105,'Completion without newer modification','새 변경 없이 완료',16,600,'middle')
v+=r(40,470,1040,67,'#f2f6fa','#c4d3df')+t(60,510,'Dirty and writeback flags can coexist; an I/O error needs separate handling.','Dirty와 Writeback Flag는 공존할 수 있으며 I/O 오류는 별도 처리해야 한다.',19,650)
fig('disk-io-03-page-states.svg','Dirty page and writeback lifecycle','Dirty Page와 Writeback 생명주기','Simplified success paths with a redirty transition','다시 Dirty가 되는 경우를 포함한 단순화된 성공 경로',v,586)
# 04 journal block structure and checkpoint/replay
v=t(40,131,'Journal transaction (full commit)','Journal Transaction (Full Commit)',22,700)
for i,(e,k,c) in enumerate([('Descriptor','Descriptor',B),('Logged blocks','기록된 블록',B),('Optional revoke','선택적 Revoke',A),('Commit record','Commit Record',G)]):
 x=40+i*265;v+=n(x,157,245,70,e,k,c=c)
 if i<3:v+=p(f'M{x+245} 192H{x+265}')
v+=n(40,292,490,78,'Crash before valid commit','유효 Commit 이전 장애','Do not replay as committed','완료 Transaction으로 Replay 금지',F)
v+=n(590,292,490,78,'Valid commit, not checkpointed','Commit 완료, Checkpoint 전','Replay eligible on recovery','복구 시 Replay 가능',G)
v+=p('M295 227V260H285V292',True,True)+p('M957 227V260H835V292',True,True)
v+=n(590,425,490,75,'Checkpoint to home locations','최종 위치로 Checkpoint','Normal post-commit path','정상적인 Commit 이후 경로',B)+p('M1080 192H1095V462H1080')
v+=t(40,550,'Commit marks a recoverable transaction; checkpoint permits safe journal reuse.','Commit은 복구 가능한 Transaction, Checkpoint는 안전한 Journal 재사용의 기준이다.',19,650)
fig('disk-io-04-journal-transaction.svg','JBD2 commit, replay and checkpoint','JBD2 Commit, Replay와 Checkpoint','Conceptual full transaction; fast commits and checksums omitted','Full Transaction 개념도 · Fast Commit과 Checksum 세부 생략',v,599)
# 05 persistence sequence and measured calls
v=t(40,130,'Same-directory replacement','같은 디렉터리에서 파일 교체',22,700)+t(665,130,'Verified observation','검증한 결과',22,700)
for i,(e,k,sub,ks,a,ak,c) in enumerate([('Write temporary file','임시 파일 쓰기','4096 bytes accepted','4096바이트 쓰기 성공','Pre-sync read matches','동기화 전 읽기 일치',B),('fsync(file)','fsync(file)','Synchronize staged contents','임시 파일 내용 동기화','Call returned successfully','호출 정상 반환',G),('rename over target','대상 이름으로 rename','Publish replacement name','교체 파일 이름 공개','Old FD still reads old bytes','기존 FD는 이전 내용 읽기',A),('fsync(directory)','fsync(directory)','Synchronize name change','이름 변경 동기화','New target bytes match','새 파일 데이터 일치',G)]):
 y=150+i*92;v+=n(40,y,560,75,e,k,sub,ks,c)+p(f'M600 {y+37}H645')+n(645,y,435,75,a,ak)
 if i<3:v+=p(f'M320 {y+75}V{y+92}')
v+=t(40,574,'Readback is visibility evidence, not a simulated power-loss result.','Readback은 가시성의 증거이며 전원 장애 실험 결과가 아니다.',20,650)
fig('disk-io-05-durability.svg','File and directory durability boundaries','파일과 디렉터리의 영속성 경계','Executed 4096-byte replacement in a temporary directory','임시 디렉터리에서 수행한 4096바이트 파일 교체',v,622,('Actual syscall checks · no crash test or latency benchmark','실제 시스템 호출 검증 · 장애 및 지연 시간 실험 없음'))
# 06 observation scopes with equal-rate examples.
v=n(40,115,320,75,'Task accounting','태스크 Accounting','pidstat / proc PID io','pidstat / proc PID io')+n(400,115,320,75,'Filesystem work','파일시스템 작업','Writeback / JBD2','Writeback / JBD2',A)+n(760,115,320,75,'Device accounting','장치 Accounting','iostat / diskstats','iostat / diskstats',G)+p('M360 152H400')+p('M720 152H760')
v+=t(40,243,'Same throughput, different request pattern','같은 Throughput, 다른 요청 패턴',22,700)
v+=t(55,284,'Requests/s','초당 요청 수',18,650)+t(360,284,'Request size','요청 크기',18,650)+t(680,284,'Throughput','Throughput',18,650)
for i,(count,size) in enumerate([(6400,4),(100,256)]):
 y=304+i*85
 v+=r(40,y,1040,72,'#f2f6fa','#c4d3df')+t(55,y+43,str(count),None,25,750)+t(360,y+43,f'{size} KiB',None,25,700)+t(680,y+43,'25 MiB/s',None,25,750)
v+=t(40,516,'Correlate request rate, size, latency, queue depth and device mapping.','요청 횟수, 크기, 지연 시간, 큐 길이 및 장치 매핑을 함께 확인한다.',20,650)
fig('disk-io-06-accounting.svg','I/O attribution across observation scopes','관측 범위에 따른 I/O 귀속','Synthetic arithmetic examples; no historical device benchmark','가상 계산 예시 · 당시 장치 성능 측정값 아님',v,564)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs; {len(L)} unique labels')
