FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m patchright install chromium
COPY main.py .

CMD ["python", "main.py"]
