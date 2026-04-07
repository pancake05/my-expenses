import json
import logging
import re

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

CATEGORIES = ["Food", "Transport", "Other"]

# Keyword-based category detection (primary parser)
TRANSPORT_KEYWORDS = [
    "bus", "бас", "автобус", "автобусный",
    "taxi", "такси", "uber", "убер",
    "metro", "метро", "subway", "сабвей",
    "tram", "трамвай", "трамвайный",
    "train", "поезд", "электричка", "жд",
    "fuel", "бензин", "заправка", "gas", "газ",
    "parking", "парковка", "паркинг",
    "car", "машина", "автомобиль", "таксомотор",
    "trolleybus", "троллейбус", "троллейбусный",
    "marshrutka", "маршрутка", "маршрут",
    "марш",
]

FOOD_KEYWORDS = [
    "food", "еда", "пицца", "pizza",
    "lunch", "обед", "ужин", "dinner", "завтрак", "breakfast",
    "coffee", "кофе", "tea", "чай",
    "burger", "бургер", "sandwich", "сэндвич",
    "sushi", "суши", "ролл", "роллы",
    "restaurant", "ресторан", "кафе", "cafe",
    "delivery", "доставка", "delivery",
    "grocery", "продукты", "супермаркет", "supermarket",
    "snack", "снек", "печенье", "cookie", "пирожок",
    "shawarma", "шаурма", "шаверма", "kebab", "кебаб",
    "bakery", "булочная", "пекарня",
    "stolovaya", "столовая",
    "milk", "молоко", "bread", "хлеб", "cheese", "сыр",
    "cola", "кола", "вода", "water", "напиток", "drink",
    "пельмени", "макароны", "паста", "pasta",
    "суп", "soup", "салат", "salad",
]


def _detect_category(text: str) -> str:
    """Detect category based on keywords in the input text."""
    lower = text.lower().strip()
    # Check transport first (more specific)
    for kw in TRANSPORT_KEYWORDS:
        if kw in lower:
            return "Transport"
    # Then food
    for kw in FOOD_KEYWORDS:
        if kw in lower:
            return "Food"
    return "Other"


def _extract_amount(text: str) -> float | None:
    """Extract the numeric amount from text."""
    cleaned = text.replace(",", ".")
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        return float(match.group(1))
    return None


def _extract_description(text: str) -> str:
    """Extract a description by removing the amount from text."""
    cleaned = text.replace(",", ".")
    # Remove the numeric part
    desc = re.sub(r"\s*\d+\.?\d*\s*$", "", cleaned).strip()
    return desc if desc else text


SYSTEM_PROMPT = (
    "You are an expense parsing assistant. The user types a short description of an expense.\n\n"
    "Extract the monetary amount and determine the category from: Food, Transport, Other.\n\n"
    "Category rules:\n"
    "- Food: meals, groceries, restaurants, delivery, coffee, snacks, pizza, sushi, lunch, dinner, breakfast, bakery, etc.\n"
    "- Transport: taxi, bus, metro, fuel, parking, tram, train, subway, uber, car, gas, etc.\n"
    "- Other: anything that doesn't fit Food or Transport.\n\n"
    "Rules:\n"
    "- The amount is always the numeric value in the text.\n"
    "- Use EXACTLY one of these three categories: Food, Transport, Other (case-sensitive).\n"
    "- Respond ONLY with a valid JSON object.\n\n"
    "Examples:\n"
    'Input: "bus 300" → Output: {"amount": 300, "category": "Transport", "description": "bus"}\n'
    'Input: "pizza 500" → Output: {"amount": 500, "category": "Food", "description": "pizza"}\n'
    'Input: "taxi 1200" → Output: {"amount": 1200, "category": "Transport", "description": "taxi"}\n'
    'Input: "coffee 150" → Output: {"amount": 150, "category": "Food", "description": "coffee"}\n'
    'Input: "shampoo 300" → Output: {"amount": 300, "category": "Other", "description": "shampoo"}'
)


class LLMParser:
    """Parse expense text using keywords first, with optional LLM enhancement."""

    def __init__(self):
        self.base_url = settings.llm_api_base_url
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    async def parse_expense(self, text: str) -> dict | None:
        """
        Parse expense text. Uses fast keyword-based detection as primary,
        with LLM as a fallback fallback for ambiguous cases.

        Returns dict with keys: amount (float), category (str), description (str)
        or None if parsing failed entirely.
        """
        # Primary: fast rule-based parsing
        amount = _extract_amount(text)
        if amount is None or amount <= 0:
            return None

        category = _detect_category(text)
        description = _extract_description(text)

        # Try to enhance with LLM if available (non-blocking)
        llm_result = await self._try_llm(text)
        if llm_result and llm_result.get("amount") and llm_result.get("amount") > 0:
            return {
                "amount": llm_result["amount"],
                "category": llm_result.get("category", category),
                "description": llm_result.get("description", description),
            }

        # Fallback: use keyword-based result
        return {
            "amount": amount,
            "category": category,
            "description": description,
        }

    async def _try_llm(self, text: str) -> dict | None:
        """Try LLM parsing as optional enhancement. Never raises."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.0,
                "max_tokens": 256,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"].strip()
                parsed = json.loads(content)
                amount = float(parsed.get("amount", 0))
                category = parsed.get("category", "Other")
                description = parsed.get("description", "")

                if category not in CATEGORIES:
                    category = "Other"

                if amount > 0:
                    return {"amount": amount, "category": category, "description": description}

        except Exception as e:
            logger.debug(f"LLM enhancement failed (using keyword fallback): {e}")

        return None


llm_parser = LLMParser()
