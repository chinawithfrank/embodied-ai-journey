"""1L engineering layout, never exports a manufacturing ZIP. Use KiCad 10 Python."""
from pathlib import Path
import pcbnew as k, re,sys
root=Path(__file__).resolve().parent
src=root.parent/'fan_robot_mainboard_v0_3/eda'
dst=root/'eda/fan_robot_mainboard.kicad_pcb'
b=k.LoadBoard(str(src/dst.name)); mm=k.FromMM
xy=lambda x,y:k.VECTOR2I(mm(x),mm(y))
def rect(r):return tuple(k.ToMM(n) for n in [r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()])
def hull(f):
 r=f.GetCourtyard(f.GetLayer()).BBox()
 return rect(r if r.GetWidth()>0 else f.GetBoundingBox(False,False))
def overlap(a,b,margin):return a[2]+margin>b[0] and b[2]+margin>a[0] and a[3]+margin>b[1] and b[3]+margin>a[1]
for z in list(b.Zones()):b.Delete(z)
# Keep only short verified front-side switching paths, not arbitrary stubs.
locked={'SW1_L1','SW2_L1','FAN_BOOST_SW','FAN_FB','FB_3V3','A_SENSE','B_SENSE'}
for t in list(b.GetTracks()):
 if isinstance(t,k.PCB_VIA) or t.GetLayer()!=k.F_Cu or not t.IsLocked() or t.GetNetname() not in locked:b.Delete(t)
fps=sorted(b.GetFootprints(),key=lambda f:f.GetReference());fixed=[];jobs=[]
for f in fps:
 ref=f.GetReference()
 if ref=='U1':
  for p in list(f.Pads()):
   if p.GetNumber()=='41' and p.GetDrillSize().x:f.Delete(p)
 if ref in ('J7','J8','C1','F1','Q2','Q3','C24','C23','C20','U8','D3') and f.GetLayer()==k.F_Cu and ref not in ('J7','J8'):
  jobs.append(f);continue
 if ref.startswith('R') and ref[1:].isdigit() and ref not in {'R2','R3','R7','R8','R24','R25'} and f.GetLayer()==k.F_Cu:
  jobs.append(f);continue
 if f.GetLayer()==k.B_Cu:
  f.Flip(f.GetPosition(),False);jobs.append(f);continue
 if ref in ('J1','J2','J3','J4','J5','J7','J8'):
  # Populate through connectors on the opposite face; mirror across the inline pin axis.
  pads=[p for p in f.Pads() if p.GetNumber() in ('1','2')];old=[p.GetPosition() for p in pads]
  f.Flip(f.GetPosition(),False)
  if (pads[1].GetPosition()-pads[0].GetPosition())!=(old[1]-old[0]):f.Rotate(f.GetPosition(),k.EDA_ANGLE(180,k.DEGREES_T))
  f.Move(old[0]-pads[0].GetPosition())
  if ref=='J5':f.Move(xy(20.32,0))
 fixed.append(hull(f) if ref!='U1' else (20.2,0,39.8,26.3))
for f in sorted(jobs,key=lambda f:(f.GetReference()!='SW1',f.GetReference().startswith('TP'),-(hull(f)[2]-hull(f)[0])*(hull(f)[3]-hull(f)[1]))):
 best=None
 for turn in (0,90):
  if turn:f.Rotate(f.GetPosition(),k.EDA_ANGLE(90,k.DEGREES_T))
  r=hull(f);p=f.GetPosition();ox,oy=k.ToMM(p.x),k.ToMM(p.y);off=[r[0]-ox,r[1]-oy,r[2]-ox,r[3]-oy]
  candidates=sorted(((x/2,y/2) for x in range(1,120) for y in range(1,100)),key=lambda t:(t[0]-ox)**2+(t[1]-oy)**2)
  for x,y in candidates:
   q=(x+off[0],y+off[1],x+off[2],y+off[3])
   if q[0]<.25 or q[1]<.25 or q[2]>59.75 or q[3]>49.75 or overlap(q,(6,0,54,6),.1) or any(overlap(q,g,.06) for g in fixed):continue
   score=(x-ox)**2+(y-oy)**2+turn/360
   if best is None or best[0]>score:best=(score,x,y,q,f.GetOrientationDegrees())
   break
 if best is None:raise ValueError(f.GetReference())
 _,x,y,q,ang=best;f.SetOrientationDegrees(ang);f.SetPosition(xy(x,y));fixed.append(q)
for d in b.GetDrawings():
 if isinstance(d,k.PCB_TEXT):
  if 'V0.3' in d.GetText():d.SetText('1L DRAFT');d.SetPosition(xy(30,3))
  else:d.SetLayer(k.Cmts_User)
# Native KiCad uses a F/B stack: prohibit all back-side routing and all vias.
def area(layer,points,keepout):
 z=k.ZONE(b);z.SetLayer(layer)
 if keepout:
  z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
 else:
  z.SetNet(b.FindNet('GND'));z.SetLocalClearance(mm(.20));z.SetMinThickness(mm(.20));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
 z.Outline().NewOutline()
 for x,y in points:z.Outline().Append(mm(x),mm(y))
 b.Add(z)
area(k.B_Cu,[(0,0),(60,0),(60,50),(0,50)],True)
area(k.F_Cu,[(.3,6.3),(59.7,6.3),(59.7,49.7),(.3,49.7)],False)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(dst),b)
if len(sys.argv)>1:
 d=Path(sys.argv[1]);k.ExportSpecctraDSN(b,str(d))
 s=re.sub(r'^    \(plane GND .*?\n','',d.read_text(),flags=re.M)
 # Retain the virtual second layer for the importer; back is blocked by full-board keepout.
 cls=(src/'fan_robot_mainboard-routing.dsn').read_text();classes=cls[cls.index('    (class kicad_default'):cls.index('\n  (wiring')];s=re.sub(r'    \(class kicad_default.*?(?=\n  \(wiring)',lambda _:classes,s,flags=re.S)
 d.write_text(s)
