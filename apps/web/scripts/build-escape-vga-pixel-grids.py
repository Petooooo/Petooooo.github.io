#!/usr/bin/env python3
"""Rebuild the five pixel-art figures from the June 2023 report's recovered
logical grids. No resampling, antialiasing, adaptive color palette, or contour
simplification is performed by this generator.

Source evidence: PDF xrefs 23, 28, 31, 33, 34, 37, 38, 39, 123, 125, 126, 127.
The retained grids are inferred from the original embedded images (not from
the old resized SVG). Screen dimensions 160x120 and sprite sizes follow the
report; screen boundaries and center sampling were fitted to source edges.
Map platform runs were extracted at their source row centers; sprite masks
are reused at observed or documented locations. Red screenshot annotations
are separate ellipse redraws, not game pixels. The original bitmaps were
reviewed, but not committed. Reconstruction is not a bit-exact RTL ROM dump.
"""
from pathlib import Path
import base64, zlib, html, json, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'apps/web/public/figures/journals'
DATA={
'start':(160,120,'eNrtm22P5CAIgElM4P//49u7mWkReVPbjpeVL521rj4BREULsGXLFimIuPmm8HBxPFwcLwSklzQF5Fa3XpvVG3k7XwUoKlQFTRWNtmlAEnTwvZXn8TUtO91r3WX4LL1q1o34yAFW1THOh611m/5pmo+G+PDUXRcfPcOH5sCd4aOr+Gy8gI8G+CjJV/4KmzNS+oOQz/ybxc0MXykH4AuMXD492CrdmPo8fgbx/FVcTj7s4QOdT1e4ygddfCXJ1/SX4aOAz5n1SqNATPKB3jdYc1cn39vnSu1/2fjCyrr5vKAu9FaPj0x8UQpN96yLnRBkW7Ww+PLzsJdVY3zgzoAmX+HCC+15OeADzfQmX7BerDT3ISydfN5iTqpPovp80vUYa8xnxxRvQgn46hfc4RRL9/KpGp3hA27R1hFjvsb5GntpUTzgc0JzPU6y+5e7RTgfLMyXWvcvgrf55vA23xxels8KXD0plhgvzZfcetlrUtBDdMRXRvjU+cvd5SXSWwKPLxTm+Ywc0BDfG4sMwHE+8vni/F9l1n/1FMAxPlJTGI6xQ68795f38YHFmhi2l/Plylz/a9cps3xWNmWMT88f9PAp0VnJpqzHp+7VluBTF/Df5nOyFdfywdj4cLIVC/JZ6YQr+MbWB6l8Fkzy2edbHfldDVCObVI2xo/ykZv0k/q8Y8EdjF/yks5nuu0LfBCfYb5/fIkPtBU+iDwgAPG05bOySEJky5Ytv1KSS4Nohs1P1trJhnlib87u4XUYvZd7+bQTCatacD5xE58xWZObH6H7+CzAET5YiK9Z2D7Gl72BAtmtwX/HB/rI7+HrviEThE/z7DsMUnqUcPggdwXqBj7o4IP7+KK7PEEynTpuyMhe4CK+2RsoSb44rdDN594avYYv4X/BDRk9rfIQH9tqdvDR/XyZrGtw6/eS8RFFd++GjH/kc+f4Ta72wEm0T/BBjs/WqZvTjgF7+TT7gpKYsewAStPr7KhGz823bNmyZcuWLU/K3DePF30tiR6f/KjrmoYxWYwJPvYe+QOZkvU+sOoBK7McrfO6iHVzKPo3+fhnLPKTlp/npwA51Pnz/R/sBZ7Fhx8dn4AezWX42GeZH1bFFHi6Qs0n/g9VzcoHHF4V25fX419B1lZA1hTCqdlDT/WLlk90U2khsm9Tr/YertbabFJpaPLVFrKsFPFhPQZsvtbqYhxhGxtsvqz+QLcvCvuCQoGiI2V8AKt88uF1YTQOe7jInNP7YuNt2bJly5Yn5A+LjJAo'),
'failure':(160,120,'eNrtmetuwyAMhS1hifd/43XJ1gQ4NjYhKdp89mNpyuXDgDEuUSgUCoVCoaWUN9lLGgs7K+Si7FEnl18UTZZt50IAoS6AK1jGAnDO5Ba+Znw9vh5hXRP16eLLXr5sNmBjLAsf7k+bTx+gNvi2E3qcj6bzZS+f3YBihx/ko5v5aB5f+fl4NPGdi0M+tYLDn7fLHL1EfOTlIxcfNXzk5CPEJM1vUWERPvoHfKTwZef6oxnrj0Q+2EmPj7x85OSjyqsQ2sqAT2CS+axhYFZdLm6V1ADLwte2Xz7IfKSGnDofiXzC+UFooXf4CJ09Fj55D8jn3QifsLPQiZm1l5p/ARVc957n72PS+guFQqFQKBQKhUKhUCgUCoVCoUXFu85v1qPbCPn97lqTN/Hxb9OL2u8NybQy4D7VnF6i119aCJHSrtPjoc/znWBeU5yQHkHp430TJkl37dlqG9Rf1BQyYFI7GfZREl+x9E4GVAAFIzae1OcsNfN5+RpChsP3mbGszuf3AIAp2Qg3f4S8VB/vhwVYrSo2wvdtY8mD6v2VfMfw6q/VuTTwpd1IGqFphhs8y1qz8G2+/IoBoblse8HGl5JrGw3A3cuXJuDdypdMc91rA/m/uXy8Oh+P44EZ5tX4uGn0QT4vIN/Ad2n91fHzPD6jqxa9k+L+P+if6wMQn1bP0XVC8Ivzd7RQBU7+JAG8i1wyEQOLuYIDIaQ4PqSZ8tuviXm4ir3tXZsBEZ+A3OIV/8jRq6nodfvVa9LOZ57hwYsRw4B8Lh+6i/Uvcz/ps2FH7OMbjvMf4Ru/iIwfZfumtw3EcVNiI19vo5CVT0wpXjTglgQQDz3LQdhJeV7ns9T2p2JmrcC2CTXlIHHBTi4nnFEzUtvvaBY2DJJtzjSCy3yM9pk2nAmZVA+gVv8uvvdxUgU0QnKuk0YU5ncK5O+ZKIHQh/guZLHlnTPdfAogD2Kv/kvt4nwUfH+Yj1bnc+kLY3hi5Q=='),
'success':(160,120,'eNrt2tuOhCAMBuAmvfjf/403M/HAoa0otuIsZLNZwyqfBZyCQzTLLLPMMsss/7TgW8ZQrJJdhLyC0qNcntQIl6pr95OKyx4Ak7My3t7cGR9UX97SES8LoMyrbrTXhzM+Enw440uqiv8hzYdLPmjhk4aW6CPjVsW7bvGRh8+YV1JT1OqTebaPlBA1+ajhKXaXD/D2lfGgJh/pvFt8JF8z/3MEH1U+ustHlo8e8FGjjwJ8FOsjw4deX0NKoAJrX33ztk/rCwhJy3UfqSmR4pPnueajs/ND8WkzsdtHpz7fpIgLI0kZ3pd81OsjyWH4xNgYvs9Bl085U518p33pP/zvZd7wq9C5SO5dPA/OG1NoPQ5H0w0H1DOqUXkjCYGRgdDL4LwRhMDQQGAoYH9zrmArRW0Ln2tErQ6DfIjABKd/RLmOSXut1tC9vpOmoVXb5zurD5sV3hhY26rOzzlxMQpxK/PwCmGLDnPX95n0WHq7kq6+D3ZxnHzFPoHmyx/HIb3Ln1KNPWXulpbsXJcAMqdA421V+YZyuzf2il/tkzHiC8CdtwB9fXxlfRntw7n4caSPz/mQ+CjKd26BziE+JYDi/LW6N9gH24eK5+ZLgel3GzTf8pvjfdziWz/oSp6fD1d8/ISPhcGWzoCkuj7FMcESfGWUOPdxpC8Z61sGSOkDOKvKny2eK7g9VFmUaI0U52XLTrPwXXmbet23dCMJvE9d5UOMD4KPWQJWtxPs4y2Xl33fyrLL/X3CFBZ99eSN9rHOW+rywyBfBXytj8u0OcYHNUrv8vHzPrbmL1dpc5APTT4ewce1D5UP0T4jgIAWPk9fuUsljsC9Sk+b7+atn6O0JHqwgEqfJ4ns+nPbu5rtrlei4rOGZJpofy8DDx9pPka9/pCq1w3Vm33KvoooEBMadaMhzFcKlapQH1gRslbxrE8tg/vwlA8/4cNzPvyAD9NntPB6H5714eU+TJ/dAl7tw/M+TN/0Td/0Td8IPqDHd/uX7I6/39zl6yY2XM7yXbpgWf4AbQelCQ=='),
'gameplay':(160,120,'eNrt2usOgjAMhuElrez+71hgw4GuaCSxXXwfcQz1x5eNcoikBGBwqsti9QLEWxk98o2eL7UovV6MgCe9CAFPexjaNE3kuxQw/AQzfowfAAAAgL+Q8/wm3wdB2rpkmtu8bQEAAAD41Q1CuQLnMhwXySpuvMMqZD5ZX3GHT0rIyNNLvu/Lt7Vdzg92PerXSKiPxitfHcF+QD2sPAvYzLdMr/plLCcP4xSiu8V1D7T3Pu98UqpXzOpQTY4RZbeY5eE3ftLm9119eB6f7SO01oSudxNF6/W228+yT77neLtIh2+dxu81Xv0slUz1DxTu2QCYbjPykQ/p9IoTwDDy1m7PD+XEg0QAAAAATHdJ0gen'),
'sword-gameplay':(160,120,'eNrt19sKwyAQRVFhivP/f9xmTLzU9KUIOcheTa0UhNMxGpsSdvd6HdfYk4oXhh759smXWijJeBFr6mkFvOkBAAAAAAAAAAAAAAAAAAAAkOD+eUf7x9jrAgAAAPY+NLtHs+js69dR2hcGXJmv/OCl9VPOtwMLuvGGD8l8Fi8h+dDqJpYu5a61VkcTypfnfDoBY27rBFstn1XPB8zf67evnz0/w1f5omzn9JpKvKjesIDLNi2zFXb1S3bWr95/IjvMdAcK7YJD/coaltqkx/VbL7VHSGrBTPWIUFfts/G8N32j8U/ptw3zlUG3I9/9EQbA'),
'map':(540,240,'eNrt3YFu2jAUBVAkQ/L/f9wCJRBKKGnsxM85RzSVtmnF5mK/aN7jcAAAAAAAAAAAAFrVv2V+ZEM2kA0AAKCQ7sw08CIaD1d4ykYnG7zeUm6XMI7fvHArhSPWqnEcLpTfVUItG8fRN4pXo12obJy3FNmwbryKxu2BdUM2rBuflhuX2xTZWCcb8UpR2VhvU1GLsqFPT4D1fzger19LTpm9/3Ovfnf+ry15Vh/KNeWbn9grNkOyIRuy0Ww2AAAAAAAAAACA2jllhGwgGwAAAAAAAAAAAHvmBBiygWwAAEBTfFY8U9F4uMJTNnxWPBNbyiHaZ8UXcjoZ6u9wSIZsTO0qlg2mq1HhwLqBdQPrBoWzYRKY3lSAD5T73OaAcyAOsiEbsiEbAADOIjIdjYcrPGXDWUQmtpSDs4hMhkMySjh+i7+rWDZKRGO4BK9GhaNINMKHw7pRKBvnLSV8NqwbRaJxe1g3aDMbXssS5cblNqWBTYUipWj8OxXUojetfdJzwTNe/b8dj9evYJMqGytkI+ikyoZsAAAAAAAAAAAAlOVYFbKBbAAAAAAQTAstNSkTjeHCqlKMaAjHFtFIAbLRQEvNmNkY1BuNBtomBozGw7ohGzwVG6nywqOVlpqB141qyw4tNTevN9SiVH6f8ldLzbxWHkhVx8w+eEaprnNw/apkI1LLStmQDQAAAAAAAAAAoDa7+BjttQeyypm38oOTDdmQDdkAAAAA4J19txZtcfTZenrsu7XoxOhT7GikjJOz23BMjD6FDke2xpT7buc0Mfr6236+i0auxpT7bh85MfoAbT/fFxt5GlPKxu/RR2j7+dG6kRbPzo5bi06MPkDbz4/qjTzF2I6z8Wr0Adp+rnSfohZt4j5lsjHlv04e5WktumQUmzXQ+6OxasryHNY9AZZ3SrfqEllRNoo+B9mQjTqyAQAAALBzp5OxYr5kAwAAAELz2cVbTkLuH5L375MN2ZAN2QBYKvD/x6NwNEbf2PkN6XM2UvDWMiPdWfOvY4FR9g/X+3qRrgFpY9Ierg1HI/8o+8vCMQpH3JYyk7PW7SIbmUd5SUV/GIWjuWx0t0vbW0rmUfbjx3Cbcr/Wak7bzu8Za7/cyD3Kn0T0h3E4hvuUetMxr2lpt+QNFWb17DIvG/1QiPaP2fhZOaqdl5lNS7sFVVqc+7Ulo5yRjduUVJyNOY2ilryj4rQCXWXdOFynod7JmNuYcsE7KlAr0ALrRn//Nt5jq642Zmbjv++oSK1AC6wbL7KRrncpqeJszGpauqCCD9QKNPd9ylS9MTxqLkXnFaNL640YxWjhbKT7ntJILbpE2um/Of7OxrX55U/3y5T6XF7+9AVmNy2dMSlvW4HW9fpt31+xwmwU7M8Y6MCjbMhGHdn4Alt8g9M='),
'player0':(12,16,'eNpVjgkOAEAEA5vM//+8oatB3KVItKjE3oFSOrfxe8rQzmUKODwmYYoQNYDX2CcHUqbyyX5rDqAHQ4AAtQ=='),
'player1':(12,16,'eNpVjocNADAIwyL5/58rSFmobHCRSFGIrR3xyNjKr6mHdiwj4HAMoZIGZQOv9cbg2KdwD9L8E+YBQpYArw=='),
'player2':(12,16,'eNpNjQkKAEEIwwL5/5+XtdRRwYuaAjjBH6lpTs5sNrpXdGeCcLUPMdcCijE/XsNir+2au6YWLx9DLAC1'),
'player3':(12,16,'eNpNjgEKADAIAg/8/5/HFKuC0igNQA5+pKbJaawwyrt0MZHQ7K6EpxWojHJzHBeeqeabfQeN3wNCYACv'),
'warder':(10,10,'eNpjYGBgAQIGEGCBERAuiAIhMMWCyoWxkAioFoQSCA3EABogAIk='),
'projectile':(2,2,'eNpjZWVlBQAANgAV'),
'sword':(14,9,'eNptjEEKAAAIgwT//+c61YK8yXCABB5tGzA2ZUOJzdM9nykFHIwAbQ=='),
'key':(7,12,'eNpjYAMBBjYGEAAyQCyQAJgDkwCzwFJgaew8qBFADAAlhgDH'),
'heart':(7,7,'eNpjYGFhACMsACLKwMAAIYE0EAMAD40AiQ=='),
'hudkey':(3,7,'eNpjYwMBBjYGBiQSAAPzAE8='),
'equipped':(21,16,'eNptj4EOACEIQtn4/3++SiufF645aYJIBV4QYLRDziLpoMFeMWMXfmGaxm7fRZvW8Ir1QxRZiYmcN7U8zvcL1GLuyc+Yo3+uGAES'),
}
RINGS={'gameplay':[[18.613,13.525,18.536,12.572],[64.258,42.949,15.988,13.642],[88.471,72.506,9.963,11.769],[118.824,74.914,8.573,9.362],[71.094,90.963,4.866,5.35]],'sword-gameplay':[[67.468,109.182,7.827,8.57],[92.17,109.182,8.805,8.57]]}
PALETTE=('#000','#00f','#0f0','#0ff','#f00','#f0f','#ff0','#fff')
LO={}
def read(k):
    w,h,b64=DATA[k]
    raw=zlib.decompress(base64.b64decode(b64,validate=True))
    assert len(raw)==w*h and max(raw)<=7,k
    return w,h,raw
def rect(x,y,w,h,fill):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
def label(x,y,en,ko,size=19,weight=500,anchor='start',color='#25364b'):
    LO.setdefault(en,ko)
    return f'<text x="{x}" y="{y}" font-family="Inter,Noto Sans KR,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{html.escape(en)}</text>'
def grid(k,x=0,y=0,scale=1,black=True):
    assert all(isinstance(v,int) for v in (x,y,scale)) and scale>0
    w,h,d=read(k)
    out=f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges" data-grid="{k}" data-grid-width="{w}" data-grid-height="{h}">'
    if black:out+=rect(0,0,w,h,'#000')
    # Merge equal horizontal runs only. Every coordinate remains an integer.
    # Group by RGB value without changing the recovered mask.
    paths=[[] for _ in PALETTE]
    check=bytearray(w*h)
    for iy in range(h):
        ix=0
        while ix<w:
            c=d[iy*w+ix];end=ix+1
            while end<w and d[iy*w+end]==c:end+=1
            if c:
                paths[c].append(f'M{ix} {iy}h{end-ix}v1h-{end-ix}z')
                check[iy*w+ix:iy*w+end]=bytes([c])*(end-ix)
            ix=end
    assert bytes(check)==d,k
    for c,commands in enumerate(paths):
        if commands:out+=f'<path fill="{PALETTE[c]}" d="{" ".join(commands)}"/>'
    return out+'</g>'
def rings(k,x=0,y=0,scale=1):
    out=f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="#f00" stroke-width="0.9" shape-rendering="geometricPrecision">'
    for cx,cy,rx,ry in RINGS[k]:out+=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>'
    return out+'</g>'
def write(slug,w,h,title,ko,content):
    LO.setdefault(title,ko)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}">'+content+'</svg>\n'
    p=DIR/(slug+'.svg');p.write_text(s,encoding='utf8');ET.parse(p)
def frame(title,ko,sub,ksub,w,h):
    return rect(0,0,w,h,'#fff')+f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12" fill="none" stroke="#d0dbe6"/>'+label(36,43,title,ko,27,700)+label(36,72,sub,ksub,16,color='#61758b')
def main():
    # Native logical size 540×240, shown at an integer multiple.
    write('escape-01-map-trace',1080,480,'Map reconstructed on the 540 × 240 grid','540 × 240 격자로 복원한 전체 맵',grid('map',scale=2))
    for name,slug,title,ko in [('gameplay','escape-09-gameplay-trace','Gameplay logical-grid reconstruction','플레이 화면 논리 픽셀 복원'),('sword-gameplay','escape-10-sword-gameplay-trace','Sword gameplay logical-grid reconstruction','검 장착 화면 논리 픽셀 복원')]:
        write(slug,640,480,title,ko,grid(name,scale=4)+rings(name,scale=4))
    # 3 x 160×120 screens, all shown at 2x, with identical logical aspect.
    b=frame('Start, failure and success screens','시작·실패·성공 화면','Recovered 160 × 120 grids · report pixel art','복원한 160 × 120 격자 · 보고서 픽셀 아트',1120,398)
    for x,k,en,ko in [(56,'start','START','시작'),(400,'failure','FAILURE','실패'),(744,'success','SUCCESS','성공')]:
        b+=label(x+160,111,en,ko,19,700,'middle')+grid(k,x,126,2)
    write('escape-11-screen-states',1120,398,'Start, failure and success screens','시작·실패·성공 화면',b)
    # Six report illustrations. Pixels are square and every sprite is at 7x.
    b=frame('Original sprite and HUD designs','원본 스프라이트와 HUD','Recovered logical cells · square pixels at 7×','복원한 논리 픽셀 · 정사각형 셀 7배 확대',1120,510)
    b+=label(56,113,'Player poses · 12 × 16 each','캐릭터 자세 · 각각 12 × 16',20,700)
    b+=rect(56,126,436,140,'#000')
    for i,x in enumerate([70,178,286,394]):b+=grid('player'+str(i),x,140,7,False)
    b+=label(552,113,'Warder and projectile','적과 포탄',20,700)
    b+=rect(552,126,512,140,'#000')+grid('warder',590,159,7,False)+grid('projectile',758,187,7,False)
    b+=label(625,245,'10 × 10','10 × 10',15,anchor='middle',color='#fff')+label(765,245,'2 × 2','2 × 2',15,anchor='middle',color='#fff')
    for x,w,en,ko in [(56,190,'Sword · 14 × 9','검 · 14 × 9'),(266,232,'Equipped sword','검 장착'),(518,144,'Key · 7 × 12','열쇠 · 7 × 12'),(682,382,'HUD · hearts and keys','HUD · 하트와 열쇠')]:
        b+=label(x,302,en,ko,18,700)+rect(x,316,w,154,'#000')
    b+=grid('sword',102,361,7,False)+grid('equipped',308,337,7,False)+grid('key',565,351,7,False)
    for x in [722,813,904]:b+=grid('heart',x,338,7,False)
    for x in [728,789,850,911,972]:b+=grid('hudkey',x,407,7,False)
    write('escape-12-sprite-traces',1120,510,'Original sprite and HUD designs','원본 스프라이트와 HUD',b)
    p=ROOT/'apps/web/i18n/svg-ko-overrides.json';d=json.loads(p.read_text())
    for k,v in LO.items():
        if k not in d:d[k]=v
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Validated',len(DATA),'recovered grids; generated five pixel-art SVGs')
if __name__=='__main__':main()
