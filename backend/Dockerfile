FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    ffmpeg \
    build-essential \
    git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python  python  /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    pip3 install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /app

COPY requirements.txt .

# Pin torch+torchaudio to 2.4.1 (CUDA 12.1 builds) BEFORE installing demucs/faster-whisper.
# torchaudio>=2.5 changed .save() to require torchcodec — this pins us to the last safe version.
# Installing from the PyTorch index first ensures demucs won't pull a newer torchaudio.
RUN pip3 install --no-cache-dir \
    torch==2.4.1 torchaudio==2.4.1 \
    --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
