"""Build the editable board; route critical local loops explicitly before autorouting."""
from pathlib import Path
import pcbnew as k,json,os,math
import wx
app=wx.App(False)
plugin=k.PCB_IO_KICAD_SEXPR()
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda';FPLIB=EDA/'FanRobot.pretty'
mm=k.FromMM
def xy(x,y):return k.VECTOR2I(mm(x),mm(y))
def line(fp,x1,y1,x2,y2,layer,width=.1):
 s=k.PCB_SHAPE(fp);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(x1,y1));s.SetEnd(xy(x2,y2));s.SetLayer(layer);s.SetWidth(mm(width));fp.Add(s)
def rect(fp,x1,y1,x2,y2,layer):
 for a,b,c,d in [(x1,y1,x2,y1),(x2,y1,x2,y2),(x2,y2,x1,y2),(x1,y2,x1,y1)]:line(fp,a,b,c,d,layer,.05 if layer==k.F_CrtYd else .1)
def layers(*ids):
 l=k.LSET()
 for v in ids:l.AddLayer(v)
 return l
def custom(name,w,h,pads,desc):
 f=k.FOOTPRINT(None);f.SetFPID(k.LIB_ID('FanRobot',name));f.SetReference('REF**');f.SetValue(name);f.SetAttributes(k.FP_SMD);f.SetLibDescription(desc)
 f.Reference().SetPosition(xy(0,-h/2-1));f.Reference().SetTextSize(xy(.8,.8));f.Reference().SetTextThickness(mm(.12))
 f.Value().SetLayer(k.F_Fab);f.Value().SetVisible(False)
 rect(f,-w/2,-h/2,w/2,h/2,k.F_Fab);rect(f,-max(w/2,1.2)-.25,-h/2-.25,max(w/2,1.2)+.25,h/2+.25,k.F_CrtYd)
 for n,x,y,px,py in pads:
  p=k.PAD(f);p.SetNumber(str(n));p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_ROUNDRECT);p.SetRoundRectRadiusRatio(.2);p.SetPosition(xy(x,y));p.SetSize(xy(px,py));p.SetLayerSet(layers(k.F_Cu,k.F_Paste,k.F_Mask));f.Add(p)
 line(f,-w/2,-h/2,-w/2+.4,-h/2,k.F_SilkS,.12)
 plugin.FootprintSave(str(FPLIB),f)
custom('TPS63802_DLA0010A',2,3,[(n,-.9,-1+(n-1)*.5,.6,.25) for n in range(1,6)]+[(n,.55 if n==8 else .75,1-(n-6)*.5,1.3 if n==8 else .9,.25) for n in range(6,11)],'TI DLA0010A; SLVSEU9D package drawing4223750/D: pins1-5 x=-0.9,w0.6;6,7,9,10 x0.75,w0.9;GND8 x0.55,w1.3; all h0.25,pitch0.5. Body2x3mm; NOT generic DFN with EP.')
custom('L_Murata_DFE201612E',2.2,1.8,[(1,-.8,0,.8,1.8),(2,.8,0,.8,1.8)],'Murata O05E Jan2019 standard land table: gap a0.8,overall b2.4,pad height c1.8; body2.0+/-0.2 x1.6+/-0.2 x1.2mm.')
# Manufacturer ground lands may use small thermal vias; exact local footprint edits are explicit.
f=plugin.FootprintLoad(str(FPLIB),'ESP32-S3-WROOM-1')
for p in f.Pads():
 if p.GetAttribute()==k.PAD_ATTRIB_PTH:
  p.SetDrillSize(xy(.3,.3)) # keep0.6mm annulus, common drill process
plugin.FootprintSave(str(FPLIB),f)
# Remove silk-only line primitives in text, avoiding mutable SWIG iterator ownership.
import re
def remove_silk(text):
 spans=[]
 for match in re.finditer(r'\(fp_(?:line|arc|circle|poly|rect|text)\b',text):
  i=match.start();depth=0;quoted=False;escaped=False
  for j in range(i,len(text)):
   c=text[j]
   if quoted:
    if escaped:escaped=False
    elif c=='\\':escaped=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:
     block=text[i:j+1]
     if re.search(r'\(layer "[FB]\.SilkS"\)',block):spans.append((i,j+1))
     break
 for a,b in reversed(spans):text=text[:a]+text[b:]
 return text
for path in FPLIB.glob('*.kicad_mod'):path.write_text(remove_silk(path.read_text()))
d=json.loads((ROOT/'design/circuit.json').read_text());b=k.BOARD();b.SetCopperLayerCount(4)
ds=b.GetDesignSettings();ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.15);ds.m_ViasMinSize=mm(.6);ds.m_MinThroughDrill=mm(.3);ds.m_CopperEdgeClearance=mm(.3);ds.m_HoleClearance=mm(.25)
ds.SetAuxOrigin(xy(0,50));ds.SetGridOrigin(xy(0,0))
nets={}
for name in sorted({pi['net'] for p in d['parts'] for pi in p['pins'].values() if pi['net']}):
 net=k.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
positions={
 'U1':(30,12.75,0),'U2':(11,11.5,90),'L1':(11,8.5,0),'C2':(8.5,10.75,180),'C3':(14.5,10.75,0),'C4':(15,13.5,0),
 'R2':(12.5,14.5,90),'R3':(10.5,14.5,270),'R4':(7.5,14.5,90),'R5':(5.5,14.5,270),'C5':(5.5,12.1,0),
 'C11':(18,8.5,0),'C12':(18,10.8,0),'R6':(18,13,0),'C6':(18,15.5,0),'SW2':(16.8,19,0),'SW3':(16.8,23.5,0),'R9':(26,28,0),
 'J6':(3.9,21,-90),'U5':(11,21,0),'R24':(14.7,20,0),'R25':(14.7,22,0),'R22':(5,27.5,90),'R23':(7,27.5,90),'R26':(2.5,28.5,90),
 'C20':(10.5,25.4,0),'U8':(15,27.5,90),'R30':(17.7,27.5,90),'C23':(15,30.6,0),'C24':(12,27.7,90),'D3':(9,31.5,0),'D2':(10.8,17,0),
 'J1':(4.5,43,0),'F1':(5,37.5,90),'Q2':(10,37,0),'R1':(8.5,35,0),'Q3':(13.7,37,0),'R29':(14,34.4,0),'C1':(19.5,38.5,0),'SW1':(4,33,-90),
 'U4':(47,19.8,0),'RS1':(42,17.8,90),'RS2':(42,22.3,90),'R15':(52,16,0),'R16':(52,18,0),'R17':(46,27,0),'R18':(46,29.1,0),'R19':(42.5,26,0),
 'C16':(55,19.8,90),'C17':(52,20.2,0),'C18':(48,24.5,0),'C19':(47.6,14.5,0),'J2':(54,10,0),'J3':(54,25,0),
 'R10':(42,7.8,0),'R11':(42,10,0),'C13':(42,12.2,0),
 'U6':(31,29,0),'C14':(31,31.3,0),'R12':(27,29.9,0),'R13':(27,32,0),'U7':(36,29,0),'C15':(36,31.3,0),'R14':(39.4,29,0),
 'U3':(47,37,180),'L2':(43,36,0),'C7':(40.8,40,90),'C8':(47,39.8,0),'C9':(54,43,0),'R7':(46,41.9,0),'R8':(42.5,42,0),'C10':(49.5,41.9,0),
 'Q1':(49,34,0),'R20':(45.5,31.7,0),'R21':(49,30.8,0),'D1':(55,40,0),'J4':(54,34,0),
 'J5':(26,44,90),'C21':(23,45,90),'C22':(23,41.7,0),'J7':(28,34.5,90),'J8':(26,38.5,90),'R27':(32,36.5,0),'R28':(36,36.5,0),
 'TP1':(3,46.5,0),'TP2':(11,42,0),'TP3':(17.5,5.5,0),'TP4':(58,42.5,0),'TP5':(24,30,0),'TP6':(38.7,33.5,0),'TP7':(43,29,0),'TP8':(46,8,0),'TP9':(2,15,0),'TP10':(18,5.5,0),'TP11':(19,29.5,0)
}
# Placement refinement after real courtyard/NPTH checks.
positions.update({'C2':(7.4,10.75,180),'C5':(3.2,12.5,180),'D2':(12,17,0),'SW2':(13,48,0),'SW3':(18.5,47.5,0),'R22':(10,24.5,90),'R23':(10,26.7,90),'R26':(4,14.8,0),'F1':(12.5,44.5,0),'Q2':(10.2,37,0),'Q3':(14.5,37,0),'C1':(20.7,38.5,0),'C22':(23,41.7,0),'R16':(52.5,18,0),'R8':(43,42.1,0),'TP1':(9,48,0),'TP3':(18,13.3,0),'TP10':(18,16.5,0),'TP9':(2,12.5,0)})
positions.update({'R4':(7.5,13.8,90),'R5':(5.5,13.8,270),'R26':(4,19.5,0),'U5':(11.4,21,0),'R24':(15,20,0),'R25':(15,22,0),'C20':(11.5,25.4,0),'C24':(12,28.3,90),'R22':(10,24,90),'R23':(12,24,90),'R27':(32,26.8,0),'R28':(36,26.8,0),'J7':(28,33,90),'J8':(25.5,39,90),'Q2':(10,37,0),'Q3':(14,37,0),'C1':(19.8,38.5,0),'R1':(8.5,35,0),'C7':(41.3,40,90),'R8':(43.5,40,0),'C8':(47.7,39.8,0),'R7':(46,41.55,0),'C10':(50,41.7,0),'RS1':(41.7,16.2,90),'RS2':(41.7,21.7,90),'C17':(52.7,20.2,0),'C16':(56,19.8,90),'C14':(31,31.3,0),'C15':(36,31.3,0),'R14':(39.8,29,0),'SW2':(30,22,0),'SW3':(37.5,22,0),'J1':(4,41,90),'SW1':(5,31.5,-90),'R6':(18.4,13.0,0)})
positions.update({'C1':(20.7,32,0),'Q2':(9.8,37,0),'Q3':(13.8,37,0),'R1':(12,33.8,0),'C24':(12,28,90),'R13':(27,29.5,0),'R8':(43.9,39.6,0),'R7':(46,41.25,0),'C8':(47.7,39.4,0)})
positions.update({'R13':(27,29.5,0),'C1':(20.7,32,0),'Q2':(9.8,37,0),'Q3':(13.8,37,0),'R1':(12,33.8,0),'C24':(12,28,90),'R8':(43.9,39.6,0),'R7':(46,41.25,0),'C8':(47.7,39.4,0),'C11':(18,8.5,180),'C12':(18,10.8,180)})
positions.update({'C23':(15,30.6,0),'R30':(15,27.5,0),'Q2':(10.2,37,0),'Q3':(14.3,37.5,0)})
positions.update({'U5':(12.2,21,0),'R24':(15.8,20,0),'R25':(15.8,22,0)})
positions.update({'R7':(46,41.25,180),'R8':(43.9,39.6,180),'C10':(46,41.25,0)})
positions.update({'RS1':(41.2,16.2,90),'RS2':(41.2,21.7,90)})
positions.update({'C1':(20.6,32,0)})
backside={'C10','C23','R30','R13','D2','R22','R23','SW1','C22','R26','R27','R28','R1','C14','C15','SW2','SW3'}|{ref for ref in positions if ref.startswith('TP')}

fps={}
for part in d['parts']:
 ref=part['ref'];f=plugin.FootprintLoad(str(FPLIB),part['footprint'].split(':')[1]);assert f,ref
 f.SetFPID(k.LIB_ID('FanRobot',part['footprint'].split(':')[1]));f.SetReference(ref);f.SetValue(part['value']);f.SetDNP(part['dnp']);f.SetPath(k.KIID_PATH(part['sheet_path']+'/'+part['schematic_uuid']))
 f.Reference().SetTextSize(xy(.7,.7));f.Reference().SetTextThickness(mm(.1));f.Reference().SetVisible(True);f.Value().SetVisible(False)
 if part['assembly']=='PCB_ONLY':f.SetAttributes(f.GetAttributes()|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES)
 x,y,a=positions[ref];f.SetOrientationDegrees(a);f.SetPosition(xy(x,y));b.Add(f)
 if ref in backside:f.Flip(xy(x,y),False)
 fps[ref]=f
 for pad in f.Pads():
  no=pad.GetNumber()
  if not no:continue
  assert no in part['pins'],(ref,no)
  net=part['pins'][no]['net']
  if net:pad.SetNet(nets[net])
 for key,val in [('MPN',part['mpn']),('LCSC',part['lcsc']),('Datasheet',part.get('source',''))]:
  f.SetField(key,val);field=f.GetField(key);field.SetVisible(False);field.SetLayer(k.B_Fab if ref in backside else k.F_Fab);field.SetPosition(f.GetPosition())
 # Reference placement kept small and on its own Fab side until final silk placement.
 f.Reference().SetLayer(k.B_Fab if ref in backside else k.F_Fab)
for i,(x,y) in enumerate([(3,3),(57,3),(3,47),(57,47)],1):
 f=plugin.FootprintLoad(str(Path(os.environ.get('FAN_KICAD_APP',Path.home()/'.local/share/fanrobot-eda/KiCad.app'))/'Contents/SharedSupport/footprints/MountingHole.pretty'),'MountingHole_2.7mm_M2.5')
 f.SetReference('H'+str(i));f.SetPosition(xy(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False);f.SetAttributes(k.FP_BOARD_ONLY|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES);b.Add(f)
for (x1,y1,x2,y2) in [(0,0,60,0),(60,0,60,50),(60,50,0,50),(0,50,0,0)]:
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(x1,y1));s.SetEnd(xy(x2,y2));s.SetLayer(k.Edge_Cuts);s.SetWidth(mm(.05));b.Add(s)
def text(s,x,y,size=.8,layer=k.F_SilkS):
 t=k.PCB_TEXT(b);t.SetText(s);t.SetPosition(xy(x,y));t.SetTextSize(xy(size,size));t.SetTextThickness(mm(.12));t.SetLayer(layer);b.Add(t)
text('FAN ROBOT V0.2',30,48.8,.8);text('3x1.5V',9,48.8,.8);text('NO CHARGING',49,48.8,.8)
# Real pin coordinates recorded for routing and interface review.
coords={}
for ref,f in fps.items():
 for pad in f.Pads():
  if pad.GetNumber():coords.setdefault(ref,{})[pad.GetNumber()]=[round(k.ToMM(pad.GetPosition().x),4),round(k.ToMM(pad.GetPosition().y),4),pad.GetNetname()]
(ROOT/'design/placed-pad-coordinates.json').write_text(json.dumps(coords,indent=2)+'\n')
b.BuildConnectivity();k.SaveBoard(str(EDA/'fan_robot_mainboard.kicad_pcb'),b)
print('Placed',len(fps),'electrical references and4 mounting holes on60x50mm,4-layer board. Routing not complete.')
