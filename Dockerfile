FROM python:3.13.2-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# System deps for common Python packages and curl for healthchecks
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip poetry poetry-plugin-export \
    && poetry export --without-hashes --format requirements.txt --output requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY . ./