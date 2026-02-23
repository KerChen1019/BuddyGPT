"""Desktop pet overlay — animated Shiba with iOS-style chat UI."""

import ctypes
import threading
import tkinter as tk
import tkinter.font as tkfont
from PIL import Image, ImageTk

from .pet import Pet, PetState
from .sprites import SpriteManager

user32 = ctypes.windll.user32

# Chroma key — all pixels of this color become fully transparent
CHROMA = "#00ff00"
CHROMA_RGB = (0, 255, 0)

# iOS-style colors
BUBBLE_BG = "#E9E9EB"
BUBBLE_FG = "#000000"
INPUT_BG = "#FFFFFF"
INPUT_BORDER = "#C7C7CC"
ACCENT = "#007AFF"
STATUS_FG = "#FFFFFF"
STATUS_BG = "#8E8E93"
HINT_FG = "#8E8E93"

SPRITE_SIZE = 128
FRAME_MS = 160  # milliseconds per animation frame
AUTO_REST_MS = 15000
ALERT_DISMISS_MS = 30000

WINDOW_W = 320

# Fixed heights for states without bubble
H_RESTING = 200
H_AWAKE = 260

# Bubble geometry
BUBBLE_TAIL_H = 15
CORNER_R = 15
BUBBLE_PAD_TOP = 16
BUBBLE_PAD_BOTTOM = 16
BUBBLE_MIN_TEXT_H = 28
BUBBLE_MAX_TEXT_H = 280

# Input bar geometry
INPUT_H = 34
INPUT_R = 17
INPUT_PAD_X = 28  # horizontal margin to narrow the pill

# Base height: sprite + status + padding
BASE_H = SPRITE_SIZE + 50
# Extra height when input bar is shown
INPUT_AREA_H = INPUT_H + 16


def _create_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Draw a rounded rectangle using a smooth polygon."""
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class OverlayWindow:
    def __init__(self, on_submit, on_activate=None):
        self._on_submit = on_submit
        self._on_activate = on_activate
        self._root: tk.Tk | None = None
        self._hwnd: int = 0
        self._image: Image.Image | None = None
        self._pet = Pet()
        self._sprites = SpriteManager(frame_size=SPRITE_SIZE, chroma=CHROMA_RGB)
        self._ready = threading.Event()
        self._drag_data = {"x": 0, "y": 0}
        self._drag_moved = False
        self._photo: ImageTk.PhotoImage | None = None
        self._bubble_total_h = 0  # current bubble height (including tail)
        self._idle_after_id: str | None = None
        self._alert_after_id: str | None = None
        self._chat_mode = False

        self._pet.on_state_change(
            lambda old, new: self._root.after(0, self._on_pet_state_change)
            if self._root else None
        )

        self._tk_thread = threading.Thread(target=self._run_tk, daemon=True)
        self._tk_thread.start()
        self._ready.wait()

    @property
    def hwnd(self) -> int:
        return self._hwnd

    def can_show_proactive(self) -> bool:
        """Whether it's safe to show proactive notifications without interruption."""
        return self._pet.state == PetState.RESTING

    # ── Tk setup ──

    def _run_tk(self):
        self._root = tk.Tk()
        self._root.title("BuddyGPT")
        self._root.attributes("-topmost", True)
        self._root.overrideredirect(True)
        self._root.configure(bg=CHROMA)
        self._root.attributes("-transparentcolor", CHROMA)
        self._root.attributes("-alpha", 1.0)

        # Position: bottom-right
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(
            f"{WINDOW_W}x{H_RESTING}+{sw - WINDOW_W - 20}+{sh - H_RESTING - 60}"
        )

        # Get Win32 HWND for skip_hwnd logic
        self._root.update_idletasks()
        self._hwnd = user32.GetParent(self._root.winfo_id()) or self._root.winfo_id()

        # Font for text measurement
        self._measure_font = tkfont.Font(family="Segoe UI", size=10)

        # ── Main frame ──
        self._frame = tk.Frame(self._root, bg=CHROMA)
        self._frame.pack(fill=tk.BOTH, expand=True)

        # ── Bubble canvas (hidden by default, drawn dynamically) ──
        canvas_w = WINDOW_W - 16
        self._canvas_w = canvas_w
        self._bubble_canvas = tk.Canvas(
            self._frame, bg=CHROMA, highlightthickness=0,
            width=canvas_w, height=0,
        )

        # Text widget for bubble (placed on canvas by _update_bubble)
        self._bubble_text = tk.Text(
            self._bubble_canvas, wrap=tk.WORD, font=("Segoe UI", 10),
            bg=BUBBLE_BG, fg=BUBBLE_FG, relief=tk.FLAT,
            height=1, width=30, state=tk.DISABLED, cursor="arrow",
            borderwidth=0, highlightthickness=0,
        )

        # Hint label for bubble
        self._bubble_hint = tk.Label(
            self._bubble_canvas, text="", font=("Segoe UI", 8),
            fg=HINT_FG, bg=BUBBLE_BG, anchor=tk.E,
        )

        # Drag on bubble
        self._bubble_canvas.bind("<Button-1>", self._drag_start)
        self._bubble_canvas.bind("<B1-Motion>", self._drag_move)

        # ── Pet sprite ──
        self._pet_label = tk.Label(
            self._frame, bg=CHROMA, cursor="hand2",
            width=SPRITE_SIZE, height=SPRITE_SIZE,
        )
        self._pet_label.pack(pady=(4, 0))
        self._pet_label.bind("<Button-1>", self._drag_start)
        self._pet_label.bind("<B1-Motion>", self._drag_move)
        self._pet_label.bind("<ButtonRelease-1>", self._on_pet_click)

        # ── Status pill badge ──
        self._status_font = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        self._status_canvas = tk.Canvas(
            self._frame, bg=CHROMA, highlightthickness=0,
            height=26,
        )
        self._status_canvas.pack(pady=(0, 4))
        self._status_canvas.bind("<Button-1>", self._drag_start)
        self._status_canvas.bind("<B1-Motion>", self._drag_move)
        self._status_pill = None  # canvas item id
        self._status_text_id = None  # canvas item id
        self._update_status("zzZ")

        # ── Input canvas (hidden by default) ──
        self._input_canvas = tk.Canvas(
            self._frame, bg=CHROMA, highlightthickness=0,
            width=canvas_w, height=INPUT_H,
        )

        # Pill-shaped background (narrower)
        pill_x1 = INPUT_PAD_X
        pill_x2 = canvas_w - INPUT_PAD_X
        pill_mid = (pill_x1 + pill_x2) // 2
        _create_rounded_rect(
            self._input_canvas, pill_x1, 2, pill_x2, INPUT_H - 2,
            r=INPUT_R, fill=INPUT_BG, outline=INPUT_BORDER, width=1,
        )

        # Entry widget inside pill
        pill_inner_w = pill_x2 - pill_x1
        self._entry = tk.Entry(
            self._input_canvas, font=("Segoe UI", 9),
            bg=INPUT_BG, fg="#000000", insertbackground="#000000",
            relief=tk.FLAT, borderwidth=0, highlightthickness=0,
        )
        self._input_canvas.create_window(
            pill_mid - 14, INPUT_H // 2,
            window=self._entry, width=pill_inner_w - 62, height=INPUT_H - 12,
        )
        self._entry.bind("<Return>", self._on_enter)
        self._entry.bind("<KeyPress>", self._on_entry_activity)

        # Send button
        self._send_btn = tk.Button(
            self._input_canvas, text="\u2191", font=("Segoe UI", 9, "bold"),
            bg=ACCENT, fg="#FFFFFF", relief=tk.FLAT,
            activebackground="#005EC4", activeforeground="#FFFFFF",
            cursor="hand2", borderwidth=0, highlightthickness=0,
            command=lambda: self._on_enter(None),
        )
        self._input_canvas.create_window(
            pill_x2 - 20, INPUT_H // 2,
            window=self._send_btn, width=26, height=26,
        )

        # Escape to dismiss
        self._root.bind("<Escape>", lambda e: self._dismiss())

        # Pick initial resting animation & start tick
        self._sprites.pick_random("resting")
        self._tick()

        self._ready.set()
        self._root.mainloop()

    # ── Bubble auto-sizing ──

    def _measure_text_height(self, text):
        """Estimate pixel height needed to display text in the bubble."""
        available_w = self._canvas_w - 40
        line_h = self._measure_font.metrics("linespace")

        total_lines = 0
        for line in text.split('\n'):
            if not line:
                total_lines += 1
                continue
            line_px = self._measure_font.measure(line)
            total_lines += max(1, -(-line_px // available_w))  # ceil division

        return max(total_lines * line_h + 8, BUBBLE_MIN_TEXT_H)

    def _update_bubble(self, text, hint=""):
        """Redraw bubble canvas sized to fit text, return total height."""
        canvas_w = self._canvas_w
        available_w = canvas_w - 40

        text_h = min(self._measure_text_height(text), BUBBLE_MAX_TEXT_H)
        hint_h = 22 if hint else 0
        bubble_h = BUBBLE_PAD_TOP + text_h + hint_h + BUBBLE_PAD_BOTTOM
        total_h = bubble_h + BUBBLE_TAIL_H

        # Resize and redraw canvas
        self._bubble_canvas.config(height=total_h)
        self._bubble_canvas.delete("all")

        # Rounded rect body
        _create_rounded_rect(
            self._bubble_canvas, 4, 4, canvas_w - 4, bubble_h,
            r=CORNER_R, fill=BUBBLE_BG, outline="",
        )

        # Tail pointing down toward the dog
        mid = canvas_w // 2
        self._bubble_canvas.create_polygon(
            mid - 10, bubble_h - 2,
            mid, bubble_h + BUBBLE_TAIL_H - 2,
            mid + 10, bubble_h - 2,
            fill=BUBBLE_BG, outline="", smooth=False,
        )

        # Place text
        self._bubble_text.config(state=tk.NORMAL)
        self._bubble_text.delete("1.0", tk.END)
        self._bubble_text.insert("1.0", text)
        self._bubble_text.config(state=tk.DISABLED)

        text_center_y = BUBBLE_PAD_TOP + text_h // 2 + 4
        self._bubble_canvas.create_window(
            canvas_w // 2, text_center_y,
            window=self._bubble_text, width=available_w, height=text_h,
        )

        # Place hint
        if hint:
            self._bubble_hint.config(text=hint)
            self._bubble_canvas.create_window(
                canvas_w // 2, bubble_h - BUBBLE_PAD_BOTTOM // 2 - 2,
                window=self._bubble_hint, width=available_w,
            )

        # Show bubble if not already visible
        if not self._bubble_canvas.winfo_ismapped():
            self._bubble_canvas.pack(fill=tk.X, padx=8, before=self._pet_label)

        self._bubble_total_h = total_h
        return total_h

    def _update_status(self, text):
        """Redraw the status pill badge with new text."""
        self._status_canvas.delete("all")
        text_w = self._status_font.measure(text)
        pill_w = text_w + 24
        pill_h = 22
        cx = self._canvas_w // 2
        x1 = cx - pill_w // 2
        x2 = cx + pill_w // 2
        y1 = 2
        y2 = y1 + pill_h
        _create_rounded_rect(
            self._status_canvas, x1, y1, x2, y2,
            r=pill_h // 2, fill=STATUS_BG, outline="",
        )
        self._status_canvas.create_text(
            cx, y1 + pill_h // 2,
            text=text, font=self._status_font, fill=STATUS_FG,
        )
        self._status_canvas.config(width=self._canvas_w)

    def _set_window_height(self, bubble_h=0, with_input=False):
        """Resize window anchored at bottom edge."""
        x = self._root.winfo_x()
        bottom = self._root.winfo_y() + self._root.winfo_height()

        new_h = BASE_H
        if bubble_h > 0:
            new_h += bubble_h + 8
        if with_input:
            new_h += INPUT_AREA_H

        self._root.geometry(f"{WINDOW_W}x{new_h}+{x}+{bottom - new_h}")

    # ── Animation tick ──

    def _tick(self):
        self._pet.tick()
        anim = self._pet.get_animation()

        state_name = anim.state.value
        frame = self._sprites.get_frame(state_name, anim.frame_index)
        if frame:
            self._photo = ImageTk.PhotoImage(frame)
            self._pet_label.config(image=self._photo)

        self._root.after(FRAME_MS, self._tick)

    # ── State change handler ──

    def _on_pet_state_change(self):
        state = self._pet.get_animation().state
        state_name = state.value
        x = self._root.winfo_x()
        bottom = self._root.winfo_y() + self._root.winfo_height()

        # Pick random sprite sheet for states with multiple options
        self._sprites.pick_random(state_name)

        if state == PetState.RESTING:
            self._cancel_auto_rest()
            self._cancel_alert_dismiss()
            self._chat_mode = False
            self._bubble_canvas.pack_forget()
            self._input_canvas.pack_forget()
            new_h = H_RESTING
            self._root.geometry(f"{WINDOW_W}x{new_h}+{x}+{bottom - new_h}")
            self._update_status("zzZ")

        elif state == PetState.ALERT:
            # Notification bubble visible, no input bar
            self._cancel_auto_rest()
            self._input_canvas.pack_forget()
            # bubble already drawn by show_alert before state change
            self._schedule_alert_dismiss()

        elif state == PetState.GREETING:
            self._cancel_auto_rest()
            self._input_canvas.pack(pady=(4, 8))
            if self._bubble_total_h > 0:
                self._set_window_height(bubble_h=self._bubble_total_h, with_input=True)
            self._update_status("Daily chat")

        elif state == PetState.AWAKE:
            self._cancel_auto_rest()
            self._bubble_canvas.pack_forget()
            self._input_canvas.pack(pady=(4, 8))
            new_h = H_AWAKE
            self._root.geometry(f"{WINDOW_W}x{new_h}+{x}+{bottom - new_h}")
            self._entry.delete(0, tk.END)
            self._entry.config(state=tk.NORMAL)
            self._send_btn.config(state=tk.NORMAL)
            self._update_status("Ask me anything!")
            self._root.after(100, lambda: self._entry.focus_set())

        elif state == PetState.THINKING:
            self._cancel_auto_rest()
            self._input_canvas.pack_forget()
            bubble_h = self._update_bubble("Thinking...")
            self._set_window_height(bubble_h=bubble_h)
            self._update_status("Hmm...")

        elif state == PetState.REPLY:
            # Layout handled by _show_answer — just update status here
            self._update_status("Ask more, or Esc to close")

        elif state == PetState.IDLE_CHAT:
            self._cancel_auto_rest()
            self._input_canvas.pack(pady=(4, 8))
            if self._bubble_total_h > 0:
                self._set_window_height(bubble_h=self._bubble_total_h, with_input=True)
            self._update_status("Keep chatting")

    # ── Public API ──

    def show(self, image: Image.Image | None = None, window_title: str = ""):
        self._image = image
        self._window_title = window_title
        if self._root:
            self._root.after(0, self._do_show)

    def show_notice(
        self,
        text: str,
        hint: str = "",
        status: str = "",
        pet_state: PetState | None = None,
    ):
        if self._root:
            self._root.after(
                150, lambda: self._do_show_notice(text, hint, status, pet_state)
            )

    def _do_show(self):
        self._chat_mode = False
        self._pet.trigger("activate")

        # Reset bubble
        self._bubble_text.config(state=tk.NORMAL)
        self._bubble_text.delete("1.0", tk.END)
        self._bubble_text.config(state=tk.DISABLED)

        # Show and focus
        self._root.deiconify()
        self._root.focus_force()

    def _do_show_notice(
        self,
        text: str,
        hint: str,
        status: str,
        pet_state: PetState | None,
    ):
        self._image = None
        self._root.deiconify()
        self._root.focus_force()

        if self._pet.state == PetState.RESTING:
            if pet_state == PetState.GREETING:
                self._pet.trigger("greet")
            elif pet_state == PetState.ALERT:
                self._pet.trigger("alert")
            else:
                self._pet.trigger("activate")

        self._chat_mode = pet_state == PetState.GREETING
        bubble_h = self._update_bubble(text, hint=hint)
        self._input_canvas.pack(pady=(4, 8))
        self._entry.delete(0, tk.END)
        self._entry.config(state=tk.NORMAL)
        self._send_btn.config(state=tk.NORMAL)
        self._set_window_height(bubble_h=bubble_h, with_input=True)
        if status:
            self._update_status(status)
        self._root.after(100, lambda: self._entry.focus_set())

    # ── Proactive alert API ──

    def show_alert(self, title: str, body: str, hint: str = "Click to respond · Esc dismiss"):
        """Proactive notification — only interrupts when RESTING."""
        if self._root:
            self._root.after(0, lambda: self._do_show_alert(title, body, hint))

    def _do_show_alert(self, title: str, body: str, hint: str):
        if self._pet.state != PetState.RESTING:
            return  # don't interrupt active conversation

        # Draw bubble before entering ALERT state
        bubble_h = self._update_bubble(body, hint=hint)
        self._input_canvas.pack_forget()
        self._set_window_height(bubble_h=bubble_h)
        self._update_status(title)

        self._root.deiconify()
        self._pet.trigger("alert")

    def _schedule_alert_dismiss(self):
        self._cancel_alert_dismiss()
        if self._root:
            self._alert_after_id = self._root.after(
                ALERT_DISMISS_MS, self._dismiss
            )

    def _cancel_alert_dismiss(self):
        if self._root and self._alert_after_id:
            self._root.after_cancel(self._alert_after_id)
            self._alert_after_id = None

    # ── Dismiss / hide ──

    def _dismiss(self):
        self._cancel_auto_rest()
        self._cancel_alert_dismiss()
        self._chat_mode = False
        self._pet.trigger("dismiss")

    # ── Input handling ──

    def _on_enter(self, event):
        question = self._entry.get().strip()
        if not question:
            return

        self._cancel_auto_rest()
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
            self._root.after(0, self._show_answer, f"Error: {e}")

    def _show_answer(self, answer):
        reply_event = "chat_answer" if self._chat_mode else "answer"
        self._pet.trigger(reply_event)

        # Draw auto-sized bubble with answer
        hint = "Esc close \u00b7 Enter follow-up"
        if self._chat_mode:
            hint = "Esc close \u00b7 Enter continue chatting"
        bubble_h = self._update_bubble(answer, hint=hint)

        # Show input for follow-up
        self._input_canvas.pack(pady=(4, 8))
        self._entry.delete(0, tk.END)
        self._entry.config(state=tk.NORMAL)
        self._send_btn.config(state=tk.NORMAL)

        self._set_window_height(bubble_h=bubble_h, with_input=True)
        self._root.after(100, lambda: self._entry.focus_set())
        self._schedule_auto_rest()

    def _on_entry_activity(self, _event):
        # User started interacting after a reply; don't auto-dismiss this turn.
        self._cancel_auto_rest()

    def _schedule_auto_rest(self):
        self._cancel_auto_rest()
        if self._root:
            self._idle_after_id = self._root.after(AUTO_REST_MS, self._dismiss)

    def _cancel_auto_rest(self):
        if self._root and self._idle_after_id:
            self._root.after_cancel(self._idle_after_id)
            self._idle_after_id = None

    # ── Drag to move ──

    def _drag_start(self, event):
        self._drag_moved = False
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _drag_move(self, event):
        self._drag_moved = True
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{x}+{y}")

    def _on_pet_click(self, _event):
        # Drag release should not activate.
        if self._drag_moved:
            return

        state = self._pet.get_animation().state

        # Click during ALERT → wake up to respond
        if state == PetState.ALERT:
            self._cancel_alert_dismiss()
            self._pet.trigger("activate")
            return

        # Click-to-wake only when resting
        if state != PetState.RESTING:
            return

        if self._on_activate:
            threading.Thread(target=self._on_activate, daemon=True).start()
        else:
            self._do_show()
