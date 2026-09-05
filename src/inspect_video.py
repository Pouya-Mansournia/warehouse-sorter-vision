import argparse
import json
import os

import cv2

def inspect_video(input_path: str, out_dir: str):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps else 0

    os.makedirs(out_dir, exist_ok=True)

    fractions = [0.0, 0.25, 0.5, 0.75, 0.999]
    saved = []
    for frac in fractions:
        idx = int(frac * (frame_count - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        fname = os.path.join(out_dir, f"frame_{int(frac*100):03d}pct_idx{idx}.png")
        cv2.imwrite(fname, frame)
        saved.append({"fraction": frac, "frame_index": idx, "path": fname})

    cap.release()

    meta = {
        "input": input_path,
        "resolution": [width, height],
        "fps": fps,
        "frame_count": frame_count,
        "duration_sec": duration,
        "sample_frames": saved,
    }

    meta_path = os.path.join(out_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(json.dumps(meta, indent=2))
    return meta

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="outputs/debug/sample_frames")
    args = parser.parse_args()
    inspect_video(args.input, args.out)
