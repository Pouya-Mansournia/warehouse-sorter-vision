from src.geometry import centroid_of_bbox, euclidean_distance, point_in_polygon

SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]

def test_point_inside_polygon():
    assert point_in_polygon((5, 5), SQUARE)

def test_point_outside_polygon():
    assert not point_in_polygon((15, 5), SQUARE)

def test_point_on_edge_counts_as_inside():
    assert point_in_polygon((0, 5), SQUARE)

def test_centroid_of_bbox():
    assert centroid_of_bbox((0, 0, 10, 20)) == (5.0, 10.0)

def test_euclidean_distance():
    assert euclidean_distance((0, 0), (3, 4)) == 5.0
