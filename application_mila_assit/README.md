# Mila-Assist

**Chatbot IA de Support AI_licia & Streaming avec Architecture RAG**

Projet RNCP Niveau 6 - Assistant conversationnel intelligent pour le support technique d'AI_licia et du streaming.

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Déploiement](#déploiement)
- [API Reference](#api-reference)
- [Pipeline RAG](#pipeline-rag)
- [Configuration](#configuration)
- [Développement](#développement)
- [Tests](#tests)

---

## Vue d'ensemble

Mila-Assist est un chatbot intelligent basé sur une architecture **RAG (Retrieval-Augmented Generation)** qui combine :

| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Embeddings** | CamemBERT MS MARCO FR | Modèle français optimisé pour la recherche sémantique (768 dim) |
| **Recherche** | FAISS IndexFlatIP | Recherche vectorielle par produit scalaire |
| **LLM** | Gemma-2-2B Q4 GGUF | Génération de texte quantifiée pour CPU |
| **Base de données** | MySQL 8.0 | Stockage des connaissances et conversations |
| **API** | FastAPI | API REST avec authentification JWT |

### Caractéristiques principales

- Architecture optimisée pour CPU (pas de GPU requis)
- Déployable sur NAS Synology DS423+ (6 Go RAM)
- Interface web de démonstration incluse
- Système de feedback utilisateur
- Auto-synchronisation FAISS
- Conformité RGPD (purge automatique 90 jours)

---

## Architecture

### Architecture 4 Containers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NAS Synology (Container Manager)                  │
│                                                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  Container 1    │    │  Container 2    │    │  Container 3    │ │
│  │    MySQL 8.0    │◄───│  API Backend    │───►│  LLM + FAISS    │ │
│  │                 │    │   (FastAPI)     │    │   Service       │ │
│  │  RAM: 1.5 GB    │    │  RAM: 2 GB      │    │  RAM: 3.5 GB    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           ▲                      ▲                                   │
│           │                      │                                   │
│  ┌─────────────────┐            │                                   │
│  │  Container 4    │            │                                   │
│  │   phpMyAdmin    │      Client (Web/Qt)                           │
│  │  RAM: 512 MB    │                                                 │
│  └─────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Flux de données

```
Question utilisateur
        │
        ▼
┌───────────────────┐
│ Client (Widget/Qt)│ ── Calcul embedding local (CamemBERT 768 dim)
└─────────┬─────────┘
          │ POST /api/v1/search {question, embedding}
          ▼
┌───────────────────┐
│  Container 2 API  │ ── Validation, rate limiting, logging
└─────────┬─────────┘
          │ HTTP POST /search
          ▼
┌───────────────────┐
│  Container 3 LLM  │ ── FAISS recherche top-k similaires
│                   │ ── MySQL récupère contexte
│                   │ ── LLM génère réponse
└─────────┬─────────┘
          │
          ▼
    Réponse JSON
    {reponse, confiance, sources, temps_ms}
```

---

## Prérequis

### Matériel

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 6 GB | 8 GB |
| CPU | 4 cores | 6+ cores |
| Stockage | 10 GB | 20 GB |

### Logiciels

- Docker 24+ et Docker Compose 2.0+
- Python 3.10+ (pour développement local)
- NAS Synology avec Container Manager (pour production)

### Modèles IA (à télécharger)

| Modèle | Taille | Usage |
|--------|--------|-------|
| `antoinelouis/biencoder-camembert-base-mmarcoFR` | ~500 MB | Embeddings français |
| `gemma-2-2b-it-q4.gguf` | ~1.2 GB | Génération de texte |

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-org/mila-assist.git
cd mila-assist
```

### 2. Configuration

```bash
# Copier le fichier d'environnement
cd deploy-nas
cp .env.example .env

# Éditer les variables
nano .env
```

Variables obligatoires :
```env
MYSQL_ROOT_PASSWORD=VotreMotDePasseRoot
MYSQL_PASSWORD=VotreMotDePasse
JWT_SECRET_KEY=VotreCleSecrete32CaracteresMin
API_KEY=VotreCleAPI
```

### 3. Créer les dossiers

```bash
mkdir -p log/{mysql,api,llm}
mkdir -p backups/faiss
mkdir -p donnees/faiss_index
mkdir -p cache_huggingface
mkdir -p modeles/{gemma,embeddings}
```

### 4. Télécharger les modèles

```bash
# Le modèle Gemma-2-2B Q4 GGUF
wget -O modeles/gemma/gemma-2-2b-it-q4.gguf \
    "https://huggingface.co/lmstudio-ai/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf"

# Les embeddings sont téléchargés automatiquement au démarrage
```

### 5. Démarrer les services

```bash
docker-compose up -d
```

---

## Déploiement

### Via Docker Compose

```bash
cd deploy-nas
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Vérifier la santé
curl http://localhost:9000/api/v1/sante
```

### Via Synology Container Manager

1. Copier le dossier `deploy-nas/` dans `/volume1/docker/Mila-Assist/`
2. Ouvrir Container Manager → Projet → Créer
3. Sélectionner le dossier et lancer

### Ordre de démarrage (automatique)

1. MySQL (healthcheck: mysqladmin ping)
2. LLM+FAISS Service (healthcheck: /health)
3. API Backend (healthcheck: /api/v1/sante)
4. phpMyAdmin

---

## 📡 API Reference

### Base URL

- **Production** : `https://votre-nas:9000/api/v1`
- **Local** : `http://localhost:9000/api/v1`

### Endpoints principaux

#### POST `/search` - Poser une question

```bash
curl -X POST "http://localhost:9000/api/v1/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre-cle-api" \
  -d '{
    "id_session": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Comment configurer le TTS ?",
    "embedding": [0.1, 0.2, ..., 0.768]
  }'
```

**Réponse** :
```json
{
  "id_conversation": 1234,
  "reponse": "Pour configurer le TTS, rendez-vous dans...",
  "confiance": 0.92,
  "sources": [245, 773, 891],
  "temps_ms": 1250
}
```

#### GET `/sante` - Healthcheck

```bash
curl "http://localhost:9000/api/v1/sante"
```

**Réponse** :
```json
{
  "statut": "healthy",
  "version": "1.0.0",
  "composants": {
    "mysql": "healthy",
    "container_3_llm_faiss": "healthy",
    "faiss_index": "loaded (1366 vecteurs)",
    "llm_model": "loaded"
  }
}
```

#### POST `/retour-utilisateur` - Soumettre un feedback

```bash
curl -X POST "http://localhost:9000/api/v1/retour-utilisateur" \
  -H "Content-Type: application/json" \
  -d '{
    "id_conversation": 1234,
    "note": 5,
    "commentaire": "Réponse parfaite !"
  }'
```

#### POST `/admin/faiss/rebuild` - Reconstruire l'index FAISS

```bash
curl -X POST "http://localhost:9000/api/v1/admin/faiss/rebuild"
```

---

## 🔬 Pipeline RAG

### Étapes du pipeline

1. **Embedding** : Le texte est encodé en vecteur 768 dimensions via CamemBERT
2. **Recherche FAISS** : Top-K vecteurs les plus similaires (produit scalaire)
3. **Récupération contexte** : MySQL retourne les Q&R correspondantes
4. **Génération** : Gemma-2B génère une réponse naturelle

### Preprocessing ML

Le module `ml_preprocessing.py` fournit :

- **Stopwords français** : 200+ mots vides pour le nettoyage
- **Tokenization** : Découpage adapté au français
- **Métriques** : Precision, Recall, F1, MRR, NDCG

```python
from src.ml_preprocessing import nettoyer_texte, calculer_metriques_retrieval

# Nettoyage
texte = nettoyer_texte("Comment configurer le TTS sur AI_licia ?")
# → "configurer tts ai_licia"

# Métriques
metriques = calculer_metriques_retrieval(
    predictions=[1, 5, 3],
    ground_truth=[1, 2, 3],
    k=3
)
# → {'precision': 0.667, 'recall': 0.667, 'f1': 0.667}
```

### Score de confiance

Le score FAISS (produit scalaire sur vecteurs normalisés) est normalisé :

```python
# Normalisation du score [-1, 1] → [0, 1]
confiance = max(0.0, min(1.0, (raw_score + 1.0) / 2.0))
```

---

## Configuration

### Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `MYSQL_HOST` | mysql | Hostname MySQL |
| `MYSQL_PASSWORD` | - | Mot de passe MySQL (requis) |
| `JWT_SECRET_KEY` | - | Clé secrète JWT 32+ caractères (requis) |
| `EMBEDDINGS_MODEL_NAME` | `antoinelouis/biencoder-camembert-base-mmarcoFR` | Modèle d'embeddings |
| `EMBEDDINGS_DIMENSION` | 768 | Dimension des vecteurs |
| `LLM_MODEL_PATH` | `/app/modeles/gemma/gemma-2-2b-it-q4.gguf` | Chemin modèle LLM |
| `LLM_TEMPERATURE` | 0.3 | Créativité (0=déterministe, 1=créatif) |
| `LLM_MAX_TOKENS` | 200 | Longueur max réponse |
| `FAISS_TOP_K` | 3 | Nombre de résultats FAISS |
| `AUTO_SYNC_INTERVAL` | 60 | Intervalle sync FAISS (secondes) |
| `LOG_LEVEL` | INFO | Niveau de logging |

### Auto-sync FAISS

L'index FAISS est automatiquement reconstruit si :

1. L'index n'existe pas au démarrage
2. MySQL a redémarré (uptime < 5 minutes)
3. La base de connaissances a été modifiée

---

##  Développement

### Structure du projet

```
mila-assist/
├── deploy-nas/
│   ├── backend/                 # Container 2: API FastAPI
│   │   ├── src/
│   │   │   ├── api/            # Routes FastAPI
│   │   │   ├── base_donnees/   # Requêtes MySQL
│   │   │   ├── clients/        # Client HTTP vers Container 3
│   │   │   ├── modeles/        # Schémas Pydantic
│   │   │   ├── securite/       # Auth JWT, validation
│   │   │   └── utilitaires/    # Config, logger, exceptions
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── llm-service/            # Container 3: LLM + FAISS
│   │   ├── src/
│   │   │   ├── embeddings.py   # Encodeur CamemBERT
│   │   │   ├── faiss_manager.py # Index FAISS
│   │   │   ├── generateur_llm.py # Gemma-2B
│   │   │   ├── auto_sync.py    # Sync automatique
│   │   │   ├── ml_preprocessing.py # Stopwords, métriques
│   │   │   └── llm_server.py   # FastAPI interne
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── mysql/                  # Scripts SQL
│   ├── widget-demo/            # Interface web démo
│   └── docker-compose.yml
├── client/                     # Client desktop Qt
├── docs/                       # Documentation
├── specs/                      # Spécifications
└── tests/                      # Tests
```

### Lancer en local

```bash
# Backend API
cd deploy-nas/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000

# LLM Service
cd deploy-nas/llm-service
pip install -r requirements.txt
uvicorn src.llm_server:app --port 8001
```

---

##  Tests

### Lancer les tests

```bash
cd tests
./run_all_tests.sh
```

### Tests unitaires

```bash
pytest deploy-nas/backend/tests/ -v
```

### Tests de charge

```bash
locust -f tests/locustfile.py --host http://localhost:9000
```

---

## Performances

| Métrique | Cible | Mesuré |
|----------|-------|--------|
| Latence moyenne | < 2s | ~1.5s |
| Latence P95 | < 5s | ~3.5s |
| Precision@3 | > 85% | ~90% |
| RAM totale | < 6 GB | ~5.5 GB |
| Utilisateurs simultanés | 50 | Testé |

---

## Sécurité

- Authentification JWT pour les endpoints sensibles
- Rate limiting (100 req/min par utilisateur)
- Validation des entrées (XSS, injection SQL)
- CORS configuré
- Purge automatique RGPD (90 jours)
- Logs sécurisés

---

## Licence

[À définir]

---

## 👥 Auteurs

Projet développé dans le cadre du RNCP Niveau 6 - Support technique AI_licia.
