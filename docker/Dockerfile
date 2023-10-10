ARG PYTHON_VERSION=3.9.6

FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
