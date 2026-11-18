"""Independent Gerber/Excellon/stencil parse with gerbonara; validate exported geometry."""
from pathlib import Path
import json,hashlib,collections,warnings
from gerbonara import LayerStack,GerberFile
from gerbonara.excellon import ExcellonFile
ROOT=Path(__file__).resolve().parents[1];G=ROOT/'fabrication/gerber';errors=[]
def need(v,msg):
 if not v:errors.append(msg)
warnings.filterwarnings('ignore',message='.*G90 header statement.*')
s=LayerStack.open(G);layers=s.graphic_layers
want={('top','copper'),('bottom','copper'),('top','mask'),('bottom','mask'),('top','silk'),('bottom','silk'),('mechanical','outline')}
need(set(layers)==want,'Exactly2 copper+2mask+2silk+1outline layers')
outline=layers[('mechanical','outline')];edges=[(round(o.x1,6),round(o.y1,6),round(o.x2,6),round(o.y2,6)) for o in outline.objects]
need(len(edges)==4,'4 rectangle edges')
endpoints=collections.Counter((x,y) for a,b,c,d in edges for x,y in [(a,b),(c,d)])
need(set(endpoints)=={(0.,0.),(60.,0.),(60.,50.),(0.,50.)} and set(endpoints.values())=={2},'Closed60x50 outline centerlines and lower-left origin')
drills={}
expected_pth=json.loads((ROOT/'checks/data-consistency.json').read_text())['plated_drill_objects_expected']
for kind,plating,count in [('PTH','Plated',expected_pth),('NPTH','NonPlated',8)]:
 path=G/('fan_robot_mainboard-'+kind+'.drl');txt=path.read_text();need('METRIC' in txt and 'TF.FileFunction,'+plating+',1,2,'+kind in txt,kind+' explicit metric/plating metadata')
 f=ExcellonFile.open(path);need(len(f.objects)==count,kind+' hole/slot count');drills[kind]={'holes_and_slots':len(f.objects),'round_holes':sum(type(x).__name__=='Flash' for x in f.objects),'routed_slots':sum(type(x).__name__=='Line' for x in f.objects),'plating_header':plating}
 if kind=='NPTH':
  holes={(round(o.x,4),round(o.y,4)) for o in f.objects if abs(o.tool.diameter-2.7)<1e-6};need(holes=={(3.,3.),(57.,3.),(3.,47.),(57.,47.)},'NPTH2.7 hole positions')
need(drills['PTH']['routed_slots']==4,'4 plated USB shell slots')
# Stencil exactly corresponds to populated pads, not hand-entered component centers.
expected=json.loads((ROOT/'checks/expected-paste-centers.json').read_text());paste={}
for side,name in [('top','F_Paste.gtp'),('bottom','B_Paste.gbp')]:
 g=GerberFile.open(ROOT/'fabrication/stencil'/('fan_robot_mainboard-'+name));need(all(type(o).__name__=='Flash' for o in g.objects),side+' aperture types')
 coords={(round(o.x,6),round(o.y,6)) for o in g.objects};e={tuple(v) for v in expected[side]};need(coords==e,side+' paste centers match actual populated PCB pads including thermal apertures; DNP absent');paste[side]={'flashes':len(g.objects),'unique_centers':len(coords),'expected_unique_centers':len(e),'extra':list(coords-e),'missing':list(e-coords)}
# SHA binds output verification to this exact PCB, netlist and placement/BOM files.
files=[ROOT/'eda/fan_robot_mainboard.kicad_pcb',ROOT/'eda/fan_robot_mainboard.xml',ROOT/'assembly/CPL_JLC.csv',ROOT/'assembly/BOM_JLC_SMT.csv',ROOT/'assembly/BOM_JLC_THT.csv']
summary={'status':'PASS' if not errors else 'FAIL','independent_parser':'gerbonara','layers':{'/'.join(k):len(v.objects) for k,v in layers.items()},'outline_centerline_dimensions_mm':[60,50],'manufacturing_origin':'lower-left,common for Gerber,drill andCPL','drills':drills,'stencil':paste,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'errors':errors,'scope':'File/data validation only; no physical prototype or factory DFM response. Standard KiCad G90-header placement accepted; explicit native plating metadata used rather than parser plating inference.'}
(ROOT/'checks/manufacturing-audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert not errors,errors
