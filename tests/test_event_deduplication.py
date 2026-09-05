from src.detector import Detection
from src.route_classifier import RouteClassifier
from src.tracker import CentroidTracker, Track
from src.zones import Zones

ZONES = Zones(
    roi=[(0, 0), (100, 0), (100, 100), (0, 100)],
    entry=[(0, 0), (40, 0), (40, 100), (0, 100)],
    left_exit=[(60, 0), (100, 0), (100, 50), (60, 50)],
    straight_exit=[(60, 50), (100, 50), (100, 100), (60, 100)],
)

def det(x, y):
    return Detection(bbox=(x - 5, y - 5, x + 5, y + 5), centroid=(x, y), confidence=1.0)

def test_repeated_zone_updates_only_count_once():
    rc = RouteClassifier(ZONES)
    track = Track(1, det(20, 50), frame_id=0)
    total_events = 0
    route_events = 0
    for frame_id, (x, y) in enumerate([(20, 50), (30, 50), (70, 25), (70, 25), (70, 25)]):
        track.update(det(x, y), frame_id)
        events = rc.update(track)
        total_events += events.count("TOTAL_COUNTED")
        route_events += events.count("ROUTE_COUNTED")
    assert total_events == 1
    assert route_events == 1

def test_brief_occlusion_keeps_same_track_id():
    tracker = CentroidTracker(max_missing_frames=5, max_assignment_distance=50)
    tracks, dropped = tracker.update([det(20, 50)], frame_id=0)
    track_id = next(iter(tracks))

    for frame_id in range(1, 4):
        tracks, dropped = tracker.update([], frame_id=frame_id)

    tracks, dropped = tracker.update([det(25, 55)], frame_id=4)
    assert list(tracks.keys()) == [track_id]
    assert dropped == []

def test_track_dropped_after_too_many_missing_frames():
    tracker = CentroidTracker(max_missing_frames=2, max_assignment_distance=50)
    tracker.update([det(20, 50)], frame_id=0)
    all_dropped = []
    for frame_id in range(1, 5):
        tracks, dropped = tracker.update([], frame_id=frame_id)
        all_dropped.extend(dropped)
    assert tracks == {}
    assert len(all_dropped) == 1
