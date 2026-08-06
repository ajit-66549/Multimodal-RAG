FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
