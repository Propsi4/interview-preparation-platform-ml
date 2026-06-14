FROM python:3.13.2-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir --upgrade pip poetry

# Copy dependency definition files
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --no-root --only main \
    && poetry run playwright install chromium --with-deps

# Copy application source code
COPY . ./

# Install root package (this links the `src` folder as configured in pyproject.toml)
RUN poetry install --only main

# Expose port
EXPOSE 8080

# Run the API server
CMD ["python", "-m", "src.api.main"]