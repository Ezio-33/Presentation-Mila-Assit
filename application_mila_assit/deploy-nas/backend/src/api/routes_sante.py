"""
Routes API pour la santé et les métriques de l'application.

Fournit des endpoints pour vérifier l'état de l'application
et obtenir des statistiques de performance.
"""

import psutil
from fastapi import APIRouter, Request, HTTPException, status
from src.modeles.metrique import ReponseSante, ReponseMetriques, StatutSante
from src.base_donnees.connexion import obtenir_connexion
from src.base_donnees.requetes_metriques import (
    obtenir_latence_moyenne,
    obtenir_taux_cache_hit
)
from src.utilitaires.logger import obtenir_logger
from src.utilitaires.exceptions import ErreurBaseDeDonnees

# Logger
logger = obtenir_logger(__name__)

# Router
router = APIRouter()


@router.get("/sante", response_model=ReponseSante)
async def verifier_sante(request: Request):
    """
    Vérifie l'état de santé de l'application et de ses composants.

    Args:
        request: Objet Request FastAPI

    Returns:
        Statut de santé global et détails par composant

    Raises:
        HTTPException 503: Si l'application est unhealthy
    """
    composants = {}
    statut_global = StatutSante.HEALTHY

    # Vérifier MySQL
    try:
        connexion = obtenir_connexion()
        connexion.ping(reconnect=True)
        connexion.close()
        composants["mysql"] = "healthy"
        logger.debug("MySQL : healthy")
    except Exception as e:
        logger.error(f"Erreur connexion MySQL : {str(e)}")
        composants["mysql"] = "unhealthy"
        statut_global = StatutSante.UNHEALTHY

    # Vérifier Container 3 (LLM+FAISS)
    try:
        from src.clients.llm_client import obtenir_llm_client

        llm_client = obtenir_llm_client()
        health_c3 = llm_client.healthcheck()

        if health_c3.get("statut") == "healthy":
            composants["container_3_llm_faiss"] = "healthy"

            # Vérifier les sous-composants depuis Container 3
            c3_composants = health_c3.get("composants", {})
            composants["faiss_index"] = c3_composants.get("faiss", "unknown")
            composants["llm_model"] = c3_composants.get("llm", "unknown")
            composants["embeddings_model"] = c3_composants.get("embeddings", "unknown")

            logger.debug("Container 3 (LLM+FAISS) : healthy")
        else:
            composants["container_3_llm_faiss"] = "unhealthy"
            statut_global = StatutSante.UNHEALTHY

    except Exception as e:
        logger.error(f"Erreur connexion Container 3 : {str(e)}")
        composants["container_3_llm_faiss"] = "unhealthy"
        composants["faiss_index"] = "unknown"
        composants["llm_model"] = "unknown"
        composants["embeddings_model"] = "unknown"
        statut_global = StatutSante.UNHEALTHY

    # Construire la réponse
    reponse = ReponseSante(
        statut=statut_global,
        version="1.0.0",
        composants=composants
    )

    # Retourner 503 si unhealthy
    if statut_global == StatutSante.UNHEALTHY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=reponse.model_dump(mode='json')
        )

    return reponse


@router.get("/metriques", response_model=ReponseMetriques)
async def obtenir_metriques(periode: str = "24h"):
    """
    Obtient les métriques de performance de l'application.

    Args:
        periode: Période pour les métriques ('24h', '7d', '30d')

    Returns:
        Métriques de latence, cache, RAM et satisfaction

    Raises:
        HTTPException 400: Si la période est invalide
        HTTPException 500: En cas d'erreur serveur
    """
    # Valider la période
    periodes_valides = ["24h", "7d", "30d"]
    if periode not in periodes_valides:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Période invalide. Valeurs autorisées : {', '.join(periodes_valides)}"
        )

    try:
        # Obtenir les métriques depuis la base de données
        latence_moy = obtenir_latence_moyenne(periode=periode)
        taux_cache = obtenir_taux_cache_hit(periode=periode)

        # Calculer l'utilisation RAM
        process = psutil.Process()
        ram_bytes = process.memory_info().rss
        ram_go = ram_bytes / (1024 ** 3)  # Convertir en Go

        # Pour les percentiles et le total, on utilise des valeurs par défaut
        # (à améliorer avec de vraies requêtes SQL dans requetes_metriques.py)
        p95 = int(latence_moy * 1.8)  # Approximation
        p99 = int(latence_moy * 2.5)  # Approximation

        # Construire la réponse
        reponse = ReponseMetriques(
            latence_moyenne_ms=latence_moy,
            latence_p95_ms=p95,
            latence_p99_ms=p99,
            taux_cache_hit=taux_cache,
            utilisation_ram_go=round(ram_go, 2),
            total_requetes=0,  # À améliorer avec COUNT(*) sur conversations
            satisfaction_moyenne=None,  # Sera ajouté en US2
            periode=periode
        )

        logger.info(
            f"Métriques ({periode}) : latence={latence_moy:.0f}ms, "
            f"cache={taux_cache:.2%}, RAM={ram_go:.2f}Go"
        )

        return reponse

    except ErreurBaseDeDonnees as e:
        logger.error(f"Erreur lors de la récupération des métriques : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer les métriques"
        )
    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite"
        )
