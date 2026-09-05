from src.geometry import point_in_polygon
from src.zones import Zones, inflate_polygon

def test_inflate_polygon_zero_percent_is_unchanged():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert inflate_polygon(square, 0) == square

def test_inflate_polygon_grows_outward_from_centroid():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    inflated = inflate_polygon(square, 10)

    assert not point_in_polygon((10.3, 5), square)
    assert point_in_polygon((10.3, 5), inflated)

def test_zones_from_config_applies_tolerance_to_exit_zones_but_not_roi():
    cfg = {
        "tolerance_percent": 50,
        "roi": [(0, 0), (10, 0), (10, 10), (0, 10)],
        "entry": [(0, 0), (10, 0), (10, 10), (0, 10)],
        "left_exit": [(0, 0), (10, 0), (10, 10), (0, 10)],
        "straight_exit": [(0, 0), (10, 0), (10, 10), (0, 10)],
    }
    zones = Zones.from_config(cfg)
    assert zones.roi == cfg["roi"]
    assert not zones.in_roi((10.3, 5))
    assert zones.in_entry((10.3, 5))
    assert zones.in_left_exit((10.3, 5))
    assert zones.in_straight_exit((10.3, 5))
