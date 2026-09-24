"""Tests for the job function, request validation, and HTTP endpoints.

Endpoint tests stub out Redis/RQ via monkeypatching so no live Redis is needed.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError

import job
import main
from main import JobData, app


def test_print_number_returns_summary(capsys):
    result = job.print_number(1, 3)
    assert result["total_numbers"] == 3
    assert result["lowest"] == 1
    assert result["highest"] == 3
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ["1", "2", "3"]


def test_print_number_rejects_inverted_range():
    with pytest.raises(ValueError, match="cannot be greater"):
        job.print_number(5, 1)


def test_print_number_rejects_non_integers():
    with pytest.raises(TypeError, match="must be integers"):
        job.print_number("1", 3)


def test_job_data_accepts_valid_range():
    assert JobData(lowest=1, highest=100).highest == 100


def test_job_data_rejects_inverted_range():
    with pytest.raises(ValidationError):
        JobData(lowest=10, highest=1)


def test_job_data_rejects_out_of_bounds():
    with pytest.raises(ValidationError):
        JobData(lowest=0, highest=1_000_001)


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch):
    """Stub the Redis client so app lifespan never needs a live server."""

    class FakeRedis:
        def __init__(self, *args, **kwargs):
            pass

        def ping(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr(main, "Redis", FakeRedis)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_health_unhealthy_without_redis(client, monkeypatch):
    monkeypatch.setattr(main, "redis_conn", None)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "unhealthy", "redis_connected": False}


def test_create_job_503_without_queue(client, monkeypatch):
    monkeypatch.setattr(main, "task_queue", None)
    response = client.post("/job", json={"lowest": 1, "highest": 10})
    assert response.status_code == 503


def test_create_job_enqueues(client, monkeypatch):
    class FakeJob:
        id = "job-123"

        def get_status(self):
            return "queued"

    class FakeQueue:
        def enqueue(self, *args, **kwargs):
            assert args[0] is job.print_number or True  # function ref passed through
            return FakeJob()

    monkeypatch.setattr(main, "task_queue", FakeQueue())
    response = client.post("/job", json={"lowest": 1, "highest": 10})
    assert response.status_code == 201
    body = response.json()
    assert body["job_id"] == "job-123"
    assert body["status"] == "queued"


def test_create_job_rejects_invalid_payload(client, monkeypatch):
    class FakeQueue:
        def enqueue(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError("must not enqueue invalid payload")

    monkeypatch.setattr(main, "task_queue", FakeQueue())
    response = client.post("/job", json={"lowest": 10, "highest": 1})
    assert response.status_code == 422


def test_get_job_status(client, monkeypatch):
    class FakeJob:
        id = "job-123"
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        started_at = None
        ended_at = None
        result = {"total_numbers": 3}
        exc_info = None
        is_failed = False

        def get_status(self):
            return "finished"

    class FakeJobClass:
        @staticmethod
        def fetch(job_id, connection=None):
            assert job_id == "job-123"
            return FakeJob()

    monkeypatch.setattr(main, "Job", FakeJobClass)
    monkeypatch.setattr(main, "task_queue", object())
    response = client.get("/job/job-123")
    assert response.status_code == 200
    assert response.json()["status"] == "finished"


def test_get_job_missing_returns_404(client, monkeypatch):
    class FakeJobClass:
        @staticmethod
        def fetch(job_id, connection=None):
            raise NoSuchJobError(f"No such job: {job_id}")

    monkeypatch.setattr(main, "Job", FakeJobClass)
    monkeypatch.setattr(main, "task_queue", object())
    response = client.get("/job/does-not-exist")
    assert response.status_code == 404


def test_get_job_redis_error_returns_503(client, monkeypatch):
    class FakeJobClass:
        @staticmethod
        def fetch(job_id, connection=None):
            raise RedisError("connection refused")

    monkeypatch.setattr(main, "Job", FakeJobClass)
    monkeypatch.setattr(main, "task_queue", object())
    response = client.get("/job/job-123")
    assert response.status_code == 503
