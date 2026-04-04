import asyncio
import json
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, LLM_MODEL, VISION_DETAIL, MAX_RESPONSE_CHARS
from agent.tools import MCPToolManager

SYSTEM_PROMPT = f"""Ты — персональный ассистент-проводник по ресторанам Алматы.
Помогаешь найти рестораны, кафе, бары, узнать о скидках и акциях.
Отвечай на русском. Используй инструменты для поиска реальных данных.
Держи ответы краткими — не более {MAX_RESPONSE_CHARS} символов (15-30 секунд речи).

Если пользователь отправляет фото еды — опиши блюдо и предложи подходящие рестораны.
Если пользователь просит оценить ресторан по фото (интерьер, вывеска, зал) — \
используй инструмент analyze_restaurant_photo для структурированной оценки."""

CRITIC_PROMPT = """Analyze this restaurant photo. Determine:
1. level: one of "fastfood", "casual", "mid-range", "fine dining"
2. status: one of "family", "romantic", "business", "youth"
3. description: 1-2 sentence description of the atmosphere (in Russian)
4. confidence: 0.0-1.0

Return ONLY valid JSON: {"level": "...", "status": "...", "description": "...", "confidence": 0.0}"""

ANALYZE_PHOTO_TOOL = "analyze_restaurant_photo"

_CUSTOM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": ANALYZE_PHOTO_TOOL,
            "description": (
                "Analyze the restaurant photo that the user just sent "
                "to determine establishment level, status, and atmosphere. "
                "Call this when the user asks to evaluate/rate a restaurant "
                "based on its photo (interior, exterior, signage)."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]


class RestaurantAgent:
    def __init__(self, tool_manager: MCPToolManager):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.tool_manager = tool_manager
        self.history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._tools = tool_manager.get_openai_tools() + _CUSTOM_TOOLS

    async def chat(self, user_text: str, image_url: str | None = None) -> str:
        """Process user message (text + optional image), return agent response."""
        content: list[dict] = []
        if user_text:
            content.append({"type": "text", "text": user_text})
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url, "detail": VISION_DETAIL},
            })

        if not content:
            return "Пожалуйста, отправьте текст, фото или аудио."

        self.history.append({"role": "user", "content": content})

        while True:
            response = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=self.history,
                tools=self._tools,
            )

            message = response.choices[0].message
            self.history.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return message.content or ""

            tool_results = await asyncio.gather(
                *(self._execute_tool(tc, image_url) for tc in message.tool_calls)
            )
            self.history.extend(tool_results)

    async def _execute_tool(self, tool_call, image_url: str | None) -> dict:
        """Execute a single tool call, return the tool message for history."""
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if fn_name == ANALYZE_PHOTO_TOOL:
            result_str = await self._analyze_restaurant_photo(image_url)
        else:
            result_str = await self.tool_manager.call_tool(fn_name, fn_args)

        return {"role": "tool", "tool_call_id": tool_call.id, "content": result_str}

    async def _analyze_restaurant_photo(self, image_url: str | None) -> str:
        """Vision-based restaurant critic. Returns JSON: {level, status, description, confidence}"""
        if not image_url:
            return json.dumps({
                "level": "unknown",
                "status": "unknown",
                "description": "Фото не предоставлено",
                "confidence": 0.0,
            })

        response = await self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CRITIC_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": VISION_DETAIL},
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content or "{}"
