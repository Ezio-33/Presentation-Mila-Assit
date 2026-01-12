"""
Routes API pour la gestion des conversations.

Fournit l'endpoint principal pour poser des questions au chatbot.
"""

from fastapi import APIRouter, HTTPException, Request, status
from src.modeles.conversation import RequeteConversation, ReponseConversation, SourceConnaissance
from src.clients.llm_client import obtenir_llm_client
from src.base_donnees.requetes_conversations import inserer_conversation
from src.base_donnees.requetes_connaissances import obtenir_reponses_par_ids
from src.securite.validation import valider_question, detecter_spam
from src.utilitaires.logger import obtenir_logger
from src.utilitaires.exceptions import (
    ErreurEmbedding,
    ErreurBaseDeDonnees,
    ErreurLLM,
    ErreurValidation
)
from src.api.middlewares import limiter

# Logger
logger = obtenir_logger(__name__)

# Router
router = APIRouter()


@router.post("/search", response_model=ReponseConversation)
@limiter.limit("100/minute")
async def creer_conversation(requete: RequeteConversation, request: Request):
    """
    Crée une nouvelle conversation en répondant à une question utilisateur.

    Args:
        requete: Requête contenant la question et l'ID de session
        request: Objet Request FastAPI (requis pour le rate limiter)

    Returns:
        Réponse contenant la réponse générée, la confiance, les sources et le temps

    Raises:
        HTTPException 400: Si la question est invalide
        HTTPException 503: Si le service est temporairement indisponible
        HTTPException 500: En cas d'erreur serveur interne
    """
    try:
        # Valider la question
        logger.info(f"Nouvelle question reçue : '{requete.question[:50]}...'")

        try:
            question_validee = valider_question(requete.question)
        except ValueError as e:
            logger.warning(f"Question invalide : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question invalide : {str(e)}"
            )

        # Vérifier le spam
        if detecter_spam(question_validee):
            logger.warning(f"Spam détecté dans la question : {requete.question}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La question contient du contenu suspect"
            )

        # Vérifier l'embedding (Architecture 4 containers)
        embedding_to_use = requete.embedding
        
        if not embedding_to_use:
            # Mode dégradé : demander au Container 3 de calculer l'embedding
            # Utile pour les tests et le widget démo
            logger.warning("Embedding manquant - mode dégradé activé (Container 3 calculera l'embedding)")
            embedding_to_use = None  # Le LLM client gèrera ce cas
        elif len(requete.embedding) != 768:
            logger.error(f"Dimension embedding invalide: {len(requete.embedding)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'embedding doit avoir 768 dimensions (reçu: {len(requete.embedding)})"
            )

        # Obtenir le client LLM (Container 3)
        llm_client = obtenir_llm_client()

        # Appeler Container 3 pour recherche FAISS + génération LLM
        logger.info(f"Appel Container 3 pour la session {requete.id_session}")
        try:
            resultat = llm_client.rechercher_et_generer(
                embedding=embedding_to_use,
                question=question_validee,
                k=5  # Augmenté pour avoir plus de contexte pour les multi-questions
            )
        except Exception as e:
            logger.error(f"Erreur Container 3 : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Le service LLM+FAISS est temporairement indisponible: {str(e)}"
            )

        # Gérer le cas où la réponse LLM est vide
        reponse_texte = resultat["reponse"]
        if not reponse_texte or not reponse_texte.strip():
            logger.warning("Réponse LLM vide - utilisation du message par défaut")
            reponse_texte = "Désolé, je n'ai pas pu générer une réponse pour cette question. Pourriez-vous reformuler ?"

        # Insérer la conversation dans la base de données
        try:
            id_conversation = inserer_conversation(
                id_session=requete.id_session,
                question=question_validee,
                reponse=reponse_texte,
                ids_kb=resultat["sources"],
                confiance=resultat["confiance"],
                temps_ms=resultat["temps_ms"],
                cache_hit=False  # Cache LRU supprimé (Architecture 4 containers)
            )
            logger.info(f"Conversation {id_conversation} enregistrée avec succès")

        except ErreurBaseDeDonnees as e:
            logger.error(f"Erreur lors de l'insertion dans la BDD : {str(e)}")
            # On ne bloque pas la réponse si l'insertion échoue
            # L'utilisateur aura quand même sa réponse
            id_conversation = -1

        # Recuperer les details des sources
        sources_details = None
        try:
            if resultat["sources"]:
                sources_data = obtenir_reponses_par_ids(resultat["sources"])
                sources_details = [
                    SourceConnaissance(
                        id=src["id"],
                        question=src["question"],
                        extrait=src["reponse"][:100] + "..." if len(src["reponse"]) > 100 else src["reponse"]
                    )
                    for src in sources_data
                ]
        except Exception as e:
            logger.warning(f"Impossible de recuperer les details des sources: {e}")

        # Construire la réponse
        reponse = ReponseConversation(
            id_conversation=id_conversation,
            reponse=reponse_texte,
            confiance=resultat["confiance"],
            sources=resultat["sources"],
            sources_details=sources_details,
            temps_ms=resultat["temps_ms"]
        )

        logger.info(
            f"Réponse générée en {resultat['temps_ms']}ms "
            f"(confiance: {resultat['confiance']:.2f})"
        )

        return reponse

    except HTTPException:
        # Re-lever les HTTPException telles quelles
        raise

    except Exception as e:
        # Logger et retourner une erreur 500 pour les erreurs inattendues
        logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite"
        )
