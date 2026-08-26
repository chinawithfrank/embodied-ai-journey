[← 第二个月 MoveIt](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 04 · 严格复现 MTC 抓取放置教程：纯 Python 版

前一版实验参考了 MTC 仓库中另一份较早的 Python `Pick` / `Place` 示例。它的物体位置、任务容器和阶段参数都与本节指定教程不同，导致“看起来类似”，但调试时无法用教程逐行对照。

这一版以[用户指定的 MTC 教程](https://ros.ncnynl.com/cn/moveit2/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)为唯一基线：保留教程的场景数值、任务属性、阶段顺序、IK 数量、笛卡尔距离、连接超时和回到 `ready` 的收尾动作。代码仍是 Python；不同之处仅是把 C++ API 翻译为 Jazzy Python binding 的属性写法。

Jazzy Python binding 中，`SerialContainer` 位于 `moveit.task_constructor.core`，而各个具体动作 Stage 位于 `moveit.task_constructor.stages`；因此代码使用 `core.SerialContainer(...)`。

Python binding 还遵循 C++ 的所有权转移：`task.add(stage)` 或 `container.add(stage)` 后，原来的 Python 变量不应再传入其他 API。需要监控已加入容器的阶段时，使用任务树查找，例如 `task['current state']` 或 `task['pick object']['attach object']`。

```text
current state → open hand → move to pick
    → pick object: approach → grasp IK → allow collision → close → attach → lift
    → move to place
    → place object: place IK → open → forbid collision → detach → retreat
    → return home
```

## 这次严格对齐了什么

| 项目 | 教程配置 | 本实验实现 |
| --- | --- | --- |
| 物体 | `world` 中圆柱体，高 `0.1 m`、半径 `0.02 m` | 完全一致 |
| 物体位置 | `x=0.5`、`y=-0.25` | 完全一致 |
| 规划组 | `panda_arm` 与 `hand` | 完全一致 |
| 初始动作 | `open hand`，关节插值 | 完全一致 |
| 接近 | 手坐标系 Z+，`0.1–0.15 m` | 完全一致 |
| 抓取采样 | `π / 12`，最多 8 个 IK，间距 `1.0` | 完全一致 |
| 抬起 | world Z+，`0.1–0.3 m` | 完全一致 |
| 放置目标 | 相对 `object` 的 Y+ `0.5 m`，最多 2 个 IK | 完全一致 |
| 撤离 | world X-，`0.1–0.3 m` | 完全一致 |
| 连接阶段 | 每段 `5 s`；放置连接同时规划手臂和手爪 | 完全一致 |
| 收尾 | 关节插值回到 `ready` | 完全一致 |

之前日志里出现的 `panda_finger_joint1` 偏差，正是“连接阶段只规划手臂、未处理手爪状态”的线索。现在 `move to place` 使用：

```python
[
    ('panda_arm', sampling_planner),
    ('hand', interpolation_planner),
]
```

因此它会分别处理手臂的自由空间路径和手爪的关节状态，再合并为完整任务解。

## 代码在哪里

- [`mtc_scene_setup.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/mtc_scene_setup.py)：通过 ROS 2 的 `/apply_planning_scene` 创建教程中的圆柱体。
- [`mtc_pick_place.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/mtc_pick_place.py)：按教程的完整阶段树构建、规划、发布并执行任务。
- [`mtc_pick_place.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/mtc_pick_place.launch.py)：启动 `move_group`、mock controller、RViz、静态 TF 和两个 Python 节点。

教程中的 `PlanningSceneInterface` 在 Jazzy Python 环境中不可用，因此场景创建改用等价的 `ApplyPlanningScene` 服务；这不改变碰撞对象的内容和时序。

## 运行前准备

MTC Python binding 需要从源码构建，并且必须放在当前 ROS 工作空间：

```bash
source /opt/ros/jazzy/setup.bash
cd ~/develops/embodied-ai-journey/ros_ws/src
git clone --branch ros2 https://github.com/moveit/moveit_task_constructor.git

cd ..
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install --packages-up-to hello_moveit_py
source install/setup.bash
```

如果 `moveit_task_constructor` 已存在，不要重复 clone；直接重新构建即可。验证绑定与可视化插件：

```bash
python3 -c "from moveit.task_constructor import core, stages; print('MTC Python ready')"
ros2 pkg prefix moveit_task_constructor_visualization
```

## 启动与预期效果

```bash
cd ~/develops/embodied-ai-journey/ros_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch hello_moveit_py mtc_pick_place.launch.py
```

按顺序观察终端：

```text
MTC object is active in the MoveIt Planning Scene.
MTC found a solution and is sending it to the mock controller.
MTC pick-and-place execution completed successfully.
```

第二行表示已经得到完整任务解；第三行表示任务已通过 `ExecuteTaskSolutionCapability` 下发到 Panda mock controller。**这版会自动执行，不需要点击普通 MotionPlanning 的 `Plan & Execute`。**

`task.plan(5)` 中的 `5` 是“最多找到 5 个成功任务解”，不是 5 秒超时；每个 `Connect` 阶段自己的超时才是 `5.0 s`。

## 在 RViz 看学习过程

自动执行并不妨碍观察任务树。为了避免把鼠标目标规划和 MTC 执行混在一起：

1. 取消勾选普通的 `MotionPlanning` Display。
2. 将 `Fixed Frame` 设为 `world`。
3. 在 `Displays` 中添加 `moveit_task_constructor_visualization → Motion Planning Tasks`。
4. 设置 `Task Solution Topic` 为 `/solution`。
5. 单击 `pick object`、`move to place`、`place object` 等阶段，再选择右侧的成功或失败解查看动画。

本实验的执行来自 `task.execute(task.solutions[0])`，不是普通 RViz 的鼠标交互目标。若要重复执行，请重启 launch，让场景、当前状态和任务树从同一初始条件重新开始。

## 任务树如何工作

### 1. 先打开手，再连到抓取起点

`CurrentState` 从 `/joint_states` 拿到 Panda 的实际 mock 状态。`open hand` 让手爪处于 SRDF 的 `open` 命名姿态；随后 `move to pick` 使用 OMPL 只为 `panda_arm` 寻找自由空间路径。这个顺序避免把“抓物”错误地当成一个孤立的末端位姿。

### 2. Pick 是一个串行容器

`pick object` 内部不依赖旧版 `SimpleGrasp` 包装器，而是把每步明确写出来：先沿 `panda_hand` 的正 Z 方向接近 `0.1–0.15 m`；`GenerateGraspPose` 每 `15°` 采样一次；`ComputeIK` 最多保留 8 个且彼此至少相距 `1.0` 的关节解。

接着 `ModifyPlanningScene` 临时允许手与物体碰撞，手爪闭合，再把物体附着到 `panda_hand`。最后沿 world 正 Z 抬起 `0.1–0.3 m`。附着这一步很重要：从此以后，物体会随手运动并参与碰撞检测。

### 3. Place 也从“物体状态”推导

`move to place` 同时处理 `panda_arm` 和 `hand`，把抓取末态连接到放置候选。放置候选不是硬编码世界坐标：目标表达为 `object` 坐标系中 Y+ `0.5 m`，并监控 `attach object` 阶段。这让 MTC 能知道物体相对手的真实附着变换。

放置后任务会打开手、恢复手与物体的碰撞、分离物体、沿 world X- 撤离 `0.1–0.3 m`，最后回到 `ready`。这正是一个可执行操作应该具备的“收尾状态”，而不只是把手移到某处。

## 排错顺序

- **没有 `MTC found a solution...`**：只看末尾的 `Failing stage(s)`。阶段树会告诉你失败在抓取 IK、接近、`move to place` 还是撤离。
- **出现 `MTC task execution failed with code`**：检查 `ros2 control list_controllers`，确认 `panda_arm_controller`、`panda_hand_controller` 和 `joint_state_broadcaster` 都是 `active`。
- **出现普通 RViz 的 `MoveGroupInterface::move()` 或 `Plan & Execute request aborted`**：这是普通 MotionPlanning Display 在规划鼠标目标，不是本实验任务；取消勾选该 Display。
- **`No default projection is set`**：这是 OMPL 的诊断输出。只有伴随某个 `Failing stage(s)` 才需要定位那个阶段的目标、碰撞或 IK。
- **KDL root inertia 警告**：来自 Panda URDF 与 KDL 的已知兼容性提示，不等同于任务失败。

## 下一步可以怎样改

成功跑通后，每次只改一个参数：把 `grasp_generator.angle_delta` 改为 `pi / 6` 比较候选数量；移动圆柱的 X/Y 观察可达性边界；或者把放置相对位移从 Y+ `0.5` 改短。每次都从 `Failing stage(s)` 反推是哪一个阶段拒绝了状态，而不是直接关闭碰撞检测。

## 参考

- [用户指定：使用 MoveIt 任务构造器进行拾取和放置](https://ros.ncnynl.com/cn/moveit2/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)
- [MoveIt 官方英文教程](https://moveit.picknik.ai/main/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)
