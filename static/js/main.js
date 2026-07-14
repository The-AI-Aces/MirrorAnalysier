const socket = io();

// Clock
function updateClock() {
  const now = new Date();
  const d = now.toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
  const t = now.toLocaleTimeString('en-GB');
  const clockEl = document.getElementById('clock');
  if (clockEl) clockEl.textContent = d + '  ' + t;
}
setInterval(updateClock, 1000);
updateClock();

// Session timer
let seconds = 0;
const sessionEl = document.getElementById('session');
setInterval(() => {
  seconds++;
  const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
  const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  if (sessionEl) sessionEl.textContent = `${h}:${m}:${s}`;
}, 1000);

function setBar(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = Math.max(0, Math.min(pct, 100)) + '%';
}

function setBadge(id, text, colorClass) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = 'badge ' + colorClass;
}

function setVal(id, text, colorClass) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  if (colorClass) {
    el.className = 'v-value ' + (colorClass === 'green' ? 'text-green' : colorClass === 'yellow' ? 'text-amber' : colorClass === 'red' ? 'text-red' : 'text-blue');
  }
}

// Actionable skin recommendations mapping
const RECOMMENDATIONS = {
  'Actinic Keratosis (AK)': 'Pre-cancerous skin lesions. Protect your skin from UV rays and schedule a dermatologist evaluation.',
  'Basal Cell Carcinoma (BCC)': 'Potential skin malignancy. Consult a medical professional for diagnosis and treatment planning.',
  'Benign Keratosis (BKL)': 'Non-cancerous skin growth. No immediate medical action is required. Monitor for changes.',
  'Dermatofibroma (DF)': 'Benign fibrous nodule. Harmless and typically requires no treatment. Keep skin hydrated.',
  'Melanoma (MEL)': 'CRITICAL: Potential melanoma. Immediate specialist clinical evaluation is highly recommended.',
  'Nevus (NV)': 'Common benign skin mole. Typically harmless. Conduct regular self checks and track any border changes.',
  'Squamous Cell Carcinoma (SCC)': 'Potential skin malignancy. Please seek medical evaluation for early removal.',
  'Vascular Lesion (VASC)': 'Benign blood vessel anomaly. Keep skin clean and consult a doctor if irritation occurs.'
};

socket.on('health_data', (d) => {
  // Update Frame
  const img = document.getElementById('faceImg');
  if (d.frame && img) img.src = 'data:image/jpeg;base64,' + d.frame;

  // Header stats updates
  const fpsEl = document.getElementById('fps');
  if (fpsEl) fpsEl.textContent = d.fps;
  
  const landmarksEl = document.getElementById('landmarks');
  if (landmarksEl) landmarksEl.textContent = d.face.landmarks;
  
  const bLmEl = document.getElementById('b-lm');
  if (bLmEl) bLmEl.textContent = d.face.landmarks;
  
  const bFpsEl = document.getElementById('b-fps');
  if (bFpsEl) bFpsEl.textContent = d.fps;
  
  const bAlertsEl = document.getElementById('b-alerts');
  if (bAlertsEl) {
    bAlertsEl.textContent = d.alerts.length;
    bAlertsEl.className = 'f-val ' + (d.alerts.length > 0 ? 'text-red' : 'text-green');
  }

  // Quick stats panels
  const stLmEl = document.getElementById('st-lm');
  if (stLmEl) stLmEl.textContent = d.face.landmarks;
  
  const stSymEl = document.getElementById('st-sym');
  if (stSymEl) stSymEl.textContent = d.face.symmetry.toFixed(1) + '%';

  // Alert Banner Control
  const banner = document.getElementById('alertBanner');
  const alertText = document.getElementById('alertText');
  if (banner && alertText) {
    const redAlerts = d.alerts.filter(a => a.level === 'RED');
    if (redAlerts.length > 0) {
      banner.className = 'alert-banner red';
      alertText.textContent = 'WARNING: ' + redAlerts[0].message.toUpperCase();
    } else {
      banner.className = 'alert-banner';
      alertText.textContent = d.eyes.fatigue
        ? 'SYSTEM ALERT: MILD FATIGUE DETECTED — HEALTH ADVISEMENT ACTIVE'
        : 'ALL DIAGNOSTIC SYSTEMS NORMAL — PATIENT STABLE';
    }
  }

  // Eye Metrics
  setBar('bar-fatigue', d.eyes.fatigue_score);
  setVal('val-fatigue', d.eyes.fatigue_score + '%', d.eyes.fatigue_score > 50 ? 'yellow' : 'green');
  setBar('bar-redness', d.eyes.redness);
  setVal('val-redness', d.eyes.redness < 20 ? 'Low' : 'High', d.eyes.redness < 20 ? 'green' : 'red');
  setBadge('val-dark', d.eyes.dark_circles ? 'Mild' : 'NONE', d.eyes.dark_circles ? 'yellow' : 'green');
  setBar('bar-sym', d.face.symmetry);
  setVal('val-sym', d.face.symmetry.toFixed(0) + '%', d.face.symmetry > 75 ? 'green' : 'yellow');
  setBadge('val-jaundice', d.eyes.jaundice ? 'ALERT' : 'NOT DETECTED', d.eyes.jaundice ? 'red' : 'green');

  // Nose Metrics
  setBar('bar-nose-red', d.nose.redness);
  setVal('val-nose-red', d.nose.redness < 20 ? 'Low' : 'High', d.nose.redness < 20 ? 'green' : 'red');
  setBadge('val-pore', d.nose.pore_size, d.nose.pore_size === 'Normal' ? 'green' : 'yellow');
  setBadge('val-black', d.nose.blackheads ? 'MILD' : 'NONE', d.nose.blackheads ? 'yellow' : 'green');
  setBadge('val-ncolor', d.nose.color_change, d.nose.color_change === 'Normal' ? 'green' : 'yellow');
  setBar('bar-nose-sym', d.nose.symmetry);
  setVal('val-nose-sym', d.nose.symmetry.toFixed(0) + '%', 'green');

  // Lip Metrics
  setVal('val-lipcolor', d.lips.lip_color, 'blue');
  setBadge('val-pallor', d.lips.pallor ? 'DETECTED' : 'NONE', d.lips.pallor ? 'red' : 'green');
  setBadge('val-cyan', d.lips.cyanosis ? 'DETECTED' : 'NOT DETECTED', d.lips.cyanosis ? 'red' : 'green');
  setBadge('val-dry', d.lips.dryness ? 'Mild' : 'None', d.lips.dryness ? 'yellow' : 'green');
  setBar('bar-lip-sym', d.lips.symmetry);
  setVal('val-lip-sym', d.lips.symmetry.toFixed(0) + '%', 'green');

  // Skin Disease Scanner
  const skinDiseaseEl = document.getElementById('skinDisease');
  if (skinDiseaseEl) {
    skinDiseaseEl.textContent = d.skin.disease;
    skinDiseaseEl.className = 'skin-disease-name' + (d.skin.urgent ? ' urgent' : '');
  }

  const skinConfEl = document.getElementById('skinConf');
  if (skinConfEl) {
    skinConfEl.textContent = 'Confidence: ' + d.skin.confidence + '%';
  }

  const skinRecEl = document.getElementById('skinRec');
  if (skinRecEl) {
    skinRecEl.textContent = RECOMMENDATIONS[d.skin.disease] || 'Initial diagnostic analysis complete. Monitor for any structural anomalies.';
  }

  // Melanoma Alerts
  setBadge('flag-mel', d.skin.urgent ? 'ALERT' : 'CLEAR', d.skin.urgent ? 'red' : 'green');

  // Score Distribution Horizontal Progress Bars
  const barsDiv = document.getElementById('scoreBars');
  if (barsDiv && d.skin.scores) {
    barsDiv.innerHTML = '';
    Object.entries(d.skin.scores).forEach(([name, val]) => {
      barsDiv.innerHTML += `
        <div class="score-dist-row">
          <span class="score-dist-label">${name}</span>
          <div class="score-dist-track">
            <div class="score-dist-fill" style="width:${val}%"></div>
          </div>
          <span class="score-dist-val">${val}%</span>
        </div>`;
    });
  }

  // SLM Report summary text
  const reportTextEl = document.getElementById('reportText');
  if (d.report && reportTextEl) {
    reportTextEl.textContent = d.report;
  }

  // Sensors raw stream values
  if (d.sensors) {
    const tempEl = document.getElementById('val-temp');
    if (tempEl) tempEl.textContent = d.sensors.temperature + ' °C';
    
    const hrEl = document.getElementById('val-hr');
    if (hrEl) hrEl.textContent = d.sensors.heart_rate + ' bpm';
    
    const spo2El = document.getElementById('val-spo2');
    if (spo2El) spo2El.textContent = d.sensors.spo2 + '%';
    
    const vibEl = document.getElementById('val-vibration');
    if (vibEl) vibEl.textContent = d.sensors.vibration;

    // Fever and tachycardia triggers
    const isFever = parseFloat(d.sensors.temperature) > 37.8;
    const isTachy = parseInt(d.sensors.heart_rate) > 100;

    const feverBadge = document.getElementById('badge-fever');
    if (feverBadge) {
      feverBadge.textContent = isFever ? 'HIGH' : 'CLEAR';
      feverBadge.className = 'badge ' + (isFever ? 'red' : 'green');
    }

    const tachyBadge = document.getElementById('badge-tachy');
    if (tachyBadge) {
      tachyBadge.textContent = isTachy ? 'HIGH' : 'NONE';
      tachyBadge.className = 'badge ' + (isTachy ? 'red' : 'green');
    }

    // HRV Stress Levels
    const hrvVal = parseInt(d.sensors.hrv);
    const hrvEl = document.getElementById('val-hrv');
    if (hrvEl) {
      if (hrvVal < 30) {
        hrvEl.textContent = 'High';
        hrvEl.className = 'v-value text-red';
      } else if (hrvVal < 45) {
        hrvEl.textContent = 'Mild';
        hrvEl.className = 'v-value text-amber';
      } else {
        hrvEl.textContent = 'Normal';
        hrvEl.className = 'v-value text-green';
      }
    }
  }
});

socket.on('camera_status', (status) => {
  const banner = document.getElementById('cameraErrorBanner');
  const txt = document.getElementById('cameraErrorText');
  if (banner) {
    if (!status.connected) {
      banner.classList.remove('hidden');
      if (txt && status.message) {
        txt.textContent = status.message;
      }
    } else {
      banner.classList.add('hidden');
    }
  }
});
