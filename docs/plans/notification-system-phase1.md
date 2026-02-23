# BuddyGPT Notification System - Phase 1: Daily Chat MVP

## Context

BuddyGPT 从 reactive (用户叫它才回应) 升级为 proactive (它会主动找你说话)。这是一个重要的产品形态转变。

Notification 系统分三个阶段：
1. **Phase 1 (本次)**: 每日闲聊 — Shiba 每天第一次激活时主动聊今日新闻
2. **Phase 2 (后续)**: 会议提醒 — Google Calendar 会议前弹出提醒
3. **Phase 3 (后续)**: 邮件/Slack 智能过滤 — AI 筛选重要信息，智能混合提醒

---

## Part A: New Pet Animation States

### 新增 3 个状态

现有：`RESTING`, `AWAKE`, `THINKING`, `REPLY`

新增：

| State | 用途 | 动画感觉 | 对应的 notification 功能 |
|-------|------|---------|----------------------|
| **GREETING** | 主动打招呼/每日闲聊 | 热情、放松，像同事走过来拍你肩膀 | Phase 1: 每日闲聊 |
| **ALERT** | 紧急通知（会议快开始、紧急邮件） | 着急、跳跃，像 Shiba 在叫你 | Phase 2/3: 会议提醒、紧急邮件 |
| **IDLE_CHAT** | 闲聊回复状态 | 轻松，像同事边喝咖啡边聊天 | Phase 1: 闲聊后的回复 |

### 完整状态转换图

```
RESTING  → activate     → AWAKE        (用户主动激活)
RESTING  → greet        → GREETING     (每日闲聊触发)
RESTING  → alert        → ALERT        (紧急通知触发, Phase 2/3)

AWAKE    → submit       → THINKING     (用户提问)
AWAKE    → dismiss      → RESTING      (用户取消)

GREETING → submit       → THINKING     (用户回复闲聊)
GREETING → dismiss      → RESTING      (用户忽略)

ALERT    → submit       → THINKING     (用户回复)
ALERT    → dismiss      → RESTING      (用户忽略)

THINKING → answer       → REPLY        (正常回复)
THINKING → chat_answer  → IDLE_CHAT    (闲聊类回复)

REPLY    → submit       → THINKING     (继续提问)
REPLY    → dismiss      → RESTING      (结束)

IDLE_CHAT → submit      → THINKING     (继续聊)
IDLE_CHAT → dismiss     → RESTING      (结束)
```

### File changes for Pet States

#### `src/pet.py`
- Add 3 new entries to `PetState` enum: `GREETING`, `ALERT`, `IDLE_CHAT`
- Update `TRANSITIONS` dict with new state transitions (as shown above)
- Add opacity for new states (all 1.0)
- Update `get_animation()`:
  - `show_input`: add `GREETING`, `ALERT`, `IDLE_CHAT` (all show input bar)
  - `show_bubble`: add `GREETING`, `ALERT`, `IDLE_CHAT` (all show bubble)

#### `src/sprites.py`
- Add new entries to `STATE_FOLDERS`: `"greeting": "greeting"`, `"alert": "alert"`, `"idle_chat": "idle_chat"`
- Sprite system auto-discovers PNGs in folders, so once the folders + sprite sheets exist, it just works

#### `assets/shiba/`
- Create new folders: `greeting/`, `alert/`, `idle_chat/`
- User will add sprite sheets (4x4 grid PNGs, same format as existing)
- **Fallback**: if folder is empty/missing, `SpriteManager` already logs a warning and continues. We'll add code to fall back to existing sprites:
  - GREETING → fallback to AWAKE sprites
  - ALERT → fallback to AWAKE sprites
  - IDLE_CHAT → fallback to REPLY sprites

#### `src/overlay.py`
- The overlay already reads pet state and renders accordingly
- Only change needed: ensure `_do_show_notice()` can accept a `pet_state` parameter to control which state to transition to (GREETING vs ALERT)

---

## Part B: Notification System Architecture

```
NotificationManager (orchestrator)
  |-- NotificationState (persists to notification_state.json)
  |-- list[NotificationSource]
        |-- DailyChatSource     (Phase 1, this PR)
        |-- CalendarSource      (Phase 2, future)
        |-- EmailSlackSource    (Phase 3, future)
```

### Data flow (Phase 1):
```
User presses hotkey → on_activate()
  → notification_manager.check_pending()
    → DailyChatSource.check(): "did we chat today?" (date comparison, fast)
    → DailyChatSource.generate(): AI + web_search → casual news greeting
  → pet transitions to GREETING state (not AWAKE)
  → overlay.show_notice(greeting)
  → mark_delivered("daily_chat")
  → User replies → THINKING → IDLE_CHAT (not regular REPLY)
  → Subsequent activations today → normal AWAKE flow
```

---

## New Files

### `src/notifications/__init__.py`
Exports `NotificationManager`, `DailyChatSource`.

### `src/notifications/base.py`
- `Notification` dataclass: `source_id`, `text`, `hint`, `status`, `priority`, `pet_state` (which PetState to use: GREETING or ALERT)
- `NotificationSource` ABC: `source_id` property, `check(state)` -> bool, `generate(state)` -> Optional[Notification]

### `src/notifications/state.py`
- `NotificationState`: reads/writes `%APPDATA%/BuddyGPT/notification_state.json`
- Separate from config.json — config = user preferences, state = runtime bookkeeping
- Methods: `get(key)`, `set(key, value)` (auto-persists on write)

### `src/notifications/manager.py`
- `NotificationManager`: holds sources list + state
- `register(source)`: add a notification source
- `check_pending()` -> Optional[Notification]: checks all sources, returns first ready notification
- `mark_delivered(source_id)`: updates state

### `src/notifications/daily_chat.py`
- `DailyChatSource(ai_assistant)`: implements `NotificationSource`
- `check()`: compares `state["daily_chat_last_date"]` with `date.today()`
- `generate()`: temporarily swaps AI system prompt + max_tokens, calls `ai.ask()` which triggers web_search, restores config
- Returns `Notification` with `pet_state=PetState.GREETING`
- Custom `DAILY_CHAT_SYSTEM_PROMPT`:
  - Always use web_search first
  - Pick ONE interesting thing
  - 2-3 sentences, casual tone
  - End with a conversation hook

---

## Existing Files to Modify

### `src/pet.py`
- Add `GREETING`, `ALERT`, `IDLE_CHAT` to PetState enum
- Update TRANSITIONS, STATE_OPACITY, get_animation()

### `src/sprites.py`
- Add `"greeting"`, `"alert"`, `"idle_chat"` to STATE_FOLDERS
- Add fallback logic: if a state folder has no sprites, use a fallback state's sprites

### `src/overlay.py`
- Update `show_notice()` to accept optional pet_state parameter
- Update `_do_show_notice()` to trigger the specified pet state transition
- Handle THINKING → IDLE_CHAT transition (when answering a follow-up during chat mode)

### `main.py`
- Import notification system
- Create manager, register DailyChatSource
- Add `threading.Lock` for activation safety
- Modify `on_activate()`: check pending notifications, use appropriate pet state
- Track "chat mode" flag so follow-up answers use IDLE_CHAT instead of REPLY

### `src/config.py`
- Add notifications default to DEFAULT_CONFIG
- Export `_user_data_dir` (rename from private to public: `user_data_dir`)

---

## Key Design Decisions

1. **Reuse single AIAssistant** — temporarily swap system prompt + max_tokens, then restore
2. **Seed conversation history** — after daily chat, seed `ai.history` so "tell me more" works
3. **State file separate from config** — `notification_state.json` vs `config.json`
4. **Lock on activation** — prevents duplicate daily chats
5. **Fail silently** — if generation fails, show normal activation
6. **Sprite fallback** — new states fall back to existing sprites if folder is empty

---

## Implementation Order

1. Update `src/pet.py` — add 3 new states + transitions
2. Update `src/sprites.py` — add new state folders + fallback logic
3. Create empty sprite folders: `assets/shiba/greeting/`, `alert/`, `idle_chat/`
4. Update `src/overlay.py` — pet_state param for show_notice, chat mode support
5. Create `src/notifications/base.py` — Notification dataclass + NotificationSource ABC
6. Create `src/notifications/state.py` — persistence layer
7. Create `src/notifications/manager.py` — orchestrator
8. Create `src/notifications/daily_chat.py` — AI news generation
9. Create `src/notifications/__init__.py` — exports
10. Modify `src/config.py` — add notifications default + export user_data_dir
11. Modify `main.py` — wire everything together

## Verification

1. Start BuddyGPT, press hotkey → Shiba enters GREETING state, shows news greeting
2. Type "tell me more" → THINKING → IDLE_CHAT state (not regular REPLY)
3. Press Esc → back to RESTING
4. Press hotkey again → normal AWAKE flow (no duplicate daily chat)
5. Delete `notification_state.json`, restart → daily chat triggers again
6. Set `"daily_chat": {"enabled": false}` → no daily chat
7. Add sprite sheets to `greeting/` folder → uses new animation
8. Empty `greeting/` folder → falls back to AWAKE animation
