from typing import Dict

import cv2
import numpy as np

from .counter import Counters
from .tracker import Track
from .zones import Zones

ROUTE_COLOR = {
    "LEFT": (0, 165, 255),
    "STRAIGHT": (255, 200, 0),
    None: (200, 200, 200),
}

def draw_polygon(frame, polygon, color, label=None):
    pts = np.array([polygon], dtype=np.int32)
    cv2.polylines(frame, pts, isClosed=True, color=color, thickness=2)
    if label:
        x, y = polygon[0]
        cv2.putText(frame, label, (int(x) + 5, int(y) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_zones(frame, zones: Zones):
    draw_polygon(frame, zones.roi, (255, 255, 255), "ROI")
    draw_polygon(frame, zones.entry, (0, 255, 0), "ENTRY")
    draw_polygon(frame, zones.left_exit, (0, 165, 255), "LEFT_EXIT")
    draw_polygon(frame, zones.straight_exit, (255, 200, 0), "STRAIGHT_EXIT")

def draw_track(frame, track: Track):
    color = ROUTE_COLOR.get(track.route, ROUTE_COLOR[None])
    x1, y1, x2, y2 = [int(v) for v in track.bbox]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cx, cy = [int(v) for v in track.centroid]
    cv2.circle(frame, (cx, cy), 4, color, -1)
    label = f"ID{track.track_id} {track.route or ''}"
    cv2.putText(frame, label, (x1, max(0, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    tail = track.trajectory[-30:]
    for i in range(1, len(tail)):
        p1 = (int(tail[i - 1][1]), int(tail[i - 1][2]))
        p2 = (int(tail[i][1]), int(tail[i][2]))
        cv2.line(frame, p1, p2, color, 2)

def draw_counters(frame, counters: Counters):
    lines = [
        f"Total: {counters.total_baskets}",
        f"Left: {counters.left_baskets}",
        f"Straight: {counters.straight_baskets}",
        f"Unclassified: {counters.unclassified_baskets}",
    ]
    for i, text in enumerate(lines):
        cv2.putText(
            frame, text, (20, 40 + i * 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
        )
