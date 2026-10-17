FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY orchestrator ./orchestrator

RUN pip install --no-cache-dir .

CMD ["python", "-m", "orchestrator.worker"]
