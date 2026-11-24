#!/usr/bin/env python3
"""Escape From The Dark: report-derived vector diagrams (June 20, 2023).
Engineering diagrams use report values; schematic positions are not hardware measurements.
Pixel art is generated separately from source-derived logical grids, not from resized palette traces.
The report and raw bitmaps are not committed.
"""
from pathlib import Path
import html, json, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'apps/web/public/figures/journals'
LO={}
def t(x,y,en,ko=None,size=22,color='#25364b',anchor='start',weight=500):
    LO.setdefault(en,ko or en)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(en)}</text>'
def rect(x,y,w,h,fill='#fff',stroke='none',r=0,sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{r}"/>'
def line(x,y,X,Y,c='#497ca8',sw=2,dash=False,arrow=False):
    return f'<path d="M{x} {y}L{X} {Y}" fill="none" stroke="{c}" stroke-width="{sw}"'+(' stroke-dasharray="7 5"' if dash else '')+(' marker-end="url(#arr)"' if arrow else '')+'/>'
def node(x,y,w,h,en,ko,sub='',ksub='',fill='#edf4fa'):
    return rect(x,y,w,h,fill,'#92acc2',9)+t(x+w/2,y+34,en,ko,23,anchor='middle',weight=700)+(t(x+w/2,y+62,sub,ksub,17,anchor='middle') if sub else '')
def fig(slug,title,ko,sub,ksub,body,h=590):
    LO.setdefault(title,ko)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(title)}"><defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#497ca8"/></marker><pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="#8da3bd"/></pattern></defs>'
    s+=rect(1,1,1118,h-2,'#fff','#d0dbe6',14)+rect(24,28,6,50,'#285d90')+t(44,54,title,ko,29,weight=750)+t(45,84,sub,ksub,17,'#61758b')+line(40,105,1080,105,'#dbe4eb',1)
    s+=body+line(40,h-44,1080,h-44,'#dbe4eb',1)+t(45,h-16,'June 2023 report · vector explanation','2023년 6월 보고서 · 벡터 설명도',14,'#61758b')+'</svg>\n'
    p=DIR/(slug+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
# Camera. World and viewport dimensions are drawn at the same scale; origin example (180,60).
b=rect(60,155,540,240,'#101827','#384f68',2)
for x,y,w in [(20,210,95),(175,165,110),(370,95,100),(455,220,70),(240,65,55)]:
    b+=rect(60+x,155+y,w,4,'#8399ac')
b+=rect(240,215,160,120,'#263b52','#23b9c7',0,3)+rect(240+76,215+57,8,6,'#f9c74f','#f9c74f')+rect(240+80-6,215+60-8,12,16,'#39dbe0')
b+=t(60,140,'540 × 240 world','540 × 240 월드',20)+t(320,365,'160 × 120','160 × 120',20,anchor='middle')+line(240,338,240,390,'#497ca8',1,True)
b+=t(62,425,'Origin ranges: x_map 0–380; y_map 0–120','카메라 기준점: x_map 0–380, y_map 0–120',19)
b+=rect(680,150,352,264,'#eef4fa','#92acc2',8)+rect(680+76*2.2,150+57*2.2,8*2.2,6*2.2,'#f9c74f','#b58a24',2)
b+=line(680+76*2.2,150,680+76*2.2,414,'#c68b22',1,True)+line(680+84*2.2,150,680+84*2.2,414,'#c68b22',1,True)+line(680,150+57*2.2,1032,150+57*2.2,'#c68b22',1,True)+line(680,150+63*2.2,1032,150+63*2.2,'#c68b22',1,True)
b+=t(847,139,'76','76',17,anchor='end')+t(865,139,'84','84',17)+t(1038,269,'57','57',16)+t(1038,302,'63','63',16)
b+=t(856,443,'Dead zone: 8 × 6','Dead Zone: 8 × 6',20,anchor='middle',weight=700)+t(60,485,'world = scan + camera offset','월드 좌표 = 스캔 좌표 + 카메라 Offset',23,weight=700)
fig('escape-02-camera','Camera and coordinate frames','카메라와 좌표계','Example viewport; dimensions and thresholds follow the RTL','예시 화면 위치 · 크기와 임계값은 RTL 기준',b,550)
# Screen states
b=node(75,180,240,90,'0 · START','0 · 시작','life = 3, key = 0','life = 3, key = 0')+node(430,180,240,90,'1 · PLAY','1 · 플레이','life / key / position','생명 / 열쇠 / 좌표')+node(815,125,235,90,'2 · FAILURE','2 · 실패','life == 0','life == 0','#fff0ee')+node(815,305,235,90,'3 · SUCCESS','3 · 성공','key == 5 + door','key == 5 + 출구','#e7f5ee')
b+=line(315,225,430,225,arrow=True)+t(372,209,'Any key','아무 버튼',16,anchor='middle')
b+=line(670,205,815,170,arrow=True)+line(670,245,815,350,arrow=True)
b+=rect(430,310,240,120,'#f6f9fc','#a6bacb',8)+t(550,342,'Hit → life − 1','피격 → life − 1',20,anchor='middle')+t(550,374,'Key → key + 1','획득 → key + 1',20,anchor='middle')+t(550,406,'Fall → life = 0','낙하 → life = 0',20,anchor='middle')
b+=line(550,270,550,310,arrow=True)+line(75,470,1050,470,'#a6bacb',2,True)+line(195,470,195,270,arrow=True)+line(932,395,932,470,'#497ca8',2)+line(1035,215,1035,470,'#497ca8',2)
b+=t(550,502,'Reset (active low) returns to START','Reset (active-low) → 시작 화면',20,anchor='middle')
fig('escape-03-game-state','Game screen transitions','게임 화면 상태 전이','Registered state; success and failure checks are separate in the RTL','레지스터 상태 · 성공 및 실패는 별도 조건',b,570)
# divider thresholds
names=[('System','system',30000),('Projectile','포탄',200000),('Horizontal player','가로 이동',300000),('Warder','적 이동',500000),('Player motion','캐릭터 모션',1000000)]
b=''
for i,(en,ko,v) in enumerate(names):
    y=130+i*65
    b+=t(52,y+25,en,ko,21)+rect(290,y,700,35,'#e9eff5',r=4)+rect(290,y,700*v/1000000,35,'#3b83b9',r=4)+t(1000,y+25,f'{v:,}',size=19)
b+=node(65,475,475,78,'Vertical player','세로 이동','30,000 × y_speed_count','30,000 × y_speed_count')+node(580,475,475,78,'Sword','검','300,000 / sword_speed_count','300,000 / sword_speed_count')
fig('escape-04-clock-rates','Clock divider thresholds','Clock Divider 기준값','Nominal fixed thresholds; variable dividers shown separately','고정 기준값과 가변 기준값을 구분',b,615)
# Jump multiplier plot. One pixel per update, interval not physical trajectory.
b=t(70,146,'Interval multiplier','이동 간격 배수',20,weight=700)+line(110,400,1030,400,'#8299ad',2)+line(110,175,110,400,'#8299ad',2)
for n in [1,5,10,15,20]:
    y=400-n*10
    b+=line(110,y,1030,y,'#dde5eb',1,True)+t(95,y+6,str(n),size=16,anchor='end')
# discrete update sequence 1..20, descending 20..5, then constant
seq=list(range(1,21))+list(range(19,4,-1))+[5]*5
coords=[(110+i*22.5,400-n*10) for i,n in enumerate(seq)]
d='M'+' L'.join(f'{x:g} {y:g}' for x,y in coords)
b+=f'<path d="{d}" fill="none" stroke="#287cb5" stroke-width="3.5"/>'
for x,y in coords:b+=f'<circle cx="{x}" cy="{y}" r="3.7" fill="#287cb5"/>'
b+=line(110+19*22.5,185,110+19*22.5,400,'#cc7e38',2,True)
b+=t(275,170,'Rise: 1 → 20','상승: 1 → 20',22,anchor='middle',weight=700)+t(735,170,'Fall: 20 → 5','하강: 20 → 5',22,anchor='middle',weight=700)+t(995,334,'5','5',18)
b+=t(570,438,'Successive vertical updates (one pixel each)','세로 방향 갱신 순서 (매번 한 픽셀)',20,anchor='middle')
b+=node(110,470,920,75,'Step interval ∝ y_speed_count','이동 간격 ∝ y_speed_count','Illustrative uninterrupted jump; actual collisions can interrupt it.','장애물과 부딪히지 않는 예시 · 실제 충돌 시 변화')
fig('escape-05-jump','Discrete jump and fall','이산적인 점프와 낙하','Divider multiplier sequence from the report; not a measured trajectory','보고서의 Divider 배수 변화 · 실측 궤적 아님',b,600)
# Collision
b=rect(70,170,480,260,'#f6f9fc','#b4c5d5',6)+rect(145,230,180,120,'#a4d7df','#248794',3)+rect(265,270,190,115,'#f5c6a1','#c17b3c',3)+rect(265,270,60,80,'#97a793','#758b72')
b+=t(180,216,'Player A','캐릭터 A',20)+t(345,410,'Object B','오브젝트 B',20)+t(295,319,'Overlap','겹침',15,anchor='middle')
b+=node(620,165,435,82,'Horizontal overlap','가로 방향 겹침','ax < bx + hx; bx < ax + hx','ax < bx + hx; bx < ax + hx')+node(620,270,435,82,'Vertical overlap','세로 방향 겹침','ay < by + hy; by < ay + hy','ay < by + hy; by < ay + hy')+node(620,375,435,82,'Both → collision','두 조건 → 충돌','Warder margins: hx = 11, hy = 13','적과의 여유: hx = 11, hy = 13','#e7f5ee')
b+=line(550,300,620,300,arrow=True)+t(75,475,'Platform edge: move back by one pixel','플랫폼 경계: 한 픽셀만큼 위치 보정',20,weight=700)
fig('escape-06-collision','Collision from coordinate comparisons','좌표 비교 기반 충돌','Schematic rectangles; combined margins follow the warder predicate','설명용 사각형 · 적의 충돌 여유는 원본 조건 기준',b,540)
# Sword anchor and spawn selector
b=rect(55,155,500,285,'#f5f9fc','#b4c5d5',7)+rect(105,240,75,112,'#71c9d6','#267a89',4)+rect(340,282,93,24,'#57d5d4','#1c8189',3)+rect(350,272,9,44,'#57d5d4','#1c8189',2)
b+=line(143,210,143,370,'#497ca8',2,True)+line(386,210,386,370,'#497ca8',2,True)+line(143,202,386,202,arrow=True)+t(264,192,'9 + sword_distance','9 + sword_distance',20,anchor='middle')
b+=t(143,400,'Player anchor','캐릭터 기준점',19,anchor='middle')+t(386,400,'Sword','검',19,anchor='middle')+t(80,470,'x_sword = x_player ± (9 + sword_distance)','x_sword = x_player ± (9 + sword_distance)',20,weight=700)
b+=node(615,145,190,78,'0','0','(14, 193)','(14, 193)')+node(860,145,190,78,'1','1','(364, 193)','(364, 193)')+node(860,300,190,78,'2','2','(469, 153)','(469, 153)')+node(615,300,190,78,'3','3','(279, 233)','(279, 233)')
b+=line(805,185,860,185,arrow=True)+line(955,223,955,300,arrow=True)+line(860,339,805,339,arrow=True)+line(710,300,710,223,arrow=True)
b+=t(830,420,'Cycle until the game starts','게임 시작까지 순환',20,anchor='middle',weight=700)+t(830,450,'Input-timing-dependent selection','입력 시점에 따른 선택',17,anchor='middle')
fig('escape-07-sword','Sword motion in a relative frame','상대좌표로 움직이는 검','The anchor follows the player; the spawn selector cycles through four positions','캐릭터를 기준으로 이동 · 네 초기 위치 순환',b,540)
# Darkness. 160x120 viewport scale 3.2. player at center.
b=rect(65,130,512,384,'#111824','#a6bacb',0)+rect(65+20*3.2,130+24*3.2,120*3.2,72*3.2,'url(#dots)','#60b1d3',0,2)+rect(65+45*3.2,130+40*3.2,70*3.2,40*3.2,'#273c54')
b+=rect(65+74*3.2,130+52*3.2,12*3.2,16*3.2,'#39dbe0')
b+=line(65+20*3.2,144,65+140*3.2,144,'#60b1d3',2)+t(321,165,'≈ 120 px','≈ 120 px',18,'#bde8ff',anchor='middle')
b+=line(565,130+24*3.2,565,130+96*3.2,'#60b1d3',2)+t(555,310,'72','72',16,'#bde8ff',anchor='end')
b+=node(630,155,410,90,'Outside bounds → black','경계 밖 → 검은색',"data = 3'b000","data = 3'b000") +node(630,265,410,90,'Transition region','중간 시야 영역','Stipple predicate not retained','점무늬 전체 조건은 미보존')+node(630,375,410,90,'God Mode','God Mode','Disable the darkness mask','어둠 마스크 해제','#e7f5ee')
fig('escape-08-darkness','Player-relative visibility','캐릭터 기준 시야','Known outer bounds; interior stipple is illustrative','외곽 경계는 RTL 기준 · 내부 점무늬는 예시',b,575)
# Append only localization entries for this generator. Preserve existing keys.
g=ROOT/'apps/web/i18n/svg-ko-overrides.json'
old=json.loads(g.read_text(encoding='utf8'))
for k,v in LO.items():
    if k not in old: old[k]=v
g.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
import runpy
runpy.run_path(str(Path(__file__).with_name('build-escape-vga-pixel-grids.py')), run_name='__main__')
print(f'Generated {len(list(DIR.glob("escape-*.svg")))} Escape figures; registered {len(LO)} analytical label mappings')
