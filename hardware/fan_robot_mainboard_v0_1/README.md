# 桌面风扇机器人专用主板 V0.1 · 电气设计评审包

**状态：电气草案 / NOT FOR FABRICATION。不能将本压缩包上传到嘉立创当作 Gerber 生产文件。**

已按用户选择设计：ESP32 模组、电机驱动、风扇开关和电源全部集成，三节 1.5V 干电池串联，目标 PCB 60×50mm、四层。保留当前已跑通外接相机、两台6V/60rpm N20和两线风扇。相机2×9针、针距/排距均2.54mm已获用户确认；新照片OV5640丝印与原OV2640记录的差异需在新板验收以实物PID核实。当前共有 88 个器件/接口/测试点位号、66 个电气网络。并非 88 颗芯片。

## 已交付内容

| 文件 | 用途 |
|---|---|
| `eda/fan_robot_mainboard.sch` + 子页 + `fan_robot.lib` | 可供 KiCad 导入的 legacy 原理图草案；局部符号为显式针脚功能框，不是已认证的厂家 CAD 库 |
| `eda/fan_robot_mainboard.net` | KiCad XML 连接网表，无猜测的 PCB 封装与坐标 |
| `design/circuit.json` | 电路连接的机器可读源数据 |
| `design/pin_net_map.csv` | 每个器件的物理脚号、脚名和网络 |
| `assembly/BOM_REVIEW_ONLY.csv` | 初步逐位号 BOM；LCSC 编号留空，待准确选型/库存核验，不可直接贴片下单 |
| `design/01-design-spec.md` | 电气方案、设计边界、布局和制造要求 |
| `design/02-interfaces-and-firmware.md` | 接口、相机候选排针、必须做的固件移植 |
| `design/03-manufacturing-and-bringup.md` | 嘉立创交付要求、释放阻断项、样板测试步骤 |
| `design/04-rfq-message.txt` | 可复制给 PCB 设计工程师的设计/布板询价文字 |
| `design/placement-concept.svg` | 60×50mm 结构分区草图，非元件坐标文件 |
| `checks/consistency-report.txt` | 电气数据一致性检查；不能代替 ERC、DRC、DFM、SI/PI 或样板测试 |
| `design/hardware-inputs.json` | 已确认2.54mm针距/排距、6V/60rpm电机，以及尚未知的电流和配对器件参数 |
| `reference/2026-11-14-component-evidence.md` + 相机照片 | 最新核验结论、相机丝印差异与实物PID验收要求；11月13日记录作为历史保留 |
| `tools/` | 可复现的原理图/网表/BOM 生成和一致性检查脚本 |

## 如何使用

1. 给具备电路审查和 PCB 布局能力的硬件工程师本评审包，冻结选型、相机接口、电机限流和结构。
2. 工程师在 KiCad 导入原理图，或照网表在嘉立创 EDA 重建并复核；这不是嘉立创 EDA 原生工程，不能承诺一键导入。
3. 完成实际封装、四层 PCB 布局布线、ERC/DRC 与独立电气审查，导出 Gerber+钻孔、最终 BOM、贴片坐标和装配图。
4. 最终生产文件才提交嘉立创 PCB+SMT 服务。原理图设计/布板服务与工厂生产是不同范围，需单独确认，常规 PCB+SMT 不会自动替客户完成设计。
5. 少量打样（建议先评估 3～5 块，不是已下单数量），完成上电、供电、电机/风扇和射频验收后再扩大生产。

当前没有 PCB 布线文件、Gerber、钻孔生产文件或最终贴片坐标，没有做 KiCad ERC/DRC，也没有刷写或改变当前机器人固件。生成的原理图尚需在实际 KiCad 中导入检查，**未宣称已在 EDA 中成功打开**。本机未安装 KiCad，不能把内部脚本检查当成 EDA 验证。
