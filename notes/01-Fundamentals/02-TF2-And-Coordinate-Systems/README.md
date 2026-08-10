[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 02 · TF2 与坐标系：让数据知道自己在哪里

这一章让机器人开始理解“东西在哪里”。

## 为什么学这个

“检测到杯子”听起来像一个完整答案，直到我追问：它在谁的坐标系里？相机看见了物体，机械臂却不知道该往哪里伸，因为相机、底盘和每个关节各自使用不同的原点与方向。TF2 把这些局部视角连接成一棵树，让程序可以在任意两个已连接的 frame 之间查询位置和朝向。

这里没有假装成真实机器人：动态广播器只是让一个 `camera_link` 绕着 `base_link` 画圈。但这正好让变换随时间变化的事实变得可见。等到 Web Gateway 接入真实状态和日志时，TF 树会让一条数据不仅有数值，也有“它在哪里、在什么时候、相对于谁”的上下文。

### 这一步如何进入月末产品

- 机器人或传感器的 frame 关系会成为后端展示状态的上下文，而不是一串无出处的数字。
- `tf2_echo` 和 TF 树截图是调试证据：网页显示异常时，可以先确认坐标链路是否存在。
- 后续的 URDF、RViz 和 MCAP 会沿用这里的 `base_link → sensor_link` 思维，而不是再创建一套概念。

## 概念

- **坐标系（frame）**：描述位置和方向的参考，例如 `base_link`（机器人底盘）、`camera_link`（相机）和 `laser_link`（雷达）。ROS2 中常用右手系：`x` 向前、`y` 向左、`z` 向上。
- **变换（transform）**：一个 frame 相对其父 frame 的平移与旋转。平移使用米，旋转使用四元数；本章样例只绕 `z` 轴旋转，因此用 yaw（弧度）生成四元数。
- **TF 树（tf tree）**：所有 frame 的父子关系。每个 child frame 只能有一个父 frame，且不能形成环；这样 TF2 才能沿树自动组合多段变换。
- **静态变换**：不会变化的安装外参，例如底盘到固定雷达的距离；发布到 `/tf_static`。
- **动态变换**：会随时间变化的姿态，例如云台、关节或移动的相机；持续发布到 `/tf`。
- **查询方向**：`lookup_transform(target, source, ...)` 返回“把 `source` 中的坐标表示成 `target` 中的坐标”所需的变换。本章监听器默认查询 `camera_link` 在 `base_link` 中的位姿。

## 构建

代码位于 [`ros_ws/src/fundamentals/tf2_coordinate_systems`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems)，包含三个节点：

1. **静态广播器**（[`static_frame_broadcaster.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/static_frame_broadcaster.py)）—— 发布 `base_link → laser_link` 固定变换，模拟安装在机器人前方的雷达。
2. **动态广播器**（[`dynamic_frame_broadcaster.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/dynamic_frame_broadcaster.py)）—— 持续发布 `base_link → camera_link`，让相机沿圆周运动并改变 yaw，用于观察时间变化的 TF。
3. **监听器**（[`frame_listener.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/frame_listener.py)）—— 使用 `tf2_ros.Buffer` 缓存 TF，并每秒查询、打印目标 frame 中的平移与 yaw。

### 依赖

ROS2 Jazzy 桌面版通常已含运行依赖；若需要查看 TF 树或缺少工具，请安装：

```bash
sudo apt install ros-jazzy-tf2-tools
```

### 编译

在 `ros_ws` 目录下：

```bash
colcon build --packages-select tf2_coordinate_systems
source install/setup.bash
```

### 运行——实验一：动态变换与查询

需要两个终端，且都先执行 `source install/setup.bash`。

终端 1：启动动态广播器。

```bash
ros2 run tf2_coordinate_systems dynamic_frame_broadcaster
```

终端 2：启动监听器。

```bash
ros2 run tf2_coordinate_systems frame_listener
```

监听器会每秒输出类似内容：

```text
[INFO] [frame_listener]: camera_link in base_link: x=0.44, y=0.24, z=0.20, yaw=0.50 rad
```

也可以直接查询 TF2 缓存：

```bash
ros2 run tf2_ros tf2_echo base_link camera_link
```

通过参数调整轨迹半径和角速度：

```bash
ros2 run tf2_coordinate_systems dynamic_frame_broadcaster --ros-args \
  -p radius:=1.0 -p angular_speed:=1.2
```

### 运行——实验二：静态安装外参

启动静态广播器，默认发布“雷达在底盘前方 `0.2 m`、上方 `0.1 m`”：

```bash
ros2 run tf2_coordinate_systems static_frame_broadcaster
```

用参数模拟不同的安装位置和朝向：

```bash
ros2 run tf2_coordinate_systems static_frame_broadcaster --ros-args \
  -p x:=0.35 -p z:=0.15 -p yaw:=0.2
```

在另一终端验证：

```bash
ros2 run tf2_ros tf2_echo base_link laser_link
```

### 查看 TF 树

运行至少一个广播器后，在同一 ROS Domain 的终端执行：

```bash
ros2 run tf2_tools view_frames
```

该命令会在当前目录生成 `frames.pdf`，其中应包含 `base_link` 及其子 frame。也可运行 `rviz2`，添加 **TF** Display 直观查看坐标轴。

## 运行后应该看到什么

把下面三个现象当成实验完成条件，而不是可选项：

1. `frame_listener` 输出的 `x`、`y` 和 yaw 会持续变化，但 `z` 保持 `0.20`；这说明它查询的是同一个动态 frame，而不是打印随机值。
2. `tf2_echo base_link camera_link` 的结果与监听器方向一致：它表达的是 camera 在 base 中的位姿。
3. 同时运行静态广播器后，`view_frames` 生成的图中，`base_link` 下应同时出现 `camera_link` 与 `laser_link`。

第一次运行时，监听器先报“Waiting for …”是正常的：它在等待 TF 缓存收到第一条变换。记录这种短暂失败比删掉它更有价值，因为真实系统里的启动顺序问题会以同样方式出现。

## 踩过的坑

- frame 名称不要随意混用前导 `/`；本章全部使用 `base_link` 这类无前导斜杠的名称。
- `lookup_transform` 的参数顺序容易写反。先用一句话确认：“我要把 source 中的点转换到 target 中。”
- listener 刚启动时 TF 缓存可能为空，这是正常现象；捕获 `TransformException` 后等待下一次查询即可。
- 静态 frame 要用 `StaticTransformBroadcaster`，不要用低频动态广播器代替；前者会通过 `/tf_static` 保存给后加入的节点。
- 四元数不是欧拉角。样例只处理 yaw，真实三维姿态请使用完整四元数或可靠的转换库，避免手写复杂旋转公式。

## 下一步

下一章将把传感器数据转换到 `base_link` 或 `map` 等统一坐标系，再用于感知、定位和运动规划。
