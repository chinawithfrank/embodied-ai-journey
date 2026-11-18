"""Cross-check actual PCB, native schematic, populated BOM/CPL and manufacturing layers."""
from pathlib import Path
import sys,os,json,csv,math,xml.etree.ElementTree as E,collections
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';b=k.LoadBoard(str(EDA/'fan_robot_mainboard.kicad_pcb'));d=json.loads((ROOT/'design/circuit.json').read_text());parts={p['ref']:p for p in d['parts']};fps={f.GetReference():f for f in b.GetFootprints()};errors=[]
def need(v,msg):
 if not v:errors.append(msg)
def read(name):return list(csv.DictReader((ROOT/'assembly'/name).open(encoding='utf-8-sig')))
# XML and JSON provide independent serializations of schematic connectivity.
x=E.parse(EDA/'fan_robot_mainboard.xml').getroot();actual=set()
for net in x.findall('./nets/net'):
 name=net.attrib['name']
 if name.startswith('unconnected-'):continue
 for nd in net.findall('node'):
  if not nd.attrib['ref'].startswith('#'):actual.add((nd.attrib['ref'],nd.attrib['pin'],name))
expected={(p['ref'],n,pin['net']) for p in parts.values() for n,pin in p['pins'].items() if pin['net']}
need(actual==expected,'Canonical vs native schematic connected pin/net mismatch')
for ref,p in parts.items():
 f=fps[ref];need(f.GetValue()==p['value'],ref+' value');need(f.GetFPIDAsString()==p['footprint'],ref+' footprint');need(f.IsDNP()==p['dnp'],ref+' DNP')
 for key,val in [('MPN',p['mpn']),('LCSC',p['lcsc']),('Datasheet',p.get('source',''))]:need(f.GetField(key).GetText()==val,ref+' '+key)
 for pad in f.Pads():
  no=pad.GetNumber()
  if not no:continue
  need(no in p['pins'],ref+' unknown pad '+no)
  want=p['pins'][no]['net'];net=pad.GetNetname()
  need(net==want if want else not net or net.startswith('unconnected-'),ref+'.'+no+' net '+net)
need(b.GetCopperLayerCount()==2,'Exactly two copper layers')
need(all(t.GetLayer() in [k.F_Cu,k.B_Cu] for t in b.GetTracks()),'No inner-layer tracks or vias')
need(all(z.GetLayer() in [k.F_Cu,k.B_Cu] for z in b.Zones()),'No inner-layer pours')
# Edge centerlines are the nominal dimensions; stroke width excluded.
pts=[]
for a in b.GetDrawings():
 if isinstance(a,k.PCB_SHAPE) and a.GetLayer()==k.Edge_Cuts:pts += [a.GetStart(),a.GetEnd()]
size=[k.ToMM(max(p.x for p in pts)-min(p.x for p in pts)),k.ToMM(max(p.y for p in pts)-min(p.y for p in pts))]
need(size==[60.,50.],'Outline60x50')
smts={p['ref'] for p in parts.values() if p['assembly']=='SMT'};tht={p['ref'] for p in parts.values() if p['assembly']=='THT'}
positions=read('positions-native.csv');cpl=read('CPL_JLC.csv');need({p['Ref'] for p in positions}==smts,'Native positions vs SMT refs');need({p['Designator'] for p in cpl}==smts,'CPL vs SMT refs')
need(len(positions)==len(smts) and len(cpl)==len(smts),'Duplicate CPL ref')
for p in positions:
 f=fps[p['Ref']];need(abs(float(p['PosX'])-k.ToMM(f.GetPosition().x))<1e-5,p['Ref']+' X');need(abs(float(p['PosY'])-(50-k.ToMM(f.GetPosition().y)))<1e-5,p['Ref']+' Y');need(p['Side']==('bottom' if f.GetLayer()==k.B_Cu else 'top'),p['Ref']+' side');need(abs(float(p['Rot'])-f.GetOrientationDegrees())<1e-5,p['Ref']+' rotation')
cp={p['Designator']:p for p in cpl}
for p in positions:
 q=cp[p['Ref']];need(float(q['Mid X'][:-2])==float(p['PosX']) and float(q['Mid Y'][:-2])==float(p['PosY']),p['Ref']+' JLC xy');need(float(q['Rotation'])==float(p['Rot'])%360,p['Ref']+' JLC rotation');need(q['Layer']==('Bottom' if p['Side']=='bottom' else 'Top'),p['Ref']+' JLC side')
for asm,refs in [('SMT',smts),('THT',tht)]:
 bom=read('BOM_JLC_'+asm+'.csv');listed=[ref for row in bom for ref in row['Designator'].split(',')];need(set(listed)==refs and len(listed)==len(refs),'BOM '+asm+' refs')
 for row in bom:
  for ref in row['Designator'].split(','):need(parts[ref]['lcsc']==row['LCSC Part #'] and parts[ref]['mpn']==row['Comment'],ref+' BOM MPN/C-code')
# Paste aperture centers expected from actual footprints, omitting DNP. Include unnamed paste-only thermal pads.
paste={}
for side,layer in [('top',k.F_Paste),('bottom',k.B_Paste)]:
 paste[side]=sorted({(round(k.ToMM(p.GetPosition().x),6),round(50-k.ToMM(p.GetPosition().y),6)) for f in b.GetFootprints() if not f.IsDNP() for p in f.Pads() if p.IsOnLayer(layer)})
(ROOT/'checks/expected-paste-centers.json').write_text(json.dumps(paste,indent=2)+'\n')
# Full pin-number/coordinate evidence for service and assembly.
summary={'status':'PASS' if not errors else 'FAIL','pcb_dimensions_mm':size,'copper_layers':2,'electrical_refs':len(parts),'smt_installed':len(smts),'tht_installed':len(tht),'dnp':[p['ref'] for p in parts.values() if p['dnp']],'pcb_testpads':sum(p['assembly']=='PCB_ONLY' for p in parts.values()),'connected_schematic_pin_net_tuples':len(expected),'plated_drill_objects_expected':sum(p.GetAttribute()==k.PAD_ATTRIB_PTH for f in b.GetFootprints() for p in f.Pads())+sum(isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'tracks':sum(not isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'cpl_origin':'lower-left (0,50mm in KiCad board coordinates); +X right,+Y up; bottom X not negated','errors':errors,'physical_validation':'Not yet fabricated or electrically tested; engineering prototype only'}
(ROOT/'checks/data-consistency.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert not errors,errors
