# ===================================================================
# Dockerfile - Mila-Assist LLM + FAISS Service (Container 3)
# Base: Python 3.10 slim (optimisé pour taille et performance)
# Contient: FAISS, Gemma-2-2B Q4, Auto-sync, sentence-transformers
# ===================================================================

# =======================
# Stage 1: Builder
# =======================
FROM python:3.10-slim as builder

# Métadonnées
LABEL maintainer="Mila-Assist <support@mila-assist.local>"
LABEL description="Service LLM+FAISS dédié avec auto-sync pour Mila-Assist"
LABEL version="1.0.0"

# Variables d'environnement pour build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système nécessaires pour compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    gcc \
    git \
    wget \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Créer un environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier et installer les dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt

# =======================
# Stage 2: Runtime
# =======================
FROM python:3.10-slim

# Variables d'environnement pour runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    TRANSFORMERS_CACHE=/app/cache_huggingface \
    HF_HOME=/app/cache_huggingface

# Installer uniquement les libs runtime nécessaires + gosu pour switch d'utilisateur
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copier l'environnement virtuel depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Créer l'utilisateur non-root pour sécurité (UID=1027 pour match Synology NAS admin)
RUN groupadd -g 1027 llm && \
    useradd -u 1027 -g llm -d /app -s /sbin/nologin -c "LLM Service User" llm

# Créer la structure de dossiers
WORKDIR /app
RUN mkdir -p \
    /app/src \
    /app/modeles/embeddings \
    /app/modeles/gemma \
    /app/donnees/faiss_index \
    /app/logs \
    /app/cache_huggingface

# Copier le code source
COPY --chown=llm:llm src/ /app/src/

# Créer un fichier de version
RUN echo "1.0.0" > /app/VERSION

# Permissions
RUN chown -R llm:llm /app && \
    chmod -R 755 /app/src && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/donnees/faiss_index && \
    chmod -R 777 /app/cache_huggingface

# Exposer le port de l'API interne (8001)
EXPOSE 8001

# Health check interne
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Passer à l'utilisateur non-root
USER llm

# Commande par défaut : Lancer le serveur FastAPI avec auto-sync en background
# 2 workers : 1 pour les requêtes de recherche, 1 pour le healthcheck
CMD ["uvicorn", "src.llm_server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--log-level", "info"]

# ===================================================================
# Notes de construction
# ===================================================================
# Build:
#   docker build -t mila-llm-service:latest -f llm-service/Dockerfile llm-service/
#
# Run standalone:
#   docker run -d -p 8001:8001 \
#     -e MYSQL_HOST=mysql \
#     -e MYSQL_USER=mila_user \
#     -e MYSQL_PASSWORD=password \
#     -v ./modeles:/app/modeles \
#     -v ./donnees:/app/donnees \
#     --name mila-llm-faiss \
#     mila-llm-service:latest
#
# Taille image estimée: ~3.2 Go (Python + FAISS + LLM + transformers)
# ===================================================================
