FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.22

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY supabase ./supabase

RUN uv pip install --system --no-cache .

CMD ["sh", "-c", "uvicorn slack_kb.render_app:app --host 0.0.0.0 --port ${PORT:-8080}"]
