# SnapDesk AI — Private, On-Device AI Workbench for Snapdragon HP PCs

> **A local-first AI assistant for students with PDF chat, voice-note transcription, and screenshot explanation — designed for Snapdragon-powered HP PCs.**

SnapDesk AI is a privacy-focused, on-device AI workbench designed to help students study without sending their documents, voice recordings, or screenshots to the cloud.

The application uses **ONNX models** and is designed to take advantage of the **Qualcomm QNN Execution Provider** when available, with CPU fallback for compatibility.

---

## Why Snapdragon / HP PC?

* Built around **ONNX Runtime** and the **QNN Execution Provider**.
* Designed for Snapdragon X Elite / X Plus systems with Qualcomm AI acceleration.
* Uses compact models such as **Qwen2.5-0.5B-Instruct**, **Whisper Tiny**, and **Florence-2**.
* Local-first architecture keeps student data on the device.
* Designed to work without an internet connection after models and dependencies are installed.
* CPU fallback allows the application to remain functional when QNN/NPU execution is unavailable.

> **NPU verification:** SnapDesk AI reports the execution provider used at runtime. Snapdragon NPU performance is only claimed after successful QNN/HTP verification and benchmark testing.

---

# Features

| Tab              | What it does                                                   | Primary Model       | Target    |
| ---------------- | -------------------------------------------------------------- | ------------------- | --------- |
| **Doc Chat**     | Drag a PDF, ask questions, generate summaries                  | Qwen2.5-0.5B        | QNN / CPU |
| **Voice Notes**  | Record memo → transcription → summary + action items           | Whisper Tiny + Qwen | QNN / CPU |
| **Snap Explain** | Capture screen region → caption → student-friendly explanation | Florence-2 + Qwen   | QNN / CPU |

### Planned Student Tools

* **Flashcards** — PDF → Q&A cards + Anki export
* **Quiz Generator** — automatic MCQs with answer keys
* **Study Plan** — syllabus → day-by-day revision schedule
* **HandyNotes OCR** — handwritten notes → searchable text
* **Translate + Speak** — translation with text-to-speech

---

# Architecture

```text
SnapDesk-AI/
│
├── app.py
│   └── PySide6 GUI
│       ├── Doc Chat
│       ├── Voice Notes
│       └── Snap Explain
│
├── core/
│   ├── npu.py
│   │   └── QNN / CPU provider selection
│   │
│   ├── doc_chat.py
│   │   └── PDF ingestion + Qwen generation
│   │
│   ├── voice.py
│   │   └── microphone + Whisper + note structuring
│   │
│   └── screenshot.py
│       └── screen capture + Florence + Qwen
│
├── features/
│   ├── flashcards/
│   ├── quiz/
│   ├── study_plan/
│   ├── handynotes/
│   └── translate/
│
├── models/
│   ├── qwen/
│   ├── whisper/
│   ├── florence/
│   ├── trocr/
│   └── tts-voices/
│
├── benchmark.py
├── requirements.txt
└── README.md
```

---

# AI Pipeline

### Doc Chat

```text
PDF
 │
 ▼
PDF Text Extraction
 │
 ▼
Prompt
 │
 ▼
Qwen2.5-0.5B
 │
 ▼
Answer / Summary
```

### Voice Notes

```text
Microphone
 │
 ▼
Whisper Tiny INT8
 │
 ▼
Transcript
 │
 ▼
Qwen2.5-0.5B
 │
 ├── Summary
 └── Action Items
```

### Snap Explain

```text
Screen Region
 │
 ▼
Screenshot Capture
 │
 ▼
Florence-2
 │
 ▼
Image Caption
 │
 ▼
Qwen2.5-0.5B
 │
 ▼
Student-Friendly Explanation
```

---

# Benchmark

The benchmark compares the same Qwen generation workload using the available execution paths.

Run:

```powershell
python benchmark.py --tokens 128
```

Example result table:

| Execution Path                  | Tokens | Time | Tokens/sec | Speedup |
| ------------------------------- | -----: | ---: | ---------: | ------: |
| Snapdragon Hexagon NPU (QNN EP) |      — |    — |          — |       — |
| CPU baseline                    |      — |    — |          — |   1.00× |

Replace the `—` values with **measured results** from `benchmark_results.json`.

### Benchmark methodology

The benchmark should:

1. Separate model-loading time from generation time.
2. Run multiple iterations.
3. Calculate average generation performance.
4. Report the actual execution provider.
5. Avoid unnecessary token decoding during throughput measurement.
6. Compare identical prompts and generation settings.

This prevents model-loading overhead or a single unusually fast/slow run from distorting the headline number.

---

# Setup

## 1. Clone / create the project

From the project directory:

```powershell
cd SnapDesk-AI
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

For Snapdragon/QNN systems, install the appropriate **ONNX Runtime QNN / GenAI packages** required by the selected model and runtime configuration.

---

# Model Setup

Models are stored locally under:

```text
models/
```

Recommended structure:

```text
models/
├── qwen/
├── whisper/
├── florence/
├── trocr/
└── tts-voices/
```

See the **Model Download Checklist** for the individual model download commands.

---

# QNN / NPU Execution

SnapDesk AI is designed with a provider fallback architecture:

```text
                SnapDesk AI
                     │
                     ▼
             ONNX Runtime
                     │
                     ▼
              Provider Check
               /          \
              /            \
          QNN EP          CPU EP
             │               │
             ▼               ▼
        Snapdragon        Standard
          HTP/NPU        CPU execution
```

When QNN is available and the model is compatible:

```text
ONNX Model
    ↓
ONNX Runtime
    ↓
QNN Execution Provider
    ↓
Qualcomm HTP / NPU
```

If QNN is unavailable:

```text
ONNX Model
    ↓
ONNX Runtime
    ↓
CPU Execution Provider
```

The application remains feature-complete through this fallback path.

> **Important:** The presence of `QNNExecutionProvider` in a configuration does not by itself prove that inference ran on the Hexagon NPU. SnapDesk AI should verify the active provider and benchmark actual execution before reporting NPU acceleration.

---

# Optimization Path

### 1. QNN Execution Provider

Use the appropriate ONNX Runtime QNN package for the target Snapdragon Windows environment.

### 2. HTP Optimization

Where supported by the selected model/runtime, configure appropriate HTP performance and precision options.

### 3. CPU Fallback

If QNN is unavailable or a model operation is unsupported:

```text
QNN → CPU fallback
```

No separate application workflow should be required.

### 4. Future WebNN Path

A future version can investigate **WebNN/WebGPU-based execution through Microsoft Edge** as an alternative acceleration path for the UI/web architecture.

---

# Privacy

SnapDesk AI follows a **local-first architecture**.

```text
Student Data
     │
     ▼
┌───────────────┐
│  SnapDesk AI  │
│     PC        │
└───────────────┘
     │
     ├── PDF
     ├── Voice
     ├── Screenshots
     └── Notes
```

The application is designed so that these inputs can remain on the user's PC.

After the required models and dependencies are installed, the core workflows can be designed to operate without sending user content to a remote AI API.

---

# Project Status

| Component              | Status     |
| ---------------------- | ---------- |
| PySide6 application    | 🚧         |
| Doc Chat               | 🚧         |
| Voice Notes            | 🚧         |
| Snap Explain           | 🚧         |
| QNN provider detection | 🚧         |
| CPU fallback           | 🚧         |
| Flashcards             | 📋 Planned |
| Quiz Generator         | 📋 Planned |
| Study Plan             | 📋 Planned |
| HandyNotes OCR         | 📋 Planned |
| Translate + Speak      | 📋 Planned |
| Benchmark              | 🚧         |

---

# Requirements

Recommended environment:

* Windows 11
* Python 3.x
* PySide6
* ONNX Runtime
* ONNX Runtime GenAI
* ONNX Runtime QNN where supported
* Hugging Face Hub
* Snapdragon X Elite / X Plus PC for QNN/NPU testing

A compatible non-Snapdragon PC can still be used for development and CPU testing.

---

# Running SnapDesk AI

After installation:

```powershell
python app.py
```

For benchmarking:

```powershell
python benchmark.py --tokens 128
```

Expected benchmark output:

```text
benchmark_results.json
```

---

# Project Vision

SnapDesk AI aims to turn a Snapdragon-powered HP PC into a **private, local AI study workstation**.

Instead of sending a student's documents, recordings, and screenshots to a cloud service:

```text
                 SNAPDESK AI

        ┌─────────────────────────┐
        │       Student PC        │
        │                         │
PDF ───►│                         │
Voice ─►│    Local AI Models      │
Image ─►│                         │
        │                         │
        │   CPU / Snapdragon NPU  │
        └─────────────────────────┘
```

**Private. Local. Student-focused.**
