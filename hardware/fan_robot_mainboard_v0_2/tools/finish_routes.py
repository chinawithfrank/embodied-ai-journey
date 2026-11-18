"""Finish reviewed residual connections with clearance-checked local A* paths."""
from pathlib import Path
import os,sys,math,heapq,itertools,json
sys.path.append(os.environ.get('FAN_EDA_SITE','/tmp/fanrobot-eda-venv/lib/python3.9/site-packages'))
import pcbnew as k
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.prepared import prep
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'eda/fan_robot_mainboard.kicad_pcb'
b=k.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()};mm=k.FromMM

def pos(ref,n):return next((k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)) for p in fps[ref].Pads() if p.GetNumber()==str(n))
def xy(p):return k.VECTOR2I(mm(p[0]),mm(p[1]))
def obstacles(net,layer):
 out=[box(6,0,54,6.05)]
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==net:continue
   if not p.IsOnLayer(layer):continue
   r=p.GetBoundingBox();out.append(box(k.ToMM(r.GetX()),k.ToMM(r.GetY()),k.ToMM(r.GetRight()),k.ToMM(r.GetBottom())))
 for t in b.GetTracks():
  if t.GetNetname()==net:continue
  w=k.ToMM(t.GetWidth(layer)) if isinstance(t,k.PCB_VIA) else k.ToMM(t.GetWidth())
  if isinstance(t,k.PCB_VIA):out.append(Point(k.ToMM(t.GetPosition().x),k.ToMM(t.GetPosition().y)).buffer(w/2))
  elif t.GetLayer()==layer:out.append(LineString([(k.ToMM(t.GetStart().x),k.ToMM(t.GetStart().y)),(k.ToMM(t.GetEnd().x),k.ToMM(t.GetEnd().y))]).buffer(w/2))
 return unary_union(out)

def route(net,points,width,layer):
 for a,c in zip(points,points[1:]):
  if math.dist(a,c)<1e-5:continue
  t=k.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)

def astar(net,a,c,width,layer,step=.15):
 geom=obstacles(net,layer);expanded=geom.buffer(width/2+.17)
 prepared=prep(expanded)
 def node(p):return (round(p[0]/step),round(p[1]/step))
 def point(n):return (round(n[0]*step,6),round(n[1]*step,6))
 src=node(a);dst=node(c);endpoints={src,dst}
 def free(n):
  x,y=point(n)
  return .5<x<59.5 and 6.3<y<49.5 and (n in endpoints or not prepared.intersects(Point(x,y)))
 seq=itertools.count();queue=[(0,next(seq),src)];cost={src:0};parent={};closed=set()
 moves=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
 while queue:
  _,_,v=heapq.heappop(queue)
  if v in closed:continue
  if v==dst:break
  closed.add(v)
  for dx,dy in moves:
   n=(v[0]+dx,v[1]+dy)
   if n in closed or not free(n):continue
   # Require every copper segment, not just grid points, to be clear.
   seg=LineString([point(v),point(n)])
   if seg.distance(geom)<width/2+.155:continue
   g=cost[v]+math.hypot(dx,dy)
   if g<cost.get(n,float('inf')):
    cost[n]=g;parent[n]=v;heapq.heappush(queue,(g+math.dist(n,dst),next(seq),n))
 else:raise RuntimeError('No clearance-safe path '+net)
 pathnodes=[dst]
 while pathnodes[-1]!=src:pathnodes.append(parent[pathnodes[-1]])
 points=[a]+[point(n) for n in reversed(pathnodes)]+[c]
 # Reduce collinear vertices and verify exact endpoint joins.
 cleaned=[points[0]]
 for p in points[1:]:
  if math.dist(cleaned[-1],p)>1e-6:cleaned.append(p)
 simplified=[cleaned[0]]
 for i in range(1,len(cleaned)-1):
  u=cleaned[i-1];v=cleaned[i];w=cleaned[i+1]
  if abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))>1e-7:simplified.append(v)
 simplified.append(cleaned[-1])
 assert all(LineString([u,v]).distance(geom)>=width/2+.15-1e-6 for u,v in zip(simplified,simplified[1:])),net
 route(net,simplified,width,layer)
 return {'net':net,'layer':b.GetLayerName(layer),'width_mm':width,'length_mm':sum(math.dist(u,v) for u,v in zip(simplified,simplified[1:])),'vertices':len(simplified)}

# Short0.20mm fanout reaches a free via, then0.45mm inner-layer motor routing.
v=(41.5,19.2);net='MOTOR_A2';a=pos('U4',4)
for layer in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]:assert Point(v).distance(obstacles(net,layer))>=.3+.15-1e-6,(net,layer)
summary=[astar(net,a,v,.2,k.F_Cu,.05)]
via=k.PCB_VIA(b);via.SetPosition(xy(v));via.SetWidth(mm(.6));via.SetDrill(mm(.3));via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(nets[net]);via.SetLocked(True);b.Add(via)
summary.append(astar(net,v,pos('J2',2),.45,k.In2_Cu))
# Prefer a local top-layer bridge; otherwise use the existing supply vias on the back.
try:summary.append(astar('VBAT',pos('C7',1),pos('L2',1),.65,k.F_Cu,.1))
except RuntimeError:
 vv=[(k.ToMM(t.GetPosition().x),k.ToMM(t.GetPosition().y)) for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='VBAT']
 p1=min(vv,key=lambda v:math.dist(v,pos('C7',1)));p2=min(vv,key=lambda v:math.dist(v,pos('L2',1)))
 summary.append(astar('VBAT',p1,p2,.8,k.B_Cu,.1))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):
  t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();k.SaveBoard(str(path),b)
(ROOT/'checks/finished-routes.json').write_text(json.dumps(summary,indent=2)+'\n')
print(summary)
