# Application Cliente Mila-Assist

**Type** : Application Desktop Python/PyQt5
**Version** : 2.0.0
**Date** : 12 Décembre 2025

---

## Description

Application desktop moderne pour accéder à Mila-Assist (NAS). Calcule les embeddings localement (sentence-transformers) et communique avec le backend API.

---

## Installation

```bash
# Activer l'environnement pyenv (si utilisé)
pyenv activate Projet-Perso

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app_mila_assist.py
```

---

## Fonctionnalités

- [OK] **Interface graphique PyQt5** moderne et intuitive
- [OK] **Calcul embeddings local** (CamemBERT MS MARCO FR - Optimisé français)
- [OK] **Détection multi-questions** (3 stratégies : numérotation, connecteurs, points d'interrogation)
- [OK] **Envoi vecteur 768 dimensions** à l'API
- [OK] **Affichage formaté** des réponses avec markdown, liens cliquables
- [OK] **Historique conversations** avec scroll automatique
- [OK] **Support feedback utilisateur** (notes + commentaires)
- [OK] **Effacement conversation** avec confirmation
- [OK] **Environnements multiples** (NAS, Mistral AI)
- [OK] **Spinner animé** pendant le traitement
- [OK] **Messages d'erreur** formatés en français

---

## Configuration

L'application est configurée pour se connecter au NAS par défaut :

```python
# Environnement NAS (par défaut)
URL: http://ezi0.synology.me:10443/api/v1
API_KEY: Configurée automatiquement

# Environnement Mistral AI (fallback)
URL: https://api.mistral.ai/v1/chat/completions
API_KEY: Configurée dans le code
```

---

## Architecture (4 Containers)

```
┌─────────────────────────────────┐
│ CLIENT Qt (app_mila_assist.py)  │
│  • Interface PyQt5 moderne      │
│  • Calcul embeddings local      │
│  • Validation + nettoyage       │
│  • Envoi vecteur 768 dim        │
└────────────┬────────────────────┘
             │ HTTP POST /search
             ↓
┌─────────────────────────────────┐
│ Container 2: API Backend        │
│  • Validation requête           │
│  • Orchestration                │
│  • Appel Container 3            │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│ Container 3: LLM + FAISS        │
│  • Recherche FAISS              │
│  • Génération LLM (Gemma-2-2B)  │
│  • Auto-sync MySQL              │
└─────────────────────────────────┘
```

---

## Dépendances

Voir `requirements.txt` :
- `PyQt5==5.15.11` : Interface graphique moderne
- `sentence-transformers==3.3.1` : Calcul embeddings (CamemBERT FR)
- `transformers==4.47.1` : Transformers Hugging Face
- `torch==2.5.1` : Backend pour sentence-transformers
- `requests==2.32.3` : Communication API
- `numpy<2.0` : Manipulation de tableaux

---

## Utilisation

1. **Lancer l'application** : `python app_mila_assist.py`
2. **Sélectionner l'environnement** : NAS (par défaut) ou Mistral AI
3. **Poser une question** dans le champ de saisie
4. **Recevoir la réponse** avec confiance et sources
5. **Donner un retour** (optionnel) avec le bouton "Donner un retour Donner un retour"
6. **Effacer la conversation** avec le bouton "Effacer Effacer"

---

## Notes

- Le premier lancement charge le modèle d'embeddings (1-2 minutes)
- Le modèle est mis en cache pour les utilisations suivantes
- Les connexions au NAS utilisent HTTP (pas HTTPS) sur le port 10443
- L'application gère automatiquement les timeouts et erreurs réseau
