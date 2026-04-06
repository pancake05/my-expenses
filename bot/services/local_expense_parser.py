"""Local expense parser — no LLM required."""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Food": [
        "еда", "пицца", "pizza", "суши", "sushi", "роллы", "бургер", "burger",
        "шаурма", "кафе", "ресторан", "restaurant", "cafe", "обед", "ужин",
        "завтрак", "перекус", "снек", "продукт", "grocery", "магазин еды",
        "delivery", "доставка", "макдак", "макдональдс", "kfc", "домино",
        "кофе", "coffee", "чай", "tea", "пирог", "торт", "мороженое",
        "фрукт", "овощ", "мясо", "рыба", "хлеб", "молоко", "сыр",
        "sandwich", "сэндвич", "салат", "soup", "суп", "паста", "лапша",
        "ramen", "рамен", "фастфуд", "fast food", "takeaway", "скорофуд",
        "плов", "кебаб", "шашлык", "гриль", "стейк", "stake",
        "пицц",  # partial match for "пицца", "пиццу", etc.
        "ед",    # partial for "еда", "еду", etc.
    ],
    "Transport": [
        "транспорт", "такси", "taxi", "uber", "яндекс такси", "метро",
        "автобус", "бус", "tram", "трамвай", "электричка", "поезд",
        "train", "билет", "бензин", "gas", "заправка", "parking", "парковка",
        "каршеринг", "carsharing", "делимобиль", "ситидрайв", "велосипед",
        "самокат", "scooter", "bike", "проезд", "transport", "авто",
        "машина", "дорога", "штраф гибдд", "мойка", "автомойка",
        "топливо", "дт", "аи", "аи-92", "аи-95", "аи-98",
    ],
}


@dataclass
class ParsedExpense:
    amount: float
    category: str
    description: Optional[str] = None
    error: Optional[str] = None


def _detect_category(text: str) -> str:
    """Detect expense category from text."""
    text_lower = text.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return "Other"


def _extract_amount(text: str) -> Optional[float]:
    """Extract numeric amount from text."""
    # Pattern: number with optional decimal part (comma or dot as decimal separator)
    # Handles: "180", "150.50", "1 500", "1500р", "1500 руб", "руб 1500"
    patterns = [
        # Number followed by currency word: "180 рублей", "150 руб"
        r'(\d[\d\s]*[.,]?\d*)\s*(?:руб|rub|₽|\$|€|сом|тыс|k)\b',
        # Currency word followed by number: "руб 150"
        r'(?:руб|rub|₽|\$|€)\s*(\d[\d\s]*[.,]?\d*)',
        # Just a number: "180", "150.50"
        r'(\d[\d\s]*[.,]?\d*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(" ", "").replace(",", ".")
            try:
                amount = float(amount_str)
                if amount > 0:
                    return amount
            except ValueError:
                continue

    return None


def _extract_description(text: str) -> str:
    """Extract description by removing amount and currency words."""
    cleaned = text.strip()
    # Remove standalone currency words
    cleaned = re.sub(r'\b(?:руб|rub|сом|тыс|рублей|рубля)\b', '', cleaned, flags=re.IGNORECASE).strip()
    # Find and remove the amount number pattern (with optional currency suffix)
    # Match: digits with optional decimal, optional trailing whitespace, optional currency char
    cleaned = re.sub(r'\s*\d[\d\s,.]*\d?\s*[рР₽$€]?$', '', cleaned).strip()
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Remove trailing prepositions
    cleaned = re.sub(r'\s+(за|на|в|по)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else None


def parse_expense(text: str) -> Optional[ParsedExpense]:
    """Parse expense description using local heuristics."""
    text = text.strip()
    if len(text) < 2:
        return None

    amount = _extract_amount(text)
    if amount is None:
        return ParsedExpense(
            amount=0,
            category="Other",
            error="Could not determine amount"
        )

    category = _detect_category(text)
    description = _extract_description(text)

    return ParsedExpense(
        amount=amount,
        category=category,
        description=description,
    )
