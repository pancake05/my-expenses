FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv pip install --system -e ".[dev]"

COPY api/ ./api/

USER 999

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
