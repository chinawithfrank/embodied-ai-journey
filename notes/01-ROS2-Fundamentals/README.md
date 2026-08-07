[← 返回主页](../../README.md) · **中文** | [English](README.en.md)

# ROS2 基础

本章统一使用 **ROS2 Jazzy Jalisco**（对应 Ubuntu 24.04）。

## 为什么学这个

机器人不是一个整体程序，而是一堆相互独立的模块：摄像头节点、底盘节点、机械臂节点……它们跑在不同进程甚至不同机器上，却要实时协作。ROS2 要解决的第一个问题，就是让这些模块能用统一的方式互相通信。不先搞懂这套通信机制，后面感知、决策、控制怎么接起来都无从谈起。

## 概念

- **Node（节点）**：一个独立运行的程序，通常只做一件事。
- **Topic（话题）**：节点之间异步广播消息的通道，一个节点发布（publish），任意多个节点可以订阅（subscribe）。
- **Message（消息）**：话题上传输的数据结构，比如 `geometry_msgs/Twist`（速度指令）、`std_msgs/String`（字符串）。
- **turtlesim**：ROS2 官方自带的一个"沙盒"仿真器，用一只小乌龟代替真实机器人，专门用来练习 topic 通信，不用碰硬件。

## 构建

代码在 [`ros_ws/src/ros2_fundamentals`](../../ros_ws/src/ros2_fundamentals)，两个实验：

1. **键盘控制小乌龟**（[`keyboard_teleop.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/keyboard_teleop.py)）—— 用 `termios`/`tty` 读终端按键，映射成 `Twist` 发布到 `/turtle1/cmd_vel`，驱动 turtlesim 的乌龟移动。
2. **Pub / Sub 样例**（[`pub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/pub_example.py) / [`sub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/sub_example.py)）—— 一个节点每秒发一条 `String` 到 `chatter` 话题，另一个节点订阅并打印。

### 依赖

```bash
sudo apt install ros-jazzy-turtlesim
```

### 编译

在 `ros_ws` 目录下：

```bash
colcon build --packages-select ros2_fundamentals
source install/setup.bash
```

### 运行——实验一：键盘控制小乌龟

需要两个终端（都要先 `source install/setup.bash`）。

终端 1：

```bash
ros2 run turtlesim turtlesim_node
```

终端 2：

```bash
ros2 run ros2_fundamentals keyboard_teleop
```

| 按键 | 动作 |
|------|------|
| w | 前进 |
| x | 后退 |
| a | 左转 |
| d | 右转 |
| s | 停止 |
| q | 退出 |

### 运行——实验二：Pub / Sub 样例

同样需要两个终端。

```bash
ros2 run ros2_fundamentals pub_example
```

```bash
ros2 run ros2_fundamentals sub_example
```

也可以用 `ros2 topic echo /chatter` 直接观察话题内容。

## 实验

TODO：在 Ubuntu + ROS2 Jazzy 上实际跑通后补充截图/录屏。

## 踩过的坑

- 键盘读取用的是原始终端模式（raw tty），必须在前台终端里用 `ros2 run` 启动，`ros2 launch` 没法可靠地把 stdin 转发给多个子进程，所以这两个实验都没有做成 launch 文件。
- 每开一个新终端都要重新 `source install/setup.bash`，忘记 source 会导致 `ros2 run` 找不到这个包。
- `turtlesim` 不是 ROS2 核心自带的，需要单独 `apt install`。

## 下一步

下一章：[TF2 与坐标系](../02-TF2-And-Coordinate-Systems) —— 让机器人知道"东西在哪儿"。
