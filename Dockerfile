FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["ticktick-mcp", "serve", "--host", "0.0.0.0", "--port", "8080"]
