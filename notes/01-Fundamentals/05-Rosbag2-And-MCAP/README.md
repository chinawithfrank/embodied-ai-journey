[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 05 · rosbag2 与 MCAP：把一次运行留下来

机器人运行起来并不等于实验完成。真正难的问题常常发生在我没有盯着终端的那一秒：一段 Marker 为什么突然跳了？某个关节的状态在什么时候开始不对？如果只能靠“再跑一遍试试看”，调试就会变成碰运气。

这次实验把前面已经存在的 R2D2 关节状态和 RViz 点线 Marker 录制为一个 **MCAP** bag，然后在没有实时发布器的情况下回放它。屏幕上的运动再次出现，说明我保存下来的不是截图，而是可以被 ROS2 重新消费的时间序列消息。

## 这次要验证什么

```text
实时发布器 ──> /joint_states ───────────┐
             /visualization_marker ──────┼──> ros2 bag record --storage mcap
                                         │
                               recordings/fundamentals_run/
                                         │
ros2 bag play ───────────────────────────┘
             │
             ├──> robot_state_publisher ──> R2D2 关节 TF
             └──> RViz Marker display ────> 点与线动画
```

`rosbag2` 记录的是 **topic 上收到的消息及其时间顺序**，不是“正在运行的节点快照”。它不会替你保存 Python 代码、launch 文件或参数服务器的全部状态；这些仍然由本仓库的回放 launch 提供。这是理解 rosbag2 最重要的边界。

## 为什么选 MCAP

MCAP 是 rosbag2 可选的存储后端之一，适合保存带 schema 和索引的机器人消息数据。本实验显式使用 `--storage mcap`，这样 `ros2 bag info` 会清楚显示存储格式，而不是依赖系统默认值。

这次只录两个主题：

- `/joint_states`：保存 R2D2 三个关节随时间变化的位置；回放时 `robot_state_publisher` 重新计算各个 link 的 TF。
- `/visualization_marker`：保存点、折线和线段组成的动画；RViz 在回放时直接消费它。

真实机器人排障通常还会录制 `/tf` 与 `/tf_static`。这里刻意不录它们：R2D2 的内部 TF 可以由已录制的关节状态重新生成，而回放 launch 用静态 `odom -> axis` 和 `odom -> my_frame` 补齐固定坐标关系。这样更容易看出“原始数据”和“根据数据重建的状态”分别是什么。

## 新增的代码

代码包位于 [`rosbag2_fundamentals`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals)。它不再新增一个随意的消息发布器，而是把前两个实验组合为两个稳定的运行状态：

- [`recording_demo.launch.py`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/launch/recording_demo.launch.py)：启动 R2D2 状态发布器、点线 Marker 发布器、`odom -> my_frame` 静态 TF 和 RViz，作为录制源。
- [`playback_visualization.launch.py`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/launch/playback_visualization.launch.py)：不启动实时状态或 Marker 发布器，只保留模型、固定 TF 和 RViz，等待 bag 回放消息。
- [`replay.rviz`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/rviz/replay.rviz)：同时显示 RobotModel、TF 与 `/visualization_marker`，Fixed Frame 为 `odom`。

## 准备环境

环境为 **Ubuntu 24.04 + ROS2 Jazzy**。先安装 rosbag2 的 MCAP 后端：

```bash
sudo apt update
sudo apt install ros-jazzy-rosbag2 ros-jazzy-rosbag2-storage-mcap
```

然后在工作空间构建这三个相互依赖的包：

```bash
cd ros_ws
colcon build --packages-select urdf_r2d2 rviz_markers rosbag2_fundamentals
source install/setup.bash
```

此后每个新终端进入 `ros_ws` 后，都执行一次：

```bash
source install/setup.bash
```

## 实验一：录制一次运行

准备两个终端。

终端 1：启动持续产生数据的场景。

```bash
ros2 launch rosbag2_fundamentals recording_demo.launch.py
```

RViz 中应该同时看到 R2D2 与三组随时间起伏的点线。这个终端必须一直保持运行，直到录制结束。

终端 2：开始录制。输出目录使用 `ros_ws/recordings/`；它已被 `.gitignore` 忽略，因此不会把大型运行数据提交到代码仓库。

```bash
mkdir -p recordings
ros2 bag record --storage mcap -o recordings/fundamentals_run \
  /joint_states /visualization_marker
```

等待约 10 秒，再在终端 2 按 `Ctrl-C`。正常结束时会显示已写入消息数，并在 `recordings/fundamentals_run/` 创建 metadata 与 MCAP 数据文件。

## 实验二：先检查，再播放

先检查录制结果，而不是急着打开 RViz：

```bash
ros2 bag info recordings/fundamentals_run
```

输出中应确认三件事：

1. **Storage id** 是 `mcap`；
2. topic 列表包含 `/joint_states` 和 `/visualization_marker`；
3. 持续时间与刚才等待的时长大致一致。

接着停止终端 1 的实时场景，避免它和回放消息同时写入相同 topic。然后准备两个新终端。

终端 1：启动只用于可视化的回放环境。

```bash
ros2 launch rosbag2_fundamentals playback_visualization.launch.py
```

终端 2：播放刚才的 bag。

```bash
ros2 bag play recordings/fundamentals_run
```

RViz 中的 R2D2 关节会再次运动，点、折线和线段也会重现刚才的起伏。为了更容易观察时间轴，可以放慢播放：

```bash
ros2 bag play recordings/fundamentals_run --rate 0.5
```

## 用命令确认回放真的在发消息

回放时另开一个终端执行：

```bash
ros2 topic echo /joint_states --once
ros2 topic echo /visualization_marker --once
```

只要能读到包含时间戳的消息，就说明数据来自 bag player，而非已经停止的实时发布器。也可以用 `ros2 topic hz /joint_states` 观察当前播放速率。

## 我想记住的边界

- **rosbag2 是事件记录，不是系统快照。** 回放可重放消息，却不会自动替你启动 RViz、机器人模型或业务节点。
- **录什么取决于你要回答的问题。** 本实验要复现关节动画和 Marker，因此只录对应主题；真实导航或感知问题则往往还需要 TF、相机、激光、地图和参数证据。
- **回放时关掉实时发布器。** 同一 topic 同时有实时源和 bag player，画面会混入两段时间线，结论不可信。
- **bag 是运行产物，不是源码。** 数据文件可能很大，也可能包含敏感环境信息；默认把 `ros_ws/recordings/` 排除在 Git 外。

## 踩过的坑

- `ros2 bag record` 报找不到 `mcap` 时，通常是没有安装 `ros-jazzy-rosbag2-storage-mcap`，或新终端没有重新 `source /opt/ros/jazzy/setup.bash`。
- `ros2 bag info` 中没有目标 topic 时，先确认终端 1 已启动，再开始录制；rosbag2 只能记录订阅建立之后收到的消息。
- 回放没有画面时，先确认实时场景已停止，再检查 `ros2 bag info` 和 RViz 的 Fixed Frame 是否仍为 `odom`。
- 本实验没有保存 R2D2 的圆周底盘轨迹，因为 `odom -> axis` 是由实时发布器生成的 TF，未列入录制主题。回放 launch 为它补了固定变换，保留关节和 Marker 的可观察效果；要复现整棵运动 TF 树，请把 `/tf` 与 `/tf_static` 也加入录制命令。

## 下一步

现在一次 ROS2 运行已经可以保存、检查和重放。下一步是让 FastAPI/WebSocket 把实时 topic、Action 进度与这份 bag 元数据带到网页，逐步组成月末的 ROS2 Web Gateway。

## 参考

- [rosbag2 MCAP 存储插件（ROS 2 官方仓库）](https://github.com/ros2/rosbag2/tree/rolling/rosbag2_storage_mcap)
- [ROS 2 Jazzy rosbag2 教程索引](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data.html)
