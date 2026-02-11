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
    parts = [f"当前应用: {app_info.label}"]
    if app_info.url_hint:
        parts.append(f"页面: {app_info.url_hint}")
    if app_info.window_title:
        parts.append(f"窗口标题: {app_info.window_title}")

    tips = _APP_TIPS.get(app_info.app_type, "")
    if tips:
        parts.append(f"提示: {tips}")
    return "\n".join(parts)


_APP_TIPS = {
    AppType.GMAIL: "这是一封邮件，注意邮件的发件人、主题和正文内容。",
    AppType.OUTLOOK: "这是 Outlook 邮件，注意邮件的发件人、主题和正文内容。",
    AppType.BROWSER: "这是浏览器页面，关注页面的主要内容。",
    AppType.VSCODE: "这是代码编辑器，关注代码内容、文件名和错误信息。",
    AppType.TERMINAL: "这是终端/命令行，关注命令输出和错误信息。",
    AppType.SLACK: "这是 Slack 消息，注意对话内容和发送者。",
    AppType.DISCORD: "这是 Discord 消息，注意对话内容和频道。",
    AppType.EXCEL: "这是 Excel 表格，关注数据内容和公式。",
    AppType.WORD: "这是 Word 文档，关注文档内容。",
    AppType.POWERPOINT: "这是 PowerPoint 演示，关注幻灯片内容。",
    AppType.PDF_READER: "这是 PDF 文档，关注文档内容。",
}
