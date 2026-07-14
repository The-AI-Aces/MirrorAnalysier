import cv2
import sys
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.face.face_analyzer import FaceAnalyzer
from modules.skin.disease_detector import SkinDiseaseDetector
from modules.eyes.eye_analyzer import EyeAnalyzer
from modules.lips.lip_analyzer import LipAnalyzer
from modules.nose.nose_analyzer import NoseAnalyzer

class HealthAnalyzer:
    def __init__(self):
        print("Initializing Mirror Analyzer...")
        self.face    = FaceAnalyzer()
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, 'model', 'skin_model_v2.tflite')
        if not os.path.exists(model_path):
            model_path = os.path.join(base_dir, 'model', 'skin_model_v2 (1).h5')
        if not os.path.exists(model_path):
            model_path = os.path.join(base_dir, 'model', 'skin_model_v2.h5')
        self.skin    = SkinDiseaseDetector(model_path)
        self.eyes    = EyeAnalyzer()
        self.lips    = LipAnalyzer()
        self.nose    = NoseAnalyzer()
        print("All modules loaded!")

    def analyze(self, frame):
        results = {'frame': frame}

        # Step 1 — Face landmarks (needed by all modules)
        face_result = self.face.analyze(frame)
        if face_result is None:
            results['error'] = 'No face detected'
            return results
        results['face'] = face_result
        points = face_result['points']

        # Step 2 — Skin disease
        results['skin'] = self.skin.predict(frame)

        # Step 3 — Eyes
        results['eyes'] = self.eyes.analyze(frame, points)

        # Step 4 — Lips
        results['lips'] = self.lips.analyze(frame, points)

        # Step 5 — Nose
        results['nose'] = self.nose.analyze(frame, points)

        # Step 6 — Urgent alerts
        results['alerts'] = self._check_alerts(results)

        return results

    def _check_alerts(self, results):
        alerts = []

        # Skin disease urgent
        if results['skin']['urgent']:
            alerts.append({
                'level': 'RED',
                'message': f"Skin: {results['skin']['disease']} detected!"
            })

        # Cyanosis (blue lips = oxygen problem)
        if results['lips']['cyanosis']:
            alerts.append({
                'level': 'RED',
                'message': 'Cyanosis detected — possible oxygen issue!'
            })

        # Fatigue
        if results['eyes']['fatigue']:
            alerts.append({
                'level': 'YELLOW',
                'message': 'Eye fatigue detected — rest needed'
            })

        # Face asymmetry
        if results['face']['symmetry'] < 60:
            alerts.append({
                'level': 'RED',
                'message': 'Severe facial asymmetry detected!'
            })

        return alerts


def print_results(results):
    print("\n" + "="*50)
    print("     MIRROR ANALYZER — HEALTH REPORT")
    print("="*50)

    if 'error' in results:
        print(f"❌ {results['error']}")
        return

    # Face
    print(f"\n👤 FACE")
    print(f"   Symmetry      : {results['face']['symmetry']}%")

    # Skin
    print(f"\n🔬 SKIN DISEASE")
    print(f"   Detected      : {results['skin']['disease']}")
    print(f"   Confidence    : {results['skin']['confidence']:.1f}%")
    print(f"   Urgent        : {'⚠️  YES' if results['skin']['urgent'] else '✅ No'}")

    # Eyes
    print(f"\n👁️  EYES")
    print(f"   Fatigue       : {'⚠️  Yes' if results['eyes']['fatigue'] else '✅ No'}")
    print(f"   Redness       : {results['eyes']['redness']:.1f}%")
    print(f"   Dark circles  : {'Yes' if results['eyes']['dark_circles'] else 'No'}")

    # Lips
    print(f"\n👄 LIPS")
    print(f"   Color         : {results['lips']['lip_color']}")
    print(f"   Cyanosis      : {'⚠️  YES' if results['lips']['cyanosis'] else '✅ No'}")
    print(f"   Pallor        : {'Yes' if results['lips']['pallor'] else 'No'}")
    print(f"   Dryness       : {'Yes' if results['lips']['dryness'] else 'No'}")

    # Nose
    print(f"\n👃 NOSE")
    print(f"   Redness       : {results['nose']['redness']:.1f}%")
    print(f"   Pore size     : {results['nose']['pore_size']}")
    print(f"   Color change  : {results['nose']['color_change']}")

    # Alerts
    print(f"\n🚨 ALERTS ({len(results['alerts'])} found)")
    if results['alerts']:
        for alert in results['alerts']:
            icon = "🔴" if alert['level'] == 'RED' else "🟡"
            print(f"   {icon} {alert['message']}")
    else:
        print("   ✅ No urgent alerts!")

    print("\n" + "="*50)


if __name__ == "__main__":
    analyzer = HealthAnalyzer()

    print("\nCapturing from webcam...")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if ret:
        results = analyzer.analyze(frame)
        print_results(results)
        cv2.imwrite(
            'D:\\Final_Mirror_Analyzer\\output\\health_report.jpg',
            frame
        )
        print("\nImage saved to output folder!")
    else:
        print("Webcam not found!")