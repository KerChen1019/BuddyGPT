"""Screenshot capture using mss for speed and win32gui for active window detection."""

import ctypes
from ctypes import wintypes

import mss
from PIL import Image

# Win32 API bindings
user32 = ctypes.windll.user32


def get_active_window_rect() -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of the foreground window, or None."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def get_active_window_title() -> str:
    """Return the title of the foreground window."""
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def capture_active_window() -> Image.Image | None:
    """Capture a screenshot of the active window. Returns a PIL Image or None."""
    rect = get_active_window_rect()
    if rect is None:
        return None

    left, top, right, bottom = rect
    # Clamp to non-negative and ensure valid size
    left = max(left, 0)
    top = max(top, 0)
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None

    monitor = {"left": left, "top": top, "width": width, "height": height}
    with mss.mss() as sct:
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def capture_full_screen(monitor_index: int = 0) -> Image.Image:
    """Capture a screen.

    Args:
        monitor_index: 0 = all monitors combined, 1 = primary, 2 = second, ...
    """
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
