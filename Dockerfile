# Multi-stage Dockerfile for ScrappingBot
FROM python:3.11-slim as base

# Variables d'environnement communes
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgdal-dev \
    libspatialindex-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installation de Playwright pour le scraping
RUN pip install playwright==1.47.0 && \
    playwright install chromium && \
    playwright install-deps

# Copie et installation des requirements
COPY requirements.txt requirements-llm.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage ETL
FROM base as etl
COPY database/requirements.txt ./database_requirements.txt
RUN pip install --no-cache-dir -r database_requirements.txt

# Copie du code ETL
COPY etl/ ./etl/
COPY database/ ./database/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Création des répertoires
RUN mkdir -p /app/logs /app/data /app/output

# Script d'entrée ETL
COPY docker/entrypoints/etl-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import etl; print('ETL module healthy')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "etl.orchestrator", "--mode", "api"]

# Stage Scraper
FROM base as scraper

# Copie du code scraper
COPY scrapers/ ./scrapers/
COPY config/ ./config/
COPY data/ ./data/

# Health check pour scraper
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import scrapy; print('Scraper healthy')" || exit 1

CMD ["python", "-m", "scrapy", "crawl", "real_estate_spider"]

# Stage API
FROM base as api

# Installation des dépendances API supplémentaires
RUN pip install --no-cache-dir uvicorn[standard]>=0.24.0

# Copie du code API
COPY api/ ./api/
COPY etl/ ./etl/
COPY database/ ./database/
COPY config/ ./config/

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8787"]

# Stage Chatbot/LLM
FROM base as chatbot

# Installation des dépendances LLM
RUN pip install --no-cache-dir -r requirements-llm.txt

# Copie du code chatbot
COPY extractor/ ./extractor/
COPY config/ ./config/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "extractor/main.py"]
