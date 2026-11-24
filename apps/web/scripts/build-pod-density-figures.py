#!/usr/bin/env python3
"""Analytical figures for the sanitized November 2026 K3s Pod-density article.

All numbers are public defaults, the reported rounded reference count, or
explicit hypothetical capacity arithmetic. No production topology or logs
are encoded. SVG labels have Korean counterparts in the existing dictionary.
"""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'apps/web/public/figures/journals'
LO={}
def tx(x,y,en,ko=None,size=21,weight=500,anchor='start',color='#26384b'):
    if ko is not None: LO.setdefault(en,ko)
    else: LO.setdefault(en,en)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(en)}</text>'
def rect(x,y,w,h,fill='#fff',stroke='none',r=5,sw=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(x,y,X,Y,color='#738da5',sw=2,arrow=False,dash=False):
    return f'<path d="M{x} {y}L{X} {Y}" fill="none" stroke="{color}" stroke-width="{sw}"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="6 5"' if dash else '')+'/>'
def node(x,y,w,h,title,ko,sub,ksub,fill='#edf4fa',stroke='#91adc3'):
    return rect(x,y,w,h,fill,stroke,9)+tx(x+w/2,y+31,title,ko,22,700,'middle')+tx(x+w/2,y+59,sub,ksub,16,500,'middle')
def fig(name,title,ko,sub,ksub,body,h=550):
    LO.setdefault(title,ko)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(title)}"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#738da5"/></marker><pattern id="unused" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 7L7 0" stroke="#c6d5e1" stroke-width="1"/></pattern></defs>'
    s+=rect(1,1,1118,h-2,'#fff','#d0dce6',14)+rect(26,26,6,50,'#2c608c',r=2)+tx(46,52,title,ko,28,750)+tx(46,82,sub,ksub,17,color='#61758b')+line(40,105,1080,105,'#dce5ed',1)
    s+=body+line(40,h-39,1080,h-39,'#dce5ed',1)+tx(46,h-13,'Analytical example · not production telemetry','설명용 계산 · 실제 운영 측정값 아님',14,color='#61758b')+'</svg>\n'
    p=DIR/(name+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
# 01: scheduling versus sandbox creation.
b=rect(48,128,1024,166,'#f3f7fb','#d7e3ec',10)+tx(68,156,'Scheduling boundary','스케줄링 경계',19,700)
b+=node(70,175,222,82,'Pending Pod','Pending Pod','Pod object','Pod 오브젝트')
b+=node(343,175,345,82,'Scheduler','Scheduler','Slots + requests + placement','슬롯 + requests + 배치 제약')
b+=node(747,175,302,82,'Bound to node','노드 할당','spec.nodeName','spec.nodeName','#e7f4ed','#8eb6a0')
b+=line(292,216,343,216,arrow=True)+line(688,216,747,216,arrow=True)
b+=tx(515,282,'Too many pods → FailedScheduling','Too many pods → FailedScheduling',17,600,'middle','#a74639')
b+=rect(48,318,1024,190,'#f5f8f7','#d7e3dd',10)+tx(68,346,'Sandbox and networking boundary','샌드박스 및 네트워크 경계',19,700)
b+=node(70,365,222,82,'Kubelet / CRI','Kubelet / CRI','Create sandbox','샌드박스 생성')
b+=node(343,365,345,82,'CNI / IPAM','CNI / IPAM','Allocate Pod IP','Pod IP 할당')
b+=node(747,365,302,82,'Sandbox ready','샌드박스 준비','Continue container startup','컨테이너 시작 단계','#e7f4ed','#8eb6a0')
b+=line(292,406,343,406,arrow=True)+line(688,406,747,406,arrow=True)
b+=tx(515,477,'IP exhaustion → possible FailedCreatePodSandBox','IP 부족 → FailedCreatePodSandBox 가능',17,600,'middle','#a74639')
fig('pod-density-01-admission','Two independent admission boundaries','서로 다른 두 수용량 제약','Binding a Pod does not guarantee a usable network sandbox','노드에 배치돼도 네트워크 샌드박스 생성이 보장되는 것은 아니다',b,565)
# 02: all bars share identical numeric units but the IP scenario is separate.
scale=2.66;x=280
b=tx(48,143,'Scheduler slots','스케줄링 슬롯',22,700)
for y,label,ko,cap in [(170,'Old limit','기존 상한',110),(245,'New limit','변경 상한',220)]:
    b+=tx(48,y+30,label,ko,21,600)
    b+=rect(x,y,253*scale,43,'url(#unused)','#cad8e5',4)
    b+=rect(x,y,103*scale,43,'#317db4',r=0)
    b+=rect(x+103*scale,y,(cap-103)*scale,43,'#b5d7cc',r=0)
    b+=line(x+cap*scale,y-5,x+cap*scale,y+50,'#394f62',2)
    b+=tx(x+103*scale/2,y+28,'103','103',21,700,'middle','#fff')
    if cap==110:
        b+=tx(985,y+28,'7 free','여유 7',19,700,'start','#28644c')
    else:
        b+=tx(x+(103+cap)*scale/2,y+28,'117 free','여유 117',19,700,'middle','#234d3f')
    b+=tx(x+cap*scale,y-10,str(cap),size=17,anchor='middle')
b+=tx(48,323,'Address budget','IP 주소 예산',22,700)
b+=tx(48,375,'Example /24','/24 예시',21,600)
b+=rect(x,344,253*scale,43,'#f1d09a','#c69b55',0)
b+=rect(x,344,220*scale,43,'#7896b0',r=0)
b+=tx(x+110*scale,372,'220 hypothetical IP users','IP 사용 Pod 220개 가정',18,700,'middle','#fff')
b+=tx(x+236.5*scale,372,'33','33',20,700,'middle','#5b4020')
b+=tx(x+253*scale,337,'253',size=17,anchor='middle')
b+=tx(48,434,'93.6% → 46.8%','93.6% → 46.8%',27,700)
b+=tx(48,465,'At the same reference count of 103','같은 기준 Pod 수 103개에서',17,color='#61758b')
b+=tx(571,434,'253 − 220 = 33','253 − 220 = 33',27,700)
b+=tx(571,465,'Illustrative reserve, not measured free IPs','예시 여유분 · 실측 가용 IP가 아님',17,color='#61758b')
assert round(103/110*100,1)==93.6 and round(103/220*100,1)==46.8
fig('pod-density-02-budget','Pod slots and IP addresses are separate budgets','Pod 슬롯과 IP 주소는 별개의 예산','Same numeric scale; the IP row assumes one address per Pod','같은 수치 스케일 · IP 행은 Pod당 주소 하나를 가정',b,520)
# 03: illustrative prefix partition, not an internal network topology.
b=tx(48,144,'Fixed cluster range: /16','고정 클러스터 대역: /16',22,700)
for y,prefix,count,addr in [(166,24,256,256),(223,23,128,512),(280,22,64,1024)]:
    b+=tx(48,y+27,f'/{prefix}',size=23,weight=700)
    # 16 representative units: 1,2,4 units per shown block.
    group=2**(24-prefix);unit=35
    for i in range(0,16,group):
        b+=rect(144+i*unit,y,unit*group-2,38,'#c1d8e8','#8eacc5',2)
    b+=tx(737,y+25,f'{count} blocks × {addr:,} addresses',f'{count}개 블록 × 주소 {addr:,}개',19,600)
    assert count*addr==65536
b+=tx(144,343,'Representative slice (16 /24 units)','대표 구간 (/24 단위 16개)',16,color='#61758b')
b+=line(48,366,1072,366,'#dce5ed',1)
b+=tx(48,400,'Existing allocation is not a resize operation','기존 할당은 단순 Resize할 수 없다',22,700)
for i in range(4):
    b+=rect(48+i*150,422,148,48,'#c1d8e8','#8eacc5',2)+tx(122+i*150,452,f'/24 · {i+1}',size=18,anchor='middle')
b+=rect(48,488,598,48,'#f4d7d0','#bd6654',3)+tx(347,519,'One /22 overlaps four existing /24 blocks','/22 하나가 기존 /24 네 개와 겹침',19,700,'middle','#8e3c30')
b+=line(347,470,347,488,'#bd6654',2)
b+=rect(693,422,380,114,'#f8f5ed','#dfc79e',7)
b+=tx(713,452,'Public K3s default ranges','K3s 공개 기본 대역',18,700)
b+=tx(713,480,'10.42.0.0/16 + 10.43.0.0/16',size=17)
b+=tx(713,510,'→ 10.42.0.0/15 would overlap Services','→ /15 확장 시 Service 대역과 중복',15,600,color='#89572d')
fig('pod-density-03-cidr','Node CIDR size trades address space for node blocks','노드 CIDR의 크기와 노드 블록 수','Public default-style ranges and theoretical partition sizes','공개 기본값을 이용한 이론적 주소 분할',b,590)
# 04: 4 nodes of 220 each; 180 each, one fails.
b=tx(48,145,'Before failure: 4 × 180 = 720 Pods','장애 전: 4 × 180 = 720 Pods',22,700)
for i in range(4):
    xx=48+i*260
    b+=rect(xx,164,244,116,'#f4f8fb','#c7d5e1',8)+tx(xx+122,194,f'Node {i+1}',f'노드 {i+1}',19,700,'middle')
    b+=rect(xx+16,207,212,34,'#b5d7cc',r=0)+rect(xx+16,207,212*180/220,34,'#317db4',r=0)
    b+=tx(xx+98,230,'180',size=20,weight=700,anchor='middle',color='#fff')+tx(xx+210,230,'40',size=16,weight=700,anchor='middle',color='#234d3f')
    b+=tx(xx+122,267,'220 slots','220 슬롯',16,anchor='middle',color='#61758b')
b+=tx(48,325,'After loss of one node','노드 한 대 장애 이후',22,700)
b+=node(48,348,235,89,'180 displaced','이동 필요 180개','From the failed node','장애 노드에서 이동','#f4d7d0','#bd6654')
b+=line(283,392,350,392,arrow=True)
b+=rect(350,348,674,89,'#f4f8fb','#c7d5e1',8)
b+=rect(363,361,432,63,'#b5d7cc',r=4)+rect(795,361,216,63,'#f4d7d0',r=4)
# Explicit bars above are drawn once, with two distinct outcomes.
b+=tx(579,387,'120 free slots','여유 120 슬롯',24,700,'middle','#234d3f')+tx(579,410,'3 × 40',size=17,anchor='middle',color='#234d3f')
b+=tx(903,387,'60 short','60개 부족',22,700,'middle','#8e3c30')+tx(903,410,'180 − 120',size=17,anchor='middle',color='#8e3c30')
b+=rect(48,469,1024,80,'#edf4fa','#b6c9d9',8)
b+=tx(68,500,'N-1 slot ceiling: (4 − 1) × 220 = 660','N-1 슬롯 상한: (4 − 1) × 220 = 660',23,700)
b+=tx(68,529,'Evenly distributed: 165 per node, before placement constraints','균등 배치 기준 노드당 165개 · 배치 제약 미고려',18)
assert 3*40==120 and 180-120==60 and 3*220==660 and 660//4==165
fig('pod-density-04-recovery','Admission capacity is not recovery capacity','배치 수용량과 장애 복구 수용량은 다르다','Four equal hypothetical nodes, each limited to 220 slots','동일한 가상 노드 4대 · 각각 220개 슬롯',b,602)
p=ROOT/'apps/web/i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
for k,v in LO.items():
    if k not in d:d[k]=v
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Generated four Pod-density analytical SVGs; labels:',len(LO))
