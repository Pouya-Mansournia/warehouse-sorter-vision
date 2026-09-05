from src.detector import Detection
from src.route_classifier import RouteClassifier
from src.tracker import Track
from src.zones import Zones

ZONES = Zones(
    roi=[(0, 0), (100, 0), (100, 100), (0, 100)],
    entry=[(0, 0), (40, 0), (40, 100), (0, 100)],
    left_exit=[(60, 0), (100, 0), (100, 50), (60, 50)],
    straight_exit=[(60, 50), (100, 50), (100, 100), (60, 100)],
)

def make_track(track_id, x, y):
    det = Detection(bbox=(x - 1, y - 1, x + 1, y + 1), centroid=(x, y), confidence=1.0)
    return Track(track_id, det, frame_id=0)

def move(track, x, y, frame_id):
    det = Detection(bbox=(x - 1, y - 1, x + 1, y + 1), centroid=(x, y), confidence=1.0)
    track.update(det, frame_id)

def test_trajectory_a_goes_left():
    rc = RouteClassifier(ZONES)
    track = make_track(1, 20, 50)
    rc.update(track)
    move(track, 80, 25, 1)
    rc.update(track)
    assert track.route == "LEFT"
    assert track.counted_total is True
    assert track.route_counted is True

def test_trajectory_b_goes_straight():
    rc = RouteClassifier(ZONES)
    track = make_track(2, 20, 50)
    rc.update(track)
    move(track, 80, 75, 1)
    rc.update(track)
    assert track.route == "STRAIGHT"
    assert track.route_counted is True

def test_trajectory_c_never_reaches_exit_stays_unclassified():
    rc = RouteClassifier(ZONES)
    track = make_track(3, 20, 50)
    rc.update(track)
    assert track.counted_total is True
    assert track.route is None
    assert track.route_counted is False

def test_route_assigned_at_most_once():
    rc = RouteClassifier(ZONES)
    track = make_track(4, 20, 50)
    rc.update(track)
    move(track, 80, 25, 1)
    rc.update(track)
    move(track, 80, 75, 2)
    rc.update(track)
    assert track.route == "LEFT"
