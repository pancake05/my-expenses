import httpx
import json
import logging
from typing import Optional
from dataclasses import dataclass

from bot.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expense parsing assistant. The user describes their expense in natural language (Russian or English).
Your task is to extract:
1. **amount** — the numeric amount spent (float, positive number)
2. **category** — one of: "Food", "Transport", "Other"
3. **description** — optional short description (can be null)

Rules:
- Map expenses to categories:
  - "Food" — meals, groceries, restaurants, delivery food, snacks, drinks (non-alcoholic)
  - "Transport" — taxi, bus, metro, gas, parking, train tickets
  - "Other" — everything else (entertainment, shopping, subscriptions, etc.)
- If amount is in a different currency, extract the number as-is (do not convert)
- Return ONLY valid JSON in this exact format, nothing else:
{"amount": 500.0, "category": "Food", "description": "pizza"}
- If you cannot determine the amount, return: {"error": "Could not determine amount"}
- If you cannot determine the category, use "Other"
"""


@dataclass
class ParsedExpense:
    amount: float
    category: str
    description: Optional[str] = None
    error: Optional[str] = None


class LLMExpenseParser:
    """Parses expense descriptions using LLM via OpenAI-compatible API."""

    def __init__(self):
        self.base_url = settings.llm_api_base_url
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    @property
    def is_available(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def parse(self, text: str) -> Optional[ParsedExpense]:
        if not self.is_available:
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 256,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

            if response.status_code != 200:
                logger.error(f"LLM API error: {response.status_code} — {response.text}")
                return None

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Extract JSON from possible markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n", 1)[0]
                content = content.removeprefix("json").strip()

            parsed = json.loads(content)

            if "error" in parsed:
                return ParsedExpense(amount=0, category="Other", error=parsed["error"])

            return ParsedExpense(
                amount=float(parsed.get("amount", 0)),
                category=parsed.get("category", "Other").capitalize(),
                description=parsed.get("description"),
            )

        except (json.JSONDecodeError, KeyError, IndexError, httpx.RequestError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None


llm_parser = LLMExpenseParser()
