import argparse
import sys

import cv2
import numpy as np
import yaml

ZONE_ORDER = ["roi", "entry", "left_exit", "straight_exit"]
ZONE_COLOR = {
    "roi": (255, 255, 255),
    "entry": (0, 255, 0),
    "left_exit": (0, 165, 255),
    "straight_exit": (255, 200, 0),
}
ZONE_HINT = {
    "roi": "Region of interest: the area detection should look at (exclude unrelated conveyors/shelving).",
    "entry": "ENTRY: where a basket is first visible on the incoming lane, before the sorter.",
    "left_exit": "LEFT_EXIT: the downstream lane that physically routes LEFT.",
    "straight_exit": "STRAIGHT_EXIT: the downstream lane that physically continues STRAIGHT.",
}
FRAME_STEP = 30

class ZoneEditor:
    def __init__(self, frame, initial_zones=None):
        self.base_frame = frame
        self.zones = {name: [] for name in ZONE_ORDER}
        if initial_zones:
            for name in ZONE_ORDER:
                points = initial_zones.get(name)
                if points:
                    self.zones[name] = [(int(x), int(y)) for x, y in points]
        self.zone_index = 0

    @property
    def current_zone(self):
        return ZONE_ORDER[self.zone_index]

    def set_frame(self, frame):
        self.base_frame = frame

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.zones[self.current_zone].append((x, y))

    def next_zone(self):
        if len(self.zones[self.current_zone]) < 3:
            print(f"'{self.current_zone}' needs at least 3 points before moving on.")
            return
        if self.zone_index < len(ZONE_ORDER) - 1:
            self.zone_index += 1
        else:
            print("All zones defined. Press 's' to save.")

    def undo_point(self):
        if self.zones[self.current_zone]:
            self.zones[self.current_zone].pop()

    def restart_zone(self):
        self.zones[self.current_zone] = []

    def render(self):
        frame = self.base_frame.copy()
        for name in ZONE_ORDER:
            points = self.zones[name]
            if len(points) >= 2:
                pts = np.array([points], dtype=np.int32)
                cv2.polylines(frame, pts, isClosed=(len(points) >= 3), color=ZONE_COLOR[name], thickness=2)
            for px, py in points:
                cv2.circle(frame, (px, py), 4, ZONE_COLOR[name], -1)

        overlay_lines = [
            f"Zone: {self.current_zone}  ({len(self.zones[self.current_zone])} points)",
            ZONE_HINT[self.current_zone],
            "[click] point  [n] next  [z] undo  [r] restart  [f/b] step frame  [s] save  [q] quit",
        ]
        for i, text in enumerate(overlay_lines):
            cv2.putText(frame, text, (10, 25 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 4)
            cv2.putText(frame, text, (10, 25 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        return frame

    def all_zones_ready(self):
        return all(len(self.zones[name]) >= 3 for name in ZONE_ORDER)

def open_calibrator(input_source, config_path: str, frame_index: int = 0, window_name: str = "Zone Editor") -> bool:
    cap = cv2.VideoCapture(input_source)
    if not cap.isOpened():
        print(f"Could not open video source: {input_source}")
        return False

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    seekable = frame_count > 1
    if seekable and frame_index:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    ok, frame = cap.read()
    if not ok:
        print("Could not read a frame from the video source.")
        cap.release()
        return False

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    initial_zones = config.get("zones", {})

    editor = ZoneEditor(frame, initial_zones=initial_zones)
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, editor.on_mouse)

    saved = False
    current_pos = frame_index if seekable else 0
    while True:
        cv2.imshow(window_name, editor.render())
        key = cv2.waitKey(20) & 0xFF
        if key == ord("n"):
            editor.next_zone()
        elif key == ord("z"):
            editor.undo_point()
        elif key == ord("r"):
            editor.restart_zone()
        elif key in (ord("f"), ord("b")) and seekable:
            current_pos += FRAME_STEP if key == ord("f") else -FRAME_STEP
            current_pos = max(0, min(current_pos, frame_count - 1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
            ok, frame = cap.read()
            if ok:
                editor.set_frame(frame)
        elif key == ord("q"):
            print("Quit without saving.")
            break
        elif key == ord("s"):
            if not editor.all_zones_ready():
                print("Every zone needs at least 3 points before saving.")
                continue
            for name in ZONE_ORDER:
                config.setdefault("zones", {})[name] = [
                    [int(x), int(y)] for x, y in editor.zones[name]
                ]
            with open(config_path, "w") as f:
                yaml.safe_dump(config, f, sort_keys=False)
            print(f"Saved zones to {config_path}")
            saved = True
            break

    cap.release()
    cv2.destroyAllWindows()
    return saved

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--frame", type=int, default=0, help="Frame index to calibrate against")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)
    input_path = args.input or cfg["video"]["input"]
    ok = open_calibrator(input_path, args.config, args.frame)
    sys.exit(0 if ok else 1)
