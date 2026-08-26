# MoveIt Web Studio v0.1

第二个月的成果项目：在浏览器中创建 Panda 的受限抓取放置任务。

## 架构

- `frontend/`：Next.js、React Three Fiber、Three.js、URDF Loader 和 ROSLIB.js；加载 Web Panda URDF，订阅 `/joint_states`，编辑抓取与放置坐标。
- `backend/`：FastAPI 网关；仅接受范围受限的取放坐标，发布到 `/web_moveit/task_request`，并接收 `/web_moveit/task_status`。
- `ros_ws/src/moveit/hello_moveit_py/web_task_executor.py`：MoveItPy 执行器；按固定的靠近、闭爪、搬运、开爪、回位流程执行任务。

浏览器绝不会直接调用 `move_group`，也不能传递任意 ROS 命令或 shell 命令。

## Docker 启动

在仓库根目录运行：

```bash
docker compose -f moveit_web_studio/docker-compose.yml up --build
```

打开 `http://localhost:3002`。后端 API 为 `http://localhost:8001`，ROSLIB 使用 `ws://localhost:9092`。

首次构建会安装 MoveIt、rosbridge 和前端依赖，耗时较长。

## 本机开发

终端一：

```bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
ros2 launch hello_moveit_py web_moveit.launch.py
```

终端二：

```bash
source /opt/ros/jazzy/setup.bash
source ros_ws/install/setup.bash
cd moveit_web_studio/backend
python3 -m pip install --user --break-system-packages -r requirements.txt
python3 -m uvicorn app.main:app --app-dir . --host 0.0.0.0 --port 8001
```

不要用普通 Python `venv` 启动这个后端：`rclpy` 由 ROS2 Jazzy 的系统包提供，不在 PyPI。若终端显示 `(venv)`，先执行 `deactivate`，再 source ROS2 环境。

终端三：

```bash
cd moveit_web_studio/frontend
npm install
npm run dev
```

## 安全边界

- 仅允许 X/Y 在 `[-0.7, 0.7] m`、Z 在 `[0.03, 0.65] m` 的取放点。
- 同一时刻只允许一个任务排队。
- 演示使用 Panda mock controller；不面向真实机械臂。
