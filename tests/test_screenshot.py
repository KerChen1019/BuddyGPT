"""Quick manual test for screenshot capture."""

import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.screenshot import (
    capture_active_window,
    capture_full_screen,
    get_active_window_title,
)


def main():
    # 1. Active window title
    title = get_active_window_title()
    print(f"Active window: {title}")

    # 2. Capture active window
    img = capture_active_window()
    if img:
        path = "test_active_window.png"
        img.save(path)
        print(f"Active window screenshot saved: {path}  ({img.size[0]}x{img.size[1]})")
    else:
        print("Failed to capture active window")

    # 3. Capture full screen
    img_full = capture_full_screen()
    path_full = "test_full_screen.png"
    img_full.save(path_full)
    print(f"Full screen screenshot saved: {path_full}  ({img_full.size[0]}x{img_full.size[1]})")


if __name__ == "__main__":
    main()
