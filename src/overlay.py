"""Desktop pet overlay — emoji Shiba with chat bubble."""

import threading
import tkinter as tk
from PIL import Image

from .pet import Pet, PetState

BG = "#1e1e2e"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
BUBBLE_BG = "#313244"
INPUT_BG = "#45475a"
ACCENT = "#89b4fa"

PET_EMOJI = {
    PetState.SLEEPING:  "💤\n🐕",
    PetState.WAKING:    "❗\n🐕",
    PetState.LISTENING: "👂\n🐕",
    PetState.THINKING:  "🤔\n🐕",
    PetState.ANSWERING: "😊\n🐕",
    PetState.RESTING:   "😴\n🐕",
}

SLEEP_FRAMES = ["💤\n🐕", " 💤\n🐕", "  💤\n🐕", " 💤\n🐕"]


class OverlayWindow:
    def __init__(self, on_submit):
        self._on_submit = on_submit
        self._root: tk.Tk | None = None
        self._image: Image.Image | None = None
        self._pet = Pet()
        self._ready = threading.Event()
        self._drag_data = {"x": 0, "y": 0}

        self._pet.on_state_change(lambda old, new: self._root.after(0, self._on_pet_state_change) if self._root else None)

        self._tk_thread = threading.Thread(target=self._run_tk, daemon=True)
        self._tk_thread.start()
        self._ready.wait()

    # ── Tk setup ──

    def _run_tk(self):
        self._root = tk.Tk()
        self._root.title("BuddyGPT")
        self._root.attributes("-topmost", True)
        self._root.overrideredirect(True)
        self._root.configure(bg=BG)

        # Position: bottom-right
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"320x140+{sw - 340}+{sh - 200}")
        self._root.attributes("-alpha", 0.7)

        # ── Main frame ──
        self._frame = tk.Frame(self._root, bg=BG)
        self._frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Drag to move
        self._frame.bind("<Button-1>", self._drag_start)
        self._frame.bind("<B1-Motion>", self._drag_move)

        # ── Bubble (hidden by default) ──
        self._bubble_frame = tk.Frame(self._frame, bg=BUBBLE_BG, padx=10, pady=8)
        # not packed yet — shown when answering

        self._bubble_text = tk.Text(
            self._bubble_frame, wrap=tk.WORD, font=("Segoe UI", 10),
            bg=BUBBLE_BG, fg=FG, relief=tk.FLAT, height=5, width=32,
            state=tk.DISABLED, cursor="arrow",
        )
        self._bubble_text.pack(fill=tk.BOTH, expand=True)

        self._bubble_hint = tk.Label(
            self._bubble_frame, text="", font=("Segoe UI", 8),
            fg=FG_DIM, bg=BUBBLE_BG, anchor=tk.E,
        )
        self._bubble_hint.pack(fill=tk.X)

        # ── Pet emoji ──
        self._pet_label = tk.Label(
            self._frame, text=PET_EMOJI[PetState.SLEEPING],
            font=("Segoe UI Emoji", 32), bg=BG, fg=FG, cursor="hand2",
        )
        self._pet_label.pack(pady=(0, 2))
        self._pet_label.bind("<Button-1>", self._drag_start)
        self._pet_label.bind("<B1-Motion>", self._drag_move)

        # ── Status line ──
        self._status = tk.Label(
            self._frame, text="zzZ", font=("Segoe UI", 8),
            fg=FG_DIM, bg=BG,
        )
        self._status.pack()

        # ── Input row (hidden by default) ──
        self._input_frame = tk.Frame(self._frame, bg=BG)
        # not packed yet — shown when listening

        self._entry = tk.Entry(
            self._input_frame, font=("Segoe UI", 10),
            bg=INPUT_BG, fg=FG, insertbackground=FG, relief=tk.FLAT,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self._entry.bind("<Return>", self._on_enter)

        self._send_btn = tk.Button(
            self._input_frame, text="▶", font=("Segoe UI", 10),
            bg=ACCENT, fg=BG, relief=tk.FLAT, padx=8,
            command=lambda: self._on_enter(None),
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # Escape to dismiss
        self._root.bind("<Escape>", lambda e: self._dismiss())

        # Start animation tick
        self._tick()

        self._ready.set()
        self._root.mainloop()

    # ── Animation tick ──

    def _tick(self):
        self._pet.tick()
        anim = self._pet.get_animation()

        # Sleeping breathing animation
        if anim.state == PetState.SLEEPING:
            idx = anim.frame_index % len(SLEEP_FRAMES)
            self._pet_label.config(text=SLEEP_FRAMES[idx])
        else:
            self._pet_label.config(text=PET_EMOJI.get(anim.state, "🐕"))

        self._root.after(500, self._tick)

    # ── State change handler ──

    def _on_pet_state_change(self):
        anim = self._pet.get_animation()
        self._root.attributes("-alpha", anim.opacity)

        # Resize window based on state
        sw = self._root.winfo_screenwidth()
        x = self._root.winfo_x()
        y = self._root.winfo_y()

        if anim.state in (PetState.SLEEPING, PetState.WAKING, PetState.RESTING):
            self._bubble_frame.pack_forget()
            self._input_frame.pack_forget()
            self._root.geometry(f"320x140+{x}+{y}")
            self._status.config(text="zzZ" if anim.state == PetState.SLEEPING else "...")

        elif anim.state == PetState.LISTENING:
            self._bubble_frame.pack_forget()
            self._input_frame.pack(fill=tk.X, pady=(4, 0))
            self._root.geometry(f"320x180+{x}+{y}")
            self._entry.delete(0, tk.END)
            self._entry.config(state=tk.NORMAL)
            self._send_btn.config(state=tk.NORMAL)
            self._status.config(text="问点什么？")
            self._root.after(100, lambda: self._entry.focus_set())

        elif anim.state == PetState.THINKING:
            self._input_frame.pack_forget()
            self._bubble_frame.pack(fill=tk.BOTH, expand=True, before=self._pet_label)
            self._bubble_text.config(state=tk.NORMAL)
            self._bubble_text.delete("1.0", tk.END)
            self._bubble_text.insert("1.0", "思考中...")
            self._bubble_text.config(state=tk.DISABLED)
            self._bubble_hint.config(text="")
            self._root.geometry(f"320x340+{x}+{y}")
            self._status.config(text="🤔 嗯...")

        elif anim.state == PetState.ANSWERING:
            self._input_frame.pack(fill=tk.X, pady=(4, 0))
            self._entry.delete(0, tk.END)
            self._entry.config(state=tk.NORMAL)
            self._send_btn.config(state=tk.NORMAL)
            self._root.geometry(f"320x380+{x}+{y}")
            self._status.config(text="继续提问，或按 Esc 关闭")
            self._root.after(100, lambda: self._entry.focus_set())

    # ── Public API ──

    def show(self, image: Image.Image | None = None, window_title: str = ""):
        self._image = image
        self._window_title = window_title
        if self._root:
            self._root.after(0, self._do_show)

    def _do_show(self):
        self._pet.trigger("activate")

        # Reset bubble
        self._bubble_text.config(state=tk.NORMAL)
        self._bubble_text.delete("1.0", tk.END)
        self._bubble_text.config(state=tk.DISABLED)

        # Show and focus
        self._root.deiconify()
        self._root.focus_force()

    # ── Dismiss / hide ──

    def _dismiss(self):
        self._pet.trigger("dismiss")

    # ── Input handling ──

    def _on_enter(self, event):
        question = self._entry.get().strip()
        if not question:
            return

        self._entry.delete(0, tk.END)
        self._entry.config(state=tk.DISABLED)
        self._send_btn.config(state=tk.DISABLED)
        self._pet.trigger("submit")

        threading.Thread(
            target=self._ask_async, args=(question,), daemon=True
        ).start()

    def _ask_async(self, question):
        try:
            answer = self._on_submit(question, self._image)
            self._image = None  # only send image on first question
            self._root.after(0, self._show_answer, answer)
        except Exception as e:
            self._root.after(0, self._show_answer, f"出错了: {e}")

    def _show_answer(self, answer):
        self._pet.trigger("answer")

        # Fill bubble with answer
        self._bubble_text.config(state=tk.NORMAL)
        self._bubble_text.delete("1.0", tk.END)
        self._bubble_text.insert("1.0", answer)
        self._bubble_text.config(state=tk.DISABLED)
        self._bubble_hint.config(text="Esc 关闭 · Enter 追问")

    # ── Drag to move ──

    def _drag_start(self, event):
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{x}+{y}")
