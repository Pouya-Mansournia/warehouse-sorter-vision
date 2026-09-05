import cv2

from src import sound
from src.color_detector import ColorDetector
from src.counter import Counters
from src.route_classifier import RouteClassifier
from src.tracker import CentroidTracker
from src.visualization import draw_counters, draw_track, draw_zones
from src.zones import Zones

class VisionPipeline:
    def __init__(self, config: dict):
        self.enable_sound = config.get("output", {}).get("enable_sound", True)
        self.show_zones = config.get("output", {}).get("show_zones", False)
        self.zones = Zones.from_config(config["zones"])
        self.detector = ColorDetector(
            hsv_lower=tuple(config["hsv"]["lower"]),
            hsv_upper=tuple(config["hsv"]["upper"]),
            min_area=config["filters"]["min_area"],
            max_area=config["filters"]["max_area"],
            min_aspect_ratio=config["filters"]["min_aspect_ratio"],
            max_aspect_ratio=config["filters"]["max_aspect_ratio"],
            roi_polygon=self.zones.roi,
        )
        self.tracker = CentroidTracker(
            max_missing_frames=config["tracking"]["max_missing_frames"],
            max_assignment_distance=config["tracking"]["max_assignment_distance"],
        )
        self.route_classifier = RouteClassifier(self.zones)
        self.counters = Counters()
        self.frame_id = 0

    def process_frame(self, frame):
        detections = self.detector.detect(frame)
        tracks, dropped_tracks = self.tracker.update(detections, self.frame_id)

        for track in tracks.values():
            events = self.route_classifier.update(track)
            if "TOTAL_COUNTED" in events:
                self.counters.record_total(track)
            if "ROUTE_COUNTED" in events:
                self.counters.record_route(track, self.frame_id, avg_confidence=1.0)
                if self.enable_sound:
                    sound.play_for_route(track.route)

        for track in dropped_tracks:
            self._finalize_track(track, self.frame_id)

        annotated = frame.copy()
        if self.show_zones:
            draw_zones(annotated, self.zones)
        for track in tracks.values():
            draw_track(annotated, track)
        draw_counters(annotated, self.counters)

        self.frame_id += 1
        return annotated

    def _finalize_track(self, track, frame_id):
        if track.route_counted:
            return
        route = self.counters.finalize_unclassified(track, frame_id, avg_confidence=1.0)
        if self.enable_sound and route in ("LEFT", "STRAIGHT"):
            sound.play_for_route(route)

    def get_mask_frame(self):
        mask = self.detector.last_mask
        if mask is None:
            return None
        return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    def finalize(self):
        for track in self.tracker.tracks.values():
            self._finalize_track(track, self.frame_id)
