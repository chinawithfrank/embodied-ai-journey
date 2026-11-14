# -*- coding: utf-8 -*-
"""Generate review-only electrical sources; never generate manufacturing Gerbers."""
from pathlib import Path
import csv, json, math, xml.etree.ElementTree as ET
from collections import defaultdict
ROOT = Path(__file__).resolve().parents[1]
hardware_inputs=json.loads((ROOT/'design/hardware-inputs.json').read_text())
parts=[]
def add(ref,value,package,pins,section,mpn='',manufacturer='',note='',status='CANDIDATE_VERIFY'):
    # pins is ordered: physical pin number -> (pin name, global net or None)
    parts.append(dict(ref=ref,value=value,package=package,pins={str(k):dict(name=v[0],net=v[1]) for k,v in pins.items()},section=section,mpn=mpn,manufacturer=manufacturer,note=note,status=status))
def two(ref,value,a,b,section,package='0603',mpn='',note='',status='CANDIDATE_VERIFY'):
    add(ref,value,package,{1:('1',a),2:('2',b)},section,mpn=mpn,note=note,status=status)
def cap(ref,value,a,b,section,package='0805',note='X7R/X5R; verify DC-bias derating and exact MPN'):
    two(ref,value,a,b,section,package,note=note)
def resistor(ref,value,a,b,section,package='0603',note='1%; exact manufacturer and LCSC SKU not frozen'):
    two(ref,value,a,b,section,package,note=note)
def conn(ref,value,nets,section,note='',package='TBD_MEASURE'):
    add(ref,value,package,{i+1:(name,net) for i,(name,net) in enumerate(nets)},section,note=note,status='MECHANICAL_CONFIRM_REQUIRED')
# Power: battery-only actuator rails. USB can power logic through diode OR, never charge cells.
conn('J1','3xAA_INPUT',[('BAT+','BAT_RAW'),('BAT-','GND')],'power',package='JST-XH-2.50_2P_CANDIDATE',note='Polarity/keying and 3A connector derating must be checked')
two('SW1','MASTER_POWER','BAT_RAW','BAT_SWITCHED','power',package='SW_SPST_TBD',note='Switch battery feed before all converters; location/ratings TBD',status='MECHANICAL_CONFIRM_REQUIRED')
two('F1','FUSE_TBD','BAT_SWITCHED','BAT_FUSED','power',package='TBD',note='Select after two-motor stall/inrush and cell capability measurements',status='BLOCKED_VALUE')
add('Q2','AO3401A','SOT-23',{1:('G','REVERSE_GATE'),2:('S','VBAT'),3:('D','BAT_FUSED')},'power',mpn='AO3401A',manufacturer='Alpha & Omega Semiconductor',note='Reverse-input protection: drain=input, source=protected rail; NOT a controlled load switch')
resistor('R1','100k','REVERSE_GATE','GND','power')
cap('C1','220uF_10V','VBAT','GND','power','SMD_ELECTROLYTIC_TBD',note='Positive=VBAT; validate transient/ripple and reverse protection response')
for ref,a in [('D2','VBAT'),('D3','USB_VBUS')]:
 add(ref,'SS34','SMA',{1:('K','VLOGIC_IN'),2:('A',a)},'power',mpn='SS34',note='Diode OR; exact vendor/If/Vf/Ir/temp selection pending. No USB-to-battery path.')
add('U2','TPS63802DLAR','DLA_10_VSON_HR',{1:('EN','LOGIC_UVLO'),2:('MODE','GND'),3:('AGND','GND'),4:('FB','FB_3V3'),5:('PG','ESP_EN'),6:('VOUT','3V3'),7:('L2','LOGIC_L2'),8:('GND','GND'),9:('L1','LOGIC_L1'),10:('VIN','VLOGIC_IN')},'power',mpn='TPS63802DLAR',manufacturer='Texas Instruments',note='3.3V buck-boost; power-save mode. Layout/effective capacitance/inductor validation required.')
two('L1','0.47uH','LOGIC_L1','LOGIC_L2','power','SHIELDED_INDUCTOR_TBD',note='Select with Isat exceeding worst-case IC current limit, DCR and thermal verified',status='BLOCKED_MPN')
cap('C2','22uF_10V','VLOGIC_IN','GND','power')
cap('C3','22uF_10V','3V3','GND','power')
cap('C4','22uF_10V','3V3','GND','power')
resistor('R2','560k','3V3','FB_3V3','power',note='0.1% preferred; nominal 0.5*(1+560/100)=3.3V')
resistor('R3','100k','FB_3V3','GND','power',note='0.1% preferred')
resistor('R4','180k','VLOGIC_IN','LOGIC_UVLO','power')
resistor('R5','100k','LOGIC_UVLO','GND','power',note='Nominal EN rising ~3.08V, falling ~2.80V at VLOGIC_IN, NOT raw battery')
cap('C5','1nF_16V','LOGIC_UVLO','GND','power','0603')
resistor('R6','10k','3V3','ESP_EN','power')
cap('C6','1uF_10V','ESP_EN','GND','power')
add('U3','TPS61023DRLR','DRL_6_SOT563',{1:('FB','FB_5V'),2:('EN','ACT_EN'),3:('VIN','VBAT'),4:('GND','GND'),5:('SW','FAN_BOOST_SW'),6:('VOUT','FAN_5V')},'power',mpn='TPS61023DRLR',manufacturer='Texas Instruments',note='5V fan supply, enabled by actuator interlock; battery only, no USB actuator feed')
two('L2','1uH','VBAT','FAN_BOOST_SW','power','SHIELDED_INDUCTOR_TBD',note='Select Isat/DCR against worst-case switch peak current, not fan average current',status='BLOCKED_MPN')
cap('C7','10uF_10V','VBAT','GND','power')
cap('C8','22uF_10V','FAN_5V','GND','power')
cap('C9','22uF_10V','FAN_5V','GND','power')
resistor('R7','732k','FAN_5V','FB_5V','power')
resistor('R8','100k','FB_5V','GND','power',note='Nominal 4.9504V at 595mV PWM reference; ~5.0V in PFM. Verify load transient and tolerance.')
cap('C10','220pF_DNP','FAN_5V','FB_5V','power','0603',note='Optional feed-forward, DNP by default; populate only from stability analysis')
# MCU: exact WROOM-1 N16R8 pad numbering, NC Octal PSRAM pins.
mapnames=['GND','3V3','EN','IO4','IO5','IO6','IO7','IO15','IO16','IO17','IO18','IO8','IO19','IO20','IO3','IO46','IO9','IO10','IO11','IO12','IO13','IO14','IO21','IO47','IO48','IO45','IO0','IO35','IO36','IO37','IO38','IO39','IO40','IO41','IO42','RXD0','TXD0','IO2','IO1','GND','EPAD']
gpio={1:'M_AIN1',2:'M_AIN2',4:'CAM_D0',5:'CAM_D1',6:'CAM_D2',7:'CAM_D3',8:'CAM_D4',9:'CAM_D5',10:'CAM_D6',11:'CAM_D7',12:'CAM_PWDN',13:'CAM_PCLK',14:'CAM_RST',15:'BAT_ADC',16:'CAM_VSYNC',17:'CAM_HREF',18:'CAM_SDA',19:'USB_DM_MCU',20:'USB_DP_MCU',21:'CAM_SCL',38:'M_BIN1',39:'M_BIN2',40:'FAN_CMD',41:'EXP_SDA',42:'M_FAULT_N',47:'ACT_REQ',48:'EXP_SCL',0:'BOOT_N'}
pins={}
for i,n in enumerate(mapnames,1):
 net='GND' if n in ('GND','EPAD') else '3V3' if n=='3V3' else 'ESP_EN' if n=='EN' else 'UART_RX' if n=='RXD0' else 'UART_TX' if n=='TXD0' else gpio.get(int(n[2:])) if n.startswith('IO') else None
 pins[i]=(n,net)
add('U1','ESP32-S3-WROOM-1-N16R8','ESP32-S3-WROOM-1',pins,'mcu',mpn='ESP32-S3-WROOM-1-N16R8',manufacturer='Espressif Systems',note='16MB Flash, 8MB Octal PSRAM. GPIO35/36/37 NC. Antenna over board edge; full keepout per manufacturer.')
cap('C11','22uF_10V','3V3','GND','mcu');cap('C12','100nF_16V','3V3','GND','mcu','0603')
resistor('R9','10k','3V3','BOOT_N','mcu')
two('SW2','RESET','ESP_EN','GND','mcu','TACT_SWITCH_TBD')
two('SW3','BOOT','BOOT_N','GND','mcu','TACT_SWITCH_TBD')
resistor('R10','1M','VBAT','BAT_ADC','mcu');resistor('R11','330k','BAT_ADC','GND','mcu');cap('C13','100nF_16V','BAT_ADC','GND','mcu','0603',note='ADC2/GPIO15 availability and acquisition settling with Wi-Fi must be validated; no eFuse writes')
# Hardware interlock prevents GPIO39/40 boot behavior from powering loads.
for ref,in_a,in_b,y in [('U6','ACT_REQ','ESP_EN','ACT_EN'),('U7','FAN_CMD','ACT_EN','FAN_GATE_LOGIC')]:
 add(ref,'SN74LVC1G08DBVR','SOT-23-5',{1:('A',in_a),2:('B',in_b),3:('GND','GND'),4:('Y',y),5:('VCC','3V3')},'interlock',mpn='SN74LVC1G08DBVR',manufacturer='Texas Instruments',note='Ioff device required; no 74HC/5V-only substitution')
resistor('R12','10k','ACT_REQ','GND','interlock');resistor('R13','10k','ACT_EN','GND','interlock');resistor('R14','100k','FAN_CMD','GND','interlock')
cap('C14','100nF_16V','3V3','GND','interlock','0603');cap('C15','100nF_16V','3V3','GND','interlock','0603')
# Driver uses HTSSOP-16 exposed pad numbering, never WQFN numbering.
add('U4','DRV8833PWPR','HTSSOP-16_PWP_EP',{1:('nSLEEP','ACT_EN'),2:('AOUT1','MOTOR_A1'),3:('AISEN','A_SENSE'),4:('AOUT2','MOTOR_A2'),5:('BOUT2','MOTOR_B2'),6:('BISEN','B_SENSE'),7:('BOUT1','MOTOR_B1'),8:('nFAULT','M_FAULT_N'),9:('BIN1','M_BIN1'),10:('BIN2','M_BIN2'),11:('VCP','DRV_VCP'),12:('VM','VBAT'),13:('GND','GND'),14:('VINT','DRV_VINT'),15:('AIN2','M_AIN2'),16:('AIN1','M_AIN1'),17:('EPAD','GND')},'motor',mpn='DRV8833PWPR',manufacturer='Texas Instruments',note='PowerPAD grounded with thermal-via array; cannot substitute PW/TSSOP or DRV8833C blindly')
for ref,net in [('R15','M_AIN1'),('R16','M_AIN2'),('R17','M_BIN1'),('R18','M_BIN2')]:resistor(ref,'10k',net,'GND','motor')
resistor('R19','10k','3V3','M_FAULT_N','motor')
for ref,net in [('RS1','A_SENSE'),('RS2','B_SENSE')]:
 resistor(ref,'0.39R_0.5W',net,'GND','motor','1206',note='PROVISIONAL: nominal Itrip=0.2/0.39=0.513A. Validate N20 start/stall/thermal and comparator tolerance before freeze.')
cap('C16','10uF_16V','VBAT','GND','motor');cap('C17','100nF_16V','VBAT','GND','motor','0603');cap('C18','10nF_25V','DRV_VCP','VBAT','motor','0603');cap('C19','2.2uF_10V','DRV_VINT','GND','motor','0603')
conn('J2','LEFT_MOTOR',[('A1','MOTOR_A1'),('A2','MOTOR_A2')],'motor',package='JST-PH_2.00_2P_CANDIDATE',note='User-confirmed N20 6V 60rpm; driven from 3 dry cells, not regulated 6V. Both pins are bridge outputs, neither is ground. Start/stall current and cable polarity require validation.')
conn('J3','RIGHT_MOTOR',[('B1','MOTOR_B1'),('B2','MOTOR_B2')],'motor',package='JST-PH_2.00_2P_CANDIDATE',note='User-confirmed N20 6V 60rpm; VBAT drive, no 6V boost. Start/stall current and cable polarity require validation.')
# Fan is a 5V two-wire BLDC fan, not an H-bridge load.
add('Q1','AO3400A','SOT-23',{1:('G','FAN_GATE'),2:('S','GND'),3:('D','FAN_SW')},'fan',mpn='AO3400A',manufacturer='Alpha & Omega Semiconductor',note='3.3V gate drive; use specified low-Vgs Rds_on, not just threshold')
resistor('R20','100R','FAN_GATE_LOGIC','FAN_GATE','fan');resistor('R21','100k','FAN_GATE','GND','fan')
add('D1','SS14','SMA',{1:('K','FAN_5V'),2:('A','FAN_SW')},'fan',mpn='SS14',note='Clamp option; exact vendor/pin marking and BLDC transient behavior reviewed before freeze')
conn('J4','5V_FAN',[('RED_+','FAN_5V'),('BLACK_-','FAN_SW')],'fan',package='JST-PH_2.00_2P_CANDIDATE',note='AFB0405MA-A two-wire 5V/0.1A; no tach feedback')
# Native USB-C USB2.0, VBUS routed only to logic OR. No charger on alkaline cells.
usbpins={'A1':('GND','GND'),'A4':('VBUS','USB_VBUS'),'A5':('CC1','USB_CC1'),'A6':('DP','USB_DP_CONN'),'A7':('DM','USB_DM_CONN'),'A8':('SBU1',None),'A9':('VBUS','USB_VBUS'),'A12':('GND','GND'),'B1':('GND','GND'),'B4':('VBUS','USB_VBUS'),'B5':('CC2','USB_CC2'),'B6':('DP','USB_DP_CONN'),'B7':('DM','USB_DM_CONN'),'B8':('SBU2',None),'B9':('VBUS','USB_VBUS'),'B12':('GND','GND'),'SH':('SHIELD','USB_SHIELD')}
add('J6','USB_C_USB2','USB_C_16P_TBD',usbpins,'usb',note='Select exact manufacturer then map pads; combined shell pads vs SH MUST be resolved before footprint assignment',status='MECHANICAL_CONFIRM_REQUIRED')
resistor('R22','5.1k','USB_CC1','GND','usb');resistor('R23','5.1k','USB_CC2','GND','usb')
add('U5','USBLC6-2SC6','SOT-23-6',{1:('IO1','USB_DM_CONN'),2:('GND','GND'),3:('IO2','USB_DP_CONN'),4:('IO2','USB_DP_ESD'),5:('VBUS','USB_VBUS'),6:('IO1','USB_DM_ESD')},'usb',mpn='USBLC6-2SC6',manufacturer='STMicroelectronics',note='Flow-through I/O pairs internally connected; place at connector, short low-inductance ground')
resistor('R24','22R','USB_DM_ESD','USB_DM_MCU','usb');resistor('R25','22R','USB_DP_ESD','USB_DP_MCU','usb')
resistor('R26','0R','USB_SHIELD','GND','usb');cap('C20','1uF_10V','USB_VBUS','GND','usb')
# Camera numbering is newly proposed; not claimed as manufacturer numbering.
cam=[('GND','GND'),('3V3','3V3'),('SCL','CAM_SCL'),('VS','CAM_VSYNC'),('SDA','CAM_SDA'),('HS','CAM_HREF'),('D0','CAM_D0'),('RST','CAM_RST'),('D2','CAM_D2'),('D1','CAM_D1'),('D4','CAM_D4'),('D3','CAM_D3'),('D6','CAM_D6'),('D5','CAM_D5'),('PCLK','CAM_PCLK'),('D7','CAM_D7'),('PWDN','CAM_PWDN'),('FLASH_NC',None)]
conn('J5','CAMERA_2x9_P2.54',cam,'camera',note='User confirmed 2x9, pitch=2.54mm, row spacing=2.54mm. This design assigns pin numbers; final socket MPN, mating-view mapping and stack height require verification. Photo OV5640 silkscreen conflicts with working OV2640 configuration; verify sensor PID.',package='2x9_P2.54_ROW2.54_SOCKET_MPN_TBD')
cap('C21','10uF_10V','3V3','GND','camera');cap('C22','100nF_16V','3V3','GND','camera','0603')
conn('J7','EXP_I2C_3V3',[('3V3','3V3'),('GND','GND'),('SDA41','EXP_SDA'),('SCL48','EXP_SCL')],'expansion',package='1x4_2.54_CANDIDATE',note='Future ToF/IMU only; not a 5V sensor/power output. Implement fault/edge sensors before open-table autonomy.')
resistor('R27','4.7k','3V3','EXP_SDA','expansion');resistor('R28','4.7k','3V3','EXP_SCL','expansion')
conn('J8','SERVICE_3V3',[('GND','GND'),('3V3_REF','3V3'),('TX43','UART_TX'),('RX44','UART_RX'),('EN','ESP_EN'),('BOOT0','BOOT_N')],'expansion',package='1x6_2.54_CANDIDATE',note='3V3 is reference/output; do not connect 5V UART. Do not drive power into 3V3.')
# Test points do not imply assembled headers.
for i,net in enumerate(['GND','VBAT','3V3','FAN_5V','ACT_REQ','ACT_EN','M_FAULT_N','BAT_ADC','USB_VBUS','ESP_EN'],1):
 add('TP'+str(i),net,'TESTPAD_1MM',{1:(net,net)},'test',note='Bare copper test pad, no purchased part',status='PCB_ONLY')

ROOT.joinpath('design/circuit.json').write_text(json.dumps(dict(project='FanRobot_Mainboard',revision='0.1-review',release='NOT_FOR_FABRICATION',hardware_inputs=hardware_inputs,parts=parts),indent=2,ensure_ascii=False)+'\n')
fields=['Reference','Value','Manufacturer','MPN','Package_candidate','Quantity','LCSC_SKU','Status','Notes']
with ROOT.joinpath('assembly/BOM_REVIEW_ONLY.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for p in parts:w.writerow(dict(Reference=p['ref'],Value=p['value'],Manufacturer=p['manufacturer'],MPN=p['mpn'],Package_candidate=p['package'],Quantity=0 if p['status']=='PCB_ONLY' or p['ref']=='C10' else 1,LCSC_SKU='',Status=p['status'],Notes=p['note']))
with ROOT.joinpath('design/pin_net_map.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Reference','Physical_pin_number','Pin_name','Global_net','Section'])
 for p in parts:
  for number,pin in p['pins'].items():w.writerow([p['ref'],number,pin['name'],pin['net'] or 'NC',p['section']])
# KiCad XML netlist (no guessed footprints or placement).
export=ET.Element('export',version='E');design=ET.SubElement(export,'design');ET.SubElement(design,'source').text='fan_robot_mainboard.sch';ET.SubElement(design,'tool').text='FanRobot design generator: REVIEW ONLY'
components=ET.SubElement(export,'components');nets=defaultdict(list)
for p in parts:
 c=ET.SubElement(components,'comp',ref=p['ref']);ET.SubElement(c,'value').text=p['value'];ET.SubElement(c,'footprint').text='';ET.SubElement(c,'datasheet').text='';ET.SubElement(c,'libsource',lib='FanRobot',part=p['ref'])
 for number,pin in p['pins'].items():
  if pin['net']:nets[pin['net']].append((p['ref'],number,pin['name']))
node=ET.SubElement(export,'nets')
for code,(name,pins) in enumerate(sorted(nets.items()),1):
 net=ET.SubElement(node,'net',code=str(code),name=name)
 for ref,number,pinname in pins:ET.SubElement(net,'node',ref=ref,pin=number,pinfunction=pinname,pintype='passive')
ET.indent(export);ET.ElementTree(export).write(ROOT/'eda/fan_robot_mainboard.net',encoding='utf-8',xml_declaration=True)
# Legacy KiCad v4 source using local, explicit pin-number symbols and global labels.
# Each component is a functional pin block, not a certified manufacturer CAD library.
def quoted(v):return v.replace('"',"'").replace('\n',' ')
lib=['EESchema-LIBRARY Version 2.4','#encoding utf-8']
geometry={}
for p in parts:
 n=len(p['pins']);left=(n+1)//2;right=n-left; half=max(200,math.ceil(left*100/2)+100);ys=[int((left-1)*50-i*100) for i in range(left)];yrs=[int((right-1)*50-i*100) for i in range(right)]
 positions=[]
 lib+=['#','# '+p['ref'],'#',f'DEF {p["ref"]} {p["ref"].rstrip("0123456789")} 0 30 Y Y 1 F N',f'F0 "{p["ref"]}" 0 {half+150} 50 H V C CNN',f'F1 "{quoted(p["value"])}" 0 {half+50} 50 H V C CNN','DRAW',f'S -650 {half} 650 {-half} 0 1 8 f']
 for i,(number,pin) in enumerate(p['pins'].items()):
  side='L' if i<left else 'R';y=ys[i] if side=='L' else yrs[i-left];x=-850 if side=='L' else 850;direction='R' if side=='L' else 'L'
  pname=pin['name'].replace(' ','_');lib.append(f'X {pname} {number} {x} {y} 200 {direction} 40 40 1 1 P');positions.append((number,x,y,side))
 lib+=['ENDDRAW','ENDDEF'];geometry[p['ref']]=positions
lib+=['#End Library'];ROOT.joinpath('eda/fan_robot.lib').write_text('\n'.join(lib)+'\n')
ROOT.joinpath('eda/fan_robot-cache.lib').write_text('\n'.join(lib)+'\n')
ROOT.joinpath('eda/fan_robot_mainboard.pro').write_text('[eeschema]\nversion=1\n[eeschema/libraries]\nLibName1=fan_robot\n')
ROOT.joinpath('eda/sym-lib-table').write_text('(sym_lib_table\n  (lib (name "FanRobot")(type "Legacy")(uri "${KIPRJMOD}/fan_robot.lib")(options "")(descr "Review-only custom pin blocks"))\n)\n')
groups=[('power',['power']),('mcu_camera',['mcu','camera']),('actuators',['interlock','motor','fan']),('usb_expansion',['usb','expansion','test'])]
for sheetno,(name,sections) in enumerate(groups,1):
 group=[p for p in parts if p['section'] in sections];columns=4;rows=math.ceil(len(group)/columns);cell_h=min(3000,14500//max(rows,1))
 sch=['EESchema Schematic File Version 4','LIBS:fan_robot','EELAYER 29 0','EELAYER END','$Descr A2 23386 16535','encoding utf-8',f'Sheet {sheetno+1} 5',f'Title "FanRobot {name} - REVIEW ONLY"','Date "2026-11-14"','Rev "0.1-NOT-FOR-FAB"','Comp "FanRobot prototype"','Comment1 "No PCB routing/ERC/DRC/footprint verification yet"','Comment2 "Global labels interconnect all sheets; NC pins explicitly marked"','Comment3 "Camera J5 pin numbering proposed; verify physical mating orientation"','Comment4 ""','$EndDescr']
 for j,p in enumerate(group):
  x=3000+(j%columns)*5500;y=1800+(j//columns)*cell_h;half=max(200,max(abs(q[2]) for q in geometry[p['ref']])+100);uid=f'{0xA0000000+sheetno*1000+j:08X}'
  sch+=['$Comp',f'L FanRobot:{p["ref"]} {p["ref"]}',f'U 1 1 {uid}',f'P {x} {y}',f'F 0 "{p["ref"]}" H {x} {y-half-150} 50 0000 C CNN',f'F 1 "{quoted(p["value"])}" H {x} {y-half-50} 45 0000 C CNN',f'F 2 "" H {x} {y} 50 0001 C CNN',f'F 3 "" H {x} {y} 50 0001 C CNN',f'\t1 {x} {y}','\t1 0 0 -1','$EndComp']
  for number,px,py,side in geometry[p['ref']]:
   xx=x+px;yy=y-py;net=p['pins'][number]['net']
   if net:
    end=xx-350 if side=='L' else xx+350;orientation=0 if side=='L' else 2
    sch+=['Wire Wire Line',f'\t{xx} {yy} {end} {yy}',f'Text GLabel {end} {yy} {orientation} 40 BiDi ~ 0',net]
   else:sch.append(f'NoConn ~ {xx} {yy}')
 sch+=['$EndSCHEMATC'];ROOT.joinpath(f'eda/{name}.sch').write_text('\n'.join(sch)+'\n')
root=['EESchema Schematic File Version 4','LIBS:fan_robot','EELAYER 29 0','EELAYER END','$Descr A4 11693 8268','encoding utf-8','Sheet 1 5','Title "FanRobot 3xAA integrated mainboard"','Date "2026-11-14"','Rev "0.1-NOT-FOR-FAB"','Comp "Engineering review source"','Comment1 "Electrical design draft: NO Gerber, placement, ERC or DRC release"','Comment2 "60x50mm, 4 layers; camera 2x9 pitch/row 2.54mm; verify sensor PID"','Comment3 "Legacy KiCad source requires import and manufacturer library review"','Comment4 ""','$EndDescr']
for i,(name,_) in enumerate(groups):
 x=2000+(i%2)*4000;y=2000+(i//2)*2000
 root+=['$Sheet',f'S {x} {y} 2500 1000',f'U {0xB0000000+i:08X}',f'F0 "{name}" 50',f'F1 "{name}.sch" 50','$EndSheet']
root+=['$EndSCHEMATC'];ROOT.joinpath('eda/fan_robot_mainboard.sch').write_text('\n'.join(root)+'\n')
print(f'Generated {len(parts)} references, {len(nets)} nets. REVIEW ONLY, NOT manufacturing output.')
