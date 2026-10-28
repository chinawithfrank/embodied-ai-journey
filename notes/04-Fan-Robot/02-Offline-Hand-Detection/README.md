[← 风扇机器人](../README.md) · **中文** | [English](README.en.md)

# 不把画面送到电脑：让 ESP32 自己找到手

上一节，浏览器里终于出现了 OV2640 的真实画面。那时是我在看画面，开发板还不知道画面中有什么。这次我把目标收窄了一点：先不追气球、不训练小网球，也不让轮子动，只问一个问题——**手在哪里？**

最初想复用电脑上的网球 YOLO 模型，但最终产品不能一直带着电脑，也不能靠云服务。把 Python 推理程序放进 ESP32 并不是简单换个运行位置：运行环境、内存和模型格式都不同。现在改用乐鑫提供的量化手部检测模型，由 ESP32-S3 完成取图、解码和推理。

## 这一次交付什么

```text
OV2640 → JPEG 320×240 → ESP32 解码 RGB888 → HandDetect → 框、置信度、中心、偏差
                                                          ├→ 串口结果
                                                          └→ 可选本地热点预览
```

- **检测的是“手”**，不是判断“是不是我的手”，也没有实现 21 个手部关键点或握拳、点赞等手势分类。
- 模型和程序一起写进 Flash。运行时不需要电脑、互联网、路由器或云端账户。初始化工具链和首次下载依赖时仍需要联网。
- 默认保留一个本地热点方便验收，手机只画框，不做推理。关闭网页、断开所有手机，开发板仍持续检测。也可编译成完全关闭 Wi-Fi 的版本。
- 本实验没有电机、舵机或风扇输出。识别错了也不会驱动机构。

手和网球的识别复杂度不完全一样。这里能直接做手，是因为已有适合 S3 的预训练模型，不必先收集你的手或给网球重新标注。至于你的实际光照、手的大小、遮挡和背景能否稳定识别，仍要实测，而不是把有模型等同于可靠。

## 代码在哪里，为什么这次不是 Arduino 草图

新工程：[`firmware/esp32_hand`](../../../ros_ws/src/fan_robot/firmware/esp32_hand)。原来的 [`esp32_camera`](../../../ros_ws/src/fan_robot/firmware/esp32_camera) 保留不改；新固件是**替代刷写**，不是两个程序同时运行。需要回退时，重新上传原相机草图即可。

为了使用官方模型组件，这次使用 ESP-IDF 构建 C++ 固件，不使用 Python，也不是 Arduino IDE 直接打开 `.ino` 的工程。电脑之前装的 PyTorch/Ultralytics 和网球 `best.pt` 均不参与这个固件，也不需要重新下载网球数据集。

| 文件 | 阅读时抓住什么 |
|---|---|
| `main/app_main.cpp` | 初始化相机；循环抓帧、解码、调用 `detector.run(image)`，再发布本帧结果 |
| `main/observation.hpp` | 只接受有效框；多只手取最高置信度；过期目标清空 |
| `main/idf_component.yml` | 固定依赖版本，避免依赖更新后 API 漂移 |
| `sdkconfig.defaults` | S3、16MB Flash、8MB OPI PSRAM、USB 串口和模型存储配置 |
| `main/Kconfig.projbuild` | 是否启用热点、置信度阈值与最小循环间隔 |

本工程固定 ESP-IDF **5.4.2**、`hand_detect` **0.1.2**、ESP-DL **3.3.4**、`esp32-camera` **2.1.3**。手部模型随组件下载，存储在 Flash rodata；无需 SD 卡，也没有运行时模型下载代码。不使用官方开发板 BSP 的固定引脚，继续用自己的接线。

## 1. 保持已跑通的接线

硬件仍是 ESP32-S3 N16R8 + BY-OV2640-V1.5。数据线 D0～D7 对应 GPIO4～11，SCL21、SDA18、VS16、HREF17、PCLK13、RST14、PWDN12，3.3V 供电、共地、FLASH 不接。板载 24MHz 时钟，`xclk_pin = -1`，不要补接 GPIO15。原生 USB 使用 GPIO19/20，不要拿来接相机。

新工程直接复用 `firmware/esp32_camera/camera_config.local.h` 的引脚、时钟和镜像配置；**不会覆盖该私有文件**。你当前已经跑通视频的配置可继续用。其他读者若还没有本地文件：复制同目录的 `camera_config.by_ov2640_v15.example.h` 为 `camera_config.local.h`，逐条核对自己的接线后再把 `wiring_confirmed` 改为 `true`。不要把现有文件覆盖掉。

这里不读取旧配置中的家用 Wi-Fi 名称/密码；新热点名是 `FanRobot-Hand`，密码 `fanrobot123`。仅限可信本地调试，不要映射公网端口。

## 2. 准备 ESP-IDF，一次性完成

若已安装 ESP-IDF 5.4.2，在新终端激活它即可。**不要在 YOLO 的 `.venv` 或 ROS2 已配置的终端里安装另一套 Python 环境。** 下面假设从家目录安装，仓库已克隆到本机：

```bash
mkdir -p ~/esp
cd ~/esp
git clone --branch v5.4.2 --depth 1 --recursive --shallow-submodules \
  https://github.com/espressif/esp-idf.git esp-idf-v5.4.2
cd esp-idf-v5.4.2
./install.sh esp32s3
. ./export.sh
idf.py --version
```

macOS 与 Ubuntu 安装前置依赖不同，缺工具时按 [ESP-IDF 官方安装指南](https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32s3/get-started/index.html) 补齐。安装目录已存在时，不要重复克隆覆盖。后续每次新开终端，运行 `. ~/esp/esp-idf-v5.4.2/export.sh` 即可，不必重装。

## 3. 编译、上传和观察

从**仓库根目录**开始。Mac 本仓库根目录是 `/Users/lichuang/Develop/team/embodied-ai-journey`；Ubuntu 按自己的克隆位置进入即可。

```bash
cd ros_ws/src/fan_robot/firmware/esp32_hand
idf.py set-target esp32s3
idf.py build
```

首次构建会下载组件和模型，耗时可能明显高于之前的相机草图。关闭 Arduino 串口监视器，仍连接之前用成功的**非 TTL 原生 USB 口**，查看串口：

```bash
# macOS
ls /dev/cu.usbmodem*
# Ubuntu
ls /dev/ttyACM*
```

下面把 `/dev/cu.usbmodemXXXX` 替换为刚查到的端口；Ubuntu 通常是 `/dev/ttyACM0`：

```bash
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

按 `Ctrl+]` 退出监视器。若自动进入下载模式失败，按住 BOOT，短按 RST，松开 BOOT，重新查看端口后再上传。不需要为此改相机接线。这个工程的 USB 控制台在 `sdkconfig.defaults` 中配置，不再去 Arduino 菜单找 CDC 开关。

串口会持续出现 `HAND {...}`。手进入视野时应看到 `found: true`、`target.center_px` 等字段；移出视野，下一有效帧应变成 `not_found`、`found: false`、`target: null`。框和坐标不会延续上一帧。

## 4. 看见框，确认不是“后台似乎在跑”

手机连接 `FanRobot-Hand`（没有互联网是正常的），打开 [本地识别页](http://192.168.4.1/)。画面上的绿色矩形和红色中心点来自开发板推理结果。页面不引用 CDN、不上传画面。一次只打开一个预览页。

先把手放在光照充足、背景简单的位置，手掌完整进入画面，不要贴到镜头上导致模糊。缓慢左右移动，再完全拿开。应依次看到“检测到手”和“没有检测到手”。网页通过 `/capture` 的 `X-Detection` 响应头获取**同一张 JPEG** 的结果，不拿另一帧的框叠到当前图像上。

`/state` 单独返回 JSON，适合后续调试控制逻辑；不是 ROS2 topic。默认不提供旧版 81 端口 MJPEG 视频或 `/health`，旧相机客户端的 `check/view` 不适用于新固件。

## 5. 验证“离线”而不是换了个云接口

1. 先保留串口监视器，断开手机和电脑到 `FanRobot-Hand` 的连接，不启动电脑推理程序。对着镜头移动手，确认串口仍更新 `frame_id` 和坐标。
2. 关闭手机移动数据，重新连开发板热点，页面仍可显示检测；这证明不依赖互联网，但仍使用本地 Wi-Fi 做显示。
3. 要连 Wi-Fi 射频也关闭：运行 `idf.py menuconfig` → `Fan robot: offline hand detector` → 取消 `Enable optional local Wi-Fi AP and browser preview`，保存，再 `idf.py build` 和 `idf.py -p 实际端口 flash monitor`。
4. 此时没有热点和网页，串口仍应输出检测结果。完全脱离电脑时可以只接可靠 USB 电源；没有屏幕时人看不到结果，不代表没有推理。之后执行机构会直接读取本地结果，不必经过串口或网络。

默认每轮至少间隔 400ms，即目标上限约 2.5 次/秒，不保证实际帧率。拍照、JPEG 解码、推理、预览都会花时间，串口 `processing_ms` 才是本机实际一轮耗时。它不是摄像头曝光时间测量，也不是严格的端到端控制延迟。

## 坐标怎么用于后续“只吹手”

像素原点在左上角，向右、向下为正。中心偏差使用：

```text
error_x = 2 × center_x / (width - 1) - 1
error_y = 2 × center_y / (height - 1) - 1
```

`error_x < 0` 表示手在左侧，`> 0` 在右侧；接近零说明目标靠近图像中线。多只手时只输出置信度最高的一只，不保证一直跟随同一个人。

**像素不是距离，框面积不是精确测距。** 后续还要校准相机视线与风扇吹风方向，加入目标丢失停止、急停、低速与输出限幅。不能直接把偏差乘到电机 PWM 上，更不能因检测到手就立即启动裸露扇叶。

## 问题出现时，从哪查

| 现象 | 优先检查 |
|---|---|
| `wiring_not_confirmed` | 是否复用到已经验证的私有配置；模板默认不允许启动 |
| `8mb_opi_psram_required` | 实际板型、OPI PSRAM 配置、供电，不要关闭保护绕过 |
| 图像正常但总是 `not_found` | 手是否清晰完整、足够大，先降低复杂背景；阈值默认 50%，可在 menuconfig 小幅调低比较误检 |
| `capture_failed` / `jpeg_decode_failed` | 供电、线长、接触和原相机实验是否仍正常，出错即清空目标 |
| `stale` | 距开始取帧超过 3 秒；旧坐标不可用，排查推理耗时或阻塞 |
| 网页消失但串口仍检测 | 是否关闭了预览配置，或热点初始化失败；网络不是识别循环的前提 |
| 误把物体看成手 | 收集失败画面，记录光照/姿态/阈值；不要宣称能识别“我的手”或所有手势 |

## 验收记录与边界

2026-10-27：在本机用上述固定版本完成带热点预览固件的完整编译，包含手部模型，程序大小 3,107,136 字节（约 2.96MiB），可放入 7MiB 应用分区。15 项主机测试通过，覆盖原相机客户端、时钟配置，以及新增的框合法性、阈值筛选、最高置信度选择、边界裁剪、中心偏差和过期清空。预览页 JavaScript 语法检查和本地文档链接检查通过。

关闭 `FAN_ENABLE_PREVIEW` 的独立配置也已完整编译通过，程序大小 2,554,688 字节（约 2.44MiB）。这是 Wi-Fi 不初始化的构建验证，不是“实物断网测试已通过”；后者仍需按上述步骤实际执行。生成的 `dependencies.lock` 保留在工程中，固定本次解析出的间接依赖版本。

**没有连接实物完成手部识别验收，不能把编译通过当成你的板子已经能识别。** 上传后应完成：手入镜/离镜、左右移动、遮挡、无手背景、两只手、关闭预览、断网、连续运行和供电重启检查，再考虑任何机构动作。

参考：[官方 HandDetect 组件](https://components.espressif.com/components/espressif/hand_detect/versions/0.1.2/readme)、[固定版本模型实现](https://github.com/espressif/esp-dl/tree/v3.3.4/models/hand_detect)、[ESP-DL 环境要求与模型部署说明](https://docs.espressif.com/projects/esp-dl/en/latest/getting_started/readme.html)。
