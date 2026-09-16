FROM python:3.12-slim

# TTF font with Czech diacritics for the PDF export
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1

EXPOSE 8000
