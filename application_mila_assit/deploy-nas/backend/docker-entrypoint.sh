#!/bin/bash
set -e

# ============================================================================
# Entrypoint Docker pour Mila-Assist API
# ============================================================================
# Ce script s'exécute au démarrage du conteneur pour:
# 1. Corriger les permissions des volumes montés
# 2. Démarrer l'application avec l'utilisateur mila
# ============================================================================

echo "[DEMARRAGE] Démarrage de Mila-Assist API..."

# Fonction pour afficher les logs avec couleur
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# ============================================================================
# Vérifier et corriger les permissions
# ============================================================================

log_info "Vérification des permissions..."

# Répertoires critiques qui doivent être accessibles en écriture
# Architecture 4 containers: Container 2 ne gère que les logs
CRITICAL_DIRS=(
    "/app/logs"
)

# UID et GID de l'utilisateur mila (défini dans le Dockerfile)
MILA_UID=999
MILA_GID=999

for dir in "${CRITICAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "Correction des permissions pour $dir"

        # Changer le propriétaire
        chown -R ${MILA_UID}:${MILA_GID} "$dir" 2>/dev/null || {
            log_warning "Impossible de changer le propriétaire de $dir (peut-être déjà correct)"
        }

        # Assurer les permissions d'écriture
        chmod -R 775 "$dir" 2>/dev/null || {
            log_warning "Impossible de changer les permissions de $dir"
        }

        log_success "✓ $dir configuré"
    else
        log_warning "$dir n'existe pas, création..."
        mkdir -p "$dir"
        chown ${MILA_UID}:${MILA_GID} "$dir"
        chmod 775 "$dir"
        log_success "✓ $dir créé"
    fi
done

# ============================================================================
# Vérifier la connectivité avec les dépendances
# ============================================================================

log_info "Vérification des dépendances..."

# Container 2 (API Backend) dépend de:
# - Container 1 (MySQL) - vérifié via healthcheck docker-compose
# - Container 3 (LLM+FAISS) - vérifié via healthcheck docker-compose

log_success "✓ Vérifications terminées (healthchecks gérés par docker-compose)"

# ============================================================================
# Démarrer l'application
# ============================================================================

log_info "Démarrage de l'application avec l'utilisateur mila (uid=${MILA_UID})..."

# Exécuter la commande passée en argument (uvicorn) avec l'utilisateur mila
exec gosu mila "$@"
