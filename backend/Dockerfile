FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 --create-home appuser
COPY --chown=appuser:appuser app.py database.py ./
COPY --chown=appuser:appuser algorithms ./algorithms
COPY --chown=appuser:appuser data_structures ./data_structures
USER appuser

EXPOSE 8000
CMD ["python", "app.py"]
