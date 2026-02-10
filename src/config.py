"""Load config from config.json with .env fallback for API key."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "claude-sonnet-4-20250514",
    "hotkey_activate": "ctrl+shift+space",
    "hotkey_quit": "ctrl+shift+q",
    "screenshot_interval": 3.0,
    "hash_threshold": 12,
    "max_tokens": 1024,
}


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    config_path = ROOT / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            user = json.load(f)
        config.update({k: v for k, v in user.items() if v != ""})

    # .env overrides empty api_key
    if not config["api_key"]:
        config["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")

    return config
