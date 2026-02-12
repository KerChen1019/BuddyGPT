"""BuddyGPT — Screen AI Assistant main program."""

import sys
import threading
import time
import logging

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

from src.config import load_config
from src.screenshot import get_active_hwnd, get_window_title, capture_window
from src.monitor import ScreenMonitor, MonitorConfig
from src.hotkey import HotkeyManager, parse_hotkey
from src.ai_assistant import AIAssistant
from src.overlay import OverlayWindow
from src.app_detector import detect_app, AppInfo
from src.content_filter import filter_content, build_context_prompt

cfg = load_config()
ai = AIAssistant(api_key=cfg["api_key"], model=cfg["model"], max_tokens=cfg["max_tokens"])
target_hwnd: int = 0
current_app: AppInfo | None = None


def on_screen_change(frame, distance):
    ts = time.strftime("%H:%M:%S")
    logger.info("[%s] Screen changed (distance=%d) window=\"%s\"", ts, distance, frame.title)


def on_submit(question, image):
    """Called by overlay UI when user submits a question."""
    # Re-capture and filter target window if no image
    if image is None and target_hwnd:
        raw = capture_window(target_hwnd)
        if raw and current_app:
            image = filter_content(raw, current_app)

    # Prepend app context to the question
    if current_app:
        context = build_context_prompt(current_app)
        full_question = f"[{context}]\n\n{question}"
    else:
        full_question = question

    answer = ai.ask(full_question, image=image)
    return answer


def on_activate(overlay):
    """Called when hotkey is pressed — detect app, capture & filter, show overlay."""
    global target_hwnd, current_app
    target_hwnd = get_active_hwnd(skip_hwnd=overlay.hwnd)
    current_app = detect_app(target_hwnd)
    img = capture_window(target_hwnd)

    # Filter content based on app type
    if img and current_app:
        img = filter_content(img, current_app)

    ai.clear_history()
    ai.set_app_context(current_app.app_type.value)
    logger.info("Activated: %s (%s) hwnd=%d", current_app.label, current_app.process_name, target_hwnd)
    overlay.show(image=img, window_title=f"{current_app.label} — {current_app.window_title}")


def main():
    activate_keys = cfg["hotkey_activate"]
    quit_keys = cfg["hotkey_quit"]

    print("=" * 50)
    print("  BuddyGPT — Screen AI Assistant")
    print("=" * 50)
    print(f"  {activate_keys} = 唤醒助手")
    print(f"  {quit_keys} = 退出程序")
    print(f"  model: {cfg['model']}")
    print("=" * 50)

    # UI overlay
    overlay = OverlayWindow(
        on_submit=on_submit,
        on_activate=lambda: on_activate(overlay),
    )
    print("UI 已就绪。")

    # Screen monitor
    monitor_config = MonitorConfig(
        interval=cfg["screenshot_interval"],
        hash_threshold=cfg["hash_threshold"],
    )
    monitor = ScreenMonitor(monitor_config)
    monitor.on_change(on_screen_change)
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()
    print("屏幕监控已启动。")

    # Hotkey listener
    hk = HotkeyManager(
        hotkey=parse_hotkey(activate_keys),
        quit_hotkey=parse_hotkey(quit_keys),
    )
    hk.on_activate(lambda: on_activate(overlay))
    hk.start()
    print("快捷键监听已启动。")
    print(f"\n等待唤醒... ({activate_keys})\n")

    # Block until quit hotkey
    hk.wait()
    hk.stop()
    print("BuddyGPT 已退出。")


if __name__ == "__main__":
    main()
