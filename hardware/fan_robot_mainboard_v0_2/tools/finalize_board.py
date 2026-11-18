"""Idempotent final metadata, C1 land update, functional silk and nominal stackup."""
from pathlib import Path
import pcbnew as k,json,re
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';path=EDA/'fan_robot_mainboard.kicad_pcb'
d=json.loads((ROOT/'design/circuit.json').read_text());b=k.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};mm=k.FromMM
xy=lambda x,y:k.VECTOR2I(mm(x),mm(y))
for part in d['parts']:
 f=fps[part['ref']];f.SetValue(part['value']);f.SetDNP(part['dnp'])
 for key,val in [('MPN',part['mpn']),('LCSC',part['lcsc']),('Datasheet',part.get('source',''))]:
  f.SetField(key,val);field=f.GetField(key);field.SetVisible(False);field.SetLayer(k.B_Fab if f.GetLayer()==k.B_Cu else k.F_Fab);field.SetPosition(f.GetPosition())
# Same copper dimensions; shift C1 pad centers0.1mm outwards to match C6 recommended land.
f=fps['C1'];f.SetPosition(xy(20.6,32));f.SetFPID(k.LIB_ID('FanRobot','CP_OSCON_C6_6.3x5.9'));f.SetLibDescription('Panasonic OS-CON C6,6.3x5.9mm,land a2.1 b9.1 c1.6')
for p in f.Pads():
 p.SetPosition(xy(20.6+(-2.8 if p.GetNumber()=='1' else 2.8),32));p.SetSize(xy(3.5,1.6))
# Remove borrowed Nichicon height model, no fabricated 3D model supplied.
f.Models().clear()
for t in b.GetDrawings():
 if isinstance(t,k.PCB_TEXT) and t.GetText()=='3xAA':t.SetText('3x1.5V');t.SetPosition(xy(9,48.8))
labels=[('LEFT',55,6.6,k.F_SilkS),('RIGHT',55,22.2,k.F_SilkS),('FAN',55,30.9,k.F_SilkS),('+',52.3,34,k.F_SilkS),('SW-',58.5,34,k.F_SilkS),('BAT+',4,43.3,k.F_SilkS),('GND',4,36.3,k.F_SilkS),('CAM 1=GND',34,42.1,k.F_SilkS),('1',24.3,44,k.F_SilkS),('C1+',16.3,30,k.F_SilkS),('USB',4,26.8,k.F_SilkS),('POWER',10.4,31.5,k.B_SilkS),('ON',7.4,35.7,k.B_SilkS),('OFF',7.5,27.2,k.B_SilkS),('RESET',30,24.2,k.B_SilkS),('BOOT',37.5,24.2,k.B_SilkS)]
existing={(t.GetText(),t.GetLayer()) for t in b.GetDrawings() if isinstance(t,k.PCB_TEXT)}
for s,x,y,layer in labels:
 if (s,layer) in existing:
  t=next(t for t in b.GetDrawings() if isinstance(t,k.PCB_TEXT) and t.GetText()==s and t.GetLayer()==layer);t.SetPosition(xy(x,y));t.SetTextSize(xy(.8,.8));continue
 t=k.PCB_TEXT(b);t.SetText(s);t.SetPosition(xy(x,y));t.SetTextSize(xy(.8,.8));t.SetTextThickness(mm(.1));t.SetLayer(layer);t.SetMirrored(layer==k.B_SilkS);b.Add(t)
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();k.SaveBoard(str(path),b)
# Explicit nominal four-layer stackup. Factory must confirm available production stackup.
s=path.read_text()
if '(stackup' not in s:
 stack='''(stackup
(layer "F.SilkS" (type "Top Silk Screen"))
(layer "F.Paste" (type "Top Solder Paste"))
(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
(layer "F.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
(layer "In1.Cu" (type "copper") (thickness 0.0175))
(layer "dielectric 2" (type "core") (thickness 1.095) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
(layer "In2.Cu" (type "copper") (thickness 0.0175))
(layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
(layer "B.Cu" (type "copper") (thickness 0.035))
(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
(layer "B.Paste" (type "Bottom Solder Paste"))
(layer "B.SilkS" (type "Bottom Silk Screen"))
(copper_finish "ENIG") (dielectric_constraints yes))'''
 s=s.replace('(setup','(setup\n'+stack,1);path.write_text(s)
 b=k.LoadBoard(str(path));k.SaveBoard(str(path),b)
coords={}
for ref,f in fps.items():
 if ref.startswith('H'):continue
 for p in f.Pads():
  if p.GetNumber():coords.setdefault(ref,{})[p.GetNumber()]=[round(k.ToMM(p.GetPosition().x),4),round(k.ToMM(p.GetPosition().y),4),p.GetNetname()]
(ROOT/'design/placed-pad-coordinates.json').write_text(json.dumps(coords,indent=2)+'\n')
print('Fields, C6 lands, functional labels and nominal1.6mm stackup finalized.')
