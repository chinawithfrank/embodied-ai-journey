from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];EDA=ROOT/'eda'
b=k.LoadBoard(str(EDA/'critical-routed.kicad_pcb'))
assert k.ImportSpecctraSES(b,str(EDA/'fan_robot_mainboard.ses'))
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
k.SaveBoard(str(EDA/'fan_robot_mainboard.kicad_pcb'),b)
print('Imported routes and refilled power/ground zones; run KiCad DRC before any release.')
