# V0.3 工程工具说明

交付板已布线，打开工程无需执行脚本。Python pcbnew 使用 KiCad10 自带 Python，CLI 使用同版 kicad-cli。当前安装在 ~/.local/share/fanrobot-eda/KiCad.app，可用 FAN_KICAD_APP 指向其他安装路径。

已有最终板的安全校验/导出：

1. kicad-cli sch erc eda/fan_robot_mainboard.kicad_sch --exit-code-violations --output checks/erc.rpt
2. kicad-cli pcb drc eda/fan_robot_mainboard.kicad_pcb --all-track-errors --schematic-parity --exit-code-violations --output checks/final-drc.rpt
3. 普通 Python 运行 export_manufacturing.py（调用原生 CLI；重导出 PDF/Gerber/钻孔/BOM/CPL）。
4. KiCad Python 运行 export_assembly.py（只在 /tmp 制图副本，不改实际板），再运行 audit_release.py。
5. 额外 gerbonara/shapely 等依赖只用于独立制造解析和走线脚本，不是打开工程必需条件。完整源包含最终报告，SHA256SUMS 用于验证交付。

从零重建会覆盖PCB/原理图，只供工程维护：build_board.py → 导出原生 XML 网表 → route_critical.py（含电机B采样短路径）→ finalize_board.py → 重新保存 critical-routed.kicad_pcb 并导出 DSN → prepare_router.py → Freerouting2.5.0/Java25 → import_routes.py → finish_routes.py → 逐项修正路由器产生的缩颈和局部连接（本版 B 通道采样与输出最终路径见 checks/local-route-fixes.json 及实际板）并运行DRC → 校验/导出。finish_routes.py在路由后加双面地铜和经几何检查的地过孔；没有内层，也不使用四层电源平面。需要 pcbnew、shapely2；所有路由结果必须经过原生DRC与工程审查，不能因为脚本执行成功就投板。

本版交付的最终板已完成连接和检查，不能为“查看”再次运行重建脚本。prepare_engineering.py、build_native_schematic.py是从历史输入生成选型/符号的维护工具，不应覆盖当前已确认电路或板图。eda/critical-routed.kicad_pcb、DSN/SES都是中间文件，eda/fan_robot_mainboard.kicad_pcb才是最终双层板。

PCB自动识别入口只上传fabrication/PCB_Gerber_V0.3.zip；该ZIP含9个平铺文件，不带钢网、gbrjob或源工程，避免被识别为多个制板文件。完整MANUFACTURING/SOURCE压缩包用于人工工程沟通/编辑，不作为PCB自动上传文件。
