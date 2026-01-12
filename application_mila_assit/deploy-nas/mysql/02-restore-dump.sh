#!/bin/bash
# ===================================================================
# Script d'initialisation MySQL - Restauration automatique du dump
# Exécuté automatiquement au premier démarrage par MySQL
# ===================================================================

set -e

echo "[SYNC] Restauration du dump SQL..."

# Attendre que MySQL soit complètement démarré
echo "Attente du démarrage complet de MySQL..."
sleep 5

# Décompresser et restaurer le dump SQL s'il existe
if [ -f "/docker-entrypoint-initdb.d/backup/mila_assist_dump.sql.gz" ]; then
    echo "[PACKAGE] Dump trouvé, restauration en cours..."

    gunzip -c /docker-entrypoint-initdb.d/backup/mila_assist_dump.sql.gz | \
        mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"

    echo "[OK] Dump SQL restauré avec succès !"

    # Vérifier le nombre d'entrées
    COUNT=$(mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -se "SELECT COUNT(*) FROM base_connaissances;" 2>/dev/null || echo "0")

    echo "[STATS] Nombre d'entrées dans base_connaissances : $COUNT"

else
    echo "[ATTENTION]  Aucun dump trouvé, base de données vide (seulement le schéma)"
fi

echo "[OK] Initialisation MySQL terminée !"
