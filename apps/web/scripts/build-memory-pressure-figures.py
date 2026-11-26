#!/usr/bin/env python3
"""Source-grounded memory diagrams and non-invasive synthetic checks.
No measurements or signals are taken from the host.
"""
from pathlib import Path
import html
import json
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
D = R / "public/figures/journals"
L = {}
INK, MUTED, BLUE, GREEN, AMBER, RED = "#273e51", "#60758a", "#e3edf5", "#e1eee5", "#f6ead0", "#f6dfda"

def text(x, y, en, ko=None, size=20, weight=500, anchor="start", color=INK):
    L.setdefault(en, ko if ko is not None else en)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(en)}</text>'

def rect(x,y,w,h,fill=BLUE,stroke="#a4b7c6",rx=7):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'

def path(d, arrow=True, dashed=False, color="#8199aa"):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="6 5"' if dashed else '')+'/>'

def node(x,y,w,h,e,k,sub=None,ks=None,fill=BLUE):
    b=rect(x,y,w,h,fill)
    b+=text(x+w/2,y+(29 if sub else h/2+7),e,k,21,700,"middle")
    if sub:b+=text(x+w/2,y+54,sub,ks,16,500,"middle",MUTED)
    return b

def figure(name,title,ko,sub,ks,body,h,footer=("Conceptual illustration · not a historical measurement","설명용 개념도 · 당시 실측값 아님")):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(title)}"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#8199aa"/></marker></defs>'
    s+=rect(1,1,1118,h-2,"#fff","#d1dce5",9)+text(40,47,title,ko,28,750)+text(40,78,sub,ks,17,500,color=MUTED)+body+text(40,h-17,*footer,14,color=MUTED)+'</svg>\n'
    p=D/name;p.write_text(s);ET.parse(p)

# 01: distinct mappings, shared physical page and backing relationships.
b=text(40,126,"Virtual mappings","가상 주소 매핑",22,700)+text(420,126,"Resident physical pages","상주 물리 페이지",22,700)+text(805,126,"Reclaim possibilities","회수 가능 경로",22,700)
b+=node(40,150,280,76,"Process A","프로세스 A","Private anonymous mapping","개인 익명 매핑")+node(40,257,280,76,"Process A","프로세스 A","Mapped file","파일 매핑")+node(40,364,280,76,"Process B","프로세스 B","Same mapped file","동일 파일 매핑")
b+=node(420,150,300,76,"Anonymous page","익명 페이지","Private data","개인 데이터",AMBER)+node(420,310,300,76,"Shared cache page","공유 캐시 페이지","File-backed mapping","파일 기반 매핑",GREEN)
b+=path("M320 188H420")+path("M320 295H369V333H420")+path("M320 402H369V363H420")
b+=node(805,150,275,76,"Swap backing","Swap 저장 공간","If available and eligible","사용 가능하고 회수 가능할 때",AMBER)+node(805,310,275,76,"Backing file","원본 파일","Clean: discard / refault","Clean: 폐기 후 재읽기",GREEN)
b+=path("M720 188H805",dashed=True)+path("M720 348H805",dashed=True)
b+=rect(40,473,1040,57,"#f3f6f9","#d3dee7")+text(60,507,"Dirty file pages may need writeback; pinned pages may not be reclaimable.","Dirty 파일 페이지는 Writeback이 필요할 수 있고 고정 페이지는 회수하지 못할 수 있다.",19,600)
figure("memory-01-page-ownership.svg","Mappings, physical pages and backing storage","주소 매핑, 물리 페이지와 저장 공간","Multiple virtual mappings may refer to one resident page","여러 가상 매핑이 같은 물리 페이지를 참조할 수 있다",b,575)

# 02: reclaim-capable allocation, zone watermark and return path.
b=node(405,115,310,74,"Allocation request","페이지 할당 요청","Allowed zone / order / flags","허용 Zone / Order / Flags")
b+=node(405,224,310,74,"Check free-page reserves","여유 페이지 검사","Zone watermarks","Zone별 Watermark")
b+=path("M560 189V224")
b+=node(40,346,310,76,"Background reclaim","백그라운드 회수","kswapd aims to restore reserve","kswapd가 여유 확보",GREEN)
b+=node(405,346,310,76,"Direct reclaim","직접 회수","Allocating task may stall","할당 태스크가 지연될 수 있음",AMBER)
b+=node(770,346,310,76,"Allocation succeeds","할당 성공","Enough suitable pages","적합한 여유 페이지 확보",GREEN)
b+=path("M465 298V321H195V346")+path("M560 298V346")+path("M655 298V321H925V346")
b+=text(195,314,"Low watermark","Low Watermark",16,600,"middle")+text(586,337,"Pressure","압박",15,600)+text(925,314,"Sufficient","충분",16,600,"middle")
b+=node(40,482,310,76,"Free / evict pages","페이지 확보 / 축출","Cache, writeback, swap","캐시, Writeback, Swap")
b+=node(405,482,310,76,"Retry / evaluate","재시도 및 판단","Reclaim or compaction result","회수 또는 Compaction 결과")
b+=node(770,482,310,76,"Fail or scoped OOM","실패 또는 범위별 OOM","Depends on allocation context","할당 조건에 따라 다름",RED)
b+=path("M195 422V482")+path("M560 422V482")+path("M350 520H405")+path("M715 520H770")+path("M655 482V451H925V422")
b+=text(743,474,"No progress","진전 없음",15,600,"middle")+text(812,444,"Recovered","회수 성공",16,600,"middle")
figure("memory-02-reclaim-path.svg","Page allocation and reclaim latency","페이지 할당과 회수 지연","Simplified reclaim-capable path; allocation flags can change the outcome","회수를 허용하는 경로의 개념도 · 할당 조건에 따라 달라짐",b,607)

# 03: synthetic examples, not incident traces; calculations verified.
samples=[(90,0,0,1,0),(90,80,65,45,24)]
assert samples[0][0]==samples[1][0] and samples[0][1:3]!=(samples[1][1:3])
assert all(0<=full<=some<=100 for _,_,_,some,full in samples)
b=text(40,130,"Illustrative sample","가상 관측값",21,700)+text(409,130,"Cold pages in swap","Swap에 남은 Cold Page",21,700,"middle")+text(880,130,"Active churn","잦은 페이지 입출력",21,700,"middle")
rows=[("Swap used (%)","Swap 점유율 (%)",0,100,"%"),("Swap-in (MiB/s)","Swap-in (MiB/s)",1,100,""),("Swap-out (MiB/s)","Swap-out (MiB/s)",2,100,""),("Memory PSI some (%)","Memory PSI some (%)",3,100,"%"),("Memory PSI full (%)","Memory PSI full (%)",4,100,"%")]
for i,(e,k,j,scale,suffix) in enumerate(rows):
    y=151+i*65
    b+=rect(40,y,1040,57,"#f5f8fa","#e2e9ee",4)+text(56,y+34,e,k,18,600)
    for x,v in [(310,samples[0][j]),(785,samples[1][j])]:
        b+=rect(x,y+17,225,22,"#e2e9ee","#e2e9ee",3)
        if v:b+=rect(x,y+17,225*v/scale,22,"#8daec7" if j==0 else ("#8eb69e" if x==310 else "#cfaa72"),"#ffffff",3)
        b+=text(x+240,y+34,str(v)+suffix,size=18,weight=650)
b+=text(40,505,"The same swap occupancy can accompany very different memory pressure.","같은 Swap 점유율에서도 메모리 압박의 정도는 크게 다를 수 있다.",21,700)
figure("memory-03-pressure-signals.svg","Swap occupancy is not swap activity","Swap 점유율과 입출력은 다른 지표","Synthetic examples: independent quantities, not a recorded time series","가상 비교값 · 실제 장애 시계열 아님",b,554)

# 04: service startup and stop are independent, path vs argv.
b=node(40,122,310,78,"Base unit","기본 Unit","ExecStart / ExecStop","ExecStart / ExecStop")
b+=node(405,122,310,78,"Drop-in + environment","Drop-in과 환경 설정","Merge and expand arguments","설정 병합 및 인자 확장")
b+=node(770,122,310,78,"Effective commands","최종 실행 명령","Start and stop separately","Start와 Stop은 별개")
b+=path("M350 161H405")+path("M715 161H770")
b+=node(40,270,310,78,"Start executable","Start 실행 파일","Lookup / execve","경로 확인 / execve")
b+=node(405,270,310,78,"Argument parsing","인자 해석","earlyoom v1.9.0")
b+=node(770,270,310,78,"Polling loop","감시 루프","Only after valid arguments","유효한 인자를 받은 뒤",GREEN)
b+=path("M925 200V230H195V270")+path("M350 309H405")+path("M715 309H770")
b+=node(40,423,310,83,"Stop executable","Stop 실행 파일","Separate stop operation","별도 종료 명령")
b+=node(405,423,310,83,"Exit status 16","종료 코드 16","Invalid swap threshold","Swap 임계값 인자 오류",RED)
b+=node(770,423,310,83,"Missing executable","실행 파일 없음","Observed stop error","관측된 Stop 오류",RED)
b+=path("M560 348V423",dashed=True)+path("M1080 161H1100V383H195V423",dashed=True)+path("M350 464H393V548H925V506",dashed=True)
b+=text(40,587,"Manual debug execution does not establish the supervised service configuration.","수동 디버그 실행만으로 systemd의 실제 설정을 증명할 수 없다.",19,600)
figure("memory-04-service-startup.svg","Service execution and argument validation","서비스 실행 경로와 인자 검증","Distinct failure gates; exact historical argv not retained","서로 다른 실패 지점 · 당시 실제 인자 배열은 미확인",b,632,("Recorded error categories + explanatory flow","관측된 오류 종류와 설명용 흐름"))

# 05: default versioned inclusive region, six executable checks.
def signal(m,s):
    if m<=5 and s<=5:return "KILL"
    if m<=10 and s<=10:return "TERM"
    return "NONE"
cases=[(4,4,"KILL"),(4,8,"TERM"),(5,5,"KILL"),(10,10,"TERM"),(4,11,"NONE"),(11,4,"NONE")]
assert all(signal(m,s)==want for m,s,want in cases)
assert 100*2/(2+18)==10 and 100*2/32==6.25
x0,y0,unit=110,490,25
b=rect(x0,y0-15*unit,15*unit,15*unit,"#edf1f4","#9db0bf",0)
b+=rect(x0,y0-10*unit,10*unit,10*unit,AMBER,"#b99f6e",0)
b+=rect(x0,y0-5*unit,5*unit,5*unit,RED,"#b9786e",0)
b+=path(f"M{x0} {y0-15*unit}V{y0}H{x0+15*unit}",False)
for v in (0,5,10,15):
    b+=text(x0+v*unit,y0+25,str(v),size=16,anchor="middle")+text(x0-18,y0-v*unit+5,str(v),size=16,anchor="end")
b+=text(x0+187,y0+52,"Available memory (%)","메모리 여유 (%)",18,600,"middle")
b+=text(40,105,"Free swap (%)","Swap 여유 (%)",17,600)
b+=text(x0+57,y0-39,"KILL",size=17,weight=750,anchor="middle",color="#8c453b")+text(x0+183,y0-193,"TERM",size=17,weight=750,anchor="middle",color="#8b692c")+text(x0+307,y0-307,"NONE",size=17,weight=750,anchor="middle")
for i,(m,s,want) in enumerate(cases):
    x,y=x0+m*unit,y0-s*unit
    b+=f'<circle cx="{x}" cy="{y}" r="5" fill="#29465c" stroke="#fff" stroke-width="1.5"/>'
b+=text(565,128,"Default v1.9.0 decisions","1.9.0 기본 판단",22,700)
for x,e,k in [(565,"Mem (%)","메모리 (%)"),(735,"Swap (%)","Swap (%)"),(910,"Signal","신호")]:b+=text(x,165,e,k,18,650)
for i,(m,s,want) in enumerate(cases):
    y=183+i*51
    b+=rect(550,y,530,43,RED if want=="KILL" else AMBER if want=="TERM" else "#edf1f4","#d5dfe7",4)+text(565,y+28,str(m),size=19)+text(735,y+28,str(s),size=19)+text(910,y+28,{"KILL":"SIGKILL","TERM":"SIGTERM","NONE":"No signal"}[want],{"KILL":"SIGKILL","TERM":"SIGTERM","NONE":"신호 없음"}[want],18,700)
b+=text(550,525,"KILL is tested before TERM.","KILL 조건을 TERM보다 먼저 검사한다.",19,650)
b+=text(40,582,"Memory % = 100 × MemAvailable / (MemAvailable + AnonPages)","메모리 % = 100 × MemAvailable / (MemAvailable + AnonPages)",18,650)
figure("memory-05-earlyoom-thresholds.svg","earlyoom 1.9.0 signal decision regions","earlyoom 1.9.0 신호 판단 영역","Defaults: both TERM limits 10%, both KILL limits 5%; inclusive comparisons","기본값: TERM 각각 10%, KILL 각각 5% · 경계값 포함",b,631,("Six synthetic boundary cases checked · no actual process signal","가상 경계값 여섯 가지 검증 · 실제 신호 전송 없음"))

# 06: three independent scopes.
b=""
cols=[
(40,"Kernel allocation OOM","커널 할당 OOM", "Allocation cannot progress","할당 진전 불가","Allowed memory scope","할당이 허용된 범위","Kernel victim selection","커널 종료 대상 선정","Kernel OOM log","커널 OOM 로그",RED),
(395,"Memory cgroup OOM","메모리 cgroup OOM","memory.max charge fails","memory.max Charge 실패","Limited cgroup subtree","제한된 cgroup 하위 계층","Scoped kernel OOM","범위 내 커널 OOM","memory.events delta","memory.events 변화량",AMBER),
(750,"earlyoom userspace","earlyoom Userspace","RAM + swap thresholds","RAM 및 Swap 임계값","Visible eligible processes","조회 및 종료 가능한 프로세스","Score / RSS policy","Score / RSS 정책","Daemon signal log","Daemon 신호 로그",GREEN)]
for x,e,k,t,tk,sc,sck,sel,selk,ev,evk,c in cols:
    b+=rect(x,116,330,418,"#f7f9fb","#cbd8e3")
    b+=text(x+165,153,e,k,21,750,"middle")
    b+=node(x+15,177,300,76,"Trigger","발생 조건",t,tk,c)
    b+=node(x+15,279,300,76,"Scope","판단 범위",sc,sck)
    b+=node(x+15,381,300,76,"Decision","종료 판단",sel,selk)
    b+=path(f"M{x+165} 253V279")+path(f"M{x+165} 355V381")
    b+=text(x+165,488,"Evidence","확인할 증거",16,700,"middle",MUTED)+text(x+165,514,ev,evk,18,650,"middle")
b+=text(40,574,"A signal or exit code alone does not identify the originating enforcement path.","종료 신호나 Exit Code만으로 어떤 판단 경로가 작동했는지 확정할 수 없다.",19,600)
figure("memory-06-oom-scopes.svg","OOM mechanisms have different decision scopes","OOM 메커니즘마다 다른 판단 범위","Host-level allocation, memory limit and userspace watchdog are distinct","호스트 할당, cgroup 메모리 한도, Userspace 감시는 별개",b,623)

p=R/"i18n/svg-ko-overrides.json"
catalog=json.loads(p.read_text())
for e,k in L.items():
    if e not in catalog:catalog[e]=k
p.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n")
print(f"6 native SVGs; 6 threshold cases and 2 synthetic pressure cases checked; {len(L)} labels")
