FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=8082 \
    DATASET_DIR=/data/dataset \
    WRITE_DIR=/data/written \
    LOG_DIR=/logs

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh src/make_dataset.py

EXPOSE 8082
ENTRYPOINT ["./docker-entrypoint.sh"]