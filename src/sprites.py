"""Sprite sheet loader for the Shiba pet — 4x4 grid PNGs."""

import logging
import random
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "shiba"

GRID_COLS = 4
GRID_ROWS = 4
FRAME_COUNT = GRID_COLS * GRID_ROWS  # 16

# Map state name → folder name
STATE_FOLDERS = {
    "resting":  "resting",
    "greeting": "greeting",
    "alert":    "alert",
    "awake":    "awake",
    "thinking": "thinking",
    "reply":    "reply",
    "idle_chat": "idle_chat",
}

STATE_FALLBACKS = {
    "greeting": "awake",
    "alert": "awake",
    "idle_chat": "reply",
}


def _cut_frames(sheet: Image.Image, target_size: int) -> list[Image.Image]:
    """Cut a 4x4 sprite sheet into 16 individual frames, scaled to target_size."""
    fw = sheet.width // GRID_COLS
    fh = sheet.height // GRID_ROWS

    frames = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
            frame = sheet.crop(box)
            if frame.size != (target_size, target_size):
                frame = frame.resize((target_size, target_size), Image.LANCZOS)
            frames.append(frame)
    return frames


class SpriteManager:
    """Preloads all sprite sheets and provides frames per state."""

    def __init__(self, frame_size: int = 128, chroma: tuple = (0, 255, 0)):
        self._frame_size = frame_size
        self._chroma = chroma
        # state_name → list of frame-lists (one per sheet)
        self._sheets: dict[str, list[list[Image.Image]]] = {}
        # state_name → index of currently active sheet
        self._active: dict[str, int] = {}
        self._load_all()

    def _load_all(self):
        for state, folder in STATE_FOLDERS.items():
            folder_path = ASSETS_DIR / folder
            if not folder_path.exists():
                logger.warning("Sprite folder missing: %s", folder_path)
                continue

            pngs = sorted(folder_path.glob("*.png"))
            if not pngs:
                logger.warning("No PNGs in %s", folder_path)
                continue

            sheet_list = []
            for png_path in pngs:
                sheet = Image.open(png_path).convert("RGBA")
                raw_frames = _cut_frames(sheet, self._frame_size)
                # Hard alpha threshold onto chroma — avoids green fringing
                processed = []
                for f in raw_frames:
                    alpha = f.split()[3]
                    mask = alpha.point(lambda a: 255 if a >= 128 else 0)
                    bg = Image.new("RGB", f.size, self._chroma)
                    bg.paste(f.convert("RGB"), (0, 0), mask)
                    processed.append(bg)
                sheet_list.append(processed)

            self._sheets[state] = sheet_list
            self._active[state] = 0
            logger.info("Loaded %d sprite sheet(s) for '%s'", len(sheet_list), state)

        for state, fallback in STATE_FALLBACKS.items():
            if self._sheets.get(state):
                continue
            fallback_sheets = self._sheets.get(fallback)
            if not fallback_sheets:
                continue
            self._sheets[state] = fallback_sheets
            self._active[state] = 0
            logger.info("State '%s' falling back to '%s' sprites", state, fallback)

    def pick_random(self, state: str):
        """Pick a random sprite sheet for a state (call on state entry)."""
        sheets = self._sheets.get(state, [])
        if sheets:
            self._active[state] = random.randint(0, len(sheets) - 1)

    def get_frame(self, state: str, frame_index: int) -> Image.Image | None:
        """Get a single frame, looping automatically."""
        sheets = self._sheets.get(state, [])
        if not sheets:
            return None
        idx = self._active.get(state, 0)
        frames = sheets[idx]
        return frames[frame_index % len(frames)]

    def get_frame_count(self, state: str) -> int:
        """How many frames in the active sheet for this state."""
        sheets = self._sheets.get(state, [])
        if not sheets:
            return 0
        idx = self._active.get(state, 0)
        return len(sheets[idx])
