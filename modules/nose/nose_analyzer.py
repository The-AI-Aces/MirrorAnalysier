import cv2
import numpy as np

class NoseAnalyzer:
    # Nose landmark indices
    NOSE_TIP      = 1
    NOSE_BRIDGE   = 6
    LEFT_NOSTRIL  = 129
    RIGHT_NOSTRIL = 358
    NOSE_BOTTOM   = 2

    def analyze(self, frame, points):
        results = {}

        # Get nose region
        nose_region = self._get_nose_region(frame, points)

        if nose_region is not None and nose_region.size > 0:
            results['redness']    = self._check_redness(nose_region)
            results['pore_size']  = self._check_pores(nose_region)
            results['blackheads'] = self._check_blackheads(nose_region)
        else:
            results['redness']    = 0.0
            results['pore_size']  = 'Normal'
            results['blackheads'] = False

        # Nose symmetry
        results['symmetry'] = self._check_symmetry(points)

        # Nose color change
        results['color_change'] = self._check_color_change(nose_region)

        return results

    def _get_nose_region(self, frame, points):
        try:
            nose_pts = [1, 2, 98, 327, 129, 358]
            pts = np.array([points[i] for i in nose_pts
                           if i in points])
            if len(pts) < 3:
                return None
            x, y, w, h = cv2.boundingRect(pts)
            pad = 10
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(frame.shape[1] - x, w + 2*pad)
            h = min(frame.shape[0] - y, h + 2*pad)
            return frame[y:y+h, x:x+w]
        except:
            return None

    def _check_redness(self, region):
        try:
            red   = float(np.mean(region[:,:,2]))
            green = float(np.mean(region[:,:,1]))
            redness = max(0, (red - green) / 255 * 100)
            return round(redness, 1)
        except:
            return 0.0

    def _check_pores(self, region):
        try:
            gray    = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            variance = np.var(gray)
            if variance > 1000:
                return 'Large'
            elif variance > 500:
                return 'Medium'
            else:
                return 'Small/Normal'
        except:
            return 'Normal'

    def _check_blackheads(self, region):
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            # Dark spots = potential blackheads
            dark_pixels = np.sum(gray < 60)
            total = gray.size
            return bool(dark_pixels / total > 0.05)
        except:
            return False

    def _check_symmetry(self, points):
        try:
            left  = points.get(self.LEFT_NOSTRIL,  None)
            right = points.get(self.RIGHT_NOSTRIL, None)
            tip   = points.get(self.NOSE_TIP,      None)
            if left and right and tip:
                center_x = (left[0] + right[0]) / 2
                offset   = abs(tip[0] - center_x)
                width    = abs(right[0] - left[0])
                symmetry = 100 - (offset/width*100) if width > 0 else 50
                return round(symmetry, 1)
            return 50.0
        except:
            return 50.0

    def _check_color_change(self, region):
        if region is None or region.size == 0:
            return 'Normal'
        try:
            avg = np.mean(region.reshape(-1, 3), axis=0)
            b, g, r = avg
            if r > g + 30:
                return 'Reddish'
            elif b > r + 20:
                return 'Bluish'
            else:
                return 'Normal'
        except:
            return 'Normal'
