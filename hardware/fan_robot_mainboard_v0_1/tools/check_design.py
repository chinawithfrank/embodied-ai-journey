# -*- coding: utf-8 -*-
"""Internal data-consistency checks, NOT ERC/DRC or an electrical safety proof."""
from pathlib import Path
import csv, json, xml.etree.ElementTree as ET
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'design/circuit.json').read_text());parts=data['parts'];by={p['ref']:p for p in parts};passed=[]
def check(ok,name):
    if not ok:raise AssertionError(name)
    passed.append('PASS: '+name)
def net(ref,pin):return by[ref]['pins'][str(pin)]['net']
check(len(by)==len(parts),'All component references unique')
check(data['release']=='NOT_FOR_FABRICATION','Review-only release state present')
check([net('U1',i) for i in [1,40,41]]==['GND']*3,'All ESP32 module ground pads connected')
check(all(net('U1',i) is None for i in [28,29,30]),'Octal PSRAM pins GPIO35/36/37 left NC')
check([net('U1',i) for i in [39,38,31,32]]==['M_AIN1','M_AIN2','M_BIN1','M_BIN2'],'Existing motor GPIO mapping preserved')
check(net('U1',33)=='FAN_CMD' and net('U1',24)=='ACT_REQ','GPIO40 fan and GPIO47 enable are distinct')
check(net('U4',1)=='ACT_EN' and net('U3',2)=='ACT_EN','Motor sleep and fan boost share hardware interlock')
check([net('U6',i) for i in [1,2,4]]==['ACT_REQ','ESP_EN','ACT_EN'],'Enable AND gate inputs/output agree with circuit')
check([net('U7',i) for i in [1,2,4]]==['FAN_CMD','ACT_EN','FAN_GATE_LOGIC'],'Fan AND gate inputs/output agree with circuit')
for reset in [0,1]:
    for fan in [0,1]:
        act=0 & reset;fanout=fan & act
        check(act==0 and fanout==0,f'Logic-only default-disable truth row EN={reset}, FAN_CMD={fan}')
check([net('Q1',i) for i in [1,2,3]]==['FAN_GATE','GND','FAN_SW'],'Fan NMOS is low-side, not shorting supply')
check(net('J4',1)=='FAN_5V' and net('J4',2)=='FAN_SW','Fan red/black remain on correct connector nets')
check(net('D1',1)=='FAN_5V' and net('D1',2)=='FAN_SW','Fan clamp diode cathode faces positive supply')
check([net('Q2',i) for i in [1,2,3]]==['REVERSE_GATE','VBAT','BAT_FUSED'],'Reverse-input PMOS has source on protected rail')
check(net('D2',1)==net('D3',1)=='VLOGIC_IN' and net('D2',2)=='VBAT' and net('D3',2)=='USB_VBUS','Logic OR diode polarity excludes intended USB-to-battery conduction')
check(net('U4',12)=='VBAT' and net('U3',3)=='VBAT','Actuator supplies do not use the USB logic OR net')
check(net('C18',1)=='DRV_VCP' and net('C18',2)=='VBAT','DRV8833 charge-pump capacitor is between VCP and VM')
check(net('C19',1)=='DRV_VINT' and net('C19',2)=='GND','DRV8833 VINT bypass does not feed other loads')
check([net('U4',i) for i in [2,4,7,5]]==['MOTOR_A1','MOTOR_A2','MOTOR_B1','MOTOR_B2'],'DRV8833 PWP outputs use correct pin order')
check(net('U4',13)==net('U4',17)=='GND','DRV8833 ground and exposed thermal pad connected')
check(abs(.5*(1+560/100)-3.3)<1e-9,'3.3V divider arithmetic')
check(4.5<.595*(1+732/100)<5.5,'Nominal fan voltage arithmetic lies within series voltage window')
check(.45<.2/.39<.6,'Provisional current-limit arithmetic only, NOT validated motor setting')
check(4.95*330/(1000+330)<1.3,'Battery ADC divider nominal full-fresh value below 1.3V')
check(net('J5',18) is None and net('J5',2)=='3V3','Camera FLASH NC and camera supply 3.3V')
xml=ET.parse(ROOT/'eda/fan_robot_mainboard.net').getroot()
check({c.attrib['ref'] for c in xml.findall('./components/comp')}==set(by),'XML netlist reference set equals JSON')
expected=Counter((p['ref'],num,pin['net']) for p in parts for num,pin in p['pins'].items() if pin['net'])
observed=Counter((node.attrib['ref'],node.attrib['pin'],n.attrib['name']) for n in xml.findall('./nets/net') for node in n.findall('node'))
check(expected==observed,'Every populated physical pin/net exported exactly once')
with (ROOT/'assembly/BOM_REVIEW_ONLY.csv').open(encoding='utf-8-sig') as f:bom=list(csv.DictReader(f))
check({p['Reference'] for p in bom}==set(by),'BOM references equal schematic data references')
check(all(not p['LCSC_SKU'] for p in bom),'No invented LCSC ordering codes')
check(all(not (ROOT/'eda'/f'{p["ref"]}.kicad_pcb').exists() for p in parts),'No placeholder PCB presented as routed output')
for filename in ['fan_robot_mainboard','power','mcu_camera','actuators','usb_expansion']:
 s=(ROOT/'eda'/f'{filename}.sch').read_text()
 check(s.startswith('EESchema Schematic File Version 4') and s.endswith('$EndSCHEMATC\n'),f'Legacy file framing {filename}; NOT a KiCad parse check')
# Declared release gates, not silently waived failures.
report='FAN ROBOT V0.1 INTERNAL CONSISTENCY CHECK\nNOT ERC / NOT DRC / NOT DFM / NOT PROTOTYPE VALIDATION\n\n'+'\n'.join(passed)+'\n\nOPEN RELEASE BLOCKERS:\n- No routed PCB, Gerber, drill or CPL\n- Legacy KiCad schematic not imported/checked in KiCad\n- All component footprints and LCSC inventory remain unfrozen\n- Camera 2x9 pitch/row 2.54mm USER CONFIRMED; socket MPN/mating view/height unreleased; photo sensor identity conflict needs PID check\n- N20 6V/60rpm USER CONFIRMED; stall/start current and sense resistor not qualified\n- Fuse and power inductors need exact rated MPNs\n- USB current, power sequencing, converter stability and RF/layout unverified\n- New-board firmware has not been ported or flashed\n'
(ROOT/'checks/consistency-report.txt').write_text(report)
print(f'{len(passed)} internal consistency checks PASS; manufacturing release remains BLOCKED.')
