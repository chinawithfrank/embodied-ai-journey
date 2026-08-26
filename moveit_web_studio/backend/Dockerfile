FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-pip \
    ros-jazzy-moveit \
    ros-jazzy-moveit-resources-panda-moveit-config \
    ros-jazzy-rosbridge-suite \
    && rm -rf /var/lib/apt/lists/*

COPY ros_ws/src/moveit /workspace/ros_ws/src/moveit
RUN . /opt/ros/jazzy/setup.sh && \
    cd /workspace/ros_ws && \
    colcon build --symlink-install --packages-select hello_moveit_py

COPY moveit_web_studio/backend/requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    -r /tmp/requirements.txt

COPY moveit_web_studio/backend/app /workspace/moveit_web_studio/backend/app
COPY moveit_web_studio/backend/start.sh /workspace/moveit_web_studio/backend/start.sh
RUN chmod +x /workspace/moveit_web_studio/backend/start.sh

CMD ["/workspace/moveit_web_studio/backend/start.sh"]
