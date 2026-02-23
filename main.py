"""BuddyGPT - Screen AI Assistant main program."""

import logging
import sys
import threading
import time
from datetime import datetime

from src.ai_assistant import AIAssistant
from src.app_detector import AppInfo, detect_app
from src.config import load_config, save_user_config
from src.content_filter import build_context_prompt, filter_content
from src.hotkey import HotkeyManager, parse_hotkey
from src.monitor import MonitorConfig, ScreenMonitor
from src.notifications import DailyChatSource, NotificationManager
from src.overlay import OverlayWindow
from src.screenshot import capture_window, get_active_hwnd

WAKE_FIRST_SLOT = "wake_first"
SCHEDULE_POLL_SECONDS = 20


def _safe_set_utf8(stream):
    if stream and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


_safe_set_utf8(sys.stdout)
_safe_set_utf8(sys.stderr)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

cfg = load_config()
ai = AIAssistant(api_key=cfg["api_key"], model=cfg["model"], max_tokens=cfg["max_tokens"])
target_hwnd: int = 0
current_app: AppInfo | None = None
news_lock = threading.Lock()

onboarding_done = bool(cfg.get("onboarding_done", bool(cfg.get("api_key", "").strip())))
onboarding_needed = bool(cfg.get("force_onboarding")) or not onboarding_done

ONBOARDING_PROMPT = (
    "Hi! Before we start, please paste your Anthropic API key here.\n\n"
    "You can also configure it manually in:\n"
    "- config.json -> api_key\n"
    "- .env -> ANTHROPIC_API_KEY"
)

daily_chat_source: DailyChatSource | None = None


def _build_notification_manager() -> NotificationManager:
    global daily_chat_source
    manager = NotificationManager()
    daily_chat_source = DailyChatSource(ai_assistant=ai, config=cfg)
    manager.register(daily_chat_source)
    return manager


notification_manager = _build_notification_manager()


def _refresh_notification_manager() -> None:
    global notification_manager
    notification_manager = _build_notification_manager()


def _looks_like_api_key(text: str) -> bool:
    value = text.strip()
    return len(value) > 20 and value.startswith("sk-")


def on_screen_change(frame, distance):
    ts = time.strftime("%H:%M:%S")
    logger.info('[%s] Screen changed (distance=%d) window="%s"', ts, distance, frame.title)


def on_submit(question, image):
    """Called by overlay UI when user submits a question."""
    global ai, onboarding_needed

    if onboarding_needed:
        text = question.strip()
        if text.lower() in {"skip", "later", "not now"}:
            return (
                "No problem. To finish setup later, add your key to either "
                "`config.json` (`api_key`) or `.env` (`ANTHROPIC_API_KEY`), "
                "then wake me again."
            )

        if _looks_like_api_key(text):
            save_user_config({"api_key": text, "onboarding_done": True, "force_onboarding": False})
            cfg["api_key"] = text
            cfg["onboarding_done"] = True
            cfg["force_onboarding"] = False
            onboarding_needed = False
            ai = AIAssistant(api_key=text, model=cfg["model"], max_tokens=cfg["max_tokens"])
            _refresh_notification_manager()
            return "Nice. API key saved. Wake me again and ask anything."

        return (
            "I still need your Anthropic API key. Paste it here and press Enter.\n"
            "Tip: it usually starts with `sk-`.\n"
            "If you want to set it manually, type `skip`."
        )

    # Re-capture and filter target window if no image.
    if image is None and target_hwnd:
        raw = capture_window(target_hwnd)
        if raw and current_app:
            image = filter_content(raw, current_app)

    # Prepend app context to the question.
    if current_app:
        context = build_context_prompt(current_app)
        full_question = f"[{context}]\n\n{question}"
    else:
        full_question = question

    return ai.ask(full_question, image=image)


def _deliver_daily_news_slot(slot_id: str, overlay: OverlayWindow, now_local: datetime | None = None) -> bool:
    """Generate and show one slot. Returns True when delivered."""
    global target_hwnd, current_app
    if daily_chat_source is None:
        return False

    now_local = now_local or datetime.now()
    notification = daily_chat_source.generate_for_slot(slot_id, now_local, notification_manager.state)
    if notification is None:
        return False

    ai.set_app_context("")
    target_hwnd = 0
    current_app = None
    overlay.show_notice(
        notification.text,
        hint=notification.hint,
        status=notification.status,
        pet_state=notification.pet_state,
    )
    return True


def _run_scheduled_news_loop(overlay: OverlayWindow) -> None:
    while True:
        time.sleep(SCHEDULE_POLL_SECONDS)
        if onboarding_needed:
            continue
        if daily_chat_source is None or not daily_chat_source.is_enabled():
            continue
        if not overlay.can_show_proactive():
            continue

        try:
            with news_lock:
                if onboarding_needed:
                    continue
                if daily_chat_source is None or not daily_chat_source.is_enabled():
                    continue
                if not overlay.can_show_proactive():
                    continue

                now_local = datetime.now()
                pending_slots = daily_chat_source.pending_timed_slots(
                    notification_manager.state,
                    now_local,
                )
                if not pending_slots:
                    continue

                slot_id = pending_slots[0]
                delivered = _deliver_daily_news_slot(slot_id, overlay, now_local)
                if delivered:
                    logger.info("Scheduled daily news delivered: %s", slot_id)
                else:
                    logger.info("Scheduled daily news skipped (no unique topic): %s", slot_id)
        except Exception:
            logger.exception("Scheduled daily news loop failed")


def on_activate(overlay):
    """Called when wake-up action is triggered."""
    global target_hwnd, current_app

    if onboarding_needed:
        overlay.show(image=None, window_title="BuddyGPT Onboarding")
        overlay.show_notice(
            ONBOARDING_PROMPT,
            hint="Paste key + Enter - type 'skip' for manual setup",
            status="Setup: API key needed",
        )
        return

    with news_lock:
        # Phase 1: first wake-up proactive news.
        try:
            if daily_chat_source and daily_chat_source.should_trigger_slot(
                notification_manager.state,
                WAKE_FIRST_SLOT,
                datetime.now(),
            ):
                if _deliver_daily_news_slot(WAKE_FIRST_SLOT, overlay, datetime.now()):
                    return
        except Exception:
            logger.exception("Daily chat wake check failed, falling back to normal activation")

        target_hwnd = get_active_hwnd(skip_hwnd=overlay.hwnd)
        current_app = detect_app(target_hwnd)
        img = capture_window(target_hwnd)

        if img and current_app:
            img = filter_content(img, current_app)

        ai.clear_history()
        if current_app:
            ai.set_app_context(current_app.app_type.value)
            logger.info(
                "Activated: %s (%s) hwnd=%d",
                current_app.label,
                current_app.process_name,
                target_hwnd,
            )
            window_title = f"{current_app.label} - {current_app.window_title}"
        else:
            ai.set_app_context("")
            logger.info("Activated: unknown app hwnd=%d", target_hwnd)
            window_title = "BuddyGPT"

        overlay.show(image=img, window_title=window_title)


def main():
    activate_keys = cfg["hotkey_activate"]
    quit_keys = cfg["hotkey_quit"]

    print("=" * 50)
    print("  BuddyGPT - Screen AI Assistant")
    print("=" * 50)
    print(f"  {activate_keys} = Wake buddy")
    print(f"  {quit_keys} = Quit")
    print(f"  model: {cfg['model']}")
    print("=" * 50)

    overlay = OverlayWindow(
        on_submit=on_submit,
        on_activate=lambda: on_activate(overlay),
    )
    print("UI ready.")

    scheduler_thread = threading.Thread(
        target=_run_scheduled_news_loop,
        args=(overlay,),
        daemon=True,
        name="daily-news-scheduler",
    )
    scheduler_thread.start()
    print("Daily news scheduler started.")

    monitor_config = MonitorConfig(
        interval=cfg["screenshot_interval"],
        hash_threshold=cfg["hash_threshold"],
    )
    monitor = ScreenMonitor(monitor_config)
    monitor.on_change(on_screen_change)
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()
    print("Screen monitor started.")

    hk = HotkeyManager(
        hotkey=parse_hotkey(activate_keys),
        quit_hotkey=parse_hotkey(quit_keys),
    )
    hk.on_activate(lambda: on_activate(overlay))
    hk.start()
    print("Hotkey listener started.")
    print(f"\nWaiting for wake-up... ({activate_keys})\n")

    hk.wait()
    hk.stop()
    print("BuddyGPT exited.")


if __name__ == "__main__":
    main()
