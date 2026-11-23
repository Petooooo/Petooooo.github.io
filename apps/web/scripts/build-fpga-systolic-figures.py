#!/usr/bin/env python3
"""Illustrative systolic-array diagrams, verified against a worked matrix example.

This is not the original 2024 Verilog, RTL timing trace, or FPGA synthesis output.
The available 2024 project record supports a Verilog FPGA matrix multiplier and
IM2COL motivation, but not a particular PE count or clock schedule.
"""
from pathlib import Path
from html import escape
import json

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"apps/web/public/figures/journals"
OVERRIDE=ROOT/"apps/web/i18n/svg-ko-overrides.json"
OUT.mkdir(parents=True,exist_ok=True)
LABELS={}
A=((1,2),(3,4))
B=((5,6),(7,8))
TARGET=((19,22),(43,50))

def wave():
    acc=[[0,0],[0,0]]
    steps=[]
    records={}
    for tick in range(4):
        active={}
        for i in range(2):
            for j in range(2):
                k=tick-i-j
                if 0 <= k < 2:
                    product=A[i][k]*B[k][j]
                    acc[i][j]+=product
                    active[(i,j)]=(f"{A[i][k]} × {B[k][j]}",acc[i][j],k)
                    records[(i,j,k)]=tick
        steps.append((active,tuple(tuple(row) for row in acc)))
    assert steps[-1][1]==TARGET
    assert len(records)==8
    assert all(records[(i,j,k)]==i+j+k for i in range(2) for j in range(2) for k in range(2))
    return steps
STEPS=wave()

def txt(x,y,en,ko=None,size=22,color="#e9f2fb",weight=500,anchor="start"):
    if ko is None:ko=en
    if en not in LABELS:LABELS[en]=ko
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(str(en))}</text>'
def rect(x,y,w,h,fill="#193247",stroke="#46647d",r=12,sw=1.4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def arrow(x1,y1,x2,y2,color="#8acbc3",sw=3):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" marker-end="url(#arrow)"/>'
def route(d,color="#8acbc3",sw=3,dashed=False,head=False):
    dash=' stroke-dasharray="7 7"' if dashed else ''
    mark=' marker-end="url(#arrow)"' if head else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{dash}{mark}/>'
def box(x,y,w,h,en,ko=None,detail="",detail_ko=None,accent="#8ad4c0",size=21):
    s=rect(x,y,w,h)
    s+=rect(x+4,y+11,5,h-22,accent,accent,2,0)
    s+=txt(x+21,y+34,en,ko,size,"#f5f9ff",700)
    if detail:s+=txt(x+21,y+60,detail,detail_ko or detail,15,"#bed0df")
    return s
def panel(x,y,w,h):
    return rect(x,y,w,h,"#13283e","#47617a",16)
def figure(n,slug,title,ktitle,subtitle,ksubtitle,content,footer="Worked example, not recovered RTL timing",kfooter="동작 설명용 예제 · 과거 RTL Timing 기록이 아님",height=740):
    w=1260
    LABELS.setdefault(title,ktitle)
    head=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" viewBox="0 0 {w} {height}" role="img" aria-label="{escape(title)}"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0c1727"/><stop offset="1" stop-color="#152b43"/></linearGradient><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9z" fill="#8acbc3"/></marker></defs><rect width="{w}" height="{height}" rx="18" fill="url(#bg)"/>'
    head+=txt(49,61,f"0{n} / {title}",f"0{n} / {ktitle}",31,"#f4f8ff",740)
    head+=txt(51,101,subtitle,ksubtitle,18,"#a5c0d3")
    head+=route("M49 132H1210","#35536d",1.6)
    head+=content
    head+=route(f"M49 {height-63}H1210","#35536d",1.4)
    head+=txt(51,height-29,footer,kfooter,15,"#a5b9ca")
    p=OUT/f"fpga-systolic-{n:02d}-{slug}.svg"
    p.write_text(head+"</svg>\n",encoding="utf8")
    print("FIG",p.name,p.stat().st_size)

def matrix(x,y,name,kn,nums,accent="#8ad4c0",cell=62,gap=8):
    s=txt(x,y-20,name,kn,22,"#f4f8ff",700)
    for i,row in enumerate(nums):
        for j,n in enumerate(row):
            bx=x+j*(cell+gap);by=y+i*(cell+gap)
            s+=rect(bx,by,cell,cell,"#20384b",accent,6,1.5)
            s+=txt(bx+cell/2,by+cell*.65,str(n),str(n),29,"#f8fbff",700,"middle")
    return s

# 1: the two concrete matrices and their exactly verified product.
s=matrix(90,299,"A / 2×2","A / 2×2",A)
s+=matrix(449,299,"B / 2×2","B / 2×2",B,"#f3c57d")
s+=matrix(876,299,"C / 2×2","C / 2×2",TARGET,"#98a7ed")
s+=txt(342,379,"×","×",44,"#e9f2fb",700,"middle")
s+=txt(765,379,"=","=",45,"#e9f2fb",700,"middle")
s+=box(80,520,1090,86,"Each output C[i,j] is a dot product of A row i and B column j","각 C[i,j]는 A의 i번째 Row와 B의 j번째 Column의 내적","All four results are verified by the executable reference model","네 개의 결과는 계산용 Reference Model과 대조했다")
figure(1,"matmul-example","A 2×2 matrix product to trace","실제 숫자로 따라갈 2×2 행렬곱","A = [[1,2],[3,4]] · B = [[5,6],[7,8]]","A = [[1,2],[3,4]] · B = [[5,6],[7,8]]",s)

# 2: two-dimensional output-stationary array illustrative choice.
s=txt(55,187,"A streams →","A는 오른쪽으로 이동 →",23,"#8ad4c0",700)
s+=txt(548,187,"B streams ↓","B는 아래쪽으로 이동 ↓",23,"#f3c57d",700)
for i in range(2):
    y=283+i*225
    s+=box(70,y+44,200,93,f"A row {i}",f"A Row {i}","left-edge injector","왼쪽 입력")
    s+=arrow(270,y+89,372,y+89)
for j in range(2):
    x=410+j*315
    s+=box(x,210,248,70,f"B column {j}",f"B Column {j}",accent="#f3c57d")
    s+=arrow(x+120,280,x+120,318)
for i in range(2):
    for j in range(2):
        x=410+j*315;y=326+i*225
        s+=box(x,y,247,108,f"PE({i},{j})",f"PE({i},{j})",f"C[{i},{j}] accumulator",f"C[{i},{j}] Accumulator",size=22)
        if j==0:s+=arrow(x+247,y+53,x+306,y+53)
        if i==0:s+=arrow(x+120,y+108,x+120,y+202,color="#f3c57d")
s+=box(1040,348,179,147,"Local MAC","Local MAC","A×B + sum","A×B + Sum",accent="#98a7ed")
figure(2,"pe-grid","Local data movement in an array","PE 사이에서 움직이는 데이터","An illustrative output-stationary mapping, not a recovered 2024 floorplan","Output-Stationary 방식의 동작 예시 · 실제 FPGA 배치도는 아님",s)

# 3: PE registers, valid gated accumulation.
s+= ""
s=box(69,250,227,112,"A register","A Register","forward A →","A를 오른쪽으로 전달")
s+=box(69,438,227,112,"B register","B Register","forward B ↓","B를 아래로 전달",accent="#f3c57d")
s+=box(403,325,241,145,"Multiplier","Multiplier","a × b","a × b",accent="#98a7ed")
s+=box(756,325,211,145,"Accumulator","Accumulator","psum + product","psum + product",accent="#98a7ed")
s+=arrow(296,308,394,377)
s+=arrow(296,485,394,428,color="#f3c57d")
s+=arrow(644,398,744,398)
s+=box(1008,328,205,134,"C[i,j]","C[i,j]","valid after k=K−1","k=K−1 이후 Valid",accent="#a3e2bd")
s+=arrow(967,398,997,398)
s+=txt(69,609,"Reset / valid gating / overflow handling depend on actual RTL","Reset·Valid·Overflow 처리는 실제 RTL 구현을 확인해야 확정된다",19,"#e9d6a9")
figure(3,"pe-anatomy","What a PE has to keep and forward","PE가 저장하고 전달해야 할 값","Minimal MAC-based reference architecture","MAC 기반 Reference Architecture",s)

# 4: left/top injection streams, including deliberate skew.
incoming=[
("t = 0",("A[0,0]","—","B[0,0]","—")),
("t = 1",("A[0,1]","A[1,0]","B[1,0]","B[0,1]")),
("t = 2",("—","A[1,1]","—","B[1,1]")),
("t = 3",("—","—","—","—")),
]
s=panel(52,202,1154,387)
head=["logical t","A row 0","A row 1","B col 0","B col 1"]
kh=["논리적 t","A Row 0","A Row 1","B Col 0","B Col 1"]
xx=[75,282,510,735,975]
for c,label in enumerate(head):
    s+=txt(xx[c],249,label,kh[c],20,"#e9f3ff",720)
for i,(time,vals) in enumerate(incoming):
    y=289+i*67
    s+=rect(69,y,1123,60,"#1b344a" if i%2==0 else "#162c41","#315068",6)
    for c,val in enumerate([time,*vals]):
        s+=txt(xx[c],y+38,val,val,19,"#f6f8ff",630)
s+=txt(80,632,"The streams must be staggered so matching k values meet at each PE","같은 k의 Operand가 각 PE에서 만나도록 Input을 한 Cycle씩 어긋나게 넣는다",20,"#f0d49f")
figure(4,"skew-streams","Inject operands with a deliberate skew","Input을 어긋나게 주입한 이유","Entry-edge schedule for the illustrative 2×2 example","2×2 설명용 예제의 입력 경계 스케줄",s)

# 5: a full snapshots by logical step with accumulated sums.
for_print=[]
s=""
for tick,(active,acc) in enumerate(STEPS):
    x=51+tick*307
    s+=panel(x,184,286,423)
    s+=txt(x+22,227,f"t = {tick}",f"t = {tick}",25,"#f4f7ff",730)
    s+=txt(x+22,255,"Logical MAC step","논리적 MAC 단계",15,"#a9bbcc")
    for i in range(2):
        for j in range(2):
            bx=x+20+j*127;by=293+i*138
            match=active.get((i,j))
            fill="#214538" if match else "#172d40"
            stroke="#8ad4c0" if match else "#35516a"
            s+=rect(bx,by,119,125,fill,stroke,8)
            s+=txt(bx+11,by+24,f"PE{i}{j}",f"PE{i}{j}",17,"#dceef5",700)
            if match:
                term,psum,k=match
                s+=txt(bx+12,by+56,term,term,17,"#f1dfb2",700)
                s+=txt(bx+12,by+92,f"Σ {psum}",f"Σ {psum}",23,"#d5ffe6",720)
            else:
                s+=txt(bx+11,by+76,"idle","대기",20,"#7f96a8")
    for_print.append((tick,{str(k):v for k,v in active.items()}))
s+=txt(67,650,"An accumulator updates only when both operands are valid","두 Operand가 모두 Valid인 Cycle에만 Accumulator를 갱신한다",19,"#f0d49f")
figure(5,"wavefront-steps","Four logical steps, eight MAC operations","네 단계의 Wavefront, 여덟 번의 MAC","Derived from verified A and B matrices, not a captured hardware waveform","A와 B를 계산해 만든 예제이며 FPGA 실제 파형 캡처는 아니다",s)

# 6: schedule table and output validity for each PE.
s=panel(58,184,1141,435)
columns=[("PE","PE"),("t=0","t=0"),("t=1","t=1"),("t=2","t=2"),("t=3","t=3"),("Final C","최종 C")]
cx=[84,265,449,632,815,1002]
for j,(en,ko) in enumerate(columns):s+=txt(cx[j],244,en,ko,20,"#e5f3ff",700)
pe_rows=[(0,0,19,1),(0,1,22,2),(1,0,43,2),(1,1,50,3)]
for i,(row,col,value,last) in enumerate(pe_rows):
 y=276+i*77
 s+=rect(75,y,1100,69,"#172e44" if i%2==0 else "#1b3449","#324e62",5)
 s+=txt(90,y+43,f"PE{row}{col}",f"PE{row}{col}",21,"#dceaf6",700)
 for tick in range(4):
  k=tick-row-col
  label=("k0" if k==0 else "k1" if k==1 else "—")
  x=cx[tick+1]
  if 0<=k<2:
   s+=rect(x-6,y+10,129,49,"#244c3d","#73d9b8",5)
   s+=txt(x+18,y+43,label,label,20,"#d9ffe6",700)
  else:s+=txt(x+18,y+43,label,label,19,"#89a0b5")
 s+=txt(1011,y+43,f"{value} @ t{last}",f"{value} @ t{last}",19,"#f2d7a0",700)
s+=txt(75,659,"Output-ready times are logical example slots; RTL register latency may add cycles","Output Valid 시점은 예제의 논리적 Slot이며 실제 RTL은 추가 Pipeline Latency가 있을 수 있다",17,"#f2d7a0")
figure(6,"valid-timeline","When each result becomes complete","PE별 결과가 완성되는 시점","K=2: active k=0 and k=1 slots for each output accumulator","K=2에서 각 Accumulator가 k=0·k=1을 처리하는 단계",s)

# 7: counterexample when B column 1 is not delayed.
s=panel(50,202,555,364)+panel(655,202,555,364)
s+=txt(79,255,"Correct skew, t=1","정상 Skew, t=1",25,"#91dfbd",730)
s+=box(88,294,461,96,"PE(0,1) sees A[0,0] and B[0,1]","PE(0,1)에 A[0,0], B[0,1] 도착","1 × 6 = 6","1 × 6 = 6",accent="#91dfbd")
s+=txt(88,459,"Matching k=0 operands","같은 k=0 Operand를 처리",20,"#d8f9ea")
s+=txt(685,255,"Missing B skew, t=1","B Skew 누락, t=1",25,"#f4c18a",730)
s+=box(694,294,457,96,"A[0,0] meets the wrong B[1,1]","A[0,0]과 잘못된 B[1,1] 결합","1 × 8 = 8 (wrong)","1 × 8 = 8 (잘못된 값)",accent="#f0a978")
s+=txt(694,459,"Same PE, incorrect k pairing","같은 PE지만 k Index가 어긋남",20,"#f6d4a4")
s+=txt(86,628,"Illustrative failure, not a reconstructed bug from the 2024 project","입력 정렬 실패를 설명하기 위한 반례이며 2024년 당시 실제 장애 기록은 아니다",20,"#f5d39b")
figure(7,"skew-counterexample","One missing delay changes the math","Delay 하나가 빠지면 연산식이 달라진다","Deliberate skew error injected into the worked example","설명용 예제에 의도적으로 Skew 오류를 넣은 비교",s)

# 8: the im2col bridge to a 3x3 image and 2x2 filter.
X=((1,2,3),(4,5,6),(7,8,9))
K=((1,0),(0,-1))
patches=[]
for i in range(2):
    for j in range(2):
        patches.append([X[i][j],X[i][j+1],X[i+1][j],X[i+1][j+1]])
cols=tuple(tuple(patches[j][i] for j in range(4)) for i in range(4))
flat=(1,0,0,-1)
conv=tuple(sum(flat[k]*cols[k][j] for k in range(4)) for j in range(4))
assert conv==(-4,-4,-4,-4)
s=matrix(51,275,"Input image 3×3","입력 이미지 3×3",X,"#8ad4c0",51,5)
s+=matrix(329,304,"Kernel 2×2","Kernel 2×2",K,"#f3c57d",51,5)
s+=txt(587,391,"IM2COL","IM2COL",26,"#f4f9ff",730)
s+=arrow(543,387,655,387)
s+=matrix(678,278,"Patch matrix Xcol 4×4","Patch Matrix Xcol 4×4",cols,"#a3afe8",49,5)
s+=txt(965,362,"×","×",35,"#f4f8ff",700)
s+=box(1010,294,199,137,"Kernel row","Kernel Row","[1, 0, 0, −1]","[1, 0, 0, −1]",accent="#f3c57d")
s+=txt(69,586,"Result: four output positions, each −4","결과: 네 Output 위치가 모두 −4",23,"#dcf4e8",730)
s+=txt(69,632,"IM2COL is one mapping option; it is not proof of the original project's buffer layout","IM2COL은 하나의 매핑 방법이다. 이 예제가 원본 프로젝트의 Buffer 배치를 증명하지는 않는다",18,"#aebfcf")
figure(8,"im2col-example","Convolution can become matrix multiplication","Convolution을 행렬곱으로 옮기는 과정","A new 3×3-by-2×2 arithmetic example; not the 2024 CNN dataset","새로 계산한 3×3·2×2 예제이며 2024년 모델 데이터가 아니다",s)

# 9: separate historical support from newly verified explanation.
s=panel(50,204,360,389)+panel(453,204,358,389)+panel(854,204,355,389)
s+=txt(75,255,"2024 project record","2024년 프로젝트 기록",22,"#8ee0c9",730)
for i,(a,b) in enumerate([("Verilog / FPGA","Verilog / FPGA"),("Systolic matrix multiplier","Systolic 행렬곱 연산기"),("Convolution / IM2COL","Convolution / IM2COL")]):
 s+=txt(77,319+i*69,a,b,19,"#eff9ff",550)
s+=txt(476,255,"Verified here","현재 예제로 검증",22,"#9fbafa",730)
for i,(a,b) in enumerate([("2×2 matrix product","2×2 행렬곱"),("Operand pairing / skew","Operand Pairing / Skew"),("MAC wavefront / outputs","MAC Wavefront / 결과")]):
 s+=txt(480,319+i*69,a,b,18,"#eff9ff",550)
s+=txt(875,255,"Not recovered","원본 자료 미확보",22,"#f3c98a",730)
for i,(a,b) in enumerate([("Original RTL / testbench","원본 RTL·Testbench"),("Measured FPGA clock / LUTs","FPGA 클럭·LUT 실측치"),("GPU benchmark conditions","GPU Benchmark 조건")]):
 s+=txt(877,319+i*69,a,b,18,"#eff9ff",550)
s+=txt(68,633,"No source-backed throughput, area, or GPU speedup number is claimed for this project","이 프로젝트의 근거 없는 처리량·자원·GPU 대비 속도 수치를 새로 주장하지 않는다",19,"#f3d69d")
figure(9,"evidence-boundaries","The boundary of what this article can verify","이 글에서 검증 가능한 범위를 구분했다","Original record versus executable educational example versus missing raw artifacts","당시 기록·새 계산 예제·확인하지 못한 원본 자료를 구분한다",s,
       footer="The 2024 CV is not a preserved synthesis report",
       kfooter="2024년 이력서는 원본 합성 보고서가 아니다")

gloss=json.loads(OVERRIDE.read_text())
new=0
collisions={}
for en,ko in LABELS.items():
    if en not in gloss:gloss[en]=ko;new+=1
    elif gloss[en]!=ko:collisions[en]=(gloss[en],ko)
OVERRIDE.write_text(json.dumps(gloss,ensure_ascii=False,indent=2)+"\n")
print("PASSED Python reference model:",TARGET,"MAC events:",8,"logical slots:",4)
print("FIGURES",len(list(OUT.glob("fpga-systolic-[0-9][0-9]-*.svg"))),"new localized captions",new,"preexisting glossary collisions",collisions)
