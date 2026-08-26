[← 返回主页](../../README.md) · **中文** | [English](README.en.md)

# 第二个月：MoveIt 与机械臂运动规划

> **本月方向：让机械臂从“能显示”走到“会规划、会执行、能解释为什么”。**

第一个月解决了机器人软件的骨架：节点怎样通信、状态怎样可视化、一次运行怎样记录，以及怎样把这些能力带到网页。第二个月开始面对一个新的问题：当我说“把末端移动到这里”时，机械臂怎样找到一条不撞自己、满足关节限制、又能被控制器执行的路径？

MoveIt 是这个问题的工作台。它不是一个简单的“机械臂移动函数”，而是一套把机器人模型、碰撞检测、运动学、规划器和控制器连接起来的框架。本月每个实验都会明确区分：**我给出了什么目标、MoveIt 计算了什么、控制器执行了什么、RViz 让我验证了什么。**

## 本月学习地图

### 已开始：第一次请求规划与执行

[01 · 第一个 MoveItPy 项目](01-Your-First-MoveIt-Project) 用 Python 的 `MoveItPy` 创建 `panda_arm` 规划组件，给末端设置位姿目标，在 RViz 的模拟控制器中规划并执行轨迹。这是从 ROS2 通信进入机械臂运动规划的第一条完整链路。

### 已完成：在执行前看懂轨迹

[02 · 在 RViz 中看懂一次规划](02-Visualizing-In-RViz-With-Python) 用纯 Python 发布目标 Marker 和 `DisplayTrajectory`，并将“显示目标 → 规划 → 执行”拆成三个可重复调用的 ROS2 服务。它回答了：屏幕上的图形究竟来自哪里，何时只是预览，何时才进入控制器。

### 已完成：让规划器看见障碍物

[03 · 纯 Python 绕障规划](03-Planning-Around-Objects-With-Python) 将同一个 `CollisionObject` 同步给 MoveItPy 与 `move_group`，用真实规划轨迹验证机械臂绕开 `box1`，而不是只在 RViz 中画一只盒子。

### 已完成：将抓取与放置组织成阶段任务

[04 · MTC 纯 Python 抓取放置](04-Pick-And-Place-With-MTC-Python) 使用 MoveIt Task Constructor 的 Python 绑定，将靠近、抓取、抬起、搬运、放下和撤离拆成可独立检查的任务阶段，并在 RViz 中查看整个解决方案树。

## 目录约定

```text
embodied-ai-journey/
├── ros_ws/
│   └── src/
│       ├── fundamentals/          # 第一个月的 ROS2 基础实验
│       └── moveit/
│           └── hello_moveit_py/   # 本月自己的 MoveIt Python 客户端
└── notes/
    └── 02-MoveIt/
        ├── README.md
        ├── 01-Your-First-MoveIt-Project/
        ├── 02-Visualizing-In-RViz-With-Python/
        ├── 03-Planning-Around-Objects-With-Python/
        └── 04-Pick-And-Place-With-MTC-Python/
```

第三方 MoveIt 资源不复制进这个仓库；实验直接使用系统安装的 `moveit_resources_panda_moveit_config`。我的代码、我的运行步骤和我的观察都留在这里，便于以后换成自己的机械臂配置包。

## 从零开始

本月环境使用 **Ubuntu 24.04 + ROS2 Jazzy**。安装 MoveIt 和 Panda 的官方演示配置：

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config
```

之后进入 [`01 · Your First MoveIt Project`](01-Your-First-MoveIt-Project)，按其中的两个终端步骤构建和运行。每个新终端都应先执行：

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
```

## 本月记录方式

这不是把 MoveIt API 按顺序抄一遍。我会持续记录目标位姿、规划组、碰撞场景、轨迹、执行反馈和失败原因之间的关系。以后接入真实机械臂时，最需要保留的不是“它动过一次”，而是“为什么它认为这条运动是安全且可执行的”。
