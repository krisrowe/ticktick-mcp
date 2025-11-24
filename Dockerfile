# Use a lightweight Python base image
FROM python:3.10-slim-bookworm

# Install curl, which is required for uv installation
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install uv (Rust-based Python package manager)
# Using the same curl | sh method as recommended by uv's documentation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

# Copy only requirements-like files to leverage Docker cache
# We'll use uv to install dependencies based on pyproject.toml implicit setup or explicit uv.txt
# For simplicity, we'll assume direct uv pip install from the command line after moving to /app
# If a pyproject.toml was used, uv would pick it up automatically.
# Here we just want to ensure mcp and httpx are installed.

# Copy project files
COPY . /app

# Install Python dependencies using uv directly into the container's Python environment
RUN uv pip install --system "mcp[cli]" httpx uvicorn requests python-dotenv

# Expose the port our MCP server runs on
EXPOSE 8000

# Set LOG_LEVEL environment variable
ENV LOG_LEVEL=INFO

# Set the entrypoint to run our server.py script using uvicorn
CMD ["uvicorn", "server:mcp_app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug", "--reload"]
