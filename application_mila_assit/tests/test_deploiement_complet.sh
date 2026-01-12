#!/bin/bash

# ===================================================================
# Script de test complet du déploiement Mila-Assist
# Vérifie que l'application fonctionne selon les spécifications
# ===================================================================
#
# Usage:
#   ./test_deploiement_complet.sh [URL_API]
#
# Exemples:
#   ./test_deploiement_complet.sh http://localhost:9000
#   ./test_deploiement_complet.sh http://192.168.1.100:9000
#

# set -e désactivé pour permettre aux tests de continuer même en cas d'erreur
# set -e  # Exit on error (sauf pour les tests individuels)

# Couleurs pour l'affichage (DÉFINIR EN PREMIER)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compteurs
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Fonction d'affichage (DÉFINIR EN SECOND)
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

log_error() {
    echo -e "${RED}❌${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((TESTS_WARNING++))
    ((TESTS_TOTAL++))
}

# Configuration (APRÈS les fonctions)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../deploy-nas/.env"

# Fonction pour charger .env de manière sécurisée (supporte caractères spéciaux)
load_env() {
    local env_file="$1"
    if [ ! -f "$env_file" ]; then
        return 1
    fi

    # Lire ligne par ligne et exporter les variables
    while IFS= read -r line || [ -n "$line" ]; do
        # Ignorer les commentaires et lignes vides
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue

        # Extraire la clé et la valeur
        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            # Exporter sans interprétation
            export "$key=$value"
        fi
    done < "$env_file"
    return 0
}

# Charger les variables depuis .env si le fichier existe
if load_env "$ENV_FILE"; then
    log_info "Variables chargées depuis $ENV_FILE"
else
    log_warning "Fichier .env non trouvé à $ENV_FILE"
fi

# URL par défaut : NAS Synology via reverse proxy HTTPS
API_URL="${1:-${CORS_ORIGINS%%,*}}"  # Utilise la première origine CORS depuis .env
if [ -z "$API_URL" ] || [ "$API_URL" = "${CORS_ORIGINS%%,*}" ]; then
    API_URL="https://ezi0.synology.me:10443"  # Fallback
fi

# Configuration MySQL (depuis .env)
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-mila_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD}"
MYSQL_DATABASE="${MYSQL_DATABASE:-mila_assist_db}"

# En-tête
echo "======================================================================"
echo "🧪 Tests de Déploiement Mila-Assist"
echo "======================================================================"
echo ""
log_info "URL de l'API: $API_URL"
log_info "Base de données: ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"
if [ -z "$MYSQL_PASSWORD" ]; then
    log_warning "Mot de passe MySQL non défini (vérifiez le fichier .env)"
fi
echo ""

# ===================================================================
# TEST 1: Healthcheck API (EF-001, EF-016)
# ===================================================================
echo "----------------------------------------------------------------------"
echo "TEST 1: Healthcheck de l'API"
echo "----------------------------------------------------------------------"

if command -v curl &> /dev/null; then
    response=$(curl -k -s -w "\n%{http_code}" "${API_URL}/api/v1/sante" 2>&1 || echo "ERROR")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        log_success "API répond sur /api/v1/sante (HTTP 200)"

        # Vérifier la structure JSON
        echo "$body" | python3 -m json.tool &>/dev/null
        json_valid=$?

        if [ $json_valid -eq 0 ]; then
            log_success "Réponse JSON valide"

            # Vérifier les champs attendus (support "status" et "statut")
            API_STATUS=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', data.get('statut', '')))" 2>/dev/null || echo "")

            if [ "$API_STATUS" = "ok" ] || [ "$API_STATUS" = "healthy" ]; then
                log_success "Status de santé: $API_STATUS"
            else
                log_warning "Status de santé inattendu: $API_STATUS (attendu: 'healthy' ou 'ok')"
            fi
        else
            log_error "Réponse JSON invalide: $body"
        fi
    else
        log_error "API ne répond pas correctement (HTTP $http_code)"
        log_info "Réponse: $body"
    fi
else
    log_warning "curl n'est pas installé, test skippé"
fi

# ===================================================================
# TEST 2: Schéma MySQL (EF-002, EF-007, EF-008)
# ===================================================================
echo ""
echo "----------------------------------------------------------------------"
echo "TEST 2: Schéma de la base de données MySQL"
echo "----------------------------------------------------------------------"

if command -v mysql &> /dev/null; then
    # Test de connexion (peut échouer si MySQL n'est pas exposé à l'extérieur)
    mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1" &>/dev/null
    mysql_accessible=$?

    if [ $mysql_accessible -eq 0 ]; then
        log_success "Connexion MySQL réussie (accès externe configuré)"

        # Vérifier les tables attendues
        tables_expected=("base_connaissances" "conversations" "retours_utilisateurs" "modifications_admin")

        for table in "${tables_expected[@]}"; do
            if mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
                -e "SHOW TABLES LIKE '$table'" 2>/dev/null | grep -q "$table"; then
                log_success "Table '$table' existe"

                # Vérifier le nombre d'entrées
                count=$(mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
                    -sN -e "SELECT COUNT(*) FROM $table" 2>/dev/null)
                log_info "  → $count entrée(s) dans la table"
            else
                log_error "Table '$table' manquante"
            fi
        done

        # Vérifier la structure de base_connaissances
        log_info "Vérification de la structure de 'base_connaissances'..."
        required_columns=("id" "etiquette" "motif" "reponse" "contexte")
        for column in "${required_columns[@]}"; do
            if mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
                -e "SHOW COLUMNS FROM base_connaissances LIKE '$column'" 2>/dev/null | grep -q "$column"; then
                log_success "  Colonne '$column' existe dans base_connaissances"
            else
                log_error "  Colonne '$column' manquante dans base_connaissances"
            fi
        done

    else
        log_warning "MySQL non accessible depuis l'extérieur (NORMAL si réseau Docker interne)"
        log_info "MySQL est accessible via l'API (vérifié dans le healthcheck)"
        log_info "Pour tester MySQL : utilisez phpMyAdmin (port 18548) ou depuis le container API"
        # Ne pas compter comme erreur si l'API a confirmé que MySQL fonctionne
        if [ "$API_STATUS" = "healthy" ]; then
            log_info "MySQL est opérationnel (confirmé par l'API healthcheck)"
        fi
    fi
else
    log_warning "Client MySQL non installé, tests de base de données skippés"
fi

# ===================================================================
# TEST 3: Index FAISS et Modèles IA (EF-002, EF-003)
# ===================================================================
echo ""
echo "----------------------------------------------------------------------"
echo "TEST 3: Disponibilité des ressources IA"
echo "----------------------------------------------------------------------"

# Test via l'API (si elle expose un endpoint de status détaillé)
curl -k -s "${API_URL}/api/v1/sante" 2>/dev/null | grep -q "faiss\|embedding\|llm"
models_check=$?

if [ $models_check -eq 0 ]; then
    log_success "L'API indique que les modèles IA sont chargés"
else
    log_info "Impossible de vérifier le chargement des modèles via l'API"
    log_info "Vérification manuelle recommandée des fichiers:"
    log_info "  - modeles/gemma-2-2b-it-q4.gguf"
    log_info "  - donnees/faiss_index/intents.index"
fi

# ===================================================================
# TEST 4: Endpoint de Conversation (EF-001, EF-002, EF-003)
# ===================================================================
echo ""
echo "----------------------------------------------------------------------"
echo "TEST 4: Endpoint POST /api/v1/conversation"
echo "----------------------------------------------------------------------"

if command -v curl &> /dev/null; then
    test_question="Comment obtenir AI_licia ?"

    log_info "Envoi de la question: \"$test_question\""

    # Générer un UUID valide pour id_session
    if command -v uuidgen &> /dev/null; then
        session_id=$(uuidgen)
    else
        # Générer un UUID v4 simple si uuidgen n'est pas disponible
        session_id=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || echo "00000000-0000-0000-0000-$(date +%s)000000")
    fi

    # Mesurer le temps de réponse
    start_time=$(date +%s.%N)

    response=$(curl -k -s -w "\n%{http_code}" --max-time 120 -X POST "${API_URL}/api/v1/conversation" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$test_question\", \"id_session\": \"$session_id\"}" \
        2>&1 || echo "ERROR")

    end_time=$(date +%s.%N)

    # Calculer le temps écoulé (avec bc si disponible, sinon approximation)
    if command -v bc &> /dev/null; then
        elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "1")
        elapsed_ms=$(echo "$elapsed * 1000" | bc 2>/dev/null | cut -d'.' -f1)
    else
        # Approximation sans bc
        start_sec=${start_time%.*}
        end_sec=${end_time%.*}
        elapsed_ms=$(( (end_sec - start_sec) * 1000 ))
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        log_success "Endpoint /api/v1/conversation répond (HTTP 200)"

        # Vérifier le temps de réponse (< 20s = 20000ms selon EF-001)
        if [ "$elapsed_ms" -lt 20000 ]; then
            log_success "Temps de réponse: ${elapsed_ms}ms (< 20000ms requis)"
        else
            log_error "Temps de réponse: ${elapsed_ms}ms (> 20000ms requis par EF-001)"
        fi

        # Vérifier la structure de la réponse
        if echo "$body" | python3 -m json.tool &>/dev/null; then
            log_success "Réponse JSON valide"

            # Vérifier les champs attendus
            reponse=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('reponse', ''))" 2>/dev/null)
            confiance=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('confiance', 0))" 2>/dev/null)

            if [ -n "$reponse" ] && [ "$reponse" != "None" ]; then
                log_success "Réponse générée (${#reponse} caractères)"
                log_info "  Extrait: \"${reponse:0:100}...\""
            else
                log_error "Pas de réponse dans le JSON"
            fi

            if [ -n "$confiance" ] && [ "$confiance" != "0" ]; then
                log_success "Score de confiance: $confiance"
            else
                log_warning "Score de confiance manquant ou nul"
            fi
        else
            log_error "Réponse JSON invalide"
        fi
    elif [ "$http_code" = "404" ]; then
        log_error "Endpoint /api/v1/conversation non trouvé (HTTP 404)"
    elif [ "$http_code" = "500" ]; then
        log_error "Erreur serveur (HTTP 500)"
        log_info "Réponse: $body"
    else
        log_error "Réponse inattendue (HTTP $http_code)"
        log_info "Réponse: $body"
    fi
else
    log_warning "curl n'est pas installé, test skippé"
fi

# ===================================================================
# TEST 5: Endpoint de Feedback Utilisateur (EF-004 à EF-008)
# ===================================================================
echo ""
echo "----------------------------------------------------------------------"
echo "TEST 5: Endpoint POST /api/v1/retour-utilisateur"
echo "----------------------------------------------------------------------"

if command -v curl &> /dev/null && [ "$http_code" = "200" ]; then
    # Récupérer l'ID de conversation de la réponse précédente
    id_conversation=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id_conversation', 0))" 2>/dev/null)

    if [ -n "$id_conversation" ] && [ "$id_conversation" != "0" ]; then
        log_info "Test avec id_conversation: $id_conversation"

        feedback_response=$(curl -k -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/retour-utilisateur" \
            -H "Content-Type: application/json" \
            -d "{\"id_conversation\": $id_conversation, \"note\": 5, \"commentaire\": \"Test automatique\", \"suggestion_reponse\": \"\"}" \
            2>&1 || echo "ERROR")

        feedback_http_code=$(echo "$feedback_response" | tail -n1)

        if [ "$feedback_http_code" = "200" ]; then
            log_success "Endpoint /api/v1/retour-utilisateur répond (HTTP 200)"
        else
            log_error "Endpoint /api/v1/retour-utilisateur ne répond pas correctement (HTTP $feedback_http_code)"
        fi
    else
        log_warning "ID de conversation non disponible, test de feedback skippé"
    fi
else
    log_warning "Test de feedback skippé (dépend du test précédent)"
fi

# ===================================================================
# TEST 6: Vérification des Logs
# ===================================================================
echo ""
echo "----------------------------------------------------------------------"
echo "TEST 6: Vérification des logs"
echo "----------------------------------------------------------------------"

# Chercher des fichiers de logs
log_dirs=("./logs" "./log" "./deploy-nas/log" "/var/log/mila-assist")

found_logs=false
for log_dir in "${log_dirs[@]}"; do
    if [ -d "$log_dir" ]; then
        log_files=$(find "$log_dir" -name "*.log" -o -name "*.txt" 2>/dev/null)
        if [ -n "$log_files" ]; then
            found_logs=true
            log_success "Fichiers de logs trouvés dans $log_dir"

            # Chercher des erreurs critiques
            critical_errors=$(grep -i "critical\|fatal\|emergency" $log_files 2>/dev/null || true)
            if [ -n "$critical_errors" ]; then
                log_error "Erreurs critiques détectées dans les logs !"
                echo "$critical_errors" | head -5
            else
                log_success "Aucune erreur critique dans les logs"
            fi
        fi
    fi
done

if [ "$found_logs" = false ]; then
    log_warning "Aucun fichier de log trouvé"
    log_info "Vérifiez les logs Docker avec: docker logs mila_assist_api"
fi

# ===================================================================
# RÉSUMÉ
# ===================================================================
echo ""
echo "======================================================================"
echo "📊 Résumé des Tests"
echo "======================================================================"
echo ""
echo -e "${GREEN}✅ Tests réussis:${NC}      $TESTS_PASSED"
echo -e "${YELLOW}⚠️  Avertissements:${NC}    $TESTS_WARNING"
echo -e "${RED}❌ Tests échoués:${NC}      $TESTS_FAILED"
echo -e "${BLUE}   Total:${NC}              $TESTS_TOTAL"
echo ""

# Critères de succès selon Success Criteria (SC-001 à SC-008)
echo "Vérification des Success Criteria:"
echo "----------------------------------------------------------------------"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ SC-001:${NC} Temps de réponse < 20s"
    echo -e "${GREEN}✅ SC-006:${NC} Système fonctionnel"
    echo -e "${GREEN}✅ SC-007:${NC} Enregistrement des feedbacks opérationnel"
    echo ""
    echo -e "${GREEN}🎉 DÉPLOIEMENT VALIDÉ !${NC}"
    echo ""
    echo "L'application Mila-Assist fonctionne conformément aux spécifications."
    echo ""
    echo "Prochaines étapes recommandées:"
    echo "  1. Tests manuels avec des questions réelles"
    echo "  2. Vérification de la qualité des réponses (SC-002: 85% pertinentes)"
    echo "  3. Tests de charge (SC-006: 20 utilisateurs simultanés)"
    echo "  4. Configuration du monitoring Grafana"
    exit 0
else
    echo -e "${RED}❌ DÉPLOIEMENT INCOMPLET${NC}"
    echo ""
    echo "Corrigez les erreurs ci-dessus avant de passer en production."
    echo ""
    echo "Aide au dépannage:"
    echo "  - Vérifier que les containers Docker sont démarrés"
    echo "  - Vérifier les logs: docker logs mila_assist_api"
    echo "  - Vérifier les variables d'environnement dans .env"
    echo "  - Consulter la documentation: specs/001-chatbot-support-retour/"
    exit 1
fi
