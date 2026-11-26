#!/usr/bin/env python3
"""Generate explanatory figures, including measured per-mapping smaps values."""
from pathlib import Path
import html,json,subprocess,sys,xml.etree.ElementTree as ET
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
def fig(name,e,k,sub,ks,b,h,footer=('Explanatory model · not a historical memory inventory','설명용 모델 · 당시 메모리 실측값 아님')):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7793a8"/></marker></defs>'
 s+=r(1,1,1118,h-2,'#fff','#d0dce5')+t(40,48,e,k,28,750)+t(40,79,sub,ks,17,c=M)+b+t(40,h-17,*footer,14,c=M)+'</svg>\n'
 f=D/name;f.write_text(s);ET.parse(f)
# Derive the display values from a verified run, not from the historic host.
result=json.loads(subprocess.check_output([sys.executable,str(R/'scripts/memory-accounting-example.py')],text=True))
assert result['rss_sum_kib']==8192 and result['pss_sum_kib']==4096
assert round(54101261*4096/2**30,1)==206.4 and round(2687499*4096/2**30,2)==10.25 and round(910581760/2**20)==868
# 01 historical observations; no inferred linkage.
v=n(40,116,500,80,'Host graph','호스트 그래프','Roughly one fifth → near saturation','약 20% → 포화에 가까운 수준',A)+n(580,116,500,80,'Selected Pod charts','확인한 Pod 그래프','No corresponding jump observed','이에 상응하는 급증 미관측')
v+=r(40,236,500,220,'#f2f6fa','#c4d3df')+t(60,270,'earlyoom selection','earlyoom 종료 대상',23,700)+t(60,323,'≈ 608 MiB',None,39,750)+t(60,354,'Reported VmRSS','보고된 VmRSS',19,600)+t(60,389,'Victim size ≠ total spike','종료 대상 크기 ≠ 전체 증가분',19,650)
v+=r(580,236,500,220,'#f2f6fa','#c4d3df')+t(600,270,'Later OOM task dump','이후 OOM Task Dump',23,700)+t(600,323,'54,101,261 pages','54,101,261페이지',34,750)+t(600,354,'≈ 206.4 GiB if page size = 4 KiB','4 KiB 페이지 가정 시 약 206.4 GiB',19,600)+t(600,389,'Large resident-memory candidate','큰 상주 메모리 소비 후보',19,650)
v+=t(40,506,'No confirmed time alignment, exclusive ownership or initiating allocation path.','시각 일치, 독점 사용량 및 최초 할당 경로는 확인되지 않았다.',19,650)
fig('memacct-01-evidence.svg','August observations: victim versus consumer','8월 관측: 종료 대상과 소비 후보','Sanitized records; page conversion is conditional','비식별화 기록 · 페이지 단위 환산은 가정에 따름',v,554,('Historical observations · not a common time-series sample','당시 관측 기록 · 동일 시각의 시계열 아님'))
# 02 synthetic per-process accounting, shared object, not physical partition.
v=n(40,120,500,70,'Process A','프로세스 A','RSS 6 MiB / PSS 4 MiB','RSS 6 MiB / PSS 4 MiB')+n(580,120,500,70,'Process B','프로세스 B','RSS 5 MiB / PSS 3 MiB','RSS 5 MiB / PSS 3 MiB')
v+=n(40,275,300,80,'Private A','개인 A','2 MiB','2 MiB',G)+n(410,275,300,80,'Shared region','공유 영역','4 MiB','4 MiB',A)+n(780,275,300,80,'Private B','개인 B','1 MiB','1 MiB',G)
v+=p('M290 190V235H190V275')+p('M290 235H500V275')+p('M830 190V235H930V275')+p('M830 235H620V275')
v+=n(40,420,500,77,'RSS sum = 11 MiB','RSS 합 = 11 MiB','Counts shared 4 MiB twice','공유 4 MiB를 두 번 집계',F)+n(580,420,500,77,'PSS sum = 7 MiB','PSS 합 = 7 MiB','Apportions shared memory','공유 메모리를 나눠 집계',G)
assert (2+4)+(1+4)==11 and (2+2)+(1+2)==7
fig('memacct-02-shared-pages.svg','Mapping counts versus proportional memory','매핑 집계와 비례 메모리 집계','Hypothetical private and shared regions','가상의 개인 및 공유 메모리 영역',v,548)
# 03 observed mapping data
v=t(40,132,'Measurement (KiB)','측정값 (KiB)',21,700)+t(420,132,'Parent','부모',21,700)+t(620,132,'Child','자식',21,700)+t(860,132,'Sum','합계',21,700)
for i,(key,e,k) in enumerate([('Size','Virtual mapping size','가상 매핑 크기'),('Rss','RSS','RSS'),('Pss','PSS','PSS'),('Private','Private clean + dirty','Private Clean + Dirty')]):
 a,b=[(q['Private_Clean']+q['Private_Dirty'] if key=='Private' else q[key]) for q in (result['parent'],result['child'])]
 y=154+i*68;v+=r(40,y,1040,59,G if key=='Pss' else ('#f2f6fa' if key!='Rss' else A),'#c4d3df',5)+t(55,y+37,e,k,20,650)+t(420,y+37,str(a),None,22,700)+t(620,y+37,str(b),None,22,700)+t(860,y+37,str(a+b),None,22,750)
v+=t(40,462,'Both processes mapped the same 4 MiB backing object.','두 프로세스가 동일한 4 MiB 저장 객체를 매핑했다.',20,700)+t(40,491,'Mapping-only measurements; process totals and cgroup charges were not measured.','해당 매핑만 측정했으며 프로세스 전체 및 cgroup Charge는 측정하지 않았다.',17,c=M)
fig('memacct-03-experiment.svg','Actual two-process shared mapping results','실제 두 프로세스 공유 매핑 결과','memfd_create + MAP_SHARED + fork + smaps','memfd_create + MAP_SHARED + fork + smaps',v,540,('Executed 4 MiB experiment; no memory-pressure test','실제 4 MiB 실험 · 메모리 압박 실험 아님'))
# 04 subset relation, not additive.
v=n(40,115,490,75,'AnonPages','AnonPages','Anonymous resident pages','익명 상주 페이지')+n(590,115,490,75,'MemAvailable','MemAvailable','Availability estimate, not a pool','가용량 추정값 · 독립 영역 아님',A)
v+=r(40,230,490,172,'#f2f6fa','#c4d3df')+t(60,265,'Cached','Cached',22,700)+n(60,283,450,82,'Includes shmem / tmpfs','shmem / tmpfs 포함','Do not add Shmem again','Shmem 중복 합산 주의',G)
v+=r(590,230,490,172,'#f2f6fa','#c4d3df')+t(610,265,'Slab','Slab',22,700)+n(610,285,210,80,'SReclaimable','SReclaimable','Reclaimable','회수 가능',G)+n(850,285,210,80,'SUnreclaim','SUnreclaim','Unreclaimable','회수 불가',A)
v+=n(40,450,490,74,'PageTables / KernelStack','PageTables / KernelStack','Kernel resources beyond RSS','RSS 밖의 커널 자원')+n(590,450,490,74,'Dirty / Writeback','Dirty / Writeback','Page states, not separate pools','페이지 상태 · 별도 영역 아님',A)
fig('memacct-04-host-fields.svg','Host memory counters are not all additive','호스트 메모리 지표는 모두 합산할 수 없다','Selected fields and overlap relationships','주요 항목과 중첩 관계',v,575)
# 05 hierarchy synthetic (parent and leaves) + charge ownership.
v=n(345,115,430,75,'Example parent: 900 MiB','부모 예시: 900 MiB','Includes descendants','하위 계층 포함',G)
v+=n(40,255,470,77,'Pod A: 500 MiB','Pod A: 500 MiB','Parent-local charge assumed zero','부모 자체 Charge 0 가정')+n(610,255,470,77,'Other service: 400 MiB','기타 서비스: 400 MiB','Outside selected Pod subtree','선택한 Pod 범위 밖',A)
v+=p('M560 190V220H275V255')+p('M560 220H845V255')
v+=n(40,390,225,74,'Container A1','Container A1','300 MiB','300 MiB')+n(285,390,225,74,'Container A2','Container A2','200 MiB','200 MiB')
v+=p('M275 332V365H152V390')+p('M275 365H397V390')
v+=n(610,390,470,74,'Shared page charge','공유 페이지 Charge','Not divided by PSS rule','PSS 방식으로 분배되지 않음',A)
v+=p('M845 332V390',True,True)
v+=t(40,515,'Correct parent total: 900 MiB; parent + descendants would double-count charges.','부모 합계는 900 MiB · 부모와 자식을 합하면 Charge가 중복된다.',19,650)
assert 300+200==500 and 500+400==900
fig('memacct-05-cgroup-hierarchy.svg','Hierarchy and memory-charge boundaries','cgroup 계층과 메모리 Charge 경계','Synthetic subtree, not the host cgroup configuration','가상 하위 계층 · 실제 호스트 cgroup 구성 아님',v,564)
# 06 synthetic working set calculation with scope.
v=t(40,132,'Example cgroup usage: 1024 MiB','가상 cgroup 사용량: 1024 MiB',22,700)
v+=r(40,155,650,60,G,'#a5bda9',0)+r(690,155,390,60,A,'#c4aa77',0)
v+=t(365,191,'Working set estimate: 640 MiB','Working Set 추정: 640 MiB',21,700,'middle')+t(885,191,'Inactive file: 384 MiB','Inactive File: 384 MiB',20,700,'middle')
v+=t(40,255,'max(usage − inactive_file, 0) = 640 MiB','max(usage − inactive_file, 0) = 640 MiB',21,650)
v+=r(40,310,1040,175,'#f2f6fa','#c4d3df')+t(60,344,'Host measurement scope','호스트 측정 범위',22,700)
v+=n(60,366,490,80,'Selected Pod series','선택한 Pod 시계열','Only selected workloads','선택한 워크로드만 집계')+n(580,366,480,80,'Other consumers','기타 메모리 소비 영역','Not represented by those series','해당 시계열에 포함되지 않음',A)
v+=t(40,535,'Working set is provider-dependent and not identical to RSS or unreclaimable memory.','Working Set은 통계 제공 방식에 따라 다르며 RSS나 회수 불가 메모리와 같지 않다.',19,650)
assert max(1024-384,0)==640
fig('memacct-06-working-set.svg','Working-set estimate and monitoring scope','Working Set 추정값과 모니터링 범위','Synthetic cAdvisor-style example; original dashboard query unknown','cAdvisor 방식의 가상 예시 · 당시 Dashboard Query 미확인',v,584)
q=R/'i18n/svg-ko-overrides.json';catalog=json.loads(q.read_text())
for e,k in L.items():catalog.setdefault(e,k)
q.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'6 native SVGs; {len(L)} unique labels; measured mapping results: {json.dumps(result)}')
