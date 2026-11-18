"""Export genuine KiCad manufacturing data; never synthesize placement coordinates."""
from pathlib import Path
import os,subprocess,csv,json,collections
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';PCB=EDA/'fan_robot_mainboard.kicad_pcb';SCH=EDA/'fan_robot_mainboard.kicad_sch'
CLI=Path(os.environ.get('FAN_KICAD_APP',Path.home()/'.local/share/fanrobot-eda/KiCad.app'))/'Contents/MacOS/kicad-cli'
for dr in ['fabrication/gerber','fabrication/stencil','assembly/drawings']: (ROOT/dr).mkdir(parents=True,exist_ok=True)
log=open('/tmp/fanrobot-export-stderr.log','w')
def run(*args):subprocess.run([str(CLI),*map(str,args)],check=True,stderr=log)
run('sch','export','netlist',SCH,'--format','kicadxml','--output',EDA/'fan_robot_mainboard.xml')
run('sch','export','netlist',SCH,'--format','kicadsexpr','--output',EDA/'fan_robot_mainboard.net')
run('sch','export','pdf',SCH,'--output',ROOT/'assembly/drawings/schematic.pdf')
run('pcb','export','gerbers',PCB,'--output',str(ROOT/'fabrication/gerber')+'/','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--precision','6','--use-drill-file-origin','--check-zones')
subprocess.run([str(CLI.parents[1]/'Frameworks/Python.framework/Versions/3.9/bin/python3'),str(ROOT/'tools/export_stencil.py')],check=True,stderr=log)
run('pcb','export','drill',PCB,'--output',str(ROOT/'fabrication/gerber')+'/','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-oval-format','route','--excellon-separate-th','--generate-report','--report-path',ROOT/'checks/drill-report.txt','--generate-map','--map-format','svg')
run('pcb','export','pos',PCB,'--format','csv','--units','mm','--side','both','--use-drill-file-origin','--smd-only','--exclude-dnp','--output',ROOT/'assembly/positions-native.csv')
run('pcb','export','ipcd356',PCB,'--output',ROOT/'fabrication/fan_robot_mainboard.ipc')
# Actual native coordinates are authoritative. No bottom-X negation and no guessed JLC rotation offsets.
with (ROOT/'assembly/positions-native.csv').open() as f:positions=list(csv.DictReader(f))
print('Native position columns:',list(positions[0]));print('Native SMT count:',len(positions))
d=json.loads((ROOT/'design/circuit.json').read_text());parts=d['parts']
def write(name,rows,fields=None):
 with (ROOT/'assembly'/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
rows=[dict(Reference=p['ref'],Value=p['value'],Manufacturer=p['manufacturer'],MPN=p['mpn'],LCSC=p['lcsc'],Footprint=p['footprint'],Assembly=p['assembly'],Quantity=0 if p['assembly'] in ['DNP','PCB_ONLY'] else 1,Notes=p['note']) for p in parts]
write('BOM_FULL.csv',rows)
groups=collections.defaultdict(list)
for p in parts:
 if p['assembly'] in ['SMT','THT']:groups[(p['mpn'],p['lcsc'],p['assembly'],p['footprint'])].append(p)
for asm in ['SMT','THT']:
 grouped=[]
 for (mpn,code,kind,fp),ps in groups.items():
  if kind!=asm:continue
  grouped.append({'Comment':mpn,'Designator':','.join(p['ref'] for p in ps),'Footprint':fp.split(':')[1],'LCSC Part #':code,'Quantity':len(ps)})
 write('BOM_JLC_'+asm+'.csv',grouped)
write('DNP.csv',[{'Designator':p['ref'],'Value':p['value'],'Reason':p['note']} for p in parts if p['dnp']])
write('CPL_JLC.csv',[{'Designator':p['Ref'],'Mid X':p['PosX']+'mm','Mid Y':p['PosY']+'mm','Layer':'Top' if p['Side']=='top' else 'Bottom','Rotation':str(float(p['Rot'])%360)} for p in positions])
# Board silk and copper plots permit independent visual review of generated native geometry.
for side,layers,mirror in [('top','F.Cu,F.SilkS,Edge.Cuts',False),('bottom','B.Cu,B.SilkS,Edge.Cuts',True)]:
 args=['pcb','export','svg',PCB,'--output',ROOT/'assembly/drawings'/('routing-'+side+'.svg'),'--layers',layers,'--mode-single','--page-size-mode','2','--exclude-drawing-sheet']
 if mirror:args+=['--mirror']
 run(*args)
print('Gerber, drills, stencil, schematic, full/SMT/THT BOM and native/JLC CPL exported.')
