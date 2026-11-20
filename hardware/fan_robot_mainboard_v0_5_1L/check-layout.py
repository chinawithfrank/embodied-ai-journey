"""Audit single-sided routing and summarize the native DRC. Not a fabrication exporter."""
from pathlib import Path
from collections import Counter
import json,re,pcbnew as k
r=Path(__file__).resolve().parent;b=k.LoadBoard(str(r/'eda/fan_robot_mainboard.kicad_pcb'))
tracks=Counter('via' if isinstance(t,k.PCB_VIA) else t.GetLayerName() for t in b.GetTracks())
zones=[z for z in b.Zones() if not z.GetIsRuleArea()]
assert set(tracks)=={'F.Cu'} and all(list(z.GetLayerSet().Seq())==[k.F_Cu] for z in zones)
d=(r/'checks/drc.rpt').read_text();issues=Counter(re.findall(r'^\[([^\]]+)\]',d,re.M))
report={'status':'NOT_FOR_FABRICATION','tracks':dict(tracks),'vias':0,'front_copper_pours':len(zones),'SMT_pads_on_back':sum(1 for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute()==k.PAD_ATTRIB_SMD and p.IsOnLayer(k.B_Cu)),'DRC_categories':dict(issues),'open_connections':issues['unconnected_items'],'native_stack_note':'KiCad retains F.Cu/B.Cu and standard through-hole pad stacks. Back routing forbidden; not an audited single-copper manufacturing stack.'}
assert report['SMT_pads_on_back']==0
(r/'checks/status.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
