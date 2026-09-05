from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .tracker import Track

@dataclass
class BasketEvent:
    basket_id: int
    first_seen_frame: int
    entry_frame: int
    decision_frame: int
    exit_frame: int
    route: str
    track_duration_frames: int
    confidence: float

@dataclass
class Counters:
    total_baskets: int = 0
    left_baskets: int = 0
    straight_baskets: int = 0
    unclassified_baskets: int = 0
    events: List[BasketEvent] = field(default_factory=list)

    def record_total(self, track: Track):
        self.total_baskets += 1

    def record_route(self, track: Track, frame_id: int, avg_confidence: float):
        if track.route == "LEFT":
            self.left_baskets += 1
        elif track.route == "STRAIGHT":
            self.straight_baskets += 1
        else:
            self.unclassified_baskets += 1

        self.events.append(
            BasketEvent(
                basket_id=track.track_id,
                first_seen_frame=track.first_seen,
                entry_frame=track.first_seen,
                decision_frame=track.trajectory[0][0],
                exit_frame=frame_id,
                route=track.route or "UNCLASSIFIED",
                track_duration_frames=track.last_seen - track.first_seen,
                confidence=avg_confidence,
            )
        )

    def finalize_unclassified(self, track: Track, frame_id: int, avg_confidence: float) -> Optional[str]:
        if track.route_counted:
            return None
        route = track.route or "UNCLASSIFIED"
        if route == "LEFT":
            self.left_baskets += 1
        elif route == "STRAIGHT":
            self.straight_baskets += 1
        else:
            self.unclassified_baskets += 1
        if not track.counted_total:
            self.total_baskets += 1
        self.events.append(
            BasketEvent(
                basket_id=track.track_id,
                first_seen_frame=track.first_seen,
                entry_frame=track.first_seen,
                decision_frame=track.trajectory[0][0],
                exit_frame=frame_id,
                route=route,
                track_duration_frames=track.last_seen - track.first_seen,
                confidence=avg_confidence,
            )
        )
        return route

    def check_invariant(self) -> bool:
        return (
            self.left_baskets + self.straight_baskets + self.unclassified_baskets
            == self.total_baskets
        )

    def summary(self) -> Dict:
        return {
            "total_baskets": self.total_baskets,
            "left_baskets": self.left_baskets,
            "straight_baskets": self.straight_baskets,
            "unclassified_baskets": self.unclassified_baskets,
        }
