FROM python:3.11-slim

WORKDIR /app
ENV PIP_DEFAULT_TIMEOUT=300
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync
COPY . .

EXPOSE 8001