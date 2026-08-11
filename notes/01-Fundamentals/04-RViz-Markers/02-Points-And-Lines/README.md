[← RViz Marker 实验](../README.md) · [← 第一个月 Fundamentals](../../README.md) · [返回主页](../../../../README.md) · **中文** | [English](README.en.md)

# 04.2 · RViz Marker：点与线

基础形状解决的是“在某个位置画一个东西”。但视觉、规划和调试任务经常需要一次画出很多点：一条预测轨迹、一组候选抓取点、一片扫描结果，或一条路径上的风险区域。这个实验把 100 个点同时编码成三种 Marker，第一次把 RViz 当作“时序几何数据”的观察工具。

## 官方逻辑与 Python 实现

[ROS2 Jazzy 官方教程](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Points-and-Lines/Marker-Points-and-Lines.html) 的原始实现为 C++。当前工作区使用等价的 rclpy 实现：[`points_and_lines.py`](../../../../ros_ws/src/fundamentals/rviz_markers/rviz_markers/points_and_lines.py)。它以 `30 Hz` 向同一个 `/visualization_marker` 话题发布三条消息：

| Marker | 颜色 | `id` | 点集如何被解释 |
|---|---:|---:|---|
| `POINTS` | 绿 | 0 | 每个 `Point` 都是一个独立点，`scale.x/y` 是点的宽和高 |
| `LINE_STRIP` | 蓝 | 1 | 按数组顺序把相邻点连成一条连续折线，`scale.x` 是线宽 |
| `LINE_LIST` | 红 | 2 | 每两个点构成一段独立线段，`scale.x` 是线宽 |

每帧的 100 个基础点沿 `x` 轴从 `-50` 到 `49` 排列；`y`、`z` 则由 `sin`/`cos` 计算。不断增加的 `phase` 让整组几何图案持续变化。红色线段的第二个端点比第一个端点高 `1 m`，因此看起来像一组竖线。

## 构建

在 `ros_ws` 目录下：

```bash
colcon build --packages-select rviz_markers
source install/setup.bash
```

## 实验：同时显示点、折线和线段

需要两个终端。它们都要先进入 `ros_ws` 并执行 `source install/setup.bash`。

终端 1：启动发布器。

```bash
ros2 run rviz_markers points_and_lines
```

终端 2：启动 RViz。

```bash
rviz2
```

在 RViz 左侧依次操作：

1. 在 **Global Options** 中将 **Fixed Frame** 设置为 `my_frame`；
2. 点击 **Add** → **By topic**；
3. 展开 `/visualization_marker`，选择 **Marker**；
4. 用鼠标滚轮缩小视图，并拖动视角观察三维几何形状。

此时同一个 Marker Display 中应同时出现：绿色散点、蓝色连续曲线和红色竖直线段。它们会以 30 Hz 平滑变化。三个 Marker 同用一个 topic 没有冲突，因为 `ns='points_and_lines'` 下的 `id=0`、`1`、`2` 不同。

## 用 CLI 验证

发布器启动后：

```bash
ros2 topic hz /visualization_marker
```

频率约为 `90 Hz`，而不是 `30 Hz`：每次定时器触发都会连续发布三条 Marker 消息。再观察一条消息：

```bash
ros2 topic echo /visualization_marker --once
```

你会看到 `ns: points_and_lines`、不同的 `id`，以及很长的 `points` 数组。`LINE_LIST` 的数组长度为 `200`，因为 100 条线段各需要两个端点。

## 我想记住的边界

`POINTS` 适合看离散样本，`LINE_STRIP` 适合看有先后顺序的路径，`LINE_LIST` 适合看互不相连的关系，例如法线、匹配关系或速度向量。它们都只是**可视化协议**：点位仍应带有可靠的 frame 和时间戳，Marker 并不会替你完成坐标转换或数据同步。

## 踩过的坑

- `LINE_LIST` 不是一条自动连续的线；必须严格按两个点一组追加，否则末尾孤立点不会形成线段。
- 点很多时，`POINTS` 的尺寸应该通过 `scale.x/y` 设置；`scale.z` 对它没有意义。
- 线 Marker 只读取 `scale.x` 作为线宽；修改 `scale.y/z` 不会让线变粗。
- 如果同时运行基础形状和本实验，它们会争用同一个 topic，但 namespace 不同，RViz 会同时显示两组内容。调试时建议一次只启动一个发布器，便于观察。

## 下一步

后续可以用真实的路径规划结果、激光点或视觉检测位置替换这里的 `sin`/`cos` 生成器，再把同一份数据推给 Web Gateway。
