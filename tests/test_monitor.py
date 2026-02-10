"""Run screen monitor for 30 seconds and report detected changes."""

import sys
import os
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.monitor import ScreenMonitor, MonitorConfig

DURATION = 30
SAVE_DIR = Path("captures")
SAVE_DIR.mkdir(exist_ok=True)


def on_change(frame, distance):
    ts = time.strftime("%H:%M:%S")
    filename = SAVE_DIR / f"change_{int(frame.timestamp)}.png"
    frame.image.save(filename)
    w, h = frame.image.size
    print(f"[{ts}] CHANGE  distance={distance:>3}  window=\"{frame.title}\"  "
          f"size={w}x{h}  saved={filename.name}")


def on_tick(monitor, elapsed):
    ts = time.strftime("%H:%M:%S")
    remaining = DURATION - int(elapsed)
    s = monitor.stats
    print(f"[{ts}]  ...    captures={s['captures']}  changes={s['changes']}  "
          f"{remaining}s left", end="\r")


def main():
    config = MonitorConfig(
        interval=3.0,
        hash_threshold=12,  # adjust: lower = more sensitive, higher = less sensitive
        hash_size=16,
    )
    monitor = ScreenMonitor(config)
    monitor.on_change(on_change)

    print(f"Monitoring for {DURATION}s  (interval={config.interval}s, threshold={config.hash_threshold})")
    print(f"Saves to: {SAVE_DIR.resolve()}")
    print("-" * 60)

    start = time.time()
    try:
        while True:
            elapsed = time.time() - start
            if elapsed >= DURATION:
                break
            monitor.check()
            on_tick(monitor, elapsed)
            time.sleep(config.interval)
    except KeyboardInterrupt:
        print("\nStopped early.")

    print()
    print("-" * 60)
    s = monitor.stats
    print(f"Done. captures={s['captures']}  changes={s['changes']}")
    print(f"Screenshots in: {SAVE_DIR.resolve()}")


if __name__ == "__main__":
    main()
