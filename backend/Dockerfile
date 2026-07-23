FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2, Pillow, PyTorch CPU
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install CPU-only PyTorch to keep image lean; swap for GPU wheel if needed
RUN pip install --no-cache-dir torch==2.3.0+cpu torchvision==0.18.0+cpu \
      --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
