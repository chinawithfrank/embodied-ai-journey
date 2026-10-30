[← Home](../../README.en.md) · [中文](README.md) | **English**

# Fan Robot: From Seeing to Acting

The goal is a small mobile robot that uses a fan to influence the world: aim at a hand, or eventually blow a floor balloon toward a goal. This is a real hardware project, not a claim that a fourth month has already been completed.

Before training any policy, I need a dependable observation. If images are missing or delayed, a failed action might be a perception problem rather than a learning problem.

| Experiment | Scope |
|---|---|
| [01 · ESP32-S3 and OV2640: First Eyes](01-ESP32-Camera/README.en.md) | User confirmed real browser video; acquisition and transport working; Python snapshots and stability still to verify |
| [02 · Offline Hand Detection on ESP32](02-Offline-Hand-Detection/README.en.md) | S3-local inference and optional AP preview without computer/Internet dependency; physical detection acceptance pending |
| [03 · Manual Dual N20 Control, Camera Retained](03-Manual-Motor-Control/README.en.md) | MotorA turns at80% PWM, not60%;10–100% range,20% default; dual-motor guide added, MotorB/coexistence pending |
| [04 · Independent5V Fan, Camera and Motors Retained](04-Manual-Fan-Control/README.en.md) | Delta two-wire fan and LR7843 labels identified; shared4.5V battery wiring added; low-voltage switching/coexistence pending, disabled by default |

All experiment code lives in [`ros_ws/src/fan_robot`](../../ros_ws/src/fan_robot). Notes stay here. Experiment02 adds offline hand detection; experiment03 adds manual motors beside camera video. Experiment04 reuses the latter and adds a separate fan switch, without integrating hand inference or autonomous following. Original sketches remain available. Physical airflow/coexistence acceptance, vehicle integration, visual closed-loop control and reinforcement learning remain future work.
