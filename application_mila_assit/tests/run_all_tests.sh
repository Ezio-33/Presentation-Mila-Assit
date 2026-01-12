#!/bin/bash

# ===================================================================
# Script de lancement de tous les tests - Mila-Assist
# Exécute tous les tests de validation du déploiement
# ===================================================================
#
# Usage:
#   ./run_all_tests.sh [URL_API]
#
# Exemples:
#   ./run_all_tests.sh http://localhost:9000
#   ./run_all_tests.sh http://192.168.1.100:9000
#

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
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

# Charger les variables depuis .env
load_env "$ENV_FILE"

# URL par défaut : NAS Synology via reverse proxy HTTPS
API_URL="${1:-${CORS_ORIGINS%%,*}}"  # Utilise la première origine CORS depuis .env
if [ -z "$API_URL" ] || [ "$API_URL" = "${CORS_ORIGINS%%,*}" ]; then
    API_URL="https://ezi0.synology.me:10443"  # Fallback si .env non trouvé
fi

echo "======================================================================"
echo -e "${BOLD}🚀 Lancement de Tous les Tests - Mila-Assist${NC}"
echo "======================================================================"
echo ""
echo -e "${BLUE}URL de l'API:${NC} $API_URL"
echo -e "${BLUE}Date/Heure:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Vérifier que les scripts existent
if [ ! -f "$SCRIPT_DIR/test_deploiement_complet.sh" ]; then
    echo -e "${RED}❌ Script test_deploiement_complet.sh introuvable${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/test_qualite_reponses.py" ]; then
    echo -e "${RED}❌ Script test_qualite_reponses.py introuvable${NC}"
    exit 1
fi

# ===================================================================
# PHASE 1: Tests d'Infrastructure
# ===================================================================
echo ""
echo "======================================================================"
echo -e "${BOLD}PHASE 1: Tests d'Infrastructure${NC}"
echo "======================================================================"
echo ""

if bash "$SCRIPT_DIR/test_deploiement_complet.sh" "$API_URL"; then
    echo ""
    echo -e "${GREEN}✅ Phase 1 réussie - Infrastructure validée${NC}"
    PHASE1_OK=true
else
    echo ""
    echo -e "${RED}❌ Phase 1 échouée - Problèmes d'infrastructure détectés${NC}"
    echo ""
    echo -e "${YELLOW}Les tests de qualité seront skippés car l'infrastructure n'est pas prête.${NC}"
    echo ""
    echo "Actions recommandées:"
    echo "  1. Vérifier que les containers Docker sont démarrés"
    echo "  2. Consulter les logs: docker logs mila_assist_api"
    echo "  3. Vérifier la configuration .env"
    echo ""
    exit 1
fi

# ===================================================================
# PHASE 2: Tests de Qualité
# ===================================================================
echo ""
echo "======================================================================"
echo -e "${BOLD}PHASE 2: Tests de Qualité des Réponses${NC}"
echo "======================================================================"
echo ""

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 non installé, tests de qualité skippés${NC}"
    echo ""
    echo "Pour installer Python 3:"
    echo "  sudo apt-get install python3 python3-pip"
    PHASE2_OK=false
else
    # Vérifier que le module requests est installé
    if ! python3 -c "import requests" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Module 'requests' non installé${NC}"
        echo -e "${BLUE}Installation automatique...${NC}"
        pip3 install requests --quiet || {
            echo -e "${RED}❌ Impossible d'installer 'requests'${NC}"
            echo "Installez-le manuellement: pip3 install requests"
            PHASE2_OK=false
        }
    fi

    if python3 "$SCRIPT_DIR/test_qualite_reponses.py" "$API_URL"; then
        echo ""
        echo -e "${GREEN}✅ Phase 2 réussie - Qualité validée${NC}"
        PHASE2_OK=true
    else
        echo ""
        echo -e "${YELLOW}⚠️  Phase 2 partiellement réussie - Améliorations recommandées${NC}"
        PHASE2_OK=false
    fi
fi

# ===================================================================
# RÉSUMÉ FINAL
# ===================================================================
echo ""
echo "======================================================================"
echo -e "${BOLD}📊 Résumé Global des Tests${NC}"
echo "======================================================================"
echo ""

if [ "$PHASE1_OK" = true ] && [ "$PHASE2_OK" = true ]; then
    echo -e "${GREEN}${BOLD}🎉 TOUS LES TESTS SONT VALIDÉS !${NC}"
    echo ""
    echo "✅ Infrastructure opérationnelle"
    echo "✅ Qualité des réponses conforme aux spécifications"
    echo "✅ Success Criteria SC-001 et SC-002 atteints"
    echo ""
    echo -e "${BLUE}L'application Mila-Assist est prête pour la production.${NC}"
    echo ""
    echo "Prochaines étapes recommandées:"
    echo "  1. Tests manuels avec des utilisateurs réels"
    echo "  2. Test de charge (20 utilisateurs simultanés)"
    echo "  3. Configuration du monitoring Grafana"
    echo "  4. Formation des administrateurs au tableau de bord"
    echo ""
    exit 0

elif [ "$PHASE1_OK" = true ] && [ "$PHASE2_OK" = false ]; then
    echo -e "${YELLOW}${BOLD}⚠️  VALIDATION PARTIELLE${NC}"
    echo ""
    echo "✅ Infrastructure opérationnelle"
    echo "⚠️  Qualité des réponses à améliorer"
    echo ""
    echo "L'application fonctionne mais nécessite des améliorations."
    echo ""
    echo "Consultez les recommandations ci-dessus pour:"
    echo "  • Améliorer les temps de réponse"
    echo "  • Augmenter la pertinence des réponses"
    echo "  • Enrichir la base de connaissances"
    echo ""
    exit 1

else
    echo -e "${RED}${BOLD}❌ VALIDATION ÉCHOUÉE${NC}"
    echo ""
    echo "L'application ne peut pas être mise en production."
    echo ""
    echo "Consultez les erreurs ci-dessus et corrigez-les avant de recommencer."
    echo ""
    exit 1
fi
