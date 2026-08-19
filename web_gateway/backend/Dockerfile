FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-pip \
    ros-jazzy-rosbag2 \
    ros-jazzy-rosbag2-storage-mcap \
    ros-jazzy-turtlesim \
    && rm -rf /var/lib/apt/lists/*

COPY ros_ws/src /workspace/ros_ws/src
RUN . /opt/ros/jazzy/setup.sh && \
    cd /workspace/ros_ws && \
    colcon build --symlink-install

COPY web_gateway/backend/requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    -r /tmp/requirements.txt

COPY web_gateway/backend/app /workspace/web_gateway/backend/app
COPY web_gateway/backend/start_gateway.sh /workspace/web_gateway/backend/start_gateway.sh
ENV PYTHONPATH=/workspace/web_gateway/backend
RUN chmod +x /workspace/web_gateway/backend/start_gateway.sh && \
    mkdir -p /recordings

CMD ["/workspace/web_gateway/backend/start_gateway.sh"]
