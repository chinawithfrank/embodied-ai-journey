"""Set two-layer widths; route ground too, without inner-plane assumptions."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'eda/fan_robot_mainboard.dsn';s=p.read_text()
assert '(layer In1.Cu' not in s and '(plane ' not in s
classes=[('MotorPower',['MOTOR_A1','MOTOR_A2','MOTOR_B1','MOTOR_B2','A_SENSE','B_SENSE'],450),('BatteryPath',['BAT_RAW','BAT_FUSED','BAT_PROTECTED','VBAT'],800),('LogicPower',['3V3','USB_VBUS','USB_LIMITED','VLOGIC_IN'],500),('FanPower',['FAN_5V','FAN_SW'],450),('GND_Return',['GND'],300)]
m=re.search(r'\(class kicad_default\s+([\s\S]*?)\(circuit',s);assert m
assigned={n for _,names,_ in classes for n in names}
s=s[:m.start(1)]+' '.join(n for n in m.group(1).split() if n not in assigned)+'\n      '+s[m.end(1):]
for name,names,width in classes:
 idx=s.index('\n  (wiring');pos=s.rfind('\n  )',0,idx)
 block='\n    (class '+name+' '+' '.join(names)+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width '+str(width)+')(clearance 150)))\n'
 s=s[:pos]+block+s[pos:]
(p.parent/'fan_robot_mainboard-routing.dsn').write_text(s)
print('Two signal layers; explicit ground and battery routing, no inner planes.')
