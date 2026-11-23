#!/usr/bin/env python3
"""Recreate evidence-bearing VECTOR illustrations from the 2024 capstone poster.

Not a vectorization of original embedded poster screenshots. Figure captions must
identify analytical reconstruction and avoid claiming original screenshot pixels.
Measurements and labels are copied only where legible in the source poster.
"""
from __future__ import annotations
from pathlib import Path
import html,json,math

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"apps/web/public/figures/journals"
I18N=ROOT/"apps/web/i18n/svg-ko-overrides.json"
OUT.mkdir(parents=True,exist_ok=True)
labels={}
def esc(s):return html.escape(str(s),quote=True)
def t(x,y,en,ko=None,size=22,weight=500,color="#242e3b",anchor="start",rotate=None):
    labels.setdefault(en, ko or en)
    tr=f' transform="rotate({rotate} {x} {y})"' if rotate else ""
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{tr}>{esc(en)}</text>'
def rect(x,y,w,h,fill="#ffffff",stroke="#555c65",radius=9,stroke_width=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
def arrow(x1,y1,x2,y2,color="#42474c",sw=3,dash=False):
    d=' stroke-dasharray="7 6"' if dash else ''
    return f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="{sw}" fill="none" stroke-linecap="round"{d} marker-end="url(#arrow)"/>'
def path(d,color="#454b52",sw=2,dash=False,arrow_end=False):
    dashstr=' stroke-dasharray="7 6"' if dash else ''
    mark=' marker-end="url(#arrow)"' if arrow_end else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"{dashstr}{mark}/>'
def block(x,y,w,h,title,ko=None,fill="#e8f1f8",sub=None,subko=None,stroke="#414954"):
    s=rect(x,y,w,h,fill,stroke,9,2)
    s+=t(x+w/2,y+33,title,ko,19,700,anchor="middle")
    if sub:s+=t(x+w/2,y+56,sub,subko,15,400,anchor="middle")
    return s
def panel(x,y,w,h,title,ko=None,color="#f5f7f9"):
    return rect(x,y,w,h,color,"#777d84",15,2)+t(x+19,y+37,title,ko,24,700)
def circle(x,y,r,fill,stroke="#414954"):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def base(title,ko,subtitle,subko,body,number,slug,width=1240,height=760):
    s=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#42474c"/></marker></defs>'''
    s+=rect(0,0,width,height,"#fafafa","#9f4240",18,5)
    s+=rect(28,23,width-56,71,"#963b38","#963b38",12,1)
    s+=t(53,69,title,ko,31,750,"#fff")
    s+=t(43,132,subtitle,subko,17,450,"#60646b")
    s+=body
    s+=path(f'M43 {height-68} H{width-43}',"#a7a8aa",1)
    s+=t(46,height-38,"Poster-based vector reconstruction · not the original screenshot","포스터 원본을 바탕으로 새로 그린 벡터 도식 · 원본 캡처 아님",16,450,"#777")
    s+='</svg>\n'
    p=OUT/f'cnn-poster-{number:02d}-{slug}.svg';p.write_text(s,encoding="utf8")
    print(p.name,p.stat().st_size)
    return p
# 01. Poster Background 1) Custom Net — stage names/sizes.
s=""
stages=[
 ("Image","입력 이미지","28 × 28"),
 ("C1","C1","4 @ 25×25"),
 ("S1","S1","4 @ 12×12"),
 ("C2","C2","8 @ 9×9"),
 ("S2","S2","8 @ 4×4"),
 ("C3","C3","16 feature maps"),
 ("Output","출력","10 classes"),
]
for i,(name,ko,size) in enumerate(stages):
 x=48+i*169;w=137;y=269
 colors=["#fafafa","#d6d6d6","#bdbdbd","#d5d5d5","#c3c3c3","#d5d5d5","#fff7ea"]
 for z in range(4 if i in [1,3,5] else 1):
  off=(3-z)*6 if i in [1,3,5] else 0
  s+=rect(x+off,y+off,w-22 if i!=6 else w-40,165-off,"#f6f6f6" if i==0 else colors[i],"#252525",3)
 s+=t(x+69,231,name,ko,23,700,anchor="middle")
 s+=t(x+69,480,size,size,17,400,anchor="middle")
 if i<6:s+=arrow(x+140,354,x+160,354)
for x,name,ko in [(217,"Conv 4×4×4","Conv 4×4×4"),(386,"MaxPool 2×2","MaxPool 2×2"),(555,"Conv 4×4×8","Conv 4×4×8"),(724,"MaxPool 2×2","MaxPool 2×2"),(893,"Conv 4×4×16","Conv 4×4×16"),(1062,"FC / argmax","FC / argmax")]:
 s+=t(x,569,name,ko,16,500,anchor="middle")
s+=t(63,636,"Source: Custom Net diagram; numbers are feature-map labels from the poster","출처: 포스터의 Custom Net 구성 · 숫자는 포스터의 Feature Map 표기",19,500)
base("Custom CNN: stage-by-stage feature maps","Custom CNN의 Feature Map 변화","Poster section: Background / Convolution Neural Network (CNN) – Custom Net","원본: Background / Custom Net",s,1,"custom-net")

# 02. PS/PL poster full architecture and 16 bank labels.
s=block(63,173,337,74,"INT8 input / INT4 weight","INT8 입력 / INT4 가중치","#f5f5f5")
s+=block(451,173,342,74,"power-of-2 quantization","2의 거듭제곱 양자화","#f5f5f5")
s+=block(846,173,338,74,"FP32 input & weight","FP32 입력·가중치","#f5f5f5")
s+=arrow(451,210,406,210)+arrow(846,210,799,210)
s+=rect(49,291,262,367,"#fffbc8","#515257",5)
s+=t(73,327,"PS","PS",26,800)
for y,en,ko in [(363,"Im2col","Im2col"),(444,"ReLU","ReLU"),(525,"Max pooling","Max Pooling")]:
 s+=block(77,y,185,66,en,ko,"#dce7f4")
s+=rect(337,291,850,367,"#f9fff9","#b7d4bd",4)
s+=t(364,327,"PL","PL",26,800)
s+=arrow(311,421,340,421)
s+=t(296,398,"AXI4-Lite","AXI4-Lite",15,600,anchor="middle")
s+=panel(369,358,203,259,"16 input BRAMs","Input BRAM 16개","#fff")
s+=panel(588,358,203,259,"16 output BRAMs","Output BRAM 16개","#fff")
for j in range(8):
 for x in [389,606]:s+=rect(x,401+j*24,165,16,"#dce6f1","#687685",2,1)
s+=block(819,388,149,149,"BRAM","BRAM","#f6dedb","FSM + Control","FSM + Control")
s+=rect(982,354,181,252,"#e9edf5","#d12826",4,5)
for row in range(4):
 for col in range(4):
  xx=996+col*40;yy=389+row*46
  s+=rect(xx,yy,34,36,"#fff","#555",0,1)
  if row in [0,3] and col in [0,3]:s+=t(xx+17,yy+23,"PE","PE",12,700,anchor="middle")
s+=t(989,636,"IS 1×16 / WS 4×16","IS 1×16 / WS 4×16",17,700)
s+=arrow(791,466,809,466)+arrow(968,466,981,466)
base("Zynq PS–PL architecture from the poster","포스터의 Zynq PS–PL Architecture","Poster: 16 input banks + 16 output banks / FSM and Controller / two PE array modes","포스터: Input·Output BRAM 각 16개 / FSM·Controller / 두 PE 배열 모드",s,2,"ps-pl-architecture")

# 03. Poster Background 2) systolic buffer structure excerpt.
s+= ''
s=block(351,172,540,70,"Weight Buffer","Weight Buffer","#f3f1ea")
s+=rect(46,286,138,290,"#e7f0fb","#414954",9,2)
s+=t(116,432,"Activation Buffer","Activation Buffer",20,700,anchor="middle",rotate=-90)
s+=block(351,588,540,65,"Accumulation Buffer","Accumulation Buffer","#eef8e7")
for row in range(4):
 for col in range(6):
  x=301+col*119;y=280+row*72
  s+=rect(x,y,71,50,"#fff","#333",0,2)+t(x+35,y+30,f"PE {row+1},{col+1}",f"PE {row+1},{col+1}",14,600,anchor="middle")
  if col<5:s+=arrow(x+71,y+25,x+114,y+25)
  if row<3:s+=arrow(x+36,y+50,x+36,y+69)
 for x in [331,569,807]:
  s+=arrow(x,242,x,270)
for y in [304,376,448,520]:s+=arrow(184,y,284,y)
s+=arrow(625,561,625,585)
base("Systolic Array: buffers feed the PE grid","Systolic Array에 데이터를 공급하는 구조","Poster excerpt: Weight / Activation / Accumulation buffers around the processing grid","원본의 Weight·Activation·Accumulation Buffer 관계",s,3,"systolic-buffers")

# 04. WS and IS compared without claiming cycle-accurate schedule.
s=""
for idx,(x,title,ko,stationary,statko,stream,streamko,c) in enumerate([
 (59,"Weight Stationary (WS)","Weight Stationary (WS)","Pre-fill weights","Weight를 먼저 채움","Inputs streamed","Input이 이동","#d6eadb"),
 (655,"Input Stationary (IS)","Input Stationary (IS)","Pre-fill inputs","Input을 먼저 채움","Weights streamed","Weight가 이동","#d9e7f4"),
]):
 s+=panel(x,187,530,405,title,ko,"#fbfbfb")
 s+=t(x+25,251,stationary,statko,20,550)
 s+=block(x+45,271,431,73,stream,streamko,c)
 rows=4 if idx==0 else 1;cols=8
 for r in range(rows):
  for k in range(cols):
   bx=x+50+k*52;by=384+r*49
   s+=rect(bx,by,38,36,"#f2f2f2","#555",1,1)+t(bx+19,by+23,"PE","PE",11,600,anchor="middle")
 s+=t(x+264,582,"4×16 array in poster" if idx==0 else "1×16 array in poster","원본의 4×16 배열" if idx==0 else "원본의 1×16 배열",18,600,anchor="middle")
base("Two stationary dataflows, two reuse choices","WS와 IS는 재사용 대상이 다르다","Partial PE grids are drawn here; source labels describe full configurations","PE Grid는 일부만 그렸고 전체 배열 크기는 원본 표기를 따른다",s,4,"ws-is-dataflow")

# 05. IM2COL exact poster symbolic matrix dimensions.
s=panel(44,196,348,345,"Packed convolution kernels","Kernel Packing","#fff")
s+=panel(445,196,353,345,"Im2col input patches","Input Patch → Im2col","#fff")
s+=panel(853,196,343,345,"Output feature map","Output Feature Map","#fff")
for r in range(5):
 for c in range(9):
  x=74+c*30;y=266+r*38;s+=rect(x,y,26,31,["#e9edf2","#d5e8da","#f4dfc4","#dae6f7","#ddd"][r%5],"#666",1,1)
for r in range(8):
 for c in range(13):
  x=473+c*22;y=274+r*28;s+=rect(x,y,18,23,"#dfeddb" if c in (0,12) else "#f3f3f3","#777",0,0.5)
for r in range(5):
 for c in range(7):
  x=904+c*35;y=287+r*40;s+=rect(x,y,30,34,"#edf4ee","#777",0,1)
s+=t(214,569,"M × K","M × K",27,700,anchor="middle")+t(621,569,"K × N","K × N",27,700,anchor="middle")+t(1021,569,"M × N","M × N",27,700,anchor="middle")
s+=t(411,417,"×","×",36,700,anchor="middle")+t(817,417,"=","=",36,700,anchor="middle")
s+=t(66,644,"M = Cout   /   K = Ck × Ck × Cin   /   N = Hout × Wout","M = Cout   /   K = Ck × Ck × Cin   /   N = Hout × Wout",20,600)
base("IM2COL changes the shape of the computation","IM2COL은 연산의 데이터 형태를 바꾼다","Poster uses symbolic M, K and N dimensions; colored cells explain flattening","원본의 M·K·N 차원과 Patch 재배치를 기반으로 다시 그렸다",s,5,"im2col-mkn")

# 06. Single PE true poster layout.
s=panel(228,187,770,426,"Single processing element (PE)","Single PE 내부 구조","#fff")
s+=block(304,261,230,68,"Input","Input","#dce8f4")
s+=block(697,261,230,68,"Weight","Weight","#f5dfc5")
s+=circle(485,417,62,"#fff")
s+=t(485,430,"Shift","Shift",24,700,anchor="middle")
s+=circle(781,417,62,"#fff")
s+=t(781,430,"+","+",50,700,anchor="middle")
s+=arrow(421,329,458,356)+arrow(774,329,513,390)
s+=arrow(547,417,717,417)
s+=block(893,372,232,69,"Partial sum","Partial Sum","#edf2f6")
s+=arrow(893,405,840,414)
s+=arrow(781,479,781,565)
s+=block(665,560,232,68,"Output / PSum","Output / Partial Sum","#e5efd9")
s+=t(65,675,"Poster PE: input + weight → shift operation → accumulation","포스터의 PE: Input·Weight → Shift → Accumulation",18,550)
base("A PE does not remove accumulation","PE에는 Shift 외에 누산도 필요했다","Shift/sign handling and partial sum accumulation are separate datapath stages","Shift·부호 처리와 Partial Sum 누산은 다른 회로 단계다",s,6,"single-pe")

# 07. Exact poster 3x3 weight examples; left value and right shift/not strings.
weights=[["x−0.4","x−0.5","x9"],["x2.3","x−0.34","x−0.47"],["x−0.12","x−0.3","x0.79"]]
shift=[["<<1 neg()","<<1 neg()","<<3"],["<<1","<<2 neg()","<<1 neg()"],["<<3 neg()","<<2 neg()","<<0"]]
s=panel(58,200,508,408,"Original weights (poster)","원본 가중치 예시","#fff")
s+=panel(679,200,508,408,"Shift-form weights (poster)","Shift 형태로 변환한 가중치","#fff")
for mat,x0 in [(weights,94),(shift,714)]:
 for r,row in enumerate(mat):
  for c,value in enumerate(row):
   x=x0+c*151;y=304+r*88
   s+=rect(x,y,132,77,"#f5faff","#4d83bd",0,2)
   s+=t(x+66,y+45,value,value,16 if len(value)>6 else 19,600,anchor="middle")
s+=arrow(576,410,668,410)
s+=t(90,645,"Cells transcribed from the source illustration; encoding details depend on fixed-point scaling","원본 그림의 예시 값을 옮겼으며, 실제 Shift 의미는 Fixed-Point Scale을 고려해야 한다",16,450)
base("Weights constrained to shift-friendly values","가중치를 Shift 가능한 형태로 제한했다","Transcription of the poster's illustrative 3×3 example; not a bit-exact multiplier specification","포스터 3×3 예시를 옮긴 그림 · 비트 단위 연산 명세는 아니다",s,7,"weight-cells")

# 08. STE forward/backward with measured example weights and gradients.
s=""
s+=panel(51,216,527,342,"Forward pass","Forward Pass","#fff")
s+=block(92,300,190,94,"FP weights","FP 가중치","#dbe8f8","1.1, 2.2, −1.7, 3.6","1.1, 2.2, −1.7, 3.6")
s+=block(331,300,197,94,"Quantized Q","양자화한 Q","#e6f0da","1, 2, −2, 2","1, 2, −2, 2")
s+=arrow(282,349,319,349)
s+=t(98,454,"Non-differentiable quantizer","미분하기 어려운 Quantizer",18,450)
s+=panel(648,216,539,342,"Backward pass","Backward Pass","#fff")
s+=block(688,300,194,94,"STE gradient","STE Gradient","#f8dede","Surrogate derivative","대체 미분값")
s+=block(938,300,202,94,"Train weights","Weight 학습","#f8e5ce","Update FP variables","FP 변수 갱신")
s+=arrow(882,349,926,349)
s+=t(692,454,"The quantized forward path still permits weight updates","Forward 양자화를 거쳐도 Weight 학습을 이어간다",17,450)
s+=t(64,623,"Poster cites STE / INQ methods; these techniques were applied rather than invented","원본의 STE·INQ 방법을 학습·가속기 설계에 적용했으며 새로 발명한 것은 아니다",18,500)
base("STE kept quantized training possible","STE로 양자화한 모델의 학습을 이어갔다","Poster training figure: separated forward quantization and backward gradient handling","원본 Training 그림의 Forward 양자화와 Backward Gradient 경로를 구분했다",s,8,"ste-training")

# 09. INQ stages: source figure is 2x3 matrices, show increasing frozen power-of-two weights.
s=""
stages=[("FP weights","FP Weight","#d6dce2",[]),("Subset fixed","일부 Weight 고정","#dae8fa",[0,5,10]),("More fixed","고정 비율 증가","#c9e2fd",[0,2,5,7,10,12]),("Power-of-2 weights","Power-of-2 Weight","#c4d7fc",list(range(16)))]
for i,(name,ko,c,selected) in enumerate(stages):
 x=58+i*296
 s+=panel(x,214,260,357,name,ko,"#fff")
 for r in range(4):
  for col in range(4):
   k=r*4+col
   s+=rect(x+28+col*52,290+r*55,44,45,"#83b2e3" if k in selected else "#f5ecd0","#59738d",1,1)
   if k in selected:s+=t(x+50+col*52,319+r*55,"2^p","2^p",15,600,"#162f4e",anchor="middle")
 if i<3:s+=arrow(x+262,407,x+288,407)
s+=t(66,625,"INQ is a stagewise idea: the poster does not provide a full retraining log","INQ는 단계적으로 Weight를 제한하는 방법이며, 원본에는 전체 학습 로그가 없다",19,500)
base("INQ gradually fixes the weight representation","INQ로 가중치 표현을 단계적으로 제한했다","Stages illustrate progressive quantization; colored positions are explanatory, not recorded indices","단계별 위치와 색상은 원리를 설명하기 위한 것으로 실제 Weight Index 기록은 아니다",s,9,"inq-stages")

# 10. poster 2) Data Flow output paths, DP labels and output BRAM banks.
s=panel(48,183,521,439,"Convolution datapaths","Convolution Data Paths","#fff")
for i in range(8):
 col=i%4;row=i//4;x=85+col*107;y=257+row*101
 s+=block(x,y,85,70,f"DP{i+1}",f"DP{i+1}","#d5e8fa")
s+=panel(632,183,555,439,"16 output BRAM banks","Output BRAM 16개","#fff")
for i in range(16):
 col=i%2;row=i//2;x=664+col*236;y=239+row*43
 s+=rect(x,y,219,35,"#eaf1eb" if i<4 else "#edf1f9","#7d8792",3,1)
 s+=t(x+109,y+23,f"Output BRAM{i}",f"Output BRAM{i}",16,500,anchor="middle")
s+=arrow(570,402,620,402)
s+=t(79,651,"Poster maps DP outputs into BRAM 0–15; this figure omits cycle-level timing","포스터는 DP 출력을 BRAM 0–15로 연결한다. 여기에는 Cycle Timing 정보가 없다",18,500)
base("Dataflow into sixteen output BRAM banks","DP 출력을 16개 Output BRAM으로 연결했다","Poster's DP1–DP8 labels and output bank naming reconstructed as a readable layout","원본의 DP1–DP8 및 Output BRAM 레이블을 읽기 쉽게 재구성했다",s,10,"output-bram-dataflow")

# 11: Vivado resource tables, verified exact counts, numeric chart.
s=""
titles=[("Our Model (bit-shift)","우리 모델 (Bit-Shift)",60,(12603,8786,34),("#bfe2ea","#cbe8e9")),("Traditional (multiply)","기존 모델 (Multiply)",647,(19833,11114,34),("#d4dfeb","#c5d2de"))]
for en,ko,x,vals,col in titles:
 s+=panel(x,209,538,372,en,ko,"#fff")
 s+=t(x+30,282,"Resource","리소스",17,700)
 s+=t(x+229,282,"Used","사용량",17,700)
 s+=t(x+370,282,"Utilization","사용률",17,700)
 for row,(name,amount,available) in enumerate(zip(["LUT","FF","BRAM"],vals,[53200,106400,140])):
  y=309+row*75
  s+=rect(x+17,y,506,62,"#f3f5f6" if row%2==0 else "#fff","#d0d0d0",1,1)
  s+=t(x+33,y+36,name,name,20,700)
  s+=t(x+220,y+36,f"{amount:,}",f"{amount:,}",20,600)
  s+=t(x+378,y+36,f"{amount/available*100:.2f}%",f"{amount/available*100:.2f}%",19,600)
s+=rect(277,610,685,55,"#f9f0e9","#a13b39",9,2)
s+=t(617,646,"LUT reduction: 36.5% in the poster","LUT 사용량 약 36.5% 감소 (포스터 결과)",22,750,"#7a2929","middle")
base("The placement screenshots and resource tables","FPGA 배치 화면에서 확인한 Resource 차이","Values transcribed from the poster's Vivado utilization tables; not a placement trace","포스터의 Vivado Utilization 표에서 수치만 재현했다. 배치 스크린샷은 아니다",s,11,"fpga-resources")

# 12: Exact source nine category accuracy chart, use 95..100 axis.
s=""
models=[("DenseNet(1)",98.4,"#efa58d"),("MobileNet(2)",96.3,"#84b8da"),("MobileNet(1)",97.8,"#ce90a2"),("ResNet(3)",96.2,"#9acee7"),("ResNet(2)",95.2,"#c1d69e"),("ResNet(1)",96.7,"#bf97c9"),("LeNet",99.4,"#f5d68c"),("Traditional Model",97.3,"#eba08c"),("Our Model",96.7,"#ed8585")]
x0=405;width=689;floor=95
for j,v in enumerate([95,96,97,98,99,100]):
 x=x0+(v-floor)*width/5
 s+=path(f'M{x:.1f} 198 V650',"#dde1e6",1)
 s+=t(x,683,str(v),str(v),16,450,anchor="middle")
for i,(name,v,c) in enumerate(models):
 y=199+i*50
 s+=t(56,y+25,name,name,18,700 if i>=7 else 500)
 sw=max(0,(v-floor)*width/5)
 s+=rect(x0,y+2,sw,39,c,"#c0b6b6",0,1)
 s+=t(x0+sw+11,y+29,f"{v:.1f}%",f"{v:.1f}%",17,700)
 if i==8:s+=rect(38,y-5,1113,50,"none","#aa3b39",0,3)
s+=t(1040,711,"Top-1 accuracy (%)","Top-1 정확도 (%)",16,550,anchor="end")
base("Poster accuracy chart: all displayed models","포스터의 Top-1 Accuracy 그래프를 다시 그렸다","Read the 97.3% traditional vs 96.7% ours pair as the stated project comparison","직접 비교 기준은 Traditional 97.3%와 Our Model 96.7%이다",s,12,"top1-accuracy",height=790)

# 13: Poster runtime table: PS only vs PS+PL.
s=""
s+=panel(58,204,552,387,"CPU (PS only)","CPU (PS Only)","#fff")
s+=panel(633,204,550,387,"Our work (PS + PL)","Our Work (PS + PL)","#fff")
for x,v,col,en,ko in [(107,15.9,"#c6d9e8","15.9 ms","15.9 ms"),(682,8.83,"#c5e7d1","8.83 ms","8.83 ms")]:
 s+=rect(x,355,408*v/15.9,92,col,"#52616a",5)
 s+=t(x,502,en,ko,35,750)
s+=t(79,645,"Runtime average · dual-core ARM Cortex-A9 @ 667 MHz (poster)","평균 실행 시간 · Dual-Core ARM Cortex-A9 @ 667MHz (포스터)",18,550)
base("Runtime measures PS-only against PS+PL","실행 시간 비교는 PS 단독과 PS+PL이다","15.9 ms and 8.83 ms measure integrated execution, not only multiplier vs shift","15.9 ms와 8.83 ms는 전체 실행 구성 비교이며 연산기 단독 비교가 아니다",s,13,"runtime-table")

original=json.loads(I18N.read_text())
changed=0
for en,ko in labels.items():
 if en not in original:
  original[en]=ko;changed+=1
I18N.write_text(json.dumps(original,ensure_ascii=False,indent=2)+"\n")
print("Generated 13 source-grounded true vector SVGs; added/updated label translations:",changed)
