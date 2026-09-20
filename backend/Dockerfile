FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Shell form (not exec-array) so $PORT expands -- Render assigns this
# dynamically at runtime; 8000 is just the local/default fallback.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
