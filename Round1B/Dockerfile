FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache the model while we still have internet
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Offline-only inference after this point
CMD ["python", "main.py"]
