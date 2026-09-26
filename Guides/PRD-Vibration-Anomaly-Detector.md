# Product Requirements Document (PRD)
## Vibration Anomaly Detector for Machinery

**Version:** 1.0
**Status:** Draft
**Owner:** [Your Name]
**Date:** August 2026

---

## 1. Purpose

Define what the Vibration Anomaly Detector must do, for whom, and how success is measured — independent of implementation detail (that lives in the companion TRD). This document guides scope decisions during the build and gives the project panel/evaluator a clear picture of intent vs. execution.

---

## 2. Background & Problem

Rotating machinery (motors, pumps, fans) degrades gradually before it fails outright — through bearing wear, shaft unbalance, or mounting looseness. Detecting this early lets an operator schedule a repair before a breakdown, instead of reacting after one. Commercial vibration-monitoring hardware exists but is priced for industrial budgets, not for students, small workshops, or hobbyist makerspaces. There is a gap for a **low-cost, edge-intelligent** device that can classify machine health from raw vibration without needing a connected cloud ML service.

---

## 3. Target Users / Personas

| Persona | Need |
|---|---|
| **Final-year engineering student (primary user, this build)** | A demoable, defensible project combining embedded systems + ML + web, buildable solo in a semester |
| **Small workshop / maker-space operator** | Cheap early-warning system for a handful of motors/fans without an industrial SCADA budget |
| **Lab instructor / TA** | Reusable teaching rig for embedded ML, DSP, or IoT coursework |
| **Project evaluator / panel** | Needs to see genuine technical depth (math, ML, systems design), not just a sensor-to-cloud demo |

---

## 4. Goals

1. Detect three machine states — **Normal**, **Unbalanced**, **Loose/Fault** — from live vibration data.
2. Perform classification **entirely on-device**, with no dependency on an external ML API.
3. Provide both **local** (OLED + buzzer) and **remote** (web dashboard) visibility of machine state.
4. Keep the entire BOM under **₹2,000 (~$25)** per unit.
5. Achieve classification latency **under 1 ms** per inference on the ESP32.
6. Produce a system whose methodology is rigorous enough to support a short technical paper.

### Non-goals (explicitly out of scope for v1)
- Certified industrial safety/shutdown functionality (this is a monitoring aid, not a safety-interlock system).
- Frequency-domain (FFT/spectral) analysis — noted as a stretch goal, not required for v1.
- Multi-sensor fusion or multi-machine fleet management dashboards — stretch goal only.
- Battery-powered/wireless-only deployment — v1 assumes a wired 5V supply.
- Mobile app — a responsive web dashboard is sufficient for v1.

---

## 5. Success Metrics

| Metric | Target |
|---|---|
| Classification accuracy (test set, 3-class) | ≥ 90% |
| On-device inference latency | < 1 ms per window |
| Feature-extraction latency per 256-sample window | < 50 ms |
| End-to-end alert latency (fault onset → buzzer) | < 3 seconds |
| Dashboard telemetry update rate | ≥ 1 update / 2 sec |
| BOM cost per unit | ≤ ₹2,000 / $25 |
| Uptime during a 30-minute continuous demo run | No crash / reboot |

---

## 6. User Stories

**As a student presenting this project**, I want the device to visibly flag an induced fault (e.g., taped weight on a fan blade) within a few seconds, so that I can demonstrate real-time detection live to a panel.

**As a workshop operator**, I want a dashboard I can glance at from across the room, showing current machine status and recent history, so that I know if something needs attention without standing next to the machine.

**As a lab instructor**, I want the OLED and buzzer to work even without WiFi, so that the core safety-relevant function isn't dependent on network conditions.

**As a project evaluator**, I want to see quantified accuracy/latency/memory benchmarks across different model types, so that I can assess the technical rigor of the work, not just whether the demo "worked once."

**As a future contributor extending this project**, I want the feature-extraction and ML-inference code cleanly separated from the WiFi/dashboard code, so that the core detection logic can be reused in a battery-powered or FFT-enhanced version later.

---

## 7. Functional Requirements

### FR1 — Vibration Sampling
- The system shall sample X, Y, Z acceleration from the MPU6050 over I2C.
- The system shall support a configurable sample rate (100 Hz default, up to 500 Hz).

### FR2 — Windowing & Feature Extraction
- The system shall buffer N=256 samples per analysis window (~2 seconds at 100 Hz, configurable).
- The system shall compute, per window: RMS, Peak-to-Peak amplitude, Variance, Crest Factor.

### FR3 — On-Device Classification
- The system shall classify each feature window into one of: Normal, Unbalanced, Loose/Fault.
- Classification shall run natively on the ESP32 using a model compiled to C++ (no external inference calls).

### FR4 — Local Alerting
- The system shall display the current machine state on the OLED display, updated every window.
- The system shall sound the buzzer and light the LED when state ≠ Normal.
- Local alerting (OLED + buzzer) shall function without any WiFi connection.

### FR5 — Telemetry
- The system shall transmit, per window, a JSON payload (features + classification + timestamp) to the backend over WebSocket when WiFi is available.
- The system shall not block or crash if WiFi/backend is unreachable; it shall retry or continue local-only operation.

### FR6 — Dashboard
- The dashboard shall display live gauges for RMS and Crest Factor.
- The dashboard shall display a current status badge (Normal / Unbalanced / Fault) with distinct visual states.
- The dashboard shall display a scrollable/queryable history log of past anomaly events with timestamps.

### FR7 — Data Logging
- The backend shall persist telemetry to a database (SQLite for v1) for later review and for training-data reuse.

### FR8 — Model Training Pipeline
- A Python pipeline shall accept a CSV of labeled feature windows and train/evaluate at least two candidate model types (e.g., Decision Tree and Random Forest or SVM).
- The pipeline shall export a chosen model to a C++ header file for embedding into firmware.

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Inference < 1 ms; feature extraction < 50 ms per window |
| **Reliability** | Device shall run continuously for ≥ 30 minutes without crash/reboot during demo conditions |
| **Cost** | Total BOM ≤ ₹2,000 / $25 per unit |
| **Portability** | Firmware buildable via both Arduino IDE and PlatformIO |
| **Usability** | Dashboard status must be interpretable at a glance (color-coded badges, no jargon) |
| **Maintainability** | Feature-extraction and ML-inference logic kept in separate, reusable C++ modules from WiFi/networking code |
| **Extensibility** | Architecture must allow adding an FFT-based feature set later without a full rewrite |
| **Offline resilience** | Core detection + local alert must not depend on network connectivity |

---

## 9. Assumptions & Constraints

- The test machine (small DC motor / PC fan) is available and safe to physically tamper with (loosen screws, tape weights) for fault-data generation.
- Development happens on a single prototype unit; the project does not need to support fleet-scale deployment.
- WiFi is available in the demo/lab environment for the dashboard portion of the demo, but the grading-critical local alerting must not require it.
- The builder has (or will gain) basic familiarity with Arduino C++, Python, and either React or plain HTML/JS.
- Semester timeline is roughly 6–10 weeks (see Project Report, Section 11) — this bounds what's realistic to include in v1 vs. stretch goals.

---

## 10. Milestones (tied to Project Report timeline)

| Milestone | Target week |
|---|---|
| Hardware bring-up (I2C sensor read verified) | Week 1–2 |
| Feature extraction verified against Python reference | Week 3 |
| Labeled dataset collected (3 classes, ≥1,000 windows each) | Week 4 |
| Trained model meets ≥90% test accuracy | Week 5 |
| On-device inference integrated and verified | Week 6 |
| Local alerting (OLED/buzzer) functional | Week 7 |
| Dashboard + telemetry functional | Week 8 |
| Full benchmarking complete (Section 12 of Project Report) | Week 9 |
| Final report/paper + demo rehearsal | Week 10 |

---

## 11. Risks (Product-Level)

| Risk | Impact | Mitigation |
|---|---|---|
| Live demo fault-induction doesn't reliably trigger detection | High (core demo moment) | Rehearse fault induction repeatedly beforehand; tune classification threshold/window size for reliability over raw accuracy |
| Panel questions the real-world validity of a consumer-grade IMU | Medium | Proactively state MPU6050 limitations vs. industrial accelerometers in the report (already covered in Project Report §8) |
| Dashboard becomes the "point of failure" during demo (WiFi drops) | Medium | Keep OLED+buzzer as the primary demo signal; dashboard as a secondary/bonus visual |
| Scope creep into FFT/multi-sensor features eats into core-feature polish time | Medium | Treat FFT, multi-device, and alerting-via-SMS strictly as stretch goals, only after FR1–FR8 are solid |

---

## 12. Open Questions

- Should the v1 dashboard be plain HTML/Chart.js (faster to build) or React (more portfolio-impressive)? Recommend HTML/Chart.js for v1 given the timeline, React as a stretch/portfolio polish item if time remains.
- Should model retraining be a one-time offline step, or should the pipeline support periodic retraining as more labeled data accumulates? Recommend one-time for v1; note as future work in the paper.
