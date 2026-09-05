import argparse
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import yaml
from PIL import Image, ImageTk

from src.events import write_events_csv, write_summary_json
from src.pipeline import VisionPipeline
from tools.zone_editor import open_calibrator

VIDEO_DISPLAY_SIZE = (860, 484)

class SorterApp:
    def __init__(self, root: tk.Tk, config_path: str, camera_index: int):
        self.root = root
        self.config_path = config_path
        self.camera_index = camera_index
        self.root.title("Basket Sorter Vision")

        self.running = False
        self.worker_thread = None
        self.cap = None
        self.pipeline = None
        self.source_is_file = True
        self.run_id = 0
        self._ui_render_pending = False

        self._build_layout()

    def _build_layout(self):
        top_bar = ttk.Frame(self.root, padding=8)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        self.path_var = tk.StringVar()
        ttk.Entry(top_bar, textvariable=self.path_var, width=60).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(top_bar, text="Browse...", command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="RUN", command=self._run_file).pack(side=tk.LEFT, padx=8)
        ttk.Button(top_bar, text="LIVE", command=self._run_live).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="STOP", command=self._stop).pack(side=tk.LEFT, padx=8)
        ttk.Button(top_bar, text="Calibrate Zones", command=self._calibrate).pack(
            side=tk.LEFT, padx=8
        )

        self.show_zones_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top_bar, text="Show Zones", variable=self.show_zones_var, command=self._on_toggle_zones
        ).pack(side=tk.LEFT, padx=8)

        self.show_mask_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top_bar, text="Show Color Mask", variable=self.show_mask_var
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(top_bar, textvariable=self.status_var).pack(side=tk.RIGHT)

        body = ttk.Frame(self.root, padding=8)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT)
        self.video_label = ttk.Label(left)
        self.video_label.pack()

        right = ttk.Frame(body, padding=(20, 0))
        right.pack(side=tk.LEFT, fill=tk.Y)

        self.total_var = tk.StringVar(value="0")
        self.left_var = tk.StringVar(value="0")
        self.straight_var = tk.StringVar(value="0")
        self.unclassified_var = tk.StringVar(value="0")

        self._counter_row(right, "Total", self.total_var, "#222222")
        self._counter_row(right, "Left", self.left_var, "#e07b00")
        self._counter_row(right, "Straight", self.straight_var, "#0078d4")
        self._counter_row(right, "Unclassified", self.unclassified_var, "#888888")

    def _counter_row(self, parent, label, var, color):
        frame = ttk.Frame(parent, padding=(0, 12))
        frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(frame, text=label, font=("Segoe UI", 14)).pack(side=tk.TOP, anchor=tk.W)
        tk.Label(frame, textvariable=var, font=("Segoe UI", 36, "bold"), fg=color).pack(
            side=tk.TOP, anchor=tk.W
        )

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select input video",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")],
        )
        if path:
            self.path_var.set(path)

    def _run_file(self):
        path = self.path_var.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Basket Sorter Vision", "Please select a valid video file first.")
            return
        self._start(source=path, source_is_file=True)

    def _run_live(self):
        self._ask_camera_source(on_choice=lambda index: self._start(source=index, source_is_file=False))

    def _ask_camera_source(self, on_choice):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Camera")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Label(
            dialog, text="Which camera should be used?", padding=(16, 16, 16, 8)
        ).pack()

        button_row = ttk.Frame(dialog, padding=(16, 0, 16, 16))
        button_row.pack()

        def choose(index):
            dialog.destroy()
            on_choice(index)

        ttk.Button(
            button_row, text="Built-in Webcam", command=lambda: choose(0)
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            button_row, text="USB Camera", command=lambda: choose(1)
        ).pack(side=tk.LEFT, padx=4)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _calibrate(self):
        self._stop()
        path = self.path_var.get().strip()
        if path and os.path.isfile(path):
            self._run_calibration(path)
        else:
            self._ask_camera_source(on_choice=self._run_calibration)

    def _run_calibration(self, source):

        self.status_var.set("Calibrating zones (see the Zone Editor window)...")
        self.root.update_idletasks()
        saved = open_calibrator(source, self.config_path)
        if saved:
            self.status_var.set("Zones updated")
            messagebox.showinfo(
                "Basket Sorter Vision",
                "Zones saved to config.yaml. Press RUN or LIVE again to use them.",
            )
        else:
            self.status_var.set("Idle")

    def _on_toggle_zones(self):
        if self.pipeline is not None:
            self.pipeline.show_zones = self.show_zones_var.get()

    def _start(self, source, source_is_file: bool):
        self._stop()

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        self.pipeline = VisionPipeline(config)
        self.pipeline.show_zones = self.show_zones_var.get()
        self.source_is_file = source_is_file
        self._config = config

        self.run_id += 1
        run_id = self.run_id
        self._ui_render_pending = False
        self.running = True
        self.status_var.set(f"Running ({'file' if source_is_file else 'live camera'})...")
        self.worker_thread = threading.Thread(target=self._loop, args=(source, run_id), daemon=True)
        self.worker_thread.start()

    def _stop(self):
        if not self.running:
            return
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        self.status_var.set("Stopped")

    def _loop(self, source, run_id):
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            self.root.after(0, self._on_open_failed, source, run_id)
            return

        source_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = 1.0 / source_fps if source_fps and source_fps > 0 else None
        is_file_source = isinstance(source, str)

        pipeline = self.pipeline
        next_frame_time = time.time()
        while self.running and run_id == self.run_id:
            ok, frame = cap.read()
            if not ok:
                break
            annotated = pipeline.process_frame(frame)

            if not self._ui_render_pending:
                self._ui_render_pending = True
                self.root.after(0, self._update_ui, annotated, run_id)

            if is_file_source and frame_interval:
                next_frame_time += frame_interval
                delay = next_frame_time - time.time()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_frame_time = time.time()

        cap.release()
        pipeline.finalize()
        self.root.after(0, self._on_finished, pipeline, run_id)

    def _on_open_failed(self, source, run_id):
        if run_id != self.run_id:
            return
        self.running = False
        self.status_var.set("Idle")
        messagebox.showerror(
            "Basket Sorter Vision", f"Could not open video source: {source}"
        )

    def _update_ui(self, annotated_frame, run_id):
        self._ui_render_pending = False
        if run_id != self.run_id:
            return

        display_frame = annotated_frame
        if self.show_mask_var.get():
            mask_frame = self.pipeline.get_mask_frame()
            if mask_frame is not None:
                display_frame = mask_frame

        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb).resize(VIDEO_DISPLAY_SIZE)
        photo = ImageTk.PhotoImage(image)
        self.video_label.configure(image=photo)
        self.video_label.image = photo

        counters = self.pipeline.counters
        self.total_var.set(str(counters.total_baskets))
        self.left_var.set(str(counters.left_baskets))
        self.straight_var.set(str(counters.straight_baskets))
        self.unclassified_var.set(str(counters.unclassified_baskets))

    def _on_finished(self, pipeline, run_id):
        if run_id != self.run_id:
            return
        self.running = False
        self.status_var.set("Finished - outputs saved")
        self._save_outputs(pipeline)

    def _save_outputs(self, pipeline):
        out_dir = self._config["output"].get("out_dir", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        counters = pipeline.counters
        write_events_csv(counters.events, os.path.join(out_dir, "events.csv"))
        summary = counters.summary()
        summary["invariant_ok"] = counters.check_invariant()
        write_summary_json(summary, os.path.join(out_dir, "summary.json"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()

    root = tk.Tk()
    SorterApp(root, config_path=args.config, camera_index=args.camera_index)
    root.mainloop()

if __name__ == "__main__":
    main()
