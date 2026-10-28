[← Home](../../README.en.md) · [中文](README.md) | **English**

# Fan Robot: From Seeing to Acting

The goal is a small mobile robot that uses a fan to influence the world: aim at a hand, or eventually blow a floor balloon toward a goal. This is a real hardware project, not a claim that a fourth month has already been completed.

Before training any policy, I need a dependable observation. If images are missing or delayed, a failed action might be a perception problem rather than a learning problem.

| Experiment | Scope |
|---|---|
| [01 · ESP32-S3 and OV2640: First Eyes](01-ESP32-Camera/README.en.md) | User confirmed real browser video; acquisition and transport working; Python snapshots and stability still to verify |
| [02 · Offline Hand Detection on ESP32](02-Offline-Hand-Detection/README.en.md) | S3-local inference and optional AP preview without computer/Internet dependency; physical detection acceptance pending |

All experiment code lives in [`ros_ws/src/fan_robot`](../../ros_ws/src/fan_robot). Notes stay here. Experiment02 adds offline hand detection; physical verification is still required. Manual driving with safety stops, a rule-based closed loop, and reinforcement learning with a measurable objective and reset procedure remain future work.
