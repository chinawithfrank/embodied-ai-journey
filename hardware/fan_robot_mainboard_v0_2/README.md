# 桌面风扇机器人主板 V0.2 - 工程样板投板包

本版已完成原生 KiCad 10 原理图、真实四层 PCB 布线和制造文件，可提交嘉立创进行工程审核、小批 PCB 打样及双面装配。板子尚未生产、上电或完成整机验证；本版不是已验证量产版。请使用 V0.2，V0.1 是旧评审资料。

| 项目 | 本版内容 |
|---|---|
| 外形 | 60×50mm，4 层，1.6mm，4 个 Ø2.7mm NPTH 安装孔 |
| 集成 | ESP32-S3-WROOM-1-N16R8、DRV8833 双桥、3.3V 升降压、5V 风扇升压/开关、USB-C 下载 |
| 供电 | 三节 1.5V 干电池串联；不充电；USB 只供逻辑/下载 |
| 装配 | 76 个 SMT + 5 个 THT；C10/J7/J8 不装；11 个测试点无需采购 |
| 检查 | ERC 0；DRC 0；未连接 0；原理图/PCB 一致性问题 0；BOM/CPL 实际板数据核对 PASS |
| 发布用途 | ENGINEERING_PROTOTYPE_FAB_READY；少量首板，非量产认证 |

## 提交哪些文件

- **只做裸板**：上传同目录 `fabrication/PCB_Gerber_V0.2.zip`，参数照 `fabrication/FABRICATION_NOTES.txt`。
- **做焊好器件的主板**：上传 Gerber，再分别导入 `assembly/BOM_JLC_SMT.csv` 和 `assembly/CPL_JLC.csv`；另把 `assembly/BOM_JLC_THT.csv` 及装配图交给工厂做 J1～J5 插件报价。插件焊接不是默认已包含在 SMT 内。
- 发给工厂的完整文件见仓库 `hardware/FanRobot_Mainboard_V0.2_MANUFACTURING.zip`，里面同时包含制造、BOM/CPL、装配/孔位图和投板说明。
- 本目录及 `FanRobot_Mainboard_V0.2_SOURCE.zip` 是可编辑源工程。使用 KiCad 10 打开 `eda/fan_robot_mainboard.kicad_pro`；根原理图为同名 `.kicad_sch`，实际布线板为同名 `.kicad_pcb`。这是 KiCad 工程，Gerber 可制造，不承诺嘉立创 EDA 原生工程导入。

## 下单时的正常工程确认

四层顺序必须是 F.Cu / In1.Cu / In2.Cu / B.Cu；双面贴片，加正面插件。先让工厂确认其可用叠层、封装方向、焊膏/散热过孔工艺及缺料处理。CPL 是真实 KiCad 原点/角度，不能假设所有元件的嘉立创物料库零度方向与 KiCad 相同：工厂需按装配图、原厂 1 脚和 `orientation-register.json` 核对。不允许只按预览图外形猜极性或自动换料。此处是下单工程审核说明，不代表已经联系或获得工厂承诺。

## 新板上电与固件

先按 `design/03-manufacturing-and-bringup.md` 用限流电源做首板检查，再连接相机、电机和风扇。现有机器人固件未修改或刷写；**旧固件不能直接当作这块新板的可运行固件**。新板改用 GPIO15 左电机 AIN1、GPIO1 电池 ADC，并增加 GPIO47 执行器使能和 GPIO42 故障输入，移植要求见 `design/02-interfaces-and-firmware.md`。工厂制造包没有烧录二进制，不包含自动运行测试服务。

电机/电池电流、启动掉压、温升、相机 PID 和无线性能需要首板实测。设计采用每路约 0.513A 名义限流作为保守初始值，不保证在三节干电池、75% PWM 下达到电机标签的 60rpm。照片的 OV5640 丝印与现有固件的 OV2640 PID 检查有差异，保留已跑通配置，验收时读取实物 PID。

## 文件和可复现检查

`checks/erc.rpt`、`checks/final-drc.rpt`、`checks/data-consistency.json` 和 `checks/manufacturing-audit.json` 为本次检查结果。`SHA256SUMS.txt` 用于检查交付完整性。工程脚本流程见 `tools/README.md`；不要为查看工程而运行生成脚本，重新放置会覆盖已完成的走线。
