"""FanRobot R2 interface trial. Dimensions in mm. Run with Python 3.11 + cadquery + trimesh."""
from pathlib import Path
import json, math
import cadquery as cq
import trimesh
R=Path(__file__).resolve().parent
# Fit parameters: trial values until measured on hardware.
W,L,H=84.,166.,36.
wall,floor=2.4,3.
gear_y,gear_z,gap=12.,10.,.25
fan_pitch,fan_bore=50.,56.  # 60 mm square guarded fan, measured holes override this
motor_y=-50.; idler_y=53.; axle_z=12.
wp=lambda: cq.Workplane('XY')
def box(w,l,h,x=0,y=0,z=0):return wp().box(w,l,h,centered=(True,True,False)).translate((x,y,z))
def rnd(w,l,h,r,z=0):return box(w,l,h,z=z).edges('|Z').fillet(r)
def cyl(d,h,x,y,z):return wp().circle(d/2).extrude(h).translate((x,y,z))
def side(d,h,x,y,z):return cyl(d,h,0,0,0).rotate((0,0,0),(0,1,0),90).translate((x,y,z))
def face(d,h,x,y,z):return cyl(d,h,0,0,0).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))
base=rnd(W,L,H,6).cut(rnd(W-2*wall,L-2*wall,H,6-wall,floor))
lid=rnd(W,L,3,6,H)
for x in [-W/2+6,W/2-6]:
 for y in [-L/2+6,L/2-6]:
  base=base.union(cyl(8,H,x,y,0)).cut(cyl(2.5,12,x,y,H-10));lid=lid.cut(cyl(3.4,6,x,y,H-1))
for x in [-27,27]:
 for y in [-22,22]:base=base.union(cyl(5.8,12,x,y,floor)).cut(cyl(2.1,9,x,y,floor+4))
# SMT faces the floor; KiCad top (x,y) maps to chassis (30-x,25-y).
base=base.cut(box(22,14,6,-4,0,-1)).cut(box(17,17,6,28,-13.5,-1)).cut(box(10,23,13,W/2,4,6))
for x in [-22,22]:base=base.cut(box(4,16,6,x,56,-1)) # battery strap
# Lid registers only along clear side walls, avoiding cover bosses.
for x in [-1,1]:lid=lid.union(box(2,65,2,x*(W/2-wall-.30-1),0,H-2))
# Inboard gearbox saddles, pressed by matching cap. Output shafts face outwards.
mx=W/2-wall-8
cap_z=axle_z+gear_z/2+gap
for s in [-1,1]:
 x=s*mx; wid=gear_y+2*gap
 base=base.union(box(16,wid+15,cap_z,x,motor_y)).cut(box(17,wid,25,x,motor_y,axle_z-gear_z/2-gap))
 for dy in [-(wid/2+3.8),wid/2+3.8]:base=base.cut(cyl(2.5,10,x,motor_y+dy,cap_z-9))
 base=base.union(box(5,20,axle_z+6,s*(W/2-2.5),idler_y))
 base=base.cut(side(7,8,s*W/2-4,motor_y,axle_z)); base=base.cut(box(12,12,3.5,s*W/2,idler_y,axle_z-1.75))
cap=box(16,gear_y+2*gap+15,3)
for s in [-1,1]:cap=cap.cut(cyl(3.4,5,0,s*((gear_y+2*gap)/2+3.8),-1))
# Front bracket with through-air opening, fixed to lid using a wide foot.
fy=-45;fz=H+3; center=fz+43; outer=max(fan_bore+10,fan_pitch+13)
mount=box(outer,4,outer,0,fy,center-outer/2).union(box(outer,18,4,0,fy+5,fz)).union(box(outer,4,center-outer/2-fz+1,0,fy,fz))
mount=mount.cut(face(fan_bore,8,0,fy-4,center))
for x in [-fan_pitch/2,fan_pitch/2]:
 for z in [center-fan_pitch/2,center+fan_pitch/2]:mount=mount.cut(face(3.6,8,x,fy-4,z))
for x in [-22,22]:
 mount=mount.cut(cyl(3.4,7,x,fy+10,fz-1));lid=lid.cut(cyl(3.4,6,x,fy+10,H-1))
# Separate inverted camera front holder; board slips between two side rails, strap only at PCB edge.
cam_y=-71; cam_w=24.6
cam=box(cam_w+8,12,3,0,cam_y+2,fz).union(box(cam_w+6,2.6,20,0,cam_y+2,fz))
for s in [-1,1]:
 cam=cam.union(box(2,5,19,s*(cam_w/2+1),cam_y,fz)).cut(box(2.8,8,4,s*(cam_w/2-2.6),cam_y+2,fz+13))
for x in [-9,9]:
 cam=cam.cut(cyl(3.3,8,x,cam_y+6,fz-1));lid=lid.cut(cyl(3.3,6,x,cam_y+6,H-1))
lid=lid.cut(box(27,8,6,0,cam_y+15,H-1)).cut(box(9,7,6,29,fy+10,H-1))
for y in [0,7,14,21]:lid=lid.cut(box(40,2.8,6,0,y,H-1))
# Coupon is an actual crop of the left drive mount (same holes, height and shaft exit).
coupon=base.intersect(box(21,32,cap_z+2,-W/2+10,motor_y))
parts={'01_chassis':base,'02_cover':lid,'03_fan_mount':mount,'04_camera_holder':cam,'05_motor_cap_print_2':cap,'T1_motor_fit':coupon,'T2_fan_hole_gauge':mount.intersect(box(outer,6,8,0,fy,center-fan_pitch/2-4))}
assembly=cq.Assembly(); placed=[]; report={}
for name,p in parts.items():
 shape=p.val(); assert shape.isValid() and len(p.solids().vals())==1,name
 if name[0]!='T':
  pieces=[p] if p is not cap else [p.translate((s*mx,motor_y,cap_z)) for s in [-1,1]]
  for i,q in enumerate(pieces):
   for n,old in placed:assert q.val().intersect(old.val()).Volume()<1e-5,(n,name)
   placed.append((name,q));assembly.add(q,name=name+'_'+str(i))
 # Print with largest useful flat face down.
 q=p
 if p is lid:q=p.rotate((0,0,0),(1,0,0),180)
 if p is mount or name.startswith('T2'):q=p.rotate((0,0,0),(1,0,0),90)
 b=q.val().BoundingBox(); q=q.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
 out=R/'STL';out.mkdir(exist_ok=True); f=out/(name+'.stl');cq.exporters.export(q,str(f),tolerance=.04,angularTolerance=.12)
 m=trimesh.load_mesh(f);assert m.is_volume and len(m.split())==1,name
 report[name]=[round(float(i),2) for i in m.extents]
# Analytical solids for fit only; not exported as printable components.
board=box(72,60,1.6,0,-5,15)
for xx in (-27,27):
 for yy in (-22,22):board=board.cut(cyl(2.7,3,xx,yy,14.5))
for nm,q in placed: assert q.val().intersect(board.val()).Volume()<1e-5,nm
assembly.export(str(R/'FanRobot-R2.step')); print(json.dumps(report,indent=2))

# Exploded view exported from the same B-reps (front points towards -Y).
preview=[]
for n,q in placed:
 dz={'01_chassis':0,'02_cover':32,'03_fan_mount':48,'04_camera_holder':48,'05_motor_cap_print_2':7}[n]
 preview.append(q.val().translate((0,0,dz)))
cq.exporters.export(cq.Compound.makeCompound(preview),str(R/'exploded.svg'),opt={'width':980,'height':780,'projectionDir':(-1,-1.45,1.05),'showHidden':False,'showAxes':False,'strokeWidth':0.55})

# Mechanical integration review: vertically flip the electrically populated board.
# KiCad STEP coordinates are x,-y; top of the substrate is the SMT datum.
ecad=cq.importers.importStep(str(R/'board-reference.step'))
substrate=max(ecad.solids().vals(),key=lambda p:p.Volume())
z=substrate.BoundingBox().zmax
ecad=ecad.rotate((0,0,0),(0,1,0),180).translate((30,25,15+z))
bb=ecad.val().BoundingBox()
intersections={}
for name,q in placed:
 intersections[name]=max(intersections.get(name,0),float(q.val().intersect(ecad.val()).Volume()))
result={'nominal_board_mm':[72,60,1.6],'mount_pitch_mm':[54,44],'substrate_side_wall_clearance_mm':3.6,'board_to_inner_floor_mm':12,'installed_model_z_extent_mm':[bb.zmin,bb.zmax],'clearance_volumes_mm3':intersections,'excluded':'Unmodelled packages, cables, screw heads, battery and track hardware. See README.'}
(R/'fit-check.json').write_text(json.dumps(result,indent=2)+'\n')
assembly.add(ecad,name='PCB_review_only',color=cq.Color(.15,.45,.31));assembly.export(str(R/'FanRobot-R2-with-board.step'))
assert max(intersections.values())<.001,intersections
