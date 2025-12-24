FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install build tool
RUN pip install --no-cache-dir hatch

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/
COPY examples/demo_app/ demo_app/

# Install dependencies and the package
RUN pip install -e .

# Default command
CMD ["python", "demo_app/manage.py", "runserver", "0.0.0.0:8000"]
