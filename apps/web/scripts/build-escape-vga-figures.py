#!/usr/bin/env python3
"""Escape From The Dark: report-derived vector diagrams (June 20, 2023).
Traces: original embedded bitmap xrefs 23, 28, 31, 33, 34, 37, 38, 39, 123, 125, 126, 127, resized preserving aspect,
quantized to 7 RGB colors, converted into merged rectangular pixel runs.
The report and raw images contain team project material and are not committed.
Diagrams use report values; schematic positions are not hardware measurements.
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
def trace(slug,w,h,data,title,ko):
    # Two base-36 digits per coordinate and extent; one palette entry per string.
    LO.setdefault(title,ko)
    cols=['#fff','#f00','#0ff','#ff0','#f0f','#0f0']
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}" shape-rendering="crispEdges">'+rect(0,0,w,h,'#000')
    for c,ds in zip(cols,data.split('|')):
        assert len(ds)%8==0,(slug,c,len(ds))
        d=[]
        for i in range(0,len(ds),8):
            x,y,ww,hh=[int(ds[i+j:i+j+2],36) for j in (0,2,4,6)]
            assert 0<=x<w and 0<=y<h and x+ww<=w and y+hh<=h,(slug,x,y,ww,hh)
            d.append(f'M{x} {y}h{ww}v{hh}h-{ww}z')
        if d:s+=f'<path fill="{c}" d="{" ".join(d)}"/>'
    p=DIR/(slug+'.svg');p.write_text(s+'</svg>\n',encoding='utf8');ET.parse(p)
trace('escape-01-map-trace',540,218,'1w0g0u022q0y0a027g0y0a02e60y0u02800y0a02940y0u026m0y0a02d10y0a028k0y0a02ar0y1e023u0y1y02301g0u023u1y0a023u200901bw2g09016c2g0t01bv2h0a016c2h0u014o2g0u03bw2i09016c2i0t018c2y1w01002y0r015s2y0u038b2z1y02002z0s024y3h0u021w3z32027h3z1e02by3z1e02124h0u026n4h0u02dc4h0a02aj4h1f02by4z0a02264z1y02004z1c02954z1g02dm4z0a025i4z1f0395511f01dn510901bz51090126511x0101511b01125h0u028b5h0u02bo5h0a02dw5h0a03135j0s018b5j0t01bp5j0901eo5l0401et5m0101eu5n0101eo5o0101el5o0101ev5o0101ek5p0101et5p0101ew5p0101en5p0101em5q0101eu5q0101es5u0101eo5u0101eq5n010cej5q0109ex5q0109ev5r0108el5r0108305z3202by5z0u03e65z0u03775z0u03005z2g0330613101|4s0p03014t0r02014x0r01014q0r01014v0s01024s0s01024p0t01024y0t01024t0u02014t0w02014r0x02014v0x0201c32601019y2p0401a22q01019x2q01019w2r0102a32r01029z2s0201a12t01029y2t0102a42t01039v2t01032g3s01012j3s01012n3s01012i3u01012o3u01022j3v01012f3u01032g3x01012j3x01012g3y03012k3y03019e4q03012d4q03012i4s01019c4s01012b4s01019j4s01019e4t01029h4u01012g4u01012d4u01012e4v02019f4v02012j4t01042a4t01049b4u01039k4u01032i4x01012b4x01019j4x01012e4x02019f4x02019c4x01012c4y02019d4y02012g4y02019h4y02014q5q03014r5t01014p5u01014n5u01034r5w01014p5y01014t5y0101|cy3q0101cz3s0a01cx3s0102d83t0101d73u0101cz3t0103d63v0101cz3w0701cx3v0103cz3x0101cy3y02019z4s0101084s0102aa4t01010j4t01019y4t0201a94u01010i4u0101064u01019x4u0101a14s01040a4s01049y4v0201074v0201a84v01010h4v01010a4w0701a14w06019z4w0102084w0102a14x01010a4x0101094y0101a04y01010b5l0102045m0101095n0101075n01010c5o0102035o0102045q02010a5q02010b5r01010d5r01017n5r0101045r01027o5s0101065s02017m5s01020e5s01020a5t01017o5t0a010b5u0101065u02017o5u01027o5w02017m5w01027o5x01010b5x0101065x01010e5x01010d5y0101045y02017n5y0101|et0m0401ey0n0102ex0p0101es0p0201et0q0201ew0q0101ew0s0101ew0u0101eu0r0105bz240401bx260101c2270201bx270201c1280101c2290101c22b0101bz280106c12d01010b2m05010a2o01010g2o01010f2p02010a2p02010b2q02010e2q01010e2r02010g2s01010e2t02010g2u01010c2r01050e2v01015v5n0401cc5n0401cg5o0102ca5p0101cd5p01015u5p0101605p0101cf5q02015z5q0201ca5q02015u5q02015v5r0101ce5r0101cb5r02015y5s0101cf5s0101cg5t0101cc5s01055w5s01055y5w0101ce5w0101cd5x0101|ax2802014d2802018a5903011r5902028b5a0101|cw3t0101a74w01015w5r01015z5s01010c5s0101045t01010c5y0101','Complete map palette trace','전체 맵 색상 트레이스')
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
trace('escape-09-gameplay-trace',160,104,'1z0y0201230y01011w0z01011t0z01011r0z01011n0z02011c0z0101210z01011k0z01012e1v07012n1v0d013g1v0701331v0b022m1w0g012d1w07013f1w0801351x0301391x03013e1x02012e1x05012l1x0i011w2c01011t2c01012a2c0101212c01011n2c0101|0d000b010m01060109010601070203010r0204010u03020105030201040402010w040101020502010x0502010h050201070502010k0502010a0502010y060101020601010q050603060607020g060702010701010z0701010r0804010h080501070805010z080201000802020i0903010s09020108090301090a0101000a010310090105000d02010z0e0101010e0101010f02010y0f02010x0g0201020g02010w0h0201030h02010v0i0201040i03010t0j0201060j02010q0k0301080k03010b0l0f011m0o0a011j0p04011w0p03011z0q02011h0q0301210r02011g0r0201220s02011f0s0101230t02011e0t0101240u02011d0u0101250v01011c0v01021b0x0106260w01081c13010225140101241502011d150101231602011e160101221702011e170201211802011g1802011h1902011z1902011j1a03011w1a03011m1b0a012b1f0801291g02012i1g03012k1h0201281h0101271i01012l1i02012m1j0101351j0701261j01023c1k0201331k02012n1k0102321l01013e1l0101311m01013f1m0102371n0301301n0201351p0101381p01012o1m0106371r0101251l0108341r0102381s0101301o01063g1o01062n1s0102261t01022m1u02013f1u0101301u0201381u0101271v01013e1v02012l1v0201311v02012k1w02013e1w0101281w0101321w01013c1x0201291x0201331x02012j1x0201341y08012b1y0801381z01012e1z01011v2005011u2102012021020121220101222301031t220105212602011u270101212701011z2802011v2802011x290201|2c1i05012h1j01012f1k01012i1l01022b1n01012h1n01012k1p01012c1q02012i1q02012h1r01012c1r01012f1s0101|070c0101060d0301070e0101070f0201070g0102|301v01011w230403|080h01012a1j01012d1k01012g1n01012a1n01032h1q0101','Gameplay result palette trace','플레이 결과 화면 색상 트레이스')
trace('escape-10-sword-gameplay-trace',160,110,'1n2001011h2001013m2h01013e2h01013g2h0101162h0a023e2i05013k2i01011y2z0b011g2z0c011g300u011g310t013p3102013v310101|0d030604030306040f070201050702012g2k08011r2k08012e2l02012o2l02011z2l01011q2l0101202m01011p2m01012d2m01012q2m01012r2n01011o2n0102212n01022c2n01021n2p0106222p01062s2p01062b2p01062c2v01012r2v01021o2v0102212v01022c2w02012p2x0201202x01011p2x01012d2x02011q2y02011y2y02012f2y01012o2y01012h2z07011s2z0601|262k05012c2m0101252m0101282n01012a2n01012d2o01012f2o0101242n01032g2p01012d2p0201252q02012e2q01012g2q0a012c2q01012g2r01012c2r03012c2s0201272s01012f2s0201252r01032d2t04012g2u06012c2u0301262u0201252w0101272x0101242x0101252y02012d2y0101|1t2n04011s2o01021y2p01011v2p01011s2q02011x2q01011t2r02011w2r01021w2u01011u2s01051w2w0101||','Sword gameplay result palette trace','검 장착 결과 화면 색상 트레이스')
# Source screen and sprite traces: compact zlib-encoded five-byte rectangles.
import base64,zlib
SOURCE_PANELS={row[0]: row[1:] for row in [[23,160,107,"eNoVlOtPGmkUxnNmXhkYFRARBmyMCt4Vb6ttpeCqqIBua9OmVUDZukl3I90vVtrSrrRNumm13Rj3fvln93e+PDnX51zmvCP9fkdk2u8XKfsDIl6gU2Qy4IqsBLAVA90iLX/SkrjbJTKusOISV3RDIteuJTLWSUixMywy2hW05Hana0uxq8eSWGe3kdtB+IrBiEg1EPSJE+h2JB6CZSQYsqQYgupBiA5qIVjiYdSRMBkPwz4RJ+y3xOuhjZEeHLdCXbbU1NZyLb9ch8SWRITcWxFyH/Z0WOJEui1J9mK72RsUKYX9Rh72GujV0R+FdCTit+VOFL5SlJDRPuhvRo0lpT5YbvT5LBmLYVuOdYjk+xwcMRpyolB5cfYyHqf75TikuTgsNXUkPKQJT+M8CiUSEEwmCF72wpbU1OYk8SaSkE4n8S4lIVhN0mkp7hipJSH1hmCZG6LJ2DCtZYbJyA0TvDtMXCzFiqdTOHZS2GJpVjyVhj6XCthSTgdQR3voeZS6JYXYaIS6w2x8aByCyTHU4QnoJycgGJpEWppgwNh4wMjglG58gmHi09SYnHRsWZ7y2dJKW65c91kJcWaYI64wNcOaljJk5MdYYHyWjOlZ1K9mKVSYZY5WRo9mjiuZnsO7OYd3cB7vzDxjbc0zvjOr1eb5oEML7CWzQFp+tsPI9gJ3dVclZ5GMuMLwos1yFvWjLJJ7V9XNFTKeKVysoG5kKVTLMtuJSht3WNiJwkWWKQs5VXNs6FNOm8wjVe9wrOdZxv+YJy2eDfhkJsudVlc7LTnJR2xpr7JiXzbsSGaNAymsYmuuQdBeY7Z76yqtU81dZ46Mwt4Go1bWONaTNb7Mi3UO01tj1FTW70qlAEujQLVmgWHaG6wzUwDuF4g72ISqodDe5CL2tqCqbxHc3iJtb5uMgy2OtbFFRnubOG+T+y6s84rvFullv0jIt9vM2ygqS5EmUyUIMlt0UCixg/0S+6uX2FqjhLettkxZZyujnpVh+Vgmwy04fvFKPJdUGb7MDg0VFPbLrKRRZtTmDv211ftph4yXu8Kydy2x3wc7xH7Hw7bfhv1AT8CyX/XaSL2oL6LA+yghl1FsZ7w8+6LPiP085hP7Dc/P/sTzs0/jqvLo7I8qnXrY3nhh4hLUeJ1Aep3kN9DqD4j96gY1Xg4ALwZRm0OkNXlC9lkK5p9S5D5Lo7bTqI0RpGc8EvvHMe1qxPjsd1O2Zf42tpi/uDzzp69DzB+OA7AC86/C7wFs//HSzG8ujqtO4B8uxfzS5RfzpRv4HCT3WuFziIzLsLHMryHbNp8j6lD40hsgg5+RcffhCx5AcHwgYloKlwqhCuBVcAyqNKowW4FvV6X7Ck9U/UFDzlRtq+oeWLYJVrFFqqhelWoDKqUVMlXilqqUzFXEMmuq7mnII1WfaNr3Gneq8KrCNs415J06PmjchdrcGlKyhm2ghjetMF+1LHNbbV8rlBUeqKNShflUpat96TCDh0gjh3jzh7DsqPpYpac14hoKZ2qL18Q2Q0dIYwoZhYVDvPkjWts5guCehjxW9Vilp2o7UWhqcEtt55rxXqVLBfeQ5URqYoxXJ21AIa2QqbOSJXWsHBJX3Be/2a3rcuq0dlzXvah0qsEtVc8144NmXKp6dUSh1Tqwr5B/gu2xQu4YeAT4mlER38/9SM9TSG+ngO/Yru9Eoa0QZE2+JuP79hjB9w0d/A/okthd"],[126,160,104,"eNoVU1lPG1cY1fmuZzz2jMd4wSvQGBxKgg0JRYoKeB3bxBizeIuxWdO0qJFaFR5ClapILZFapPSlUvN7e+7L0fmW8213BvNBA9gNWsCvGpQdBCK2ArK2DbyyGW3aLvCDHQI+aOZzAkDGodl0ZujT4AtRNuP4BOlQGFi1AwrNUIRRDYZLRdj1ASmXyUaYVVJhBlpuRHCnwZxx2MNxDfgj7JuciQpaGq4jbHSnmT/KHquuZeA46gf+1LAY9Qt6MROY2oEArqOW4EGb/bhBbdwRfNLMilk+JKN+A0txU6EQ8/vQSzDvQUMqSVjUUEjyBr0kl37QkE7Rl0uxUVFDK2r5caTZnWZ/aJZOc5limrJXjuniOsFGd2lu+U+a+37RkMlwo7UM79JKhzlVRm+kzUCSA2WzPM56lr5WljeYxi0L15rdaficMQX/afg8x4G+zPkgK1t+yPK2DdnagsjyjgP5Zkcg32r4uhSHlEqAPC8HINtlRVahYrZK7bMqWaQWoq9mQD7UqLivMTlSZ5VndfqqNRa90WbMY4HnHmXvPab85LHyJ48Ko0FwGibkXYOBHxtp+pps9H1Tm80s5C/NnKZf5Lo1Byk0YEjNgymFNrWPbY5R3GNKtS0ixQ59lQ4LrO2TlffZ8nHPUrLepa/U5VSPXa04IGxr+PuAzVcO2cg+DkJyx1T8riHY4+DBPhfM9lk+12P5+54S+VebgYELyQxYNDfQyUOaC0Mq7gfMc0cMxEbMmx0lWG/EaOLNLOS3NxH6ximycZTsZAHy8YTX2Jgw+eOEKYlJVmQw1eaUgeQpR7s55ZD3p5wldcYL1U5NkekZfb+ccYXMeRJSP+cYk3OLPg0LFyyweMGU+gVnmVzwAW60uXzJQOGCLzO5ZN7NJU8yd0Vf/ooHm14x5eaKpZ6+pe/2LbW33zFw+w6iKiUF1eIXoTbLfqhKOQK1UQlCVSuzUC+rLlk1DfWiFoaq1TJQ63Wm1OtzUGteFMrzFgiNJ1D5pkXWzEHNt5jstfJQsV1qvd0GVPj1PBWNmKG8100ot02Zu/cV67UjokIdFnjRoSy0zwIv9x3K2i2fcrsMbHQ5kNfVsgPKNvm+yjvQRQ8TZIceVPFINz96CvWzZoXjHaj3xyGo1V6X0F+BGvY50GiwRHOQF1UYLYkaDvNKrY3ZcjhmYPOE4w5PFrnghC1HE+474pOp8amCuc5/wazzazfX2oT1DmGVX4RZHAP/AyCwj/o="],[127,160,104,"eNoVVFlTYlcQrj4HZLnsKqBkRFRQEb0qiOw7soMoCCg6GRdwwjCTpUqTpyRWnhLnP+frl6967/769L3kN2iJFKOBaMUoiTaNRqKwUU+UNcLRYmlo1BE9snfG6otxgejNqCH6l1WTgly3guANxQQvqyYTqrhNCPGZrKinGAS1GB4UraAX9r6xZDYj2GVG3LrZhkaKXtIDq/8pOklmiwUOi51oZEGjewscL2aboLbZIGlkNSPOsiDIYjUJ8lodgjo2F5HVjvJeOzJ2GcJmvZZsDjQKOsBjphj09G7TSjq3L0t6X0TR86Ulou9LIGhbxAReh05De4sLkiIsdZcXiV6tVh2tO8E8yBBxonLXiaJjlv50orLPhR3suiCdMPzlQty7C0V9bvA4cfNOlQULXbh0gsYMf7t5ayvYWnQFa7pYQcaY4W2Fd+AGN7tTp6XNVTQ6XQXfy1Vk3DLMFvV6enVqtfTPKiGYbXYPcv0eSAkPul16UOWWYebBQK8svXswUOMDoL6GuKoXlSvrmODMhyGLGw6iwuYyUX4Lm8z6PUSZwBpRenudKLXjA/1d5H5h2A2iQDmI5j2GMcOMbTt76PYTw3YIT/EcUogC++iRCa0Jmu6Dx9YB+FYP0Lx3gEknrGYOsJK+CgqpQ0GUO0SpPsP4EJX9h2ZBySNQyDPUVDxUn6WbI8wyZW/iGC0Lx07cC0uBMLzxMHqUwqA1ZOlrGOVjEUw1YChHrIJOoxhtEMWQ5SiO61tEq6FABIuNxZAxYPga47Q4QgYMgTheZpDgp2CYxzF4LKERlEngqEsxh4YGSTS/Y/iSBMFAkkNSyC2lMFqHYcBqLI0xSmnEXabBY8DqLIUvJZDWo14GtlGGq2RQJZ6Fms9C7bOkZgkhWSEon4N6lcPWrlm9Y0ciJ+HNY3X5PDtY+pyDN1ng7Ra4Wx7qM0tqXkhKFtFjUARVtQTbsARu0yJopUvgOyyjr1qGOjyDN3MGqsMKSk3K+JjUCtRsFSGDKrxPVVTJ1bhHDSGBrM5Eag1VcnX+3uqY5aoOx2MNe5mzd7vBT8vQaCC330DuN1YDTQTvNBEcYqnQxFS9JhxzVn9m+I3B30LGXgtxagM/j0ILVS7Z9tDAqfzK0h9N8PU2QXWrjQLBNjNvg3SRodNGxn0bzz1vIe4XDvmdQ8odXKfawaNUz+H91MGvUO0CfrxQBH3s4XzUngLbANJd3wxpiBu/HVoEqSOLpPE1zszbsThJHVsNdDO2GWjOqvfJiwN+wrf1w2QD0mQT0hR/wjlAho61JD8fa0gGwzqSz7hduReBNI3ohdw7AUyiBthODUI+MYTiUB8ZQgkjyQeG/STgnmEfBycbKdS7TyHkALcmq2nYPrGkZgCVjBlqBt7DLKCcxRgfsyaoOXhLOQdUlo7y8N7lkXtbABwVjEIW80tSHpfYVoQaLiNuzBA+g+2GIVKBWiwta+R1BUUjVdiuGYrVJSFHNUgnNUXIUh3ebh30hyxFG3CUcRayi4uQlSaGHDYQF22ahKy24L1qwXbaRnAD7yb7baixDqDHEDsHjy5DvLsDuNgWMtHzk0z0t4RMDjZJpoY+kunROuDaK2Rm/EGR2amHFiYnRP8DEpLEGg=="],[28,100,31,"eNod0l1v2jAAheE5DiYJFcsHLG0ZorCqg6JqV2UsYp0yxMfNBEOhAlWUTdr//w07b28enWMnlp3YvPv4z9q9C4yt1yNjezCDClaBMbYWeJ5NA+PZLnwKNTZirKCW1GXoGbtj7Pw2Fqn+jTTRCI21zUgTA7ijPkHZ0Owz6Rh61tqGyKADY5jCGrbwB/wmG3pvjY2hC0MoYAE7OEEa6+F2rL2M4IE6IRWkJWlD2pHCRG+0EtUc+tQpqSRtEz1yJJ1jHfA1Va3Fnm8vMqU447VUB+zGxre31CF8SXTAR5hRf/DwivoLqlRLHeDMbL1V056hB/ct39ivUFI3cISwrVVuYA5VW+++kMIPSmlb6/VJQ1IBc2o9Fxe51muRBrkOc0+a5nr3ibqg7uBArV1qonGpGkOb2ifdwZg6gRm1hBVsGXsmvZDyK6Ue3MIQHqCADVRwAv9K2w0hhUeYw+9rLXUg1TraWtbROfqkEWkCC+qWdBSucsa4pS6wa+qKugG86na6vS6miyKl79DRlXJjmML6rSY8rD/tQv1pV8LnjPX039yopTSBQN/efYOfkOnTuRFEOr67gSXsYa0DuvxaFHAS/wG8rzTM"],[31,56,34,"eNoVzEEOwjAMRFH8iatgGizRiMqUDTtOgLj/ybA3T56xNHJ6/VTk/RXGcgHrwKMIE8HXJnSj4UOFuHJm3PIxi+EZZzHu1RW+NVCncxR9zynfs4u6LHJvRkZ7KmzHIvpZVf89vwSx"],[33,30,29,"eNoVjEsSgCAMQ00j6NTxAzggLrz/MQ2bTF6aFNP7ketuoJ8AlxNGv5IwKetDQqKxZ11ZhE+RC7cyz5hZ77Gom7ZVDW/CtRuiH0CM+hdbGa7CfrqLA1c="],[34,45,28,"eNoVj1FvgzAQg+cYbimFFpKQMtYJEKr6tP//9+p7Ofli3ycHX+t/4C8v4Np04NIicDeAL1c1BvBpILfvEFguDZg7uekqo3Z6e0c0DH3S2rfg2RMMg9w0RLC5K1xvyq2utrsANkrlm6B11MXfqPBrECVOouyTIjFN4JGEytkBWerIypUi91m0nkVGmZ08e+fqnV3lh9Ti43jo4u1qXvzCR/kR4NSwlYBt+qq1KmRJhWybpPbka3a3uhLAygJ8AFPWC0M="],[37,30,32,"eNoVjFEOQEAQQ3VMlrEYu4RF4v7H1Pl5eU3Tovs+kboDambQZaYNWXqtgWFV6BYw76HTRrhD1Attj5kftHoK7Yq20XIRU7/ZLg8kjROQVj6n2YnSIr7AD/KJA+c="],[38,60,29,"eNodj9tSwzAMBUeylDZpgCZpLoRMeWPclssUM/z/p6HlZWdlS8eyejLRQ0qi78DMRRuwJFM9gxvlHZv8MWnyB9N534peMa/raK6bCMB2TSW6gg+wO8TsCj5B3Yro1qroF0h9lOVZxNKxUlvBHVhvYk/HWO4Fe8O+exfzQcW6ISY2LGMF81P0dacUF1jGCuZjWDfSDAqlT6RMpIyqlrHCmc+kzKRgGSv/ZwsBoABfYqxj8Q3L2E+g2sePqldwidWqYQycwRX8gku89gc6Pg9i"]]}
def panel(xref,x,y,scale):
    w,h,encoded=SOURCE_PANELS[xref]
    buf=zlib.decompress(base64.b64decode(encoded))
    assert len(buf)%5==0
    colors=['#000','#fff','#f00','#0ff','#ff0','#f0f','#0f0']
    out=f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges">'+rect(0,0,w,h,'#000')
    paths=[[] for _ in colors]
    for i in range(0,len(buf),5):
        c,xx,yy,ww,hh=buf[i:i+5]
        assert 0<c<len(colors) and xx+ww<=w and yy+hh<=h
        paths[c].append(f'M{xx} {yy}h{ww}v{hh}h-{ww}z')
    for c,d in enumerate(paths):
        if d:out+=f'<path fill="{colors[c]}" d="{" ".join(d)}"/>'
    return out+'</g>'
b=''
for x,xref,en,ko,dim in [(50,23,'START','시작','752 × 504'),(400,126,'FAILURE','실패','416 × 271'),(750,127,'SUCCESS','성공','418 × 272')]:
    b+=t(x+160,143,en,ko,20,anchor='middle',weight=700)+panel(xref,x,160,2)+t(x+160,400,dim,size=16,anchor='middle')
b+=t(560,438,'Source image sizes in pixels · reduced palette traces','원본 이미지 크기(px) · 축소 색상 트레이스',18,anchor='middle')
fig('escape-11-screen-states','Start, failure and success screens','시작·실패·성공 화면','Report page 44 · palette-quantized vector traces','보고서 44쪽 · 색상 양자화 벡터 트레이스',b,490)
# Original sprite illustrations grouped in source order, pp. 2–4.
b=''
for x,y,xref,scale,en,ko in [(65,155,28,5,'Player directions and poses','캐릭터 방향과 자세'),(660,155,31,4,'Warder and projectile','적과 포탄'),(65,400,33,4,'Sword','검'),(250,400,34,4,'Equipped sword','검 장착'),(500,400,37,4,'Key','열쇠'),(705,400,38,5,'HUD','HUD')]:
    w,h,_=SOURCE_PANELS[xref]
    b+=t(x,y-12,en,ko,19,weight=700)+panel(xref,x,y,scale)
fig('escape-12-sprite-traces','Original sprite and HUD designs','원본 스프라이트와 HUD','Report pages 2–4 · reduced palette traces of six source illustrations','보고서 2–4쪽 · 원본 그림 여섯 장의 색상 트레이스',b,610)
# Append only localization entries for this generator. Preserve existing keys.
g=ROOT/'apps/web/i18n/svg-ko-overrides.json'
old=json.loads(g.read_text(encoding='utf8'))
for k,v in LO.items():
    if k not in old: old[k]=v
g.write_text(json.dumps(dict(sorted(old.items())),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'Generated {len(list(DIR.glob("escape-*.svg")))} Escape figures; registered {len(LO)} label mappings')
