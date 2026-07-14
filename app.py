import cv2
import sys
import base64
import threading
import time
import numpy as np
import ollama
from flask import Flask, render_template
from flask_socketio import SocketIO

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from health_analyzer import HealthAnalyzer

app    = Flask(__name__)
socket = SocketIO(app, cors_allowed_origins="*",
                  async_mode='threading')

analyzer   = HealthAnalyzer()
report     = "Initializing health analysis..."
generating = False

# Camera stream details
camera_index = -1
camera_width = 0
camera_height = 0
camera_status = {"connected": False, "message": "Webcam not detected"}

# Global state to store live physical sensor values
latest_sensor_data = {
    'temperature': 36.7,
    'heart_rate': 72,
    'spo2': 98,
    'hrv': 38,
    'vibration': 0.0
}

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
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={'num_predict': 35, 'temperature': 0.3, 'num_ctx': 256, 'num_thread': 4}
            )
            raw = resp['message']['content']
            sentences = raw.replace('\n',' ').split('.')
            report = '. '.join(
                sentences[:2]).strip() + '.'
        except:
            report = "Analysis complete."
        generating = False
    threading.Thread(target=run,
                     daemon=True).start()

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

def init_camera():
    attempts = [
        (0, cv2.CAP_DSHOW),
        (0, None),
        (1, cv2.CAP_DSHOW),
        (1, None),
        (2, cv2.CAP_DSHOW),
        (2, None)
    ]
    for idx, api in attempts:
        try:
            print(f"[CAMERA] Attempting to open webcam at index {idx}...")
            if api is not None:
                cap = cv2.VideoCapture(idx, api)
            else:
                cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
                    print(f"[CAMERA SUCCESS] Succeeded on index {idx} (Resolution: {w}x{h})")
                    return cap, idx, w, h
                cap.release()
        except Exception as e:
            print(f"[CAMERA ERROR] Failed attempting index {idx}: {e}")
    print("[CAMERA ERROR] Could not open webcam at index 0, 1, or 2. Check: (1) another app using the camera, (2) Windows camera privacy settings, (3) correct camera index.")
    return None, -1, 0, 0

def camera_loop():
    global report, camera_index, camera_width, camera_height, camera_status
    cap, camera_index, camera_width, camera_height = init_camera()
    
    if cap is None:
        camera_status = {
            "connected": False,
            "message": "⚠ Camera not detected — close other apps using the camera and check Windows camera privacy settings"
        }
        # In a loop, emit offline status periodically and try to reconnect
        while cap is None:
            socket.emit('camera_status', camera_status)
            time.sleep(2)
            cap, camera_index, camera_width, camera_height = init_camera()
            
    camera_status = {"connected": True, "message": "Webcam connected"}
    socket.emit('camera_status', camera_status)

    counter = 0
    t0      = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            # Emit camera failure on runtime disconnect
            camera_status = {
                "connected": False,
                "message": "⚠ Camera not detected — close other apps using the camera and check Windows camera privacy settings"
            }
            socket.emit('camera_status', camera_status)
            time.sleep(1)
            continue

        fps = 1 / max(time.time()-t0, 0.001)
        t0  = time.time()

        results = {}
        if counter % 10 == 0:
            results = analyzer.analyze(frame)
            if ('skin' in results and
                    counter % 150 == 0):
                gen_report(results)

        counter += 1

        if not results:
            continue

        # Encode frame to base64 for browser
        _, buf = cv2.imencode(
            '.jpg', frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_b64 = base64.b64encode(
            buf).decode('utf-8')

        # Get results safely
        skin   = results.get('skin',  {})
        eyes   = results.get('eyes',  {})
        lips   = results.get('lips',  {})
        nose   = results.get('nose',  {})
        face   = results.get('face',  {})
        alerts = results.get('alerts', [])

        # Convert all scores to plain float
        raw_scores = skin.get('all_scores', {})
        clean_scores = {
            safe_str(k): round(safe_float(v), 1)
            for k, v in raw_scores.items()
        }

        data = {
            'frame' : frame_b64,
            'fps'   : round(safe_float(fps), 1),
            'report': safe_str(report),
            'face': {
                'symmetry' : round(safe_float(
                    face.get('symmetry', 0)), 1),
                'landmarks': int(len(
                    face.get('points', {}))),
            },
            'skin': {
                'disease'   : safe_str(
                    skin.get('disease', '')),
                'confidence': round(safe_float(
                    skin.get('confidence', 0)), 1),
                'urgent'    : safe_bool(
                    skin.get('urgent', False)),
                'scores'    : clean_scores,
            },
            'eyes': {
                'fatigue'      : safe_bool(
                    eyes.get('fatigue', False)),
                'fatigue_score': round(safe_float(
                    eyes.get('fatigue_score', 0)), 1),
                'redness'      : round(safe_float(
                    eyes.get('redness', 0)), 1),
                'dark_circles' : safe_bool(
                    eyes.get('dark_circles', False)),
            },
            'lips': {
                'lip_color': safe_str(
                    lips.get('lip_color', 'Normal')),
                'cyanosis' : safe_bool(
                    lips.get('cyanosis', False)),
                'pallor'   : safe_bool(
                    lips.get('pallor', False)),
                'dryness'  : safe_bool(
                    lips.get('dryness', False)),
                'symmetry' : round(safe_float(
                    lips.get('symmetry', 0)), 1),
            },
            'nose': {
                'redness'     : round(safe_float(
                    nose.get('redness', 0)), 1),
                'pore_size'   : safe_str(
                    nose.get('pore_size', 'Normal')),
                'blackheads'  : safe_bool(
                    nose.get('blackheads', False)),
                'color_change': safe_str(
                    nose.get('color_change',
                             'Normal')),
                'symmetry'    : round(safe_float(
                    nose.get('symmetry', 0)), 1),
            },
            'alerts': [
                {
                    'level'  : safe_str(a['level']),
                    'message': safe_str(a['message'])
                }
                for a in alerts
            ],
            'sensors': {
                'temperature': latest_sensor_data['temperature'],
                'heart_rate' : latest_sensor_data['heart_rate'],
                'spo2'       : latest_sensor_data['spo2'],
                'hrv'        : latest_sensor_data['hrv'],
                'vibration'  : f"{latest_sensor_data['vibration']:.1f} kPa",
            }
        }

        socket.emit('health_data', data)
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sensors/update', methods=['POST'])
def update_sensors():
    from flask import request, jsonify
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON payload"}), 400
        
        # Save received physical values directly into the global state
        if 'temperature' in data:
            latest_sensor_data['temperature'] = float(data['temperature'])
        if 'heart_rate' in data:
            latest_sensor_data['heart_rate'] = int(data['heart_rate'])
        if 'spo2' in data:
            latest_sensor_data['spo2'] = int(data['spo2'])
        if 'hrv' in data:
            latest_sensor_data['hrv'] = int(data['hrv'])
        if 'vibration' in data:
            latest_sensor_data['vibration'] = float(data['vibration'])
            
        return jsonify({"success": True, "received": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@socket.on('connect')
def handle_connect():
    socket.emit('camera_status', camera_status)

if __name__ == '__main__':
    t = threading.Thread(
        target=camera_loop, daemon=True)
    t.start()
    
    # Wait a moment for camera loop to finish initialization and set global variables
    time.sleep(2.0)
    
    # Determine fallback modes
    is_mediapipe_fallback = analyzer.face.face_mesh is None
    is_tensorflow_fallback = analyzer.skin.model is None
    
    print("\n" + "="*60)
    print("           MIRROR ANALYZER PRO STARTUP SUMMARY")
    print("="*60)
    if camera_index != -1:
        print(f"  Web Camera Index  : {camera_index}")
        print(f"  Resolution        : {camera_width}x{camera_height}")
        print(f"  Camera Status     : ACTIVE (ONLINE)")
    else:
        print(f"  Camera Status     : ERROR (OFFLINE)")
        print(f"  Warning           : No webcam discovered on index 0, 1, or 2.")
    
    print(f"  MediaPipe Status  : {'FALLBACK MODE (No Solutions)' if is_mediapipe_fallback else 'ACTIVE'}")
    print(f"  TensorFlow Status : {'FALLBACK MODE (Prediction Mock)' if is_tensorflow_fallback else 'ACTIVE'}")
    print("-"*60)
    print("  Dashboard URL     : http://localhost:5000")
    print("="*60 + "\n")
    
    socket.run(app, host='0.0.0.0',
               port=5000, debug=False, allow_unsafe_werkzeug=True)