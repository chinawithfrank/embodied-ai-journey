[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 01 · ROS2 通信：先让模块彼此说话

本章统一使用 **ROS2 Jazzy Jalisco**（对应 Ubuntu 24.04）。

## 为什么学这个

第一个真正让我从“写 Web 服务”切换到“写机器人软件”的瞬间，是意识到机器人并不是一个整体程序。摄像头节点、底盘节点、机械臂节点各自在不同进程、甚至不同机器上运行，却必须对同一件事达成协作。ROS2 要先解决的，就是让这些小模块用同一种语言交换消息、请求和任务。

这个实验包刻意很小：字符串、开关和 turtlesim 的小乌龟都不是真实产品功能。但它们让我先看见通信模型的边界——什么时候系统只需要推送一个事件，什么时候应该等待答复，什么时候任务必须有进度和取消能力。Web Gateway 最终会把这些边界变成网页上的实时状态、按钮和任务记录。

### 这一步如何进入月末产品

| 今天的实验 | 在 ROS2 Web Gateway 中会变成 |
|---|---|
| Topic 发布/订阅 | 实时状态或传感器数据，通过 WebSocket 推到网页 |
| Service | 短操作，例如更新一个开关或读取即时状态 |
| Action | 可显示进度、可取消的长任务 |
| Parameter | 启动配置和运行期可调项 |

## 概念

- **Node（节点）**：一个独立运行的程序，通常只做一件事。
- **Topic（话题）**：节点之间异步广播消息的通道，一个节点发布（publish），任意多个节点可以订阅（subscribe）。
- **Service（服务）**：同步的请求/响应通信，适合“执行一次并给出结果”的工作，例如启用电机或读取配置。
- **Action（动作）**：面向耗时任务的目标（goal）通信；服务端会持续反馈进度，并允许客户端取消目标。
- **Parameter（参数）**：节点自身的可配置键值；可在启动时传入，也可在节点运行中通过命令行修改。
- **Message（消息）**：话题上传输的数据结构，比如 `geometry_msgs/Twist`（速度指令）、`std_msgs/String`（字符串）。
- **turtlesim**：ROS2 官方自带的一个"沙盒"仿真器，用一只小乌龟代替真实机器人，专门用来练习 topic 通信，不用碰硬件。

## 构建

代码在 [`ros_ws/src/fundamentals/ros2_fundamentals`](../../../ros_ws/src/fundamentals/ros2_fundamentals)，包含以下实验：

1. **键盘控制小乌龟**（[`keyboard_teleop.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/keyboard_teleop.py)）—— 用 `termios`/`tty` 读终端按键，映射成 `Twist` 发布到 `/turtle1/cmd_vel`，驱动 turtlesim 的乌龟移动。
2. **Pub / Sub 样例**（[`pub_example.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/pub_example.py) / [`sub_example.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/sub_example.py)）—— 一个节点每秒发一条 `String` 到 `chatter` 话题，另一个节点订阅并打印。
3. **Service 样例**（[`service_server.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/service_server.py) / [`service_client.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/service_client.py)）—— 服务端提供 `std_srvs/SetBool` 类型的 `/set_motors_enabled`；客户端发送“启用/禁用电机”请求并等待响应。
4. **Action 样例**（[`action_client.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/action_client.py)）—— 连接 turtlesim 内置的 `/turtle1/rotate_absolute` action，发送目标朝向并输出旋转过程中的反馈。
5. **Parameter 样例**（[`parameter_example.py`](../../../ros_ws/src/fundamentals/ros2_fundamentals/ros2_fundamentals/parameter_example.py)）—— 声明并校验 `robot_name` 与 `publish_period`；修改周期时会重建定时器，使配置立即生效。

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

### 运行——实验三：Service 样例

需要两个终端。终端 1 启动服务端：

```bash
ros2 run ros2_fundamentals service_server
```

终端 2 发送请求（默认启用）：

```bash
ros2 run ros2_fundamentals service_client
```

也可以传入参数来禁用：

```bash
ros2 run ros2_fundamentals service_client --ros-args -p enabled:=false
```

使用 ROS2 CLI 查看接口和直接调用服务：

```bash
ros2 service list
ros2 interface show std_srvs/srv/SetBool
ros2 service call /set_motors_enabled std_srvs/srv/SetBool "{data: true}"
```

### 运行——实验四：Action 样例

先在终端 1 启动 turtlesim。它自带 `RotateAbsolute` action 服务端：

```bash
ros2 run turtlesim turtlesim_node
```

终端 2 发送一个目标朝向（弧度）：

```bash
ros2 run ros2_fundamentals action_client --ros-args -p theta:=1.57
```

运行时客户端会打印反馈中的剩余旋转角度，结束时打印最终转角。可用下面的命令查看 action 定义：

```bash
ros2 action list -t
ros2 interface show turtlesim/action/RotateAbsolute
```

### 运行——实验五：Parameter 样例

启动时传入参数：

```bash
ros2 run ros2_fundamentals parameter_example --ros-args \
  -p robot_name:=journey_bot -p publish_period:=2.0
```

另开一个终端查看、读取或修改正在运行节点的参数：

```bash
ros2 param list /parameter_example
ros2 param get /parameter_example robot_name
ros2 param set /parameter_example robot_name scout
ros2 param set /parameter_example publish_period 0.5
```

`robot_name` 会在下一次日志中更新；`publish_period` 会重新设置定时器。空名称和非正周期会被节点拒绝。

## 运行后应该看到什么

不要只满足于“命令没有报错”。运行后，请至少验证这些可观察结果：

1. `pub_example` 每秒打印一次 `Publishing`，`sub_example` 能在另一终端收到同一计数。
2. service 客户端得到 `Motors are enabled.` 或 `Motors are disabled.`；服务端也会记录同样的状态变化。
3. action 客户端持续打印 `Remaining rotation`，而不是只在结束时返回一个结果。
4. 修改 `robot_name` 或 `publish_period` 后，parameter 节点的下一条日志或输出频率发生变化。

这些观察点以后会成为 Web 页面与后端测试的验收条件。建议在真正的 Ubuntu 环境跑通后，把终端输出或 60 秒录屏补在这里，并记下第一次与预期不同的地方。

## 踩过的坑

- 键盘读取用的是原始终端模式（raw tty），必须在前台终端里用 `ros2 run` 启动，`ros2 launch` 没法可靠地把 stdin 转发给多个子进程，所以这两个实验都没有做成 launch 文件。
- 每开一个新终端都要重新 `source install/setup.bash`，忘记 source 会导致 `ros2 run` 找不到这个包。
- `turtlesim` 不是 ROS2 核心自带的，需要单独 `apt install`。
- service 的调用者会等待一次响应，适合短操作；不要把长时间运行的导航、抓取等任务塞进 service，应使用 action。
- ROS2 参数有类型限制。命令行的值要与声明类型一致，例如 `publish_period` 是浮点数，`enabled` 是布尔值。

## 下一步

下一章：[TF2 与坐标系](../02-TF2-And-Coordinate-Systems) —— 让机器人知道“东西在哪儿”。
