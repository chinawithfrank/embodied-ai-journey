import pcbnew as k,sys
from pathlib import Path
p=str(Path(__file__).resolve().parent/'eda/fan_robot_mainboard.kicad_pcb');b=k.LoadBoard(p)
assert k.ImportSpecctraSES(b,sys.argv[1])
assert all(not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.F_Cu for t in b.GetTracks())
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(p,b)
