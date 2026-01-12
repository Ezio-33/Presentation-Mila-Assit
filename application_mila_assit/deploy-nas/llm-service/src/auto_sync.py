"""
Module Auto-Sync FAISS pour Container 3 (LLM + FAISS Service).

Surveille MySQL et déclenche automatiquement le rebuild de l'index FAISS.

IMPORTANT: Ce module surveille UNIQUEMENT la table base_connaissances.
Les modifications dans d'autres tables (conversations, retours_utilisateurs, etc.)
NE DÉCLENCHENT PAS de rebuild de l'index FAISS.

Triggers de rebuild:
1. Premier démarrage (pas d'index existant)
2. MySQL redémarré (uptime < 300s) - Assure la cohérence après redémarrage
3. Base de connaissances modifiée (last_update changé dans base_connaissances)

Protection anti-surcharge:
- Intervalle minimum de 5 minutes entre deux rebuilds successifs
- Logs détaillés pour diagnostiquer les déclenchements intempestifs
"""

import logging
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import mysql.connector

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Variables d'environnement
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "mila_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mila_assist")

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/app/donnees/faiss_index/index_faiss.bin")
AUTO_SYNC_INTERVAL = int(os.getenv("AUTO_SYNC_INTERVAL", "60"))  # secondes
AUTO_SYNC_MYSQL_UPTIME_THRESHOLD = int(os.getenv("AUTO_SYNC_MYSQL_UPTIME_THRESHOLD", "300"))  # 5 minutes


# ============================================================================
# Classe FAISSAutoSync
# ============================================================================

class FAISSAutoSync:
    """
    Gestionnaire auto-sync pour l'index FAISS.

    Surveille MySQL et déclenche le rebuild automatiquement selon 3 triggers:
    1. Index FAISS n'existe pas
    2. MySQL vient de redémarrer (uptime < 5 min)
    3. Base de connaissances modifiée (last_update changé)
    """

    def __init__(self, index_manager, encodeur):
        """
        Initialise l'auto-sync.

        Args:
            index_manager: Instance de IndexFAISS
            encodeur: Instance de EncodeurSentences
        """
        self.index_manager = index_manager
        self.encodeur = encodeur
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_update_timestamp: Optional[datetime] = None
        self.rebuild_en_cours = False
        self.dernier_rebuild_timestamp: Optional[datetime] = None  # Nouvelle protection
        self.rebuild_min_interval_seconds = 300  # Minimum 5 minutes entre 2 rebuilds

        logger.info("Auto-sync FAISS initialisé")
        logger.info(f"  Intervalle surveillance: {AUTO_SYNC_INTERVAL}s")
        logger.info(f"  Intervalle minimum rebuild: {self.rebuild_min_interval_seconds}s")

    def demarrer(self) -> None:
        """Démarre le thread de surveillance auto-sync."""
        if self.running:
            logger.warning("[ATTENTION]  Auto-sync déjà en cours")
            return

        self.running = True
        self.thread = threading.Thread(target=self._boucle_surveillance, daemon=True)
        self.thread.start()

        logger.info("[OK] Auto-sync FAISS démarré")

    def arreter(self) -> None:
        """Arrête le thread de surveillance."""
        if not self.running:
            return

        logger.info("Arrêt de l'auto-sync...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)

        logger.info("[OK] Auto-sync arrêté")

    def _boucle_surveillance(self) -> None:
        """Boucle principale de surveillance (thread)."""
        logger.info(f"Démarrage de la boucle de surveillance (intervalle: {AUTO_SYNC_INTERVAL}s)")

        # Vérification initiale au démarrage
        time.sleep(5)  # Attendre que les services soient prêts
        self._verifier_triggers()

        # Boucle continue
        while self.running:
            try:
                time.sleep(AUTO_SYNC_INTERVAL)
                self._verifier_triggers()

            except Exception as e:
                logger.error(f"[ERREUR] Erreur dans la boucle auto-sync: {e}")
                time.sleep(10)  # Pause avant retry

    def _verifier_triggers(self) -> None:
        """Vérifie les 3 triggers et déclenche rebuild si nécessaire."""
        if self.rebuild_en_cours:
            logger.debug("Rebuild déjà en cours, skip vérification")
            return

        try:
            # Trigger 1: Index n'existe pas
            if not Path(FAISS_INDEX_PATH).exists():
                logger.info("[SEARCH] Trigger 1 : Index FAISS n'existe pas")
                self._declencher_rebuild("Index n'existe pas")
                return

            # Vérifier uptime MySQL et last_update
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                connect_timeout=5
            )
            cursor = conn.cursor(dictionary=True)

            # Trigger 2: MySQL vient de redémarrer
            # ATTENTION: Ce trigger peut déclencher des rebuilds fréquents
            # si MySQL/Docker redémarre souvent
            cursor.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
            uptime_row = cursor.fetchone()
            if uptime_row:
                uptime_seconds = int(uptime_row['Value'])
                
                # Log toujours l'uptime pour debug (pas seulement en mode debug)
                if uptime_seconds < AUTO_SYNC_MYSQL_UPTIME_THRESHOLD:
                    logger.warning(f"[SEARCH] Trigger 2 : MySQL redémarré récemment!")
                    logger.warning(f"  Uptime MySQL: {uptime_seconds}s (seuil: {AUTO_SYNC_MYSQL_UPTIME_THRESHOLD}s)")
                    logger.warning(f"  Rebuild déclenché pour synchroniser l'index")
                    cursor.close()
                    conn.close()
                    self._declencher_rebuild(f"MySQL redémarré (uptime={uptime_seconds}s)")
                    return
                else:
                    logger.debug(f"MySQL uptime OK: {uptime_seconds}s (pas de rebuild nécessaire)")

            # Trigger 3: Données modifiées UNIQUEMENT dans base_connaissances
            # CRITIQUE: Surveille UNIQUEMENT la table base_connaissances
            # pour éviter les rebuilds lors de l'ajout de conversations
            cursor.execute("""
                SELECT MAX(last_update) as dernier_changement,
                       COUNT(*) as nombre_entrees
                FROM base_connaissances
                WHERE active = 1
            """)
            result = cursor.fetchone()

            if result and result['dernier_changement']:
                dernier_changement = result['dernier_changement']
                nombre_entrees = result['nombre_entrees']

                # Première vérification : initialiser le timestamp
                if self.last_update_timestamp is None:
                    logger.info(f"[SYNC] Initialisation timestamp: {dernier_changement} ({nombre_entrees} entrées actives)")
                    self.last_update_timestamp = dernier_changement
                    cursor.close()
                    conn.close()
                    return

                # Comparer avec le dernier connu
                if dernier_changement > self.last_update_timestamp:
                    logger.info(f"[SEARCH] Trigger 3 : BASE DE CONNAISSANCES modifiée")
                    logger.info(f"  Ancien timestamp: {self.last_update_timestamp}")
                    logger.info(f"  Nouveau timestamp: {dernier_changement}")
                    logger.info(f"  Entrées actives: {nombre_entrees}")
                    cursor.close()
                    conn.close()
                    self._declencher_rebuild(f"Base de connaissances modifiée à {dernier_changement}")
                    self.last_update_timestamp = dernier_changement
                    return
                else:
                    # Log silencieux (debug) pour confirmer qu'aucun changement n'est détecté
                    logger.debug(f"[SYNC] Aucune modification détectée (last_update={dernier_changement})")

            cursor.close()
            conn.close()

        except mysql.connector.Error as e:
            logger.warning(f"[ATTENTION]  Erreur connexion MySQL (auto-sync): {e}")
        except Exception as e:
            logger.error(f"[ERREUR] Erreur vérification triggers: {e}")

    def _declencher_rebuild(self, raison: str) -> None:
        """
        Déclenche le rebuild de l'index FAISS.

        Args:
            raison: Raison du rebuild
        """
        if self.rebuild_en_cours:
            logger.warning("[ATTENTION]  Rebuild déjà en cours, skip")
            return

        # Protection contre les rebuilds trop fréquents
        if self.dernier_rebuild_timestamp:
            temps_ecoule = (datetime.now() - self.dernier_rebuild_timestamp).total_seconds()
            if temps_ecoule < self.rebuild_min_interval_seconds:
                logger.warning(f"[SKIP] Rebuild demandé trop tôt ({temps_ecoule:.0f}s depuis le dernier)")
                logger.warning(f"  Raison ignorée: {raison}")
                logger.warning(f"  Minimum requis: {self.rebuild_min_interval_seconds}s")
                return

        try:
            self.rebuild_en_cours = True
            self.dernier_rebuild_timestamp = datetime.now()
            logger.info(f"[SYNC] Déclenchement rebuild FAISS : {raison}")

            # Effectuer le rebuild
            stats = self.index_manager.rebuild_depuis_mysql(self.encodeur)

            if stats['success']:
                logger.info(f"[OK] Rebuild réussi : {stats['nombre_vecteurs']} vecteurs en {stats['temps_secondes']}s")
            else:
                logger.error(f"[ERREUR] Rebuild échoué : {stats.get('raison', 'Erreur inconnue')}")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du rebuild: {e}")

        finally:
            self.rebuild_en_cours = False

    def forcer_rebuild(self) -> Dict[str, any]:
        """
        Force un rebuild immédiat (endpoint admin).

        Returns:
            Statistiques du rebuild
        """
        logger.info("[SYNC] Rebuild forcé via endpoint admin")
        return self.index_manager.rebuild_depuis_mysql(self.encodeur)

    def obtenir_statut(self) -> Dict[str, any]:
        """
        Obtient le statut de l'auto-sync.

        Returns:
            Dict avec statut complet
        """
        statut = {
            "actif": self.running,
            "rebuild_en_cours": self.rebuild_en_cours,
            "last_update_timestamp": str(self.last_update_timestamp) if self.last_update_timestamp else None,
            "dernier_rebuild": str(self.dernier_rebuild_timestamp) if self.dernier_rebuild_timestamp else None,
            "intervalle_secondes": AUTO_SYNC_INTERVAL,
            "mysql_uptime_threshold": AUTO_SYNC_MYSQL_UPTIME_THRESHOLD,
            "rebuild_min_interval": self.rebuild_min_interval_seconds,
            "index_existe": Path(FAISS_INDEX_PATH).exists(),
            "index_ntotal": self.index_manager.ntotal
        }

        # Ajouter le temps depuis le dernier rebuild
        if self.dernier_rebuild_timestamp:
            temps_depuis_rebuild = (datetime.now() - self.dernier_rebuild_timestamp).total_seconds()
            statut["temps_depuis_dernier_rebuild_s"] = int(temps_depuis_rebuild)

        return statut


# ============================================================================
# Singleton global
# ============================================================================

_auto_sync_global: FAISSAutoSync = None


def obtenir_auto_sync(index_manager=None, encodeur=None) -> FAISSAutoSync:
    """
    Obtient l'instance globale de l'auto-sync (singleton).

    Args:
        index_manager: Instance IndexFAISS (requis première fois)
        encodeur: Instance EncodeurSentences (requis première fois)

    Returns:
        Instance de FAISSAutoSync
    """
    global _auto_sync_global

    if _auto_sync_global is None:
        if index_manager is None or encodeur is None:
            raise ValueError("index_manager et encodeur requis pour première initialisation")

        _auto_sync_global = FAISSAutoSync(index_manager, encodeur)

    return _auto_sync_global


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'FAISSAutoSync',
    'obtenir_auto_sync'
]
