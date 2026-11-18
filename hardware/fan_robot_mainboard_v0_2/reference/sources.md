# 设计依据与核验范围（2026-11-14）

以下是具体引脚、封装、参考电路和工艺设计的依据。网页/器件目录信息不代表下单时现货、贴装服务或实物测试通过。

- [ESP32-S3-WROOM-1/1U 数据表](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- [Espressif 硬件指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/index.html)
- [TI DRV8833](https://www.ti.com/lit/ds/symlink/drv8833.pdf)
- [TI TPS63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf)，DLA0010A 图4223750/D，非通用DFN封装
- [TI TPS61023](https://www.ti.com/lit/ds/symlink/tps61023.pdf)
- [TI TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf)，SLVS841G，限流电阻上下限公式
- [TI SN74LVC1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf)
- [AOS AO3400A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf)、[AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf)
- [ST USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)
- [Murata DFE201612E-R47M=P2](https://www.murata.com/en-us/products/productdetail?partno=DFE201612E-R47M%3DP2)：参数与 O05E 2019 标准焊盘表对照，gap0.8/overall2.4/height1.8mm
- [Wurth 74438357010 数据表](https://www.we-online.com/components/products/datasheet/74438357010.pdf)
- [Panasonic 10SVPE220M](https://industrial.panasonic.com/ww/products/pt/os-con/models/10SVPE220M)：220µF10V，2.7Arms@100kHz，ESR20mΩ，C6
- [Panasonic 推荐焊盘/回流](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL10.pdf)：C6 gap2.1/overall9.1/height1.6mm
- [C1 LCSC C165949](https://www.lcsc.com/product-detail/C165949.html)
- 其余具体 MPN/LCSC 逐项见 BOM_FULL.csv 和 circuit.json 的 source URL；分立料封装基于原厂资料与 KiCad10 官方封装库，修改见 footprint-provenance.json。
- [KiCad 库许可](https://www.kicad.org/libraries/license/)，CC BY-SA 4.0 带用于电路设计的例外。

用户已确认相机2×9、针距/排距2.54mm，电机6V/60rpm。相机照片/尺寸图保存在本目录。旧11月13/14日记录反映早期评审状态；本版实际工程状态以主README、检查报告和制造文件为准。照片OV5640丝印与历史OV2640工作配置不一致，首板仍读取PID，未宣称已经对新照片实物读取PID。
