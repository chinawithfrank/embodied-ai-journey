[中文](README.md) | **English**

# 🤖 Build Your Own Embodied AI Robot

> Follow my journey building real-world AI robots from zero.

A software engineer's journey into embodied intelligence.

I spent years building software systems.
Now I'm learning how to build machines that can see,
think and act in the physical world.

This repository documents my journey:
from ROS2 basics → robot simulation → perception →
AI agents → real-world robots.

Everything is open-source.
Everything is built step by step.

⭐ Star this repo if you are also exploring embodied AI.

---

## 🗺️ The Journey

```
software engineer ──► ROS2 basics ──► simulation ──► perception ──► AI agents ──► real-world robot
```

Every chapter follows the same loop: **Learn → Build → Share**.
I hit a real problem, learn the concept behind it, build something small
that proves I understand it, and share exactly what went wrong along the way.

## 📚 Chapters

| # | Chapter | Status | Notes |
|---|---------|--------|-------|
| 00 | [Why Embodied AI](notes/00-Why-Embodied-AI) | ✅ Published | Why a software engineer is betting on physical intelligence |

More chapters (ROS2 fundamentals, TF2 coordinate systems, simulation, perception, AI agents, real-world deployment…) get added here as each one is actually written.

## 🧭 How Each Chapter Is Written

Every chapter in [`notes/`](notes) follows the same template
(see [`notes/TEMPLATE.md`](notes/TEMPLATE.md)), so you always know what to expect:

```
# Title

## Why I learned this
The real-world problem — why a robot needs this capability.

## Concept
The plain-language explanation.

## Build
The actual code.

## Experiment
Screenshots / recordings of it running.

## What went wrong
The pitfalls I hit.

## Next step
Where this leads next.
```

## 🗂️ Repo Structure

```
embodied-ai-journey/
├── README.md          this file (Chinese)
├── README.en.md        English version
├── notes/              the journey, written chapter by chapter
│   ├── TEMPLATE.md
│   ├── 00-Why-Embodied-AI/
│   └── 01-Fundamentals/             month one: ROS2 Web Gateway v0.1
│       ├── 01-ROS2-Communication/
│       ├── 02-TF2-And-Coordinate-Systems/
│       └── 03-URDF-And-RViz/
└── ros_ws/             the ROS2 workspace — everything I build gets run here
    └── src/fundamentals/
        ├── ros2_fundamentals/
        ├── tf2_coordinate_systems/
        └── urdf_r2d2/
```

## ⭐ Follow Along

If you're a software engineer curious about robots, this repo is for you.
Star it, watch it, and follow along as the journey unfolds.
