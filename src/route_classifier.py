from typing import List

from .tracker import Track
from .zones import Zones

STATE_DETECTED = "DETECTED"
STATE_ROUTING = "ROUTING"
STATE_COMPLETED = "COMPLETED"

class RouteClassifier:
    def __init__(self, zones: Zones):
        self.zones = zones
        self.states = {}

    def state_of(self, track_id: int) -> str:
        return self.states.get(track_id, STATE_DETECTED)

    def update(self, track: Track) -> List[str]:
        events: List[str] = []
        centroid = track.centroid

        if not track.counted_total and self.zones.in_entry(centroid):
            track.counted_total = True
            events.append("TOTAL_COUNTED")

        if track.route is None:
            if self.zones.in_left_exit(centroid):
                track.route = "LEFT"
                self.states[track.track_id] = STATE_ROUTING
            elif self.zones.in_straight_exit(centroid):
                track.route = "STRAIGHT"
                self.states[track.track_id] = STATE_ROUTING

        if track.route is not None and track.counted_total and not track.route_counted:
            track.route_counted = True
            self.states[track.track_id] = STATE_COMPLETED
            events.append("ROUTE_COUNTED")

        return events
