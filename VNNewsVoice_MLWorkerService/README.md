# VNNewsVoice ML Worker Service

Queue-only microservice for:
- consuming `ml.tasks`
- summarizing article content
- generating TTS audio
- publishing enriched events to fanout exchange `article.events`

This project is separated from `VNNewsVoice_MLService` so the legacy ML service can remain unchanged.

## Run With uv

1. Initialize env file:
```bash
cp .env.example .env
```

2. Sync dependencies:
```bash
uv sync
```

3. Start service:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8006
```

4. Check health:
```bash
curl http://127.0.0.1:8006/health
```

## Runtime Endpoints

- `GET /`
- `GET /health`
- `GET /ops/messaging`
- `POST /admin/reload-model`

## AMQP Flow

- Consume queue: `ml.tasks`
- Publish fanout exchange: `article.events`
- Bound queues (declared on startup):
  - `article.events.rag-service`
  - `article.events.article-service`
