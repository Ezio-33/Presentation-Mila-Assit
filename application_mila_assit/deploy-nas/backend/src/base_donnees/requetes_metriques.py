"""
Requêtes MySQL pour la table metriques.

Gère l'enregistrement et la récupération des métriques système.
"""

import logging
from typing import Dict, Optional, Any
import json

from src.base_donnees.connexion import obtenir_curseur
from src.utilitaires.exceptions import ErreurRequeteBD

logger = logging.getLogger(__name__)


def inserer_metrique(
    type_metrique: str,
    valeur: float,
    details: Optional[Dict[str, Any]] = None
) -> int:
    """
    Insère une métrique dans la base de données.

    Args:
        type_metrique: Type de métrique (precision_recherche, temps_reponse, etc.)
        valeur: Valeur numérique de la métrique
        details: Détails additionnels (stockés en JSON)

    Returns:
        ID de la métrique insérée

    Raises:
        ErreurRequeteBD: Si l'insertion échoue

    Example:
        >>> inserer_metrique(
        ...     type_metrique='temps_reponse',
        ...     valeur=850.5,
        ...     details={'composant': 'pipeline_rag', 'cache': False}
        ... )
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            # Convertir details en JSON
            details_json = json.dumps(details) if details else None

            query = """
                INSERT INTO metriques (
                    type_metrique,
                    valeur_metrique,
                    details
                ) VALUES (%s, %s, %s)
            """

            cursor.execute(query, (type_metrique, valeur, details_json))
            conn.commit()

            id_metrique = cursor.lastrowid

            logger.debug(f"[OK] Métrique insérée: {type_metrique}={valeur}")

            return id_metrique

    except Exception as e:
        logger.error(f"[ERREUR] Erreur insertion métrique: {e}")
        raise ErreurRequeteBD(
            requete="INSERT INTO metriques",
            raison=str(e)
        )


def obtenir_latence_moyenne(periode: str = '24h') -> float:
    """
    Calcule la latence moyenne sur une période.

    Args:
        periode: Période ('1h', '24h', '7d', '30d')

    Returns:
        Latence moyenne en millisecondes

    Example:
        >>> latence = obtenir_latence_moyenne('24h')
        >>> print(f"Latence moyenne: {latence}ms")
    """
    # Convertir période en intervalle MySQL
    interval_map = {
        '1h': '1 HOUR',
        '24h': '24 HOUR',
        '7d': '7 DAY',
        '30d': '30 DAY'
    }

    interval = interval_map.get(periode, '24 HOUR')

    try:
        with obtenir_curseur() as (conn, cursor):
            query = f"""
                SELECT AVG(temps_reponse_ms) as latence_moyenne
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL {interval})
                AND temps_reponse_ms IS NOT NULL
            """

            cursor.execute(query)
            result = cursor.fetchone()

            latence = result['latence_moyenne'] if result and result['latence_moyenne'] else 0.0

            return float(latence)

    except Exception as e:
        logger.error(f"[ERREUR] Erreur calcul latence moyenne: {e}")
        return 0.0


def obtenir_taux_cache_hit(periode: str = '24h') -> float:
    """
    Calcule le taux de succès du cache sur une période.

    Args:
        periode: Période ('1h', '24h', '7d', '30d')

    Returns:
        Taux de cache hit entre 0.0 et 1.0

    Example:
        >>> taux = obtenir_taux_cache_hit('24h')
        >>> print(f"Cache hit rate: {taux:.1%}")
    """
    interval_map = {
        '1h': '1 HOUR',
        '24h': '24 HOUR',
        '7d': '7 DAY',
        '30d': '30 DAY'
    }

    interval = interval_map.get(periode, '24 HOUR')

    try:
        with obtenir_curseur() as (conn, cursor):
            query = f"""
                SELECT
                    SUM(CASE WHEN cache_hit = TRUE THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as taux
                FROM conversations
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL {interval})
            """

            cursor.execute(query)
            result = cursor.fetchone()

            taux = result['taux'] if result and result['taux'] else 0.0

            return float(taux)

    except Exception as e:
        logger.error(f"[ERREUR] Erreur calcul taux cache: {e}")
        return 0.0


def obtenir_satisfaction_moyenne(periode: str = '24h') -> float:
    """
    Calcule la satisfaction moyenne (note feedback) sur une période.

    Args:
        periode: Période ('1h', '24h', '7d', '30d')

    Returns:
        Note moyenne entre 1.0 et 5.0

    Example:
        >>> satisfaction = obtenir_satisfaction_moyenne('7d')
        >>> print(f"Satisfaction: {satisfaction:.2f}/5")
    """
    interval_map = {
        '1h': '1 HOUR',
        '24h': '24 HOUR',
        '7d': '7 DAY',
        '30d': '30 DAY'
    }

    interval = interval_map.get(periode, '24 HOUR')

    try:
        with obtenir_curseur() as (conn, cursor):
            query = f"""
                SELECT AVG(note) as moyenne
                FROM retours_utilisateurs
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL {interval})
            """

            cursor.execute(query)
            result = cursor.fetchone()

            moyenne = result['moyenne'] if result and result['moyenne'] else 0.0

            return float(moyenne)

    except Exception as e:
        logger.error(f"[ERREUR] Erreur calcul satisfaction moyenne: {e}")
        return 0.0


def obtenir_distribution_notes() -> Dict[int, int]:
    """
    Obtient la distribution des notes de feedback.

    Returns:
        Dictionnaire {note: nombre} (ex: {1: 5, 2: 10, 3: 20, 4: 30, 5: 35})

    Example:
        >>> distribution = obtenir_distribution_notes()
        >>> for note, count in distribution.items():
        ...     print(f"{note} étoiles: {count} feedbacks")
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            query = """
                SELECT note, COUNT(*) as count
                FROM retours_utilisateurs
                GROUP BY note
                ORDER BY note
            """

            cursor.execute(query)
            results = cursor.fetchall()

            distribution = {row['note']: row['count'] for row in results}

            # Assurer que toutes les notes (1-5) sont présentes
            for note in range(1, 6):
                if note not in distribution:
                    distribution[note] = 0

            return distribution

    except Exception as e:
        logger.error(f"[ERREUR] Erreur distribution notes: {e}")
        return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def obtenir_metriques_completes(periode: str = '24h') -> Dict[str, Any]:
    """
    Obtient toutes les métriques principales en une seule requête.

    Args:
        periode: Période pour les stats

    Returns:
        Dictionnaire complet avec toutes les métriques

    Example:
        >>> metriques = obtenir_metriques_completes('24h')
        >>> print(f"Latence: {metriques['latence_moyenne_ms']}ms")
        >>> print(f"Cache: {metriques['taux_cache_hit']:.1%}")
    """
    return {
        'latence_moyenne_ms': obtenir_latence_moyenne(periode),
        'taux_cache_hit': obtenir_taux_cache_hit(periode),
        'satisfaction_moyenne': obtenir_satisfaction_moyenne(periode),
        'distribution_notes': obtenir_distribution_notes(),
        'periode': periode
    }


__all__ = [
    'inserer_metrique',
    'obtenir_latence_moyenne',
    'obtenir_taux_cache_hit',
    'obtenir_satisfaction_moyenne',
    'obtenir_distribution_notes',
    'obtenir_metriques_completes'
]
