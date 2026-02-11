# BuddyGPT

A little Shiba that lives on your desktop.

It doesn't do your work. It doesn't write your emails. It just sits there, napping in the corner of your screen — until you get stuck, glance over, and ask "hey, what's this?"

Then it wakes up, peeks at your screen, and says something like:

> "Oh, `user` is None here. Just use `.get()` and you're good."

That's it. Like a colleague sitting next to you who happens to be good at everything.

## What it is

BuddyGPT is a **desktop companion**, not an AI assistant.

The difference matters:
- An assistant takes your task and does it for you
- A companion **sits with you** while you do it yourself

When you're reading a long email and can't figure out what they actually want — you ask. When you're staring at an error message at 2am — you ask. When you're on a webpage and just want someone to tell you if it's worth reading — you ask.

It glances at your screen, gives you a short nudge in the right direction, and goes back to sleep.

## How it works

A small Shiba lives in the corner of your screen:

```
💤        ← sleeping, semi-transparent, out of your way
🐕
```

Press **Ctrl+Shift+Space** anywhere — it wakes up:

```
👂        ← ears up, ready to listen
🐕
[ask me anything___]
```

Ask a question — it thinks:

```
🤔        ← peeking at your screen
🐕
[thinking...]
```

Then gives you a quick answer:

```
┌──────────────────────────────┐
│ He's just asking for the     │
│ report by Friday. Include    │
│ Q3 data and you're good.    │
└──────────────────────────────┘
😊
🐕
```

Press **Esc** — it yawns and goes back to sleep. That's the whole interaction.

## Features

- **Always there, never in the way** — semi-transparent pet sits on your desktop, draggable anywhere
- **Sees what you see** — captures your active window when you ask, knows if you're in Gmail, VS Code, Terminal, etc.
- **Smart about context** — filters out UI noise (sidebars, nav bars) and adjusts its tone based on what app you're using
- **Short answers only** — trained to respond like a colleague, not an encyclopedia. 2-3 sentences max
- **Remembers your window** — even after the chat overlay takes focus, it still watches the window you were on

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure API key
copy config.example.json config.json
# Edit config.json and add your Anthropic API key
# Or: echo ANTHROPIC_API_KEY=sk-ant-xxx > .env

# Run
py main.py
```

## Hotkeys

| Shortcut | What it does |
|----------|-------------|
| **Ctrl+Shift+Space** | Wake up the Shiba, capture current screen |
| **Esc** | Dismiss, Shiba goes back to sleep |
| **Ctrl+Shift+Q** | Quit the program |

All hotkeys work from any window, no admin rights needed.

## Configuration

Edit `config.json`:

```json
{
    "api_key": "",
    "model": "claude-sonnet-4-20250514",
    "hotkey_activate": "ctrl+shift+space",
    "hotkey_quit": "ctrl+shift+q",
    "screenshot_interval": 3.0,
    "hash_threshold": 12,
    "max_tokens": 1024
}
```

## Project Structure

```
BuddyGPT/
├── main.py                # Entry point
├── config.json            # Your config (gitignored)
├── config.example.json    # Config template
├── src/
│   ├── overlay.py         # Desktop pet UI (tkinter)
│   ├── pet.py             # Pet state machine (sleep → wake → think → answer)
│   ├── prompts.py         # Personality & conversation style
│   ├── ai_assistant.py    # Claude API (vision)
│   ├── app_detector.py    # Detect current app (Gmail, VS Code, etc.)
│   ├── content_filter.py  # Crop screenshots to remove UI noise
│   ├── screenshot.py      # Screen capture (multi-monitor, per-window)
│   ├── monitor.py         # Background change detection
│   ├── hotkey.py          # Global hotkey listener
│   └── config.py          # Config loader
├── assets/shiba/          # Pet sprites (coming soon)
└── tests/
```

## Requirements

- Windows
- Python 3.12+
- Anthropic API key

## Roadmap

- [ ] Real Shiba sprites to replace emoji
- [ ] Smoother animations (wake up, think, yawn)
- [ ] Voice input
- [ ] Conversation memory across sessions
