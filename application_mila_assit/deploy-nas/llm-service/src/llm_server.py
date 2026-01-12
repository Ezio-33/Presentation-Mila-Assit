"""
Serveur FastAPI pour Container 3 (LLM + FAISS Service).

Endpoints:
- POST /search : Recherche FAISS + génération LLM
- GET /health : Healthcheck
- POST /admin/rebuild : Force rebuild FAISS
- GET /admin/status : Statut auto-sync
"""

import logging
import os
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import mysql.connector

# Import modules locaux
from src.embeddings import obtenir_encodeur
from src.faiss_manager import obtenir_index
from src.generateur_llm import obtenir_generateur, llm_est_disponible
from src.auto_sync import obtenir_auto_sync
from src.ml_preprocessing import nettoyer_texte

# ============================================================================
# Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MySQL Config
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "mila_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mila_assist")


# ============================================================================
# Modèles Pydantic
# ============================================================================

class RequeteRecherche(BaseModel):
    """Requête de recherche avec embedding."""
    embedding: Optional[List[float]] = Field(None, description="Vecteur embedding (768 dimensions CamemBERT) - optionnel, calculé automatiquement si absent")
    question: str = Field(..., description="Question originale")
    k: int = Field(default=3, description="Nombre de résultats")


class ReponseRecherche(BaseModel):
    """Réponse avec génération LLM."""
    reponse: str = Field(..., description="Réponse générée par le LLM")
    confiance: float = Field(..., description="Score de confiance (0-1)")
    sources: List[int] = Field(..., description="IDs base_connaissances utilisés")
    temps_ms: int = Field(..., description="Temps de traitement (ms)")


class ReponseSante(BaseModel):
    """Statut de santé du service."""
    statut: str
    composants: Dict[str, str]


# ============================================================================
# Lifecycle Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gere le cycle de vie de l'application."""
    logger.info("[DEMARRAGE] Container 3 (LLM + FAISS Service)...")
    logger.info("=" * 70)

    # Debug environnement au démarrage
    logger.info("Debug - Variables d'environnement:")
    logger.info(f"  MYSQL_HOST: {os.getenv('MYSQL_HOST', 'non défini')}")
    logger.info(f"  HF_HOME: {os.getenv('HF_HOME', 'non défini')}")
    logger.info(f"  TRANSFORMERS_CACHE: {os.getenv('TRANSFORMERS_CACHE', 'non défini')}")
    logger.info(f"  EMBEDDINGS_MODEL_NAME: {os.getenv('EMBEDDINGS_MODEL_NAME', 'non défini')}")
    logger.info(f"  EMBEDDINGS_MODEL_PATH: {os.getenv('EMBEDDINGS_MODEL_PATH', 'non défini')}")
    logger.info(f"  FAISS_INDEX_PATH: {os.getenv('FAISS_INDEX_PATH', 'non défini')}")
    logger.info(f"  LLM_MODEL_PATH: {os.getenv('LLM_MODEL_PATH', 'non défini')}")

    # Debug user et permissions
    logger.info("Debug - Utilisateur et permissions:")
    logger.info(f"  UID: {os.getuid()}")
    logger.info(f"  GID: {os.getgid()}")
    logger.info(f"  Working dir: {os.getcwd()}")

    # Vérifier dossiers critiques
    for path_name, path_value in [
        ("Cache HF", os.getenv('HF_HOME', '/app/cache_huggingface')),
        ("FAISS Index", os.getenv('FAISS_INDEX_PATH', '/app/donnees/faiss_index')),
        ("Modèles LLM", os.getenv('LLM_MODEL_PATH', '/app/modeles'))
    ]:
        if os.path.exists(path_value):
            stat_info = os.stat(path_value)
            perms = oct(stat_info.st_mode)[-3:]
            logger.info(f"  {path_name}: existe - {perms} {stat_info.st_uid}:{stat_info.st_gid}")
        else:
            logger.warning(f"  {path_name}: N'EXISTE PAS - {path_value}")

    logger.info("=" * 70)

    try:
        # Initialiser les composants
        logger.info("Chargement des composants...")
        encodeur = obtenir_encodeur()
        index_faiss = obtenir_index()
        
        # LLM optionnel - le service peut fonctionner en mode RAG seul
        generateur = obtenir_generateur(optionnel=True)
        if generateur:
            logger.info("[OK] LLM chargé - Mode complet (RAG + génération)")
        else:
            logger.warning("[ATTENTION] LLM non disponible - Mode RAG seul (sans génération)")
            logger.warning("           Pour activer la génération, placez le modèle Gemma dans:")
            logger.warning("           modeles/gemma/gemma-2-2b-it-q4.gguf (~1.5 Go)")

        # Démarrer auto-sync
        auto_sync = obtenir_auto_sync(index_faiss, encodeur)
        auto_sync.demarrer()

        logger.info("[OK] Container 3 pret")

        yield

        # Shutdown
        logger.info("Arrêt du Container 3...")
        auto_sync.arreter()
        logger.info("[OK] Arret termine")

    except Exception as e:
        logger.error(f"[ERREUR] Erreur critique au demarrage: {e}")
        raise


# ============================================================================
# Application FastAPI
# ============================================================================

app = FastAPI(
    title="Mila-Assist LLM+FAISS Service",
    description="Service dédié pour recherche FAISS et génération LLM",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Endpoints
# ============================================================================

@app.post("/search", response_model=ReponseRecherche)
async def rechercher_et_generer(requete: RequeteRecherche):
    """
    Recherche FAISS + génération LLM.

    1. Recherche top-k dans FAISS
    2. Récupère contexte depuis MySQL
    3. Génère réponse avec LLM
    """
    import time
    start_time = time.time()

    try:
        # 1. Convertir embedding en numpy array (ou le calculer si non fourni)
        if requete.embedding is not None:
            embedding_np = np.array(requete.embedding, dtype=np.float32).reshape(1, -1)
        else:
            # Calculer l'embedding avec l'encodeur local
            # IMPORTANT: Appliquer le même nettoyage que le client natif pour cohérence
            texte_pour_embedding = nettoyer_texte(requete.question, supprimer_stopwords=False)
            logger.info(f"Calcul de l'embedding pour: '{texte_pour_embedding[:50]}...'")
            encodeur = obtenir_encodeur()
            embedding_np = encodeur.encoder(texte_pour_embedding, normalize=True).reshape(1, -1)

        # 2. Recherche FAISS
        index_faiss = obtenir_index()
        distances, indices = index_faiss.rechercher(embedding_np, k=requete.k)

        # Convertir indices FAISS en IDs MySQL
        ids_mysql = index_faiss.obtenir_ids_mysql(indices)

        if not ids_mysql or ids_mysql[0] == -1:
            raise HTTPException(status_code=404, detail="Aucun résultat trouvé")

        # 3. Récupérer contexte depuis MySQL
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)

        placeholders = ','.join(['%s'] * len(ids_mysql))
        query = f"""
            SELECT id, question, reponse
            FROM base_connaissances
            WHERE id IN ({placeholders})
            ORDER BY FIELD(id, {placeholders})
        """
        cursor.execute(query, ids_mysql + ids_mysql)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        # Construire le contexte
        contexte_parts = []
        for row in rows:
            contexte_parts.append(f"Q: {row['question']}\nR: {row['reponse']}")

        contexte = "\n\n".join(contexte_parts)

        # 4. Générer réponse avec LLM (ou retourner contexte si LLM indisponible)
        generateur = obtenir_generateur(optionnel=True)
        if generateur:
            reponse_llm = generateur.generer_reponse_chatbot(
                question=requete.question,
                contexte=contexte,
                max_tokens=400  # Augmenté pour permettre des réponses multi-questions
            )
        else:
            # Mode RAG seul - retourner la meilleure réponse du contexte
            if rows:
                reponse_llm = rows[0]['reponse']
            else:
                reponse_llm = "Aucune réponse trouvée dans la base de connaissances."

        # 5. Calculer temps et normaliser confiance
        temps_ms = int((time.time() - start_time) * 1000)

        # Normaliser le score de similarité (produit scalaire) entre 0 et 1
        # Le produit scalaire sur vecteurs normalisés est déjà dans [-1, 1]
        # On clip et normalise pour avoir [0, 1]
        raw_score = float(distances[0][0])
        confiance = max(0.0, min(1.0, (raw_score + 1.0) / 2.0))

        # 6. Ajouter un préfixe si confiance < 65%
        SEUIL_CONFIANCE = 0.65
        if confiance < SEUIL_CONFIANCE:
            reponse_llm = (
                "Je ne suis pas certain d'avoir bien compris votre question, "
                "mais voici ce que je peux vous dire : " + reponse_llm
            )
            logger.info(f"[INFO] Faible confiance ({confiance:.2%}) - Préfixe ajouté à la réponse")

        return ReponseRecherche(
            reponse=reponse_llm,
            confiance=confiance,
            sources=ids_mysql,
            temps_ms=temps_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERREUR] Erreur recherche: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=ReponseSante)
async def healthcheck():
    """Healthcheck du service."""
    try:
        encodeur = obtenir_encodeur()
        index_faiss = obtenir_index()
        
        # LLM optionnel
        llm_status = "loaded" if llm_est_disponible() else "non disponible (mode RAG seul)"

        return ReponseSante(
            statut="healthy",
            composants={
                "encodeur": "loaded",
                "index_faiss": f"loaded ({index_faiss.ntotal} vecteurs)",
                "generateur_llm": llm_status,
                "auto_sync": "actif"
            }
        )
    except Exception as e:
        logger.error(f"[ERREUR] Healthcheck failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/faiss/rebuild")
async def forcer_rebuild():
    """Force un rebuild de l'index FAISS (admin)."""
    try:
        auto_sync = obtenir_auto_sync()
        stats = auto_sync.forcer_rebuild()
        return {"message": "Rebuild terminé", "stats": stats}
    except Exception as e:
        logger.error(f"[ERREUR] Erreur rebuild: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/faiss/status")
async def obtenir_statut():
    """Obtient le statut de l'auto-sync (admin)."""
    try:
        auto_sync = obtenir_auto_sync()
        return auto_sync.obtenir_statut()
    except Exception as e:
        logger.error(f"[ERREUR] Erreur statut: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
