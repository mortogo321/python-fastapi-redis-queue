# FastAPI + Redis Queue

A minimal FastAPI service demonstrating background job processing with Redis Queue (RQ): submit a job over HTTP, track its status, and fetch the result once it finishes.

## What's inside

- `POST /job` — enqueues a background job (prints numbers in a range) and returns a job ID
- `GET /job/{job_id}` — polls job status and result
- `GET /health` — reports API and Redis connection status
- A separate RQ worker process consuming the same queue
- Fully containerized: API, Redis, and worker as separate services

## Tech stack

- FastAPI, Python 3.13
- Redis + RQ (Redis Queue)
- Pydantic v2
- Docker Compose

## Quickstart

```bash
git clone git@github.com:mortogo321/python-fastapi-redis-queue.git
cd python-fastapi-redis-queue
docker compose -f docker/docker-compose.development.yaml up -d --build
```

Starts three services: `api` (port 8000), `redis` (port 6379), and `worker`.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Stop:
```bash
docker compose -f docker/docker-compose.development.yaml down --rmi all --remove-orphans
```

### Without Docker

```bash
pip install -r requirements.txt
redis-server
uvicorn main:app --reload --port 8000
rq worker task_queue   # in a separate terminal
```

## Example: create and check a job

```bash
curl -X POST http://localhost:8000/job \
  -H "Content-Type: application/json" \
  -d '{"lowest": 1, "highest": 100}'
# => {"job_id": "...", "status": "queued", ...}

curl http://localhost:8000/job/<job_id>
# => {"status": "finished", "result": {...}, ...}
```

## Structure

```
main.py             # FastAPI app and endpoints
job.py              # Background job function run by the worker
requirements.txt
docker/
├── Dockerfile
└── docker-compose.development.yaml
```

Configuration is read from environment variables (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `QUEUE_NAME`) — see `.env.development`.
