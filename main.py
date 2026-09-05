import argparse
import os
import time

import cv2
import yaml

from src.events import write_events_csv, write_summary_json
from src.pipeline import VisionPipeline
from src.video_io import VideoReader, VideoWriter

def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run(input_path: str, config: dict, debug: bool, max_frames: int = None):
    pipeline = VisionPipeline(config)

    out_dir = config["output"].get("out_dir", "outputs")
    os.makedirs(out_dir, exist_ok=True)

    reader = VideoReader(input_path)
    writer = None
    if config["output"].get("save_video", True):
        writer = VideoWriter(
            os.path.join(out_dir, "annotated_output.mp4"),
            fps=reader.fps,
            width=reader.width,
            height=reader.height,
        )

    start_time = time.time()

    for frame in reader:
        annotated = pipeline.process_frame(frame)

        if writer:
            writer.write(annotated)
        if debug:
            cv2.imshow("debug", cv2.resize(annotated, (960, 540)))
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        if max_frames and pipeline.frame_id >= max_frames:
            break

    pipeline.finalize()

    reader.release()
    if writer:
        writer.release()
    if debug:
        cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    processing_fps = pipeline.frame_id / elapsed if elapsed > 0 else 0.0
    counters = pipeline.counters

    if config["output"].get("save_csv", True):
        write_events_csv(counters.events, os.path.join(out_dir, "events.csv"))
    if config["output"].get("save_json", True):
        summary = counters.summary()
        summary["invariant_ok"] = counters.check_invariant()
        summary["processing_fps"] = processing_fps
        write_summary_json(summary, os.path.join(out_dir, "summary.json"))

    print("Processing complete.")
    print(f"Total baskets:      {counters.total_baskets}")
    print(f"Left:               {counters.left_baskets}")
    print(f"Straight:           {counters.straight_baskets}")
    print(f"Unclassified:       {counters.unclassified_baskets}")
    print(f"Processing FPS:     {processing_fps:.1f}")
    if not counters.check_invariant():
        print("WARNING: counting invariant failed (left+straight+unclassified != total)")

    return counters

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--max-frames", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    input_path = args.input or cfg["video"]["input"]
    run(input_path, cfg, debug=args.debug, max_frames=args.max_frames)
