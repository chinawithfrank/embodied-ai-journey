[← 第三个月：机器人视觉](../README.md) · [返回主页](../../../README.md) · **中文** | [English](README.en.md)

# 01 · YOLO 网球识别：从相机画面到像素坐标

“让机器人看见一个网球”听起来像一个很小的目标，但它第一次把机器人的输入从“人填写的坐标”换成了真实世界的相机画面。

本实验训练一个只认识 `tennis-ball` 的 YOLO 模型。运行时我手持网球面对摄像头，程序会画出边界框、置信度和中心像素坐标：

```text
tennis-ball 92% | pixel=(534, 287)
```

这里的 `(534, 287)` 是**像素坐标**：从图像左上角开始，右为 X 正方向、下为 Y 正方向。它很适合做“目标在画面左边还是右边”的决策，但不是米，也不能直接发送给 MoveIt 当作抓取点。

## 我为什么先做检测，而不是直接做抓取

MoveIt 的输入通常是一个机器人坐标系中的目标位姿；相机最开始能给我的却只是二维图片。YOLO 的作用是先完成“是什么、在哪里”的第一步：输出类别、边界框和图像中心点。后续还需要相机标定、深度或双目，才能把像素变成 `camera_link` 或 `world` 坐标。

```text
摄像头图像 → YOLO 边界框 → 像素中心 (u, v)
                                  ↓
                   标定 + 深度/多视角（下一阶段）
                                  ↓
                        机器人可用的三维坐标 (x, y, z)
```

## 数据集选择

默认下载 [Roboflow Universe 的 Tennis_Yolo](https://universe.roboflow.com/yolov8-training-o2cxu/tennis_yolo)：542 张已标注图像、一个 `tennis-ball` 类别、MIT 许可。下载脚本将它导出为 YOLO 格式，并记录生成的 `data.yaml` 路径。虽然数据集公开，Roboflow Python SDK 下载时仍要求登录或提供 API Key。

公开数据主要来自网球运动场景，**不能保证**对“室内、手拿、复杂背景”的网球同样可靠。这不是代码错误，而是训练数据与实际使用场景之间的差异。实验后半段会采集自己的手持样本；标注并加入训练集后再微调，才是让模型适应实际桌面场景的正确方法。

## 代码在哪里

- [`download_dataset.py`](../../../ros_ws/src/vision/yolo_tennis_ball/yolo_tennis_ball/download_dataset.py)：从公开数据集下载 YOLO 标签与图片。
- [`train.py`](../../../ros_ws/src/vision/yolo_tennis_ball/yolo_tennis_ball/train.py)：从 `yolo26n.pt` 微调单类别检测模型。
- [`webcam_detector.py`](../../../ros_ws/src/vision/yolo_tennis_ball/yolo_tennis_ball/webcam_detector.py)：打开摄像头，绘制框与 `(u, v)`；可选发布 ROS2 话题。
- [`capture_images.py`](../../../ros_ws/src/vision/yolo_tennis_ball/yolo_tennis_ball/capture_images.py)：采集自己的手持网球图片，作为后续补充数据。

## 环境准备

训练和 OpenCV 使用独立 Python 虚拟环境；这样不会把 PyTorch、YOLO 依赖混进系统 ROS2 安装。不要使用 `--system-site-packages`：它会把系统和用户目录中无关的包也暴露给虚拟环境。安装依赖时也先不要 source ROS2；如果当前终端已经 source 过，安装命令临时移除 `PYTHONPATH`，避免 pip 扫描 ROS2 的 Python 包并报告无关的依赖警告。

```bash
cd ~/develops/embodied-ai-journey/ros_ws/src/vision/yolo_tennis_ball

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
env -u PYTHONPATH python -m pip install -r requirements.txt
```

确认版本：`python -c "from importlib.metadata import version; print(version('ultralytics'))"`。这只读取安装信息，无需加载较慢的 PyTorch。`import ultralytics` 本身会导入 OpenCV、NumPy 和 PyTorch，不能用它的耗时单独判断 Ultralytics 哪里慢。本实验使用 Ultralytics `8.4.158` 及以上的 `8.4` 系列版本；你已安装的 `8.4.160` 符合要求。

如果 `.venv` 曾经用旧命令（带 `--system-site-packages`）创建，或安装日志出现系统中 `openxlab`、`types-seaborn` 等与本实验无关的冲突，建议删除后按上面的命令重建一次：

```bash
deactivate  # 若当前虚拟环境已激活
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
env -u PYTHONPATH python -m pip install -r requirements.txt
```

确认 GPU 是否被 PyTorch 看见：

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

如果结果是 `False CPU`，先按你 CUDA 版本安装匹配的 PyTorch；之后训练命令把 `--device 0` 改成 `--device cpu` 也能跑，只是更慢。

## 实验一：下载公开数据集

先在 [Roboflow](https://app.roboflow.com/) 注册或登录，打开自己 Workspace 的 **Settings → Roboflow API**，复制私有 API Key。下面的命令会在终端隐藏输入，不会把密钥写进仓库或 shell 历史；仅对当前终端有效：

```bash
read -rsp 'Roboflow API Key: ' ROBOFLOW_API_KEY; echo
export ROBOFLOW_API_KEY
```

然后下载：

```bash
cd ~/develops/embodied-ai-journey/ros_ws/src/vision/yolo_tennis_ball
source .venv/bin/activate
python -m yolo_tennis_ball.download_dataset --output data
```

脚本会打印实际的 `data.yaml` 路径，同时把该路径写入 `data/last_download.txt`。因此后续不需要猜 Roboflow 下载目录的名称。

## 实验二：训练自己的网球检测器

```bash
python -m yolo_tennis_ball.train \
  --data data/last_download.txt \
  --model yolo26n.pt \
  --epochs 80 \
  --imgsz 640 \
  --device 0
```

`yolo26n.pt` 是 YOLO26 的轻量预训练检测模型；本实验不是从零训练，而是让它在网球数据上微调。它由 Ultralytics 在首次使用时下载。若之前已用 YOLO11 训练出 `best.pt`，旧权重仍能使用；想使用 YOLO26 的权重则需要重新训练。训练产物会出现在：

```text
runs/tennis_ball_yolo26/weights/best.pt
```

训练结束时不要只看“完成”。打开 `runs/tennis_ball_yolo26/results.png`，重点看验证集的 precision、recall、mAP；这些指标只说明它在相近数据上的表现，不等于它已经适合手持网球的真实桌面环境。

如果你的机器在训练开始前打印 `Missing required CPU features: avx, avx2...`，然后以 `Illegal instruction (core dumped)` 退出，原因是默认的 Polars 二进制包与当前 CPU 指令集不兼容；GPU 型号并不能说明 CPU 一定支持 AVX。最新版依赖清单已包含兼容运行时，已有 `.venv` 只需补装并验证：

```bash
env -u PYTHONPATH python -m pip install "polars[rtcompat]>=1.44,<2"
python -c "import polars as pl; print(pl.__version__, pl.DataFrame({'x': [1]}).select(pl.sum('x')))"
```

验证后重新执行上面的训练命令，无需重新下载数据集。日志中的 GitHub 权重下载曾超时，但随后成功加载了预训练参数；大量 `NNPACK` 警告来自 CPU 优化库，并非这次崩溃原因。此前相对路径 `project=runs` 曾被 Ultralytics 解析到仓库根目录的 `runs/detect/runs/...`；脚本现传入绝对路径，后续权重会保存在本实验目录下的 `runs/tennis_ball_yolo26/weights/best.pt`。

## 实验三：面对摄像头识别网球并显示坐标

```bash
python -m yolo_tennis_ball.webcam_detector \
  --model runs/tennis_ball_yolo26/weights/best.pt \
  --camera 0 \
  --confidence 0.35
```

把网球放到镜头中，窗口应显示绿色框、红色中心点和 `pixel=(u, v)`。按 `q` 退出。如果外接摄像头不是编号 0，依次尝试 `--camera 1`、`--camera 2`。

## 实验四：把像素坐标发给 ROS2

发布 ROS2 话题前，在当前终端加载 ROS2 环境（激活 `.venv` 不会清除 ROS2 设置的 `PYTHONPATH`）：

```bash
source /opt/ros/jazzy/setup.bash
python -c "import rclpy; print('rclpy ready')"
python -m yolo_tennis_ball.webcam_detector \
  --model runs/tennis_ball_yolo26/weights/best.pt \
  --ros-topic /vision/tennis_ball_pixel
```

另一终端验证：

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /vision/tennis_ball_pixel
```

消息类型为 `geometry_msgs/PointStamped`：`point.x=u`、`point.y=v`、`point.z=confidence`，`header.frame_id` 为 `camera_pixels`。这是为了演示 ROS2 传递视觉结果，不表示它已经是三维空间中的 `Point`。

## 实验五：让它适应“手持网球”

公开网球赛事图像和我的桌面摄像头相差很大。我会采集至少 50 张自己的图片：不同距离、角度、光线、背景，也要包含没有网球的背景图。

```bash
python -m yolo_tennis_ball.capture_images --output captures/handheld
```

按空格保存一帧，按 `q` 退出。之后用 Roboflow Annotate、CVAT 或 Label Studio 为每个网球画框，类别保持为 `tennis-ball`，导出 YOLO 格式并合并进训练集，再重新训练。这个步骤比继续盲目增加 epoch 更能提升手持场景表现。

## 常见问题

- **`ModuleNotFoundError: ultralytics`**：确认已激活 `.venv`，再执行 `python -m pip install -r requirements.txt`。
- **`API Key is of Incorrect Type` / `NoneType`**：缺少 Roboflow API Key；按“实验一”设置 `ROBOFLOW_API_KEY`，在同一个终端重试。不要把真实密钥贴进 issue 或提交到 Git。
- **`Cannot open camera index 0`**：检查摄像头权限，或尝试 `--camera 1`。
- **框到的是黄色物品，不是网球**：提高 `--confidence`，并补充室内背景、黄色物体和手持网球的标注数据。
- **训练时 CUDA out of memory**：减小 `--batch`，例如 `--batch 8`；仍失败则降低 `--imgsz 512`。
- **安装日志显示依赖冲突，但最后是 `Successfully installed`**：本次安装已完成。例如 `generate-parameter-library-py` 缺少 `typeguard` 是 pip 看到了 ROS2 的包，不代表 YOLO 安装失败。以后安装依赖时用 `env -u PYTHONPATH python -m pip install -r requirements.txt`；若旧 `.venv` 带 `--system-site-packages`，按“环境准备”重建。
- **摄像头窗口报 `cv2.imshow` / `function is not implemented`**：Roboflow 可能带入无界面的 `opencv-python-headless`。在已激活的 `.venv` 中执行：`python -m pip uninstall -y opencv-python-headless`，然后执行 `python -m pip install --force-reinstall "opencv-python>=4.10,<5"`。
- **`--ros-topic` 提示没有 `rclpy`**：在启动检测器的终端执行 `source /opt/ros/jazzy/setup.bash`，再用 `python -c "import rclpy"` 验证；不要用 pip 安装 `rclpy`。

## 下一步

下一节不再满足于“网球在第 534 列像素”。我会标定相机，并引入深度或多视角，把二维像素点投影到机器人坐标系；那时视觉结果才能真正成为机械臂抓取任务的输入。
