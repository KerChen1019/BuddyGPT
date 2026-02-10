"""Minimal overlay UI — pops up on hotkey, takes a question, shows AI answer."""

import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image


class OverlayWindow:
    def __init__(self, on_submit):
        """on_submit(question, image) -> answer_str. Called in background thread."""
        self._on_submit = on_submit
        self._root: tk.Tk | None = None
        self._image: Image.Image | None = None
        self._ready = threading.Event()

        # Start Tk on its own thread
        self._tk_thread = threading.Thread(target=self._run_tk, daemon=True)
        self._tk_thread.start()
        self._ready.wait()

    def _run_tk(self):
        self._root = tk.Tk()
        self._root.withdraw()  # hidden until show()
        self._root.title("BuddyGPT")
        self._root.attributes("-topmost", True)
        self._root.configure(bg="#1e1e2e")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._hide)

        # ── Layout ──
        frame = tk.Frame(self._root, bg="#1e1e2e", padx=16, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(
            frame, text="BuddyGPT", font=("Segoe UI", 14, "bold"),
            fg="#cdd6f4", bg="#1e1e2e",
        ).pack(anchor=tk.W)

        # Status line
        self._status = tk.Label(
            frame, text="", font=("Segoe UI", 9),
            fg="#6c7086", bg="#1e1e2e", anchor=tk.W,
        )
        self._status.pack(fill=tk.X, pady=(2, 8))

        # Answer area
        self._answer = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Segoe UI", 11),
            bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, height=10, width=60, state=tk.DISABLED,
        )
        self._answer.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Input row
        input_frame = tk.Frame(frame, bg="#1e1e2e")
        input_frame.pack(fill=tk.X)

        self._entry = tk.Entry(
            input_frame, font=("Segoe UI", 12),
            bg="#45475a", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self._entry.bind("<Return>", self._on_enter)

        self._send_btn = tk.Button(
            input_frame, text="发送", font=("Segoe UI", 11),
            bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT, padx=16, pady=4,
            command=lambda: self._on_enter(None),
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # Escape to close
        self._root.bind("<Escape>", lambda e: self._hide())

        self._ready.set()
        self._root.mainloop()

    def show(self, image: Image.Image | None = None, window_title: str = ""):
        """Show the overlay with a new screenshot context."""
        self._image = image
        self._window_title = window_title
        if self._root:
            self._root.after(0, self._do_show)

    def _do_show(self):
        # Reset
        self._answer.config(state=tk.NORMAL)
        self._answer.delete("1.0", tk.END)
        self._answer.config(state=tk.DISABLED)
        self._entry.delete(0, tk.END)

        if self._image:
            w, h = self._image.size
            self._status.config(text=f"监视窗口: {self._window_title}  ({w}x{h})")
        else:
            self._status.config(text="未截取到屏幕")

        # Center on screen
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        ww, wh = 580, 420
        x = (sw - ww) // 2
        y = (sh - wh) // 3
        self._root.geometry(f"{ww}x{wh}+{x}+{y}")
        self._root.deiconify()
        self._root.focus_force()
        self._entry.focus_set()

    def _hide(self):
        if self._root:
            self._root.withdraw()

    def _on_enter(self, event):
        question = self._entry.get().strip()
        if not question:
            return

        self._entry.delete(0, tk.END)
        self._append_text(f"你: {question}\n\n")
        self._set_input_enabled(False)
        self._status.config(text="AI 思考中...")

        # Run API call in background thread
        threading.Thread(
            target=self._ask_async, args=(question,), daemon=True
        ).start()

    def _ask_async(self, question):
        try:
            answer = self._on_submit(question, self._image)
            # Only send image on first question
            self._image = None
            self._root.after(0, self._show_answer, answer)
        except Exception as e:
            self._root.after(0, self._show_answer, f"错误: {e}")

    def _show_answer(self, answer):
        self._append_text(f"AI: {answer}\n\n")
        self._status.config(text="继续提问，或按 Esc 关闭")
        self._set_input_enabled(True)
        self._entry.focus_set()

    def _append_text(self, text):
        self._answer.config(state=tk.NORMAL)
        self._answer.insert(tk.END, text)
        self._answer.see(tk.END)
        self._answer.config(state=tk.DISABLED)

    def _set_input_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._entry.config(state=state)
        self._send_btn.config(state=state)
