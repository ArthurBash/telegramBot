
FROM python:3.14-rc-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nano gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Elimina herramientas innecesarias
RUN apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "app.main"]