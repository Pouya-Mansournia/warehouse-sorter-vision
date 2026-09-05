from typing import Sequence, Tuple

import cv2
import numpy as np

Point = Tuple[float, float]

def point_in_polygon(point: Point, polygon: Sequence[Point]) -> bool:
    poly = np.array(polygon, dtype=np.float32)
    result = cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False)
    return result >= 0

def centroid_of_bbox(bbox: Tuple[float, float, float, float]) -> Point:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

def euclidean_distance(a: Point, b: Point) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))
