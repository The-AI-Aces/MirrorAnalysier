const socket = io();

let sessionSeconds = 0;

// Update clock
function updateClock() {
    const now = new Date();
    const date = now.toLocaleDateString('en-US', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
    });
    const time = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
    // Can update display if needed
}
setInterval(updateClock, 1000);
updateClock();

// Session timer
setInterval(() => {
    sessionSeconds++;
    const h = String(Math.floor(sessionSeconds / 3600)).padStart(2, '0');
    const m = String(Math.floor((sessionSeconds % 3600) / 60)).padStart(2, '0');
    const s = String(sessionSeconds % 60).padStart(2, '0');
    document.getElementById('sessionTime').textContent = `${h}:${m}:${s}`;
}, 1000);

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        
        // Remove active from all buttons and panes
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Add active to clicked button and corresponding pane
        button.classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// Helper functions
function setBarWidth(elementId, percentage) {
    const el = document.getElementById(elementId);
    if (el) {
        el.style.width = Math.min(percentage, 100) + '%';
    }
}

function setText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text;
}

function setBadgeClass(elementId, badgeClass) {
    const el = document.getElementById(elementId);
    if (el) {
        el.className = 'badge';
        if (badgeClass) el.classList.add(badgeClass);
    }
}

function setAlertBanner(isAlert, message) {
    const banner = document.getElementById('alertBanner');
    const text = document.getElementById('alertText');
    if (isAlert) {
        banner.classList.add('danger');
        text.textContent = '🚨 ' + message;
    } else {
        banner.classList.remove('danger', 'warning');
        banner.classList.add('success');
        text.textContent = '✓ All systems normal';
    }
}

function updateScoreRing(score) {
    const ring = document.getElementById('scoreRing');
    if (ring) {
        const circumference = 283;
        const offset = circumference - (score / 100) * circumference;
        ring.style.strokeDashoffset = offset;
    }
}

// Real-time data updates
socket.on('health_data', (data) => {
    try {
        // Update face image
        const img = document.getElementById('faceImg');
        if (data.frame) {
            img.src = 'data:image/jpeg;base64,' + data.frame;
        }

        // Update top stats
        setText('fps', data.fps.toFixed(1));
        setText('landmarks', data.face.landmarks);
        setText('alertCount', data.alerts.length);

        // Update footer
        setText('footerFps', data.fps.toFixed(1));

        // SKIN TAB
        const skinDisease = data.skin.disease || 'Analyzing...';
        const skinConfidence = data.skin.confidence || 0;
        const skinUrgent = data.skin.urgent || false;

        setText('skinDisease', skinDisease);
        setText('skinConfidence', skinConfidence.toFixed(1) + '%');

        const urgentBadge = document.getElementById('urgencyBadge');
        if (skinUrgent) {
            urgentBadge.className = 'urgency-badge danger';
            setText('urgencyText', '⚠️ URGENT - See Doctor');
        } else {
            urgentBadge.className = 'urgency-badge';
            setText('urgencyText', '✓ Normal');
        }

        // Skin recommendation
        if (skinUrgent) {
            setText('skinRecommendation', 
                'This condition requires immediate consultation with a dermatologist. ' +
                'Please seek professional medical advice as soon as possible.');
        } else {
            setText('skinRecommendation', 
                'Your skin analysis shows normal results. Continue regular skincare ' +
                'and maintain healthy habits.');
        }

        // Score breakdown
        const scoreList = document.getElementById('scoreList');
        scoreList.innerHTML = '';
        const scores = data.skin.scores || {};
        Object.entries(scores).forEach(([name, val]) => {
            const shortName = name.includes('(') 
                ? name.split('(')[1].replace(')', '')
                : name.substring(0, 8);
            const item = document.createElement('div');
            item.className = 'score-item';
            item.innerHTML = `
                <span class="score-item-label">${shortName}</span>
                <div class="score-item-bar">
                    <div class="score-item-fill" style="width: ${val}%"></div>
                </div>
                <span class="score-item-value">${val.toFixed(1)}%</span>
            `;
            scoreList.appendChild(item);
        });

        // EYES TAB
        const eyeFatigue = data.eyes.fatigue_score || 0;
        const eyeRedness = data.eyes.redness || 0;
        const darkCircles = data.eyes.dark_circles || false;

        setBarWidth('eyeFatigueBar', eyeFatigue);
        setText('eyeFatigueVal', eyeFatigue > 50 ? 'High' : 'Low');

        setBarWidth('eyeRednessBar', eyeRedness);
        setText('eyeRednessVal', eyeRedness < 20 ? 'Low' : 'High');

        const darkCirclesBadge = document.getElementById('darkCirclesBadge');
        if (darkCircles) {
            darkCirclesBadge.className = 'badge warning';
            darkCirclesBadge.textContent = 'Detected';
        } else {
            darkCirclesBadge.className = 'badge';
            darkCirclesBadge.textContent = 'None Detected';
        }

        setText('eyeRecommendation',
            eyeFatigue > 50 
                ? 'Your eyes show signs of fatigue. Take regular breaks and rest your eyes.'
                : 'Your eye health looks good. Maintain regular eye care habits.');

        // NOSE TAB
        const noseRedness = data.nose.redness || 0;
        const poreSize = data.nose.pore_size || 'Normal';
        const blackheads = data.nose.blackheads || false;
        const noseColor = data.nose.color_change || 'Normal';
        const noseSymmetry = data.nose.symmetry || 0;

        setBarWidth('noseRednessBar', noseRedness);
        setText('noseRednessVal', noseRedness < 20 ? 'Low' : 'High');

        setBadgeClass('poreSizeBadge', 'success');
        setText('poreSizeBadge', poreSize);

        if (blackheads) {
            document.getElementById('blackheadsBadge').className = 'badge warning';
            setText('blackheadsBadge', 'Detected');
        } else {
            document.getElementById('blackheadsBadge').className = 'badge';
            setText('blackheadsBadge', 'None');
        }

        setBadgeClass('noseColorBadge', 'success');
        setText('noseColorBadge', noseColor);

        setBarWidth('noseSymmetryBar', noseSymmetry);
        setText('noseSymmetryVal', noseSymmetry.toFixed(0) + '%');

        // LIPS TAB
        const lipColor = data.lips.lip_color || 'Normal';
        const cyanosis = data.lips.cyanosis || false;
        const pallor = data.lips.pallor || false;
        const dryness = data.lips.dryness || false;
        const lipSymmetry = data.lips.symmetry || 0;

        setBadgeClass('lipColorBadge', 'success');
        setText('lipColorBadge', lipColor);

        if (cyanosis) {
            document.getElementById('cyanosisBadge').className = 'badge danger';
            setText('cyanosisBadge', 'Detected ⚠️');
        } else {
            document.getElementById('cyanosisBadge').className = 'badge';
            setText('cyanosisBadge', 'Not Detected');
        }

        if (pallor) {
            document.getElementById('pallorBadge').className = 'badge warning';
            setText('pallorBadge', 'Detected');
        } else {
            document.getElementById('pallorBadge').className = 'badge';
            setText('pallorBadge', 'Not Detected');
        }

        if (dryness) {
            document.getElementById('drynessBadge').className = 'badge warning';
            setText('drynessBadge', 'Detected');
        } else {
            document.getElementById('drynessBadge').className = 'badge';
            setText('drynessBadge', 'None');
        }

        setBarWidth('lipSymmetryBar', lipSymmetry);
        setText('lipSymmetryVal', lipSymmetry.toFixed(0) + '%');

        // OVERALL TAB
        const faceSymmetry = data.face.symmetry || 0;
        setText('faceSymmetryVal', faceSymmetry.toFixed(0) + '%');
        setText('landmarksDetected', data.face.landmarks);

        // Calculate health score
        const baseScore = 80;
        let healthScore = baseScore;
        if (skinUrgent) healthScore -= 25;
        if (eyeFatigue > 50) healthScore -= 10;
        if (cyanosis) healthScore -= 20;
        if (dryness) healthScore -= 5;
        healthScore = Math.max(0, Math.min(100, healthScore));

        setText('healthScore', Math.round(healthScore));
        updateScoreRing(healthScore);

        // PHI-3 Report
        if (data.report) {
            setText('phi3Text', data.report);
        }

        // Alerts list
        const alertsList = document.getElementById('alertsList');
        alertsList.innerHTML = '';
        if (data.alerts && data.alerts.length > 0) {
            setAlertBanner(true, data.alerts[0].message);
            data.alerts.forEach(alert => {
                const alertEl = document.createElement('div');
                alertEl.className = 'alert-item' + (alert.level === 'RED' ? ' danger' : '');
                alertEl.innerHTML = `
                    <span class="alert-item-text">
                        ${alert.level === 'RED' ? '🔴' : '🟡'} ${alert.message}
                    </span>
                `;
                alertsList.appendChild(alertEl);
            });
        } else {
            setAlertBanner(false, '');
            const noAlertEl = document.createElement('div');
            noAlertEl.className = 'alert-item';
            noAlertEl.innerHTML = '<span class="alert-item-text">✓ No alerts</span>';
            alertsList.appendChild(noAlertEl);
        }

    } catch (err) {
        console.error('Error updating data:', err);
    }
});

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});
