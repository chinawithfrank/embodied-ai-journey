[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 04 · RViz Marker：发送基础形状

R2D2 实验展示的是机器人“自身是什么样子”。但真实开发中，还有大量东西不属于 URDF：相机识别出的目标、规划出的路径、碰撞区域、抓取候选点、调试状态。这些临时、动态的可视化数据，适合用 `visualization_msgs/Marker` 直接发送给 RViz。

这是 RViz Marker 系列的第一个实验。它每秒把同一个 Marker 更新为绿色的立方体、球体、箭头和圆柱，让我先弄清楚：RViz 不是只能看模型，也可以像一个由 ROS2 消息驱动的调试画布。

## 实验目录

1. **基础形状**（当前页）—— 通过一个不断更新的 Marker 理解 type、颜色、尺度和身份。
2. [**点与线**](02-Points-And-Lines) —— 同时显示 `POINTS`、`LINE_STRIP` 与 `LINE_LIST`，理解点集的不同解释方式。

## 概念

- **Marker**：发送给 RViz 的单个可视化对象；它不是物理碰撞体，也不会驱动机器人运动。
- **`header.frame_id`**：Marker 所在的坐标系。该实验使用 `my_frame`，并在 RViz 中把 Fixed Frame 也设为 `my_frame`，因此不需要额外发布 TF。
- **namespace + id**：Marker 的唯一身份。相同的 `ns='basic_shapes'` 和 `id=0` 表示更新同一个对象，而不是每秒新增一个形状。
- **type**：本实验依次切换 `CUBE`、`SPHERE`、`ARROW`、`CYLINDER`。
- **action**：`ADD` 会创建或更新对象；后续实验会用 `DELETE` 和 `DELETEALL` 清理对象。
- **pose、scale、color、lifetime**：分别定义位置姿态、尺寸、颜色和保留时长。透明度 `color.a` 必须非零，否则 Marker 不可见。

## 代码

官方 Jazzy 教程使用 C++；本仓库将相同行为改写为 rclpy，以便与已有 Fundamentals 包保持一致。[官方教程](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Sending-Basic-Shapes/Marker-Sending-Basic-Shapes.html) 的关键逻辑都保留在 [`basic_shapes.py`](../../../ros_ws/src/fundamentals/rviz_markers/rviz_markers/basic_shapes.py)：

1. 向 `/visualization_marker` 创建 `Marker` 发布器；
2. 每秒构造一个 `ns='basic_shapes'`、`id=0` 的绿色 Marker；
3. 发布后将类型推进到下一个基础形状；
4. 四种类型循环，RViz 因为收到同一个身份的新消息而更新画面。

代码包位于 [`ros_ws/src/fundamentals/rviz_markers`](../../../ros_ws/src/fundamentals/rviz_markers)。

## 构建

如果系统未安装 RViz：

```bash
sudo apt install ros-jazzy-rviz2
```

在 `ros_ws` 目录下：

```bash
colcon build --packages-select rviz_markers
source install/setup.bash
```

## 实验：在 RViz 中看基础形状

需要两个终端；每一个终端都进入 `ros_ws` 后执行 `source install/setup.bash`。

终端 1：发布 Marker。

```bash
ros2 run rviz_markers basic_shapes
```

终端 2：启动 RViz。

```bash
rviz2
```

在 RViz 左侧按以下步骤配置：

1. 展开 **Global Options**，将 **Fixed Frame** 改为 `my_frame`；
2. 点击左下角 **Add**；
3. 选择 **By topic**；
4. 展开 `/visualization_marker`，选择 **Marker**。

等待一秒后，中央视图会出现一个绿色形状，并每秒按 **立方体 → 球体 → 箭头 → 圆柱** 循环。若看不到它，先用鼠标滚轮拉远/拉近视角，因为形状位于原点。

## 用 CLI 验证

RViz 之前，先确认消息确实存在：

```bash
ros2 topic echo /visualization_marker --once
```

你应看到类似字段：

```text
header:
  frame_id: my_frame
ns: basic_shapes
id: 0
type: 1
action: 0
color:
  g: 1.0
  a: 1.0
```

`type` 会随时间变化；消息频率可用下面命令确认：

```bash
ros2 topic hz /visualization_marker
```

## 我想记住的边界

URDF 描述的是相对稳定的机器人结构；Marker 描述的是某次运行中的临时信息。以后在 Web Gateway 或 RViz 中显示“检测到的杯子”“规划路径”“当前目标”和“错误区域”时，都不应该硬塞进 URDF，而应该发布带时间戳和 frame 的 Marker。

## 踩过的坑

- RViz 报 `Fixed Frame [my_frame] does not exist` 时，先确认终端 1 已在发布消息；Marker 的 `header.frame_id` 与 Fixed Frame 完全相同即可显示。
- Marker 存在但看不见，优先检查 `color.a` 是否大于 `0`，以及 `scale` 三个轴是否都为正数。
- 不要在循环中随意改变 `ns` 或 `id`；否则 RViz 会把每条消息当成新对象，画面会越来越乱。
- Marker 是可视化数据，不等于 TF、URDF 或真实环境中的障碍物。它不会替代坐标变换、碰撞检测或运动规划。

## 下一步

下一项 Marker 实验将用 `POINTS`、`LINE_STRIP` 和 `LINE_LIST` 显示轨迹、点云式结果或规划路径。
