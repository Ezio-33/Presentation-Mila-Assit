# ===================================================================
# Dockerfile - Mila-Assist API Backend (Container 2)
# Architecture: 4 Containers (9 Déc 2025)
# Base: Python 3.10 slim (optimisé pour taille et performance)
# Contient: FastAPI, MySQL connector, HTTP client vers Container 3
# ===================================================================

# =======================
# Stage 1: Builder
# =======================
FROM python:3.10-slim as builder

# Métadonnées
LABEL maintainer="Mila-Assist <support@mila-assist.local>"
LABEL description="Chatbot IA avec RAG pour support AI_licia et streaming"
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
    APP_HOME=/app

# Installer uniquement les libs runtime nécessaires + gosu pour switch d'utilisateur
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copier l'environnement virtuel depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Créer l'utilisateur non-root pour sécurité
RUN groupadd -r mila && \
    useradd -r -g mila -d /app -s /sbin/nologin -c "Mila Assistant User" mila

# Créer la structure de dossiers
WORKDIR /app
RUN mkdir -p \
    /app/src \
    /app/frontend \
    /app/logs

# Copier le code source
COPY --chown=mila:mila src/ /app/src/

# Copier le script d'entrypoint (avec permissions root)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Créer un fichier de version
RUN echo "1.0.0" > /app/VERSION

# Permissions
RUN chown -R mila:mila /app && \
    chmod -R 755 /app/src && \
    chmod -R 777 /app/logs

# Exposer le port de l'API
EXPOSE 8000

# Health check interne
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/sante || exit 1

# Point d'entrée avec script qui gère les permissions puis switch vers mila
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Commande par défaut (sera exécutée par l'entrypoint avec l'utilisateur mila)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]

# ===================================================================
# Notes de construction
# ===================================================================
# Build:
#   docker build -t mila-assist-api:latest -f backend/Dockerfile backend/
#
# Run standalone:
#   docker run -d -p 8000:8000 \
#     -e MYSQL_HOST=mysql \
#     -e MYSQL_USER=mila_user \
#     -e MYSQL_PASSWORD=password \
#     --name mila-api \
#     mila-assist-api:latest
#
# Taille image estimée: ~2.5 Go (Python + ML libs)
# ===================================================================
