#!/usr/bin/env python3
"""Synthetic authorization examples, never actual cluster policy or topology."""
from pathlib import Path
import html,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3]/'apps/web';D=R/'public/figures/journals';L={}
def txt(x,y,e,k=None,s=19,w=500,a='start',c='#26394b'):
 L.setdefault(e,k or e)
 return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{s}" font-weight="{w}" text-anchor="{a}" fill="{c}">{html.escape(e)}</text>'
def rect(x,y,w,h,c='#eef4fa',st='#b0c5d4'):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{c}" stroke="{st}"/>'
def line(d,dash=False):
 return f'<path d="{d}" stroke="#7893a9" stroke-width="2" fill="none" marker-end="url(#a)"'+(' stroke-dasharray="6 4"' if dash else '')+'/>'
def node(x,y,w,h,e,k,sub,ks,c='#eef4fa'):
 return rect(x,y,w,h,c)+txt(x+w/2,y+30,e,k,21,700,'middle')+txt(x+w/2,y+57,sub,ks,16,500,'middle')
def fig(n,e,k,sub,ks,b,h):
 L.setdefault(e,k)
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{h}" viewBox="0 0 1120 {h}" role="img" aria-label="{html.escape(e)}"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7893a9"/></marker></defs>'
 s+=rect(1,1,1118,h-2,'#fff','#d0dce6')+txt(40,48,e,k,28,750)+txt(40,78,sub,ks,17,c='#61758b')+b+txt(40,h-16,'Illustrative policy model · not deployed permissions','설명용 정책 모델 · 실제 적용 권한 아님',14,c='#61758b')+'</svg>\n'
 p=D/(n+'.svg');p.write_text(s);ET.parse(p)
b=node(40,125,290,82,'ServiceAccount','ServiceAccount','Identity in namespace A','Namespace A의 신원')
b+=node(410,125,300,82,'RoleBinding','RoleBinding','Binding in namespace B','Namespace B의 Binding')
b+=node(790,125,290,82,'Role / ClusterRole','Role / ClusterRole','Resource + verb rules','Resource + Verb 규칙')
b+=line('M330 166H410')+line('M710 166H790')
b+=txt(40,260,'Request attributes','요청의 속성',22,700)
for i,(e,k) in enumerate([('Subject','요청 신원'),('API group','API Group'),('Resource / subresource','Resource / Subresource'),('Verb + namespace','Verb + Namespace')]):
 x=40+i*260;b+=rect(x,280,245,59)+txt(x+122,315,e,k,17,650,'middle')
b+=node(40,380,300,80,'Authentication','인증','Establish identity','신원 확인')+node(410,380,300,80,'Authorization','인가','Match effective grants','유효 권한 대조')+node(780,380,300,80,'Admission','Admission','Applicable write requests','해당 쓰기 요청 검사')
b+=line('M340 420H410')+line('M710 420H780')
b+=txt(40,499,'A namespaced binding grants access in its own namespace, not the subject namespace.','Namespace 범위의 Binding은 신원이 아닌 Binding의 Namespace에 권한을 부여한다.',19,650)
fig('identity-01-rbac-scope','Identity, rules and binding scope','신원, 권한 규칙과 Binding 범위','Generic namespaces A and B; API authorization is not admission','가상의 Namespace A와 B · API 인가와 Admission은 별개',b,548)
b=txt(40,125,'API request','API 요청',20,700)+txt(505,125,'Required resource and verb','필요한 Resource 및 Verb',20,700)+txt(950,125,'Example','예시',20,700)
rows=[('List Pod names','Pod 이름 목록','pods · list',True),('Read one Pod','Pod 하나 조회','pods · get',True),('Read container logs','Container 로그 조회','pods/log · get',True),('Read Secret','Secret 조회','secrets · get',False),('Execute a command','명령 실행','pods/exec · create',False),('Delete Pod','Pod 삭제','pods · delete',False)]
for i,(e,k,v,ok) in enumerate(rows):
 y=143+i*54;b+=rect(40,y,1040,46,'#f2f7fa' if i%2==0 else '#fff','#dbe4eb')+txt(55,y+29,e,k,19)+txt(505,y+29,v,s=19)+txt(985,y+29,'Allow' if ok else 'Deny','허용' if ok else '거부',18,700,'middle','#276748' if ok else '#a34437')
b+=txt(40,490,'Assumes no other matching grants; Kubernetes RBAC permissions are additive.','다른 허용 규칙이 없다고 가정 · Kubernetes RBAC 권한은 합산된다.',19,650)
fig('identity-02-log-subresource','Pod access is not automatically log access','Pod 조회 권한이 로그 권한을 포함하지는 않는다','Hypothetical read-only observer; not a complete Runner role','가상의 조회 전용 Observer · Runner 전체 Role이 아님',b,535)
b=node(40,125,290,83,'Browser','브라우저','Authorization redirect','인가 페이지 이동')
b+=node(410,125,300,83,'Identity provider','Identity Provider','User signs in','사용자 로그인')
b+=line('M330 167H410')+line('M560 208V255H190V291')
b+=node(40,291,300,83,'Application backend','애플리케이션 Backend','Callback with code','Code를 받은 Callback')
b+=node(410,291,300,83,'Token / profile API','Token / Profile API','Server-to-server request','서버 간 요청')
b+=line('M340 332H410')
b+=rect(780,291,300,83,'#f9e6e1','#d8a398')+txt(930,322,'DNS / connect failure','DNS / 연결 실패',20,700,'middle')+txt(930,350,'EAI_AGAIN / ETIMEDOUT',s=17,a='middle')
b+=line('M710 332H780',True)
b+=node(410,427,300,83,'Application session','애플리케이션 Session','Identity established','신원 확인 이후')
b+=node(780,427,300,83,'Object access check','객체 접근 검사','Read / edit decision','읽기 / 수정 판단','#e7f3ec')
b+=line('M560 374V427')+line('M710 468H780')
fig('identity-03-oauth-boundary','Browser login and backend reachability','브라우저 로그인과 Backend 연결','Authorization-code flow, simplified; observed errors are not policy denials','인가 Code 흐름의 개념도 · 관측 오류는 정책 거부가 아님',b,562)
# Evaluate a tiny set-relation model; not an OpenFGA deployment.
members={'alice'};direct={'bob'}
def can_view(u):return u in members or u in direct
assert [can_view(x) for x in ('alice','bob','carol')]==[True,True,False]
members.remove('alice')
assert [can_view(x) for x in ('alice','bob','carol')]==[False,True,False]
b=node(40,130,245,80,'Alice','Alice','Team member','팀 멤버')
b+=node(355,130,265,80,'Team A','Team A','member userset','member Userset')
b+=node(795,130,285,80,'Document X','Document X','viewer relation','viewer 관계','#e7f3ec')
b+=line('M285 170H355')+line('M620 170H795')
b+=txt(707,153,'Inherited','상속',17,600,'middle')
b+=node(40,251,245,80,'Bob','Bob','Direct viewer','직접 Viewer')
b+=line('M285 291H750V191H795')
b+=txt(40,382,'Check viewer on Document X','Document X의 viewer 검사',21,700)
for x,e,k in [(40,'Subject','신원'),(340,'Before revocation','철회 전'),(720,'After team removal','팀 제외 후')]:b+=txt(x,420,e,k,19,700)
for i,(u,before,after) in enumerate([('Alice',True,False),('Bob',True,True),('Carol',False,False)]):
 y=434+i*49;b+=rect(40,y,1040,42,'#f3f7fa','#dce5eb')+txt(55,y+27,u,s=20)
 for x,ok in [(340,before),(720,after)]:b+=txt(x,y+27,'Allow' if ok else 'Deny','허용' if ok else '거부',20,700,c='#28664c' if ok else '#a34437')
fig('identity-04-relation-graph','Object access can be inherited or direct','객체 접근 권한의 상속과 직접 부여','Synthetic relation graph; reference set model executed locally','가상의 관계 그래프 · 집합 모델만 실행하여 검증',b,628)
p=R/'i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
for k,v in L.items():
 if k not in d:d[k]=v
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('4 native diagrams; 6 synthetic relation decisions verified')
