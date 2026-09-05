from src.counter import Counters
from src.detector import Detection
from src.tracker import Track

def make_track(track_id, route):
    det = Detection(bbox=(0, 0, 10, 10), centroid=(5, 5), confidence=1.0)
    track = Track(track_id, det, frame_id=0)
    track.route = route
    return track

def test_invariant_holds_after_mixed_routes():
    counters = Counters()
    t1 = make_track(1, "LEFT")
    t1.counted_total = True
    counters.record_total(t1)
    counters.record_route(t1, frame_id=5, avg_confidence=1.0)

    t2 = make_track(2, "STRAIGHT")
    t2.counted_total = True
    counters.record_total(t2)
    counters.record_route(t2, frame_id=6, avg_confidence=1.0)

    t3 = make_track(3, None)
    counters.finalize_unclassified(t3, frame_id=7, avg_confidence=1.0)

    assert counters.total_baskets == 3
    assert counters.left_baskets == 1
    assert counters.straight_baskets == 1
    assert counters.unclassified_baskets == 1
    assert counters.check_invariant()

def test_duplicate_route_event_not_double_counted():
    counters = Counters()
    t1 = make_track(1, "LEFT")
    t1.counted_total = True
    t1.route_counted = True
    counters.finalize_unclassified(t1, frame_id=10, avg_confidence=1.0)
    assert counters.total_baskets == 0
    assert counters.left_baskets == 0
