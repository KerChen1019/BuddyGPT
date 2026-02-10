"""Test: capture screenshot → ask Claude → print answer."""

import sys
import os
import logging

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.screenshot import capture_active_window, get_active_window_title
from src.ai_assistant import AIAssistant


def main():
    # 1. Capture
    print("Capturing active window...")
    img = capture_active_window()
    if img is None:
        print("Failed to capture active window.")
        return
    title = get_active_window_title()
    print(f"Window: {title}  Size: {img.size[0]}x{img.size[1]}")

    # 2. Ask Claude
    print("Sending to Claude...")
    ai = AIAssistant()
    answer = ai.ask("这个截图里有什么？请简要描述。", image=img)

    # 3. Print answer
    print("-" * 40)
    print(answer)
    print("-" * 40)


if __name__ == "__main__":
    main()
