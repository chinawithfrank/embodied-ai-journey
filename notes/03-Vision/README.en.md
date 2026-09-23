[← Home](../../README.en.md) · [中文](README.md) | **English**

# Month Three: Robot Vision

> **Monthly direction: move from knowing how to act to understanding what is in front of the camera.**

The first two months covered ROS2 state flow and MoveIt motion planning. A robot also needs to perceive an object before it can decide what to grasp. This month begins with the smallest complete loop: capture an image, detect an object, report where it is in that image, and make the result available to the rest of the robot.

## Learning map

[01 · YOLO Tennis-Ball Detection and Pixel Coordinates](01-YOLO-Tennis-Ball) downloads a public annotated dataset, trains a one-class detector, draws the detection and image centre `(u, v)` on a webcam stream, and can optionally publish the result to ROS2.

## Important boundary

The first lab produces **pixel coordinates**, not metres. `(u, v)` answers where the ball appears in a frame; camera calibration plus depth or multiple views are required to recover a 3D robot-frame position. That distinction will guide the next labs.
