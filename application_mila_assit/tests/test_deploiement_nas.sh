#!/bin/bash

###############################################################################
# Script de Test du Déploiement Mila-Assist sur NAS Synology
# Version: 1.0
# Date: 2025-12-01
# Description: Vérifie que toutes les fonctionnalités sont opérationnelles
###############################################################################

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compteurs
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Fonction pour afficher les résultats
print_test() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ [OK]${NC} $test_name"
        [ -n "$message" ] && echo -e "   ${BLUE}→${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  [WARN]${NC} $test_name"
        [ -n "$message" ] && echo -e "   ${YELLOW}→${NC} $message"
    else
        echo -e "${RED}❌ [FAIL]${NC} $test_name"
        [ -n "$message" ] && echo -e "   ${RED}→${NC} $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "============================================================================="
echo "  TESTS DE DÉPLOIEMENT - MILA-ASSIST"
echo "  NAS Synology DS423+ (4 Go RAM)"
echo "============================================================================="
echo ""

###############################################################################
# TEST 1: État des Containers
###############################################################################
echo -e "${BLUE}═══ TEST 1: État des Containers ═══${NC}"
echo ""

# MySQL
if docker ps | grep -q "mila_assist_mysql"; then
    STATUS=$(docker ps --format "{{.Status}}" --filter "name=mila_assist_mysql")
    if echo "$STATUS" | grep -q "Up"; then
        print_test "Container MySQL" "OK" "Status: $STATUS"
    else
        print_test "Container MySQL" "FAIL" "Status: $STATUS (non démarré)"
    fi
else
    print_test "Container MySQL" "FAIL" "Container non trouvé"
fi

# API
if docker ps | grep -q "mila_assist_api"; then
    STATUS=$(docker ps --format "{{.Status}}" --filter "name=mila_assist_api")
    if echo "$STATUS" | grep -q "Up"; then
        print_test "Container API" "OK" "Status: $STATUS"
    else
        print_test "Container API" "FAIL" "Status: $STATUS (non démarré)"
    fi
else
    print_test "Container API" "FAIL" "Container non trouvé"
fi

# phpMyAdmin
if docker ps | grep -q "mila_assist_phpmyadmin"; then
    STATUS=$(docker ps --format "{{.Status}}" --filter "name=mila_assist_phpmyadmin")
    if echo "$STATUS" | grep -q "Up"; then
        print_test "Container phpMyAdmin" "OK" "Status: $STATUS"
    else
        print_test "Container phpMyAdmin" "WARN" "Status: $STATUS (optionnel)"
    fi
fi

echo ""

###############################################################################
# TEST 2: Endpoints API
###############################################################################
echo -e "${BLUE}═══ TEST 2: Endpoints API ═══${NC}"
echo ""

# Health check simple
RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/health 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "healthy"; then
    print_test "GET /health" "OK" "API répond correctement"
else
    print_test "GET /health" "FAIL" "API ne répond pas: $RESPONSE"
fi

# Endpoint racine
RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/ 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "Bienvenue"; then
    print_test "GET /" "OK" "Page d'accueil accessible"
else
    print_test "GET /" "FAIL" "Erreur: $RESPONSE"
fi

# Endpoint santé détaillé
RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/api/v1/sante 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "mysql"; then
    print_test "GET /api/v1/sante" "OK" "Endpoint santé détaillé fonctionnel"

    # Vérifier les composants
    if echo "$RESPONSE" | grep -q '"mysql":.*"statut":"ok"'; then
        print_test "  → Connexion MySQL" "OK" "MySQL accessible"
    else
        print_test "  → Connexion MySQL" "FAIL" "MySQL non accessible"
    fi

    if echo "$RESPONSE" | grep -q '"faiss"'; then
        print_test "  → Index FAISS" "OK" "FAISS chargé"
    fi

    if echo "$RESPONSE" | grep -q '"llm"'; then
        print_test "  → Modèle LLM" "OK" "LLM chargé"
    fi
else
    print_test "GET /api/v1/sante" "FAIL" "Erreur: $RESPONSE"
fi

echo ""

###############################################################################
# TEST 3: Schéma MySQL
###############################################################################
echo -e "${BLUE}═══ TEST 3: Schéma MySQL ═══${NC}"
echo ""

# Liste des tables
TABLES=$(docker exec mila_assist_mysql mysql -u root -pSouleymane92@ mila_assist_db -e "SHOW TABLES;" 2>/dev/null | tail -n +2)

# Tables obligatoires
REQUIRED_TABLES=("base_connaissances" "conversations" "retours_utilisateurs" "metriques" "modifications_admin" "alertes_qualite")

for table in "${REQUIRED_TABLES[@]}"; do
    if echo "$TABLES" | grep -q "^$table$"; then
        print_test "Table $table" "OK" "Existe"
    else
        print_test "Table $table" "FAIL" "Manquante"
    fi
done

# Vérifier les colonnes critiques dans conversations
COLUMNS=$(docker exec mila_assist_mysql mysql -u root -pSouleymane92@ mila_assist_db -e "DESCRIBE conversations;" 2>/dev/null | awk '{print $1}' | tail -n +2)

REQUIRED_COLUMNS=("temps_embedding_ms" "temps_retrieval_ms" "temps_generation_ms" "cache_hit")

for col in "${REQUIRED_COLUMNS[@]}"; do
    if echo "$COLUMNS" | grep -q "^$col$"; then
        print_test "  → Colonne conversations.$col" "OK" "Existe"
    else
        print_test "  → Colonne conversations.$col" "FAIL" "Manquante"
    fi
done

# Vérifier les colonnes dans retours_utilisateurs
COLUMNS=$(docker exec mila_assist_mysql mysql -u root -pSouleymane92@ mila_assist_db -e "DESCRIBE retours_utilisateurs;" 2>/dev/null | awk '{print $1}' | tail -n +2)

REQUIRED_COLUMNS=("categorie_probleme" "statut" "id_admin_traitement" "justification" "date_traitement")

for col in "${REQUIRED_COLUMNS[@]}"; do
    if echo "$COLUMNS" | grep -q "^$col$"; then
        print_test "  → Colonne retours_utilisateurs.$col" "OK" "Existe"
    else
        print_test "  → Colonne retours_utilisateurs.$col" "FAIL" "Manquante"
    fi
done

echo ""

###############################################################################
# TEST 4: Nouvelles Routes Feedback (US2)
###############################################################################
echo -e "${BLUE}═══ TEST 4: Routes Feedback (US2) ═══${NC}"
echo ""

# Test POST /retour-utilisateur (sans conversation réelle, donc attendu 404)
RESPONSE=$(docker exec mila_assist_api curl -s -X POST http://localhost:8000/api/v1/retour-utilisateur \
    -H "Content-Type: application/json" \
    -d '{"id_conversation":999999,"note":5,"commentaire":"Test"}' 2>/dev/null || echo "ERROR")

if echo "$RESPONSE" | grep -q "404\|n'existe pas"; then
    print_test "POST /api/v1/retour-utilisateur" "OK" "Route existe (404 attendu car conversation inexistante)"
elif echo "$RESPONSE" | grep -q "id_retour"; then
    print_test "POST /api/v1/retour-utilisateur" "OK" "Route fonctionnelle"
else
    print_test "POST /api/v1/retour-utilisateur" "FAIL" "Erreur: $RESPONSE"
fi

# Test GET /retours/statistiques
RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/api/v1/retours/statistiques 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "total_retours"; then
    print_test "GET /api/v1/retours/statistiques" "OK" "Route fonctionnelle"
    TOTAL=$(echo "$RESPONSE" | grep -o '"total_retours":[0-9]*' | cut -d':' -f2)
    [ -n "$TOTAL" ] && print_test "  → Nombre de retours" "OK" "$TOTAL retours en base"
else
    print_test "GET /api/v1/retours/statistiques" "FAIL" "Erreur: $RESPONSE"
fi

# Test GET /retours/par-note
RESPONSE=$(docker exec mila_assist_api curl -s "http://localhost:8000/api/v1/retours/par-note?note_min=1&note_max=5" 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "\[\]" || echo "$RESPONSE" | grep -q "id_conversation"; then
    print_test "GET /api/v1/retours/par-note" "OK" "Route fonctionnelle"
else
    print_test "GET /api/v1/retours/par-note" "FAIL" "Erreur: $RESPONSE"
fi

echo ""

###############################################################################
# TEST 5: Documentation Swagger
###############################################################################
echo -e "${BLUE}═══ TEST 5: Documentation Swagger ═══${NC}"
echo ""

RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/docs 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "Swagger" || echo "$RESPONSE" | grep -q "openapi"; then
    print_test "Swagger UI" "OK" "Documentation accessible"
else
    print_test "Swagger UI" "FAIL" "Non accessible"
fi

# Vérifier que les routes Retours sont documentées
RESPONSE=$(docker exec mila_assist_api curl -s http://localhost:8000/openapi.json 2>/dev/null || echo "ERROR")
if echo "$RESPONSE" | grep -q "retour-utilisateur"; then
    print_test "  → Routes Retours documentées" "OK" "Présentes dans OpenAPI"
else
    print_test "  → Routes Retours documentées" "FAIL" "Absentes d'OpenAPI"
fi

echo ""

###############################################################################
# TEST 6: Logs
###############################################################################
echo -e "${BLUE}═══ TEST 6: Logs ═══${NC}"
echo ""

# Vérifier que les logs API sont créés
if [ -f "/volume1/docker/RNCP-6/Mila-assit/log/api/mila_assist.log" ]; then
    SIZE=$(du -h "/volume1/docker/RNCP-6/Mila-assit/log/api/mila_assist.log" | cut -f1)
    print_test "Log API créé" "OK" "Taille: $SIZE"

    # Vérifier les logs récents
    RECENT_LOGS=$(tail -n 5 "/volume1/docker/RNCP-6/Mila-assit/log/api/mila_assist.log" 2>/dev/null)
    if [ -n "$RECENT_LOGS" ]; then
        print_test "  → Logs récents" "OK" "Logs actifs"
    fi
else
    print_test "Log API créé" "WARN" "Fichier non trouvé (vérifier le montage du volume)"
fi

# Vérifier les logs MySQL
if [ -f "/volume1/docker/RNCP-6/Mila-assit/log/mysql/error.log" ]; then
    SIZE=$(du -h "/volume1/docker/RNCP-6/Mila-assit/log/mysql/error.log" | cut -f1)
    print_test "Log MySQL créé" "OK" "Taille: $SIZE"
else
    print_test "Log MySQL créé" "WARN" "Fichier non trouvé"
fi

echo ""

###############################################################################
# TEST 7: Ressources Système
###############################################################################
echo -e "${BLUE}═══ TEST 7: Ressources Système ═══${NC}"
echo ""

# RAM utilisée par les containers
API_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" mila_assist_api 2>/dev/null | awk '{print $1}')
MYSQL_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" mila_assist_mysql 2>/dev/null | awk '{print $1}')

if [ -n "$API_MEM" ]; then
    print_test "RAM API" "OK" "$API_MEM utilisés"

    # Vérifier si > 4.2 Go (limite)
    API_MEM_NUM=$(echo "$API_MEM" | sed 's/[^0-9.]//g')
    if (( $(echo "$API_MEM_NUM > 4200" | bc -l 2>/dev/null || echo 0) )); then
        print_test "  → Limite RAM" "WARN" "Proche de la limite (4.2 Go max)"
    fi
fi

if [ -n "$MYSQL_MEM" ]; then
    print_test "RAM MySQL" "OK" "$MYSQL_MEM utilisés"
fi

# CPU
API_CPU=$(docker stats --no-stream --format "{{.CPUPerc}}" mila_assist_api 2>/dev/null)
if [ -n "$API_CPU" ]; then
    print_test "CPU API" "OK" "$API_CPU"
fi

echo ""

###############################################################################
# RÉSUMÉ
###############################################################################
echo "============================================================================="
echo -e "${BLUE}RÉSUMÉ DES TESTS${NC}"
echo "============================================================================="
echo ""
echo -e "Total de tests      : ${TESTS_TOTAL}"
echo -e "Tests réussis       : ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests échoués       : ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS SONT PASSÉS !${NC}"
    echo ""
    echo "Le déploiement Mila-Assist est opérationnel."
    echo ""
    echo "Accès:"
    echo "  - API Documentation: http://ezi0.synology.me:9000/docs"
    echo "  - API Santé:         http://ezi0.synology.me:9000/api/v1/sante"
    echo "  - phpMyAdmin:        http://ezi0.synology.me:18548"
    exit 0
else
    echo -e "${RED}❌ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
    echo ""
    echo "Consultez les logs pour plus d'informations:"
    echo "  docker logs mila_assist_api"
    echo "  docker logs mila_assist_mysql"
    echo ""
    echo "Ou consultez la documentation de dépannage."
    exit 1
fi
