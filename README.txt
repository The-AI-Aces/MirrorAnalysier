═══════════════════════════════════════════
        MIRROR ANALYZER — SETUP GUIDE
═══════════════════════════════════════════

PROJECT: Mirror Analyzer
DESCRIPTION: Real-time face health monitoring
             using AI and webcam

REQUIREMENTS:
- Windows 10/11 64-bit
- Python 3.11
- Webcam (built-in or external)
- Google Chrome browser
- Ollama installed (for health report)
- Minimum 8GB RAM
- Minimum 4GB free disk space

═══════════════════════════════════════════
STEP BY STEP SETUP ON NEW PC
═══════════════════════════════════════════

STEP 1 — Install Python 3.11
  Download from: https://python.org
  Version: 3.11.x (NOT 3.12 or higher)
  IMPORTANT: Check "Add Python to PATH"
             during installation!

STEP 2 — Install Ollama
  Download from: https://ollama.com
  After install, open Command Prompt and run:
  ollama pull phi3:mini
  (downloads 2.3GB — needs internet once)

STEP 3 — Extract project folder
  Extract Mirror_Analyzer.zip to:
  C:\Mirror_Analyzer
  or any folder you prefer

STEP 4 — Open Command Prompt
  Press Windows + R
  Type: cmd
  Press Enter

STEP 5 — Go to project folder
  cd C:\Mirror_Analyzer

STEP 6 — Create virtual environment
  python -m venv mirror_env

STEP 7 — Activate environment
  mirror_env\Scripts\activate
  You will see (mirror_env) appear

STEP 8 — Install all packages
  pip install -r requirements.txt
  (takes 5-10 minutes, needs internet once)

STEP 9 — Run the project
  python app.py

STEP 10 — Open Chrome
  Go to: http://localhost:5000
  Point webcam at your face
  Health analysis starts automatically!

═══════════════════════════════════════════
TO RUN AGAIN NEXT TIME (only 3 steps):
═══════════════════════════════════════════

  cd C:\Mirror_Analyzer
  mirror_env\Scripts\activate
  python app.py

Then open Chrome → http://localhost:5000

═══════════════════════════════════════════
EXTERNAL WEBCAM:
═══════════════════════════════════════════

  Open app.py and change:
  cap = cv2.VideoCapture(0)
  to:
  cap = cv2.VideoCapture(1)

═══════════════════════════════════════════
PROJECT STRUCTURE:
═══════════════════════════════════════════

  Mirror_Analyzer/
  ├── app.py                 (main server)
  ├── health_analyzer.py     (AI engine)
  ├── requirements.txt       (packages)
  ├── README.txt             (this file)
  ├── model/
  │   └── best_skin_model.h5 (AI model)
  ├── modules/
  │   ├── skin/              (skin disease)
  │   ├── face/              (landmarks)
  │   ├── eyes/              (eye analysis)
  │   ├── lips/              (lip analysis)
  │   └── nose/              (nose analysis)
  ├── templates/
  │   └── index.html         (dashboard)
  └── static/
      ├── css/style.css      (design)
      └── js/main.js         (live updates)

═══════════════════════════════════════════
TROUBLESHOOTING:
═══════════════════════════════════════════

Problem: Webcam not showing
Solution: Change VideoCapture(0) to (1) in app.py

Problem: Ollama health report not working
Solution: Open new terminal and run: ollama serve

Problem: Package install fails
Solution: Make sure Python 3.11 is installed
          not 3.12 or higher

Problem: Port 5000 already in use
Solution: Change port=5000 to port=5001
          in app.py last line
          Then open: http://localhost:5001

═══════════════════════════════════════════
BUILT BY: [Nerual Nexus]
COLLEGE:  [Your College Name]
YEAR:     2026
═══════════════════════════════════════════