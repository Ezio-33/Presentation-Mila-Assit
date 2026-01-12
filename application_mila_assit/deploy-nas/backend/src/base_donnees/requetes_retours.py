"""
Requêtes MySQL pour la table retours_utilisateurs.

Gère les feedbacks utilisateurs sur les réponses du chatbot.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.base_donnees.connexion import obtenir_curseur
from src.utilitaires.exceptions import ErreurRequeteBD, ErreurEnregistrementIntrouvable

logger = logging.getLogger(__name__)


def inserer_retour(
    id_conversation: int,
    note: int,
    commentaire: Optional[str] = None,
    suggestion_reponse: Optional[str] = None,
    categorie_probleme: Optional[str] = None
) -> int:
    """
    Insère un nouveau retour utilisateur dans la base de données.

    Args:
        id_conversation: ID de la conversation évaluée
        note: Note de satisfaction (1 à 5)
        commentaire: Commentaire libre de l'utilisateur
        suggestion_reponse: Meilleure réponse proposée
        categorie_probleme: Classification du problème

    Returns:
        ID du retour inséré

    Raises:
        ErreurRequeteBD: Si l'insertion échoue
        ValueError: Si la note est hors de la plage 1-5

    Example:
        >>> id_retour = inserer_retour(
        ...     id_conversation=42,
        ...     note=4,
        ...     commentaire="Bonne réponse !",
        ...     categorie_probleme="autre"
        ... )
        >>> print(f"Retour {id_retour} créé")
    """
    # Validation de la note
    if not 1 <= note <= 5:
        raise ValueError(f"La note doit être entre 1 et 5, reçu: {note}")

    # Validation de la catégorie
    categories_valides = [
        'reponse_incorrecte',
        'reponse_incomplete',
        'ton_inapproprie',
        'reponse_obsolete',
        'hors_sujet',
        'autre',
        None
    ]

    if categorie_probleme and categorie_probleme not in categories_valides:
        raise ValueError(
            f"Catégorie invalide: {categorie_probleme}. "
            f"Valeurs autorisées: {', '.join([c for c in categories_valides if c])}"
        )

    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                INSERT INTO retours_utilisateurs (
                    id_conversation,
                    note,
                    commentaire,
                    suggestion_reponse,
                    categorie_probleme,
                    statut
                ) VALUES (
                    %s, %s, %s, %s, %s, 'nouveau'
                )
            """

            cursor.execute(query, (
                id_conversation,
                note,
                commentaire,
                suggestion_reponse,
                categorie_probleme
            ))

            conn.commit()

            # Récupérer l'ID auto-incrémenté
            id_retour = cursor.lastrowid

            logger.info(
                f"[OK] Retour {id_retour} inséré "
                f"(conversation={id_conversation}, note={note}/5)"
            )

            return id_retour

    except Exception as e:
        logger.error(f"[ERREUR] Erreur insertion retour utilisateur: {e}")
        raise ErreurRequeteBD(
            requete="INSERT INTO retours_utilisateurs",
            raison=str(e)
        )


def obtenir_retour(id_retour: int) -> Dict:
    """
    Récupère un retour utilisateur par son ID.

    Args:
        id_retour: ID du retour

    Returns:
        Dictionnaire avec les informations complètes

    Raises:
        ErreurEnregistrementIntrouvable: Si le retour n'existe pas
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT
                    ru.*,
                    c.question_utilisateur,
                    c.reponse_bot,
                    c.score_confiance
                FROM retours_utilisateurs ru
                LEFT JOIN conversations c ON ru.id_conversation = c.id
                WHERE ru.id = %s
            """

            cursor.execute(query, (id_retour,))
            result = cursor.fetchone()

            if not result:
                raise ErreurEnregistrementIntrouvable(
                    table="retours_utilisateurs",
                    identifiant=id_retour
                )

            logger.debug(f"Retour {id_retour} récupéré")

            return result

    except ErreurEnregistrementIntrouvable:
        raise
    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération retour {id_retour}: {e}")
        raise ErreurRequeteBD(
            requete="SELECT FROM retours_utilisateurs",
            raison=str(e)
        )


def obtenir_retours_par_conversation(id_conversation: int) -> List[Dict]:
    """
    Récupère tous les retours associés à une conversation.

    Args:
        id_conversation: ID de la conversation

    Returns:
        Liste de dictionnaires avec les retours

    Raises:
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT *
                FROM retours_utilisateurs
                WHERE id_conversation = %s
                ORDER BY date_creation DESC
            """

            cursor.execute(query, (id_conversation,))
            results = cursor.fetchall()

            logger.debug(
                f"{len(results)} retour(s) trouvé(s) "
                f"pour la conversation {id_conversation}"
            )

            return results

    except Exception as e:
        logger.error(
            f"[ERREUR] Erreur récupération retours conversation {id_conversation}: {e}"
        )
        raise ErreurRequeteBD(
            requete="SELECT FROM retours_utilisateurs",
            raison=str(e)
        )


def obtenir_retours_par_note(
    note_min: int = 1,
    note_max: int = 5,
    limite: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Récupère les retours filtrés par note.

    Args:
        note_min: Note minimale (1-5)
        note_max: Note maximale (1-5)
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination

    Returns:
        Liste de dictionnaires avec les retours

    Raises:
        ErreurRequeteBD: Si la requête échoue
        ValueError: Si les notes sont invalides
    """
    if not 1 <= note_min <= 5 or not 1 <= note_max <= 5:
        raise ValueError("Les notes doivent être entre 1 et 5")

    if note_min > note_max:
        raise ValueError("note_min doit être <= note_max")

    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT
                    ru.*,
                    c.question_utilisateur,
                    c.reponse_bot
                FROM retours_utilisateurs ru
                LEFT JOIN conversations c ON ru.id_conversation = c.id
                WHERE ru.note BETWEEN %s AND %s
                ORDER BY ru.date_creation DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (note_min, note_max, limite, offset))
            results = cursor.fetchall()

            logger.debug(
                f"{len(results)} retour(s) trouvé(s) "
                f"avec note entre {note_min} et {note_max}"
            )

            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération retours par note: {e}")
        raise ErreurRequeteBD(
            requete="SELECT FROM retours_utilisateurs",
            raison=str(e)
        )


def obtenir_retours_par_statut(
    statut: str,
    limite: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Récupère les retours filtrés par statut.

    Args:
        statut: Statut du retour ('nouveau', 'en_cours', 'traite', 'ignore')
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination

    Returns:
        Liste de dictionnaires avec les retours

    Raises:
        ErreurRequeteBD: Si la requête échoue
        ValueError: Si le statut est invalide
    """
    statuts_valides = ['nouveau', 'en_cours', 'traite', 'ignore']

    if statut not in statuts_valides:
        raise ValueError(
            f"Statut invalide: {statut}. "
            f"Valeurs autorisées: {', '.join(statuts_valides)}"
        )

    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT
                    ru.*,
                    c.question_utilisateur,
                    c.reponse_bot,
                    c.score_confiance
                FROM retours_utilisateurs ru
                LEFT JOIN conversations c ON ru.id_conversation = c.id
                WHERE ru.statut = %s
                ORDER BY ru.date_creation DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (statut, limite, offset))
            results = cursor.fetchall()

            logger.debug(
                f"{len(results)} retour(s) trouvé(s) avec statut '{statut}'"
            )

            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération retours par statut: {e}")
        raise ErreurRequeteBD(
            requete="SELECT FROM retours_utilisateurs",
            raison=str(e)
        )


def obtenir_retours_par_categorie(
    categorie: str,
    limite: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Récupère les retours filtrés par catégorie de problème.

    Args:
        categorie: Catégorie du problème
        limite: Nombre maximum de résultats
        offset: Décalage pour pagination

    Returns:
        Liste de dictionnaires avec les retours

    Raises:
        ErreurRequeteBD: Si la requête échoue
        ValueError: Si la catégorie est invalide
    """
    categories_valides = [
        'reponse_incorrecte',
        'reponse_incomplete',
        'ton_inapproprie',
        'reponse_obsolete',
        'hors_sujet',
        'autre'
    ]

    if categorie not in categories_valides:
        raise ValueError(
            f"Catégorie invalide: {categorie}. "
            f"Valeurs autorisées: {', '.join(categories_valides)}"
        )

    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT
                    ru.*,
                    c.question_utilisateur,
                    c.reponse_bot
                FROM retours_utilisateurs ru
                LEFT JOIN conversations c ON ru.id_conversation = c.id
                WHERE ru.categorie_probleme = %s
                ORDER BY ru.date_creation DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (categorie, limite, offset))
            results = cursor.fetchall()

            logger.debug(
                f"{len(results)} retour(s) trouvé(s) "
                f"avec catégorie '{categorie}'"
            )

            return results

    except Exception as e:
        logger.error(f"[ERREUR] Erreur récupération retours par catégorie: {e}")
        raise ErreurRequeteBD(
            requete="SELECT FROM retours_utilisateurs",
            raison=str(e)
        )


def marquer_retour_traite(
    id_retour: int,
    id_admin: int,
    justification: str,
    nouveau_statut: str = 'traite'
) -> bool:
    """
    Marque un retour comme traité par un administrateur.

    Args:
        id_retour: ID du retour à mettre à jour
        id_admin: ID de l'administrateur
        justification: Justification du traitement
        nouveau_statut: Nouveau statut ('traite' ou 'ignore')

    Returns:
        True si la mise à jour a réussi

    Raises:
        ErreurRequeteBD: Si la mise à jour échoue
        ValueError: Si le statut est invalide
    """
    statuts_valides = ['traite', 'ignore']

    if nouveau_statut not in statuts_valides:
        raise ValueError(
            f"Statut invalide: {nouveau_statut}. "
            f"Valeurs autorisées: {', '.join(statuts_valides)}"
        )

    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                UPDATE retours_utilisateurs
                SET
                    statut = %s,
                    id_admin_traitement = %s,
                    justification = %s,
                    date_traitement = NOW()
                WHERE id = %s
            """

            cursor.execute(query, (
                nouveau_statut,
                id_admin,
                justification,
                id_retour
            ))

            conn.commit()

            if cursor.rowcount == 0:
                raise ErreurEnregistrementIntrouvable(
                    table="retours_utilisateurs",
                    identifiant=id_retour
                )

            logger.info(
                f"[OK] Retour {id_retour} marqué '{nouveau_statut}' "
                f"par admin {id_admin}"
            )

            return True

    except ErreurEnregistrementIntrouvable:
        raise
    except Exception as e:
        logger.error(f"[ERREUR] Erreur mise à jour retour {id_retour}: {e}")
        raise ErreurRequeteBD(
            requete="UPDATE retours_utilisateurs",
            raison=str(e)
        )


def obtenir_statistiques_retours() -> Dict:
    """
    Calcule les statistiques globales des retours utilisateurs.

    Returns:
        Dictionnaire avec les statistiques

    Raises:
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            # Statistiques générales
            query_stats = """
                SELECT
                    COUNT(*) as total_retours,
                    AVG(note) as note_moyenne,
                    MIN(note) as note_min,
                    MAX(note) as note_max,
                    SUM(CASE WHEN note >= 4 THEN 1 ELSE 0 END) as retours_positifs,
                    SUM(CASE WHEN note <= 2 THEN 1 ELSE 0 END) as retours_negatifs,
                    SUM(CASE WHEN note = 3 THEN 1 ELSE 0 END) as retours_neutres
                FROM retours_utilisateurs
            """

            cursor.execute(query_stats)
            stats = cursor.fetchone()

            # Répartition par statut
            query_statuts = """
                SELECT statut, COUNT(*) as count
                FROM retours_utilisateurs
                GROUP BY statut
            """

            cursor.execute(query_statuts)
            statuts = cursor.fetchall()

            # Répartition par catégorie
            query_categories = """
                SELECT categorie_probleme, COUNT(*) as count
                FROM retours_utilisateurs
                WHERE categorie_probleme IS NOT NULL
                GROUP BY categorie_probleme
            """

            cursor.execute(query_categories)
            categories = cursor.fetchall()

            # Construire le résultat
            result = {
                'total_retours': stats['total_retours'] if stats else 0,
                'note_moyenne': round(float(stats['note_moyenne']), 2) if stats and stats['note_moyenne'] else 0,
                'note_min': stats['note_min'] if stats else 0,
                'note_max': stats['note_max'] if stats else 0,
                'retours_positifs': stats['retours_positifs'] if stats else 0,
                'retours_negatifs': stats['retours_negatifs'] if stats else 0,
                'retours_neutres': stats['retours_neutres'] if stats else 0,
                'par_statut': {row['statut']: row['count'] for row in statuts},
                'par_categorie': {row['categorie_probleme']: row['count'] for row in categories}
            }

            logger.debug(f"Statistiques calculées: {result['total_retours']} retours")

            return result

    except Exception as e:
        logger.error(f"[ERREUR] Erreur calcul statistiques retours: {e}")
        raise ErreurRequeteBD(
            requete="SELECT statistiques retours_utilisateurs",
            raison=str(e)
        )


def compter_retours() -> int:
    """
    Compte le nombre total de retours utilisateurs.

    Returns:
        Nombre total de retours

    Raises:
        ErreurRequeteBD: Si la requête échoue
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = "SELECT COUNT(*) as count FROM retours_utilisateurs"

            cursor.execute(query)
            result = cursor.fetchone()

            count = result['count'] if result else 0

            logger.debug(f"{count} retour(s) total dans la base")

            return count

    except Exception as e:
        logger.error(f"[ERREUR] Erreur comptage retours: {e}")
        raise ErreurRequeteBD(
            requete="SELECT COUNT FROM retours_utilisateurs",
            raison=str(e)
        )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'inserer_retour',
    'obtenir_retour',
    'obtenir_retours_par_conversation',
    'obtenir_retours_par_note',
    'obtenir_retours_par_statut',
    'obtenir_retours_par_categorie',
    'marquer_retour_traite',
    'obtenir_statistiques_retours',
    'compter_retours'
]
