"""Load config from config.json with .env fallback for API key."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "api_key": "",
    "onboarding_done": False,
    "force_onboarding": False,
    "model": "claude-sonnet-4-20250514",
    "hotkey_activate": "ctrl+shift+space",
    "hotkey_quit": "ctrl+shift+q",
    "screenshot_interval": 3.0,
    "hash_threshold": 12,
    "max_tokens": 1024,
    "daily_chat": {
        "enabled": True,
        "push_times": ["15:00", "20:00"],
        "max_topic_retry": 3,
    },
}


def user_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "BuddyGPT"
    return Path.home() / ".buddygpt"


def _config_candidates() -> list[Path]:
    user_config = user_data_dir() / "config.json"
    local_config = ROOT / "config.json"
    if getattr(sys, "frozen", False):
        return [user_config, local_config]
    return [local_config, user_config]


def _load_env_files() -> None:
    # For installed app, prefer user-scoped env file; for dev, keep local .env support.
    load_dotenv(user_data_dir() / ".env", override=False)
    load_dotenv(ROOT / ".env", override=False)


def _user_data_dir() -> Path:
    """Backward-compatible alias for older imports."""
    return user_data_dir()


def load_config() -> dict:
    _load_env_files()
    config = dict(DEFAULT_CONFIG)
    for config_path in _config_candidates():
        if not config_path.exists():
            continue
        with open(config_path, "r", encoding="utf-8-sig") as f:
            user = json.load(f)
        config.update({k: v for k, v in user.items() if v != ""})
        break

    # Merge nested daily_chat settings.
    daily_chat_cfg = config.get("daily_chat")
    if not isinstance(daily_chat_cfg, dict):
        daily_chat_cfg = {}
    merged_daily_chat = dict(DEFAULT_CONFIG["daily_chat"])
    merged_daily_chat.update(daily_chat_cfg)
    config["daily_chat"] = merged_daily_chat

    # .env overrides empty api_key
    if not config["api_key"]:
        config["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")

    return config


def save_user_config(updates: dict) -> None:
    """Persist selected config fields to config.json."""
    config_path = _config_candidates()[0]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    current = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                current = json.load(f)
        except (json.JSONDecodeError, OSError):
            current = {}

    current.update(updates)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=4)
