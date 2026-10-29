**中文** | [English](README.en.md)

# 从零打造具身智能机器人

> 记录我从零开始打造真实世界 AI 机器人的旅程。

一个软件工程师踏入具身智能的旅程。

我花了很多年时间构建软件系统。
现在，我在学习如何打造能在物理世界中
感知、思考、行动的机器。

这个仓库正在记录了我的整个学习历程：
从 ROS2 基础 → 机器人仿真 → 感知 → AI 智能体 → 真实机器人 →

一切都是开源的。
一切都是一步步搭建起来的。

⭐ 如果你也在探索具身智能，欢迎 Star 这个仓库。

---

## 旅程地图

```
软件工程师 ──► ROS2 基础 ──► 仿真 ──► 感知 ──► AI 智能体 ──► 真实机器人
```

每一章都遵循同一个循环：**学习 → 构建 → 分享（Learn → Build → Share）**。
我遇到一个真实问题，学习背后的原理，动手搭建一个小东西来验证自己真的理解了，
然后原原本本地分享一路踩过的坑。

## 📚 章节目录

| # | 章节 | 状态 | 说明 |
|---|------|------|------|
| 00 | [为什么是具身智能](notes/00-Why-Embodied-AI) | ✅ 已发布 | 一个软件工程师为什么押注物理世界的智能 |
| 01 | [第一个月：机器人软件 Fundamentals](notes/01-Fundamentals) | ✅ 已完成 | 月度成果：ROS2 Web Gateway v0.1 |
| 01.1 | [ROS2 通信](notes/01-Fundamentals/01-ROS2-Communication) | ✅ 已发布 | Topic、Service、Action 与 Parameter 的边界和样例 |
| 01.2 | [TF2 与坐标系](notes/01-Fundamentals/02-TF2-And-Coordinate-Systems) | ✅ 已发布 | 静态/动态变换、查询与 TF 树 |
| 01.3 | [URDF 与 RViz](notes/01-Fundamentals/03-URDF-And-RViz) | ✅ 已发布 | 用 R2D2 验证模型、关节状态与 TF 如何共同驱动可视化 |
| 01.4 | [RViz Marker：基础形状](notes/01-Fundamentals/04-RViz-Markers) | ✅ 已发布 | 通过 `visualization_msgs/Marker` 在 RViz 显示循环基础形状 |
| 01.5 | [RViz Marker：点与线](notes/01-Fundamentals/04-RViz-Markers/02-Points-And-Lines) | ✅ 已发布 | 用 `POINTS`、`LINE_STRIP` 和 `LINE_LIST` 观察时序点集 |
| 01.6 | [rosbag2 与 MCAP](notes/01-Fundamentals/05-Rosbag2-And-MCAP) | ✅ 已发布 | 录制关节与 Marker 消息，并在 RViz 中回放一次运行 |
| 01.7 | [ROS2 Web Gateway v0.1](notes/01-Fundamentals/06-ROS2-Web-Gateway) | ✅ 已发布 | 在网页观察 ROS2 状态、创建/取消任务、查看日志并触发 MCAP 录制 |
| 02 | [第二个月：MoveIt 与机械臂运动规划](notes/02-MoveIt) | ✅ 已完成 | 月度成果：MoveIt Web Studio v0.1 |
| 02.1 | [第一个 MoveItPy 项目](notes/02-MoveIt/01-Your-First-MoveIt-Project) | ✅ 已发布 | 用 Python `MoveItPy` 为 Panda 规划并执行第一次末端位姿运动 |
| 02.2 | [在 RViz 中看懂一次规划](notes/02-MoveIt/02-Visualizing-In-RViz-With-Python) | ✅ 已发布 | 用 Python Marker、`DisplayTrajectory` 和分步服务可视化目标、轨迹与执行 |
| 02.3 | [纯 Python 绕障规划](notes/02-MoveIt/03-Planning-Around-Objects-With-Python) | ✅ 已发布 | 将 `CollisionObject` 同步到 MoveItPy 与 `move_group`，规划并执行绕开障碍物的轨迹 |
| 02.4 | [MTC 纯 Python 抓取放置](notes/02-MoveIt/04-Pick-And-Place-With-MTC-Python) | ✅ 已发布 | 用 MTC Python 阶段任务规划、检查并执行 Panda 的抓取与放置 |
| 02.5 | [MoveIt Web Studio](notes/02-MoveIt/05-MoveIt-Web-Studio) | ✅ 已发布 | 在网页创建受限抓取任务，用 Three.js 观察 Panda，用 MoveItPy 执行取放 |
| 03 | [第三个月：机器人视觉](notes/03-Vision) | 🚧 进行中 | 学习从相机画面中检测物体，并逐步连接到机器人坐标系 |
| 03.1 | [YOLO 网球识别与像素坐标](notes/03-Vision/01-YOLO-Tennis-Ball) | ✅ 已发布 | 训练单类别 YOLO 模型，在摄像头画面中识别网球并显示中心像素坐标 |
| 04 | [真实项目：风扇机器人](notes/04-Fan-Robot) | 🚧 进行中 | 从相机取流开始，逐步实现视觉闭环与强化学习实验 |
| 04.1 | [ESP32-S3 与 OV2640：第一双眼睛](notes/04-Fan-Robot/01-ESP32-Camera) | ✅ 浏览器取流已验证 | 板载24MHz、8MB PSRAM及网页视频已跑通；Python拍照与长时间稳定性继续验收 |
| 04.2 | [ESP32 离线手部检测](notes/04-Fan-Robot/02-Offline-Hand-Detection) | 🚧 待实物验收 | S3 本地模型输出手部框、中心与偏差；可选热点预览，也可关闭 Wi-Fi |
| 04.3 | [保留相机，手动控制双 N20 电机](notes/04-Fan-Robot/03-Manual-Motor-Control) | 🚧 待实物验收 | DRV8833 双路点动、松手/断联锁定；相机预览保留，新增单电机500ms满功率诊断 |

目录与 `notes/` 同步维护：每新增一个学习子板块，都要在这里补上对应入口链接和状态。

## 🧭 每一章是怎么写的

[`notes/`](notes) 下的每一章都遵循同一个模板
（见 [`notes/TEMPLATE.md`](notes/TEMPLATE.md)），让你知道每章会看到什么：

```
# 标题

## 为什么学这个
现实中的问题——机器人为什么需要这个能力。

## 概念
用简单的语言解释清楚。

## 构建
实际的代码。

## 实验
运行截图 / 录屏。

## 踩过的坑
遇到的问题和教训。

## 下一步
接下来要做什么。
```

## 🗂️ 仓库结构

```
embodied-ai-journey/
├── README.md          本文件（中文）
├── README.en.md        英文版
├── notes/              旅程记录，逐章更新
│   ├── TEMPLATE.md
│   ├── 00-Why-Embodied-AI/
│   ├── 01-Fundamentals/             第一个月：ROS2 Web Gateway v0.1
│       ├── 01-ROS2-Communication/
│       ├── 02-TF2-And-Coordinate-Systems/
│       ├── 03-URDF-And-RViz/
│       ├── 04-RViz-Markers/
│       ├── 05-Rosbag2-And-MCAP/
│       └── 06-ROS2-Web-Gateway/
│   ├── 02-MoveIt/                  第二个月：MoveIt 与机械臂运动规划
│       ├── 01-Your-First-MoveIt-Project/
│       ├── 02-Visualizing-In-RViz-With-Python/
│       ├── 03-Planning-Around-Objects-With-Python/
│       ├── 04-Pick-And-Place-With-MTC-Python/
│       └── 05-MoveIt-Web-Studio/
│   ├── 03-Vision/                   第三个月：机器人视觉
│   │   └── 01-YOLO-Tennis-Ball/
│   └── 04-Fan-Robot/                真实项目：风扇机器人
│       ├── 01-ESP32-Camera/
│       ├── 02-Offline-Hand-Detection/
│       └── 03-Manual-Motor-Control/
├── ros_ws/             ROS2 工作空间——所有代码都在这里跑起来
│   └── src/
│       ├── fundamentals/
│       │   ├── ros2_fundamentals/
│       │   ├── tf2_coordinate_systems/
│       │   ├── urdf_r2d2/
│       │   ├── rviz_markers/
│       │   ├── rosbag2_fundamentals/
│       │   └── web_gateway_demo/
│       ├── moveit/
│           └── hello_moveit_py/
│       ├── vision/
│       │   └── yolo_tennis_ball/
│       └── fan_robot/               相机固件与电脑端实验工具
│           ├── firmware/
│           └── tools/
├── web_gateway/        第一个月成果：ROS2 Web Gateway v0.1
├── moveit_web_studio/  第二个月成果：MoveIt 网页抓取放置工作台
└── recordings/         本地 rosbag2/MCAP 运行产物（不进入 Git）
```

## ⭐ 一起关注

如果你是一个对机器人感兴趣的软件工程师，这个仓库就是为你准备的。
Star 一下，关注更新，一起见证这段旅程。
