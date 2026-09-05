import io
import math
import platform
import queue
import struct
import threading
import wave

_IS_WINDOWS = platform.system() == "Windows"
_SAMPLE_RATE = 44100
_queue = queue.Queue()
_worker_lock = threading.Lock()
_worker_started = False


def _generate_tone(frequency, duration_ms, volume=0.6):
    n_samples = int(_SAMPLE_RATE * duration_ms / 1000)
    frames = bytearray()
    for i in range(n_samples):
        t = i / _SAMPLE_RATE
        fade = min(1.0, i / 200.0, (n_samples - i) / 200.0)
        sample = int(volume * fade * 32767 * math.sin(2 * math.pi * frequency * t))
        frames += struct.pack("<h", sample)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(_SAMPLE_RATE)
        wav.writeframes(bytes(frames))
    return buf.getvalue()


def _worker():
    import winsound

    while True:
        tones = _queue.get()
        for frequency, duration_ms in tones:
            data = _generate_tone(frequency, duration_ms)
            try:
                winsound.PlaySound(data, winsound.SND_MEMORY)
            except Exception:
                pass


def _ensure_worker():
    global _worker_started
    if _worker_started:
        return
    with _worker_lock:
        if not _worker_started:
            threading.Thread(target=_worker, daemon=True).start()
            _worker_started = True


def _play_async(tones):
    if not _IS_WINDOWS:
        return
    _ensure_worker()
    _queue.put(tones)


def play_left():
    _play_async([(500, 400)])


def play_straight():
    _play_async([(1200, 150), (1200, 150)])


def play_for_route(route):
    if route == "LEFT":
        play_left()
    elif route == "STRAIGHT":
        play_straight()
