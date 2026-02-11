"""AI assistant powered by Claude API with vision support."""

import base64
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from PIL import Image

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

from .prompts import SYSTEM_PROMPT, APP_PROMPTS

DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass
class ChatMessage:
    role: str          # "user" or "assistant"
    text: str
    image: Image.Image | None = None


class AIAssistant:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 1024,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.history: list[ChatMessage] = []
        self._app_type: str = ""

    def set_app_context(self, app_type: str):
        """Set the current app type for context-aware prompting."""
        self._app_type = app_type

    def _get_full_system_prompt(self) -> str:
        prompt = self.system_prompt
        app_addition = APP_PROMPTS.get(self._app_type, "")
        if app_addition:
            prompt += f"\n\n## 当前场景\n{app_addition}"
        return prompt

    @staticmethod
    def _image_to_base64(img: Image.Image, max_size: int = 1280) -> str:
        """Resize and encode image to base64 JPEG."""
        # Resize to save tokens
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    def _build_user_content(self, question: str, image: Image.Image | None = None) -> list:
        """Build the content blocks for a user message."""
        content = []
        if image is not None:
            b64 = self._image_to_base64(image)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                },
            })
        content.append({"type": "text", "text": question})
        return content

    def _build_messages(self) -> list:
        """Convert chat history to API message format."""
        messages = []
        for msg in self.history:
            if msg.role == "user":
                messages.append({
                    "role": "user",
                    "content": self._build_user_content(msg.text, msg.image),
                })
            else:
                messages.append({
                    "role": "assistant",
                    "content": msg.text,
                })
        return messages

    def ask(self, question: str, image: Image.Image | None = None) -> str:
        """Send a question (optionally with a screenshot) and return Claude's answer."""
        self.history.append(ChatMessage(role="user", text=question, image=image))

        try:
            logger.info("Sending request to Claude API (model=%s)", self.model)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_full_system_prompt(),
                messages=self._build_messages(),
            )
            answer = response.content[0].text
            self.history.append(ChatMessage(role="assistant", text=answer))
            logger.info("Got response (%d chars)", len(answer))
            return answer

        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            self.history.pop()  # remove failed user message
            raise

    def clear_history(self):
        """Reset conversation history."""
        self.history.clear()
