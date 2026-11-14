EESchema Schematic File Version 4
LIBS:fan_robot
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 5
Title "FanRobot 3xAA integrated mainboard"
Date "2026-11-14"
Rev "0.1-NOT-FOR-FAB"
Comp "Engineering review source"
Comment1 "Electrical design draft: NO Gerber, placement, ERC or DRC release"
Comment2 "60x50mm, 4 layers; camera 2x9 pitch/row 2.54mm; verify sensor PID"
Comment3 "Legacy KiCad source requires import and manufacturer library review"
Comment4 ""
$EndDescr
$Sheet
S 2000 2000 2500 1000
U B0000000
F0 "power" 50
F1 "power.sch" 50
$EndSheet
$Sheet
S 6000 2000 2500 1000
U B0000001
F0 "mcu_camera" 50
F1 "mcu_camera.sch" 50
$EndSheet
$Sheet
S 2000 4000 2500 1000
U B0000002
F0 "actuators" 50
F1 "actuators.sch" 50
$EndSheet
$Sheet
S 6000 4000 2500 1000
U B0000003
F0 "usb_expansion" 50
F1 "usb_expansion.sch" 50
$EndSheet
$EndSCHEMATC
