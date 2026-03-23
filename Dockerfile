FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

CMD ["bash", "start.sh"]
