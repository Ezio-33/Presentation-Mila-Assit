"""
Système de logging centralisé pour Mila-Assist.

Configure un logger avec rotation de fichiers, formatage personnalisé,
et niveaux de log différenciés.

Utilisation:
    from src.utilitaires.logger import logger

    logger.info("Démarrage de l'application")
    logger.error("Erreur lors du chargement du modèle", exc_info=True)
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.utilitaires.config import parametres


class FormatteurCouleur(logging.Formatter):
    """
    Formatteur personnalisé avec codes couleurs ANSI pour la console.
    Les couleurs ne sont appliquées que sur la sortie console, pas dans les fichiers.
    """

    # Codes couleurs ANSI
    GRIS = "\x1b[38;21m"
    BLEU = "\x1b[38;5;39m"
    JAUNE = "\x1b[38;5;226m"
    ROUGE = "\x1b[38;5;196m"
    ROUGE_GRAS = "\x1b[31;1m"
    RESET = "\x1b[0m"

    # Mapping niveau → couleur
    COULEURS = {
        logging.DEBUG: GRIS,
        logging.INFO: BLEU,
        logging.WARNING: JAUNE,
        logging.ERROR: ROUGE,
        logging.CRITICAL: ROUGE_GRAS
    }

    def __init__(self, fmt: str, utiliser_couleurs: bool = True):
        """
        Initialise le formatteur.

        Args:
            fmt: Format du message de log
            utiliser_couleurs: Active/désactive les couleurs
        """
        super().__init__(fmt)
        self.utiliser_couleurs = utiliser_couleurs

    def format(self, record: logging.LogRecord) -> str:
        """
        Formate un enregistrement de log avec couleurs si activées.

        Args:
            record: Enregistrement de log à formater

        Returns:
            Message formaté avec ou sans couleurs
        """
        if self.utiliser_couleurs and record.levelno in self.COULEURS:
            # Copier le record pour ne pas modifier l'original
            record = logging.makeLogRecord(record.__dict__)

            # Ajouter couleur au niveau de log
            couleur = self.COULEURS[record.levelno]
            record.levelname = f"{couleur}{record.levelname:8s}{self.RESET}"

        return super().format(record)


def configurer_logger(
    nom: str = "mila_assist",
    niveau: Optional[str] = None,
    fichier_log: Optional[str] = None,
    rotation_max_bytes: int = 10 * 1024 * 1024,  # 10 Mo
    rotation_backup_count: int = 5
) -> logging.Logger:
    """
    Configure et retourne un logger avec handlers console et fichier.

    Args:
        nom: Nom du logger
        niveau: Niveau de logging (DEBUG, INFO, etc.). Si None, utilise config
        fichier_log: Chemin du fichier de log. Si None, utilise config
        rotation_max_bytes: Taille max d'un fichier log avant rotation
        rotation_backup_count: Nombre de fichiers de backup à conserver

    Returns:
        Logger configuré
    """
    # Déterminer niveau et fichier depuis config si non fournis
    niveau = niveau or parametres.LOG_LEVEL
    fichier_log = fichier_log or parametres.LOG_FILE

    # Créer le logger
    logger_instance = logging.getLogger(nom)
    logger_instance.setLevel(getattr(logging, niveau))

    # Éviter les doublons si déjà configuré
    if logger_instance.handlers:
        return logger_instance

    # Format des logs
    format_console = (
        "%(levelname)s | "
        "%(asctime)s | "
        "%(name)s:%(funcName)s:%(lineno)d | "
        "%(message)s"
    )

    format_fichier = (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(module)s:%(funcName)s:%(lineno)d | "
        "%(message)s | "
        "%(pathname)s"
    )

    format_date = "%Y-%m-%d %H:%M:%S"

    # ===================================================================
    # Handler 1: Console (stdout)
    # ===================================================================
    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setLevel(logging.DEBUG)

    formatteur_console = FormatteurCouleur(
        fmt=format_console,
        utiliser_couleurs=True
    )
    formatteur_console.datefmt = format_date
    handler_console.setFormatter(formatteur_console)

    logger_instance.addHandler(handler_console)

    # ===================================================================
    # Handler 2: Fichier avec rotation
    # ===================================================================
    try:
        # Créer le répertoire de logs si inexistant
        chemin_fichier_log = Path(fichier_log)
        chemin_fichier_log.parent.mkdir(parents=True, exist_ok=True)

        handler_fichier = RotatingFileHandler(
            filename=fichier_log,
            maxBytes=rotation_max_bytes,
            backupCount=rotation_backup_count,
            encoding="utf-8"
        )
        handler_fichier.setLevel(logging.INFO)  # Ne log que INFO+ dans fichier

        formatteur_fichier = logging.Formatter(
            fmt=format_fichier,
            datefmt=format_date
        )
        handler_fichier.setFormatter(formatteur_fichier)

        logger_instance.addHandler(handler_fichier)

    except (OSError, PermissionError) as e:
        logger_instance.warning(
            f"Impossible de créer le fichier de log {fichier_log}: {e}. "
            "Logging sur console uniquement."
        )

    # ===================================================================
    # Handler 3: Erreurs dans fichier séparé (optionnel)
    # ===================================================================
    if parametres.est_production:
        try:
            fichier_erreurs = chemin_fichier_log.parent / "erreurs.log"
            handler_erreurs = RotatingFileHandler(
                filename=str(fichier_erreurs),
                maxBytes=rotation_max_bytes,
                backupCount=rotation_backup_count,
                encoding="utf-8"
            )
            handler_erreurs.setLevel(logging.ERROR)  # Seulement ERROR et CRITICAL
            handler_erreurs.setFormatter(formatteur_fichier)

            logger_instance.addHandler(handler_erreurs)

        except (OSError, PermissionError) as e:
            logger_instance.warning(
                f"Impossible de créer le fichier d'erreurs: {e}"
            )

    # Message de démarrage
    logger_instance.info(
        f"Logger '{nom}' configuré (niveau: {niveau}, fichier: {fichier_log})"
    )

    return logger_instance


# ===================================================================
# Instance globale du logger (singleton)
# ===================================================================
logger = configurer_logger()


# ===================================================================
# Fonction utilitaire pour logging d'exceptions
# ===================================================================
def logger_exception(
    exception: Exception,
    message_contexte: str = "",
    niveau: int = logging.ERROR
) -> None:
    """
    Log une exception avec son stack trace complet.

    Args:
        exception: Exception à logger
        message_contexte: Message contextuel supplémentaire
        niveau: Niveau de log (ERROR par défaut)

    Exemple:
        try:
            1 / 0
        except ZeroDivisionError as e:
            logger_exception(e, "Erreur lors du calcul")
    """
    message = f"{message_contexte}: {type(exception).__name__} - {str(exception)}"
    logger.log(niveau, message, exc_info=True)


# ===================================================================
# Décorateur pour logger les appels de fonction
# ===================================================================
def logger_appels(func):
    """
    Décorateur pour logger automatiquement les appels de fonction.

    Exemple:
        @logger_appels
        def ma_fonction(param1, param2):
            pass
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nom_fonction = func.__name__
        logger.debug(
            f"Appel de {nom_fonction} avec args={args}, kwargs={kwargs}"
        )

        try:
            resultat = func(*args, **kwargs)
            logger.debug(f"{nom_fonction} terminée avec succès")
            return resultat

        except Exception as e:
            logger_exception(
                e,
                f"Erreur dans {nom_fonction}",
                niveau=logging.ERROR
            )
            raise

    return wrapper


def obtenir_logger(nom: Optional[str] = None) -> logging.Logger:
    """
    Retourne l'instance globale du logger ou configure un nouveau logger avec un nom spécifique.

    Cette fonction permet d'obtenir le logger de manière compatible avec les imports
    dans l'application.

    Args:
        nom: Nom optionnel pour un logger spécifique. Si None, retourne le logger global

    Returns:
        Instance de logger configurée

    Example:
        from src.utilitaires.logger import obtenir_logger
        logger = obtenir_logger(__name__)
        logger.info("Message de log")
    """
    if nom is None:
        return logger
    return configurer_logger(nom)


# Export pour import simplifié
__all__ = [
    "logger",
    "configurer_logger",
    "obtenir_logger",
    "logger_exception",
    "logger_appels",
    "FormatteurCouleur"
]
