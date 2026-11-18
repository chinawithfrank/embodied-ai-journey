"""Create readable native assembly views from the actual routed board (no electrical edits)."""
from pathlib import Path
import pcbnew as k,subprocess,os,json,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';APP=Path(os.environ.get('FAN_KICAD_APP',Path.home()/'.local/share/fanrobot-eda/KiCad.app'));CLI=APP/'Contents/MacOS/kicad-cli'
b=k.LoadBoard(str(EDA/'fan_robot_mainboard.kicad_pcb'));mm=k.FromMM
# Fabrication-layer duplicate ${REFERENCE} labels are hidden only in this plot copy.
for f in b.GetFootprints():
 ref=f.GetReference()
 for g in f.GraphicalItems():
  if hasattr(g,'GetText') and hasattr(g,'SetVisible'):g.SetVisible(False)
 f.Reference().SetTextSize(k.VECTOR2I(mm(.6),mm(.6)));f.Reference().SetTextThickness(mm(.1));f.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T))
 f.Reference().SetPosition(f.GetPosition());f.Reference().SetVisible(not ref.startswith('H'))
 if ref in ['J1','J2','J3','J4']:f.Reference().SetPosition(f.GetPosition()+k.VECTOR2I(mm(1 if ref!='J1' else 0),mm(1.9)))
 if ref=='J5':f.Reference().SetPosition(k.VECTOR2I(mm(36),mm(45.27)))
 if ref=='J6':f.Reference().SetPosition(k.VECTOR2I(mm(3),mm(21)))
 if ref=='J7':f.Reference().SetPosition(k.VECTOR2I(mm(31.8),mm(33)))
 if ref=='J8':f.Reference().SetPosition(k.VECTOR2I(mm(31.8),mm(39)))
path=Path('/tmp/fanrobot-assembly-copy.kicad_pcb');k.SaveBoard(str(path),b)
# KiCad plots user text on Fab even if hidden; remove only duplicate reference primitives in the disposable copy.
s=path.read_text();spans=[]
for match in re.finditer(r'\(fp_text user "\$\{REFERENCE\}"',s):
 depth=0;quoted=False;escaped=False
 for j in range(match.start(),len(s)):
  c=s[j]
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':depth+=1
  elif c==')':
   depth-=1
   if depth==0:spans.append((match.start(),j+1));break
for a,z in reversed(spans):s=s[:a]+s[z:]
path.write_text(s)
for side,layer,mirror in [('top','F.Fab',False),('bottom','B.Fab',True)]:
 out=ROOT/'assembly/drawings'/('assembly-'+side+'.svg')
 cmd=[str(CLI),'pcb','export','svg',str(path),'-o',str(out),'--layers',layer+',Edge.Cuts','--mode-single','--page-size-mode','2','--exclude-drawing-sheet','--black-and-white','--crossout-DNP-footprints-on-fab-layers']
 if mirror:cmd+=['--mirror']
 subprocess.run(cmd,check=True,stderr=open('/tmp/fanrobot-assembly-warnings.log','w'))
# Assembly register has exact pin1 coordinates/nets and native orientation for every installed part.
d=json.loads((ROOT/'design/circuit.json').read_text());parts={p['ref']:p for p in d['parts']};rows=[]
for f in b.GetFootprints():
 if f.GetReference() not in parts:continue
 p=parts[f.GetReference()]
 pads=[pad for pad in f.Pads() if pad.GetNumber()=='1'];pad=pads[0] if pads else None
 rows.append({'ref':p['ref'],'mpn':p['mpn'],'assembly':p['assembly'],'side':'Bottom' if f.GetLayer()==k.B_Cu else 'Top','anchor_mm':[k.ToMM(f.GetPosition().x),50-k.ToMM(f.GetPosition().y)],'rotation_degrees':f.GetOrientationDegrees(),'pin1_mm':[k.ToMM(pad.GetPosition().x),50-k.ToMM(pad.GetPosition().y)] if pad else None,'pin1_net':pad.GetNetname() if pad else None})
(ROOT/'assembly/orientation-register.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Actual top/bottom assembly drawings and orientation register exported.')
