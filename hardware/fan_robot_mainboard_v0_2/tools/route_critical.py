"""Route local switching/USB loops and provide short returns to dedicated planes."""
from pathlib import Path
import sys,math,json,os
sys.path.append(os.environ.get('FAN_EDA_SITE','/tmp/fanrobot-eda-venv/lib/python3.9/site-packages'))
import pcbnew as k
from shapely.geometry import Point,LineString,box
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';path=EDA/'fan_robot_mainboard.kicad_pcb'
b=k.LoadBoard(str(path));mm=k.FromMM
fps={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
# Preserve native schematic single-pad NC nets for schematic/PCB parity.
import xml.etree.ElementTree as ET
for net in ET.parse(EDA/'fan_robot_mainboard.xml').findall('./nets/net'):
 name=net.attrib['name']
 if name.startswith('unconnected-'):
  ni=k.NETINFO_ITEM(b,name);b.Add(ni);nets[name]=ni
  for nd in net.findall('node'):
   ref=nd.attrib['ref'];no=nd.attrib['pin']
   for pp in fps[ref].Pads():
    if pp.GetNumber()==no:pp.SetNet(ni)

def xy(p):return k.VECTOR2I(mm(p[0]),mm(p[1]))
def pt(p):return (k.ToMM(p.x),k.ToMM(p.y))
def pad(ref,no):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(no))
def pos(ref,no):return pt(pad(ref,no).GetPosition())
tracks=[];vias=[]
def route(net,points,width=.25,layer=k.F_Cu):
 for a,c in zip(points,points[1:]):
  if math.dist(a,c)<.00001:continue
  t=k.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t);tracks.append((net,layer,LineString([a,c]),width))
def join(ra,na,rb,nb,width=.25,middle=(),layer=k.F_Cu):
 net=pad(ra,na).GetNetname();assert net==pad(rb,nb).GetNetname(),(ra,rb)
 route(net,[pos(ra,na),*middle,pos(rb,nb)],width,layer)
def via(net,p,dia=.6,drill=.3):
 v=k.PCB_VIA(b);v.SetPosition(xy(p));v.SetWidth(mm(dia));v.SetDrill(mm(drill));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[net]);v.SetLocked(True);b.Add(v);vias.append((net,p,dia))
# TPS63802 local hot loops, feedback sampled directly at its output capacitor.
join('U2',9,'L1',1,.3,[(10.5,9.4),(10.2,9.1)])
join('U2',7,'L1',2,.3,[(11.5,9.4),(11.8,9.1)])
join('U2',10,'C2',1,.3)
join('U2',6,'C3',1,.3)
join('C3',1,'C4',1,.65,[(13.55,12.0),(14.05,12.5)])
join('R2',2,'R3',1,.2,[(12.5,13.675),(10.5,13.675)])
join('U2',4,'R2',2,.2,[(11.5,13.675)])
join('R2',1,'C4',1,.25,[(13.2,15.325),(14.05,14.475)])
join('U2',8,'U2',3,.3)
join('U2',2,'U2',3,.2)
via('GND',(9.4,11.9));route('GND',[pos('U2',8),(11,11.7),(9.4,11.7),(9.4,11.9)],.25)
# MCU supply is fed past the local capacitors, not around them.
join('C11',1,'U1',2,.65,[(20,8.5),(20.26,8.76)])
# Fan boost hot loop and feedback. Keep FB away from SW.
route('FAN_BOOST_SW',[pos('L2',2),(44.185,37),(45.3,37)],.5)
route('FAN_BOOST_SW',[(45.3,37),pos('U3',5)],.3)
join('U3',6,'C8',1,.3,[(46.2875,38.6),(46.75,39.0625)])
join('R7',2,'R8',1,.2,[(44.725,40.8)])
join('U3',1,'R7',2,.2,[(48.5,37.5),(49.8,38.8),(49.8,42.1),(45.175,42.1)])
join('C8',1,'R7',1,.25)
# USB connector D+/D- reversal contacts are both connected; one short DM layer crossing.
via('USB_DM_CONN',(9.2,21.4));via('USB_DM_CONN',(9.5,19))
route('USB_DM_CONN',[pos('J6','A7'),(8.85,21.25),(9,21.4),(9.2,21.4)],.25)
route('USB_DM_CONN',[(9.2,21.4),(9.2,19.3),(9.5,19)],.25,k.B_Cu)
route('USB_DM_CONN',[(9.5,19),(10.05,19.55),(10.55,20.05),pos('U5',1)],.25)
route('USB_DM_CONN',[pos('J6','B7'),(8.75,20.25),(8.95,20.05),pos('U5',1)],.25)
route('USB_DP_CONN',[pos('J6','A6'),(9.4,20.75),(9.825,21.175),(9.825,21.7),(10.075,21.95),pos('U5',3)],.25)
route('USB_DP_CONN',[pos('J6','B6'),(8.7,21.75),(8.95,22),(10.2,22),(10.25,21.95),pos('U5',3)],.25)
join('U5',6,'R24',1,.25);join('U5',4,'R25',1,.25)
via('USB_VBUS',(10.3,18.8));via('USB_VBUS',(14.3,21))
route('USB_VBUS',[pos('J6','A4'),(8.7,18.55),(8.95,18.3),(10.3,18.3),(10.3,18.8)],.45)
route('USB_VBUS',[(10.3,18.8),(14.3,21)],.45,k.B_Cu)
route('USB_VBUS',[(14.3,21),pos('U5',5)],.45)
route('USB_DM_MCU',[pos('R24',2),(16.8,20),(18.8,22),(19.7,22),(20.43,22.73),pos('U1',13)],.25)
route('USB_DP_MCU',[pos('R25',2),(16.8,22),(17.2,22.4),(19.3,22.4),(19.3,23.27),(20.03,24),pos('U1',14)],.25)
# DRV8833 exposed copper uses vias outside its paste window, not unfilled via-in-paste.
for dx in [-1.35,1.35]:
 for dy in [-1.8,1.8]:via('GND',(47+dx,19.8+dy),.6,.3)
# Direct supply plane transitions; power transistor receives multiple larger vias.
for p in [(16.1,37),(16.1,38)]:via('VBAT',p,.8,.4)
route('VBAT',[pos('Q3',3),(15.6,37.5),(16.1,37)],.65)
route('VBAT',[(15.6,37.5),(16.1,38)],.65)
via('GND',(45.3,35.7));route('GND',[pos('U3',4),(45.8,36.5),(45.3,36),(45.3,35.7)],.25)
via('VBAT',(48.5,36.5));route('VBAT',[pos('U3',3),(48.5,36.5)],.25)
# Build geometry for short plane-return stubs. Rectangular pad bounds are conservative.
padboxes=[]
for f in b.GetFootprints():
 for p in f.Pads():
  if not (p.IsOnLayer(k.F_Cu) or p.IsOnLayer(k.B_Cu)):continue
  r=p.GetBoundingBox();g=box(k.ToMM(r.GetX()),k.ToMM(r.GetY()),k.ToMM(r.GetRight()),k.ToMM(r.GetBottom()))
  padboxes.append((p,p.GetNetname(),g,[L for L in [k.F_Cu,k.B_Cu] if p.IsOnLayer(L)],p.GetAttribute()==k.PAD_ATTRIB_PTH))
via_fail=[]
def free_trace(net,a,c,width,layer):
 
 if math.dist(a,c)<1e-5:return True
 ls=LineString([a,c]);margin=width/2+.155
 for _,other,g,layers,_ in padboxes:
  if other!=net and layer in layers and ls.distance(g)<margin-1e-5:return False
 for other,l,g,w in tracks:
  if other!=net and l==layer and ls.distance(g)<(width+w)/2+.155-1e-5:return False
 for other,p,d in vias:
  if other!=net and ls.distance(Point(p))<(d+width)/2+.155:return False
 return True
def free_via(net,p,d=.6):
 x,y=p
 if x<d/2+.35 or x>59.65-d/2 or y<d/2+.35 or y>49.65-d/2:return False
 if 6<=x<=54 and y-d/2<6.05:return False
 for _,other,g,_,pth in padboxes:
  dist=Point(p).distance(g)
  if other!=net and dist<d/2+.155:return False
  if not pth and dist<.26:return False # keep drilled holes out of exposed SMD lands
  if pth and dist<.55:return False
 for other,_,g,w in tracks:
  if other!=net and g.distance(Point(p))<(d+w)/2+.155:return False
 for _,v,vd in vias:
  if math.dist(p,v)<(d+vd)/2+.25:return False
 return True
# GND/PWR vias: shortest safe straight or L-shaped route; small stubs never replace motor wires.
for f in b.GetFootprints():
 ref=f.GetReference()
 for p in f.Pads():
  n=p.GetNumber();net=p.GetNetname()
  if net not in ['GND','VBAT'] or p.GetAttribute()!=k.PAD_ATTRIB_SMD:continue
  if (ref=='U3' and n in ['3','4']) or (ref=='U2' and n in ['2','3','8']) or (ref=='U4' and n=='17') or (ref=='Q3' and n=='3'):continue
  # Repeated SMD ground lands already share explicit through-hole pad41 within module.
  if ref=='U1' and n=='41':continue
  a=pt(p.GetPosition());layer=k.F_Cu if p.IsOnLayer(k.F_Cu) else k.B_Cu;width=.3 if net=='GND' else .45
  done=False
  for radius in [.8,1.0,1.2,1.5,1.8,2.2,2.7,3.3,4.0]:
   if done:break
   for angle in range(0,360,30):
    c=(round(a[0]+radius*math.cos(math.radians(angle)),4),round(a[1]+radius*math.sin(math.radians(angle)),4))
    if not free_via(net,c):continue
    choices=[[a,c],[a,(c[0],a[1]),c],[a,(a[0],c[1]),c]]
    for points in choices:
     if all(free_trace(net,u,v,width,layer) for u,v in zip(points,points[1:])):
      route(net,points,width,layer);via(net,c);done=True;break
    if done:break
  if not done:via_fail.append((ref,n,net))
# Inner layers are dedicated planes; outer layers carry signals and local power loops.
for layer,net in [(k.In1_Cu,'GND'),(k.In2_Cu,'VBAT')]:
 z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets[net]);z.SetLocalClearance(mm(.2));z.SetMinThickness(mm(.15));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(.3,.3),(59.7,.3),(59.7,49.7),(.3,49.7)]:poly.Append(mm(x),mm(y))
 b.Add(z)
# Header grounds use thermal reliefs for solderability; vias and local bypass returns remain solid.
for f in b.GetFootprints():
 if f.GetReference().startswith('J'):
  for p in f.Pads():
   if p.GetAttribute()==k.PAD_ATTRIB_PTH:p.SetLocalZoneConnection(k.ZONE_CONNECTION_THERMAL)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();k.SaveBoard(str(path),b)
(ROOT/'checks/plane-via-review.json').write_text(json.dumps({'unresolved_direct_plane_stubs':via_fail,'through_vias_added':len(vias),'critical_segments':len(tracks)},indent=2)+'\n')
print('Critical routing and plane transitions created; unresolved direct plane stubs:',via_fail)
# Preserve a clear EDA stage before the general router, never present it as a finished board.
k.SaveBoard(str(EDA/'critical-routed.kicad_pcb'),b)
k.ExportSpecctraDSN(b,str(EDA/'fan_robot_mainboard.dsn'))
