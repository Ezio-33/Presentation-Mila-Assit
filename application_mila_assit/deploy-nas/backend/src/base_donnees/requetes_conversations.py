"""
Requêtes MySQL pour la table conversations.

Gère l'historique des conversations utilisateur-chatbot.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID
import json

from src.base_donnees.connexion import obtenir_curseur
from src.utilitaires.exceptions import ErreurRequeteBD, ErreurEnregistrementIntrouvable

logger = logging.getLogger(__name__)


def inserer_conversation(
    id_session: UUID,
    question: str,
    reponse: str,
    ids_kb: Optional[List[int]] = None,
    confiance: Optional[float] = None,
    temps_ms: Optional[int] = None,
    temps_embedding_ms: Optional[int] = None,
    temps_retrieval_ms: Optional[int] = None,
    temps_generation_ms: Optional[int] = None,
    cache_hit: bool = False
) -> int:
    """
    Insère une nouvelle conversation dans la base de données.

    Args:
        id_session: UUID de la session utilisateur
        question: Question posée
        reponse: Réponse générée
        ids_kb: IDs des entrées KB utilisées (top-3)
        confiance: Score de confiance
        temps_ms: Temps total de traitement
        temps_embedding_ms: Temps calcul embedding
        temps_retrieval_ms: Temps recherche FAISS
        temps_generation_ms: Temps génération LLM
        cache_hit: Indique si la réponse vient du cache

    Returns:
        ID de la conversation insérée

    Raises:
        ErreurRequeteBD: Si l'insertion échoue

    Example:
        >>> from uuid import uuid4
        >>> id_conv = inserer_conversation(
        ...     id_session=uuid4(),
        ...     question="Test",
        ...     reponse="Réponse test",
        ...     ids_kb=[1, 2, 3],
        ...     confiance=0.95,
        ...     temps_ms=850
        ... )
        >>> print(f"Conversation {id_conv} créée")
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            # Convertir UUID en string
            id_session_str = str(id_session)

            # Convertir la liste d'IDs en JSON
            ids_kb_json = json.dumps(ids_kb) if ids_kb else None

            query = """
                INSERT INTO conversations (
                    id_session,
                    question_utilisateur,
                    reponse_bot,
                    ids_connaissances_recuperees,
                    score_confiance,
                    temps_reponse_ms,
                    temps_embedding_ms,
                    temps_retrieval_ms,
                    temps_generation_ms,
                    cache_hit
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            cursor.execute(query, (
                id_session_str,
                question,
                reponse,
                ids_kb_json,
                confiance,
                temps_ms,
                temps_embedding_ms,
                temps_retrieval_ms,
                temps_generation_ms,
                cache_hit
            ))

            conn.commit()

            # Récupérer l'ID auto-incrémenté
            id_conversation = cursor.lastrowid

            logger.info(f"[OK] Conversation {id_conversation} insérée (session={id_session_str[:8]}...)")

            return id_conversation

    except Exception as e:
        logger.error(f"[ERREUR] Erreur insertion conversation: {e}")
        raise ErreurRequeteBD(
            requete="INSERT INTO conversations",
            raison=str(e)
        )


def obtenir_conversation(id_conversation: int) -> Dict:
    """
    Récupère une conversation par son ID.

    Args:
        id_conversation: ID de la conversation

    Returns:
        Dictionnaire avec les informations complètes

    Raises:
        ErreurEnregistrementIntrouvable: Si la conversation n'existe pas
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT *
                FROM conversations
                WHERE id = %s
            """

            cursor.execute(query, (id_conversation,))
            result = cursor.fetchone()

            if not result:
                raise ErreurEnregistrementIntrouvable(
                    table="conversations",
                    identifiant=id_conversation
                )

            # Parser le JSON des IDs KB
            if result.get('ids_connaissances_recuperees'):
                result['ids_connaissances_recuperees'] = json.loads(
                    result['ids_connaissances_recuperees']
                )

            return result

    except ErreurEnregistrementIntrouvable:
        raise

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération conversation: {e}")
        raise ErreurRequeteBD(
            requete=f"SELECT conversations WHERE id={id_conversation}",
            raison=str(e)
        )


def obtenir_conversations_session(
    id_session: UUID,
    limite: int = 10
) -> List[Dict]:
    """
    Récupère les conversations d'une session.

    Args:
        id_session: UUID de la session
        limite: Nombre maximum de conversations à retourner

    Returns:
        Liste des conversations (plus récentes en premier)
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT *
                FROM conversations
                WHERE id_session = %s
                ORDER BY date_creation DESC
                LIMIT %s
            """

            cursor.execute(query, (str(id_session), limite))
            results = cursor.fetchall()

            # Parser les JSONs
            for result in results:
                if result.get('ids_connaissances_recuperees'):
                    result['ids_connaissances_recuperees'] = json.loads(
                        result['ids_connaissances_recuperees']
                    )

            logger.info(f"[OK] {len(results)} conversations récupérées pour session {str(id_session)[:8]}...")

            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération conversations session: {e}")
        raise ErreurRequeteBD(
            requete=f"SELECT conversations WHERE session={id_session}",
            raison=str(e)
        )


def obtenir_statistiques_conversations(periode_heures: int = 24) -> Dict:
    """
    Obtient des statistiques sur les conversations.

    Args:
        periode_heures: Période en heures pour les stats

    Returns:
        Dictionnaire avec les statistiques
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            stats = {}

            # Nombre total dans la période
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """, (periode_heures,))
            stats['total'] = cursor.fetchone()['total']

            # Temps de réponse moyen
            cursor.execute("""
                SELECT
                    AVG(temps_reponse_ms) as moyenne,
                    MIN(temps_reponse_ms) as min,
                    MAX(temps_reponse_ms) as max
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND temps_reponse_ms IS NOT NULL
            """, (periode_heures,))
            temps_stats = cursor.fetchone()
            stats['temps_reponse_ms'] = temps_stats

            # Taux de cache hit
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN cache_hit = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as taux
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """, (periode_heures,))
            stats['taux_cache_hit'] = cursor.fetchone()['taux'] or 0.0

            # Score de confiance moyen
            cursor.execute("""
                SELECT AVG(score_confiance) as moyenne
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND score_confiance IS NOT NULL
            """, (periode_heures,))
            stats['confiance_moyenne'] = cursor.fetchone()['moyenne'] or 0.0

            return stats

    except Exception as e:
        logger.error(f"[ERREUR] Erreur statistiques conversations: {e}")
        return {}


__all__ = [
    'inserer_conversation',
    'obtenir_conversation',
    'obtenir_conversations_session',
    'obtenir_statistiques_conversations'
]
