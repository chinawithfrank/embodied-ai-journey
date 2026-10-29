# 风扇机器人实验代码

学习过程和完整启动步骤见 [风扇机器人笔记](../../../notes/04-Fan-Robot/README.md)，第一节是 [ESP32-S3 + OV2640 相机取流](../../../notes/04-Fan-Robot/01-ESP32-Camera/README.md)。

| 路径 | 用途 |
|---|---|
| `firmware/esp32_camera/esp32_camera.ino` | 烧录到 ESP32-S3 的 Arduino 固件：状态、JPEG 拍照、MJPEG 视频、中文预览页 |
| `firmware/esp32_camera/camera_app.hpp` | 相机共用实现；原相机草图和新增手动电机草图复用，私有相机配置不变 |
| `firmware/esp32_camera/camera_config.example.h` | 独立 DVP 模块的拟定配置；不是已确认的板载相机引脚 |
| `firmware/esp32_camera/camera_config.onboard_clock.example.h` | 无 XCLK 引出、使用转接板时钟时的候选配置；默认禁止初始化，频率待查 |
| `firmware/esp32_camera/camera_config.by_ov2640_v15.example.h` | 当前BY-OV2640-V1.5专用模板：原理图确认板载24MHz，仍需读者确认自己的接线 |
| `tools/camera_client.py` | 电脑上的 Python 检查、拍照和可选 OpenCV 预览工具 |
| `tools/tests/` | 不连接实物也能运行的 HTTP 客户端测试 |
| `firmware/esp32_hand/` | ESP-IDF 离线手部检测：Flash 内模型、本机推理、串口坐标、可选热点预览 |
| `firmware/tests/hand_observation_test.cpp` | 手部框、最高置信度、归一化偏差及过期结果清空的主机测试 |
| `firmware/esp32_motor_manual/` | Arduino 相机加双N20手动点动；82端口控制、独立停机任务，默认电机禁用 |
| `firmware/tests/motor_guard_test.cpp` | 心跳/运行限时、旧会话与倒序命令拒绝、反转等待和引脚冲突测试 |

第三节：[保留相机，手动点动双N20](../../../notes/04-Fan-Robot/03-Manual-Motor-Control/README.md)。GPIO1/2/38/39接DRV8833的IN1/IN2/IN3/IN4，电机独立供电并共地；默认 `wiring_confirmed = false`，需确认电源和实际接线。相机80/81端口保留，手动控制在82端口；松开、断联或普通点动超过3秒会锁定。用户提供的模块说明确认J1默认拉高EEP、OUT1/2对应IN1/2、OUT3/4对应IN3/4，保留J1和 `sleep_pin = -1`。针对手工接线能转、40% PWM不起动的问题，另加单电机A持续高电平诊断，板端500ms限时，普通点动上限仍40%；操作前阅读第三节诊断步骤。用户补充的LR7843是开关而非电源，当前不加入电路。该Arduino固件不包含第二节的手部检测，不会根据画面自动驱动电机，也没有风扇输出。

供电计划已由用户确认：三节1.5V干电池串联标称4.5V，电池盒自带开关，用户已识别正负输出。ESP32/相机仍用原USB供电。单电机直接供电与手工控制输入已由用户确认能转，网页40%起动失败；新诊断和双电机共存待实测，示例配置默认禁用状态不因此改变。

新增实验：[ESP32 离线手部检测与完整刷写教程](../../../notes/04-Fan-Robot/02-Offline-Hand-Detection/README.md)。这次直接识别手，不使用电脑端网球 YOLO。新固件需要 ESP-IDF 5.4.2，不是 Arduino 草图；复用已有相机私有引脚配置，但刷写后替代旧固件。手部推理不需要电脑或互联网，可通过 menuconfig 关闭 Wi-Fi。默认可选热点为 `FanRobot-Hand`，不是旧相机的 `FanRobot-Camera`。实物检测效果仍需上传后验收。

手部固件的带预览版（约2.96MiB）和关闭Wi-Fi版（约2.44MiB）均已完整编译通过；15项主机测试通过。此记录不代表已经在实物上测得识别准确率、帧率或离线稳定性。

当前硬件：**ESP32-S3 N16R8 + 配套OV2640摄像头模块（BY-OV2640-V1.5）**。已根据用户补充的原理图确认：Y1为24MHz，其输出经R1连接SEN-MCLK，再到相机插座P1的MCLK；18针P2不引出XCLK。模块接3.3V，FLASH不接，不额外连接GPIO15。相机和模块排线按配套接口安装，不再以误传的OV5640商品图判断兼容性。

本机已按用户完成的接线将私有配置 `camera_config.local.h` 设置为 `wiring_confirmed = true`、`onboard_clock_confirmed = true`、`xclk_frequency_hz = 24000000`、`xclk_pin = -1`，需要重新编译上传才会在开发板上生效。该文件被Git忽略，不会把Wi-Fi密码提交到仓库。其他读者应复制专用示例并确认自己的接线；通用模板继续保留未确认保护，不把24MHz推广到其他板型。

已收到的实物反馈确认8MB PSRAM、热点网页及真实视频图像正常。完整固件已使用Arduino-ESP32 3.3.12及本地24MHz配置编译通过，由用户上传并验证浏览器取流；Python拍照及长时间稳定性尚待单独验收。串口和 `/health` 会显示配置的时钟来源/频率，用于确认是否刷入了新配置，不代表现场测量了时钟。

```bash
cd ros_ws/src/fan_robot
python3 tools/camera_client.py --url http://192.168.4.1 check
python3 tools/camera_client.py --url http://192.168.4.1 snapshot --output captures/first.jpg
python3 -m unittest discover -s tools/tests -v
```

这不是已经完成视觉闭环或强化学习的整机，也不是需要 `colcon build` 的 ROS2 包。第一节相机和第三节手动电机固件由 Arduino 工具链编译，第二节离线手部检测由 ESP-IDF 编译；Python 相机工具直接运行。`firmware/COLCON_IGNORE` 防止 ROS2 构建扫描进入嵌入式工程。代码在工作空间中，不代表它必须运行在 ROS2 上。后续可在本目录下增加真正的 ROS2 相机桥接包。
