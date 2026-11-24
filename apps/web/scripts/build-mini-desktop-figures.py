#!/usr/bin/env python3
"""Mini-Desktop diagrams from the original 2023 65-page PDF (64 content + blank).
Real diagrams/results are reconstructed into scalable vectors; screenshots are
NOT upscaled, traced as exact pixels, nor misrepresented as new measurements.
The source PDF is not included because it contains contributor identifiers.
"""
from pathlib import Path
import html,xml.etree.ElementTree as ET,json
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'apps/web/public/figures/journals'
GLOSS=ROOT/'apps/web/i18n/svg-ko-overrides.json'
DIR.mkdir(parents=True,exist_ok=True)
LO={}
def tr(x,y,en,ko=None,size=22,weight=500,color='#263746',anchor='start',family='Inter,Noto Sans KR,Arial,sans-serif'):
  ko=ko or en
  LO.setdefault(en,ko)
  return f'<text x="{x}" y="{y}" fill="{color}" text-anchor="{anchor}" font-family="{family}" font-size="{size}" font-weight="{weight}">{html.escape(str(en))}</text>'
def box(x,y,w,h,fill='#fff',stroke='#a3b7c9',r=8,sw=2):
  return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}"/>'
def path(d,col='#287fbd',sw=3,tip=False,dash=False):
  return f'<path d="{d}" stroke="{col}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round"'+(' marker-end="url(#arr)"' if tip else '')+(' stroke-dasharray="6 6"' if dash else '')+'/>'
def arr(x,y,X,Y,col='#287fbd',sw=3):
  return path(f'M{x} {y}L{X} {Y}',col,sw,True)
def node(x,y,w,h,en,ko=None,detail='',dko=None,fill='#e7edf2',stroke='#244b79'):
  s=box(x,y,w,h,fill,stroke,3,2.3)
  s+=tr(x+w/2,y+33,en,ko,22,700,'#20384d','middle')
  if detail:s+=tr(x+w/2,y+60,detail,dko,16,500,'#5b6c7a','middle')
  return s
def plate(x,y,w,h,name,ko,sub='',subko=''):
  s=box(x,y,w,h,'#dce2e8','#7e93a9',0,3)
  s+=tr(x+w/2,y-14,name,ko,22,730,'#243b50','middle')
  if sub:s+=tr(x+w/2,y+h-22,sub,subko,15,560,'#415366','middle')
  return s
def fig(n,slug,title,ko,sub,kosub,body,foot='Source-grounded vector reconstruction · not the original screenshot',kofoot='원본 보고서 기반 벡터 재구성 · 원본 캡처 아님',H=760):
  W=1260;LO.setdefault(title,ko)
  s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}"><defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M1 1L9 5L1 9z" fill="#287fbd"/></marker></defs>'
  s+=box(0,0,W,H,'#fff','#cdd8e1',17,2)
  s+=box(31,29,7,54,'#204e82','#204e82',2,1)
  s+=tr(54,60,title,ko,31,760)
  s+=tr(55,94,sub,kosub,18,520,'#647789')
  s+=path('M40 119H1220','#d7e1e9',1)
  s+=body+path(f'M40 {H-62}H1220','#d7e1e9',1)
  s+=tr(46,H-28,foot,kofoot,15,440,'#6d8090')+'</svg>\n'
  p=DIR/f'mini-desktop-{n:02d}-{slug}.svg'
  p.write_text(s);ET.parse(p)
  print(p.name,p.stat().st_size)
# 01: preserve the visual arrangement of the report's page 3 (ultrasonic, Board 1, five switches, Board 2, Board3).
s=box(37,171,1185,461,'#fff','#333',0,3)
s+=plate(170,272,196,291,'Board 1','Board 1','Tasks 1 · 5 · 8','Task 1·5·8')
s+=plate(542,272,204,291,'Board 2','Board 2','Tasks 2 · 3 · 4','Task 2·3·4')
s+=plate(945,272,225,291,'Board 3','Board 3','Tasks 6 · 7 · 9 · 10','Task 6·7·9·10')
s+=node(58,290,92,85,'Sensor','센서','HCSR04','HCSR04')
s+=arr(150,333,165,333,'#68a3d4')
for i,(n,label) in enumerate([('SW1','UP'),('SW2','DOWN'),('SW3','LEFT'),('SW4','RIGHT'),('B1','CLICK')]):
 y=302+i*52;s+=node(427,y,91,43,n,n,fill='#f4f6f8');s+=tr(520,y+30,label,label,15,600)
 s+=arr(518,y+22,536,y+22,'#68a3d4')
for i,(en,ko) in enumerate([('Sleep','Sleep'),('Distance','Distance')]):
 y=198+i*44;s+=path(f'M366 {y+130}H{864+i*22}V{y+182}H938','#e4ac2e',4,True);s+=tr(405,y+116,en,ko,16,600,'#91670f')
for i,(en,ko) in enumerate([('Enable','Enable'),('Direction (2 bits)','Direction (2-bit)'),('Click','Click')]):
 y=403+i*48;s+=arr(746,y,933,y,'#e4ac2e',4);s+=tr(756,y-11,en,ko,16,560,'#946811')
s+=path('M542 571H478V605H177V563','#e4ac2e',4,True)
s+=tr(378,624,'Move enable → Board 1','Move Enable → Board 1',16,600,'#946811','middle')
fig(1,'overall-system','Three-board system · original block arrangement','세 보드의 전체 구조를 원본 배치대로','Report p.3 · blue: input/internal flow · yellow: GPIO across boards','보고서 3쪽 · 파란 선은 입력/보드 내부, 노란 선은 보드 간 GPIO',s)
# 02: fix role confusion, GPIO vs uart
s=plate(71,240,294,333,'Board 1','Board 1','Ultrasonic + sleep','초음파 센서·절전 제어')
s+=plate(481,240,294,333,'Board 2','Board 2','Button + cursor signals','버튼·커서 신호')
s+=plate(896,240,294,333,'Board 3','Board 3','ASCII terminal renderer','문자 기반 화면 출력')
s+=node(96,306,244,88,'HCSR04 / 6-bit','HCSR04 / 6-bit','distance + sleep','거리·Sleep')
s+=node(505,306,244,88,'SW1–SW4 / B1','SW1–SW4 / B1','movement + click','이동·Click')
s+=node(920,306,244,88,'PrintNCalculate','PrintNCalculate','screen array → UART2','화면 문자열 → UART2')
s+=path('M365 361H888','#e4ac2e',4,True)
s+=path('M775 420H888','#e4ac2e',4,True)
s+=path('M624 573V610H216V574','#e4ac2e',4,True)
s+=tr(423,332,'GPIO (distance, sleep)','GPIO (Distance·Sleep)',18,630,'#8a690c')
s+=tr(781,410,'GPIO','GPIO',17,650,'#8a690c')
s+=arr(1179,351,1230,351,'#236a9b')
s+=tr(920,632,'UART2 → PC terminal, not the inter-board control bus','UART2는 PC Terminal 출력이며 보드 간 제어 Bus가 아니다',17,580)
fig(2,'gpio-versus-uart','GPIO between boards; UART to the terminal','보드 간 GPIO와 Terminal UART를 구분했다','Report pp.3, 12, 15–19 · board-to-board control is GPIO','보고서 3·12·15–19쪽 · 보드 사이 신호는 GPIO',s)
# 03: board1 source
s+= ''
s=plate(402,208,405,432,'Board 1','Board 1','Distance and sleep logic','거리·절전 로직')
for i,(a,b,d) in enumerate([('Task 1','ULTRASONIC','HCSR04 → Distance'),('Task 5','SleepCount','15s inactivity'),('Task 8','SleepButton','Manual sleep toggle')]):
 y=265+i*119;s+=node(445,y,317,91,a,a,b,b,fill='#f7f9fb')
 s+=tr(837,y+52,d,{'HCSR04 → Distance':'HCSR04 → Distance','15s inactivity':'15초 무입력','Manual sleep toggle':'수동 Sleep 전환'}[d],19,560)
s+=node(64,308,255,87,'HCSR04','HCSR04','TRIG / ECHO','TRIG / ECHO')
s+=arr(319,351,398,351,'#68a3d4')
s+=tr(902,636,'priority: 1 / 2 / 3','Priority: 1 / 2 / 3',18,650)
fig(3,'board1-original','Board 1 · sensor and sleep tasks','Board 1 · 초음파와 절전 Task','Report p.4 · three tasks and original gray block layout','보고서 4쪽 · 세 Task와 회색 원본 블록 배치',s)
# 04: GPIO pin mapping sensor
s=box(67,203,1147,400,'#f7fafc','#a7b7c7',11,2)
s+=node(101,272,285,97,'HCSR04','HCSR04','VCC 5V / GND','VCC 5V / GND')
s+=node(503,275,342,94,'STM32 TIM3','STM32 TIM3','Input Capture CH1','Input Capture CH1')
s+=arr(386,311,490,311)
s+=arr(490,346,396,346,'#c28c39')
s+=tr(402,296,'TRIG PA5','TRIG PA5',16,600,'#267ba1')
s+=tr(401,370,'ECHO PA6','ECHO PA6',16,600,'#b2822f')
s+=box(882,262,286,116,'#edf3f9','#32658c',9,2)
s+=tr(1025,310,'ECHO pulse width','ECHO Pulse Width',23,690,anchor='middle')
s+=tr(1025,346,'Rise → Fall','Rising → Falling',18,520,anchor='middle')
s+=path('M126 489H385V459H619V489H887','#286f96',3)
s+=tr(636,455,'Difference (µs)','Difference (µs)',17,630,'#286f96','middle')
s+=tr(100,558,'distance_cm = Difference × 0.034 / 2','distance_cm = Difference × 0.034 / 2',24,700)
fig(4,'ultrasonic-input-capture','Ultrasonic timing with TIM3 Input Capture','TIM3 Input Capture로 측정한 초음파 시간','Report pp.5–8 · HCSR04 TRIG/ECHO + rising/falling edge','보고서 5–8쪽 · HCSR04 TRIG·ECHO와 Rising·Falling Edge',s)
# 05: sixbit mapping exact
pins=[('5','PC9'),('4','PC8'),('3','PB8'),('2','PC6'),('1','PB9'),('0','PC5')]
s=box(68,217,1123,351,'#f9fbfd','#c3d2df',12,2)
s+=tr(89,254,'Board 1 output','Board 1 Output',22,700)
s+=tr(851,254,'Board 3 input','Board 3 Input',22,700)
for j,(bit,pin) in enumerate(pins):
 y=273+j*45
 s+=box(215,y,208,37,'#e6f1f9','#487cad',3,1)
 s+=tr(231,y+26,f'Distance[{bit}]',f'Distance[{bit}]',16,600)
 s+=arr(423,y+17,743,y+17,'#dfb23b',2)
 s+=box(766,y,230,36,'#e9f1f5','#5b7c92',3,1)
 s+=tr(783,y+25,pin,pin,18,700)
s+=tr(116,624,'6 bits encode 0–63cm; values beyond 63 are saturated','6-bit로 0–63cm 표현 · 63cm 초과 시 Saturation',19,600)
fig(5,'distance-sixbit-gpio','Six GPIO lines carried the distance','6개의 GPIO로 Distance 값을 보냈다','Report pp.7, 25 · source pin map used on Board 3','보고서 7·25쪽 · Board 3에서 읽는 실제 Pin Map',s)
# 06: board2 gray source
s=plate(418,214,440,416,'Board 2','Board 2','Cursor + click','Cursor·Click')
for j,(a,ka,detail,kdet) in enumerate([('Task 2','Task 2','Click_Task','Click_Task'),('Task 3','Task 3','MOVE_Task','MOVE_Task'),('Task 4','Task 4','NONE_Task','NONE_Task')]):
 y=258+j*120;s+=node(470,y,334,91,a,ka,detail,kdet)
for j,btn in enumerate(['B1','SW1','SW2','SW3','SW4']):
 x=91;y=252+j*66;s+=node(x,y,111,50,btn,btn,fill='#f5f6f8')
 target=300 if j==0 else 387
 s+=path(f'M202 {y+24}H279V{target}H460','#5e9acb',2.5,True)
for j,(name,pin) in enumerate([('Click','PC1'),('Direction 1','PA7'),('Direction 0','PA6'),('Enable','PB6')]):
 y=290+j*70;s+=arr(858,y,1084,y,'#e0ad2e',3)
 s+=tr(882,y-12,name+' / '+pin,name+' / '+pin,17,620,'#8e6818')
fig(6,'board2-original','Board 2 · switch processing and GPIO','Board 2 · 스위치와 GPIO 출력','Report pp.12–14 · Click, Move, None and their output pins','보고서 12–14쪽 · Click·Move·None과 출력 Pin',s)
# 07: cursor truth table source pin on board3 C0/C1/C2 order note
s=box(56,184,1144,450,'#fff','#b6c9d9',12)
cols=[91,425,679,909];head=['Action','PC0 (C0)','PC1 (C1)','PC2 Enable']
kh=['동작','PC0 (C0)','PC1 (C1)','PC2 Enable']
for j,x in enumerate(cols):s+=tr(x,235,head[j],kh[j],21,740)
rows=[('Up','1','1','1'),('Left','1','0','1'),('Down','0','1','1'),('Right','0','0','1'),('Stop','X','X','0')]
for i,row in enumerate(rows):
 y=260+i*66;s+=box(78,y,1086,59,'#f2f6f9' if i%2==0 else '#fff','#d2dce3',2,1)
 for j,v in enumerate(row):s+=tr(cols[j],y+38,v,{'Up':'위','Left':'왼쪽','Down':'아래','Right':'오른쪽','Stop':'정지'}.get(v,v),21,660)
s+=tr(94,666,'Board 3 decodes two direction bits only when Enable = 1','Board 3은 Enable = 1일 때만 두 Direction Bit를 해석한다',18,560)
fig(7,'cursor-direction-encoding','Cursor movement encoded with two bits','커서 방향을 두 Bit로 표현했다','Report p.17 · action truth table from Board 3 decode','보고서 17쪽 · Board 3의 Direction Decode Table',s)
# 08 Board3 original tasks
s=plate(377,235,511,417,'Board 3','Board 3','Desktop display and games','화면·게임 처리')
tasks=[('Task 6','PrintNCalculate'),('Task 7','Sleep'),('Task 9','Gomoku'),('Task 10','Curling')]
for i,(n,name) in enumerate(tasks):
 x=409+(i//2)*236;y=289+(i%2)*154
 s+=node(x,y,210,113,n,n,name,name)
s+=tr(72,354,'GPIO inputs →','GPIO 입력 →',21,670,'#977126')
s+=arr(190,354,366,354,'#dba72c',3)
s+=arr(888,362,1124,362,'#1e7eae',3)
s+=tr(927,339,'UART2 → PC terminal','UART2 → PC Terminal',18,650,'#226783')
s+=path('M619 350H650V507','#61a0cb',2.5)
s+=tr(90,638,'CoordinateMutex protects screen arrays and UART output consistency','CoordinateMutex가 화면 배열과 UART 출력의 일관성을 보호한다',17,570)
fig(8,'board3-original','Board 3 · screen and two games','Board 3 · 화면 처리와 두 게임','Report pp.15, 19–24 · 4 tasks and original block geometry','보고서 15·19–24쪽 · 네 Task와 원본 블록 구성',s)
# 09 timers/ priorities explicit from appendix
s=box(55,187,1144,452,'#fbfcfd','#d1dce5',12)
for x,head,ko,rows in [
 (76,'Board 1','Board 1',[('SleepCount',1),('ULTRASONIC',2),('SleepButton',3)]),
 (454,'Board 2','Board 2',[('MOVE',1),('NONE',2),('CLICK',2)]),
 (837,'Board 3','Board 3',[('Gomoku / Curling',1),('PrintNCalculate',2),('Sleep',3)])]:
 s+=tr(x,235,head,ko,23,750)
 for j,(name,pri) in enumerate(rows):
  y=278+j*88;s+=box(x,y,329,73,'#f0f6fa','#bed0df',8,1)
  s+=tr(x+13,y+31,name,name,18,620)
  s+=tr(x+13,y+57,'priority '+str(pri),'Priority '+str(pri),15,570,'#356b86')
s+=tr(71,609,'Board 2: narrative says Move > None, but actual xTaskCreate sets Move=1 and None=2','Board 2: 설명은 Move 우선, 실제 생성 코드는 Move=1·None=2',18,630,'#9b5830')
fig(9,'task-priority-source','Ten FreeRTOS tasks and their coded priorities','10개 FreeRTOS Task와 생성 코드의 Priority','Report appendix pp.37–38, 43, 63 · task creation values','보고서 Appendix 37–38·43·63쪽 · xTaskCreate 값',s)
# 10 scheduler/sleep timeline
s=box(50,205,1155,355,'#f8fbfd','#c4d3df',11)
for j,(a,ka,b,kb) in enumerate([('0–15s','0–15초','Active / presence','활동·사용자 감지'),('15s inactivity','15초 무입력','Auto sleep requested','자동 절전 요청'),('PB4 button','PB4 버튼','Manual sleep toggle','수동 Sleep 전환')]):
 x=88+j*372;s+=node(x,303,327,112,a,ka,b,kb)
 if j<2:s+=arr(x+327,357,x+367,357,'#d9a22b')
s+=tr(76,494,'The report describes both motion-enable reset and sensor-presence tracking','원본에는 Move Enable과 초음파 Presence 두 경로가 기록돼 있다',20,600)
s+=tr(78,605,'State-change sequence; not a measured RTOS latency trace','상태 전환 흐름이며 측정한 RTOS Latency 파형은 아니다',19,480)
fig(10,'sleep-entry-logic','Automatic and button-triggered sleep','무입력 자동 절전과 수동 절전 버튼','Report pp.9–10, 19 · 15s and Board 1 SleepButton','보고서 9–10·19쪽 · 15초, Board 1 SleepButton',s)
# 11 coordinate mutex corruption
s=box(47,190,566,424,'#f9fbfd','#aebfcf',12)
s+=box(648,190,562,424,'#f9fbfd','#aebfcf',12)
s+=tr(78,243,'Without CoordinateMutex','CoordinateMutex가 없으면',22,740,'#ba5f3c')
s+=tr(681,243,'With CoordinateMutex','CoordinateMutex로 보호하면',22,740,'#207c62')
for x,bad in [(95,True),(687,False)]:
 s+=box(x,285,453,246,'#0b0b0b','#414e59',5,2)
 for k in range(7):
  y=307+k*31
  text='|' + ('. '*16 if not bad or k%2==0 else '  /* unexpected */  ')+'|'
  s+=tr(x+16,y+18,text,text,16,500,'#dae5e1',family='monospace')
s+=tr(95,562,'UART renders a mixture of old and new characters','UART에서 이전·새 배열 문자들이 섞여 출력',16,500)
s+=tr(687,562,'Single protected frame assembled for printing','일관된 화면 문자열을 보호해 출력',16,500)
fig(11,'coordinate-mutex-tearing','A shared terminal frame can tear','화면 출력 중 배열을 바꾸면 생기는 문제','Report pp.15–18, 30 · illustrated failure mode, not an original screen capture','보고서 15–18·30쪽 · 원본 설명을 따른 재구성, 캡처 아님',s)
# 12 cursor render layer
s=box(58,190,1148,440,'#f8fbfd','#ced9e2',10)
layers=[('Sleep blank screen','Sleep일 때 Blank Screen'),('Cursor','Cursor'),('Active window','최상단 Window'),('Lower window','아래 Window'),('Desktop icons','Desktop Icon / Background')]
for i,(name,ko) in enumerate(layers):
 x=95+i*229;y=253+i*47
 s+=box(x,y,320,138,'#dbe9f3' if i%2 else '#edf3f7','#5983a6',7,2)
 s+=tr(x+16,y+33,name,ko,20,680)
s+=tr(105,595,'isChange = 1 → rebuild; calculate ~50ms, print ~200ms in report','isChange=1일 때 재구성 · 계산 약 50ms, 출력 약 200ms',19,600)
fig(12,'ascii-compositor','Layer order of the UART desktop renderer','UART Desktop 화면의 Layer 순서','Report pp.17–19 · cursor, windows and display update flag','보고서 17–19쪽 · Cursor·Window·isChange 출력 제어',s)
# terminal helpers
def terminal(x,y,w,h,window='gomoku',shift=0):
 b=box(x,y,w,h,'#08090c','#282e35',4,3)
 b+=box(x,y,w,34,'#1e2028','#1e2028',3,1)
 for i,c in enumerate(['#fa625b','#f3bd4b','#5fbe69']):
  b+=f'<circle cx="{x+21+i*18}" cy="{y+16}" r="6" fill="{c}"/>'
 b+=tr(x+105,y+24,'screen /dev/tty.usbmodem','screen /dev/tty.usbmodem',14,480,'#b5b6bc',family='monospace')
 b+=box(x+17,y+73,100,48,'#050505','#7a7e83',0,1)
 b+=tr(x+30,y+103,'Gomoku','Gomoku',16,550,'#b1b7be',family='monospace')
 b+=box(x+17,y+130,100,48,'#050505','#7a7e83',0,1)
 b+=tr(x+30,y+160,'Curling','Curling',16,550,'#b1b7be',family='monospace')
 if window=='gomoku':
  bx=x+156+shift;by=y+94
  b+=box(bx,by,w-211,305,'#0c0c0d','#7d8589',0,1)
  b+=tr(bx+15,by+24,'Gomoku ─────────────── [X]','Gomoku ─────────────── [X]',15,520,'#c5c8cd',family='monospace')
  for i in range(12):
   content='.'.join(['.' for _ in range(18)])
   if i==4: content='....O...X...O...X....'
   b+=tr(bx+22,by+49+i*18,content,content,12,500,'#d4d7db',family='monospace')
 else:
  bx=x+145+shift;by=y+112
  b+=box(bx,by,w-188,335,'#0c0c0e','#707e86',0,1)
  b+=tr(bx+17,by+23,'Curling       P1:[19] P2:[18]','Curling       P1:[19] P2:[18]',14,550,'#e3e5e6',family='monospace')
  for i in range(10):
   text='#########' if i in [0,9] else ('###*****###' if i in [2,7] else '###**X**###' if i in [4,5] else '####***####')
   b+=tr(bx+90,by+62+i*22,text,text,16,500,'#d2d5d7',family='monospace')
 return b
s=terminal(67,213,541,439,'gomoku')+terminal(653,213,541,439,'curling')
fig(13,'terminal-ui-gomoku-curling','Gomoku and Curling as ASCII windows','Gomoku·Curling을 ASCII Window로 구현했다','Report pp.20–26, 31 · recreated screen motif, not source pixel tracing','보고서 20–26·31쪽 · 터미널 형태를 벡터로 재구성, 캡처 복제 아님',s)
# 14 window drag original screenshot before / after
s=terminal(53,217,560,429,'gomoku')+terminal(644,217,560,429,'gomoku',70)
s+=tr(189,682,'Before drag','Drag 이전',18,650)
s+=tr(814,682,'After drag','Drag 이후',18,650)
fig(14,'window-drag-before-after','Click + direction buttons moved a window','Click과 방향 버튼으로 Window를 이동했다','Report pp.28–31 · states illustrated; exact source pixels not reproduced','보고서 28–31쪽 · 상태 변화를 설명하는 벡터 도식',s)
# 15 curling 6-bit, scoring
s=box(57,191,1146,439,'#fbfdfe','#c5d6e2',12)
s+=node(84,275,288,126,'Distance 6-bit','Distance 6-bit','0–63cm / Board 1','0–63cm / Board 1')
s+=node(472,274,283,126,'Curling_Task','Curling_Task','target at ~15cm','Target 약 15cm')
s+=node(842,274,288,126,'Score / ball','Score / Ball','O = P1, X = P2','O = P1, X = P2')
s+=arr(372,335,462,335,'#d7a22f',3)+arr(755,335,834,335,'#287fbd',3)
s+=tr(88,486,'A cap or small object moves toward the sensor during the round','병뚜껑 등 물체를 초음파 센서 쪽으로 움직여 게임 진행',20,540)
s+=tr(88,536,'Report example: P1 9 → 19 (+10 points)','원본 실행 예시: P1 9 → 19 (+10점)',20,720,'#20715b')
fig(15,'curling-distance-game','Distance-driven Curling interaction','초음파 거리로 Curling 게임을 제어했다','Report pp.22–26 · 6-bit sensor input and visible scoring example','보고서 22–26쪽 · 6-bit 센서 입력과 실제 점수 변화 예시',s)
# 16 sleep snapshot / mutex
s=box(62,201,1130,407,'#f8fbfd','#c5d2df',12)
s+=node(94,307,301,123,'Screen active','Screen Active','screenState = 1','screenState = 1')
s+=node(482,307,298,123,'Sleep_Task','Sleep_Task','SleepMutex / isChange','SleepMutex / isChange')
s+=node(871,307,288,123,'Blank screen','Blank Screen','screenState = 0','screenState = 0')
s+=arr(395,365,470,365,'#d5a737')+arr(780,365,859,365,'#d5a737')
s+=path('M1019 434V513H237V433','#287fbd',3,True)
s+=tr(614,495,'Resume → restore screen updates','Resume → 화면 갱신 재개',18,630,'#276d8e','middle')
s+=tr(92,570,'The report demonstrates a blank screen; full task pause requires correct mutex use','원본에는 Blank Screen이 확인되지만 Task 일시정지는 Mutex 동작 검토가 필요',18,500)
fig(16,'sleep-resume-screen','Sleep changes display state and gates work','Sleep은 화면 상태와 작업 진행을 함께 제어했다','Report pp.19–20, 30–32 · source behavior and mutex contract','보고서 19–20·30–32쪽 · 화면 전환과 Mutex 경계',s)

mapping=json.loads(GLOSS.read_text())
added=0
for en,ko in LO.items():
  if en not in mapping: mapping[en]=ko;added+=1
GLOSS.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
print('GENERATED',len(list(DIR.glob('mini-desktop-[0-9][0-9]-*.svg'))),'new native SVGs,',added,'new translations; older translations unchanged')
