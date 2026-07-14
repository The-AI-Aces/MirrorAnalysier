import cv2
import sys
import os
import base64
import threading
import time
import numpy as np
import ollama
from flask import Flask, render_template, request
from flask_socketio import SocketIO

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from health_analyzer import HealthAnalyzer

app = Flask(__name__)
socket = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

analyzer = HealthAnalyzer()
report = "Initializing health analysis..."
generating = False
camera_status = {"connected": False, "message": "Camera offline"}

def gen_report(r):
    global report, generating
    if generating:
        return
    generating = True
    def run():
        global report, generating
        try:
            prompt = (
                f"Health scan: "
                f"Face symmetry {r['face']['symmetry']:.0f}%, "
                f"Skin: {r['skin']['disease']} "
                f"({r['skin']['confidence']:.0f}% confidence), "
                f"Eye fatigue: {r['eyes']['fatigue']}, "
                f"Lip color: {r['lips']['lip_color']}, "
                f"Alerts: {len(r['alerts'])}. "
                f"Write 2 sentences health summary "
                f"in plain professional English."
            )
            resp = ollama.chat(
                model='phi3:mini',
                messages=[{'role': 'user', 'content': prompt}],
                options={'num_predict': 50, 'temperature': 0.3}
            )
            raw = resp['message']['content']
            sentences = raw.replace('\n',' ').split('.')
            report = '. '.join(sentences[:2]).strip() + '.'
        except:
            report = "Analysis complete."
        generating = False
    threading.Thread(target=run, daemon=True).start()

def safe_bool(val):
    return bool(val)

def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

def safe_str(val, default=''):
    try:
        return str(val)
    except:
        return default

def camera_loop():
    global report, camera_status
    cap = None
    try:
        cap = cv2.VideoCapture(0)
    except:
        pass
        
    counter = 0
    t0 = time.time()

    while True:
        if cap is None or not cap.isOpened():
            camera_status = {"connected": False, "message": "No camera on server. Using browser webcam."}
            socket.emit('camera_status', camera_status)
            time.sleep(2.0)
            try:
                cap = cv2.VideoCapture(0)
            except:
                pass
            continue
            
        ret, frame = cap.read()
        if not ret:
            camera_status = {"connected": False, "message": "Camera disconnected. Using browser webcam."}
            socket.emit('camera_status', camera_status)
            time.sleep(2.0)
            continue

        camera_status = {"connected": True, "message": "Using server camera."}
        socket.emit('camera_status', camera_status)

        fps = 1 / max(time.time()-t0, 0.001)
        t0 = time.time()

        results = {}
        if counter % 10 == 0:
            results = analyzer.analyze(frame)
            if ('skin' in results and counter % 150 == 0):
                gen_report(results)

        counter += 1

        if not results:
            continue

        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_b64 = base64.b64encode(buf).decode('utf-8')

        skin = results.get('skin', {})
        eyes = results.get('eyes', {})
        lips = results.get('lips', {})
        nose = results.get('nose', {})
        face = results.get('face', {})
        alerts = results.get('alerts', [])

        raw_scores = skin.get('all_scores', {})
        clean_scores = {
            safe_str(k): round(safe_float(v), 1)
            for k, v in raw_scores.items()
        }

        data = {
            'frame': frame_b64,
            'fps': round(safe_float(fps), 1),
            'report': safe_str(report),
            'face': {
                'symmetry': round(safe_float(face.get('symmetry', 0)), 1),
                'landmarks': int(len(face.get('points', {}))),
            },
            'skin': {
                'disease': safe_str(skin.get('disease', '')),
                'confidence': round(safe_float(skin.get('confidence', 0)), 1),
                'urgent': safe_bool(skin.get('urgent', False)),
                'scores': clean_scores,
            },
            'eyes': {
                'fatigue': safe_bool(eyes.get('fatigue', False)),
                'fatigue_score': round(safe_float(eyes.get('fatigue_score', 0)), 1),
                'redness': round(safe_float(eyes.get('redness', 0)), 1),
                'dark_circles': safe_bool(eyes.get('dark_circles', False)),
            },
            'lips': {
                'lip_color': safe_str(lips.get('lip_color', 'Normal')),
                'cyanosis': safe_bool(lips.get('cyanosis', False)),
                'pallor': safe_bool(lips.get('pallor', False)),
                'dryness': safe_bool(lips.get('dryness', False)),
                'symmetry': round(safe_float(lips.get('symmetry', 0)), 1),
            },
            'nose': {
                'redness': round(safe_float(nose.get('redness', 0)), 1),
                'pore_size': safe_str(nose.get('pore_size', 'Normal')),
                'blackheads': safe_bool(nose.get('blackheads', False)),
                'color_change': safe_str(nose.get('color_change', 'Normal')),
                'symmetry': round(safe_float(nose.get('symmetry', 0)), 1),
            },
            'alerts': [
                {'level': safe_str(a['level']), 'message': safe_str(a['message'])}
                for a in alerts
            ],
        }

        socket.emit('health_data', data)
        time.sleep(0.01)

def generate_fallback_report(r):
    try:
        disease = r['skin']['disease']
        conf = r['skin']['confidence']
        fatigue = r['eyes']['fatigue']
        redness = r['eyes']['redness']
        lip_color = r['lips']['lip_color']
        cyanosis = r['lips']['cyanosis']
        symmetry = r['face']['symmetry']
        
        parts = []
        if r['skin']['urgent']:
            parts.append(f"Visual inspection indicates a potential skin condition ({disease}, {conf:.1f}% confidence) requiring direct clinical evaluation.")
        else:
            parts.append(f"Skin assessment identifies {disease} ({conf:.1f}% confidence), with no urgent flags detected.")
            
        eye_status = "mild eye fatigue" if fatigue else "normal eye appearance"
        lip_status = "cyanotic indications" if cyanosis else f"{lip_color.lower()} lip color"
        parts.append(f"Ocular scans show {eye_status} (redness {redness:.1f}%), while oral scans indicate {lip_status} with facial symmetry at {symmetry:.1f}%.")
        
        return " ".join(parts)
    except:
        return "Analysis complete."

@socket.on('connect')
def handle_connect():
    socket.emit('camera_status', camera_status)

@socket.on('client_frame')
def handle_client_frame(data_url):
    try:
        # Decode base64 image
        header, encoded = data_url.split(",", 1)
        img_data = base64.b64decode(encoded)
        np_img = np.frombuffer(img_data, dtype=np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        
        if frame is None:
            return
            
        # Run health analyzer
        results = analyzer.analyze(frame)
        
        # Check alerts
        alerts = results.get('alerts', [])
        
        # Generate summary report (using fallback if Ollama is not running)
        client_report = "Analyzing..."
        try:
            prompt = (
                f"Health scan: "
                f"Face symmetry {results['face']['symmetry']:.0f}%, "
                f"Skin: {results['skin']['disease']} "
                f"({results['skin']['confidence']:.0f}% confidence), "
                f"Eye fatigue: {results['eyes']['fatigue']}, "
                f"Lip color: {results['lips']['lip_color']}, "
                f"Alerts: {len(results['alerts'])}. "
                f"Write 2 sentences health summary "
                f"in plain professional English."
            )
            resp = ollama.chat(
                model='phi3:mini',
                messages=[{'role': 'user', 'content': prompt}],
                options={'num_predict': 50, 'temperature': 0.3}
            )
            raw = resp['message']['content']
            sentences = raw.replace('\n',' ').split('.')
            client_report = '. '.join(sentences[:2]).strip() + '.'
        except Exception:
            client_report = generate_fallback_report(results)
            
        fps = 15.0 # Client-side streaming simulated FPS
        
        skin = results.get('skin', {})
        eyes = results.get('eyes', {})
        lips = results.get('lips', {})
        nose = results.get('nose', {})
        face = results.get('face', {})
        
        raw_scores = skin.get('all_scores', {})
        clean_scores = {
            safe_str(k): round(safe_float(v), 1)
            for k, v in raw_scores.items()
        }
        
        data = {
            'fps': round(safe_float(fps), 1),
            'report': safe_str(client_report),
            'face': {
                'symmetry': round(safe_float(face.get('symmetry', 0)), 1),
                'landmarks': int(len(face.get('points', {}))),
            },
            'skin': {
                'disease': safe_str(skin.get('disease', '')),
                'confidence': round(safe_float(skin.get('confidence', 0)), 1),
                'urgent': safe_bool(skin.get('urgent', False)),
                'scores': clean_scores,
            },
            'eyes': {
                'fatigue': safe_bool(eyes.get('fatigue', False)),
                'fatigue_score': round(safe_float(eyes.get('fatigue_score', 0)), 1),
                'redness': round(safe_float(eyes.get('redness', 0)), 1),
                'dark_circles': safe_bool(eyes.get('dark_circles', False)),
            },
            'lips': {
                'lip_color': safe_str(lips.get('lip_color', 'Normal')),
                'cyanosis': safe_bool(lips.get('cyanosis', False)),
                'pallor': safe_bool(lips.get('pallor', False)),
                'dryness': safe_bool(lips.get('dryness', False)),
                'symmetry': round(safe_float(lips.get('symmetry', 0)), 1),
            },
            'nose': {
                'redness': round(safe_float(nose.get('redness', 0)), 1),
                'pore_size': safe_str(nose.get('pore_size', 'Normal')),
                'blackheads': safe_bool(nose.get('blackheads', False)),
                'color_change': safe_str(nose.get('color_change', 'Normal')),
                'symmetry': round(safe_float(nose.get('symmetry', 0)), 1),
            },
            'alerts': [
                {'level': safe_str(a['level']), 'message': safe_str(a['message'])}
                for a in alerts
            ],
        }
        
        socket.emit('health_data', data, room=request.sid)
    except Exception as e:
        print(f"Error processing client frame: {e}")

@app.route('/')
def index():
    return render_template('index_medical.html')

if __name__ == '__main__':
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()
    print("\n" + "="*60)
    print("  Mirror Analyzer - MEDICAL THEME")
    print("="*60)
    port = int(os.environ.get('PORT', 5001))
    print(f"\nRunning on port: {port}")
    print("="*60 + "\n")
    socket.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)