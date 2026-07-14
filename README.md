---
title: Mirror Analyzer
emoji: 🪞
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Mirror Analyzer
### AI-Powered Non-Contact Health Monitoring System

![Python](https://img.shields.io/badge/Python-3.11-blue)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16.1-orange)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-green)
![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey)

---

## 🎯 Problem Statement

Millions of people worldwide miss early signs of serious health 
conditions because basic screening requires expensive doctor visits. 
Mirror Analyzer brings AI health screening to anyone with a laptop 
and webcam — zero cost, zero internet, zero doctor visit needed.

---

## 🔬 What It Does

Mirror Analyzer uses a regular webcam to analyze **47 health 
indicators** from your face in real time using 3 AI models 
working simultaneously:

| AI Model | Purpose | Performance |
|----------|---------|-------------|
| EfficientNetB3 | Skin disease detection (8 classes) | 61.5% val accuracy |
| Google MediaPipe | 478 facial landmark detection | 60+ FPS |
| Microsoft Phi-3 Mini | Natural language health report | Fully offline |

---

## 🏥 Health Indicators Analyzed

- **Eyes** — Fatigue, redness, dark circles, jaundice, symmetry
- **Lips** — Cyanosis, pallor, dryness, color analysis
- **Nose** — Redness, pore size, blackheads, symmetry
- **Skin** — 8 disease classes including Melanoma detection
- **Face** — Symmetry, landmarks, head pose
- **Vitals** — Heart rate, SpO2, temperature (simulated)

---

## 🚀 Quick Start

### Requirements
- Windows 10/11 64-bit
- Python 3.11
- Webcam
- Google Chrome
- 8GB RAM minimum

### Installation

```bash
# Step 1 — Clone repository
git clone https://github.com/rammanoshankarpoffic-coder/Mirror-Analyzer.git
cd Mirror-Analyzer

# Step 2 — Create virtual environment
python -m venv mirror_env
mirror_env\Scripts\activate

# Step 3 — Install packages
pip install -r requirements.txt

# Step 4 — Install Ollama + Phi-3
# Download Ollama from https://ollama.com
ollama pull phi3:mini

# Step 5 — Download AI model
# Download skin_model_v2.h5 from Google Drive
# Place in: model/skin_model_v2.h5
```

### Run

```bash
# Medical Theme (recommended)
python app_medical.py
# Open Chrome → http://localhost:5001

# Dark Tech Theme
python app.py  
# Open Chrome → http://localhost:5000
```
---

## 🤖 AI Model

- **Architecture:** EfficientNetB3 (Transfer Learning)
- **Dataset:** ISIC 2019 — 25,331 dermoscopy images
- **Classes:** MEL, NV, BCC, AK, BKL, DF, VASC, SCC
- **Training:** Google Colab T4 GPU
- **Accuracy:** 61.5% validation accuracy
- **Challenge:** 54x class imbalance handled with compute_class_weight



---

## 🛠️ Tech Stack
Backend    : Python 3.11, Flask, Flask-SocketIO

AI/ML      : TensorFlow 2.16.1, Keras, MediaPipe

Vision     : OpenCV 4.11

LLM        : Ollama + Phi-3 Mini (Microsoft)

Frontend   : HTML5, CSS3, JavaScript, Socket.IO

Training   : Google Colab, EfficientNetB3

Dataset    : ISIC 2019 (International Skin Imaging Collaboration)
---

## 📁 Project Structure
Mirror-Analyzer/

├── app.py                    # Dark theme server (port 5000)

├── app_medical.py            # Medical theme server (port 5001)

├── health_analyzer.py        # Master AI engine

├── requirements.txt          # Python dependencies

├── modules/

│   ├── eyes/eye_analyzer.py  # Eye fatigue & redness

│   ├── face/face_analyzer.py # MediaPipe landmarks

│   ├── lips/lip_analyzer.py  # Cyanosis & pallor

│   ├── nose/nose_analyzer.py # Redness & pores

│   └── skin/disease_detector.py # EfficientNetB3 model

├── templates/

│   ├── index.html            # Dark cyberpunk UI

│   └── index_medical.html    # Medical SaaS UI

└── static/

├── css/style.css         # Dark theme styles

├── css/style_medical.css # Medical theme styles

├── js/main.js            # Dark theme JS

└── js/main_medical.js    # Medical theme JS


---

## 👥 Team — Neural Nexus

Built for **HackArena 2.0** — Semifinalist 🏆

---

## ⚠️ Disclaimer

Mirror Analyzer is a **screening tool only** — not a medical device.
All results should be interpreted by a qualified healthcare professional.
No health data is transmitted or stored. 100% offline operation.

---

## 📄 License

MIT License — Free to use for educational and research purposes.
