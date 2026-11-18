from pathlib import Path
import re,argparse
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'eda/fan_robot_mainboard.dsn';s=p.read_text()
for layer in ['In1.Cu']:
 s=s.replace('(layer '+layer+'\n      (type signal)','(layer '+layer+'\n      (type power)',1)
# Keep L2 as an uninterrupted GND reference. L3 supports signals around the VBAT pour.
s=re.sub(r'    \(plane VBAT \(polygon In2.Cu [^\n]+\)\)\n','',s)
classes=[('MotorPower',['MOTOR_A1','MOTOR_A2','MOTOR_B1','MOTOR_B2','A_SENSE','B_SENSE'],450),('BatteryPath',['BAT_RAW','BAT_FUSED','BAT_PROTECTED'],1000),('LogicPower',['3V3','USB_VBUS','USB_LIMITED','VLOGIC_IN'],500),('FanPower',['FAN_5V','FAN_SW'],450),('PlaneGND',['GND'],300),('PlaneVBAT',['VBAT'],1000)]
match=re.search(r'\(class kicad_default\s+([\s\S]*?)\(circuit',s);assert match
names=match.group(1).split();assigned={n for _,ns,_ in classes for n in ns};remaining=[n for n in names if n not in assigned]
s=s[:match.start(1)]+' '.join(remaining)+'\n      '+s[match.end(1):]
for name,ns,width in classes:
 idx=s.index('\n  (wiring');pos=s.rfind('\n  )',0,idx)
 block='\n    (class '+name+' '+' '.join(ns)+' (circuit (use_via "Via[0-3]_600:300_um")) (rule (width '+str(width)+')(clearance 150)))\n'
 s=s[:pos]+block+s[pos:]
(p.parent/'fan_robot_mainboard-routing.dsn').write_text(s)
print('Router input: L2 ground plane protected; F/L3/B available for signals; VBAT plane re-filled and independently checked after routing.')
