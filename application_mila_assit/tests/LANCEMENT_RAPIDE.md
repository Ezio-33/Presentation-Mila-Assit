# 🚀 Guide de Lancement Rapide des Tests

## Configuration du NAS

**URL du NAS Synology** : `https://ezi0.synology.me:10443`

### Informations de Connexion

```bash
# API
URL HTTPS (via reverse proxy): https://ezi0.synology.me:10443
URL HTTP (direct):              http://ezi0.synology.me:9000

# MySQL (si accès externe configuré)
Host:     ezi0.synology.me
Port:     3306
User:     mila_user
Password: (BuB-FCp%pvxwJr#V%K%zbByhE=ruiR3
Database: mila_assist_db

# phpMyAdmin (dev uniquement)
URL:      http://ezi0.synology.me:18548
```

## Tests Automatiques (Recommandé)

### Option 1: Lancement Complet

```bash
# Exécuter tous les tests automatiquement
cd /root/Holberton_School/Projet-RNCP6-V2/chatbot/Mila-assit
./tests/run_all_tests.sh
```

Ce script va:
1. ✅ Tester l'infrastructure (API, MySQL, FAISS)
2. ✅ Tester la qualité des réponses (10 questions types)
3. ✅ Valider les Success Criteria SC-001 et SC-002
4. 📊 Afficher un résumé global

### Option 2: Tests Séparés

**Test d'infrastructure uniquement:**
```bash
./tests/test_deploiement_complet.sh
```

**Test de qualité uniquement:**
```bash
# Installer les dépendances Python si nécessaire
pip3 install requests

python3 tests/test_qualite_reponses.py
```

## Tests Manuels Rapides

### 1. Vérifier que l'API répond

```bash
# Test healthcheck
curl https://ezi0.synology.me:10443/api/v1/sante

# Résultat attendu:
# {"status":"healthy","version":"1.0.0",...}
```

### 2. Tester une conversation

```bash
curl -X POST https://ezi0.synology.me:10443/api/v1/conversation \
  -H "Content-Type: application/json" \
  -d '{"question":"Comment obtenir AI_licia ?","id_session":"test-123"}'

# Résultat attendu:
# {"id_conversation":...,"reponse":"...","confiance":...,"temps_ms":...}
```

### 3. Vérifier MySQL (depuis le NAS ou avec accès externe)

```bash
# Si client mysql installé
mysql -h ezi0.synology.me -u mila_user -p'(BuB-FCp%pvxwJr#V%K%zbByhE=ruiR3' \
  -e "USE mila_assist_db; SHOW TABLES;"

# Résultat attendu:
# +---------------------------+
# | Tables_in_mila_assist_db  |
# +---------------------------+
# | base_connaissances        |
# | conversations             |
# | retours_utilisateurs      |
# | metriques                 |
# | modifications_admin       |
# +---------------------------+
```

### 4. Accéder à phpMyAdmin (développement)

Ouvrir dans un navigateur:
```
http://ezi0.synology.me:18548
```

**Identifiants:**
- Serveur: `mysql`
- Utilisateur: `mila_user`
- Mot de passe: `(BuB-FCp%pvxwJr#V%K%zbByhE=ruiR3`

## Interprétation des Résultats

### ✅ Tests Réussis

Si tous les tests passent, vous verrez:

```
====================================================================
🎉 TOUS LES TESTS SONT VALIDÉS !
====================================================================

✅ Infrastructure opérationnelle
✅ Qualité des réponses conforme aux spécifications
✅ Success Criteria SC-001 et SC-002 atteints

L'application Mila-Assist est prête pour la production.
```

**Actions suivantes:**
1. Tests manuels avec des utilisateurs réels
2. Test de charge (20 utilisateurs simultanés)
3. Configuration du monitoring Grafana

### ⚠️ Tests Partiels

Si certains tests échouent:

```
⚠️ VALIDATION PARTIELLE

✅ Infrastructure opérationnelle
⚠️  Qualité des réponses à améliorer
```

**Actions recommandées:**
- Consulter la section "Dépannage" ci-dessous
- Vérifier les recommandations affichées par le script
- Améliorer la base de connaissances

### ❌ Tests Échoués

Si l'infrastructure ne fonctionne pas:

```
❌ VALIDATION ÉCHOUÉE

L'application ne peut pas être mise en production.
```

**Actions immédiates:**
1. Vérifier que les containers Docker sont démarrés
2. Consulter les logs: `docker logs mila_assist_api`
3. Vérifier la configuration `.env`

## Dépannage Rapide

### Erreur: "Failed to connect"

**Cause:** L'API n'est pas accessible

**Solutions:**
```bash
# 1. Vérifier que les containers sont démarrés
docker ps | grep mila_assist

# 2. Vérifier les logs API
docker logs mila_assist_api --tail 50

# 3. Vérifier les logs MySQL
docker logs mila_assist_mysql --tail 50

# 4. Redémarrer les containers si nécessaire
cd /root/Holberton_School/Projet-RNCP6-V2/chatbot/Mila-assit/deploy-nas
docker-compose restart
```

### Erreur: "MySQL connection refused"

**Cause:** MySQL n'est pas prêt ou mal configuré

**Solutions:**
```bash
# 1. Vérifier que MySQL est healthy
docker ps | grep mila_assist_mysql

# 2. Attendre que MySQL termine son initialisation (peut prendre 2-3 minutes)
docker logs mila_assist_mysql | grep "ready for connections"

# 3. Tester la connexion depuis le container API
docker exec mila_assist_api python -c "import mysql.connector; print('OK')"
```

### Erreur: Temps de réponse > 20s

**Cause:** Modèles IA lents ou ressources insuffisantes

**Solutions:**
```bash
# 1. Vérifier l'utilisation des ressources
docker stats mila_assist_api

# 2. Vérifier que le modèle Q4 est bien utilisé (pas FP16)
docker exec mila_assist_api ls -lh /app/modeles/

# 3. Vérifier les logs pour identifier le goulot d'étranglement
docker logs mila_assist_api | grep "temps_reponse"
```

### Erreur: "ModuleNotFoundError"

**Cause:** Dépendances Python manquantes

**Solutions:**
```bash
# Reconstruire l'image Docker
cd /root/Holberton_School/Projet-RNCP6-V2/chatbot/Mila-assit/deploy-nas
docker-compose build --no-cache api
docker-compose up -d
```

## Tests Avancés

### Test de Charge (20 utilisateurs simultanés)

```bash
# Installer Apache Bench
sudo apt-get install apache2-utils

# Créer un fichier de requête
cat > question.json <<EOF
{"question": "Comment configurer le TTS ?", "id_session": "load-test"}
EOF

# Lancer le test de charge
ab -n 100 -c 20 -p question.json -T application/json \
   https://ezi0.synology.me:10443/api/v1/conversation

# Analyser les résultats:
# - Time per request (mean): Doit être < 20000 ms
# - Failed requests: Doit être 0
```

### Vérifier les Logs en Temps Réel

```bash
# Logs API + IA Engine
docker logs -f mila_assist_api

# Logs MySQL
docker logs -f mila_assist_mysql

# Tous les logs
docker-compose -f deploy-nas/docker-compose.yml logs -f
```

### Consulter les Métriques

```bash
# Via l'API
curl https://ezi0.synology.me:10443/api/v1/metriques | python3 -m json.tool

# Résultat attendu:
# {
#   "latence_moyenne_ms": 500,
#   "latence_p95_ms": 2000,
#   "taux_cache_hit": 0.6,
#   "utilisation_ram_go": 3.8,
#   "total_requetes": 150,
#   "satisfaction_moyenne": 4.2
# }
```

## Prochaines Étapes Après Validation

Une fois que tous les tests sont validés:

1. **Tests Utilisateurs Réels**
   - Inviter 5-10 utilisateurs beta
   - Collecter leurs feedbacks via l'interface
   - Analyser les retours négatifs (note < 3)

2. **Configuration Monitoring**
   - Installer Grafana
   - Importer les dashboards Prometheus
   - Configurer les alertes (latence > 20s, RAM > 90%)

3. **Optimisations**
   - Augmenter le cache si hit rate < 50%
   - Enrichir la base de connaissances
   - Ajuster les paramètres du LLM (temperature, top_p)

4. **Documentation Utilisateur**
   - Créer un guide utilisateur final
   - Enregistrer une vidéo démo
   - Préparer le PowerPoint pour le jury

## Support

En cas de problème non résolu:

1. Consulter la documentation complète: `tests/README_TESTS.md`
2. Vérifier les spécifications: `specs/001-chatbot-support-retour/`
3. Examiner les logs détaillés dans `/deploy-nas/log/`

---

**Dernière mise à jour:** 2025-01-26
**Version:** 1.1.0
**Contact:** Voir documentation projet
