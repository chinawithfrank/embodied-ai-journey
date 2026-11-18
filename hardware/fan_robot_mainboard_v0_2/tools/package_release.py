"""Package verified manufacturing data and editable sources with separate manifests."""
from pathlib import Path
import json,hashlib,zipfile,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Fail closed on final native checks and exported data validation.
erc=(ROOT/'checks/erc.rpt').read_text();drc=(ROOT/'checks/final-drc.rpt').read_text()
assert re.search(r'ERC messages: 0\s+Errors 0\s+Warnings 0',erc)
assert '** Found 0 DRC violations **' in drc and '** Found 0 unconnected pads **' in drc and '** Found 0 Footprint errors **' in drc
for name in ['data-consistency.json','manufacturing-audit.json']:assert json.loads((ROOT/'checks'/name).read_text())['status']=='PASS'
# Verify exported-data evidence is tied to the current source, not stale reports.
a=json.loads((ROOT/'checks/manufacturing-audit.json').read_text())
for name,wanted in a['source_sha256'].items():assert sha(ROOT/name)==wanted,name
fab=ROOT/'fabrication/PCB_Gerber_V0.2.zip'
with zipfile.ZipFile(fab,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((ROOT/'fabrication/gerber').iterdir()):
  if p.suffix.lower() in ['.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gm1','.drl','.gbrjob']:z.write(p,p.name)
assert len(zipfile.ZipFile(fab).namelist())==12
manifest={'project':'FanRobot Mainboard','revision':'0.2','release':'ENGINEERING_PROTOTYPE_FAB_READY','purpose':'Small first-prototype fabrication and assembly; not physically validated production release','board_mm':[60,50],'copper_layers':4,'nominal_thickness_mm':1.6,'finish':'ENIG','population':{'SMT_top':60,'SMT_bottom':16,'THT_top':5,'DNP':['C10','J7','J8'],'test_pads_no_purchase':11},'checks':{'ERC':0,'DRC':0,'unconnected_pads':0,'schematic_parity_issues':0,'data_consistency':'PASS','independent_manufacturing_parse':'PASS'},'pcb_sha256':sha(ROOT/'eda/fan_robot_mainboard.kicad_pcb'),'gerber_zip_sha256':sha(fab),'firmware':'Not modified or supplied; new-board port required','factory_status':'No order, payment, CAM/DFM acceptance or assembly orientation approval obtained','physical_validation_pending':['loaded motor start/current','battery droop and supply transients','temperature','camera PID and mating orientation','USB and RF in enclosure','firmware port/interlock/reset tests'],'packages':['PCB_Gerber_V0.2.zip','FanRobot_Mainboard_V0.2_MANUFACTURING.zip','FanRobot_Mainboard_V0.2_SOURCE.zip']}
(ROOT/'release-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
# Root manifest covers every source/deliverable in this directory.
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS.txt','.DS_Store'] and not p.name.endswith('.kicad_prl'))
(ROOT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files))
# Manufacturing-only archive avoids route intermediates and component-selection source files.
selected=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or p.name=='.DS_Store':continue
 rel=p.relative_to(ROOT).as_posix()
 if rel in ['README.md','release-manifest.json'] or rel.startswith(('fabrication/','assembly/','design/01-','design/02-','design/03-','design/04-','checks/erc.rpt','checks/final-drc.rpt','checks/data-consistency.json','checks/manufacturing-audit.json','checks/drill-report.txt')):selected.append(p)
mfg=OUT/'FanRobot_Mainboard_V0.2_MANUFACTURING.zip'
with zipfile.ZipFile(mfg,'w',zipfile.ZIP_DEFLATED) as z:
 prefix='FanRobot_Mainboard_V0.2/'
 for p in sorted(selected):z.write(p,prefix+p.relative_to(ROOT).as_posix())
 z.writestr(prefix+'SHA256SUMS.txt',''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in sorted(selected)))
source=OUT/'FanRobot_Mainboard_V0.2_SOURCE.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file() and p.name!='.DS_Store' and not p.name.endswith('.kicad_prl'):z.write(p,'fan_robot_mainboard_v0_2/'+p.relative_to(ROOT).as_posix())
# Verify actual archive CRCs, no duplicate paths, and all per-archive checksums.
for p in [fab,mfg,source]:
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None,p
  names=z.namelist();assert len(names)==len(set(names)),p
  for manifestname in [n for n in names if n.endswith('/SHA256SUMS.txt')]:
   prefix=manifestname[:-len('SHA256SUMS.txt')]
   for line in z.read(manifestname).decode().splitlines():
    digest,name=line.split('  ',1);assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest,(p,name)
 print(str(p),p.stat().st_size,'bytes,CRC+manifest PASS')
(OUT/'FanRobot_Mainboard_V0.2_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in [fab,mfg,source]))
