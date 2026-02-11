"""Screenshot capture using mss for speed and win32gui for active window detection."""

import ctypes
from ctypes import wintypes

import mss
from PIL import Image

# Win32 API bindings
user32 = ctypes.windll.user32


def get_active_hwnd(skip_hwnd: int = 0) -> int:
    """Return the handle of the foreground window.

    If skip_hwnd is set and the foreground window matches it,
    walk the Z-order to find the next visible, appropriately-sized window.
    """
    hwnd = user32.GetForegroundWindow()
    if skip_hwnd and hwnd == skip_hwnd:
        GW_HWNDNEXT = 2
        candidate = user32.GetWindow(hwnd, GW_HWNDNEXT)
        while candidate:
            if user32.IsWindowVisible(candidate):
                rect = wintypes.RECT()
                user32.GetWindowRect(candidate, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 200 and h > 200:
                    return candidate
            candidate = user32.GetWindow(candidate, GW_HWNDNEXT)
    return hwnd


def get_window_title(hwnd: int = 0) -> str:
    """Return the title of a window. If hwnd=0, uses the foreground window."""
    if not hwnd:
        hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


# Keep old name working
get_active_window_title = get_window_title


def get_window_rect(hwnd: int = 0) -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of a window. If hwnd=0, uses foreground."""
    if not hwnd:
        hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


# Keep old name working
get_active_window_rect = get_window_rect


def capture_window(hwnd: int = 0) -> Image.Image | None:
    """Capture a specific window by handle. If hwnd=0, uses foreground window."""
    rect = get_window_rect(hwnd)
    if rect is None:
        return None

    left, top, right, bottom = rect
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


# Keep old name working
capture_active_window = capture_window


def capture_full_screen(monitor_index: int = 0) -> Image.Image:
    """Capture a screen.

    Args:
        monitor_index: 0 = all monitors combined, 1 = primary, 2 = second, ...
    """
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
