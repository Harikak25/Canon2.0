FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user and group
RUN groupadd -r app && useradd -r -g app appuser \
    && mkdir -p /app \
    && chown -R appuser:app /app

WORKDIR /app

# Copy requirements as non-root-owned files and install
COPY --chown=appuser:app requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code with correct ownership
COPY --chown=appuser:app app/ /app/app/

# Drop privileges
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
