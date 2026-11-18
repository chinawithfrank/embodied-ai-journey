"""Dimension drawing from nominal board edge, actual NPTH coordinates and connector anchors."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1];p=json.loads((r/'design/placed-pad-coordinates.json').read_text())
a=['''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1000" viewBox="0 0 1100 1000"><rect width="1100" height="1000" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#152b3c} .d{fill:none;stroke:#456;stroke-width:1.4} .l{font-size:16px} .s{font-size:14px}</style><text x="65" y="58" font-size="29" font-weight="bold">FanRobot V0.3 | Mechanical &amp; connector datum</text><text x="65" y="90" class="l">Engineering prototype / all dimensions mm / top view / not a 1:1 print template</text>''']
x0,y0,sc=230,205,10
# Board outline and nominal antenna keepout are based on actual layout.
a.append(f'<rect x="{x0}" y="{y0}" width="600" height="500" fill="#f4f8fa" stroke="#152b3c" stroke-width="2"/><rect x="{x0+60}" y="{y0}" width="480" height="60" fill="#fcebdc"/>')
a.append('<text x="355" y="240" class="l">ALL-LAYER ANTENNA COPPER KEEPOUT</text>')
for x,y in [(3,3),(57,3),(3,47),(57,47)]:
 px=x0+x*sc;py=y0+y*sc;a.append(f'<circle cx="{px}" cy="{py}" r="13.5" fill="white" stroke="#203848" stroke-width="1.5"/><path d="M{px-20},{py}h40 M{px},{py-20}v40" class="d"/>')
# Datum identifies the physical lower left used for production exports.
a.append(f'<path d="M{x0},{y0+500}h50 M{x0},{y0+500}v-50" stroke="#c45130" stroke-width="3"/><text x="70" y="731" class="l">CPL (0,0)</text>')
labels={'J1':('BATTERY 1=+',-143,25),'J2':('LEFT MOTOR',-135,8),'J3':('RIGHT MOTOR',-145,8),'J4':('FAN 1=5V',-120,8),'J5':('CAMERA 1=GND',35,-10),'J6':('USB-C',10,-15),'J7':('I2C DNP',0,-20),'J8':('UART DNP',0,-20)}
# Pin1 exact centers, not a fabricated connector body outline.
for ref,(label,dx,dy) in labels.items():
 x,y,_=p[ref]['A1' if ref=='J6' else '1'];px=x0+x*sc;py=y0+y*sc
 a.append(f'<rect x="{px-5}" y="{py-5}" width="10" height="10" fill="#1d7191"/><text x="{px+dx}" y="{py+dy}" class="l">{ref} {label}</text>')
# Camera second row and pitch/longitudinal span as actual pads.
for n,coords in p['J5'].items():
 x,y,_=coords;a.append(f'<circle cx="{x0+x*sc}" cy="{y0+y*sc}" r="3.4" fill="#1d7191"/>')
# Main board and mounting-center dimensions.
for x1,y1,x2,y2,text,tx,ty in [(230,156,830,156,'60.00',501,145),(180,205,180,705,'50.00',110,462),(260,757,800,757,'54.00 hole centers',435,784),(886,235,886,675,'44.00',905,460)]:
 a.append(f'<path d="M{x1},{y1}L{x2},{y2}" class="d"/><text x="{tx}" y="{ty}" class="l">{text}</text>')
 for x,y in [(x1,y1),(x2,y2)]:a.append(f'<path d="M{x-6},{y-6}l12,12" class="d"/>')
a += ['''<text x="65" y="842" class="l">4 x Ø2.70 NPTH / M2.5 insulated hardware / centers 3.00mm from adjacent edges</text><text x="65" y="873" class="l">J5: 2 x 9, pitch &amp; row gap 2.54; longitudinal center span 20.32; pad1 = GND</text><text x="65" y="904" class="l">1.6 nominal 2-layer PCB; bottom components/buttons require ≥5mm standoff clearance review</text><text x="65" y="935" class="s">External camera/motor/fan enclosure fit and connector engagement require physical integration checks.</text><text x="65" y="960" class="s">Manufacturing holes: use Excellon files. Component orientation: use assembly views and orientation register.</text></svg>''']
(r/'assembly/drawings/mechanical-dimensions.svg').write_text(''.join(a))
