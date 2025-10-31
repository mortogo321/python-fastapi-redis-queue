from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis import Redis
from rq import Queue
from rq.job import Job

from job import print_number


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env.development",
        case_sensitive=False,
        extra="ignore"
    )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str
    queue_name: str = "default"


# Global settings instance
settings = Settings()

# Global connections
redis_conn: Redis | None = None
task_queue: Queue | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - setup and teardown."""
    global redis_conn, task_queue

    # Startup: Initialize Redis connection and queue
    redis_conn = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_keepalive=True,
    )
    task_queue = Queue(settings.queue_name, connection=redis_conn)

    # Test connection
    try:
        redis_conn.ping()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Redis: {e}")

    yield

    # Shutdown: Close connections
    if redis_conn:
        redis_conn.close()


app = FastAPI(
    title="FastAPI Redis Queue",
    description="Background job processing with Redis Queue",
    version="2.0.0",
    lifespan=lifespan,
)


class JobData(BaseModel):
    """Job data model with validation."""

    lowest: int = Field(..., ge=0, le=1_000_000, description="Lowest number in range")
    highest: int = Field(..., ge=0, le=1_000_000, description="Highest number in range")

    @field_validator("highest")
    @classmethod
    def validate_range(cls, highest: int, info) -> int:
        """Ensure highest is greater than or equal to lowest."""
        if "lowest" in info.data and highest < info.data["lowest"]:
            raise ValueError("highest must be greater than or equal to lowest")
        return highest


class JobResponse(BaseModel):
    """Standardized job response."""

    success: bool
    job_id: str
    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    redis_connected: bool


@app.get("/", response_model=dict[str, Any])
async def index() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "success": True,
        "message": "FastAPI Redis Queue API",
        "version": "2.0.0",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint to verify Redis connection."""
    redis_connected = False

    if redis_conn:
        try:
            redis_conn.ping()
            redis_connected = True
        except Exception:
            pass

    return HealthResponse(
        status="healthy" if redis_connected else "unhealthy",
        redis_connected=redis_connected,
    )


@app.post("/job", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobData) -> JobResponse:
    """
    Create a new background job to print numbers in range.

    Args:
        job_data: Job parameters with lowest and highest range

    Returns:
        JobResponse with job ID and status

    Raises:
        HTTPException: If queue is not available
    """
    if not task_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue is not available",
        )

    try:
        job_instance: Job = task_queue.enqueue(
            print_number,
            job_data.lowest,
            job_data.highest,
            job_timeout="10m",
            result_ttl=3600,
            failure_ttl=86400,
        )

        return JobResponse(
            success=True,
            job_id=job_instance.id,
            status=job_instance.get_status(),
            message=f"Job created to print numbers from {job_data.lowest} to {job_data.highest}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        )


@app.get("/job/{job_id}", response_model=dict[str, Any])
async def get_job_status(job_id: str) -> dict[str, Any]:
    """
    Get the status of a specific job.

    Args:
        job_id: The ID of the job to check

    Returns:
        Job status information

    Raises:
        HTTPException: If job not found or queue unavailable
    """
    if not task_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue is not available",
        )

    try:
        job = Job.fetch(job_id, connection=redis_conn)

        return {
            "success": True,
            "job_id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
            "exc_info": job.exc_info if job.is_failed else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {str(e)}",
        )
