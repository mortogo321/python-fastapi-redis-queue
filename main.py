from fastapi import FastAPI
from redis import Redis
from rq import Queue
from pydantic import BaseModel
from job import print_number
from os import environ as env

app = FastAPI()

redis_conn = Redis(host=env['REDIS_HOST'], port=env['REDIS_PORT'], password=env['REDIS_PASSWORD'])
task_queue = Queue(env['QUEUE_NAME'], connection=redis_conn)


class JobData(BaseModel):
    lowest: int
    highest: int


@app.get('/')
def index():
    return {
        "success": True,
        "message": "Ok",
    }


@app.post("/job")
def post_job(job: JobData):
    lowest = job.lowest
    highest = job.highest
    job_instant = task_queue.enqueue(print_number, lowest, highest)

    return {
        "success": True,
        "job_id": job_instant.id
    }
