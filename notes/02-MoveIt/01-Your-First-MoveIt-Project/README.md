[← 第二个月 MoveIt](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 01 · 第一个 MoveItPy 项目：用 Python 给机械臂一个位姿目标

我最初按官方“Your First C++ MoveIt Project”看到了 `MoveGroupInterface`，但当前目标不是尽快掌握 C++ 语法，而是先把机械臂规划的因果链讲清楚。因此这个实验保留官方教程的核心任务——**给末端位姿目标、规划、执行**——但采用官方的 Python API：`moveit_py`。

当 RViz 中 Panda 动起来时，真正发生的是：Python 把目标交给 MoveIt 的规划组件；它根据 Panda 模型、当前关节状态和 OMPL 配置找出轨迹；mock controller 接收轨迹并发布新的关节状态；RViz 因而显示机械臂运动。

```text
PoseStamped 目标
      │
hello_moveit_py ──> MoveItPy / PlanningComponent(panda_arm)
      │                         │
      │                         ├── 读取机器人模型与 /joint_states
      │                         ├── OMPL 规划
      │                         └── execute() ──> panda_arm_controller
      │                                                   │
      └────────────────────────────────────── RViz <── /joint_states
```

## 这次的代码

实验包位于 [`hello_moveit_py`](../../../ros_ws/src/moveit/hello_moveit_py)。它有三块缺一不可的代码：

- [`pose_goal.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/pose_goal.py)：创建 `MoveItPy`、取得 `panda_arm`、设置 `PoseStamped` 目标、规划并执行。
- [`moveit_py.yaml`](../../../ros_ws/src/moveit/hello_moveit_py/config/moveit_py.yaml)：给 Python 进程提供 Planning Scene Monitor、`/joint_states`、OMPL 和规划请求参数。
- [`demo.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/demo.launch.py)：加载 Panda 模型与上述 YAML，启动 Python 节点、mock `ros2_control` 控制器、静态 TF 和 RViz。

与 C++ 教程不同，这里**不启动 `move_group`**。`MoveItPy` 是 MoveItCpp 的 Python 接口，规划场景和规划管线运行在 Python 节点内部；这正是它必须从 launch 接收完整 MoveIt 参数的原因。

## 先准备环境

环境为 **Ubuntu 24.04 + ROS2 Jazzy**。安装 MoveIt、Panda 配置和 Python 绑定：

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config
```

确认最关键的两个包存在：

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg prefix moveit_py
ros2 pkg prefix moveit_resources_panda_moveit_config
```

两个命令都应输出安装路径。若 `moveit_py` 缺失，先检查 `$ROS_DISTRO` 是否为 `jazzy`，并确认安装命令没有报错。

## 构建

在仓库中的 ROS 工作空间执行：

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

这里构建的是我的 Python 包、launch 文件和 YAML；Panda 的 URDF、SRDF、控制器配置和 RViz 配置来自系统安装的官方资源包，不复制到仓库。

## 实验：一次命令看见规划与执行

这次只需要一个终端，因为 launch 文件会同时启动场景、控制器、RViz 和 Python 程序：

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
ros2 launch hello_moveit_py demo.launch.py
```

RViz 打开后，终端应输出类似：

```text
[INFO] [hello_moveit_py]: Planning a pose goal for panda_link8.
[INFO] [hello_moveit_py]: Plan found. Executing trajectory.
```

Panda 的七个手臂关节会移动，末端趋近这个目标：

```text
frame: panda_link0
position: (0.28, -0.20, 0.50)
orientation: (0, 0, 0, 1)
link: panda_link8
```

`panda_link0` 是目标坐标的参考 frame，`panda_link8` 是被要求到达该位姿的末端 link。四元数不能全为零；`w = 1.0` 表示单位四元数，即末端不额外旋转。

## 从命令行验证运行状态

Python 程序完成动作后会退出，但 RViz 和控制器会继续运行。另开一个终端执行：

```bash
source /opt/ros/jazzy/setup.bash
ros2 control list_controllers
ros2 topic echo /joint_states --once
```

应看到 `joint_state_broadcaster`、`panda_arm_controller` 等控制器处于 active，且 `/joint_states` 带有 Panda 关节名和位置。它说明：执行的结果不是一张 RViz 截图，而是控制器发布的机器人状态。

## 关键代码，逐步理解

### 1. 创建 MoveItPy 与规划组件

```python
moveit_py = MoveItPy(node_name='hello_moveit_py')
panda_arm = moveit_py.get_planning_component('panda_arm')
```

`MoveItPy` 读取 launch 传入的模型、场景监视器和规划管线参数；`panda_arm` 则限定本次规划只控制 Panda 的七个手臂关节。规划组必须与 Panda SRDF 中的名称一致。

### 2. 明确起点与目标

```python
panda_arm.set_start_state_to_current_state()
panda_arm.set_goal_state(
    pose_stamped_msg=pose_goal,
    pose_link='panda_link8',
)
```

起点来自 `/joint_states`，而不是写死的一组角度；这也是重复运行时轨迹可能不同的原因。目标则是一个带 frame 的位姿，不是孤立的 XYZ 数字。

### 3. 规划后才执行

```python
plan_result = panda_arm.plan()
if plan_result:
    moveit_py.execute(plan_result.trajectory, controllers=[])
```

`plan()` 只生成候选轨迹。只有结果存在时才交给控制器执行；这是以后接入真实硬件时必须坚持的边界。当前 `controllers=[]` 让 MoveIt 使用配置中已知的 mock 控制器，**不会驱动真实机械臂**。

## 踩过的坑

- **直接 `ros2 run hello_moveit_py hello_moveit_py`**：它不会自动得到模型和 OMPL 参数。第一步请用 `ros2 launch`；launch 文件就是 Python 程序的 MoveIt 配置入口。
- **目标没有 frame 或四元数全零**：MoveIt 无法可靠解释目标；保持 `panda_link0` 和 `orientation.w = 1.0`。
- **一启动就失败**：控制器可能尚未发布第一条关节状态。等待几秒后重新运行 launch，或检查 `ros2 control list_controllers`。
- **以为现在连接了真实机器人**：Panda demo 使用 mock components。真实机械臂还需要硬件接口、标定、速度/力限制、急停和独立安全链路。

## 下一步

下一节将继续使用 Python：把碰撞物加入 Planning Scene，并用 RViz 区分“目标能到达”与“整条路径安全”。

## 参考

- [MoveIt 官方：Your First C++ MoveIt Project](https://moveit.picknik.ai/main/doc/tutorials/your_first_project/your_first_project.html)
- [MoveIt 官方：Motion Planning Python API](https://moveit.picknik.ai/main/doc/examples/motion_planning_python_api/motion_planning_python_api_tutorial.html)
- [官方 Python 教程的 launch 实现](https://github.com/moveit/moveit2_tutorials/blob/main/doc/examples/motion_planning_python_api/launch/motion_planning_python_api_tutorial.launch.py)
