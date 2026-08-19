[← 第一个月 Fundamentals](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 06 · ROS2 Web Gateway v0.1：让一次机器人实验能被操作与复盘

到这里，ROS2 的 Topic、Service、Action、TF、RViz 和 rosbag2 都各自跑通了。但它们散落在很多终端里：我知道该输入什么命令，别人却很难看懂机器人现在是否在线、任务是否还在执行、刚才发生了什么。

**ROS2 Web Gateway v0.1** 是本月的收口产品。它不是“把所有 ROS2 都暴露到网页”的危险代理，而是一个面向本地实验的、受限的控制台：把一段真实 ROS2 运行变成可观察、可操作、可留下证据的闭环。

## 月末展示：我能证明什么

打开 `http://localhost:3001` 后，页面能完成下面的故事：

1. 看到 ROS2 bridge 是否连接，以及 R2D2 的 `/joint_states` 是否仍在更新；
2. 用网页调用演示电机 Service，看到网关事件日志；
3. 从网页创建一个无界面的模拟转向 Action，看到状态、反馈进度，并可请求取消；
4. 点击“开始录制”，让网关将关节状态与 Marker 写入 MCAP；
5. 点击“停止并保存”，在页面看到本次记录和文件大小；
6. 用 `ros2 bag info` 检查这份记录，必要时继续使用第 05 章的 RViz 回放流程。

这回答了路线图中的七件事：机器人在线状态、传感器/状态数据、任务创建、进度、取消、日志与 MCAP 录制。当前的“传感器数据”是 R2D2 的关节状态；真实设备接入时，只需在同一个白名单模式下增加经过审核的传感器摘要，而不是把原始 topic 全部裸露给浏览器。

## 架构：浏览器不是 ROS2 节点

```text
Next.js Dashboard (3001)
        │ HTTP + WebSocket
        ▼
FastAPI Gateway (8000) ─── ROS2 allowlist ─── ROS2 Demo Graph
        │                         │                 ├─ /joint_states
        │                         │                 ├─ /set_motors_enabled
        │                         │                 └─ /turtle1/rotate_absolute
        │                         ▼
        └──────────── ros2 bag record --storage mcap ──> Docker volume
```

Gateway 是唯一理解浏览器请求的一层。它在独立的 ROS2 executor 线程中订阅数据，FastAPI 再通过 WebSocket 推送快照。这样 Web 事件循环不会被 ROS2 的 spin 阻塞，ROS2 回调也不会直接操作浏览器连接。

## 代码在哪里

```text
web_gateway/
├── backend/                         # FastAPI、rclpy bridge、MCAP 进程管理
├── frontend/                        # Next.js Dashboard
└── docker-compose.yml               # Gateway（内置 demo ROS 图）与 Dashboard 两个服务

ros_ws/src/fundamentals/web_gateway_demo/
└── launch/demo.launch.py            # R2D2、Marker、Service、无界面 Action 的演示 ROS 图
```

关键实现：

- [`ros_bridge.py`](../../../web_gateway/backend/app/ros_bridge.py) 是受限 ROS API：只能读取 `/joint_states`，只能调用一个 `SetBool` Service 和一个 `RotateAbsolute` Action。
- [`recordings.py`](../../../web_gateway/backend/app/recordings.py) 固定录制 `/joint_states` 与 `/visualization_marker`，并总是使用 `--storage mcap`。
- [`main.py`](../../../web_gateway/backend/app/main.py) 提供 HTTP API 与 WebSocket，不把 rclpy 对象泄露到请求处理层。
- [`demo.launch.py`](../../../ros_ws/src/fundamentals/web_gateway_demo/launch/demo.launch.py) 把以前的实验组合成一个可展示的 ROS 图。

## 一键启动

Gateway 容器会同时启动 ROS2 演示图与 FastAPI，因此 rclpy bridge 与 ROS 节点在同一容器内通信，不依赖跨容器 DDS 发现。演示 Action 没有 GUI，也不会再因为缺少 `DISPLAY` 而崩溃。

在仓库根目录执行：

```bash
docker compose --env-file web_gateway/.env.example \
  -f web_gateway/docker-compose.yml up --build
```

首次构建会下载 ROS Jazzy、Python 与 Node 镜像，耐心等待。看到 Dashboard 服务监听 `3001` 后，在浏览器打开：

```text
http://localhost:3001
```

保留 Compose 终端不要关闭。结束服务时，另开终端：

```bash
docker compose -f web_gateway/docker-compose.yml down
```

不要在想保留录制时加 `-v`，因为 MCAP 放在名为 `gateway-recordings` 的 Docker volume 中。

## 三分钟验收脚本

### 0:00–0:30：证明数据链路

页面顶部应显示“机器人在线”；R2D2 关节卡片每隔几百毫秒更新，最后状态时间持续前进。若没有，先看：

```bash
docker compose -f web_gateway/docker-compose.yml logs gateway
```

### 0:30–1:20：证明任务链路

1. 点击“启用电机”，日志中应出现 `Motors are enabled.`；
2. 输入 `90`，点击“创建任务”；
3. 任务卡显示 `queued` / `running`、进度条和最终状态；
4. 再建一个旋转任务，趁运行时点击“取消”。

无界面 Action Server 使用与 turtlesim 相同的 `RotateAbsolute` 消息类型，但不启动图形窗口，也不控制实体硬件。若想从 ROS2 侧确认 Action 已注册：

```bash
docker compose -f web_gateway/docker-compose.yml exec gateway \
  bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list'
```

### 1:20–2:10：证明运行可以留住

1. 点击“开始录制”，让它运行 10 秒；
2. 点击“停止并保存”，记录列表应出现 `run-YYYYMMDD-HHMMSS`；
3. 检查内容：

```bash
docker compose -f web_gateway/docker-compose.yml exec gateway \
  bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 bag info /recordings/run-*'
```

输出应包含 `mcap`、`/joint_states` 与 `/visualization_marker`。这一点把第 05 章的手动 rosbag2 实验变成了网页可触发的运行证据。

### 2:10–3:00：说清边界

最后展示日志，并说明：页面**不能**发布任意 topic、调用任意 service 或传入任意 action 名称。它只是把开发和测试真正需要的几个能力封装为显式 API；真实机器人还要在此基础上补鉴权、审计、急停和独立安全控制器。

## HTTP API

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/api/status` | 在线、关节、Service 与录制状态快照 |
| `POST` | `/api/motors` | 调用白名单 `/set_motors_enabled` |
| `POST` | `/api/tasks` | 创建模拟转向 Action，body 为 `target_degrees` |
| `POST` | `/api/tasks/{id}/cancel` | 请求取消已接受的任务 |
| `GET` | `/api/logs` | 网关最近 200 条事件 |
| `GET/POST` | `/api/recordings` | 列出记录 / 开始新的 MCAP 记录 |
| `POST` | `/api/recordings/stop` | 正常停止当前记录 |
| `WS` | `/ws/telemetry` | 状态快照推送 |

浏览器不能指定 topic 名称、ROS 类型、Service 名称或 shell 命令；这正是 v0.1 有意保留的安全边界。

## 失败时先查什么

- 页面显示“未连接”：看 `gateway` 日志中 rclpy 是否启动；再确认两个 ROS 服务使用相同的 `ROS_DOMAIN_ID`。
- `robot_online` 一直为 false：演示图未启动或 `/joint_states` 没有到达 bridge；用 `docker compose ... logs gateway` 检查状态发布器和 bridge 的启动日志。
- Action 被拒绝：无界面转向服务还未准备好，稍等后重试；这也是 UI 把 ROS2 异常转换为可见反馈的例子。
- 停止录制后没有文件：查看 gateway 日志；容器内使用 `/recordings`，而不是宿主机的当前目录。
- 在真实机器人上使用：不要复用这个示例的“电机”按钮。真正的运动控制必须有独立的权限、限位、急停和硬件安全链路。

## 下一步

本月产品闭环已经成立。第二个月开始，应把 demo 数据源换成 Gazebo/真实传感器，并将 Gateway 演进为带身份认证、任务审计、数据保留策略和明确安全等级的机器人开发平台，而不是盲目扩大远程控制权限。
