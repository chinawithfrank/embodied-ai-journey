FanRobot V0.5 单面布线工程草案｜72 × 60 mm｜禁止投板 / NOT FOR FABRICATION
打开 eda/fan_robot_mainboard.kicad_pro。原 V0.3 双面发布件和 V0.4 草案均保留。本目录不含 PCB 下单包。

新板以 KiCad 左上方为参考：外形 x=-6..66、y=0..60，厚度标称1.6；保留 4×Ø2.7 孔，中心仍为 (3,3)、(57,3)、(3,47)、(57,47)。相对旧板左右各加6，朝相机排针的一边加10。ESP32、电机驱动、两路电源和相机接口保持原电气分配。J5 改面后须按新图核对针1和线束方向。不应复用旧 CPL/BOM。

电气：顶层600个走线段、1个地铜区，无走线过孔、无背面贴片。KiCad 源文件仍有默认 F/B 工作叠层和通孔焊盘定义；尚非经制造审核的单铜层叠层。保留天线禁布区。以附带 KiCad 原生项目及封装库为权威快照。
RJ1/RJ2/RJ3 是真实需装的 1206 0Ω，位于 ACT_EN、FAN_GATE_LOGIC、M_AIN1 逻辑信号上。crossovers 原理图页记录实际器件；PCB 原生 jumper_pad_groups 指定两座焊盘由安装后的器件导通。未把电池、电机和散热回流当作逻辑跨接。料号 1206W4F0000T5E，LCSC C17888：https://www.lcsc.com/product-detail/C17888.html 。checks/crossovers.csv 是增量物料表，不是完整贴片BOM。

生产门槛：ERC 为0、PCB与原理图一致。PCB原生DRC目前仍报告63处未连接；检查退出码5，不通过。checks/open-connections.csv 按真实网络和两端坐标列出全部断点。检查命令：
kicad-cli pcb drc --all-track-errors --schematic-parity --exit-code-violations -o checks/drc.rpt eda/fan_robot_mainboard.kicad_pcb
检查报告里的“0 DRC violations”不含另行统计的未连接项，不代表放行。禁止将草案或删去底层的V0.3文件上传下单。下一步须在当前板框内逐组完成相机并口、USB数据差分、电机输出/采样和地回流布局；复查单层回流通道宽度、电流/热、天线和厂家单面焊盘/孔工艺。全部通过后重新生成和独立核对 Gerber/钻孔/BOM/CPL。

外壳：enclosure/FanRobot-R2-with-board.step 是带板装配参考；enclosure/STL 是试装打印件，05 压板打印2件。板上贴片朝壳底、插件朝上，USB位于机身右侧。孔柱距内底12，打印底盘外轮廓仍为84×166。裸板和已有器件STEP与打印件的实体干涉检查见 enclosure/fit-check.json。不是全实物装车通过。STEP中缺少 U4、SW1、J6、F1、C1、L1、U2 实体；未测试螺钉、USB插头外形、相机线、插拔路径、履带、电池盒和电机实物。风扇支架仍按60 mm方框/50 mm孔距试装。如原型尚未定型，请勿提前批量打印外壳。
