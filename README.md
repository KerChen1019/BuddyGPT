# BuddyGPT - Screen AI Assistant

A screen-aware AI assistant that watches your active window and answers questions about what's on screen — like having a colleague looking over your shoulder.

## Features

- **Screenshot capture** — active window or full screen, multi-monitor support
- **Smart change detection** — periodic capture with perceptual hash diffing, only saves when the screen actually changes (ignores cursor blinks, mouse moves)
- **Global hotkeys** — works from any window without admin rights
- **Claude API vision** — sends screenshots to Claude, understands screen content
- **Overlay UI** — floating dialog for Q&A, remembers target window even after focus changes
- **Configurable** — hotkeys, screenshot interval, sensitivity, model, all via `config.json`

## Project Structure

```
BuddyGPT/
├── main.py              # Main entry point
├── config.json          # User config (not tracked by git)
├── config.example.json  # Config template
├── requirements.txt
├── src/
│   ├── config.py        # Config loader
│   ├── screenshot.py    # Screenshot capture (active window / full screen / multi-monitor)
│   ├── monitor.py       # Smart change detection with image hashing
│   ├── hotkey.py        # Global hotkey listener (pynput)
│   ├── ai_assistant.py  # Claude API integration (vision)
│   └── overlay.py       # Floating UI overlay (tkinter)
└── tests/
    ├── test_screenshot.py
    ├── test_monitor.py
    ├── test_hotkey.py
    └── test_ai.py
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key (choose one)
#    Option A: copy config and fill in api_key
copy config.example.json config.json

#    Option B: use .env file
echo ANTHROPIC_API_KEY=sk-ant-xxx > .env
```

## Usage

```bash
py main.py
```

1. Program starts, background screen monitoring begins
2. Switch to any window you want help with
3. Press **Ctrl+Shift+Space** — BuddyGPT captures that window and pops up a dialog
4. Type your question and press Enter
5. AI answers based on the screenshot, you can follow up
6. Press **Esc** to close the dialog, continue working
7. Press **Ctrl+Shift+Q** from anywhere to quit

## Configuration

Edit `config.json` to customize:

| Key | Default | Description |
|-----|---------|-------------|
| `api_key` | `""` | Anthropic API key (falls back to `.env`) |
| `model` | `claude-sonnet-4-20250514` | Claude model to use |
| `hotkey_activate` | `ctrl+shift+space` | Hotkey to activate assistant |
| `hotkey_quit` | `ctrl+shift+q` | Hotkey to quit program |
| `screenshot_interval` | `3.0` | Seconds between background captures |
| `hash_threshold` | `12` | Change detection sensitivity (lower = more sensitive) |
| `max_tokens` | `1024` | Max tokens in AI response |

## Requirements

- Windows
- Python 3.12+
- Anthropic API key

## Next Steps

- [ ] Improved UI overlay design
- [ ] Application-aware context (detect which app is running)
- [ ] Conversation history persistence
