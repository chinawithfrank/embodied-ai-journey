[← 返回主页](../../README.md) · **中文** | [English](README.en.md)

# 第一个月：机器人软件 Fundamentals

> **本月目标：ROS2 Web Gateway v0.1** —— 让机器人世界里的数据和任务，第一次进入我熟悉的 Web 系统。

我不是从电机、机械结构或控制理论开始这段旅程，而是从一个更贴近自己背景的问题开始：一个机器人节点产生的数据，怎样可靠地抵达后端与网页？一个网页上的按钮，怎样变成可追踪、可取消的机器人任务？

这一个月不会急着买硬件，也不会追逐 SLAM、Isaac Sim 或 VLA。先搭起最小但完整的软件骨架：ROS2 负责机器人侧的通信和任务，Web 系统负责把状态、日志和控制交给人。后面的机械臂、视觉与数据平台都会长在这条链路上。

## 这个月完成什么

月末的展示产品叫做 **ROS2 Web Gateway v0.1**。它不是一个漂亮但空洞的 Dashboard，而是一条能跑通的任务链路：

```text
ROS2 节点发布状态 ──> 后端接收 ──> WebSocket ──> 网页实时展示
网页创建任务 ────────> 后端调用 ──> ROS2 Service / Action ──> 节点执行
                                             │
                                     进度、取消、日志、MCAP 记录
```

月末验收时，演示至少要回答六个问题：

1. 机器人现在是否在线？
2. 它正在发送什么传感器或状态数据？
3. 用户能否从网页创建一个任务？
4. 长任务的进度是否可见、是否可取消？
5. 发生问题时，日志在哪里？
6. 这次运行能否被录制和回放？

这是本月已经完成的产品契约：通信、TF2、URDF、RViz 与 rosbag2/MCAP 样例最终汇入了可运行的 Web Gateway。它仍是本地实验版，不是直接用于实体机器人安全控制的产品。

## 目录约定

这里保持一个非常简单的边界：

```text
embodied-ai-journey/
├── ros_ws/                         # 只放可构建、可运行的 ROS2 实验代码
│   └── src/fundamentals/
│       ├── ros2_fundamentals/      # Topic、Service、Action、Parameter
│       ├── tf2_coordinate_systems/ # 静态/动态 TF 与查询
│       ├── urdf_r2d2/              # URDF、JointState、TF 与 RViz
│       ├── rviz_markers/           # Marker 基础形状与后续可视化实验
│       ├── rosbag2_fundamentals/   # MCAP 录制与可视化回放
│       └── web_gateway_demo/        # 组合前述节点的月度成果演示图
└── notes/                          # 只放学习叙事、概念解释、实验步骤与复盘
    └── 01-Fundamentals/
        ├── README.md               # 本月入口与产品目标
        ├── 01-ROS2-Communication/
        ├── 02-TF2-And-Coordinate-Systems/
        ├── 03-URDF-And-RViz/
        ├── 04-RViz-Markers/
        ├── 05-Rosbag2-And-MCAP/
        └── 06-ROS2-Web-Gateway/
```

新的实验代码只进入 `ros_ws`；每个实验的“为什么做、怎么运行、看到了什么、踩了什么坑”只写在 `notes`。这样读者可以从笔记理解旅程，也可以只进入工作空间直接构建代码。

## 学习地图

### 已开始：让节点互相说话

[01 · ROS2 通信](01-ROS2-Communication) 从 Topic 开始，逐步把 Service、Action 和 Parameter 放进同一个小包里。它回答的是：什么时候只需要“广播事件”，什么时候要“等一个答复”，什么时候必须“看进度、允许取消”。这些边界会直接决定 Web Gateway 的 API 形状。

### 已开始：让数据知道自己在哪里

[02 · TF2 与坐标系](02-TF2-And-Coordinate-Systems) 用静态和动态 frame 把“相机在机器人哪里”变成可查询的事实。现在的圆周运动只是一个看得见的最小实验；后面真实的相机、机械臂和检测结果都要依赖同样的 TF 树。

### 已开始：让机器人能被看见

[03 · URDF 与 RViz](03-URDF-And-RViz) 让 R2D2 的结构、关节状态和 TF 同时可见。它是从“理解 frame”到“验证一个模型正在被数据驱动”的关键一步。

### 已开始：让运行时信息浮现在画面上

[04 · RViz Marker](04-RViz-Markers) 已包含基础形状与点线实验，把 ROS2 运行时消息变成 RViz 中的对象。后面的感知目标、轨迹和调试区域都会使用这条可视化通道。

### 已开始：让一次运行可以被重放

[05 · rosbag2 与 MCAP](05-Rosbag2-And-MCAP) 把 R2D2 的关节消息和 Marker 动画写入 MCAP，并在停止实时发布器后重新送回 RViz。它让“这次到底发生了什么”有了可检查、可分享的运行证据。

### 已完成：让系统变得可展示

[06 · ROS2 Web Gateway v0.1](06-ROS2-Web-Gateway) 用 FastAPI、WebSocket、Next.js 和 Docker Compose 把前面的能力收拢为一个本地实验控制台。它显示机器人状态、创建/取消受限任务、保存网关日志，并让用户从网页开始或停止 MCAP 录制。

## 从零运行当前实验

环境固定为 **Ubuntu 24.04 + ROS2 Jazzy**。首次使用时：

```bash
cd ros_ws
colcon build --packages-select ros2_fundamentals tf2_coordinate_systems urdf_r2d2 rviz_markers rosbag2_fundamentals web_gateway_demo
source install/setup.bash
```

然后从上面的两个章节任选一个实验，严格按“终端 1 / 终端 2”的步骤运行。每个新终端进入 `ros_ws` 后都需要再执行一次：

```bash
source install/setup.bash
```

## 学习记录方式

这不是官方教程的逐句翻译。每一篇笔记都会保留四件事：

- **我当时想验证什么**：先把实验放回真实机器人/产品问题里。
- **你可以照做的步骤**：命令、终端数量、预期输出和观察点都写出来。
- **概念边界**：说明一个机制该用在哪里，以及不该滥用在哪里。
- **失败与下一步**：保留问题，不把学习过程写成“永远一次成功”的假象。

当本月结束时，这些章节应当连成一条可回放的证据链，而不只是零散的 API 笔记。
