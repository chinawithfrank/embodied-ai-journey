# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape
root=Path(__file__).resolve().parents[1]
def text(x,y,value,cls=''):
 return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="middle">{escape(value)}</text>'
def area(x,y,w,h,label):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" class="part"/>'+text(x+w/2,y+h/2+5,label)
s='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 390" role="img" aria-label="60乘50毫米主板分区草案，未布线，接口与孔位未冻结"><title>主板结构分区草案，非PCB生产布局</title><style>
text{font:14px system-ui,-apple-system,"PingFang SC",sans-serif;fill:var(--foreground,#21313d)}
.board{fill:var(--card,#f2f7fa);stroke:var(--foreground,#21313d);stroke-width:1.2}
.part{fill:var(--muted,#e5edf4);stroke:var(--border,#9bafbd);stroke-width:1}
.dim{fill:none;stroke:var(--muted-foreground,#6c8090);stroke-width:1}
.title{font-weight:500}.small{font-size:13px}
</style>'''
s+=text(200,23,'60 × 50mm · 结构分区草案','title')
s+='<rect x="50" y="65" width="300" height="250" rx="7" class="board"/>'
s+='<path d="M50 58 V40 H350 V58 M358 65 H375 V315 H358" class="dim"/>'
s+=text(200,38,'60mm')+text(376,197,'50', 'small')
for x,y in [(65,80),(335,80),(65,300),(335,300)]:s+=f'<circle cx="{x}" cy="{y}" r="5.5" class="dim"/>'
s+=area(155,65,90,128,'ESP32-S3')
s+='<rect x="155" y="65" width="90" height="30" fill="var(--warning-surface,#ffefcd)" stroke="var(--warning,#c49b38)" stroke-dasharray="4 3"/>'
s+=text(200,86,'ANT')
s+=area(50,145,40,50,'USB')+area(100,200,60,25,'OR')
s+=area(75,235,65,40,'3.3V')+area(155,230,100,30,'CAM 2×9')
s+=area(260,130,55,55,'DRV')+area(320,105,30,30,'L')+area(320,150,30,30,'R')
s+=area(260,220,55,50,'5V')+area(320,245,30,25,'F')
s+=area(75,290,60,25,'BAT')+area(145,290,40,25,'SW')+area(200,290,60,25,'I2C')+area(270,290,45,25,'DBG')
s+=text(200,346,'ANT 天线禁布区 · L/R 履带 · F 风扇','small')
s+=text(200,369,'未布线；元件、接口和孔位均待实际布板确认。','small')+'</svg>'
(root/'design/placement-concept.svg').write_text(s)
