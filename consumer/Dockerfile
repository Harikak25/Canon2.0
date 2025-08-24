FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install dependencies as root so uvicorn is available in PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user and switch
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser /app
USER appuser

# Copy application code
COPY --chown=appuser:appuser app app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
