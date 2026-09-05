import csv
import json
import os
from typing import Dict, List

from .counter import BasketEvent

def write_events_csv(events: List[BasketEvent], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = [
        "basket_id",
        "first_seen_frame",
        "entry_frame",
        "decision_frame",
        "exit_frame",
        "route",
        "track_duration_frames",
        "confidence",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for e in events:
            writer.writerow(vars(e))

def write_summary_json(summary: Dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
