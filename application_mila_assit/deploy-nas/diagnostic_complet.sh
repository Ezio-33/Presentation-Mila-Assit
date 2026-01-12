#!/bin/bash
# ===================================================================
# Script de diagnostic complet pour Mila-Assist Container 3
# ===================================================================

echo "==============================================="
echo "DIAGNOSTIC COMPLET - Mila-Assist Container 3"
echo "Date: $(date)"
echo "==============================================="

echo ""
echo "1. VÉRIFICATION FICHIERS SUR NAS"
echo "-----------------------------------"
echo "Checksum requirements.txt:"
md5sum /volume1/docker/RNCP-6/Mila-assit/llm-service/requirements.txt 2>&1

echo ""
echo "Contenu requirements.txt (20 premières lignes):"
head -20 /volume1/docker/RNCP-6/Mila-assit/llm-service/requirements.txt 2>&1

echo ""
echo "2. IMAGES DOCKER"
echo "-----------------------------------"
docker images | grep -E "REPOSITORY|mila"

echo ""
echo "3. CONTAINERS ACTIFS"
echo "-----------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.CreatedAt}}"

echo ""
echo "4. LOGS CONTAINER 3 (50 dernières lignes)"
echo "-----------------------------------"
docker logs mila_llm_faiss --tail 50 2>&1

echo ""
echo "5. VERSIONS DANS LE CONTAINER"
echo "-----------------------------------"
echo "Python packages:"
docker exec mila_llm_faiss pip list 2>&1 | grep -E "sentence-transformers|transformers|torch|faiss" || echo "Container ne répond pas"

echo ""
echo "6. MODÈLE CAMEMBERT SUR NAS"
echo "-----------------------------------"
if [ -f "/volume1/docker/RNCP-6/Mila-assit/modeles/embeddings/config_sentence_transformers.json" ]; then
    echo "Fichier config trouvé:"
    cat /volume1/docker/RNCP-6/Mila-assit/modeles/embeddings/config_sentence_transformers.json
else
    echo "[ERREUR] Modèle CamemBERT PAS TROUVÉ sur le NAS!"
fi

echo ""
echo "7. STRUCTURE DOSSIERS"
echo "-----------------------------------"
echo "Dossier llm-service:"
ls -lah /volume1/docker/RNCP-6/Mila-assit/llm-service/ 2>&1

echo ""
echo "Dossier modeles/embeddings:"
ls -lh /volume1/docker/RNCP-6/Mila-assit/modeles/embeddings/ 2>&1 | head -12

echo ""
echo "8. TEST CONTAINER 3"
echo "-----------------------------------"
echo "Health check:"
curl -s http://localhost:8001/health 2>&1 || echo "[ERREUR] Container 3 ne répond pas sur port 8001"

echo ""
echo "==============================================="
echo "FIN DU DIAGNOSTIC"
echo "==============================================="
