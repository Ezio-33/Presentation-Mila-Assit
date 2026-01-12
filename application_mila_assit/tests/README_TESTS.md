# Guide de Test - Mila-Assist

Ce dossier contient les scripts de test pour vérifier que l'application Mila-Assist fonctionne conformément aux spécifications définies dans `specs/001-chatbot-support-retour/`.

## Scripts Disponibles

### 1. `test_deploiement_complet.sh` - Tests d'Infrastructure

Script Bash qui vérifie les aspects techniques et infrastructure du déploiement.

**Ce qu'il teste:**

| Test | Exigence | Description |
|------|----------|-------------|
| Healthcheck API | EF-001, EF-016 | Vérifie que l'API répond sur `/api/v1/sante` |
| Schéma MySQL | EF-002, EF-007, EF-008 | Vérifie la présence des 4 tables requises |
| Structure Tables | EF-002 | Vérifie les colonnes de `base_connaissances` |
| Endpoint Conversation | EF-001, EF-002, EF-003 | Teste `POST /api/v1/conversation` |
| Temps de Réponse | EF-001, SC-001 | Mesure le temps (< 20s requis) |
| Endpoint Feedback | EF-004 à EF-008 | Teste `POST /api/v1/retour-utilisateur` |
| Logs | EF-016 | Vérifie l'absence d'erreurs critiques |

**Usage:**

```bash
# Test par défaut (NAS Synology via HTTPS reverse proxy)
./tests/test_deploiement_complet.sh

# Test avec URL personnalisée
./tests/test_deploiement_complet.sh https://ezi0.synology.me:10443

# Test HTTP direct (port 9000, si reverse proxy non configuré)
./tests/test_deploiement_complet.sh http://ezi0.synology.me:9000

# Test local en développement
./tests/test_deploiement_complet.sh http://localhost:9000

# Avec variables d'environnement MySQL personnalisées
MYSQL_HOST=ezi0.synology.me \
MYSQL_USER=mila_user \
MYSQL_PASSWORD='(BuB-FCp%pvxwJr#V%K%zbByhE=ruiR3' \
./tests/test_deploiement_complet.sh
```

**Prérequis:**
- `curl` installé
- `mysql` client installé (pour tests de base de données)
- `bc` installé (pour calculs de temps)
- Accès réseau à l'API et à MySQL

**Codes de sortie:**
- `0`: Tous les tests passent (déploiement validé)
- `1`: Au moins un test échoue (corrections nécessaires)

---

### 2. `test_qualite_reponses.py` - Tests de Qualité

Script Python qui vérifie la qualité des réponses du chatbot selon les Success Criteria.

**Ce qu'il teste:**

| Test | Success Criteria | Description |
|------|-----------------|-------------|
| Temps de Réponse | SC-001 | 95% des réponses < 20 secondes |
| Pertinence | SC-002 | 85% des réponses considérées pertinentes |
| Soumission Feedback | SC-003 | Feedback soumis en < 1 minute |

**Usage:**

```bash
# Installer les dépendances
pip3 install requests

# Test par défaut (NAS Synology via HTTPS)
python3 tests/test_qualite_reponses.py

# Test avec URL personnalisée
python3 tests/test_qualite_reponses.py https://ezi0.synology.me:10443

# Test HTTP direct (port 9000)
python3 tests/test_qualite_reponses.py http://ezi0.synology.me:9000

# Test local en développement
python3 tests/test_qualite_reponses.py http://localhost:9000
```

**Fonctionnement:**

Le script pose 10 questions de test basées sur les User Stories et vérifie:

1. **Temps de réponse** : Chaque question doit recevoir une réponse en < 20s
2. **Pertinence** : La réponse contient au moins 50% des mots-clés attendus
3. **Score de confiance** : Un score de confiance est retourné
4. **Feedback** : Possibilité de soumettre un feedback

**Questions de Test:**

Les questions sont définies dans le code et couvrent:
- Obtention d'AI_licia
- Configuration TTS
- Streaming Twitch
- Problèmes de son
- Support et contact

**Résultat:**

Le script affiche:
- Nombre de tests réussis/échoués
- Temps moyen de réponse
- Pourcentage de réponses < 20s (validation SC-001)
- Pertinence moyenne
- Validation SC-002 (85% des réponses pertinentes)
- Recommandations d'amélioration

**Codes de sortie:**
- `0`: SC-001 et SC-002 validés (prêt pour production)
- `1`: Au moins un SC non validé (améliorations nécessaires)

---

## Workflow de Test Recommandé

### Étape 1: Vérification de l'Infrastructure

```bash
# Exécuter le test d'infrastructure (utilise l'URL par défaut du NAS)
./tests/test_deploiement_complet.sh

# Ou spécifier l'URL manuellement
./tests/test_deploiement_complet.sh https://ezi0.synology.me:10443

# Vérifier que tous les tests passent ✅
# Si des erreurs ❌ apparaissent, consulter les logs Docker
```

**À corriger si échec:**
- API ne répond pas → Vérifier `docker logs mila_assist_api`
- Tables MySQL manquantes → Vérifier `docker logs mila_assist_mysql`
- Erreurs dans les logs → Consulter `/log/api/*.log`

### Étape 2: Vérification de la Qualité

```bash
# Exécuter le test de qualité (nécessite Python 3)
python3 tests/test_qualite_reponses.py

# Ou avec URL personnalisée
python3 tests/test_qualite_reponses.py https://ezi0.synology.me:10443

# Analyser les résultats
# - SC-001: ≥95% des réponses < 20s
# - SC-002: ≥85% des réponses pertinentes
```

**À améliorer si échec:**

| Problème | Solution |
|----------|----------|
| Temps > 20s | • Augmenter RAM container<br>• Optimiser cache LRU<br>• Vérifier CPU disponible |
| Pertinence < 85% | • Enrichir `base_connaissances`<br>• Améliorer les patterns de questions<br>• Revoir les embeddings FAISS |
| Confiance faible | • Vérifier la qualité des données d'entraînement<br>• Ajuster MAX_RETRIEVE_RESULTS |

### Étape 3: Tests Manuels

Après validation automatique, effectuer des tests manuels:

1. **Test Utilisateur Final:**
   - Ouvrir `http://IP_NAS:9000` dans un navigateur
   - Poser 5-10 questions réelles
   - Vérifier la qualité des réponses
   - Tester le système de feedback

2. **Test Admin:**
   - Accéder au tableau de bord admin
   - Vérifier les feedbacks enregistrés
   - Tester la modification de la base de connaissances

3. **Test de Charge (SC-006):**
   ```bash
   # Installer Apache Bench (ab) si nécessaire
   sudo apt-get install apache2-utils

   # Simuler 20 utilisateurs simultanés
   ab -n 100 -c 20 -p question.json -T application/json \
      http://IP_NAS:9000/api/v1/conversation
   ```

   Créer `question.json`:
   ```json
   {"question": "Comment obtenir AI_licia ?", "id_session": "test-ab"}
   ```

   **Critère de succès:** Temps de réponse moyen < 20s même avec 20 requêtes simultanées

---

## Monitoring Continu

### Vérification Quotidienne

```bash
# Script cron pour vérifier la santé quotidiennement
0 8 * * * /chemin/vers/test_deploiement_complet.sh http://IP_NAS:9000 > /var/log/mila-assist-health.log 2>&1
```

### Métriques à Surveiller

Selon `spec.md`, configurer Grafana pour surveiller:

| Métrique | Seuil d'Alerte | Prometheus Query |
|----------|----------------|------------------|
| Temps de réponse p95 | > 20s | `histogram_quantile(0.95, pipeline_latence_seconds)` |
| Taux de feedbacks négatifs | > 30% | `reponse_note_distribution{note<3}` |
| Cache hit rate | < 40% | `cache_hit_rate` |
| RAM usage | > 90% | `ram_usage_bytes / total_ram` |

### Logs à Consulter

Logs disponibles (selon `docker-compose.yml`):

```bash
# Logs API (FastAPI + IA Engine)
tail -f deploy-nas/log/api/*.log

# Logs MySQL
tail -f deploy-nas/log/mysql/*.log

# Logs phpMyAdmin
tail -f deploy-nas/log/phpmyadmin/*.log

# Logs Docker (si pas de volume monté)
docker logs -f mila_assist_api
docker logs -f mila_assist_mysql
```

---

## Validation des Success Criteria

Checklist complète selon `spec.md`:

- [ ] **SC-001**: 95% des questions reçoivent une réponse en < 20s
  - ✅ Validé par `test_qualite_reponses.py`

- [ ] **SC-002**: 85% des utilisateurs considèrent les réponses pertinentes (score > 3/5)
  - ✅ Validé par `test_qualite_reponses.py` (pertinence automatique)
  - ⚠️ À confirmer manuellement avec vrais utilisateurs

- [ ] **SC-003**: Soumission de feedback en < 1 minute
  - ✅ Validé par `test_qualite_reponses.py`

- [ ] **SC-004**: Admin peut traiter 10 feedbacks en < 15 minutes
  - ⚠️ Test manuel requis (accéder au dashboard admin)

- [ ] **SC-005**: Taux de réponses incorrectes diminue de 30% après 1 mois
  - ⏳ Nécessite monitoring sur 1 mois (impossible en pré-production)

- [ ] **SC-006**: Temps < 20s même avec 20 utilisateurs simultanés
  - ⚠️ Test de charge requis (voir Étape 3 ci-dessus)

- [ ] **SC-007**: 100% des feedbacks enregistrés et consultables
  - ✅ Validé par `test_deploiement_complet.sh` + `test_qualite_reponses.py`

- [ ] **SC-008**: Zéro perte de données en cas d'erreur
  - ⚠️ Test manuel requis:
    1. Soumettre un feedback
    2. Redémarrer le container API
    3. Vérifier que le feedback est toujours en base MySQL

---

## Dépannage

### Erreur: "curl: (7) Failed to connect"

**Cause:** L'API n'est pas accessible

**Solutions:**
1. Vérifier que les containers sont démarrés: `docker ps`
2. Vérifier le port mapping: `docker port mila_assist_api`
3. Vérifier le firewall du NAS
4. Tester depuis le NAS lui-même: `curl http://localhost:9000/api/v1/sante`

### Erreur: "mysql: command not found"

**Cause:** Client MySQL non installé

**Solutions:**
```bash
# Debian/Ubuntu
sudo apt-get install mysql-client

# Alpine (dans un container)
apk add mysql-client

# Ou skipper les tests MySQL (non recommandé)
# Le script continuera avec des warnings
```

### Tests de qualité: Pertinence faible

**Cause:** La base de connaissances ne contient pas les informations attendues

**Solutions:**
1. Vérifier le contenu de la table `base_connaissances`:
   ```sql
   SELECT * FROM base_connaissances WHERE etiquette LIKE '%ai_licia%';
   ```
2. Ajouter/modifier les entrées manquantes via phpMyAdmin (port 18548)
3. Regénérer l'index FAISS:
   ```bash
   python3 generer_index_faiss.py
   ```
4. Redémarrer le container API pour recharger l'index

### Tests de qualité: Temps > 20s

**Cause:** Ressources insuffisantes ou modèle trop lent

**Solutions:**
1. Vérifier l'utilisation CPU/RAM:
   ```bash
   docker stats mila_assist_api
   ```
2. Augmenter la RAM allouée au container (modifier `docker-compose.yml`)
3. Vérifier que le modèle Q4 est bien utilisé (pas FP16)
4. Augmenter le cache LRU (variable `CACHE_SIZE` dans `.env`)

---

## Contribution

Pour ajouter de nouveaux tests:

1. **Tests d'infrastructure** → Modifier `test_deploiement_complet.sh`
2. **Tests de qualité** → Ajouter des questions dans `QUESTIONS_TEST` de `test_qualite_reponses.py`
3. **Tests de charge** → Créer un nouveau script `test_charge.sh`

Structure recommandée:
```
tests/
├── README_TESTS.md               # Ce fichier
├── test_deploiement_complet.sh   # Tests infrastructure
├── test_qualite_reponses.py      # Tests qualité
├── test_charge.sh                # Tests de charge (à créer)
└── fixtures/                     # Données de test
    ├── questions_test.json
    └── feedbacks_test.json
```

---

## Références

- **Spécifications:** `specs/001-chatbot-support-retour/spec.md`
- **Plan d'implémentation:** `specs/001-chatbot-support-retour/plan.md`
- **Tasks:** `specs/001-chatbot-support-retour/tasks.md`
- **Docker Compose:** `deploy-nas/docker-compose.yml`
- **Documentation API:** `http://IP_NAS:9000/docs` (FastAPI Swagger)

---

**Dernière mise à jour:** 2025-01-26
**Auteur:** Claude Code
**Version:** 1.0.0
