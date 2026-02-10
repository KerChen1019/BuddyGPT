"""Global hotkey listener using pynput (no admin rights needed)."""

import threading
from pynput import keyboard


DEFAULT_HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.Key.space}
QUIT_HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_vk(0x51)}  # Q


class HotkeyManager:
    def __init__(self, hotkey: set | None = None, quit_hotkey: set | None = None):
        self.hotkey = hotkey or DEFAULT_HOTKEY
        self.quit_hotkey = quit_hotkey or QUIT_HOTKEY
        self._callbacks: list = []
        self._quit_callbacks: list = []
        self._pressed: set = set()
        self._listener: keyboard.Listener | None = None
        self._stop_event = threading.Event()

    def on_activate(self, callback):
        self._callbacks.append(callback)

    def on_quit(self, callback):
        self._quit_callbacks.append(callback)

    def _fire(self):
        for cb in self._callbacks:
            cb()

    def _fire_quit(self):
        for cb in self._quit_callbacks:
            cb()
        self._stop_event.set()

    def _on_press(self, key):
        k = self._normalize(key)
        self._pressed.add(k)
        if self.quit_hotkey.issubset(self._pressed):
            self._fire_quit()
        elif self.hotkey.issubset(self._pressed):
            self._fire()

    def _on_release(self, key):
        k = self._normalize(key)
        self._pressed.discard(k)

    def _normalize(self, key):
        """Normalize keys so left/right modifiers match, and letter keys
        always compare by virtual-key code regardless of held modifiers."""
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return keyboard.Key.ctrl_l
        if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            return keyboard.Key.shift
        if isinstance(key, keyboard.KeyCode):
            if key.vk is not None:
                return keyboard.KeyCode.from_vk(key.vk)
            if key.char is not None:
                return keyboard.KeyCode.from_vk(ord(key.char.upper()))
        return key

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def wait(self):
        """Block until quit hotkey is pressed."""
        self._stop_event.wait()
