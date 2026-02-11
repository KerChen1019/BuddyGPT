"""AI assistant powered by Claude API with vision and web search."""

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from PIL import Image

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

from .prompts import SYSTEM_PROMPT, APP_PROMPTS
from .web_search import search, format_results

DEFAULT_MODEL = "claude-sonnet-4-20250514"

_IMAGE_PRESETS = {
    "terminal":  {"max_size": 800, "quality": 60},
    "vscode":    {"max_size": 900, "quality": 65},
    "excel":     {"max_size": 900, "quality": 65},
}
_DEFAULT_PRESET = {"max_size": 1024, "quality": 70}

SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Search the web for current information. Use this when you need to "
        "verify facts, look up documentation, find recent news, or when the "
        "user's question requires information you're not sure about."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
        },
        "required": ["query"],
    },
}


@dataclass
class ChatMessage:
    role: str
    text: str
    image: Image.Image | None = None


class AIAssistant:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 300,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.history: list[ChatMessage] = []
        self._app_type: str = ""

    def set_app_context(self, app_type: str):
        self._app_type = app_type

    def _get_full_system_prompt(self) -> str:
        prompt = self.system_prompt
        app_addition = APP_PROMPTS.get(self._app_type, "")
        if app_addition:
            prompt += f"\n\n## Current context\n{app_addition}"
        return prompt

    def _image_to_base64(self, img: Image.Image) -> str:
        preset = _IMAGE_PRESETS.get(self._app_type, _DEFAULT_PRESET)
        max_size = preset["max_size"]
        quality = preset["quality"]

        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        size_kb = buf.tell() / 1024
        logger.info("Image: %dx%d → %dx%d, %.0fKB (quality=%d)",
                     w, h, img.size[0], img.size[1], size_kb, quality)
        return base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    def _build_user_content(self, question: str, image: Image.Image | None = None) -> list:
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
        messages = []
        for i, msg in enumerate(self.history):
            if msg.role == "user":
                is_latest_user = (i == len(self.history) - 1) or all(
                    m.role == "assistant" for m in self.history[i + 1:]
                )
                img = msg.image if is_latest_user else None
                messages.append({
                    "role": "user",
                    "content": self._build_user_content(msg.text, img),
                })
            else:
                messages.append({
                    "role": "assistant",
                    "content": msg.text,
                })
        return messages

    def _handle_tool_call(self, response, messages: list) -> str:
        """Handle tool use responses — loop until we get a text answer."""
        max_rounds = 3

        for round_num in range(max_rounds):
            assistant_content = response.content

            # Execute all tool calls in this response
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    logger.info("Tool call [round %d]: %s(%s)",
                                round_num + 1, block.name, block.input)
                    if block.name == "web_search":
                        results = search(block.input["query"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": format_results(results),
                        })

            if not tool_results:
                break

            # Send tool results back to Claude
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            logger.info("Sending search results back to Claude (round %d)", round_num + 1)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_full_system_prompt(),
                tools=[SEARCH_TOOL],
                messages=messages,
            )

            usage = response.usage
            logger.info("Tokens (after search) — input: %d, output: %d",
                         usage.input_tokens, usage.output_tokens)

            if response.stop_reason != "tool_use":
                break

        # Extract text from final response
        text_parts = []
        for block in response.content:
            if hasattr(block, "text") and block.text:
                text_parts.append(block.text)
        return "\n".join(text_parts) if text_parts else "(No response after search)"

    def ask(self, question: str, image: Image.Image | None = None) -> str:
        self.history.append(ChatMessage(role="user", text=question, image=image))

        try:
            messages = self._build_messages()
            logger.info("Sending request (model=%s, max_tokens=%d, history=%d)",
                        self.model, self.max_tokens, len(self.history))

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_full_system_prompt(),
                tools=[SEARCH_TOOL],
                messages=messages,
            )

            usage = response.usage
            logger.info("Tokens — input: %d, output: %d", usage.input_tokens, usage.output_tokens)

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                answer = self._handle_tool_call(response, messages)
            else:
                # Normal text response
                answer = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        answer = block.text
                        break

            self.history.append(ChatMessage(role="assistant", text=answer))
            return answer

        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            self.history.pop()
            raise

    def clear_history(self):
        self.history.clear()
