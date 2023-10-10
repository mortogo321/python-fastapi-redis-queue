# Python FastAPI with Redis Queue
Dockernized Python FastAPI for background process via Redis Queue

## UP
```bash
docker compose -f docker/docker-compose.development.yaml up -d --build
```

## Down
```bash
docker compose -f docker/docker-compose.development.yaml down --rmi all --remove-orphans
```
