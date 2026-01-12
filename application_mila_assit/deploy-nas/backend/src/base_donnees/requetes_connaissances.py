"""
Requêtes MySQL pour la table base_connaissances.

Gère toutes les interactions avec la base de connaissances.
"""

import logging
from typing import List, Dict, Optional

from src.base_donnees.connexion import obtenir_curseur
from src.utilitaires.exceptions import ErreurRequeteBD, ErreurEnregistrementIntrouvable

logger = logging.getLogger(__name__)


def obtenir_reponses_par_ids(ids: List[int]) -> List[Dict]:
    """
    Récupère les réponses de la base de connaissances par leurs IDs.

    Args:
        ids: Liste des IDs à récupérer

    Returns:
        Liste de dictionnaires contenant les informations complètes

    Raises:
        ErreurRequeteBD: Si la requête échoue

    Example:
        >>> reponses = obtenir_reponses_par_ids([1, 2, 3])
        >>> for r in reponses:
        ...     print(r['question'], r['reponse'])
    """
    if not ids:
        return []

    try:
        with obtenir_curseur() as (conn, cursor):
            # Créer les placeholders
            placeholders = ', '.join(['%s'] * len(ids))

            query = f"""
                SELECT
                    id,
                    etiquette,
                    question,
                    reponse,
                    contexte,
                    id_embedding,
                    date_creation,
                    date_modification
                FROM base_connaissances
                WHERE id IN ({placeholders})
                ORDER BY FIELD(id, {placeholders})
            """

            cursor.execute(query, ids + ids)
            results = cursor.fetchall()

            logger.info(f"[OK] {len(results)} réponses récupérées")
            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération réponses: {e}")
        raise ErreurRequeteBD(
            requete=f"SELECT base_connaissances WHERE id IN ({ids[:3]}...)",
            raison=str(e)
        )


def obtenir_toutes_connaissances() -> List[Dict]:
    """
    Récupère toutes les entrées de la base de connaissances.

    Utilisé principalement pour la génération de l'index FAISS.

    Returns:
        Liste de tous les enregistrements

    Raises:
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT
                    id,
                    etiquette,
                    question,
                    reponse,
                    contexte,
                    id_embedding
                FROM base_connaissances
                ORDER BY id
            """

            cursor.execute(query)
            results = cursor.fetchall()

            logger.info(f"[OK] {len(results)} connaissances récupérées")
            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération connaissances: {e}")
        raise ErreurRequeteBD(
            requete="SELECT * FROM base_connaissances",
            raison=str(e)
        )


def obtenir_par_etiquette(etiquette: str) -> List[Dict]:
    """
    Récupère toutes les entrées d'une étiquette donnée.

    Args:
        etiquette: Tag à rechercher (ex: "salutations", "aide_tts")

    Returns:
        Liste des entrées correspondantes
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT *
                FROM base_connaissances
                WHERE etiquette = %s
                ORDER BY id
            """

            cursor.execute(query, (etiquette,))
            results = cursor.fetchall()

            logger.info(f"[OK] {len(results)} entrées trouvées pour '{etiquette}'")
            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur recherche par étiquette: {e}")
        raise ErreurRequeteBD(
            requete=f"SELECT WHERE etiquette={etiquette}",
            raison=str(e)
        )


def obtenir_statistiques() -> Dict:
    """
    Obtient des statistiques sur la base de connaissances.

    Returns:
        Dictionnaire avec les stats
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            stats = {}

            # Nombre total
            cursor.execute("SELECT COUNT(*) as total FROM base_connaissances")
            stats['total'] = cursor.fetchone()['total']

            # Nombre de tags uniques
            cursor.execute("SELECT COUNT(DISTINCT etiquette) as nb_tags FROM base_connaissances")
            stats['nb_tags'] = cursor.fetchone()['nb_tags']

            # Nombre avec embeddings
            cursor.execute("SELECT COUNT(*) as total FROM base_connaissances WHERE id_embedding IS NOT NULL")
            stats['avec_embeddings'] = cursor.fetchone()['total']

            # Top 5 tags
            cursor.execute("""
                SELECT etiquette, COUNT(*) as count
                FROM base_connaissances
                GROUP BY etiquette
                ORDER BY count DESC
                LIMIT 5
            """)
            stats['top_tags'] = cursor.fetchall()

            return stats

    except Exception as e:
        logger.error(f"[ERREUR] Erreur statistiques: {e}")
        return {}


__all__ = [
    'obtenir_reponses_par_ids',
    'obtenir_toutes_connaissances',
    'obtenir_par_etiquette',
    'obtenir_statistiques'
]
