# Mila-Assist - Déploiement sur Synology NAS

**Version** : 2.0 - Déploiement automatisé
**Date** : 2025-11-28

---

## [DEMARRAGE] Démarrage rapide

### Pré-requis
- Synology NAS avec Container Manager installé
- Dossier projet : `/volume1/docker/RNCP-6/Mila-assit/`

### Installation automatique

1. **Configurez** le fichier `.env` (voir section Configuration ci-dessous)
2. **Arrêtez** le projet actuel (si existant)
3. **Supprimez** le contenu de `mysql_data/`
4. **Uploadez** tous les fichiers de ce dossier sur le NAS
5. **Démarrez** le projet dans Container Manager
6. **Attendez** 3-5 minutes (init automatique)

### 🔐 Configuration (IMPORTANT)

**Avant le premier démarrage**, configurez vos informations sensibles :

```bash
# 1. Copiez le template
cp .env.example .env

# 2. Éditez le fichier .env et remplacez:
# - MYSQL_ROOT_PASSWORD
# - MYSQL_PASSWORD
# - API_KEY
# - JWT_SECRET_KEY
# - SECRET_KEY
# - CORS_ORIGINS (avec votre domaine NAS)

# 3. Générez des clés sécurisées (optionnel):
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**[ATTENTION] SÉCURITÉ**:
- Le fichier `.env` contient des informations sensibles
- Il est dans `.gitignore` et ne sera JAMAIS commité
- Ne partagez JAMAIS votre fichier `.env`
- Utilisez `.env.example` comme template

[OK] **Tout se fait automatiquement** :
- Migration de 218 entrées vers MySQL
- Création de l'index FAISS
- Configuration LLM optimisée

---

## [FOLDER] Structure du projet

```
deploy-nas/
├── README.md                           ← Ce fichier
├── .env                                ← Configuration (LLM_MAX_TOKENS=150)
├── docker-compose.yml                  ← Services Docker
│
├── GUIDE_DEPLOIEMENT_AUTOMATIQUE.md    ← Guide complet de déploiement
├── PARAMETRES_LLM_V2.md                ← Documentation paramètres LLM
├── PORTS_CONFIGURATION.md              ← Référence des ports réseau
├── GUIDE_REDIRECTION_PORTS.md          ← Config redirection ports NAS
│
├── backend/
│   ├── scripts/
│   │   ├── init_faiss_auto.py          ← Création auto index FAISS
│   │   ├── migrer_intents.py
│   │   └── creer_index_faiss.py
│   └── src/                            ← Code source API
│
├── mysql/
│   ├── init.sql                        ← Création tables MySQL
│   └── 02-migration_base_connaissances.sql  ← 218 entrées auto
│
├── donnees/
│   └── faiss_index/                    ← Index FAISS (créé auto)
│
├── modeles/                            ← Modèles IA
├── frontend/                           ← Interface web
├── log/                                ← Logs des containers
│
└── Utilitaires/
    ├── tester_api.py                   ← Tests API
    ├── verifier_deploiement.sh         ← Vérification déploiement
    └── telecharger_modele.sh           ← Téléchargement modèles
```

---

## Configuration

### Variables d'environnement (`.env`)

Paramètres LLM optimisés :
```bash
LLM_MAX_TOKENS=150          # Limite génération (20-30s par réponse)
LLM_TEMPERATURE=0.7         # Cohérence des réponses
LLM_TOP_P=0.9               # Nucleus sampling
LLM_TOP_K=40                # Top-k sampling
LLM_REPETITION_PENALTY=1.1  # Anti-répétition
```

### Ports exposés

| Service | Port Interne | Port Externe | Usage |
|---------|--------------|--------------|-------|
| API FastAPI | 8000 | **9000** | API REST + Interface web |
| phpMyAdmin | 80 | **18548** | Admin MySQL |
| MySQL | 3306 | - | Interne uniquement |

**Accès** :
- API : http://IP_NAS:9000
- Docs API : http://IP_NAS:9000/docs
- phpMyAdmin : http://IP_NAS:18548

---

## 📖 Documentation

| Fichier | Description |
|---------|-------------|
| **GUIDE_DEPLOIEMENT_AUTOMATIQUE.md** | 📘 Guide complet de déploiement |
| **PARAMETRES_LLM_V2.md** | 📗 Explication paramètres LLM |
| **PORTS_CONFIGURATION.md** | 📙 Référence ports réseau |
| **GUIDE_REDIRECTION_PORTS.md** | 📕 Configuration NAT/firewall |

---

## [TEST] Tests et vérification

### Test rapide de l'API

```bash
curl -k http://ezi0.synology.me:9000/api/v1/sante
```

**Résultat attendu** :
```json
{
  "statut": "healthy",
  "composants": {
    "mysql": "healthy",
    "pipeline_rag": "healthy",
    "embeddings": "healthy",
    "llm": "healthy"
  }
}
```

### Test de conversation

```bash
curl -k -X POST "http://ezi0.synology.me:9000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "Bonjour", "id_session": "123e4567-e89b-12d3-a456-426614174000"}'
```

**Temps de réponse attendu** : ~20-30 secondes [OK]

### Script de vérification complet

```bash
bash verifier_deploiement.sh
```

---

## [CONFIG] Dépannage

### Problème : API ne démarre pas

**Logs** :
```bash
docker logs mila_assist_api
```

**Cherchez** :
- `"INITIALISATION AUTOMATIQUE INDEX FAISS"`
- `"218 entrées chargées"`
- `"Index FAISS créé avec succès"`

### Problème : Table base_connaissances vide

**Vérifier** :
1. Logs MySQL : `docker logs mila_assist_mysql`
2. Fichier existe : `ls -lh mysql/02-migration_base_connaissances.sql`
3. Via phpMyAdmin : `SELECT COUNT(*) FROM base_connaissances;`

**Solution** : Supprimez `mysql_data/` et redémarrez

### Problème : Temps de réponse >30s

**Ajuster** dans `.env` :
```bash
LLM_MAX_TOKENS=100  # Réduit le temps à ~15-20s
```

Puis redémarrez les containers.

---

## [STATS] Métriques de performance

| Métrique | Valeur |
|----------|--------|
| Entrées base de connaissances | 218 |
| Dimension vecteurs FAISS | 768 (CamemBERT FR) |
| Taille index FAISS | ~600-1000 KB |
| Temps de réponse moyen | 20-30 secondes |
| Tokens générés par réponse | ~112 (150 max) |

---

## [SYNC] Mise à jour

### Modifier les paramètres LLM

1. Éditez `.env` sur le NAS
2. Redémarrez les containers :
   ```bash
   docker restart mila_assist_api
   ```

### Ajouter des données

1. Éditez `mysql/02-migration_base_connaissances.sql`
2. Supprimez `mysql_data/`
3. Redémarrez le projet (réinitialisation complète)

---

## 🆘 Support

**Logs** :
```bash
docker logs mila_assist_api
docker logs mila_assist_mysql
```

**Restart complet** :
1. Arrêter le projet
2. Nettoyer les containers
3. Supprimer `mysql_data/`
4. Démarrer le projet

**Contact** : Consultez la documentation dans les fichiers `GUIDE_*.md`

---

## [OK] Checklist de déploiement

- [ ] Containers arrêtés
- [ ] Dossier `mysql_data/` vidé
- [ ] Tous les fichiers uploadés sur le NAS
- [ ] Projet démarré
- [ ] Attente 3-5 minutes
- [ ] API accessible (test `/api/v1/sante`)
- [ ] Conversation fonctionne (~20-30s)
- [ ] 218 entrées dans MySQL (phpMyAdmin)
- [ ] Index FAISS créé (~300-500 KB)

---

**Déploiement 100% automatique - Version 2.0** [DEMARRAGE]
