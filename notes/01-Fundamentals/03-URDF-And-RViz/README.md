[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 03 · URDF 与 RViz：第一次看见机器人

前两篇实验让我能够发布消息、查询坐标变换，但终端里的一串数字还不像一个机器人。URDF 把这些抽象的 link、joint 和坐标系变成有几何形状的模型；RViz 则把模型、TF 和关节状态同时摆在眼前。这个 R2D2 实验是第一次让“我发布了一个关节角度”变成“我看见机器人动起来”。

## 这一步如何进入月末产品

Web Gateway 的第一版不会只展示一张静态卡片。URDF 为“机器人型号、关节和 frame”提供了可读的结构，`joint_states` 为网页实时状态提供了第一种可视化数据，而 RViz 则是开发阶段比网页更直接的真相来源：当两者不一致时，先确认 ROS2 内部的模型和 TF 是否正确。

## 概念

- **URDF**：用 XML 描述机器人结构的格式。它说明机器人有哪些部件、它们的几何外观，以及部件如何通过关节相连。
- **Link**：刚性部件，例如 R2D2 的身体、头部或轮子；每个 link 都有自己的坐标系。
- **Joint**：两个 link 的连接方式。关节可以固定、连续旋转或沿一条轴线移动。
- **`JointState`**：发布关节名称和位置的消息。`robot_state_publisher` 读取它，再结合 URDF 计算每个 link 的 TF。
- **`robot_state_publisher`**：把 URDF 的结构定义和实时关节状态合并，发布整棵机器人 TF 树。
- **RViz**：ROS2 的三维可视化工具。本实验同时显示机器人模型和 TF，方便判断“数据有没有真的驱动模型”。

## 代码与资源

实验包在 [`ros_ws/src/fundamentals/urdf_r2d2`](../../../ros_ws/src/fundamentals/urdf_r2d2)。其中的资产来自 ROS2 Jazzy 官方 URDF 教程，并以原文件保存：

- [`r2d2.urdf.xml`](../../../ros_ws/src/fundamentals/urdf_r2d2/urdf/r2d2.urdf.xml) — [官方 URDF 源文件](https://docs.ros.org/en/jazzy/_downloads/872802005223ffdb75b1ab7b25ad445b/r2d2.urdf.xml)
- [`r2d2.rviz`](../../../ros_ws/src/fundamentals/urdf_r2d2/rviz/r2d2.rviz) — [官方 RViz 配置](https://docs.ros.org/en/jazzy/_downloads/96d68aef72c4f27f32af5961ef48c475/r2d2.rviz)
- [`state_publisher.py`](../../../ros_ws/src/fundamentals/urdf_r2d2/urdf_r2d2/state_publisher.py) — 以 `30 Hz` 发布 `swivel`、`tilt`、`periscope` 三个关节状态，并发布 `odom → axis` 的圆周运动变换。
- [`display.launch.py`](../../../ros_ws/src/fundamentals/urdf_r2d2/launch/display.launch.py) — 一次启动 `robot_state_publisher`、状态发布器和带官方配置的 RViz。

## 构建

若未安装 ROS2 Jazzy Desktop，请先安装 RViz 和状态发布器：

```bash
sudo apt install ros-jazzy-robot-state-publisher ros-jazzy-rviz2
```

在 `ros_ws` 目录下编译并加载工作空间：

```bash
colcon build --packages-select urdf_r2d2
source install/setup.bash
```

## 实验：让 R2D2 动起来

终端 1 在 `ros_ws` 内启动完整实验：

```bash
ros2 launch urdf_r2d2 display.launch.py
```

RViz 打开后，你应该看到 R2D2 模型。等待数秒并拖动视角，观察三件事：

1. 模型不是静止的：头部/关节会随 `JointState` 更新而变化；
2. R2D2 的根部沿半径为 `2 m` 的圆周运动；
3. TF Display 中能看到由 URDF 推导出的 link 关系，以及状态发布器给出的 `odom → axis`。

终端 2 进入同一个 `ros_ws` 并重新 `source install/setup.bash`，直接检查关节消息：

```bash
ros2 topic echo /joint_states
```

你会看到：

```text
name: [swivel, tilt, periscope]
position: [0.1..., -0.0..., 0.0...]
```

再查询根部的动态变换：

```bash
ros2 run tf2_ros tf2_echo odom axis
```

`translation.x` 和 `translation.y` 会变化，而 `translation.z` 保持接近 `0.7`。这正是代码中圆周轨迹的可验证证据。

最后可选地导出完整 TF 树：

```bash
ros2 run tf2_tools view_frames
```

## 状态发布器在做什么

这段代码保留官方教程的运动逻辑，但使用 ROS2 定时器替代节点构造函数中的阻塞循环：这让启动、关闭和 launch 管理遵循与工作区其他节点相同的模式。每 `1/30` 秒，它会：

1. 发布 `JointState`，让 `robot_state_publisher` 根据 URDF 推导关节 link 的位置；
2. 将 yaw 角转换为四元数，发布 `odom → axis`；
3. 更新 `tilt`、`periscope`、`swivel` 和圆周运动角度，准备下一帧。

这里的关键不是记住四元数公式，而是建立数据链路的直觉：**URDF 定义结构，`JointState` 定义当前姿态，TF2 定义各个 frame 的关系，RViz 把它们同时验证出来。**

## 踩过的坑

- RViz 没有模型时，先看 launch 终端是否有 `robot_state_publisher` 错误，再确认 `robot_description` 是否成功加载了 URDF。
- 模型存在却不动时，运行 `ros2 topic echo /joint_states`；关节名称必须和 URDF 中的 joint 名称完全一致。
- TF 报错时，不要随意修改 RViz 的 Fixed Frame。先用 `tf2_echo odom axis` 验证发布器是否真的在发根变换。
- URDF 中的长度单位是米，角度通常是弧度；把毫米或角度制直接填入会导致“模型看似存在但比例/姿态离谱”。

## 下一步

下一步把这次可视化运行录成 rosbag2/MCAP。这样月末产品不仅能“展示现在”，也能把一次问题完整回放出来。
