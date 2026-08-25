[← 第二个月 MoveIt](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 03 · 不只是到达目标：纯 Python 绕障规划实验

上一节里，我已经能在 RViz 看到一条轨迹。但一条轨迹看起来很漂亮，不代表它在真实工作空间中安全。现在给机械臂与目标之间放上一面橙色的墙，问题才变得真实：**目标仍然可达时，MoveIt 会不会主动绕开它？**

官方教程用 C++ `PlanningSceneInterface` 把 `box1` 加进 `move_group`。本实验以 Python 完成同一件事，并且故意多走一步：同一个 `CollisionObject` 同时写入 Python `MoveItPy` 的本地 Planning Scene，以及 `move_group` 的 `/apply_planning_scene` 服务。前者决定 Python 规划会不会避障，后者让 RViz 与其他 MoveIt 客户端看到同一世界。

```text
CollisionObject(box1)
        ├──> MoveItPy Planning Scene ──> Python plan() 的碰撞检查
        └──> /apply_planning_scene ───> move_group ──> RViz Planning Scene

目标 + box1 + 当前 /joint_states ──> OMPL ──> DisplayTrajectory ──> 审查 ──> execute()
```

这就是“看见障碍物”和“避开障碍物”的区别：橙色 Marker 只能让人看见；`CollisionObject.ADD` 才能让规划器把它当作不可穿越的几何体。

## 代码与官方教程的对应关系

实验继续放在 [`hello_moveit_py`](../../../ros_ws/src/moveit/hello_moveit_py)：

- [`planning_around_objects.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/planning_around_objects.py)：创建目标、`box1`、Planning Scene 同步、Marker、规划与执行服务。
- [`planning_around_objects.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/planning_around_objects.launch.py)：启动 Python 节点、`move_group`、Panda mock controller、TF、robot state publisher 和 RViz。

官方示例的关键数据保持不变：

```text
目标 frame: panda_link0
目标 position: (0.10, 0.40, 0.40) m
目标 orientation: (x=0.0, y=0.8, z=0.0, w=0.6)

障碍物 ID: box1
障碍物中心: (0.20, 0.20, 0.25) m
障碍物尺寸: (0.50, 0.10, 0.50) m
```

盒子的 pose 表示**中心**，因此它是一面从 `z = 0.0` 到 `z = 0.5` 的竖直薄墙。红、绿、蓝目标轴会根据目标四元数旋转，不再只是固定在世界坐标系中；这是这节第一次能直观看到“姿态也会影响规划”。

## 构建

环境为 **Ubuntu 24.04 + ROS 2 Jazzy**：

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

若这是第一次学习 MoveIt，还需要：

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config
```

## 实验步骤：先确认世界，再请求路径

### 1. 启动完整场景

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
ros2 launch hello_moveit_py planning_around_objects.launch.py
```

等待终端输出：

```text
[INFO] [python_object_planner]: box1 is active in MoveItPy and move_group Planning Scenes.
```

这句日志很重要。程序在 `move_group` 服务尚未就绪时不会接受规划请求，避免出现“RViz 里有盒子，但实际场景还没有它”的误判。

### 2. 配置 RViz 的两层显示

1. 在左侧 `Displays` 点击 `Add`，添加 `MarkerArray`。
2. 将 MarkerArray 的 `Topic` 设置为 `/rviz_visual_tools`。
3. 保持 `MotionPlanning` 启用；在 `Planned Path` 中确认 `Show Robot Visual` 已勾选、轨迹 Topic 为 `/display_planned_path`。

MarkerArray 会显示标题、金色目标球、旋转的三色坐标轴和橙红色 `box1`。MotionPlanning 会显示真实 `RobotTrajectory` 预览。两者都要看：第一个帮助理解世界，第二个帮助判断规划是否绕障。

### 3. 检查目标和障碍物

另开一个已 source 的终端：

```bash
ros2 service call /python_object_planner/show_scene std_srvs/srv/Trigger "{}"
```

观察到橙红色墙位于 Panda 前方，白色标签为 `COLLISION / box1`，金色球位于墙的另一侧。此时不要急着执行：先用鼠标旋转 RViz，确认直线到目标会被墙阻挡。这是“为什么需要规划”的第一手证据。

### 4. 规划绕行轨迹

```bash
ros2 service call /python_object_planner/plan std_srvs/srv/Trigger "{}"
```

成功时返回：

```text
success=True
message='Published a collision-aware trajectory to RViz.'
```

机械臂的 Planned Path 出现，但当前场景机器人仍静止。绕不同方向是正常的：OMPL 可找到多条合法路径，重复运行不一定得到完全相同的关节轨迹。判断标准不是“形状是否固定”，而是路径中的机械臂不穿过 `box1`。

### 5. 执行已经看过的安全轨迹

```bash
ros2 service call /python_object_planner/execute std_srvs/srv/Trigger "{}"
```

只有这一步才调用 `moveit_py.execute()`；Panda mock controller 更新 `/joint_states`，RViz 场景机器人随轨迹运动。执行后 `box1` 仍留在 Planning Scene，说明障碍物是环境状态，而不是一次规划结束后自动消失的绘图效果。

## 哪段代码真正让机械臂绕开盒子

核心不是橙红色 Cube Marker，而是这三层代码：

```python
collision_object.operation = CollisionObject.ADD
scene.apply_collision_object(self.collision_object)
request.scene.world.collision_objects.append(self.collision_object)
```

- `ADD` 说明本次消息把一个新物体加入碰撞世界；同一个 ID 的后续 ADD 会更新它。
- `scene.apply_collision_object()` 将盒子加入 `MoveItPy` 内部场景，`self.panda_arm.plan()` 因而在此世界中寻找路径。
- `ApplyPlanningScene` 请求把相同盒子交给 `move_group`，使 RViz 的规划场景、其他客户端和 Python 看到一致的障碍物。

`Marker.CUBE` 只负责展示。把 `create_box_marker()` 删掉，规划仍然会避障；反过来，只留下 Marker 而删除碰撞物写入，轨迹可能直接穿过“看得到的墙”。

## 把实验变成自己的问题

在 [`planning_around_objects.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/planning_around_objects.py) 顶部修改：

```python
BOX_DIMENSIONS = (0.50, 0.10, 0.50)
BOX_POSITION = (0.20, 0.20, 0.25)
```

每次只改一个变量并重启实验。建议依次尝试：

1. 把 `BOX_POSITION` 的 Y 增大到 `0.35`，观察机械臂哪一侧更容易通过。
2. 把 `BOX_DIMENSIONS` 的 X 增大，直到规划失败；失败不是 bug，而是“没有碰撞自由路径”的答案。
3. 将盒子移开后再次规划，对比没有障碍物和有障碍物时的轨迹。

## 常见问题

- **服务提示等待 `box1`**：`move_group` 还在启动。等待成功日志后再调用 `plan`。
- **能看到墙但轨迹穿过它**：检查是否使用了本节的 `planning_around_objects.launch.py`，而不是上一节的 `visualizing.launch.py`；同时确认终端出现 `box1 is active...`。
- **没有看到墙或目标球**：添加 `MarkerArray`，Topic 必须是 `/rviz_visual_tools`。
- **看不到路径预览**：检查 `MotionPlanning → Planned Path → Show Robot Visual` 和 `/display_planned_path`。
- **规划失败**：目标可能不可达，或你把墙加宽到封死了所有通道。先恢复官方尺寸验证基线。

## 这节真正学到的事

碰撞检测不是 RViz 的视觉效果，而是 Planning Scene 中的数据约束。一个未来来自相机、激光雷达或网页配置的障碍物，最终都要变成带 frame、形状、pose、ID 和操作类型的 `CollisionObject`。当这条数据链正确时，规划器才有理由为安全绕路。

## 参考

- [MoveIt 官方：Planning Around Objects](https://moveit.picknik.ai/main/doc/tutorials/planning_around_objects/planning_around_objects.html)
- [MoveIt 官方：Visualizing in RViz](https://moveit.picknik.ai/main/doc/tutorials/visualizing_in_rviz/visualizing_in_rviz.html)
