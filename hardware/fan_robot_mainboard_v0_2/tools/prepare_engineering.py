"""Select exact parts for an engineering prototype; no fabrication release is implied."""
from pathlib import Path
import json,csv,shutil,os
ROOT=Path(__file__).resolve().parents[1]
KICAD=Path(os.environ.get('FAN_KICAD_APP',Path.home()/'.local/share/fanrobot-eda/KiCad.app'))
LIB=KICAD/'Contents/SharedSupport/footprints'
d=json.loads((ROOT/'design/base-circuit-v0_1.json').read_text())
p={x['ref']:x for x in d['parts']}
def select(ref,mpn,mfr,code,fp,note=''):
 x=p[ref];x.update(mpn=mpn,manufacturer=mfr,lcsc=code,footprint=fp,status='SELECTED_ENGINEERING_PROTOTYPE',dnp=ref in ['C10','J7','J8'])
 x['note']=note or x['note']
 x['source']='https://www.lcsc.com/product-detail/'+code+'.html' if code else ''
 x['assembly']='DNP' if x['dnp'] else 'THT' if ref in ['J1','J2','J3','J4','J5'] else 'SMT'
def new(ref,value,pins,section='power',package='0603'):
 p[ref]=dict(ref=ref,value=value,package=package,pins={str(k):dict(name=v[0],net=v[1]) for k,v in pins.items()},section=section,mpn='',manufacturer='',note='',status='DRAFT')
# MOSFET power control: slide-switch contacts carry only gate current.
p['F1']['pins']['1']['net']='BAT_RAW'
p['Q2']['pins']['2']['net']='BAT_PROTECTED'
new('Q3','AO3401A',{1:('G','POWER_GATE'),2:('S','BAT_PROTECTED'),3:('D','VBAT')},package='SOT-23')
new('R29','100k',{1:('1','POWER_GATE'),2:('2','BAT_PROTECTED')})
p['SW1']['pins']={'1':dict(name='OFF',net=None),'2':dict(name='COMMON',net='POWER_GATE'),'3':dict(name='ON',net='GND')}
p['SW1']['value']='POWER_GATE_SWITCH'
# ADC1 is usable while Wi-Fi runs. This is a separate new-board pin map.
p['U1']['pins']['8']['net']='M_AIN1' # IO15
p['U1']['pins']['39']['net']='BAT_ADC' # IO1/ADC1_CH0
p['U1']['note']='N16R8: 16MB Flash, 8MB Octal PSRAM. GPIO35/36/37 NC. New board: BAT_ADC GPIO1/ADC1; AIN1 GPIO15. Other mappings preserved.'
p['C13']['note']='ADC1/GPIO1 channel 0; calibrate 1M/330k divider and use settled averaged oneshot reads. No ADC2/Wi-Fi contention.'
# Limit USB logic supply independently of battery-only actuator feed.
new('U8','TPS2553DBVR',{1:('IN','USB_VBUS'),2:('GND','GND'),3:('EN','USB_VBUS'),4:('nFAULT','USB_FAULT_N'),5:('ILIM','USB_ILIM'),6:('OUT','USB_LIMITED')},'usb','SOT-23-6')
new('R30','68.1k',{1:('1','USB_ILIM'),2:('2','GND')},'usb')
new('C23','1uF_16V',{1:('1','USB_LIMITED'),2:('2','GND')},'usb','0805')
new('C24','100nF_16V',{1:('1','USB_VBUS'),2:('2','GND')},'usb')
p['D3']['pins']['2']['net']='USB_LIMITED'
# KiCad10 HRO footprint uses SH for all four shield tabs.
new('TP11','USB_FAULT_N',{1:('USB_FAULT_N','USB_FAULT_N')},'test','TESTPAD_1MM')
ics={
 'U1':('ESP32-S3-WROOM-1-N16R8','Espressif Systems','C2913202','RF_Module:ESP32-S3-WROOM-1'),
 'U2':('TPS63802DLAR','Texas Instruments','C2845237','FanRobot:TPS63802_DLA0010A'),
 'U3':('TPS61023DRLR','Texas Instruments','C919459','Package_TO_SOT_SMD:SOT-563'),
 'U4':('DRV8833PWPR','Texas Instruments','C50506','Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm'),
 'U5':('USBLC6-2SC6','STMicroelectronics','C7519','Package_TO_SOT_SMD:SOT-23-6'),
 'U6':('SN74LVC1G08DBVR','Texas Instruments','C7666','Package_TO_SOT_SMD:SOT-23-5'),
 'U7':('SN74LVC1G08DBVR','Texas Instruments','C7666','Package_TO_SOT_SMD:SOT-23-5'),
 'U8':('TPS2553DBVR','Texas Instruments','C55266','Package_TO_SOT_SMD:SOT-23-6'),
}
for ref,args in ics.items():select(ref,*args)
p['U8']['note']='USB input protection: 68.1k +/-1% ILIM resistor; max current from datasheet equations <500mA. Not USB current negotiation; battery required for full-load operation. FAULT is open drain test point.'
for ref in ['Q1','Q2','Q3']:
 select(ref,'AO3400A' if ref=='Q1' else 'AO3401A','Alpha & Omega Semiconductor','C20917' if ref=='Q1' else 'C15127','Package_TO_SOT_SMD:SOT-23')
p['Q2']['note']='Reverse protector: D=BAT_FUSED, S=BAT_PROTECTED, gate to GND via R1. Intentional reverse D/S relative to conventional load switch.'
p['Q3']['note']='Power switch: S=BAT_PROTECTED, D=VBAT; R29 pulls gate to source (OFF). SW1 pulls gate to GND (ON). Gate contacts carry about 50uA, not motor current.'
select('F1','MF-MSMF200-2','Bourns','C210837','Fuse:Fuse_1812_4532Metric','2A hold/4A trip at 23C, 8V PPTC. Thermal derating and loaded cell tests are prototype acceptance items; not precision motor current protection.')
p['F1']['value']='2A_HOLD_PPTC'
select('L1','DFE201612E-R47M=P2','Murata','C668312','FanRobot:L_Murata_DFE201612E','470nH +/-20%; Isat 5.5A (30% drop), Itemp 4.5A, DCR max26mOhm. Listed in TI TPS63802 recommended inductors.')
select('L2','74438357010','Wurth Elektronik','C5542269','Inductor_SMD:L_Wuerth_MAPI-4030','1uH +/-20%; TI TPS61023 recommended inductor; Isat9.6A, DCR max13.5mOhm. No substitution with same-size low-current part.')
for ref in ['D1','D2','D3']:
 select(ref,'SS14' if ref=='D1' else 'SS34','MDD','C2480' if ref=='D1' else 'C8678','Diode_SMD:D_SMA', 'Cathode=pad1. D2/D3 diode OR only powers logic; no USB backfeed into battery. Validate reverse leakage and temperature.')
res={'100k':('1003','C25803'),'10k':('1002','C25804'),'560k':('5603','C23203'),'180k':('1803','C22827'),'732k':('7323','C23239'),'1M':('1004','C22935'),'330k':('3303','C23137'),'100R':('1000','C22775'),'22R':('220J','C23345'),'0R':('0000','C21189'),'4.7k':('4701','C23162'),'5.1k':('5101','C23186'),'68.1k':('6812','C25976')}
for ref,x in list(p.items()):
 if ref.startswith('R') and not ref.startswith('RS'):
  code,lcsc=res[x['value']];select(ref,'0603WAF'+code+'T5E','UNI-ROYAL',lcsc,'Resistor_SMD:R_0603_1608Metric','1%, 100mW, 0603; feedback/divider tolerances included in engineering calculations.')
for ref in ['RS1','RS2']:
 select(ref,'RL12FTNR390','TA-I Tech','C188072','Resistor_SMD:R_1206_3216Metric','0.39ohm +/-1%,0.5W. Nominal motor chopper limit0.513A; fixed conservative first-board setting, qualify loaded starting before any increase.')
capdefs={
 '22uF':('GRM21BR61A226ME51L','Murata','C77074','0805','22uF_10V'),
 '10uF':('GRM21BR61C106KE15L','Murata','C77075','0805','10uF_16V'),
 '100nF':('GRM188R71C104KA01D','Murata','C45000','0603','100nF_16V'),
 '1nF':('CL10B102KB8NNNC','Samsung Electro-Mechanics','C1588','0603','1nF_50V'),
 '1uF':('GRM21BR71C105KA01L','Murata','C77079','0805','1uF_16V'),
 '2.2uF':('GRM21BR71C225KA12L','Murata','C108378','0805','2.2uF_16V'),
 '10nF':('CL10B103KB8NNNC','Samsung Electro-Mechanics','C1589','0603','10nF_50V'),
 '220pF':('CL10C221JB8NNNC','Samsung Electro-Mechanics','C27675','0603','220pF_DNP'),
}
for ref,x in list(p.items()):
 if ref.startswith('C') and ref!='C1':
  k=x['value'].split('_')[0];mpn,mfr,code,case,value=capdefs[k]
  x['value']=value;x['package']=case
  select(ref,mpn,mfr,code,'Capacitor_SMD:C_'+case+('_2012Metric' if case=='0805' else '_1608Metric'),'X5R/X7R (C10 C0G); actual MPN and voltage rating selected. C10 DNP. Effective capacitance/ripple verified in supply review and prototype acceptance.')
select('C1','10SVPE220M','Panasonic','C165949','FanRobot:CP_OSCON_C6_6.3x5.9','220uF10V OS-CON polymer; ESR20mOhm, ripple2.7Arms@100kHz/105C (frequency derating applies),6.3x5.9mm,C6. Pad1 positive. Panasonic land a2.1,b9.1,c1.6mm. Do not replace with low-ripple general-purpose electrolytic.')
for ref in ['SW2','SW3']:
 select(ref,'KMR221GLFS','C&K','C72443','Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2')
select('SW1','JS102011SAQN','C&K','C221660','Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN','SPDT: common pad2 POWER_GATE; pad3 GND enables power, pad1 NC. Carries MOSFET gate current only.')
select('J1','B2B-XH-A(LF)(SN)','JST','C158012','Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical','3A rated header; use XHP-2 housing and SXH contacts with 22AWG battery wire. Pad1 battery positive, pad2 GND.')
for ref in ['J2','J3','J4']:
 select(ref,'B2B-PH-K-S(LF)(SN)','JST','C131337','Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical','2A rated header; matching PHR-2 housing and SPH contacts. Motor outputs must not be grounded; fan pad1 positive.26AWG minimum for this limited-current prototype.')
select('J5','2.54-2*9P','BOOMELE','C71956','Connector_PinSocket_2.54mm:PinSocket_2x09_P2.54mm_Vertical','2x9 female header; pitch and row spacing2.54mm. Board pad1=GND, pad2=3V3; pin1 marked. Camera mating orientation/continuity must be checked unpowered; use a verified labelled harness if direct mating does not fit.')
select('J6','TYPE-C-31-M-12','Korean Hroparts Elec','C165948','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12','16-contact USB2 receptacle. Four shell tabs all SH=USB_SHIELD. Paired A1/B12 etc pads are intentionally coincident and share their assigned nets.')
for ref,n in [('J7',4),('J8',6)]:
 select(ref,'DNP_2.54mm_1x'+str(n),'Not populated','','Connector_PinHeader_2.54mm:PinHeader_1x%02d_P2.54mm_Vertical'%n,'Reserved 2.54mm service/expansion footprint; DNP by default, no purchased part included.')
for ref,x in p.items():
 if ref.startswith('TP'):
  x.update(mpn='',manufacturer='',lcsc='',source='',footprint='TestPoint:TestPoint_Pad_D1.0mm',dnp=False,assembly='PCB_ONLY',status='PCB_ONLY')
# Use actual component pin electrical types, not all-passive ICs.
for ref,x in p.items():
 for no,pin in x['pins'].items():
  t='passive'
  if ref=='U1':
   t='power_in' if no in ['1','2','40','41'] else 'input' if no in ['3','36'] else 'output' if no=='37' else 'bidirectional'
  elif ref in ['U6','U7']:t={'1':'input','2':'input','3':'power_in','4':'output','5':'power_in'}[no]
  elif ref=='U2':t={'1':'input','2':'input','3':'power_in','4':'input','5':'open_collector','6':'power_out','7':'passive','8':'power_in','9':'passive','10':'power_in'}[no]
  elif ref=='U3':t={'1':'input','2':'input','3':'power_in','4':'power_in','5':'passive','6':'power_out'}[no]
  elif ref=='U4':t='power_in' if no in ['12','13','17'] else 'output' if no in ['2','4','5','7'] else 'open_collector' if no=='8' else 'power_out' if no=='14' else 'input' if no in ['1','9','10','15','16'] else 'passive'
  elif ref=='U5':t='power_in' if no in ['2','5'] else 'passive'
  elif ref=='U8':t={'1':'power_in','2':'power_in','3':'input','4':'open_collector','5':'passive','6':'power_out'}[no]
  pin['type']=t
for x in p.values():
 if x['assembly'] not in ['DNP','PCB_ONLY']:assert x['mpn'] and x['lcsc'] and x['footprint'],x['ref']
d.update(project='FanRobot_Mainboard',revision='0.2-engineering',release='IN_DESIGN_NOT_FOR_FABRICATION',parts=list(p.values()))
d['hardware_inputs']['motors']['current_limit_status']='0.39ohm,0.5W fixed engineering prototype selection; loaded start/thermal qualification after fabrication'
d['hardware_inputs']['camera']['connector_mpn']='BOOMELE 2.54-2*9P / C71956'
d['hardware_inputs']['new_board_gpio_changes']={'BAT_ADC':'GPIO1/ADC1_CH0','M_AIN1':'GPIO15','ACT_REQ':'GPIO47','M_FAULT_N':'GPIO42'}
(ROOT/'design/circuit.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
fpdir=ROOT/'eda/FanRobot.pretty';fpdir.mkdir(exist_ok=True)
provenance=[]
for fid in sorted({x['footprint'] for x in p.values()}):
 lib,name=fid.split(':')
 if lib=='FanRobot':continue
 src=LIB/(lib+'.pretty')/(name+'.kicad_mod');assert src.exists(),src
 shutil.copy2(src,fpdir/(name+'.kicad_mod'))
 provenance.append(dict(footprint=name,source=str(src.relative_to(KICAD)),library_version='KiCad10.0.8',license='KiCad libraries CC-BY-SA4.0 with exception'))
for x in p.values():x['footprint']='FanRobot:'+x['footprint'].split(':')[1]
(ROOT/'design/circuit.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
(ROOT/'reference/footprint-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
shutil.copy2(LIB.parent/'footprints/LICENSE.md',ROOT/'reference/KiCad-footprint-LICENSE.md') if (LIB/'LICENSE.md').exists() else None
(ROOT/'eda/fp-lib-table').write_text('(fp_lib_table (lib (name "FanRobot") (type "KiCad") (uri "${KIPRJMOD}/FanRobot.pretty") (options "") (descr "Locally pinned KiCad10 and datasheet-derived footprints")))\n')
rows=[]
for x in p.values():
 rows.append(dict(Reference=x['ref'],Value=x['value'],Manufacturer=x['manufacturer'],MPN=x['mpn'],LCSC=x['lcsc'],Footprint=x['footprint'],Assembly=x['assembly'],Quantity=0 if x['assembly'] in ['DNP','PCB_ONLY'] else 1,Notes=x['note']))
with (ROOT/'assembly/BOM_ENGINEERING.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Selected',len(p),'references; all populated purchased parts have exact MPN and sourced LCSC code. Not a fabrication release.')
