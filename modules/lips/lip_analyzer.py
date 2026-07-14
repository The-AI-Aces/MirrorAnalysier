import cv2
import numpy as np

class LipAnalyzer:
    # Lip landmark indices
    OUTER_LIPS = [61, 84, 17, 314, 291, 308, 415, 310, 
                  311, 312, 13, 82, 81, 80, 191, 78]
    INNER_LIPS = [78, 191, 80, 81, 82, 13, 312, 311, 
                  310, 415, 308, 324, 318, 402, 317, 14,
                  87, 178, 88, 95]
    TOP_LIP    = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]
    BOTTOM_LIP = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]

    def analyze(self, frame, points):
        results = {}

        # Get lip region
        lip_region = self._get_lip_region(frame, points)

        if lip_region is not None and lip_region.size > 0:
            # Lip color analysis
            results['lip_color'] = self._get_lip_color(lip_region)
            results['pallor']    = self._check_pallor(lip_region)
            results['cyanosis']  = self._check_cyanosis(lip_region)
            results['dryness']   = self._check_dryness(lip_region)
        else:
            results['lip_color'] = 'Unknown'
            results['pallor']    = False
            results['cyanosis']  = False
            results['dryness']   = False

        # Lip symmetry
        results['symmetry'] = self._check_symmetry(points)

        return results

    def _get_lip_region(self, frame, points):
        try:
            pts = np.array([points[i] for i in self.OUTER_LIPS
                           if i in points])
            if len(pts) < 3:
                return None
            x, y, w, h = cv2.boundingRect(pts)
            pad = 5
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(frame.shape[1] - x, w + 2*pad)
            h = min(frame.shape[0] - y, h + 2*pad)
            return frame[y:y+h, x:x+w]
        except:
            return None

    def _get_lip_color(self, region):
        try:
            avg = np.mean(region.reshape(-1, 3), axis=0)
            b, g, r = avg
            if r > 150 and g < 100:
                return 'Red/Healthy'
            elif r < 100 and g < 100 and b < 100:
                return 'Dark/Concerning'
            elif b > r and b > g:
                return 'Bluish/Cyanosis'
            elif r < 130 and g < 110:
                return 'Pale'
            else:
                return 'Normal'
        except:
            return 'Unknown'

    def _check_pallor(self, region):
        try:
            avg = np.mean(region)
            return bool(avg > 180)
        except:
            return False

    def _check_cyanosis(self, region):
        try:
            avg = np.mean(region.reshape(-1, 3), axis=0)
            b, g, r = avg
            return bool(b > r + 20)
        except:
            return False

    def _check_dryness(self, region):
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            # High texture variance = dry/cracked lips
            variance = np.var(gray)
            return bool(variance > 800)
        except:
            return False

    def _check_symmetry(self, points):
        try:
            left_corner  = points.get(61,  None)
            right_corner = points.get(291, None)
            top_lip      = points.get(0,   None)
            if left_corner and right_corner and top_lip:
                center_x = (left_corner[0] + right_corner[0]) / 2
                offset   = abs(top_lip[0] - center_x)
                width    = abs(right_corner[0] - left_corner[0])
                symmetry = 100 - (offset / width * 100) if width > 0 else 50
                return round(symmetry, 1)
            return 50.0
        except:
            return 50.0
