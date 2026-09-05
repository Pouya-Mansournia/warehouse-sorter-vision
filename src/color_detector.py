from typing import List, Optional, Tuple

import cv2
import numpy as np

from .detector import Detection

class ColorDetector:
    def __init__(
        self,
        hsv_lower: Tuple[int, int, int],
        hsv_upper: Tuple[int, int, int],
        min_area: float,
        max_area: float,
        min_aspect_ratio: float,
        max_aspect_ratio: float,
        roi_polygon: Optional[List[Tuple[float, float]]] = None,
    ):
        self.lower = np.array(hsv_lower, dtype=np.uint8)
        self.upper = np.array(hsv_upper, dtype=np.uint8)
        self.min_area = min_area
        self.max_area = max_area
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.roi_polygon = roi_polygon
        self._open_kernel = np.ones((5, 5), np.uint8)
        self._close_kernel = np.ones((15, 15), np.uint8)
        self.last_mask = None

    def _roi_mask(self, shape) -> np.ndarray:
        mask = np.zeros(shape[:2], dtype=np.uint8)
        if self.roi_polygon:
            pts = np.array([self.roi_polygon], dtype=np.int32)
            cv2.fillPoly(mask, pts, 255)
        else:
            mask[:] = 255
        return mask

    def compute_mask(self, frame_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.bitwise_and(mask, self._roi_mask(frame_bgr.shape))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._open_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._close_kernel)
        return mask

    def detect(self, frame_bgr: np.ndarray) -> List[Detection]:
        mask = self.compute_mask(frame_bgr)
        self.last_mask = mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections: List[Detection] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area or area > self.max_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if h == 0:
                continue
            aspect_ratio = w / float(h)
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue

            bbox = (float(x), float(y), float(x + w), float(y + h))
            centroid = (x + w / 2.0, y + h / 2.0)

            solidity = area / (w * h)
            confidence = float(min(1.0, solidity))
            detections.append(Detection(bbox=bbox, centroid=centroid, confidence=confidence))

        return detections
