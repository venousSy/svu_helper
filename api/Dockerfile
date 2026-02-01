FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies from root requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Run FastAPI
# Run FastAPI (Use shell form to expand $PORT)
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
