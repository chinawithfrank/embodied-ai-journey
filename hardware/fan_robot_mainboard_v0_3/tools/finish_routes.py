"""Add two-side GND copper and clearance-checked stitching after explicit routing."""
from pathlib import Path
import os,sys,json
sys.path.append(os.environ.get('FAN_EDA_SITE','/tmp/fanrobot-eda-venv/lib/python3.9/site-packages'))
import pcbnew as k
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'eda/fan_robot_mainboard.kicad_pcb'
b=k.LoadBoard(str(path));assert b.GetCopperLayerCount()==2
mm=k.FromMM;xy=lambda x,y:k.VECTOR2I(mm(x),mm(y))
net=next(n for n in b.GetNetsByNetcode().values() if n.GetNetname()=='GND')
for z in list(b.Zones()):b.Remove(z)
zones=[]
for layer in [k.F_Cu,k.B_Cu]:
 z=k.ZONE(b);z.SetLayer(layer);z.SetNet(net);z.SetLocalClearance(mm(.2));z.SetMinThickness(mm(.2));z.SetPadConnection(k.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(.3,6.3),(59.7,6.3),(59.7,49.7),(.3,49.7)]:poly.Append(mm(x),mm(y))
 b.Add(z);zones.append(z)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones())
# Stitch only where both existing fills have ground. Keep drills outside SMD
# lands and apply conservative via-to-copper and hole-to-hole clearance.
obstacles=[]
for f in b.GetFootprints():
 for p in f.Pads():
  r=p.GetBoundingBox();g=box(k.ToMM(r.GetX()),k.ToMM(r.GetY()),k.ToMM(r.GetRight()),k.ToMM(r.GetBottom()))
  if p.GetNetname()!='GND':obstacles.append(g.buffer(.46))
  if p.GetAttribute()==k.PAD_ATTRIB_SMD:obstacles.append(g.buffer(.27))
  elif p.GetDrillSize().x:obstacles.append(Point(k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)).buffer(k.ToMM(p.GetDrillSize().x)/2+.56))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):obstacles.append(Point(k.ToMM(t.GetPosition().x),k.ToMM(t.GetPosition().y)).buffer(k.ToMM(t.GetWidth(k.F_Cu))/2+.56))
 elif t.GetNetname()!='GND':obstacles.append(LineString([(k.ToMM(t.GetStart().x),k.ToMM(t.GetStart().y)),(k.ToMM(t.GetEnd().x),k.ToMM(t.GetEnd().y))]).buffer(k.ToMM(t.GetWidth())/2+.46))
blocked=unary_union(obstacles);added=[]
for yi in range(8,49,4):
 for xi in range(2,59,4):
  if blocked.intersects(Point(xi,yi)):continue
  if not all(z.HitTestFilledArea(layer,xy(xi,yi)) for z,layer in zip(zones,[k.F_Cu,k.B_Cu])):continue
  v=k.PCB_VIA(b);v.SetPosition(xy(xi,yi));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(net);b.Add(v);added.append([xi,yi])
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();k.SaveBoard(str(path),b)
(ROOT/'checks/finished-routes.json').write_text(json.dumps({'copper_layers':2,'gnd_pours':2,'stitching_vias_added':added},indent=2)+'\n')
print('Two-side GND filled; stitching vias:',len(added))
