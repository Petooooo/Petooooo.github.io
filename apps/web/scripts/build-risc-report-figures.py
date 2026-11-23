#!/usr/bin/env python3
"""Source-grounded diagram set for the 2024 13-page RISC TOY design report.

The original report is NOT included in the repository. These are native-vector
reconstructions and mechanism diagrams. No original screenshot or actual RTL
simulation trace is represented as regenerated. Reference: RISC CPU 설계.pdf.
"""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"apps/web/public/figures/journals"
CAT=ROOT/"apps/web/i18n/svg-ko-overrides.json"
OUT.mkdir(parents=True,exist_ok=True)
L={}
def t(x,y,en,ko=None,size=21,weight=500,color="#203346",anchor="start"):
    ko=ko if ko is not None else en
    L.setdefault(en,ko)
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}">{html.escape(str(en))}</text>'
def rect(x,y,w,h,fill="#fff",stroke="#2a526c",r=8,sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def path(d,color="#0c6184",sw=2.6,dash=False,head=False):
    return f'<path d="{d}" stroke="{color}" stroke-width="{sw}" fill="none" stroke-linejoin="round" stroke-linecap="round"'+(' stroke-dasharray="7 7"' if dash else '')+(' marker-end="url(#arrow)"' if head else '')+'/>'
def arrow(x1,y1,x2,y2,color="#0c6184",sw=2.6):
    return path(f'M{x1} {y1}L{x2} {y2}',color,sw,head=True)
def panel(x,y,w,h,subtitle,ko=None):
    return rect(x,y,w,h,"#f8fbfd","#c4d0d9",12,1.5)+t(x+18,y+31,subtitle,ko,22,750)
def block(x,y,w,h,title,ko=None,subtitle=None,subko=None,fill="#f4f9fc",accent="#1f7396",font=22):
    s=rect(x,y,w,h,fill,accent,9,2)
    s+=t(x+w/2,y+35,title,ko,font,740,anchor="middle")
    if subtitle:s+=t(x+w/2,y+61,subtitle,subko or subtitle,16,510,"#527085","middle")
    return s
def labelnum(x,y,en,ko=None):
    return t(x,y,en,ko,17,650,"#155b83")
def svg(n,slug,title,kotitle,kicker,koko,body,foot="Vector redraw of the source report · not a hardware trace",kofoot="원본 보고서를 바탕으로 그린 SVG · 실측 파형 아님",h=750):
    w=1280
    L.setdefault(title,kotitle)
    result=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse"><path d="M1 1L9 4L1 7z" fill="#0c6184"/></marker></defs>'
    result+=rect(0,0,w,h,"#fff","#bed0da",18,2)
    result+=rect(0,0,w,113,"#f5f9fc","#f5f9fc",18,1)
    result+=rect(36,35,6,47,"#0e6384","#0e6384",2,1)
    result+=t(58,61,title,kotitle,32,760)
    result+=t(59,93,kicker,koko,17,510,"#587184")
    result+=path("M40 124H1240","#cfdae3",1.3)
    result+=body
    result+=path(f"M40 {h-56}H1240","#c4d4df",1)
    result+=t(47,h-24,foot,kofoot,15,480,"#6d8593")
    result+="</svg>\n"
    p=OUT/f"risc-report-{n:02d}-{slug}.svg"
    p.write_text(result)
    ET.parse(p)
    print(p.name,len(result))
    return p

# FIG 1 — first original source architecture page. Match its major boxes and relative placement.
b=t(80,188,"Instruction Fetch","Instruction Fetch",23,750,"#12617d")
b+=t(708,188,"Instruction Decode","Instruction Decode",23,750,"#12617d")
b+=block(73,335,164,293,"IF Pipe-reg","IF Pipe-reg",fill="#ffffff")
b+=block(332,355,210,251,"Instruction memory","Instruction Memory",fill="#ffffff",font=20)
b+=block(599,325,153,303,"ID Pipe-reg","ID Pipe-reg",fill="#ffffff")
b+=block(824,392,150,111,"Register file","Register File",fill="#ffffff",font=20)
b+=block(1086,327,143,302,"EX Pipe-reg","EX Pipe-reg",fill="#ffffff")
b+=block(70,232,124,58,"PC mux","PC Mux",fill="#eaf4f8")
b+=block(298,254,128,56,"PC+4","PC+4",fill="#eaf4f8")
b+=arrow(130,290,155,323)
b+=arrow(237,463,321,463)
b+=arrow(542,477,589,477)
b+=arrow(752,437,812,437)
b+=arrow(974,438,1075,438)
b+=arrow(974,475,1075,475)
b+=path("M426 282H478V363H589","#0b6088",2)
b+=arrow(752,340,1075,340)
for y in [519,549,577,606]:
 b+=arrow(752,y,1075,y)
b+=t(774,333,"Next_PC 32-bit","Next_PC 32-bit",15,500)
b+=t(780,404,"rb_addr / rc_addr 5-bit","rb_addr / rc_addr 5-bit",16,520)
b+=t(980,424,"VAL_B / VAL_C","VAL_B / VAL_C",15,520)
b+=t(766,513,"Offset17 / Offset22","Offset17 / Offset22",15,500)
b+=t(771,547,"dest 5-bit / op 5-bit","dest 5-bit / op 5-bit",15,500)
b+=t(771,580,"i / shamt 5-bit / cond 3-bit","i / shamt 5-bit / cond 3-bit",14,500)
b+=path("M1082 641H564V638H427V609","#0b6088",2,head=True)
b+=t(583,667,"IWDATA / Write Back 32-bit","IWDATA / Write Back 32-bit",17,660,"#0b6088")
svg(1,"if-id-original","Original architecture · IF and ID","원본 전체 구조 · IF와 ID","Report page 1 · retains the source signal names and block order","보고서 1쪽 · 원본의 신호명과 주요 블록 배치를 유지",b,
 "Architecture redrawn from page 1; simplified buses and offsets","1쪽 원본 블록도를 참고했으며 Bus 일부는 단순화")

# FIG 2 — second panel source.
b=t(76,173,"Execution","Execution",24,750,"#12617d")
b+=t(753,173,"Memory Access","Memory Access",24,750,"#12617d")
b+=f'<path d="M112 324 L266 360 L266 494 L112 535Z" fill="#ffffff" stroke="#225371" stroke-width="2.5"/>'
b+=t(185,439,"ALU","ALU",31,730,anchor="middle")
b+=block(391,319,184,300,"MEM Pipe-reg","MEM Pipe-reg",fill="#fff")
b+=block(705,366,236,232,"Data memory","Data Memory",fill="#fff")
b+=block(1059,317,151,304,"WB Pipe-reg","WB Pipe-reg",fill="#fff")
for y in [390,463,486]:
 b+=arrow(49,y,102,y)
b+=t(61,370,"Input_A / B","Input_A / B",17,600)
b+=arrow(266,419,383,419)
for y in [479,509,539]:b+=arrow(266,y,383,y)
b+=arrow(575,414,697,414)
b+=arrow(575,487,697,487)
b+=arrow(941,414,1048,414)
b+=arrow(941,518,1048,518)
b+=arrow(575,368,1048,368)
b+=path("M486 318V251H97","#0b6088",2.4,head=True)
b+=t(251,239,"target 32-bit","target 32-bit",17,590)
b+=t(296,400,"ALU_OUT 32-bit","ALU_OUT 32-bit",16,570)
b+=t(286,475,"DRW / DREQ / WEN","DRW / DREQ / WEN",15,550)
b+=t(593,476,"MOUT 32-bit","MOUT 32-bit",16,590)
b+=path("M1134 621V660H706","#0b6088",2,head=True)
b+=t(787,683,"IWDATA / Write Back 32-bit","IWDATA / Write Back 32-bit",17,600,"#0b6088")
svg(2,"ex-mem-original","Original architecture · EX, MEM and WB","원본 전체 구조 · EX·MEM·WB","Report page 2 · ALU, Data Memory, target and writeback paths","보고서 2쪽 · ALU·Data Memory·Target·Writeback 경로",b,
 "Source-panel structural redraw; not a timing-accurate circuit netlist","원본 구조 재구성 · 실제 Gate-Level Netlist가 아님")

# FIG 3 — bit field encoding faithfully from original code.
fields=[("Opcode","Opcode","31:27",5,"#d0e7f1"),("Destination","Destination","26:22",5,"#e0eff6"),("rb","rb","21:17",5,"#cce5ef"),("rc","rc","16:12",5,"#dcebf3"),("Other fields","다른 필드","11:0",12,"#eef3f5")]
b=panel(48,199,1184,379,"32-bit instruction · field boundaries","32-bit Instruction · Field Boundary")
x=87;y=292
for name,ko,bits,width,color in fields:
 w=width*29
 b+=rect(x,y,w,118,color,"#1d5c80",0,2)
 b+=t(x+w/2,y+42,name,ko,19 if width>=5 else 15,700,"#1d3b52","middle")
 b+=t(x+w/2,y+84,bits,bits,21,570,"#285b7c","middle")
 x+=w
b+=t(87,474,"offset_17 = INST[16:0] / offset_22 = INST[21:0]","offset_17 = INST[16:0] / offset_22 = INST[21:0]",18,620)
b+=t(87,523,"i = INST[5] · shamt = INST[4:0] · cond = INST[2:0]","i = INST[5] · shamt = INST[4:0] · cond = INST[2:0]",18,620)
b+=t(83,622,"Store-specific rc address is a separate decode decision, not an encoding rewrite","Store에서 rc 주소를 선택하는 조건은 별도의 Decode 로직이다",19,520)
svg(3,"instruction-fields","Encoding fields carried between stages","Pipeline에 함께 전달한 Instruction Field","Report pages 1, 4–5 · actual bit slices from the EX register code","보고서 1·4–5쪽 · EX Register 코드에서 확인한 비트 범위",b)

# FIG 4 — IF conditional PC selection & hold.
b=panel(52,193,1152,434,"Instruction Fetch has separate address and instruction state","IF에는 PC와 Instruction 상태가 따로 있다")
b+=block(87,300,213,105,"PC state","PC State","start / RSTN","start / RSTN")
b+=block(390,273,226,100,"Hold or PC+4","Hold / PC+4","stall_MEM / stall_ID","stall_MEM / stall_ID",accent="#c17b36")
b+=block(390,425,226,98,"Branch target","Branch Target","BRANCH = 1","BRANCH = 1",accent="#27759a")
b+=block(718,319,211,113,"INSTR → INST_M","INSTR → INST_M","fetch buffer","Fetch Buffer")
b+=block(1012,319,171,113,"ID INST","ID INST","posedge CLK","posedge CLK")
b+=arrow(300,351,380,324)+arrow(300,361,380,469)
b+=arrow(616,329,708,362)+arrow(616,479,706,391)
b+=arrow(929,373,999,373)
b+=t(85,582,"A held PC does not automatically mean INST_M and INST are held on the same edge","PC 유지와 INST_M·INST 유지 조건은 각각 확인해야 한다",18,560)
svg(4,"fetch-stall-path","Why PC hold alone was not enough","PC만 멈추면 충분하지 않았던 이유","Report pages 2–3 · conditional PC, INST_M buffer and ID capture","보고서 2–3쪽 · PC 조건 분기·INST_M Buffer·ID Capture",b)

# FIG 5 — store-dependent second source address field selection.
b=panel(60,192,1149,410,"rc_ADDR_M depends on STORE","STORE에 따라 rc_ADDR_M Source가 바뀐다")
b+=block(89,284,267,102,"Normal decode","일반 Decode","INST[16:12] → rc","INST[16:12] → rc")
b+=block(88,453,268,105,"ST / STR decode","ST / STR Decode","INST[26:22] → rc","INST[26:22] → rc",accent="#b8712d")
b+=block(451,344,291,158,"Source-address mux","Source Address Mux","select = STORE","select = STORE")
b+=block(866,370,297,120,"Register File","Register File","rb_ADDR_M / rc_ADDR_M","rb_ADDR_M / rc_ADDR_M")
b+=arrow(356,328,442,400)+arrow(356,506,442,443)
b+=arrow(742,432,855,432)
b+=t(77,636,"The store data register participates in later data forwarding and load→store hazards","Store Data Register도 Forwarding과 Load→Store Hazard 검사에 포함된다",19,550)
svg(5,"store-register-select","Store instructions select a different source","Store는 Source Register 선택이 달랐다","Report page 4 · actual STORE-dependent rc_ADDR_M logic","보고서 4쪽 · STORE에 따라 달라지는 실제 rc_ADDR_M 로직",b)

# FIG 6 — three data hazard cases.
b=panel(56,187,1158,433,"Original report: three dependency classes","원본 보고서: Data Hazard 세 가지")
rows=[
("Case 1 · MEM ALU bypass","Case 1 · MEM ALU Forwarding","ALU_OUT_MEM → valB / valC","ALU_OUT_MEM → valB / valC","#d7ebf6"),
("Case 2 · WB ALU bypass","Case 2 · WB ALU Forwarding","ALU_OUT_WB → valB / valC","ALU_OUT_WB → valB / valC","#deeff3"),
("Case 3 · load then forward","Case 3 · Load 이후 Forwarding","stall_MEM (1 slot) → MOUT","stall_MEM (1 Cycle) → MOUT","#f9e9d9")]
for i,(en,ko,d,dk,fill) in enumerate(rows):
 y=260+i*119
 b+=rect(91,y,1058,98,fill,"#8daeba",10)
 b+=t(111,y+37,en,ko,23,750)
 b+=t(113,y+69,d,dk,18,610,"#3c6580")
b+=t(68,654,"All three cases were documented; the exact priority logic deserves separate inspection","세 가지 Case는 원본에 기록돼 있으며 선택 우선순위는 별도로 검토해야 한다",18,510)
svg(6,"forwarding-cases","Three forwarding paths from the report","원본 보고서의 세 가지 Forwarding 경로","Report pages 8–9 · MEM ALU, WB ALU and load result","보고서 8–9쪽 · MEM ALU·WB ALU·Load 결과",b)

# FIG 7 — true operand mux priority and historical guard condition.
b=panel(55,191,1152,451,"valB / valC selection order in the original expression","원본 valB·valC 선택식의 우선순위")
choices=[
("1. MEM ALU","1. MEM ALU","dest_MEM == src and !WEN_MEM and !DREQ_MEM","dest_MEM == src and !WEN_MEM and !DREQ_MEM","#d6edf6"),
("2. WB ALU","2. WB ALU","dest_WB == src and !WEN_WB and !DREQ_MEM","dest_WB == src and !WEN_WB and !DREQ_MEM","#e8edf9"),
("3. MEM load","3. MEM Load","dest_MEM == src and !DRW_MEM and DREQ_MEM","dest_MEM == src and !DRW_MEM and DREQ_MEM","#f4e5d4"),
("4. Register value","4. Register Value","fallback: valB_EX / valC_EX","기본값: valB_EX / valC_EX","#ecf3f6")]
for i,(en,ko,detail,kdetail,fill) in enumerate(choices):
 x=76+i*293
 b+=rect(x,274,267,239,fill,"#9bb9c9",10)
 b+=t(x+16,316,en,ko,20,730)
 if i<3:
  fragments=detail.split(" and ")
  for part_idx,fragment in enumerate(fragments):
   b+=t(x+13,365+30*part_idx,fragment,fragment,14,570,"#324f65")
 else:
  b+=t(x+13,378,detail,kdetail,14,520,"#324f65")
 if i<3:b+=arrow(x+267,392,x+289,392)
b+=t(76,558,"Preserved quirk: the WB check reads !DREQ_MEM, not the WB request signal","원본 WB 조건은 WB의 DREQ가 아닌 !DREQ_MEM을 검사한다",19,650,"#9c4d31")
b+=t(77,601,"This is a regression target, not a proven hardware defect","추가 회귀 테스트 대상이지 실제 오류로 입증된 사실은 아니다",18,530)
svg(7,"forwarding-priority","The bypass priority is part of correctness","Forwarding 선택 우선순위도 설계의 일부였다","Report page 9 · historical condition order, including an unmodified guard","보고서 9쪽 · 원본 선택 순서와 그대로 남긴 Guard 조건",b)

# FIG 8 — MEM stall, one-cycle hold and memory result.
b=panel(61,205,1149,377,"Load-use dependence","Load-use Dependency")
b+=block(84,297,229,139,"Load in MEM","MEM의 Load","DREQ_MEM = 1","DREQ_MEM = 1")
b+=block(427,298,290,140,"stall_MEM = 1","stall_MEM = 1","hold IF / ID / EX / MEM","IF·ID·EX·MEM 상태 유지",accent="#b77c32")
b+=block(858,298,277,139,"Forward MOUT","MOUT Forwarding","resume consumer","Consumer 다시 진행",accent="#287c75")
b+=arrow(313,365,412,365)+arrow(717,365,845,365)
b+=t(83,532,"Store-data dependency also triggers the load-use check","Store Data의 Load 의존성도 Hazard 검사에 포함된다",20,580)
svg(8,"load-use-stall","A load is not an ALU result","Load 결과는 ALU 결과보다 늦게 준비된다","Report pages 9–10 · one-cycle stall_MEM and MOUT forwarding","보고서 9–10쪽 · stall_MEM 1 Cycle과 MOUT Forwarding",b)

# FIG 9 — branch/jump opcodes, 1→2→0.
b=panel(56,194,1160,425,"Control transfer detected from INST_M[31:27]","INST_M[31:27]에서 Control Transfer 조기 감지")
ops=[("BR 15","BR 15"),("BRL 16","BRL 16"),("J 17","J 17"),("JL 18","JL 18")]
for i,(a,k) in enumerate(ops):
 x=81+i*288;b+=block(x,278,256,87,a,k,fill="#e9f4f8")
for i,(a,k,c) in enumerate([("stall_ID = 1","stall_ID = 1","#f7eadc"),("stall_ID = 2","stall_ID = 2","#f3dfca"),("stall_ID = 0","stall_ID = 0","#e9f4ec")]):
 x=168+i*385
 b+=rect(x,424,280,86,c,"#7899aa",10)
 b+=t(x+140,475,a,k,24,750,anchor="middle")
 if i<2:b+=arrow(x+280,468,x+369,468)
b+=t(87,568,"Two explicit stall states ≠ three-cycle report description to the target","Stall 상태 2개와 Target에 도착하는 3 Cycle 설명은 의미가 다르다",18,610)
svg(9,"branch-stall-states","Branch decode and two stall states","Branch·Jump 인식과 두 Stall 상태","Report pages 10–11 · BR/BRL/J/JL, state transition 1 → 2 → 0","보고서 10–11쪽 · BR·BRL·J·JL, 상태 전이 1 → 2 → 0",b)

# FIG 10 — synchronous register file / MA path.
b=panel(57,183,1164,438,"The WB boundary depends on the Register File clock","WB 타이밍은 Register File의 Clock 동작에 좌우된다")
b+=block(94,312,291,148,"MEM outputs","MEM Output","ALU_OUT_MEM / MOUT_M","ALU_OUT_MEM / MOUT_M")
b+=block(479,298,286,175,"MA signals","MA Signals","dest_MA / WEN_MA / op_MA","dest_MA / WEN_MA / op_MA",accent="#1977a0")
b+=block(879,314,258,147,"Register File","Register File","synchronous write","Synchronous Write",accent="#8a66af")
b+=arrow(385,384,465,384)+arrow(765,384,865,384)
b+=t(93,523,"ALU_OUT_MA <= ALU_OUT_MEM","ALU_OUT_MA <= ALU_OUT_MEM",18,630)
b+=t(93,554,"MOUT_MA <= MOUT_M","MOUT_MA <= MOUT_M",18,630)
b+=t(93,591,"Documented to avoid the extra WB pipe register delaying visible writes","WB Pipe Register로 인해 Write가 늦어지는 문제를 피하려고 구성한 경로",18,520)
svg(10,"writeback-ma-timing","Why the MA writeback signals existed","Writeback에 별도 MA 신호를 둔 이유","Report page 8 · synchronous register-file timing and the MA interface","보고서 8쪽 · Synchronous Register File과 MA Interface",b)

# FIG 11 — rotate right bit width.
b=panel(52,193,1149,424,"Source ROR code duplicates valB before a right shift","원본 ROR은 valB를 두 번 이어 붙여 Shift한다")
b+=block(82,301,230,117,"valB 32-bit","valB 32-bit",fill="#edf6fa")
b+=block(392,300,292,119,"{valB, valB}","{valB, valB}","64-bit concatenation","64-bit Concatenation")
b+=block(779,299,189,120,">> shamt",">> shamt","or valC[4:0]","또는 valC[4:0]")
b+=block(1039,302,137,112,"[31:0]","[31:0]","ROR output","ROR Output")
b+=arrow(312,360,380,360)+arrow(684,360,766,360)+arrow(968,360,1027,360)
b+=t(88,529,"The operation wraps shifted-out bits by selecting the lower 32 bits afterward","아래 32비트를 선택해 밀려난 비트를 반대쪽에 다시 나타낸다",19,590)
svg(11,"rotate-right-datapath","Rotate-right was not just an arithmetic shift","ROR은 단순 Right Shift가 아니었다","Report pages 5–6 · concatenation and variable shift selection","보고서 5–6쪽 · Concatenation과 Shift Amount 선택",b)

# FIG 12 — original directed test cases from pages 11-12.
b=panel(51,186,1160,458,"Selected original directed-test checkpoints","원본 Directed Test에서 확인한 주요 Checkpoint")
tests=[
("MOVI R1,1 → ADDI R0,R1,32","MOVI R1,1 → ADDI R0,R1,32","R0 = 33","R0 = 33"),
("ADD R6,R7,R8 (7 + 8)","ADD R6,R7,R8 (7 + 8)","R6 = 15","R6 = 15"),
("LD R21 → ADDI R22,R21,57","LD R21 → ADDI R22,R21,57","R21 = -308, R22 = -251","R21 = -308, R22 = -251"),
("LD R0 → ST R0 → LD R1","LD R0 → ST R0 → LD R1","R0 = 154, R1 = 154","R0 = 154, R1 = 154"),
("BR / BRL / J / JL","BR / BRL / J / JL","PC returns to 0 in the redirect scenario","분기 시나리오에서 PC = 0")]
for i,(en,ko,result,kresult) in enumerate(tests):
 y=250+i*72
 b+=rect(72,y,1119,64,"#f0f6fa" if i%2==0 else "#fafcfd","#bdced8",4,1)
 b+=t(85,y+39,en,ko,18,610)
 b+=t(693,y+39,result,kresult,18,660,"#1a6585")
b+=t(73,628,"These are reported test-plan expectations, not rerun simulator measurements","원본 테스트 계획의 기대 결과이며 이번에 다시 돌린 시뮬레이션 수치는 아니다",18,530)
svg(12,"testbench-checkpoints","Original instruction-test checkpoints","원본 Instruction Test의 주요 결과","Report pages 11–12 · expected register results and branch scenario","보고서 11–12쪽 · 기대 Register 값과 Branch 시나리오",b)

# FIG 13 — describe screenshot evidence without imitating the actual bit traces.
b=panel(51,192,1168,446,"Two source waveforms exist, but they are not vector-traced here","원본 보고서에는 두 파형이 있지만 실제 Bit Trace로 다시 그리지 않았다")
b+=block(80,280,517,148,"No taken branch","Branch 미실행","register/PC progression in the report","원본의 Register·PC 진행 확인",accent="#237d68")
b+=block(674,280,517,148,"Redirect to PC 0","PC 0으로 분기","register/PC progression in the report","원본의 Register·PC 변경 확인",accent="#27809c")
b+=t(91,505,"Source p12 / p13 have green-on-black wave screenshots","원본 12·13쪽에 녹색 Signal 파형 화면이 남아 있다",20,640)
b+=t(91,552,"Transition times and signal values were not re-extracted as exact coordinates","각 Transition의 실제 시점과 수치가 확인되지 않아 좌표를 새로 만들지 않았다",18,550)
svg(13,"waveform-evidence","What the original waveforms can establish","원본 시뮬레이션 파형으로 확인할 수 있는 범위","Report pages 12–13 · original screenshots are retained only in the source PDF","보고서 12–13쪽 · 실제 캡처는 원본 PDF에만 보존",b)

old=json.loads(CAT.read_text())
new=0
for en,ko in L.items():
    if en not in old:old[en]=ko;new+=1
CAT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+"\n")
print("13 SVG figures;",new,"new translations. Existing translations left unchanged.")
