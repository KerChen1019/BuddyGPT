# BuddyGPT

## What's New

- Added scheduled daily news pushes at **3:00 PM** and **8:00 PM** (local time).
- Kept the first wake-up daily news flow, so you now have up to 3 daily news slots:
  - first wake-up
  - 3:00 PM update
  - 8:00 PM update
- Enforced same-day topic dedupe across all slots:
  - if a generated topic repeats, BuddyGPT retries generation
  - if no unique topic is found, that slot is skipped (no duplicate push)
- Added "catch up when available today" behavior:
  - if a scheduled time is missed while you are busy in chat, BuddyGPT pushes it when it can safely show.

A tiny Shiba that lives in your screen corner and helps you unstuck.

BuddyGPT is not a "do-it-for-me" agent. It is more like a friendly coworker who leans over, takes a quick look at your screen, and gives you a short, practical answer.

The original pain point was simple: I was asking ChatGPT a lot of practical questions, but each time I had to manually take screenshots or copy/paste email context before I could ask.

BuddyGPT removes that repetitive overhead. Instead of "screenshot -> copy context -> paste -> ask", you wake the dog and ask directly, so the whole flow feels smoother and more natural.

## What BuddyGPT Is

BuddyGPT is a desktop companion for lightweight help:
- "What does this email actually want?"
- "Why is this error happening?"
- "Is this page worth reading?"

It stays out of your way, then helps when you ask.

## Quick Install (Windows)

1. Download the latest installer: `BuddyGPT-Setup.exe` (from Releases).
2. Double-click the installer and complete setup.
3. Launch BuddyGPT from Start Menu.
4. On first wake-up, paste your Anthropic API key when the dog asks.

That is it - install, wake, ask.

## Product Soul

- `Soul.md`: product identity, boundaries, and behavior principles.
- `docs/soul-roadmap.md`: implementation status and future milestones aligned with `Soul.md`.

## How It Works

1. **Resting mode**: the Shiba hangs out in the corner.
2. **Wake up**: press `Ctrl+Shift+Space` or click the dog.
   - On first run (when no API key is configured), BuddyGPT enters onboarding and asks you to paste your API key.
3. **Context capture**: BuddyGPT captures your **last active window before wake-up**.
4. **Ask**: type your question and press `Enter`.
5. **Thinking -> Reply**: it analyzes your context and gives a short answer.
6. **Back to rest**:
- Press `Esc` to dismiss immediately.
- If there is no user response after a reply, it auto-returns to `resting` after **15 seconds**.

## Last Active Window Behavior

BuddyGPT tries to answer based on what you were just working on.

Examples:
- If you were writing an email, it captures that email window.
- If you were on a browser tab, it captures that tab window.

Implementation note:
- Wake-up from hotkey and wake-up from mouse click share the same activation pipeline.
- If overlay is foreground during activation, the code attempts to skip overlay and recover your previous real window.

## Pet States

| Resting (`zzZ`) | Awake (`Ask me anything!`) |
|---|---|
| ![Resting state](assets/shiba/states/state-resting.png) | ![Awake state](assets/shiba/states/state-awake.png) |
| Thinking (`Hmm...`) | Reply (`Ask more, or Esc to close`) |
| ![Thinking state](assets/shiba/states/state-thinking.png) | ![Reply state](assets/shiba/states/state-reply.png) |

Pet character attribution: from **Nudaeng** (`@nudaengdotbonk`).

## Hotkeys and Use Cases

| Hotkey / Action | Typical Use Case |
|---|---|
| `Ctrl+Shift+Space` | Wake BuddyGPT while you are reading an email, ticket, or docs page and want quick help. |
| Click the dog | Same as hotkey wake-up when your hand is already on the mouse. |
| `Enter` | Send your question after BuddyGPT captures context. |
| `Esc` | Close the current session immediately and send the dog back to rest. |
| `Ctrl+Shift+Q` | Quit BuddyGPT completely when you are done for the day. |

## Features

- Animated Shiba states: `resting` / `greeting` / `awake` / `thinking` / `idle_chat` / `reply`
- Active-window screenshot understanding
- App-aware context filtering
- Optional web lookup (DuckDuckGo) when needed
- Proactive daily news:
  - first wake-up push
  - scheduled pushes at 15:00 and 20:00 (local time)
  - same-day topic dedupe (no repeated topic in one day)
- Short, colleague-style answers
- Language matching (ask in Chinese, get Chinese; ask in English, get English)

## Setup

```bash
pip install -r requirements.txt
py main.py
```

## Windows Installer

Build a Windows app + installer from this repo:

```powershell
# from repository root
.\scripts\build_windows.ps1
```

Build only the app (skip Setup.exe):

```powershell
.\scripts\build_windows.ps1 -SkipInstaller
```

If your default Python is not the build target, set it explicitly:

```powershell
.\scripts\build_windows.ps1 -PythonCmd "py -3.12"
```

If your network requires a custom package index:

```powershell
.\scripts\build_windows.ps1 -PipIndexUrl "https://pypi.org/simple"
```

Outputs:
- App folder: `dist\BuddyGPT\`
- Single EXE: `dist\BuddyGPT\BuddyGPT.exe`
- Installer (when Inno Setup is available): `dist\installer\BuddyGPT-Setup.exe`

Notes:
- The script uses PyInstaller for EXE packaging.
- Setup builder uses Inno Setup (`iscc.exe`) via `packaging\BuddyGPT.iss`.
- If `pyinstaller` cannot be resolved, provide a reachable index URL with `-PipIndexUrl`.

## Uninstall

You can uninstall BuddyGPT in three ways:
- Windows Settings -> Apps -> Installed apps -> BuddyGPT -> Uninstall
- Start Menu -> BuddyGPT -> `Uninstall BuddyGPT`
- Silent uninstall (for scripts/IT):

```cmd
"C:\Program Files\BuddyGPT\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

## Configuration

Use `config.json`:

```json
{
  "api_key": "",
  "model": "claude-sonnet-4-20250514",
  "hotkey_activate": "ctrl+shift+space",
  "hotkey_quit": "ctrl+shift+q",
  "screenshot_interval": 3.0,
  "hash_threshold": 12,
  "max_tokens": 1024,
  "daily_chat": {
    "enabled": true,
    "push_times": ["15:00", "20:00"],
    "max_topic_retry": 3
  }
}
```

Or use `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxx
```

Config priority in current code:
1. If `config.json` has non-empty `api_key`, that key is used.
2. Otherwise fallback to `.env` `ANTHROPIC_API_KEY`.

Installed app config location:
- `%APPDATA%\BuddyGPT\config.json`
- `%APPDATA%\BuddyGPT\.env`

## Token Usage (Detailed)

### When tokens are NOT used

No model tokens are consumed for:
- idle animation
- wake-up UI itself
- local window detection
- local screenshot capture/filtering
- drag/move UI actions
- auto-return to resting

### When tokens ARE used

Model tokens are consumed when:
- you send a question (`Enter`)
- you send follow-up questions
- tool-use triggers extra model rounds (for web lookup flow)

### What contributes to token count

Per request, usage is roughly:
- **Input tokens**: system prompt + your question + conversation history + attached context
- **Output tokens**: assistant reply

Important details:
- First turn commonly includes the captured window image.
- Image content can significantly increase input token usage.
- Longer follow-up chains increase history size and input tokens.

### What `max_tokens` actually does

- `max_tokens` limits **output tokens per model call**.
- It does **not** limit input tokens.
- If tool-use causes multiple model calls, each call has its own output cap.

### How to inspect token usage

Runtime logs already print:
- `input_tokens`
- `output_tokens`

You can use this to identify high-cost workflows.

### Practical ways to reduce token cost

- Ask more specific questions in one turn.
- Keep sessions shorter when possible.
- Avoid unnecessary web-search style prompts.
- Wake and ask from cleaner, less noisy screens.

## Privacy and Data Boundaries (Detailed)

### What stays local

These happen locally on your machine:
- hotkey listening
- mouse click wake handling
- active window detection
- screenshot capture and filtering
- UI rendering and pet state machine

Conversation history is held in memory and cleared on each new wake-up session.

### What may be sent externally

When you submit a question, request payload may include:
- your question text
- captured screenshot context
- prompt/context strings

If web lookup is triggered, additional query/result text may be exchanged in the tool-use flow.

### API key handling

- API key can come from `config.json` or `.env`.
- Both `.env` and `config.json` are gitignored in this project.
- Best practice: keep a single source of truth (usually `.env`).

### Main privacy risks

- screenshots may contain sensitive info (email content, customer data, internal links)
- terminal windows may expose secrets
- logs/screenshots shared externally can leak data

### Privacy best practices

- Check the foreground window before waking BuddyGPT.
- Mask sensitive content before asking.
- Rotate API keys immediately if exposure is suspected.
- Do not share logs/screenshots/configs that may contain secrets.

## Project Structure

```text
BuddyGPT/
|-- main.py
|-- config.example.json
|-- requirements.txt
|-- src/
|   |-- overlay.py
|   |-- pet.py
|   |-- ai_assistant.py
|   |-- screenshot.py
|   |-- content_filter.py
|   |-- app_detector.py
|   |-- web_search.py
|   '-- ...
'-- assets/
```

## Requirements

- Windows 10/11
- Python 3.12+
- Anthropic API key

If you see the little Shiba napping, everything is working as intended.

## FAQ

### 1) Is DuckDuckGo web search free?

Yes, search itself is free in this project (no separate search API key).  
If search is used, total Claude token usage can still increase because extra model rounds are needed to read and summarize search results.

### 2) Does BuddyGPT keep spending tokens while idle?

No. Idle animation, wake-up, and local UI actions do not consume model tokens.  
Tokens are used only when you submit a question (and optional tool-use rounds).

### 3) Why does BuddyGPT sometimes answer using the wrong window?

BuddyGPT captures the last active window at wake-up.  
If focus changes right before activation, context may be off. Wake it again while the correct app is focused.

### 4) Why are README images not showing on GitHub?

Usually because image files were not tracked by git due to ignore rules (for example `*.png`).  
This repo already whitelists the Shiba state image folders in `.gitignore`.

### 5) Do I need both `config.json` and `.env` API keys?

No. Use one source of truth.  
If `config.json` has a non-empty `api_key`, it takes priority over `.env`.

### 6) Build script says `No matching distribution found for pyinstaller`

This is usually a package index/network issue, not a BuddyGPT issue.  
Try running the build with a reachable index:

```powershell
.\scripts\build_windows.ps1 -PythonCmd "py -3.12" -PipIndexUrl "https://pypi.org/simple"
```

### 7) What happens on first launch after install?

If BuddyGPT cannot find an API key, it starts an onboarding prompt on wake-up.  
Paste your Anthropic key in the dog input box and press `Enter`, and BuddyGPT will save it to `config.json` automatically.

