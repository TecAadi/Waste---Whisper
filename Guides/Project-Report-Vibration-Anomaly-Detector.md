# Vibration Anomaly Detector for Machinery — Full Project Report

**Subtitle:** Edge-AI Predictive Maintenance System using ESP32, MPU6050 and On-Device Machine Learning
**Document type:** Final Year Project Report
**Date:** August 2026

---

## 1. Executive Summary

This project builds a low-cost, edge-intelligent vibration monitoring device that detects early signs of mechanical failure (unbalance, looseness, bearing wear) in rotating machinery such as motors, pumps, and fans. Unlike typical IoT projects that just stream sensor data to the cloud, this system does the actual "thinking" — feature extraction and classification — directly on the ESP32 microcontroller, using a machine learning model compiled into C++. This gives it three things that make it stand out academically and practically: real edge AI (not just data logging), a genuine mathematics/DSP component, and a working predictive-maintenance use case with industrial relevance.

It is well-scoped for a final year CSE/ECE/Mechatronics project: buildable in 6–10 weeks, costs under ₹2,000 (~$25), and produces a demoable device plus a publishable methodology.

---

## 2. Problem Statement

Unplanned downtime in industrial equipment is expensive. Traditional maintenance is either **reactive** (fix it after it breaks — costly and disruptive) or **preventive** (fixed schedule — wasteful, since parts get replaced whether they need it or not). **Predictive maintenance** — monitoring the actual condition of equipment and intervening only when needed — is the industry-preferred approach, but commercial vibration-monitoring systems (e.g., SKF, Bently Nevada) cost anywhere from a few hundred to several thousand dollars per monitoring point, putting them out of reach for small workshops, labs, and student/hobbyist deployments.

This project asks: **can a sub-$15 microcontroller and a $2 accelerometer detect the same class of faults (unbalance, looseness, bearing defects) that expensive industrial systems detect — using on-device statistical feature extraction and a lightweight ML model, with no cloud dependency?**

---

## 3. Project Objectives

1. Sample tri-axial vibration data from a rotating machine using an MPU6050 accelerometer.
2. Extract time-domain statistical features (RMS, peak-to-peak, variance, crest factor) on-device.
3. Train a lightweight classifier (Decision Tree / Random Forest / SVM) offline in Python, then port it to run natively on the ESP32.
4. Classify machine state in real time (Normal / Unbalanced / Loose-Fault) in under 1 millisecond per inference.
5. Provide local feedback (OLED + buzzer) and remote visibility (web dashboard over WebSockets).
6. Benchmark the approach — accuracy, latency, memory footprint — well enough to support a short IEEE/Scopus-style paper.

---

## 4. How the System Works

```
[ Rotating Machine ]
       │ (Vibrations)
       ▼
[ MPU6050 Accelerometer ] ──(I2C)──► [ ESP32 Microcontroller ]
                                            │
                                            ├─► 1. Sample 256 vibration points
                                            ├─► 2. Compute RMS, Crest Factor, Variance, P2P
                                            ├─► 3. Run on-chip ML model (<1ms)
                                            │
                                     (WiFi / WebSockets)
                                            │
                                            ▼
                                [ React + FastAPI Dashboard ]
```

**Pipeline stages:**

| Stage | What happens | Where it runs |
|---|---|---|
| Sampling | MPU6050 streams X/Y/Z acceleration at 100–500 Hz | ESP32 (I2C) |
| Windowing | Buffer 256 samples (~2 sec window) | ESP32 RAM |
| Feature extraction | Compute RMS, peak-to-peak, variance, crest factor | ESP32 (C++ math) |
| Classification | Decision Tree / Random Forest inference | ESP32 (compiled C++ model) |
| Local alerting | OLED status text, buzzer/LED on anomaly | ESP32 GPIO |
| Telemetry | Push feature + classification JSON over WebSocket | ESP32 → FastAPI |
| Visualization | Live gauges, status badges, history log | React/HTML dashboard |

---

## 5. The CS & Math Core (what makes this a strong CSE project)

This is the part that separates it from a generic "connect a sensor to WiFi" project — it's genuinely doing signal processing and applied ML, not just data forwarding.

**Time-domain features** computed per window of N samples (x₁ … x_N):

- **RMS (Root Mean Square)** — overall vibration energy: `RMS = sqrt((1/N) * Σxᵢ²)`
- **Peak-to-Peak (Vp-p)** — maximum swing: `max(x) − min(x)`
- **Variance (σ²)** — signal instability/spread around the mean
- **Crest Factor (CF)** — `peak / RMS`; spikes relative to background vibration, good for catching early bearing cracks/impacts

**ML pipeline:**
1. Collect ~1,000 labeled windows per class (Normal, Unbalanced, Loose/Fault) via a logging sketch → CSV.
2. Train a Decision Tree / Random Forest / SVM in scikit-learn on the extracted features (not raw waveforms — this keeps the model tiny).
3. Convert the trained model to C++ using **micromlgen** or **m2cgen**, producing a `model.h` you `#include` directly in the Arduino sketch — no runtime interpreter, no external inference library, no network call needed to classify.

This on-device-only inference is the technical differentiator: latency is sub-millisecond and the device works even with no WiFi connection at all.

---

## 6. Features

### Core (MVP) features
- Real-time vibration sampling from MPU6050 at 100 Hz.
- Sliding-window feature extraction (RMS, P2P, variance, crest factor).
- On-chip 3-class classification (Normal / Unbalanced / Fault).
- Local OLED display of current status.
- Buzzer + LED alert on anomaly detection.
- WebSocket telemetry to a FastAPI backend.
- Live web dashboard with gauges and a status badge.

### Extended / stretch features (good for differentiating a final-year project)
- **Historical trend logging** (SQLite/InfluxDB) with a "vibration health over time" chart, so degradation trends are visible before failure.
- **Multi-device support** — dashboard that monitors several machines at once (useful for a "smart factory floor" demo).
- **Threshold auto-calibration** — a "learn normal" button that recalibrates the baseline for a specific machine.
- **MQTT support** alongside WebSockets, for integration with existing industrial IoT stacks (Node-RED, Home Assistant).
- **Email/Telegram/SMS alerting** when a fault is sustained for N consecutive windows (reduces false-positive noise).
- **Battery + deep-sleep mode** for a wireless, machine-mounted version.
- **Feature importance dashboard panel** — shows which metric triggered the classification, useful both for the report and for real diagnostic value.
- **Frequency-domain add-on (FFT)** — a possible "if time permits" extension comparing time-domain vs frequency-domain (FFT-based) features for accuracy, which strengthens the research angle considerably.

---

## 7. Advantages

- **Low cost** — total BOM well under ₹2,000 / $25 (see Section 10), versus hundreds to thousands of dollars for commercial vibration sensors.
- **No cloud dependency for the critical function** — classification happens on-device; the system still detects and alerts on a fault even if WiFi is down. This is a genuinely useful edge-AI property, not just a buzzword.
- **Low latency** — inference in under 1 ms means the device can, in principle, react in real time.
- **Low bandwidth** — only compact feature vectors and classification results are transmitted, not raw high-frequency waveform data, which matters at scale (many sensors, limited factory WiFi).
- **Educational value is high and cross-disciplinary** — touches embedded systems, signal processing, applied statistics, machine learning, full-stack web development, and IoT communication protocols in one project.
- **Demoable** — a physical fan/motor with a weight taped to a blade "failing" live in front of a panel is a strong, tangible demo (better than most CSE final-year software-only projects).
- **Publishable methodology** — the benchmarking angle (Section 12) gives a clear, structured basis for an IEEE/Scopus-style paper.
- **Extensible** — clear paths to add FFT-based frequency-domain features, more machine states, multiple sensors, or cloud analytics later.

---

## 8. Disadvantages & Limitations

- **MPU6050 is a low-cost consumer-grade IMU**, not an industrial accelerometer. It has noise floor and bandwidth limitations (typical usable bandwidth is a few hundred Hz), so it can reliably catch coarse mechanical faults (unbalance, looseness) but is unlikely to catch high-frequency bearing defect signatures that industrial piezoelectric accelerometers (sampling in the kHz range) are built for.
- **Small, imbalanced training data** collected from a single test motor/fan risks overfitting — a model trained on your bench setup may generalize poorly to a different real machine (different RPM, mounting, mass).
- **Time-domain features alone have limited diagnostic resolution.** Many real bearing/gear faults are best distinguished in the frequency domain (FFT, envelope spectrum) — the time-domain-only version is a good "detect anomaly" system but weaker at "diagnose exact fault type" without the FFT extension.
- **Mechanical coupling matters a lot** — how rigidly the MPU6050 is mounted to the machine significantly affects the signal; a loose sensor mount will itself look like a "fault," which is a real experimental pitfall worth documenting.
- **ESP32 resource constraints** — decision trees/small SVMs fit comfortably, but larger models (e.g., neural nets) would need TinyML frameworks (TensorFlow Lite Micro) and more careful memory management.
- **WiFi dependency for remote visibility** — local alerting still works offline, but the dashboard, logging, and remote alerts require a working WiFi connection.
- **No functional safety certification** — this is a monitoring/demo project, not a certified industrial safety system; it should not be the sole safeguard for critical machinery in a real deployment.
- **Single-point sensing** — one accelerometer per machine gives limited spatial information versus multi-point industrial vibration monitoring rigs.

---

## 9. Benefits (Academic + Practical)

**Academic benefits**
- Strong final-year project: covers embedded systems, DSP, ML, and full-stack web in a single coherent narrative — easy to defend in a viva.
- Natural fit for a short conference/journal paper (Section 12 gives the exact benchmarking structure).
- Demonstrates understanding of the full ML lifecycle: data collection → feature engineering → training → embedded deployment — a skill set directly relevant to TinyML/Edge-AI roles.

**Practical / real-world benefits**
- Reusable as a genuine low-cost condition-monitoring tool for small workshops, college labs, or maker/hobbyist machine shops.
- Portfolio piece that demonstrates hardware + ML + web skills together — valuable for embedded systems, IoT, or applied ML job applications.
- Modular design means individual pieces (feature extraction library, dashboard, ML pipeline) are reusable in other IoT/edge-AI projects.

---

## 10. Requirements & Bill of Materials (with researched pricing)

### 10.1 Hardware BOM

| Component | Qty | Purpose | Approx. Price (India) | Approx. Price (Global) |
|---|---|---|---|---|
| ESP32 NodeMCU (CP2102/CH340, WROOM-32) | 1 | Main controller, WiFi, edge ML | ₹350 – ₹450 | $4 – $9 |
| MPU6050 (GY-521) accelerometer/gyro module | 1 | Vibration sensing | ₹150 – ₹250 | $2 – $4 |
| 0.96" I2C OLED display (128×64) | 1 | Local status display | ₹200 – ₹350 | $3 – $5 |
| Active buzzer + LED | 1 | Local alert | ₹30 – ₹60 | $0.50 – $1 |
| 5V DC motor / small PC fan | 1 | Test-bench "machine" | ₹150 – ₹300 | $2 – $5 |
| Small weight/nut (for unbalance test) | few | Simulating unbalance fault | ~₹0 (scrap) | ~$0 |
| Breadboard + jumper wires | 1 set | Prototyping | ₹150 – ₹250 | $2 – $4 |
| USB cable (micro-USB/USB-C) | 1 | Power + programming | ₹80 – ₹150 | $1 – $3 |
| Mounting hardware / enclosure (optional) | 1 | Sensor rigidity, presentation | ₹150 – ₹400 | $2 – $6 |
| 5V power supply/adapter | 1 | Standalone operation | ₹100 – ₹200 | $1.5 – $3 |

**Researched total (realistic, India):** roughly **₹1,300 – ₹2,300** depending on supplier and whether you already own a breadboard/wires. The frequently-cited "₹1,000–1,200" figure floating around online tends to assume you already have jumper wires/breadboard and skips the enclosure and power adapter — a more realistic first-time build lands closer to **₹1,800 (~$22)**. Buying a bundled "ESP32 + OLED WiFi Kit" (some suppliers sell ESP32 with an OLED pre-attached for ~₹950–1,100) can reduce total cost.

**Global equivalent:** roughly **$18 – $30** for a single prototype unit, before shipping, which is consistent with common hobbyist ESP32-project BOM costs.

> Prices fluctuate with supplier, bulk discounts, and shipping; treat the above as planning estimates, not quotes. Buying from a single India-based components retailer (Robocraze, ElectronicsComp, Robokits, KTRON) in one order will usually beat piecing components together from Amazon at retail markup.

### 10.2 Software / tooling requirements (all free/open-source)

| Layer | Tool |
|---|---|
| Firmware | Arduino IDE or PlatformIO, C++ |
| Sensor library | Adafruit_MPU6050, Adafruit_Sensor |
| Data serialization | ArduinoJson |
| ML training | Python 3, scikit-learn, pandas, numpy |
| Model → C++ export | micromlgen or m2cgen |
| Backend | Python, FastAPI, Uvicorn, websockets, paho-mqtt (optional) |
| Database | SQLite (simplest) or InfluxDB (if doing serious time-series work) |
| Frontend | React (or plain HTML/JS) + Chart.js or Recharts |
| Version control | Git/GitHub |

### 10.3 Non-monetary requirements
- A small DC motor or PC fan test rig you can safely mount a nut/weight to and loosen screws on (for generating labeled fault data).
- A quiet-ish bench location (external vibration/noise sources will contaminate your baseline data).
- Roughly 15–25 hours of hands-on lab time to collect a clean, balanced labeled dataset across all three classes — this is usually the most time-consuming step, not the coding.

---

## 11. Suggested Timeline (6–10 week plan)

| Week | Milestone |
|---|---|
| 1 | Procure BOM, set up dev environment, verify MPU6050 I2C communication |
| 2 | Build sampling + windowing firmware, validate against known-good sampling rate |
| 3 | Implement RMS/P2P/Variance/Crest Factor in C++, verify against Python reference values |
| 4 | Build test rig (fan/motor), collect labeled dataset (Normal / Unbalanced / Loose) |
| 5 | Train and evaluate Decision Tree / Random Forest / SVM in Python; pick best model |
| 6 | Export model via micromlgen/m2cgen, integrate into firmware, verify on-device accuracy |
| 7 | Build OLED + buzzer alerting, WebSocket telemetry |
| 8 | Build FastAPI backend + React/HTML dashboard |
| 9 | Benchmarking: latency, memory footprint, accuracy across models and window sizes |
| 10 | Report/paper writing, polish demo, rehearse viva/defense |

---

## 12. Research Paper Strategy

**Proposed title:** *"Edge-Calculated Time-Domain Feature Extraction and Machine Learning for Low-Cost Predictive Industrial Maintenance"*

**What to benchmark:**
- **Accuracy vs. model size** — Decision Tree vs. Random Forest vs. SVM, compared on flash footprint (KB) and inference latency on the ESP32.
- **Feature importance** — which of RMS / Crest Factor / Variance / P2P contributes most to detecting unbalance vs. looseness.
- **Computational latency** — measured feature-extraction time (µs) for window sizes N = 128, 256, 512.
- **(Stretch) Time-domain vs. frequency-domain** — if you add an FFT-based feature set, a direct accuracy/latency comparison against the time-domain-only approach would meaningfully strengthen the paper's contribution.

This structure maps directly onto a standard IEEE conference paper: Introduction → Related Work (commercial predictive maintenance systems, TinyML) → Methodology (pipeline, math, ML) → Experimental Setup → Results (the benchmarks above) → Conclusion & Future Work.

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Sensor mount looseness contaminates data | Use rigid mounting (hot glue/screw bracket), document mounting method in report |
| Small/imbalanced dataset → overfit model | Collect ≥1,000 windows/class, use cross-validation, report confusion matrix honestly |
| WiFi instability during demo | Ensure local OLED/buzzer alerting works fully standalone, don't depend on dashboard for the core demo |
| ESP32 memory overflow with larger models | Prefer Decision Tree/small Random Forest over large SVMs; monitor flash/RAM usage during build |
| Panel skepticism about "real-world validity" | Be upfront about MPU6050 vs industrial-accelerometer limitations (Section 8) — acknowledging scope honestly is well received academically |

---

## 14. Conclusion

This project is well-matched to a final-year CSE/ECE portfolio: it's cheap, buildable in a semester, has a real and demoable output, and — critically — has genuine technical depth (DSP math + embedded ML + full-stack telemetry) rather than being a thin wrapper around a cloud API. Its main limitation is sensor-grade fidelity, which is worth stating candidly in both the report and any paper rather than overclaiming industrial-grade capability. Companion documents — the **PRD** and **TRD** — break this down into concrete requirements and technical specifications for implementation.
