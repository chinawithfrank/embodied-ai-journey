# 设计来源与核验范围

访问日期：2026-11-13。网页官方资料用于设计输入，不等于器件库存/板厂服务范围已确认。

- 嘉立创SMT交付文件要求：https://www.jlc.com/portal/server_guide_19326.html
- 嘉立创EDA下单流程：https://docs.lceda.cn/cn/PCB/Order-PCB/index.html
- Espressif ESP32-S3-WROOM-1/1U datasheet v1.8：https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf
- Espressif硬件设计指南：https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/index.html
- TI DRV8833 datasheet SLVSAR1E：https://www.ti.com/lit/ds/symlink/drv8833.pdf
- TI TPS63802 datasheet SLVSEU9D：https://www.ti.com/lit/ds/symlink/tps63802.pdf
- TI TPS61023 datasheet SLVSF14B：https://www.ti.com/lit/ds/symlink/tps61023.pdf
- TI SN74LVC1G08 datasheet：https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf
- AOS AO3400A：https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf
- AOS AO3401A：https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf
- ST USBLC6-2：https://www.st.com/resource/en/datasheet/usblc6-2.pdf
- 相机转接板布局/丝印：仓库 notes/04-Fan-Robot/01-ESP32-Camera/images/by_ov2640_layout.png
- 相机转接板原理图：仓库 notes/04-Fan-Robot/01-ESP32-Camera/images/by_ov2640_schematic.png
- 当前接线图与控制器配置：仓库 notes/04-Fan-Robot/wiring 与 ros_ws/src/fan_robot/firmware。

主要IC的物理针脚由上述原厂数据表核对。封装焊盘/天线禁布/叠层/电容有效值/电感电流/具体BOM料号尚未冻结，必须在EDA与实板中继续验证。没有使用未知同名芯片的商品图代替原厂数据表。

本轮用户提供资料（未作为原厂器件参数证明）：
- 相机尺寸裁剪原图：`camera-header-user-dimension.png`，板宽标注24mm、2×9针；节距/排距/插合朝向未直接标注。
- N20购买来源：https://item.taobao.com/item.htm?id=769096395403 。本次未能读取有效商品详情，未确认所选SKU、电压、转速或电流。
- 详细证据与待确认项：`2026-11-13-component-evidence.md`。

2026-11-14用户确认更新：
- 相机针距和两排中心距均2.54mm，2×9针。
- 实物正面照片 `camera-user-front-photo.png` 可见OV5640丝印，与历史OV2640记录冲突；以实物PID核验，不因照片改动现有驱动。
- 两台N20规格6V、60rpm（用户提供），电流/转速测试条件未知。
- 最新结论见 `2026-11-14-component-evidence.md`，机器可读输入见 `../design/hardware-inputs.json`。没有取得新的卖家数据表。
