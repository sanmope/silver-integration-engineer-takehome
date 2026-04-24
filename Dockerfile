FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY mock_server/ ./mock_server/

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "uvicorn", "mock_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
