"""Test app detector — switch between windows and watch detection results."""

import sys
import os
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app_detector import detect_app

DURATION = 30
INTERVAL = 2


def main():
    print(f"App detector test — switching windows for {DURATION}s")
    print(f"Switch to different apps and watch the detection results.")
    print("-" * 65)
    print(f"{'Time':<10} {'App Type':<16} {'Process':<25} {'Title'}")
    print("-" * 65)

    start = time.time()
    last_proc = ""
    while time.time() - start < DURATION:
        info = detect_app()
        # Only print when the window changes
        if info.process_name != last_proc or info.window_title != getattr(main, '_last_title', ''):
            last_proc = info.process_name
            main._last_title = info.window_title
            ts = time.strftime("%H:%M:%S")
            title_short = info.window_title[:40] + ("..." if len(info.window_title) > 40 else "")
            print(f"{ts:<10} {info.label:<16} {info.process_name:<25} {title_short}")
            if info.url_hint:
                print(f"{'':10} URL hint: {info.url_hint[:60]}")
        time.sleep(INTERVAL)

    print("-" * 65)
    print("Done.")


if __name__ == "__main__":
    main()
