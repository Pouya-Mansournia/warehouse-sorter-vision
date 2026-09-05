from typing import Dict, List, Optional, Tuple

from .detector import Detection
from .geometry import euclidean_distance

class Track:
    def __init__(self, track_id: int, detection: Detection, frame_id: int):
        self.track_id = track_id
        self.bbox = detection.bbox
        self.centroid = detection.centroid
        self.trajectory: List[Tuple[int, float, float]] = [
            (frame_id, detection.centroid[0], detection.centroid[1])
        ]
        self.first_seen = frame_id
        self.last_seen = frame_id
        self.missing_frames = 0
        self.counted_total = False
        self.route: Optional[str] = None
        self.route_counted = False

    def update(self, detection: Detection, frame_id: int):
        self.bbox = detection.bbox
        self.centroid = detection.centroid
        self.trajectory.append((frame_id, detection.centroid[0], detection.centroid[1]))
        self.last_seen = frame_id
        self.missing_frames = 0

    def mark_missing(self):
        self.missing_frames += 1

class CentroidTracker:
    def __init__(self, max_missing_frames: int, max_assignment_distance: float):
        self.max_missing_frames = max_missing_frames
        self.max_assignment_distance = max_assignment_distance
        self.tracks: Dict[int, Track] = {}
        self._next_id = 1

    def update(self, detections: List[Detection], frame_id: int) -> Tuple[Dict[int, Track], List[Track]]:
        unmatched_detections = list(range(len(detections)))
        unmatched_tracks = list(self.tracks.keys())

        candidate_pairs = []
        for track_id in unmatched_tracks:
            track = self.tracks[track_id]
            for det_idx in unmatched_detections:
                dist = euclidean_distance(track.centroid, detections[det_idx].centroid)
                if dist <= self.max_assignment_distance:
                    candidate_pairs.append((dist, track_id, det_idx))
        candidate_pairs.sort(key=lambda p: p[0])

        assigned_tracks = set()
        assigned_detections = set()
        for dist, track_id, det_idx in candidate_pairs:
            if track_id in assigned_tracks or det_idx in assigned_detections:
                continue
            self.tracks[track_id].update(detections[det_idx], frame_id)
            assigned_tracks.add(track_id)
            assigned_detections.add(det_idx)

        for track_id in unmatched_tracks:
            if track_id in assigned_tracks:
                continue
            self.tracks[track_id].mark_missing()

        stale_ids = [t for t in self.tracks if self.tracks[t].missing_frames > self.max_missing_frames]
        dropped_tracks = [self.tracks.pop(t) for t in stale_ids]

        for det_idx in unmatched_detections:
            if det_idx in assigned_detections:
                continue
            track = Track(self._next_id, detections[det_idx], frame_id)
            self.tracks[self._next_id] = track
            self._next_id += 1

        return self.tracks, dropped_tracks
