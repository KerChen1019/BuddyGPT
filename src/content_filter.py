"""Crop screenshots to remove UI noise based on detected app type."""

from PIL import Image

from .app_detector import AppType, AppInfo


def _crop_ratio(img: Image.Image, left: float, top: float, right: float, bottom: float) -> Image.Image:
    """Crop image by ratios (0.0–1.0 of width/height)."""
    w, h = img.size
    box = (int(w * left), int(h * top), int(w * right), int(h * bottom))
    return img.crop(box)


# ── Per-app crop rules ──
# (left%, top%, right%, bottom%) — portion of image to KEEP

_CROP_RULES: dict[AppType, tuple[float, float, float, float]] = {
    # Gmail: skip left sidebar (~20%) and top nav (~8%)
    AppType.GMAIL:       (0.20, 0.08, 1.0, 1.0),
    # Outlook: similar to Gmail
    AppType.OUTLOOK:     (0.20, 0.08, 1.0, 1.0),
    # Browser: skip top bar (~7%), keep the rest
    AppType.BROWSER:     (0.0, 0.07, 1.0, 1.0),
    # VS Code: skip left activity bar (~4%) and top title bar (~5%)
    AppType.VSCODE:      (0.04, 0.05, 1.0, 0.95),
    # Terminal: small trim of window chrome
    AppType.TERMINAL:    (0.01, 0.04, 0.99, 0.99),
    # Slack: skip left workspace sidebar (~18%) and top bar (~6%)
    AppType.SLACK:       (0.18, 0.06, 1.0, 1.0),
    # Discord: skip left server/channel sidebar (~20%) and top bar
    AppType.DISCORD:     (0.20, 0.06, 1.0, 1.0),
    # Excel/Word/PowerPoint: skip ribbon (~15% top)
    AppType.EXCEL:       (0.0, 0.15, 1.0, 0.97),
    AppType.WORD:        (0.0, 0.15, 1.0, 0.97),
    AppType.POWERPOINT:  (0.0, 0.15, 1.0, 0.97),
    # PDF reader: light trim
    AppType.PDF_READER:  (0.0, 0.06, 1.0, 1.0),
    # File Explorer: skip nav pane (~22%) and ribbon (~12%)
    AppType.FILE_EXPLORER: (0.22, 0.12, 1.0, 1.0),
}

# Default: keep center 90%
_DEFAULT_CROP = (0.05, 0.05, 0.95, 0.95)


def filter_content(img: Image.Image, app_info: AppInfo) -> Image.Image:
    """Crop screenshot to keep only the useful content area."""
    rule = _CROP_RULES.get(app_info.app_type, _DEFAULT_CROP)
    cropped = _crop_ratio(img, *rule)

    # Don't return a tiny image if crop went wrong
    if cropped.size[0] < 100 or cropped.size[1] < 100:
        return img
    return cropped


def build_context_prompt(app_info: AppInfo) -> str:
    """Build an app-aware context string to prepend to the AI system prompt."""
    parts = [f"Active app: {app_info.label}"]
    if app_info.url_hint:
        parts.append(f"Page: {app_info.url_hint}")
    if app_info.window_title:
        parts.append(f"Window title: {app_info.window_title}")

    tips = _APP_TIPS.get(app_info.app_type, "")
    if tips:
        parts.append(f"Tip: {tips}")
    return "\n".join(parts)


_APP_TIPS = {
    AppType.GMAIL: "This is an email. Note the sender, subject, and body content.",
    AppType.OUTLOOK: "This is an Outlook email. Note the sender, subject, and body content.",
    AppType.BROWSER: "This is a browser page. Focus on the main content of the page.",
    AppType.VSCODE: "This is a code editor. Focus on code content, filenames, and error messages.",
    AppType.TERMINAL: "This is a terminal/command line. Focus on command output and error messages.",
    AppType.SLACK: "This is a Slack message. Note the conversation content and sender.",
    AppType.DISCORD: "This is a Discord message. Note the conversation content and channel.",
    AppType.EXCEL: "This is an Excel spreadsheet. Focus on data content and formulas.",
    AppType.WORD: "This is a Word document. Focus on document content.",
    AppType.POWERPOINT: "This is a PowerPoint presentation. Focus on slide content.",
    AppType.PDF_READER: "This is a PDF document. Focus on document content.",
}
