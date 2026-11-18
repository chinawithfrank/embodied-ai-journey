# V0.2 工程工具说明

交付板已布线，打开工程无需执行脚本。Python pcbnew 使用 KiCad10 自带 Python，CLI 使用同版 kicad-cli。当前安装在 ~/.local/share/fanrobot-eda/KiCad.app，可用 FAN_KICAD_APP 指向其他安装路径。

已有最终板的安全校验/导出：

1. kicad-cli sch erc eda/fan_robot_mainboard.kicad_sch --exit-code-violations --output checks/erc.rpt
2. kicad-cli pcb drc eda/fan_robot_mainboard.kicad_pcb --all-track-errors --schematic-parity --exit-code-violations --output checks/final-drc.rpt
3. 普通 Python 运行 export_manufacturing.py（调用原生 CLI；重导出 PDF/Gerber/钻孔/BOM/CPL）。
4. KiCad Python 运行 export_assembly.py（只在 /tmp 制图副本，不改实际板），再运行 audit_release.py。
5. 额外 gerbonara/shapely 等依赖只用于独立制造解析和走线脚本，不是打开工程必需条件。完整源包含最终报告，SHA256SUMS 用于验证交付。

从零重建是另一条会覆盖PCB/原理图的开发流程：prepare_engineering.py → build_native_schematic.py → build_board.py → 原生导出 XML 网表 → route_critical.py → prepare_router.py → Freerouting1.9.0 → import_routes.py → finish_routes.py → finalize_board.py → 校验/导出。需要 pcbnew、shapely2、Java21/Freerouting1.9.0，并人工审查布线。finalize_board.py 是幂等元数据/标识整理；finish_routes.py 非幂等，只在原始路由导入后运行一次。自动生成脚本不等于已经验证所有未来修改，改板必须重新 ERC/DRC、数据核对与导出。

eda/critical-routed.kicad_pcb、DSN/SES 是中间路由工程，不是投板文件；eda/fan_robot_mainboard.kicad_pcb 才是当前完成板。base-circuit-v0_1.json 是生成器输入历史，不是当前发布网表。release 字段仅在最终检查、制造审核和打包完成时更新。
