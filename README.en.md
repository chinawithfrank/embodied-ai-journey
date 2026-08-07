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
| 00 | [Why Embodied AI](notes/00-Why-Embodied-AI) | 📝 Draft | Why a software engineer is betting on physical intelligence |
| 01 | [Linux & Hardware](notes/01-Linux-And-Hardware) | 📝 Draft | Setting up the machine that will run a robot |
| 02 | [ROS2 Fundamentals](notes/02-ROS2-Fundamentals) | 📝 Draft | The nervous system that connects a robot's parts |
| 03 | [TF2 & Coordinate Systems](notes/03-TF2-And-Coordinate-Systems) | 📝 Draft | How I taught my robot to understand where things are |

More chapters (simulation, perception, AI agents, real-world deployment) are added as I get there.

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

Example — Chapter 03: *Understanding TF2*

> **Problem:** the robot's camera sees an object, but the robot's arm
> doesn't know where it is.
>
> **What I learned:** coordinate frames, transforms, the tf tree.
>
> **Build:** `camera_frame` → `base_link`.

## 🗂️ Repo Structure

```
embodied-ai-journey/
├── README.md          this file (Chinese)
├── README.en.md        English version
├── notes/              the journey, written chapter by chapter
│   ├── TEMPLATE.md
│   ├── 00-Why-Embodied-AI/
│   ├── 01-Linux-And-Hardware/
│   ├── 02-ROS2-Fundamentals/
│   └── 03-TF2-And-Coordinate-Systems/
└── ros_ws/             the ROS2 workspace — everything I build gets run here
    └── src/
```

## ⭐ Follow Along

If you're a software engineer curious about robots, this repo is for you.
Star it, watch it, and follow along as the journey unfolds.
