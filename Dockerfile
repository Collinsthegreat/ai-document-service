

FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder /root/.local /root/.local


COPY . .


ENV PATH=/root/.local/bin:$PATH


RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser


EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]