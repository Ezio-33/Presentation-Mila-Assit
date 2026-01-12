"""
Routes API pour la gestion des retours utilisateurs (feedback).

Fournit les endpoints pour soumettre et gérer les feedbacks sur les réponses du chatbot.
"""

from fastapi import APIRouter, HTTPException, Request, status
from typing import List, Optional

from src.modeles.retour import (
    RequeteRetour,
    ReponseRetour,
    StatutRetour,
    CategorieProbleme,
    FeedbackAdmin,
    ReponseFeedbacksAdmin
)
from src.base_donnees.requetes_retours import (
    inserer_retour,
    obtenir_retour,
    obtenir_retours_par_conversation,
    obtenir_retours_par_note,
    obtenir_retours_par_statut,
    obtenir_retours_par_categorie,
    marquer_retour_traite,
    obtenir_statistiques_retours,
    compter_retours
)
from src.base_donnees.requetes_conversations import obtenir_conversation
from src.utilitaires.logger import obtenir_logger
from src.utilitaires.exceptions import (
    ErreurRequeteBD,
    ErreurEnregistrementIntrouvable,
    ErreurValidation
)
from src.api.middlewares import limiter

# Logger
logger = obtenir_logger(__name__)

# Router
router = APIRouter()


@router.post("/retour-utilisateur", response_model=ReponseRetour, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def soumettre_retour(requete: RequeteRetour, request: Request):
    """
    Soumet un retour utilisateur sur une réponse du chatbot.

    Args:
        requete: Requête contenant la note, le commentaire et la conversation évaluée
        request: Objet Request FastAPI (requis pour le rate limiter)

    Returns:
        Confirmation de l'enregistrement du feedback

    Raises:
        HTTPException 400: Si la requête est invalide
        HTTPException 404: Si la conversation n'existe pas
        HTTPException 500: En cas d'erreur serveur interne

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/retour-utilisateur \\
          -H "Content-Type: application/json" \\
          -d '{
            "id_conversation": 123,
            "note": 4,
            "commentaire": "Très bonne réponse !",
            "categorie_probleme": "autre"
          }'
        ```
    """
    try:
        logger.info(
            f"Nouveau retour utilisateur reçu : "
            f"conversation={requete.id_conversation}, note={requete.note}/5"
        )

        # Vérifier que la conversation existe
        try:
            obtenir_conversation(requete.id_conversation)
        except ErreurEnregistrementIntrouvable:
            logger.warning(
                f"Tentative de retour sur conversation inexistante : "
                f"id={requete.id_conversation}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La conversation {requete.id_conversation} n'existe pas"
            )

        # Insérer le retour dans la base de données
        try:
            id_retour = inserer_retour(
                id_conversation=requete.id_conversation,
                note=requete.note,
                commentaire=requete.commentaire,
                suggestion_reponse=requete.suggestion_reponse,
                categorie_probleme=requete.categorie_probleme.value if requete.categorie_probleme else None
            )

            logger.info(f"[OK] Retour {id_retour} enregistré avec succès")

            return ReponseRetour(
                id_retour=id_retour,
                message="Merci pour votre retour ! Il nous aidera à améliorer le service."
            )

        except ValueError as e:
            logger.warning(f"Validation échouée pour le retour : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except HTTPException:
        # Re-lever les HTTPException telles quelles
        raise

    except Exception as e:
        # Logger et retourner une erreur 500 pour les erreurs inattendues
        logger.error(f"Erreur inattendue lors de la soumission du retour : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite lors de l'enregistrement de votre retour"
        )


@router.get("/retour-utilisateur/{id_retour}", response_model=dict)
@limiter.limit("100/minute")
async def obtenir_retour_par_id(id_retour: int, request: Request):
    """
    Récupère un retour utilisateur par son ID.

    Args:
        id_retour: ID du retour à récupérer
        request: Objet Request FastAPI (requis pour le rate limiter)

    Returns:
        Informations complètes du retour

    Raises:
        HTTPException 404: Si le retour n'existe pas
        HTTPException 500: En cas d'erreur serveur interne
    """
    try:
        logger.debug(f"Récupération retour ID={id_retour}")

        retour = obtenir_retour(id_retour)

        logger.debug(f"Retour {id_retour} récupéré avec succès")

        return retour

    except ErreurEnregistrementIntrouvable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Le retour {id_retour} n'existe pas"
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du retour {id_retour} : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du retour"
        )


@router.get("/retours-conversation/{id_conversation}", response_model=List[dict])
@limiter.limit("100/minute")
async def obtenir_retours_conversation(id_conversation: int, request: Request):
    """
    Récupère tous les retours associés à une conversation.

    Args:
        id_conversation: ID de la conversation
        request: Objet Request FastAPI (requis pour le rate limiter)

    Returns:
        Liste des retours pour cette conversation

    Raises:
        HTTPException 500: En cas d'erreur serveur interne
    """
    try:
        logger.debug(f"Récupération retours pour conversation ID={id_conversation}")

        retours = obtenir_retours_par_conversation(id_conversation)

        logger.debug(f"{len(retours)} retour(s) trouvé(s) pour la conversation {id_conversation}")

        return retours

    except Exception as e:
        logger.error(
            f"Erreur lors de la récupération des retours pour la conversation {id_conversation} : {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des retours"
        )


@router.get("/retours/statistiques", response_model=dict)
@limiter.limit("100/minute")
async def obtenir_stats_retours(request: Request):
    """
    Récupère les statistiques globales des retours utilisateurs.

    Args:
        request: Objet Request FastAPI (requis pour le rate limiter)

    Returns:
        Statistiques globales (note moyenne, répartition, etc.)

    Raises:
        HTTPException 500: En cas d'erreur serveur interne

    Example:
        ```bash
        curl -X GET http://localhost:8000/api/v1/retours/statistiques
        ```
    """
    try:
        logger.debug("Récupération des statistiques des retours")

        stats = obtenir_statistiques_retours()

        logger.debug(f"Statistiques calculées : {stats['total_retours']} retours")

        return stats

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques"
        )


@router.get("/retours/par-note", response_model=List[dict])
@limiter.limit("100/minute")
async def obtenir_retours_filtres_note(
    note_min: int = 1,
    note_max: int = 5,
    limite: int = 100,
    offset: int = 0,
    request: Request = None
):
    """
    Récupère les retours filtrés par note.

    Args:
        note_min: Note minimale (1-5)
        note_max: Note maximale (1-5)
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination
        request: Objet Request FastAPI

    Returns:
        Liste des retours filtrés

    Raises:
        HTTPException 400: Si les paramètres sont invalides
        HTTPException 500: En cas d'erreur serveur interne

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/retours/par-note?note_min=1&note_max=2&limite=50"
        ```
    """
    try:
        logger.debug(f"Récupération retours avec note entre {note_min} et {note_max}")

        retours = obtenir_retours_par_note(note_min, note_max, limite, offset)

        logger.debug(f"{len(retours)} retour(s) trouvé(s)")

        return retours

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des retours par note : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des retours"
        )


@router.get("/retours/par-statut/{statut}", response_model=List[dict])
@limiter.limit("100/minute")
async def obtenir_retours_filtres_statut(
    statut: str,
    limite: int = 100,
    offset: int = 0,
    request: Request = None
):
    """
    Récupère les retours filtrés par statut.

    Args:
        statut: Statut du retour ('nouveau', 'en_cours', 'traite', 'ignore')
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination
        request: Objet Request FastAPI

    Returns:
        Liste des retours filtrés

    Raises:
        HTTPException 400: Si le statut est invalide
        HTTPException 500: En cas d'erreur serveur interne

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/retours/par-statut/nouveau?limite=50"
        ```
    """
    try:
        logger.debug(f"Récupération retours avec statut '{statut}'")

        retours = obtenir_retours_par_statut(statut, limite, offset)

        logger.debug(f"{len(retours)} retour(s) trouvé(s)")

        return retours

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des retours par statut : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des retours"
        )


@router.get("/retours/par-categorie/{categorie}", response_model=List[dict])
@limiter.limit("100/minute")
async def obtenir_retours_filtres_categorie(
    categorie: str,
    limite: int = 100,
    offset: int = 0,
    request: Request = None
):
    """
    Récupère les retours filtrés par catégorie de problème.

    Args:
        categorie: Catégorie du problème
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination
        request: Objet Request FastAPI

    Returns:
        Liste des retours filtrés

    Raises:
        HTTPException 400: Si la catégorie est invalide
        HTTPException 500: En cas d'erreur serveur interne

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/retours/par-categorie/reponse_incorrecte?limite=50"
        ```
    """
    try:
        logger.debug(f"Récupération retours avec catégorie '{categorie}'")

        retours = obtenir_retours_par_categorie(categorie, limite, offset)

        logger.debug(f"{len(retours)} retour(s) trouvé(s)")

        return retours

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des retours par catégorie : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des retours"
        )


# ============================================================================
# Export
# ============================================================================

__all__ = ['router']
