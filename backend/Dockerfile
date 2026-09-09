# ToDate backend + demo web client — one image, one origin.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# uv for fast, reproducible installs (matches local tooling, ADR-0002).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install deps first (better layer caching), then the app.
COPY pyproject.toml ./
COPY . .
RUN uv sync

EXPOSE 8000
CMD ["bash", "start.sh"]
