[← 第二个月 MoveIt](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 02 · 在 RViz 中看懂一次规划：纯 Python 可视化实验

机械臂“动起来”不等于我理解了它。真正有价值的问题是：目标在哪里？规划器选了什么轨迹？执行前我是否看过它？

官方教程用 C++ 的 `MoveItVisualTools` 把这些问题变成 RViz 中的标题、目标和轨迹，再用 `Next` 按钮逐步执行。本实验保留这个学习节奏，但**不写任何 C++**：Python 节点直接发布 `MarkerArray` 和 `DisplayTrajectory`，并用三个 ROS 2 `Trigger` 服务替代 GUI 的 `Next` 按钮。

```text
show_goal 服务 ──> MarkerArray ──────────────> RViz：标题、目标球、XYZ 坐标轴
plan 服务      ──> MoveItPy ──> DisplayTrajectory ──> RViz：真实规划轨迹
execute 服务   ──> mock controller ───────────> RViz：当前机械臂状态更新
```

这不是为了绕开官方工具，而是刻意把“可视化到底由哪些 ROS 消息组成”拆开：Marker 是我自己画的解释层，`DisplayTrajectory` 是 MoveIt 的真实规划结果，控制器的 `/joint_states` 则是已经执行的事实。

## 代码在哪里

代码继续放在 [`hello_moveit_py`](../../../ros_ws/src/moveit/hello_moveit_py)：

- [`rviz_visualizer.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/rviz_visualizer.py)：纯 Python 实现三个服务、目标球、三色坐标轴、标题和轨迹发布。
- [`visualizing.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/visualizing.launch.py)：启动 Python 节点、`move_group`、Panda mock controller、TF、robot state publisher 和 RViz。
- [`moveit_py.yaml`](../../../ros_ws/src/moveit/hello_moveit_py/config/moveit_py.yaml)：给 Python `MoveItPy` 进程提供 Planning Scene Monitor 和 OMPL 参数。

本实验的固定目标仍是 `panda_link8` 在 `panda_link0` 坐标系中的 `(0.28, -0.20, 0.50)`。目标球是金黄色；红、绿、蓝箭头分别是目标局部坐标的 X、Y、Z 方向。为了让初学阶段更容易识别，示例目标使用单位四元数，坐标轴也与基坐标轴对齐。

## 环境与构建

环境为 **Ubuntu 24.04 + ROS 2 Jazzy**。若还没有安装 MoveIt：

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config

source /opt/ros/jazzy/setup.bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

## 实验步骤：先看，再规划，最后执行

### 1. 启动

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
ros2 launch hello_moveit_py visualizing.launch.py
```

等待 RViz 打开，终端出现：

```text
[INFO] [python_rviz_visualizer]: Call show_goal, plan, then execute through ROS 2 services.
```

### 2. 配置 RViz 的两层可视化

官方教程需要添加 `Marker Array`；本实验同样如此：

1. 在 RViz 左侧 `Displays` 点击 `Add`，选择 `MarkerArray`。
2. 将它的 `Topic` 设为 `/rviz_visual_tools`。
3. 保持已有的 `MotionPlanning` 显示启用，并在 `Planned Path` 中确认 `Show Robot Visual` 已勾选；它订阅 `/display_planned_path`，负责显示真实轨迹。

MarkerArray 是“解释图层”，MotionPlanning 是“真实轨迹图层”。若只看到标题和目标球而看不到机械臂路径，通常是第 3 步没有开启。

### 3. 显示目标

另开一个已 source 的终端：

```bash
ros2 service call /python_rviz_visualizer/show_goal std_srvs/srv/Trigger "{}"
```

此时机器人上方显示 `1. Goal pose...`，末端目标处有金色球和三支坐标轴。先在屏幕上确认：目标不在地面下、不在底座内部，也没有明显超出机械臂工作范围。

### 4. 规划并查看结果

```bash
ros2 service call /python_rviz_visualizer/plan std_srvs/srv/Trigger "{}"
```

服务成功时会返回 `Published the planned trajectory to RViz.`。RViz 标题变为 `3. Plan ready...`，MotionPlanning 的 Planned Path 显示 MoveItPy 刚刚得到的真实关节轨迹。此时**机械臂当前状态还没有改变**，所以可以安心旋转视角检查路径。

### 5. 执行已检查的轨迹

```bash
ros2 service call /python_rviz_visualizer/execute std_srvs/srv/Trigger "{}"
```

这一步才会调用 `moveit_py.execute()`。mock controller 发布新的 `/joint_states`，RViz 中的场景机械臂随之运动。服务返回 `Mock controller executed...` 后，计划缓存会被清空，防止误重复执行旧轨迹。

## Python 如何替代官方 C++ 工具

| 官方 C++ 教程 | 本实验的 Python 实现 | 你应该观察什么 |
| --- | --- | --- |
| `publishText()` | `Marker.TEXT_VIEW_FACING` | 程序此刻处于显示目标、规划或执行哪个阶段 |
| `publishAxisLabeled()` | 金色球 + 三支 `Marker.ARROW` | 目标位置与朝向 |
| `publishTrajectoryLine()` | `DisplayTrajectory` 发布到 `/display_planned_path` | MoveIt 实际规划出的机械臂运动 |
| `RvizVisualToolsGui` 的 `Next` | `/show_goal`、`/plan`、`/execute` 三个 `Trigger` 服务 | 每一步都能停下来观察 |
| `trigger()` 批量发送 | 每次服务直接发布消息 | Python 中发布与状态切换的明确边界 |

`DisplayTrajectory` 不只是“画一条想象中的线”：它携带 `MoveItPy` 返回的 `RobotTrajectory` 消息。RViz 按这段关节轨迹渲染机械臂，因而这层预览与随后传给 controller 的内容来自同一次规划。

## 修改目标，观察规划如何改变

打开 [`rviz_visualizer.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/rviz_visualizer.py)，修改 `create_target_pose()` 中的 XYZ，再构建和重启：

```bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

建议一次只改一个坐标，例如把 `y = -0.20` 改成 `y = 0.20`。先调用 `show_goal` 观察球的位置，再调用 `plan`。这种“先看目标、再看路径”的顺序，比直接执行更接近未来真实机械臂的工作方式。

## 常见问题

- **看不到文字或球**：确认新增的是 `MarkerArray`，Topic 精确为 `/rviz_visual_tools`。
- **看不到规划中的机械臂**：保持 `MotionPlanning` 启用，并检查 `Planned Path` 的轨迹 Topic 为 `/display_planned_path`、`Show Robot Visual` 已勾选。
- **`plan` 失败**：目标可能不可达或初始关节状态还未到达。等待 controller 就绪后重试，或把目标拖近初始姿态附近。
- **`execute` 返回失败**：这是有意的保护；必须先成功调用一次 `plan`。
- **调用服务找不到命令**：新终端忘记了 `source install/setup.bash`，或 launch 尚未完成启动。

## 这一步学到了什么

到这里，我不再只会说“MoveIt 会规划”。我能指出：目标是哪个 ROS Marker，轨迹在哪个 Topic 中，何时只是预览，何时才真正进入 controller。以后接入障碍物、相机或 Web 控制台时，这种可视化分层会是最直接的排错工具。

## 参考

- [MoveIt 官方：Visualizing in RViz](https://moveit.picknik.ai/main/doc/tutorials/visualizing_in_rviz/visualizing_in_rviz.html)
- [MoveIt 官方：Motion Planning Python API](https://moveit.picknik.ai/main/doc/examples/motion_planning_python_api/motion_planning_python_api_tutorial.html)
