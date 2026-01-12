"""
Point d'entrée principal de l'API Mila-Assist.

Configure l'application FastAPI avec tous ses composants :
- Routes API
- Middlewares (CORS, rate limiting, logging)
- Client HTTP vers Container 3 (LLM + FAISS)
- Connexions base de données

Architecture 4 containers (9 Déc 2025):
Container 2 (API Backend) → Container 3 (LLM+FAISS) via HTTP
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.clients.llm_client import obtenir_llm_client
from src.base_donnees.connexion import obtenir_pool, fermer_pool
from src.utilitaires.logger import obtenir_logger
from src.utilitaires.config import obtenir_config
from src.api.middlewares import configurer_middlewares

# Logger
logger = obtenir_logger(__name__)

# Configuration
config = obtenir_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application (startup et shutdown).

    Args:
        app: Instance FastAPI
    """
    # Startup
    logger.info("[DEMARRAGE] Démarrage de Mila-Assist API (Container 2)...")

    try:
        # Initialiser le pool de connexions MySQL
        logger.info("Initialisation du pool de connexions MySQL...")
        pool = obtenir_pool()
        logger.info("✓ Pool de connexions MySQL initialisé")

        # Vérifier la connectivité avec Container 3 (LLM+FAISS)
        logger.info("Vérification de la connectivité avec Container 3 (LLM+FAISS)...")
        try:
            llm_client = obtenir_llm_client()
            health = llm_client.healthcheck()
            logger.info(f"✓ Container 3 opérationnel : {health.get('statut', 'unknown')}")
        except Exception as e:
            logger.warning(f"[ATTENTION] Container 3 non accessible au démarrage : {e}")
            logger.warning("   L'API démarrera mais les requêtes échoueront jusqu'à ce que Container 3 soit prêt")

        logger.info("[OK] Mila-Assist API (Container 2) démarrée avec succès")

    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors du démarrage : {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("🛑 Arrêt de Mila-Assist API...")

    try:
        # Fermer le pool de connexions
        logger.info("Fermeture du pool de connexions MySQL...")
        fermer_pool()
        logger.info("✓ Pool de connexions fermé")

        logger.info("[OK] Mila-Assist API arrêtée proprement")

    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors de l'arrêt : {str(e)}", exc_info=True)


# Créer l'application FastAPI
app = FastAPI(
    title="Mila-Assist API",
    description="API de chatbot intelligent avec support RAG et feedback utilisateur",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuration CORS - Autoriser toutes les origines pour widget et accès externe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines (fichiers locaux, domaines externes)
    allow_credentials=False,  # Doit être False quand allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"]
)

# Configuration des middlewares (rate limiting, logging)
configurer_middlewares(app)

# Import et enregistrement des routes
# Note: Les imports sont ici pour éviter les imports circulaires
try:
    from .routes_conversation import router as conversation_router
    from .routes_sante import router as sante_router
    from .routes_retour import router as retour_router
    from .routes_admin import router as admin_router

    app.include_router(conversation_router, prefix="/api/v1", tags=["Conversation"])
    app.include_router(sante_router, prefix="/api/v1", tags=["Santé"])
    app.include_router(retour_router, prefix="/api/v1", tags=["Retours"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Administration"])

    logger.info("✓ Routes enregistrées : conversation, santé, retours, admin")

except ImportError as e:
    logger.warning(f"[ATTENTION] Certaines routes n'ont pas pu etre importees : {str(e)}")


@app.get("/")
async def root():
    """
    Endpoint racine de l'API.

    Returns:
        Message de bienvenue
    """
    return {
        "message": "Bienvenue sur l'API Mila-Assist",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check simple pour vérifier que l'API répond.

    Returns:
        Statut de l'API
    """
    return {
        "status": "healthy",
        "service": "Mila-Assist API"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Démarrage du serveur uvicorn...")
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
