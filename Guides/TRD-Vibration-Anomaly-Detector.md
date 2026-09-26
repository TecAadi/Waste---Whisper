# Technical Requirements Document (TRD)
## Vibration Anomaly Detector for Machinery

**Version:** 1.0
**Status:** Draft
**Companion docs:** Project Report, PRD
**Date:** August 2026

---

## 1. System Architecture

```
┌────────────────────┐      I2C       ┌───────────────────────────┐
│  MPU6050 (Accel/    │◄──────────────►│        ESP32 (WROOM-32)   │
│  Gyro, 6-DOF)        │  SDA→GPIO21    │                            │
└────────────────────┘  SCL→GPIO22    │  • Sampling engine          │
                                        │  • Feature extraction       │
┌────────────────────┐      I2C       │  • ML inference (model.h)   │
│  0.96" OLED (SSD1306)│◄──────────────►│  • Alert controller         │
└────────────────────┘  shared bus    │  • WebSocket client         │
                                        └───────────┬────────────────┘
┌────────────────────┐    GPIO23                    │ WiFi (WebSocket)
│  Buzzer + LED        │◄───────────────────────────┘
└────────────────────┘                              ▼
                                        ┌───────────────────────────┐
                                        │   FastAPI Backend (Python) │
                                        │  • WS/REST endpoints        │
                                        │  • SQLite persistence       │
                                        └───────────┬────────────────┘
                                                     │ REST / WS
                                                     ▼
                                        ┌───────────────────────────┐
                                        │  React / HTML Dashboard     │
                                        │  • Live gauges, status badge│
                                        │  • History log              │
                                        └───────────────────────────┘
```

---

## 2. Hardware Specification

| Component | Spec | Interface | Pin mapping |
|---|---|---|---|
| ESP32 NodeMCU (WROOM-32) | Dual-core Tensilica LX6, 240 MHz, 520 KB SRAM, WiFi + BT | — | Master controller |
| MPU6050 | 6-axis (3-axis accel + 3-axis gyro), 16-bit ADC, I2C up to 400 kHz | I2C | SDA→GPIO21, SCL→GPIO22, addr 0x68 |
| OLED SSD1306, 0.96", 128×64 | I2C | I2C (shared bus) | SDA→GPIO21, SCL→GPIO22, addr 0x3C (typical) |
| Active buzzer | Digital on/off | GPIO | GPIO23 |
| Status LED | Digital on/off | GPIO | GPIO23 (or separate pin, e.g., GPIO2) |
| Test motor/fan | 5V DC | External power | Not connected to ESP32 power rail |

**Bus note:** MPU6050 and OLED share the I2C bus (GPIO21/22) at different addresses (0x68 vs 0x3C) — no conflict, but confirm both devices support the same bus speed (400 kHz standard mode is safe for both).

**Power:** ESP32 via USB (5V) or external 5V/1A supply. Motor/fan powered independently — do not draw motor current through the ESP32's regulator.

---

## 3. Firmware Design (ESP32, C++/Arduino)

### 3.1 Sampling Module
- Read accel X/Y/Z from MPU6050 via `Adafruit_MPU6050` at a fixed interval (10 ms for 100 Hz).
- Use a hardware timer or `millis()`-based scheduler — avoid `delay()` blocking, since WiFi/WebSocket handling must run concurrently.
- Store samples in a circular buffer of size N (default 256).

### 3.2 Feature Extraction Module
Implement as a standalone, testable C++ function/module (`features.h` / `features.cpp`) so it can be unit-tested against the Python reference implementation used in training.

For a window of N samples x₁ … x_N:

```
RMS      = sqrt( (1/N) * Σ xᵢ² )
P2P      = max(x) - min(x)
Variance = (1/N) * Σ (xᵢ - mean)²
CrestFactor = max(|x|) / RMS
```

- Compute features independently per axis (X, Y, Z) — 4 features × 3 axes = 12 features per window, OR combine into a single magnitude signal `|a| = sqrt(x² + y² + z²)` and compute 4 features on that — **recommend starting with the magnitude approach** for a smaller, simpler feature vector (easier to fit a small tree, easier to explain in the paper), with per-axis features as a stretch/ablation study.
- Use `float` (32-bit), not `double`, for ESP32 efficiency.

### 3.3 ML Inference Module
- Model is trained offline in Python (see Section 6) and exported via **micromlgen** or **m2cgen** to a pure-C++ header (`model.h`) containing the decision logic as nested if/else or array-based tree traversal — no runtime interpreter needed.
- `#include "model.h"` in the main sketch; call the generated `predict(features[])` function once per window.
- Target: inference completes in **< 1 ms**.

### 3.4 Alert Controller
- State machine: `NORMAL → UNBALANCED → FAULT`, plus a debounce/hysteresis rule (e.g., require 2 consecutive non-Normal windows before triggering buzzer) to avoid single-window false-positive alerts.
- On non-Normal state: update OLED text, activate buzzer/LED.
- On return to Normal: clear alert state.

### 3.5 Connectivity Module
- WiFi connect (WPA2, credentials via a `config.h` or a simple captive-portal library like `WiFiManager` if you want to avoid hardcoding credentials).
- WebSocket client (e.g., `arduinoWebSockets` library) connects to the FastAPI backend.
- On each window: serialize `{timestamp, rms, p2p, variance, crest_factor, state}` to JSON via `ArduinoJson`, send over WebSocket.
- Must be non-blocking: if WiFi/WS is unavailable, sampling/feature/inference/alert pipeline continues unaffected (per FR4/FR5 in the PRD).

### 3.6 Firmware Module Boundaries (for maintainability, per PRD NFRs)

```
/firmware
  ├── sampling.h/.cpp        (MPU6050 read + circular buffer)
  ├── features.h/.cpp        (RMS/P2P/Variance/CrestFactor — pure math, no hardware calls)
  ├── model.h                (auto-generated by micromlgen/m2cgen — do not hand-edit)
  ├── alert.h/.cpp           (state machine, OLED, buzzer/LED)
  ├── telemetry.h/.cpp       (WiFi, WebSocket, JSON serialization)
  └── main.ino               (setup/loop orchestration only)
```

---

## 4. Communication Protocol

**Transport:** WebSocket (primary), MQTT (optional stretch goal for industrial-stack interop).

**Message schema (ESP32 → backend), JSON, one message per window:**

```json
{
  "device_id": "esp32-01",
  "timestamp": 1735900000,
  "rms": 0.842,
  "p2p": 2.13,
  "variance": 0.071,
  "crest_factor": 3.4,
  "state": "unbalanced",
  "confidence": 0.91
}
```

- `state` ∈ `{"normal", "unbalanced", "fault"}`.
- `confidence` is optional (only meaningful if the chosen model type exposes probabilities, e.g., Random Forest vote fraction; plain Decision Trees may omit this field).
- Backend should tolerate missing optional fields gracefully (schema validation should not hard-fail on their absence).

---

## 5. Backend Design (FastAPI)

### 5.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| `WS` | `/ws/telemetry` | Receives live telemetry from ESP32 device(s); broadcasts to connected dashboard clients |
| `GET` | `/api/status/latest` | Latest known state per device |
| `GET` | `/api/history?device_id=&since=&limit=` | Historical telemetry for charts/log |
| `GET` | `/api/devices` | List of known device IDs (for multi-device stretch goal) |

### 5.2 Data Model (SQLite, v1)

```sql
CREATE TABLE telemetry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  ts INTEGER NOT NULL,
  rms REAL,
  p2p REAL,
  variance REAL,
  crest_factor REAL,
  state TEXT NOT NULL,
  confidence REAL
);
CREATE INDEX idx_telemetry_device_ts ON telemetry(device_id, ts);
```

- If the InfluxDB stretch goal is pursued instead, model the same fields as an InfluxDB point with `device_id` as a tag and the numeric fields as fields.

### 5.3 Backend responsibilities
- Accept WebSocket connections from ESP32 device(s), validate/parse incoming JSON, persist to DB.
- Accept WebSocket connections from dashboard client(s), broadcast new telemetry in real time.
- Serve REST endpoints for historical queries (used by the dashboard's history panel).
- Basic input validation: reject malformed payloads without crashing the connection for other clients.

---

## 6. ML Training Pipeline (Python, offline)

### 6.1 Data Collection
- Firmware "logging mode": stream raw feature windows + a manually-set label to serial/CSV during controlled tests (Normal / Unbalanced-weight-taped / Loose-screws).
- Target ≥ 1,000 windows per class (per PRD FR8 / Project Report §6).
- Store as `dataset.csv`: columns `rms, p2p, variance, crest_factor, label`.

### 6.2 Training Script (`train.py`)
```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("dataset.csv")
X = df[["rms", "p2p", "variance", "crest_factor"]]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

candidates = {
    "decision_tree": DecisionTreeClassifier(max_depth=5, random_state=42),
    "random_forest": RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42),
    "svm": SVC(kernel="rbf", probability=True, random_state=42),
}

for name, model in candidates.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    print(f"--- {name} ---")
    print(classification_report(y_test, preds))
    print(confusion_matrix(y_test, preds))
```

- Evaluate all three; select based on accuracy **and** exported model size/latency (Project Report §12 benchmarking).
- Prefer `max_depth` limits on trees to keep the exported C++ model small.

### 6.3 Model Export
```python
from micromlgen import port
c_code = port(candidates["decision_tree"])  # or whichever model is chosen
with open("model.h", "w") as f:
    f.write(c_code)
```
(`m2cgen` is a drop-in alternative with broader model-type support if micromlgen's output doesn't fit a chosen model type.)

### 6.4 Validation step (important, often skipped)
- Re-implement the same RMS/P2P/Variance/CrestFactor formulas in Python exactly as in the C++ firmware, and confirm feature values match within floating-point tolerance on a shared sample set — this catches subtle bugs (e.g., population vs. sample variance, `float` vs `double` rounding) before they silently degrade on-device accuracy.

---

## 7. Frontend / Dashboard Design

- **v1 stack recommendation:** plain HTML + Chart.js (fast to build, matches timeline in PRD §12); React + Recharts as an optional polish upgrade if time allows.
- **Components:**
  - Live gauge(s) for RMS and Crest Factor (updated via WebSocket push).
  - Status badge: green "Normal", yellow "Unbalanced", red "Fault" — large and glance-readable.
  - History table/chart: last N events with timestamp + state, backed by `GET /api/history`.
  - (Stretch) Device selector, if multiple ESP32 units are deployed.

---

## 8. Performance Requirements

| Metric | Target | How measured |
|---|---|---|
| Sampling rate | 100 Hz (configurable to 500 Hz) | Firmware timer accuracy check |
| Feature extraction latency | < 50 ms per 256-sample window | `micros()` timestamps around the extraction call |
| ML inference latency | < 1 ms | `micros()` timestamps around `predict()` |
| End-to-end alert latency | < 3 s from fault onset to buzzer | Manual stopwatch test during induced-fault trials |
| Flash footprint of exported model | Document actual KB for each candidate model type | Compare `.bin` size across Decision Tree / RF / SVM builds |
| Dashboard update latency | < 2 s from ESP32 send to UI update | Manual/timestamp comparison |

---

## 9. Testing Strategy

| Test type | What it covers |
|---|---|
| **Unit tests (Python)** | Feature-extraction formulas match hand-calculated reference values |
| **Cross-validation (C++ vs Python)** | Same raw sample window fed to both implementations must produce matching feature outputs |
| **Model evaluation** | Train/test split + k-fold cross-validation; report accuracy, confusion matrix per candidate model |
| **Hardware-in-the-loop test** | Induce each fault physically (tape weight, loosen screws) and confirm correct on-device classification and alerting |
| **Endurance test** | Run continuously for ≥ 30 minutes, confirm no crash/reboot/memory leak (watch free heap via `ESP.getFreeHeap()`) |
| **Network resilience test** | Disconnect WiFi mid-run, confirm local alerting (OLED/buzzer) continues unaffected, confirm reconnect behavior |
| **Latency benchmarking** | Automated timing captures for feature extraction and inference across N = 128/256/512 (feeds directly into the Project Report §12 paper benchmarks) |

---

## 10. Security Considerations

- WiFi credentials should not be hardcoded in a committed source file — use a `config.h` excluded via `.gitignore`, or `WiFiManager` for runtime configuration.
- WebSocket endpoint has no built-in device authentication in v1 — acceptable for a lab/demo deployment on a private network, but should be flagged as a limitation if this were ever extended toward a real deployment (a device token or shared-secret header would be the minimal next step).
- No PII is collected or transmitted; only mechanical telemetry.

---

## 11. Deployment Notes

- **Firmware:** flash via Arduino IDE or PlatformIO over USB; OTA updates are out of scope for v1.
- **Backend:** run FastAPI/Uvicorn on a laptop or Raspberry Pi on the same local network as the ESP32 for the demo; no cloud hosting required for v1.
- **Dashboard:** served by FastAPI as static files, or run as a separate `npm run dev` process during development.

---

## 12. Traceability to PRD

| PRD Requirement | TRD Section |
|---|---|
| FR1 Sampling | §3.1 |
| FR2 Feature extraction | §3.2, §6.4 |
| FR3 On-device classification | §3.3, §6 |
| FR4 Local alerting | §3.4 |
| FR5 Telemetry | §3.5, §4 |
| FR6 Dashboard | §7 |
| FR7 Data logging | §5.2 |
| FR8 Training pipeline | §6 |
| NFR Performance targets | §8 |
