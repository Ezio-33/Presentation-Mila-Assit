"""
Module de gestion des connexions MySQL pour Mila-Assist.

Gère un pool de connexions MySQL pour optimiser les performances
et la gestion des ressources.
"""

import logging
import time
from typing import Optional
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector.pooling import MySQLConnectionPool

from src.utilitaires.config import obtenir_config
from src.utilitaires.exceptions import ErreurConnexionBD, ErreurBaseDeDonnees

# ============================================================================
# Configuration
# ============================================================================

settings = obtenir_config()
logger = logging.getLogger(__name__)

# ============================================================================
# Pool de connexions global
# ============================================================================

_pool: Optional[MySQLConnectionPool] = None


def creer_pool_connexions(max_retries: int = 30, retry_delay: int = 2) -> MySQLConnectionPool:
    """
    Crée un pool de connexions MySQL avec retry automatique.

    Args:
        max_retries: Nombre maximum de tentatives de connexion
        retry_delay: Délai en secondes entre chaque tentative

    Returns:
        Pool de connexions MySQL

    Raises:
        ErreurConnexionBD: Si toutes les tentatives échouent
    """
    logger.info("Création du pool de connexions MySQL...")

    pool_config = {
        'pool_name': settings.MYSQL_POOL_NAME,
        'pool_size': settings.MYSQL_POOL_SIZE,
        'pool_reset_session': True,
        'host': settings.MYSQL_HOST,
        'port': settings.MYSQL_PORT,
        'database': settings.MYSQL_DATABASE,
        'user': settings.MYSQL_USER,
        'password': settings.MYSQL_PASSWORD,
        'charset': settings.MYSQL_CHARSET,
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': False,
        'use_unicode': True,
        'get_warnings': True,
    }

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)

            logger.info(
                f"[OK] Pool MySQL créé: {settings.MYSQL_POOL_SIZE} connexions "
                f"({settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE})"
            )

            return pool

        except MySQLError as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"[ATTENTION] Tentative {attempt}/{max_retries} échouée: {e}. "
                    f"Nouvelle tentative dans {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                logger.error(f"[ERREUR] Échec après {max_retries} tentatives: {e}")

    # Si on arrive ici, toutes les tentatives ont échoué
    raise ErreurConnexionBD(
        host=settings.MYSQL_HOST,
        database=settings.MYSQL_DATABASE,
        raison=str(last_error)
    )


def obtenir_pool() -> MySQLConnectionPool:
    """
    Obtient le pool de connexions global (crée-le si nécessaire).

    Returns:
        Pool de connexions MySQL

    Raises:
        ErreurConnexionBD: Si le pool ne peut pas être créé
    """
    global _pool

    if _pool is None:
        _pool = creer_pool_connexions()

    return _pool


def fermer_pool() -> None:
    """
    Ferme le pool de connexions MySQL.

    Note: Cette fonction doit être appelée lors de l'arrêt de l'application
    (shutdown event dans FastAPI).
    """
    global _pool

    if _pool is not None:
        logger.info("Fermeture du pool de connexions MySQL...")

        # Note: mysql.connector.pooling.MySQLConnectionPool n'a pas de méthode close()
        # Les connexions sont automatiquement fermées lors de la destruction de l'objet

        _pool = None
        logger.info("[OK] Pool MySQL fermé")


def obtenir_connexion() -> mysql.connector.MySQLConnection:
    """
    Obtient une connexion depuis le pool.

    Returns:
        Connexion MySQL

    Raises:
        ErreurConnexionBD: Si aucune connexion n'est disponible

    Example:
        >>> conn = obtenir_connexion()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM base_connaissances LIMIT 1")
        >>> result = cursor.fetchone()
        >>> cursor.close()
        >>> conn.close()  # Retourne la connexion au pool
    """
    try:
        pool = obtenir_pool()
        connexion = pool.get_connection()

        if not connexion.is_connected():
            raise ErreurConnexionBD(
                host=settings.MYSQL_HOST,
                database=settings.MYSQL_DATABASE,
                raison="Connexion non active après récupération depuis le pool"
            )

        return connexion

    except MySQLError as e:
        logger.error(f"[ERREUR] Échec d'obtention de connexion depuis le pool: {e}")
        raise ErreurConnexionBD(
            host=settings.MYSQL_HOST,
            database=settings.MYSQL_DATABASE,
            raison=str(e)
        )


@contextmanager
def obtenir_connexion_context():
    """
    Context manager pour obtenir et libérer automatiquement une connexion.

    Yields:
        Connexion MySQL

    Raises:
        ErreurConnexionBD: Si aucune connexion n'est disponible

    Example:
        >>> with obtenir_connexion_context() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM base_connaissances")
        ...     results = cursor.fetchall()
        ...     cursor.close()
        ... # La connexion est automatiquement retournée au pool
    """
    connexion = obtenir_connexion()

    try:
        yield connexion
    finally:
        if connexion.is_connected():
            connexion.close()  # Retourne la connexion au pool


@contextmanager
def obtenir_curseur():
    """
    Context manager pour obtenir connexion + curseur et les libérer automatiquement.

    Yields:
        Tuple (connexion, curseur)

    Raises:
        ErreurConnexionBD: Si aucune connexion n'est disponible

    Example:
        >>> with obtenir_curseur() as (conn, cursor):
        ...     cursor.execute("SELECT COUNT(*) FROM base_connaissances")
        ...     count = cursor.fetchone()[0]
        ...     print(f"Nombre d'entrées: {count}")
        ... # Curseur et connexion automatiquement fermés
    """
    connexion = obtenir_connexion()
    curseur = None

    try:
        curseur = connexion.cursor(dictionary=True)
        yield connexion, curseur
    finally:
        if curseur is not None:
            curseur.close()
        if connexion.is_connected():
            connexion.close()


def verifier_connexion() -> bool:
    """
    Vérifie que la connexion à MySQL fonctionne.

    Returns:
        True si la connexion fonctionne, False sinon

    Example:
        >>> if verifier_connexion():
        ...     print("MySQL OK")
        ... else:
        ...     print("MySQL KO")
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            if result and list(result.values())[0] == 1:
                logger.info("[OK] Connexion MySQL OK")
                return True

        return False

    except Exception as e:
        logger.error(f"[ERREUR] Vérification connexion MySQL échouée: {e}")
        return False


def obtenir_info_bd() -> dict:
    """
    Obtient des informations sur la base de données.

    Returns:
        Dictionnaire avec les informations de la base de données

    Example:
        >>> info = obtenir_info_bd()
        >>> print(info['version'])
        '8.0.33'
    """
    try:
        with obtenir_curseur() as (conn, cursor):
            # Version MySQL
            cursor.execute("SELECT VERSION() as version")
            version_result = cursor.fetchone()

            # Nom de la base de données
            cursor.execute("SELECT DATABASE() as database_name")
            db_result = cursor.fetchone()

            # Nombre de tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            # Taille de la base de données
            cursor.execute("""
                SELECT
                    SUM(data_length + index_length) / 1024 / 1024 as size_mb
                FROM information_schema.TABLES
                WHERE table_schema = %s
            """, (settings.MYSQL_DATABASE,))
            size_result = cursor.fetchone()

            return {
                'version': version_result['version'] if version_result else 'unknown',
                'database': db_result['database_name'] if db_result else 'unknown',
                'tables_count': len(tables),
                'size_mb': round(size_result['size_mb'], 2) if size_result and size_result['size_mb'] else 0,
                'host': settings.MYSQL_HOST,
                'port': settings.MYSQL_PORT,
                'charset': settings.MYSQL_CHARSET,
                'pool_size': settings.MYSQL_POOL_SIZE
            }

    except Exception as e:
        logger.error(f"[ERREUR] Erreur lors de la récupération des infos BD: {e}")
        return {
            'error': str(e)
        }


# ============================================================================
# Fonctions d'initialisation et shutdown
# ============================================================================

def initialiser_connexions() -> None:
    """
    Initialise le pool de connexions MySQL.

    À appeler au démarrage de l'application (startup event dans FastAPI).
    """
    logger.info("Initialisation des connexions MySQL...")

    try:
        pool = obtenir_pool()

        # Vérifier la connexion
        if not verifier_connexion():
            raise ErreurConnexionBD(
                host=settings.MYSQL_HOST,
                database=settings.MYSQL_DATABASE,
                raison="Vérification de connexion échouée"
            )

        # Afficher les infos
        info = obtenir_info_bd()
        logger.info(f"MySQL {info.get('version')} - {info.get('tables_count')} tables - {info.get('size_mb')} Mo")

    except Exception as e:
        logger.error(f"[ERREUR] Échec d'initialisation des connexions: {e}")
        raise


def fermer_connexions() -> None:
    """
    Ferme toutes les connexions MySQL.

    À appeler à l'arrêt de l'application (shutdown event dans FastAPI).
    """
    logger.info("Fermeture des connexions MySQL...")

    try:
        fermer_pool()
        logger.info("[OK] Connexions MySQL fermées")

    except Exception as e:
        logger.error(f"[ATTENTION]  Erreur lors de la fermeture des connexions: {e}")


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'obtenir_connexion',
    'obtenir_connexion_context',
    'obtenir_curseur',
    'verifier_connexion',
    'obtenir_info_bd',
    'initialiser_connexions',
    'fermer_connexions',
    'creer_pool_connexions',
    'obtenir_pool',
    'fermer_pool'
]
