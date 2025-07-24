FROM --platform=linux/amd64 ubuntu:20.04

# Install all system dependencies first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.8 \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    libnss3 \
    libxcb-xtest0 \
    libxkbcommon0 \
    libxrandr2 \
    libcrypt1 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for libcrypt
RUN ln -s /lib/x86_64-linux-gnu/libcrypt.so.1 /lib/x86_64-linux-gnu/libcrypt.so.2

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "src/main.py"]