FROM python:3.12-slim-bookworm

ENV PythonUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
# Assuming standard setup, or just pip install .
# Since we are in the repo root, likely `pip install -e .`
COPY . .
RUN pip install -e .[dev]

# Default entrypoint
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
