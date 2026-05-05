FROM python:3.11-slim

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Cache layer: install dependencies without source code
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Remove development-only torch assets that are not needed at runtime.
RUN rm -rf \
    /app/.venv/lib/python3.11/site-packages/torch/test \
    /app/.venv/lib/python3.11/site-packages/torch/include

# Copy only runtime files needed by the service
COPY app ./app
COPY workers ./workers
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
