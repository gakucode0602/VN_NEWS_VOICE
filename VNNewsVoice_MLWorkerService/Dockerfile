# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install AWS CLI (adapter sync) + OpenSSH (RunPod terminal access)
RUN apt-get update && apt-get install -y --no-install-recommends \
        awscli \
        openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd \
    # Secure SSH: pubkey only, no password auth
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY main.py ./main.py
COPY scripts/entrypoint.sh ./entrypoint.sh
# ^ scripts/ is excluded in .dockerignore but entrypoint.sh is explicitly allowed via !scripts/entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8006 22

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
