"""Export stencil from exact PCB geometry with DNP paste openings removed."""
from pathlib import Path
import pcbnew as k,subprocess,os
ROOT=Path(__file__).resolve().parents[1];APP=Path(os.environ.get('FAN_KICAD_APP',Path.home()/'.local/share/fanrobot-eda/KiCad.app'))
b=k.LoadBoard(str(ROOT/'eda/fan_robot_mainboard.kicad_pcb'))
for f in b.GetFootprints():
 if f.IsDNP():
  for p in f.Pads():
   layers=p.GetLayerSet();layers.RemoveLayer(k.F_Paste);layers.RemoveLayer(k.B_Paste);p.SetLayerSet(layers)
tmp=Path('/tmp/fanrobot-stencil');tmp.mkdir(exist_ok=True);path=tmp/'fan_robot_mainboard.kicad_pcb';k.SaveBoard(str(path),b)
subprocess.run([str(APP/'Contents/MacOS/kicad-cli'),'pcb','export','gerbers',str(path),'--output',str(ROOT/'fabrication/stencil')+'/','--layers','F.Paste,B.Paste','--precision','6','--use-drill-file-origin'],check=True,stderr=open('/tmp/fanrobot-stencil-warnings.log','w'))
print('DNP pads omitted from stencil only; electrical PCB untouched.')
