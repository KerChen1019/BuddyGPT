# BuddyGPT - Screen AI Assistant

A screen-aware AI assistant that watches your active window and answers questions about what's on screen — like having a colleague looking over your shoulder.

## Features (Day 1)

- **Screenshot capture** — active window or full screen, multi-monitor support
- **Smart change detection** — periodic capture with perceptual hash diffing, only saves when the screen actually changes (ignores cursor blinks, mouse moves)
- **Global hotkeys** — Ctrl+Shift+Space to activate, Ctrl+Shift+Q to quit, works from any window without admin rights

## Project Structure

```
BuddyGPT/
├── requirements.txt
├── src/
│   ├── screenshot.py    # Screenshot capture (active window / full screen / multi-monitor)
│   ├── monitor.py       # Smart change detection with image hashing
│   └── hotkey.py        # Global hotkey listener (pynput)
└── tests/
    ├── test_screenshot.py
    ├── test_monitor.py
    └── test_hotkey.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Quick Test

```bash
# Screenshot capture
py tests\test_screenshot.py

# Screen change monitor (runs 30s)
py tests\test_monitor.py

# Hotkey listener
py tests\test_hotkey.py
```

## Hotkeys

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+Space | Activate assistant |
| Ctrl+Shift+Q | Quit |

## Requirements

- Windows
- Python 3.12+

## Next Steps

- [ ] Connect to Claude API (vision)
- [ ] User input via natural language
- [ ] Build simple UI overlay
