FROM python:3.12-slim

WORKDIR /code

# System dependencies (librosa aur audio processing ke liye)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

# Python libraries install karein
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

# Yahan main:app ki jagah server:app kar diya hai kyunki file ka naam server.py hai
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
