FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv pip install --system -e ".[dev]"

COPY bot/ ./bot/

USER 999

CMD ["python", "-m", "bot.main"]
