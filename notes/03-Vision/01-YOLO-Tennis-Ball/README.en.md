[← Month Three: Vision](../README.en.md) · [Home](../../../README.en.md) · [中文](README.md) | **English**

# 01 · YOLO Tennis-Ball Detection: from webcam image to pixel coordinates

This first vision lab fine-tunes a one-class YOLO detector for `tennis-ball`. A webcam window draws the bounding box, confidence, and the centre pixel coordinate:

```text
tennis-ball 92% | pixel=(534, 287)
```

`(u, v)` is a **pixel coordinate**, measured from the top-left corner of the image. It says where the ball appears in a frame, not where it is in metres. Camera calibration plus depth or multi-view geometry are needed before this can become a robot-frame 3D grasp point.

## Dataset

The default downloader uses the public [Tennis_Yolo dataset on Roboflow Universe](https://universe.roboflow.com/yolov8-training-o2cxu/tennis_yolo): 542 annotated images, one `tennis-ball` class, MIT licence. It is exported as a YOLO dataset by the script. The Roboflow Python SDK requires an API key or login even for this public download.

The public data is mainly tennis-sport imagery, so it cannot guarantee reliable indoor, hand-held detection. Capture and label your own hand-held samples before making accuracy claims about the target setting.

## Setup

Use an isolated virtual environment. Do not use `--system-site-packages`: it exposes unrelated user and system packages. Install dependencies without ROS 2's `PYTHONPATH` so pip does not report conflicts from ROS 2 packages. Source ROS 2 only when running the optional ROS publisher.

```bash
cd ~/develops/embodied-ai-journey/ros_ws/src/vision/yolo_tennis_ball
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
env -u PYTHONPATH python -m pip install -r requirements.txt
```

Check the installed version with `python -c "from importlib.metadata import version; print(version('ultralytics'))"`. This reads package metadata without importing the slower PyTorch dependency. Importing Ultralytics itself loads OpenCV, NumPy, and PyTorch. This lab uses YOLO26 with Ultralytics `8.4.158` or newer in the `8.4` series; your installed `8.4.160` qualifies.

If an earlier environment used `--system-site-packages`, recreate it with the commands above. Do not install `rclpy` with pip. If `cv2.imshow` reports that the function is not implemented, remove Roboflow's headless OpenCV package and reinstall the GUI build:

```bash
python -m pip uninstall -y opencv-python-headless
python -m pip install --force-reinstall "opencv-python>=4.10,<5"
```

## Run the experiment

Sign in at [Roboflow](https://app.roboflow.com/), open your workspace's **Settings → Roboflow API**, and copy the private API key. Enter it without saving it to shell history or the repository:

```bash
read -rsp 'Roboflow API Key: ' ROBOFLOW_API_KEY; echo
export ROBOFLOW_API_KEY
```

```bash
# Download public YOLO labels and images.
python -m yolo_tennis_ball.download_dataset --output data

# Fine-tune a small pretrained YOLO26 model on an NVIDIA GPU.
python -m yolo_tennis_ball.train --data data/last_download.txt --model yolo26n.pt --device 0

# Show a webcam box, confidence, and centre pixel coordinate.
python -m yolo_tennis_ball.webcam_detector \
  --model runs/tennis_ball_yolo26/weights/best.pt
```

Press `q` to close the webcam window. Add `--ros-topic /vision/tennis_ball_pixel` to publish `geometry_msgs/PointStamped`, where `x=u`, `y=v`, and `z=confidence`.

Existing YOLO11 `best.pt` files still work for inference. Train again to produce YOLO26 weights.

If training exits with `Missing required CPU features` followed by `Illegal instruction`, install Polars' compatible runtime in the existing virtual environment, then rerun training without downloading the dataset again:

```bash
env -u PYTHONPATH python -m pip install "polars[rtcompat]>=1.44,<2"
python -c "import polars as pl; print(pl.__version__, pl.DataFrame({'x': [1]}).select(pl.sum('x')))"
```

The dependency list now requests this runtime for new installations. Training passes an absolute project path to Ultralytics so weights land in this lab's `runs/tennis_ball_yolo26/weights/best.pt`, matching the webcam command. GitHub timeouts may delay the first weights download; the logged pretrained transfer confirms it eventually succeeded. NNPACK warnings are separate from the Polars crash.

Before using `--ros-topic`, run `source /opt/ros/jazzy/setup.bash` in the same terminal and check `python -c "import rclpy"`. A pip warning that `generate-parameter-library-py` requires `typeguard`, followed by `Successfully installed`, means the YOLO dependencies installed; pip saw an unrelated ROS 2 package through `PYTHONPATH`.

To improve performance on a hand-held ball, run `python -m yolo_tennis_ball.capture_images`, annotate the saved frames with the same class name, merge them into the training data, and fine-tune again.
