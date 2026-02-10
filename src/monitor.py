"""Smart screen monitor with image-hash based change detection."""

import time
from dataclasses import dataclass, field
from pathlib import Path

import imagehash
from PIL import Image

from .screenshot import capture_active_window, get_active_window_title


@dataclass
class MonitorConfig:
    interval: float = 3.0           # seconds between captures
    hash_threshold: int = 12        # perceptual hash distance to count as "changed"
    hash_size: int = 16             # hash resolution (higher = more sensitive)
    save_dir: Path = Path("captures")


@dataclass
class FrameInfo:
    image: Image.Image
    phash: imagehash.ImageHash
    title: str
    timestamp: float


class ScreenMonitor:
    def __init__(self, config: MonitorConfig | None = None):
        self.config = config or MonitorConfig()
        self._last_frame: FrameInfo | None = None
        self._change_count: int = 0
        self._capture_count: int = 0
        self._on_change_callbacks: list = []

    def on_change(self, callback):
        """Register a callback: callback(frame_info, distance)."""
        self._on_change_callbacks.append(callback)

    def _compute_hash(self, img: Image.Image) -> imagehash.ImageHash:
        return imagehash.phash(img, hash_size=self.config.hash_size)

    def capture_and_compare(self) -> tuple[FrameInfo | None, int | None]:
        """Capture current screen, compare with last frame.

        Returns (frame_info, distance).  distance is None on first capture.
        """
        img = capture_active_window()
        if img is None:
            return None, None

        self._capture_count += 1
        phash = self._compute_hash(img)
        title = get_active_window_title()
        frame = FrameInfo(image=img, phash=phash, title=title, timestamp=time.time())

        if self._last_frame is None:
            self._last_frame = frame
            return frame, None

        distance = self._last_frame.phash - phash
        return frame, distance

    def check(self) -> bool:
        """Single check cycle. Returns True if a meaningful change was detected."""
        frame, distance = self.capture_and_compare()
        if frame is None:
            return False

        # First frame — always counts as a change
        if distance is None:
            self._last_frame = frame
            self._change_count += 1
            for cb in self._on_change_callbacks:
                cb(frame, 0)
            return True

        if distance >= self.config.hash_threshold:
            self._last_frame = frame
            self._change_count += 1
            for cb in self._on_change_callbacks:
                cb(frame, distance)
            return True

        return False

    def run(self, duration: float | None = None):
        """Run the monitor loop. Blocks until duration expires or KeyboardInterrupt."""
        start = time.time()
        try:
            while True:
                if duration and (time.time() - start) >= duration:
                    break
                self.check()
                time.sleep(self.config.interval)
        except KeyboardInterrupt:
            pass

    @property
    def stats(self) -> dict:
        return {
            "captures": self._capture_count,
            "changes": self._change_count,
        }
