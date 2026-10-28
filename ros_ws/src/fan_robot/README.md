# 风扇机器人实验代码

学习过程和完整启动步骤见 [风扇机器人笔记](../../../notes/04-Fan-Robot/README.md)，第一节是 [ESP32-S3 + OV2640 相机取流](../../../notes/04-Fan-Robot/01-ESP32-Camera/README.md)。

| 路径 | 用途 |
|---|---|
| `firmware/esp32_camera/esp32_camera.ino` | 烧录到 ESP32-S3 的 Arduino 固件：状态、JPEG 拍照、MJPEG 视频、中文预览页 |
| `firmware/esp32_camera/camera_config.example.h` | 独立 DVP 模块的拟定配置；不是已确认的板载相机引脚 |
| `firmware/esp32_camera/camera_config.onboard_clock.example.h` | 无 XCLK 引出、使用转接板时钟时的候选配置；默认禁止初始化，频率待查 |
| `firmware/esp32_camera/camera_config.by_ov2640_v15.example.h` | 当前BY-OV2640-V1.5专用模板：原理图确认板载24MHz，仍需读者确认自己的接线 |
| `tools/camera_client.py` | 电脑上的 Python 检查、拍照和可选 OpenCV 预览工具 |
| `tools/tests/` | 不连接实物也能运行的 HTTP 客户端测试 |
| `firmware/esp32_hand/` | ESP-IDF 离线手部检测：Flash 内模型、本机推理、串口坐标、可选热点预览 |
| `firmware/tests/hand_observation_test.cpp` | 手部框、最高置信度、归一化偏差及过期结果清空的主机测试 |

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

这不是已经实现强化学习或电机控制的整机程序，也不是需要 `colcon build` 的 ROS2 包。第一节相机固件由 Arduino 工具链编译，第二节离线手部检测由 ESP-IDF 编译；Python 相机工具直接运行。`firmware/COLCON_IGNORE` 防止 ROS2 构建扫描进入嵌入式工程。代码在工作空间中，不代表它必须运行在 ROS2 上。后续可在本目录下增加真正的 ROS2 相机桥接包。
