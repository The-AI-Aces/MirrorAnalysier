import cv2
import numpy as np

class EyeAnalyzer:
    # Landmark indices for eyes
    LEFT_EYE  = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]
    LEFT_IRIS  = [468, 469, 470, 471, 472]
    RIGHT_IRIS = [473, 474, 475, 476, 477]

    def analyze(self, frame, points):
        results = {}

        # Eye openness (detects fatigue)
        left_ear  = self._eye_aspect_ratio(points, self.LEFT_EYE)
        right_ear = self._eye_aspect_ratio(points, self.RIGHT_EYE)
        avg_ear   = (left_ear + right_ear) / 2

        results['left_ear']   = round(left_ear, 3)
        results['right_ear']  = round(right_ear, 3)
        results['fatigue']    = avg_ear < 0.2
        results['fatigue_score'] = round((1 - avg_ear) * 100, 1)

        # Eye redness (from color)
        left_region  = self._get_eye_region(frame, points, self.LEFT_EYE)
        right_region = self._get_eye_region(frame, points, self.RIGHT_EYE)

        results['left_redness']  = self._check_redness(left_region)
        results['right_redness'] = self._check_redness(right_region)
        results['redness']       = (results['left_redness'] +
                                    results['right_redness']) / 2

        # Dark circles
        results['dark_circles'] = self._check_dark_circles(
            frame, points
        )

        return results

    def _eye_aspect_ratio(self, points, eye_indices):
        try:
            p = [points[i] for i in eye_indices]
            # Vertical distances
            v1 = np.linalg.norm(np.array(p[1]) - np.array(p[5]))
            v2 = np.linalg.norm(np.array(p[2]) - np.array(p[4]))
            # Horizontal distance
            h  = np.linalg.norm(np.array(p[0]) - np.array(p[3]))
            return (v1 + v2) / (2.0 * h) if h > 0 else 0
        except:
            return 0.3

    def _get_eye_region(self, frame, points, eye_indices):
        try:
            pts = np.array([points[i] for i in eye_indices])
            x, y, w, h = cv2.boundingRect(pts)
            # Add padding
            pad = 5
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(frame.shape[1] - x, w + 2*pad)
            h = min(frame.shape[0] - y, h + 2*pad)
            return frame[y:y+h, x:x+w]
        except:
            return None

    def _check_redness(self, region):
        if region is None or region.size == 0:
            return 0.0
        try:
            # Red channel vs green channel ratio
            red   = float(np.mean(region[:,:,2]))
            green = float(np.mean(region[:,:,1]))
            redness = max(0, (red - green) / 255 * 100)
            return round(redness, 1)
        except:
            return 0.0

    def _check_dark_circles(self, frame, points):
        try:
            # Under eye region
            left_under  = points.get(110, None)
            right_under = points.get(339, None)
            if left_under and right_under:
                region = frame[
                    left_under[1]:left_under[1]+20,
                    left_under[0]:right_under[0]
                ]
                if region.size > 0:
                    brightness = np.mean(region)
                    return brightness < 80
            return False
        except:
            return False
