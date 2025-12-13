FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

COPY --from=cloudflare/cloudflared:latest /usr/local/bin/cloudflared /usr/local/bin/cloudflared

COPY main.py api.py logs.py ./

RUN uv pip install --system --no-cache \
    requests \
    watchdog

RUN chmod +x main.py

CMD ["python", "/app/main.py"]