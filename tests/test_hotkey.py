"""Test global hotkey listener."""

import sys
import os
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.hotkey import HotkeyManager


def on_activate():
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] 已唤醒！")


def on_quit():
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] 正在退出...")


def main():
    hk = HotkeyManager()
    hk.on_activate(on_activate)
    hk.on_quit(on_quit)
    hk.start()

    print("快捷键监听已启动")
    print("  Ctrl+Shift+Space = 唤醒助手")
    print("  Ctrl+Shift+Q     = 退出程序")
    print("-" * 40)

    hk.wait()
    hk.stop()
    print("已退出。")


if __name__ == "__main__":
    main()
