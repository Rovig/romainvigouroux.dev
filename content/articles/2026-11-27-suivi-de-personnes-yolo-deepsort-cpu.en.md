---
title: "Specify before you code: tracking people on CPU with YOLO11 and DeepSORT"
description: "A GPU-free person detection and tracking system, written by Claude Code from a precise technical specification: modules, configuration, constraints."
date: 2026-11-27
slug: people-tracking-yolo-deepsort-cpu
tags: [Computer vision, Agentic coding, Claude Code]
keywords: [YOLO11, DeepSORT, multi-object tracking, MOT20, CPU, specification, agentic coding]
tldr: "With a coding agent, the quality of the result depends mostly on the specification. One page fixing the file tree, each module's responsibility, the configuration and the constraints (CPU only, typing, error handling) was enough to get a modular, testable YOLO11 + DeepSORT tracker."
problem: "Detecting and tracking people in a video, keeping a stable identifier for each, on a machine without a GPU."
context: "Project for the RCP217 course (object detection and tracking), built in 2026 in Python 3.13 with Claude Code."
constraints:
  - "CPU-only execution, explicitly enforced"
  - "No hard-coded values: all configuration in one YAML file"
  - "Imposed architecture, one module per responsibility"
  - "Optional fine-tuning on the MOT20 dataset"
stack: [Python, YOLO11, DeepSORT, OpenCV, PyYAML, pytest, Claude Code]
outcome: "A command-line tool that tracks people in a video or from a webcam, drawing identifiers and trajectories, with a MOT20 fine-tuning script and tests. [TO CONFIRM: FPS measured on the machine used, grade obtained for the course]"
faq:
  - q: "Can you track people in real time without a GPU?"
    a: "Yes, provided you choose a light detector such as YOLO11 Nano and tune the tracker accordingly. The project documentation gives an expected order of magnitude of 8 to 12 frames per second on an Intel i7 or Apple M1 class processor; the real figure depends on video resolution."
  - q: "What is the difference between YOLO and DeepSORT?"
    a: "YOLO detects objects frame by frame, with no memory. DeepSORT links those detections over time: it gives each person an identifier and keeps it from one frame to the next using a motion model and visual re-identification features."
  - q: "How do you get good results from a coding agent like Claude Code?"
    a: "Give it a specification rather than an idea: expected file tree, each module's responsibility, configuration format, non-negotiable constraints and coding rules. The agent no longer has to guess the architecture, and the result can be checked point by point against the document."
---
With a coding agent, the quality of the result depends first on the quality of the request. For a CPU-based person
detection and tracking project, I wrote a one-page technical specification before handing the implementation to
Claude Code. The result is a modular, configurable and testable YOLO11 + DeepSORT system that runs without a GPU.

## The situation

The RCP217 course project was about a detection and tracking system: spotting every person in a video and keeping
the same identifier for them throughout the sequence. The constraint was set from the start: everything had to run
on CPU, with no GPU dependency.

## Why it's harder than it looks

**Detecting is not enough.** A detector like YOLO works frame by frame, with no memory. Tracking a person means
linking detections over time, despite crossings, occlusions and missed detections.

**The CPU forces trade-offs.** Without a GPU every choice matters: model size, confidence threshold, number of
confirmations before a track is validated. These settings must change without touching the code.

**A coding agent improvises if you let it.** A vague request produces an arbitrary architecture, hard-coded values
and implicit GPU dependencies. The code may work, but it cannot be maintained.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| Asking the agent directly for “a people tracker” | Unpredictable architecture, impossible to check against a written expectation |
| A larger detection model (YOLO11 medium or large) | Too slow on CPU; kept as a configuration option |
| A GPU solution in the cloud | Outside the project's constraints |

## The architecture I chose

```text
config.yaml ─► main.py
                 │  video or webcam (OpenCV, frame by frame)
                 ▼
        YoloDetector (YOLO11n, CPU enforced, “person” class only)
                 │  boxes + scores
                 ▼
        DeepSortTracker (stable identifiers, re-identification)
                 │  tracks
                 ▼
        draw_utils (boxes, identifiers, trajectories) ─► annotated video
```

**The specification fixed the file tree**, one module per responsibility: detection, tracking, geometry and video
utilities, visualisation. Each class had its role, its inputs and its outputs.

**All configuration lives in a YAML file**: model, confidence and IoU thresholds, tracked classes, DeepSORT parameters
(`max_age`, `n_init`, `max_iou_distance`), video source. Switching from a video to the webcam, or from a Nano to a
Medium model, needs no code change.

**The CPU is enforced explicitly**, so that no library looks for a GPU by default.

**One section of the specification was addressed to Claude Code**: type hints on every function, error handling when
loading files and models, vectorised NumPy operations rather than nested loops, automatic creation of the output
folder.

**A separate training script** fine-tunes the detector on the MOT20 dataset, with its hyperparameters on the command
line.

## What it delivered

A command-line tool that tracks people in a video or from a webcam, draws their boxes, identifiers and trajectories,
and can be fine-tuned on MOT20. The documentation gives an expected order of magnitude of 8 to 12 frames per second
with YOLO11 Nano on an Intel i7 or Apple M1 class processor.

[TO CONFIRM: frames per second measured on the machine used, grade obtained for the course.]

## What I would do differently

The performance figures in the README are expected values, not measurements. The specification could have required a
script measuring throughput and tracking quality, so that these numbers are produced by the code rather than
announced.
