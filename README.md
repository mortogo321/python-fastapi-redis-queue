# Python FastAPI with Redis Queue

Modern FastAPI application with Redis Queue for background job processing. Built with Python 3.13, FastAPI 0.115.6, and the latest dependencies.

## Features

- **FastAPI 0.115.6** - Modern async web framework
- **Python 3.13** - Latest Python version with performance improvements
- **Redis Queue (RQ)** - Background job processing
- **Pydantic v2** - Data validation and settings management
- **Type Safety** - Full type hints throughout the codebase
- **Health Checks** - Monitor Redis connection status
- **Job Tracking** - Query job status and results
- **Docker Support** - Fully containerized application

## Project Structure

```
.
├── main.py                 # FastAPI application with endpoints
├── job.py                  # Background job worker functions
├── requirements.txt        # Python dependencies
├── .env.development       # Environment variables
└── docker/
    ├── Dockerfile         # Container image definition
    └── docker-compose.development.yaml  # Docker Compose config
```

## Quick Start

### Start the Application

```bash
docker compose -f docker/docker-compose.development.yaml up -d --build
```

This will start three services:
- **api** - FastAPI application on port 8000
- **redis** - Redis server on port 6379
- **worker** - RQ worker for background jobs

### Stop the Application

```bash
docker compose -f docker/docker-compose.development.yaml down --rmi all --remove-orphans
```

## API Endpoints

### Root
```bash
GET /
```
Returns API information and version.

### Health Check
```bash
GET /health
```
Check Redis connection status.

**Response:**
```json
{
  "status": "healthy",
  "redis_connected": true
}
```

### Create Job
```bash
POST /job
Content-Type: application/json

{
  "lowest": 1,
  "highest": 100
}
```
Creates a background job to print numbers from `lowest` to `highest`.

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Job created to print numbers from 1 to 100"
}
```

### Get Job Status
```bash
GET /job/{job_id}
```
Retrieve the status and results of a job.

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "finished",
  "created_at": "2025-10-31T15:30:00",
  "started_at": "2025-10-31T15:30:01",
  "ended_at": "2025-10-31T15:30:05",
  "result": {
    "status": "completed",
    "lowest": 1,
    "highest": 100,
    "total_numbers": 100,
    "message": "Successfully printed 100 numbers from 1 to 100"
  },
  "exc_info": null
}
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Environment variables are defined in `.env.development`:

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=mQINBF9FWioBEADfBiOE
QUEUE_NAME=task_queue
```

## Development

### Requirements

- Docker & Docker Compose
- Python 3.13+ (for local development)

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis:
```bash
redis-server
```

3. Run the API:
```bash
uvicorn main:app --reload --port 8000
```

4. Run the worker:
```bash
rq worker task_queue
```

## Version History

### v2.0.0 (2025)
- Upgraded to Python 3.13
- Updated all dependencies to latest versions
- Added health check endpoint
- Added job status tracking endpoint
- Implemented proper lifecycle management
- Added comprehensive logging
- Full type hints and validation
- Improved error handling

### v1.0.0 (2023)
- Initial release
