"""Create native KiCad schematics with typed pins and explicit power sources."""
from pathlib import Path
import json,math,uuid,csv
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda'
d=json.loads((ROOT/'design/circuit.json').read_text());parts=d['parts']
NS=uuid.UUID('10230e1c-776b-49c1-96e7-cc6e7c2490ee')
def uid(s):return str(uuid.uuid5(NS,s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def eff(sz=1.016,justify='',hide=False):return '(effects (font (size %s %s)) %s %s)'%(sz,sz,'(justify '+justify+')' if justify else '','(hide yes)' if hide else '')
def prop(name,value,x,y,hidden=False):return f'(property {q(name)} {q(value)} (at {x:.4f} {y:.4f} 0)'+ (' (hide yes)' if hidden else '')+f' {eff()})'
geometry={};libraries=[]
for p in parts:
 ref=p['ref'];items=list(p['pins'].items());n=len(items);left=(n+1)//2;right=n-left
 # ICs/connectors use 100mil pin grid. Discrete 2-pin passives get compact familiar graphics.
 compact=(n==2 and ref[0] in 'RCLD')
 half=max(2.54,left*1.27+1.27);bodyw=16.51 if not compact else 1.27
 loc=[]
 for i,(number,pin) in enumerate(items):
  side='L' if i<left else 'R';count=left if side=='L' else right;ix=i if side=='L' else i-left
  y=(count-1)*1.27-ix*2.54;x=-(bodyw+5.08) if side=='L' else bodyw+5.08
  if compact:x=-5.08 if i==0 else 5.08;y=0
  loc.append((number,x,y,0 if side=='L' else 180))
 geometry[ref]=(half,loc)
 symbol=[f'(symbol {q("FanRobot:"+ref)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',prop('Reference',ref,0,half+4),prop('Value',p['value'],0,half+2),prop('Footprint',p['footprint'],0,0,True),prop('Datasheet',p.get('source',''),0,0,True)]
 graphic=[]
 if compact and ref.startswith('C'):
  for x in [-.635,.635]:graphic.append(f'(polyline (pts (xy {x} -1.905)(xy {x} 1.905)) (stroke (width 0.254)(type default))(fill (type none)))')
  for xa,xb in [(-3.81,-.635),(.635,3.81)]:graphic.append(f'(polyline (pts (xy {xa} 0)(xy {xb} 0)) (stroke (width 0)(type default))(fill (type none)))')
 elif compact and ref.startswith('R'):
  graphic.append('(rectangle (start -2.54 1.016)(end 2.54 -1.016)(stroke (width 0.254)(type default))(fill (type none)))')
  for xa,xb in [(-3.81,-2.54),(2.54,3.81)]:graphic.append(f'(polyline (pts (xy {xa} 0)(xy {xb} 0)) (stroke (width 0)(type default))(fill (type none)))')
 else:graphic.append(f'(rectangle (start {-bodyw} {half})(end {bodyw} {-half})(stroke (width 0.254)(type default))(fill (type background)))')
 symbol.append(f'(symbol {q(ref+"_0_1")} '+''.join(graphic)+')')
 symbol.append(f'(symbol {q(ref+"_1_1")}')
 for number,x,y,ang in loc:
  pin=p['pins'][number];length=1.27 if compact else 5.08
  symbol.append(f'(pin {pin["type"]} line (at {x:.4f} {y:.4f} {ang})(length {length})(name {q(pin["name"])} {eff(.889)})(number {q(number)} {eff(.889)}))')
 symbol.append('))');libraries.append('\n'.join(symbol))
flag='''(symbol "FanRobot:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom no) (on_board no)
(property "Reference" "#FLG" (at 0 1.905 0) (hide yes) (effects(font(size 1 1))))
(property "Value" "PWR_FLAG" (at 0 3.81 0)(effects(font(size 1 1))))
(symbol "PWR_FLAG_0_1" (polyline(pts(xy 0 0)(xy 0 1.27)(xy -1.27 2.54)(xy 1.27 2.54)(xy 0 1.27))(stroke(width 0)(type default))(fill(type none))))
(symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90)(length 0)(name "pwr" (effects(font(size 1 1))))(number "1" (effects(font(size 1 1)))))))'''
libraries.append(flag)
(EDA/'FanRobot.kicad_sym').write_text('(kicad_symbol_lib (version 20250114)(generator "kicad_symbol_editor")\n'+'\n'.join(s.replace('"FanRobot:','"',1) for s in libraries)+'\n)\n')
(EDA/'sym-lib-table').write_text('(sym_lib_table (lib (name "FanRobot")(type "KiCad")(uri "${KIPRJMOD}/FanRobot.kicad_sym")(options "")(descr "Datasheet pin mapping with electrical types")))\n')
rootid=uid('root');groups=[('power',['power']),('mcu_camera',['mcu','camera']),('actuators',['interlock','motor','fan']),('usb_expansion',['usb','expansion','test'])]
def label(net,x,y,angle=0):
 return f'(global_label {q(net)} (shape bidirectional)(at {x:.4f} {y:.4f} {angle}) {eff(.889,"right")} (uuid {q(uid(net+str(x)+str(y)+str(angle)))}))'
def header(name,id,paper):
 return [f'(kicad_sch (version 20250114)(generator "eeschema")(uuid {q(id)})(paper {q(paper)})(title_block(title {q("FanRobot V0.3 - "+name)})(date "2026-11-15")(rev "0.3 ENGINEERING")(comment 1 "3x1.5V dry cells; no charging; do not substitute power parts"))']
for gi,(name,sections) in enumerate(groups):
 sid=uid('sheet-'+name);group=[p for p in parts if p['section'] in sections]
 out=header(name,uid('file-'+name),'A2');out.append('(lib_symbols '+'\n'.join(libraries)+')')
 rows=math.ceil(len(group)/4);cell_h=math.floor(min(76.2,340/max(rows,1))/1.27)*1.27;cx=73.66;cy=48.26
 for j,p in enumerate(group):
  ref=p['ref'];x=cx+(j%4)*139.7;y=cy+(j//4)*cell_h;half,loc=geometry[ref]
  symbolid=uid(ref);p['schematic_uuid']=symbolid;p['sheet_path']='/'+rootid+'/'+sid
  out.append(f'(symbol (lib_id {q("FanRobot:"+ref)})(at {x:.4f} {y:.4f} 0)(unit 1)(in_bom {"no" if p["assembly"]=="PCB_ONLY" else "yes"})(on_board yes)(dnp {"yes" if p["dnp"] else "no"})(uuid {q(symbolid)})')
  out.extend([prop('Reference',ref,x,y-half-4),prop('Value',p['value'],x,y-half-1.6),prop('Footprint',p['footprint'],x,y,True),prop('Datasheet',p.get('source',''),x,y,True),prop('MPN',p['mpn'],x,y,True),prop('LCSC',p['lcsc'],x,y,True)])
  for number,_,_,_ in loc:out.append(f'(pin {q(number)} (uuid {q(uid(ref+"-pin-"+number))}))')
  out.append(f'(instances (project "fan_robot_mainboard"(path {q(p["sheet_path"])}(reference {q(ref)})(unit 1)))))')
  for number,px,py,ang in loc:
   xx=x+px;yy=y-py;net=p['pins'][number]['net']
   if net:
    ex=xx+(-5.08 if ang==0 else 5.08)
    out.append(f'(wire(pts(xy {xx:.4f} {yy:.4f})(xy {ex:.4f} {yy:.4f}))(stroke(width 0)(type default))(uuid {q(uid(ref+"wire"+number))}))')
    out.append(label(net,ex,yy,ang))
   else:out.append(f'(no_connect (at {xx:.4f} {yy:.4f})(uuid {q(uid(ref+"NC"+number))}))')
 if name=='power':
  for i,net in enumerate(['GND','VBAT','VLOGIC_IN','USB_VBUS']):
   x=69.85+i*129.54;y=393.7;ref='#FLG0'+str(i+1)
   out.append(f'(symbol(lib_id "FanRobot:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid {q(uid(ref))})'+prop('Reference',ref,x,y,True)+prop('Value','PWR_FLAG',x,y-5)+f'(instances(project "fan_robot_mainboard"(path {q("/"+rootid+"/"+sid)}(reference {q(ref)})(unit 1)))))')
   out.append(label(net,x,y))
 out.append('(embedded_fonts no))');(EDA/(name+'.kicad_sch')).write_text('\n'.join(out)+'\n')
root=header('Mainboard',rootid,'A4');root.append('(lib_symbols)')
for i,(name,_) in enumerate(groups):
 x=30+(i%2)*125;y=40+(i//2)*75;sid=uid('sheet-'+name)
 root.append(f'(sheet(at {x} {y})(size 90 42)(fields_autoplaced)(stroke(width 0)(type default))(fill(color 0 0 0 0))(uuid {q(sid)})'+prop('Sheetname',name,x+5,y-2)+prop('Sheetfile',name+'.kicad_sch',x+5,y+44)+f'(instances(project "fan_robot_mainboard"(path {q("/"+rootid)}(page {q(str(i+2))})))))')
root.append('(sheet_instances(path "/"(page "1")))(embedded_fonts no))');(EDA/'fan_robot_mainboard.kicad_sch').write_text('\n'.join(root)+'\n')
(ROOT/'design/circuit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
pro={'board':{'design_settings':{'rules':{'min_clearance':0.15,'min_track_width':0.15,'min_via_annular_width':0.1,'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_copper_edge_clearance':0.3,'min_hole_clearance':0.25,'min_hole_to_hole':0.25,'min_silk_clearance':0.1,'min_silk_text_height':0.7,'min_silk_text_thickness':0.1},'rule_severities':{}}},'net_settings':{'classes':[{'name':'Default','clearance':0.15,'track_width':0.2,'via_diameter':0.6,'via_drill':0.3,'diff_pair_width':0.2,'diff_pair_gap':0.15}]},'meta':{'filename':'fan_robot_mainboard.kicad_pro','version':1}}
(EDA/'fan_robot_mainboard.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
with (ROOT/'design/pin_net_map.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Ref','Physical_pad','Pin_name','Net','Electrical_type'])
 for p in parts:
  for n,pin in p['pins'].items():w.writerow([p['ref'],n,pin['name'],pin['net'] or 'NC',pin['type']])
print('Native KiCad sheets generated with typed IC pins, 4 documented incoming-power flags, and embedded local symbols.')
