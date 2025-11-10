FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY src/ /app/src/
RUN pip install --no-cache-dir requests flask
ENTRYPOINT ["python3", "/app/src/gptlinux5.py"]
