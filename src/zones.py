from dataclasses import dataclass
from typing import Dict, List, Tuple

from .geometry import Point, point_in_polygon

def inflate_polygon(points: List[Point], percent: float) -> List[Point]:
    if not percent:
        return points
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    scale = 1.0 + percent / 100.0
    return [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in points]

@dataclass
class Zones:
    roi: List[Point]
    entry: List[Point]
    left_exit: List[Point]
    straight_exit: List[Point]

    @classmethod
    def from_config(cls, zones_cfg: Dict) -> "Zones":
        tolerance_percent = zones_cfg.get("tolerance_percent", 0)
        return cls(
            roi=zones_cfg["roi"],
            entry=inflate_polygon(zones_cfg["entry"], tolerance_percent),
            left_exit=inflate_polygon(zones_cfg["left_exit"], tolerance_percent),
            straight_exit=inflate_polygon(zones_cfg["straight_exit"], tolerance_percent),
        )

    def in_roi(self, point: Point) -> bool:
        return point_in_polygon(point, self.roi)

    def in_entry(self, point: Point) -> bool:
        return point_in_polygon(point, self.entry)

    def in_left_exit(self, point: Point) -> bool:
        return point_in_polygon(point, self.left_exit)

    def in_straight_exit(self, point: Point) -> bool:
        return point_in_polygon(point, self.straight_exit)
