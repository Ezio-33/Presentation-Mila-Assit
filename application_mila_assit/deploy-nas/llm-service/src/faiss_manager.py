"""
Module de gestion FAISS pour Container 3 (LLM + FAISS Service).

Gère l'index FAISS : chargement, recherche, rebuild.
"""

import logging
import os
import json
from typing import Tuple, Optional, List, Dict
from pathlib import Path
import time

import numpy as np
import faiss
import mysql.connector

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Variables d'environnement
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/app/donnees/faiss_index/index_faiss.bin")
FAISS_TOP_K = int(os.getenv("FAISS_TOP_K", "3"))
EMBEDDINGS_DIMENSION = int(os.getenv("EMBEDDINGS_DIMENSION", "768"))

# MySQL Config
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "mila_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mila_assist")


# ============================================================================
# Classe IndexFAISS
# ============================================================================

class IndexFAISS:
    """
    Gestionnaire d'index FAISS pour recherche de similarité.

    Attributes:
        index: Index FAISS chargé
        dimension: Dimension des vecteurs
        ntotal: Nombre de vecteurs dans l'index
        id_mapping: Mapping index FAISS → ID MySQL
    """

    def __init__(
        self,
        chemin_index: Optional[str] = None,
        dimension: Optional[int] = None,
        creer_nouveau: bool = False
    ):
        """
        Initialise l'index FAISS.

        Args:
            chemin_index: Chemin du fichier index FAISS
            dimension: Dimension des vecteurs (requis si creer_nouveau=True)
            creer_nouveau: Créer un nouvel index vide

        Raises:
            Exception: Si le chargement échoue
        """
        self.chemin_index = chemin_index or FAISS_INDEX_PATH
        self.dimension = dimension or EMBEDDINGS_DIMENSION
        self.index: Optional[faiss.Index] = None
        self.id_mapping: List[int] = []  # Liste des ID MySQL correspondant aux index FAISS

        if creer_nouveau:
            self._creer_index()
        else:
            self._charger_index()

    def _creer_index(self) -> None:
        """Crée un nouvel index FAISS vide."""
        logger.info(f"Création d'un nouvel index FAISS (dimension={self.dimension})...")

        try:
            # Utiliser IndexFlatIP pour similarité cosinus sur vecteurs normalisés
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_mapping = []

            logger.info(f"[OK] Index vide cree")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la creation de l'index: {e}")
            raise Exception(f"Erreur création index FAISS: {e}")

    def _charger_index(self) -> None:
        """Charge l'index FAISS et le mapping IDs depuis le disque."""
        logger.info(f"Chargement de l'index FAISS: {self.chemin_index}")

        try:
            chemin = Path(self.chemin_index)

            if not chemin.exists():
                logger.warning(f"[ATTENTION] Index introuvable: {self.chemin_index}")
                logger.info("Création d'un nouvel index...")
                self._creer_index()
                return

            # Charger l'index
            self.index = faiss.read_index(str(chemin))

            # Charger le mapping IDs (CRITIQUE pour le pipeline RAG)
            chemin_mapping = chemin.parent / "id_mapping.json"
            if chemin_mapping.exists():
                with open(chemin_mapping, 'r') as f:
                    self.id_mapping = json.load(f)
                logger.info(f"[OK] Mapping IDs charge: {len(self.id_mapping)} entrees")
            else:
                logger.warning(f"[ATTENTION] Mapping IDs introuvable: {chemin_mapping}")
                logger.warning("   Le pipeline RAG peut ne pas fonctionner correctement!")
                self.id_mapping = []

            # Vérifier la dimension
            if self.index.d != self.dimension:
                logger.warning(
                    f"[ATTENTION] Dimension de l'index ({self.index.d}) != "
                    f"dimension attendue ({self.dimension})"
                )
                self.dimension = self.index.d

            # Vérifier cohérence mapping/index
            if len(self.id_mapping) != self.index.ntotal:
                logger.warning(
                    f"[ATTENTION] Incoherence: {len(self.id_mapping)} IDs mappes vs "
                    f"{self.index.ntotal} vecteurs dans l'index"
                )

            logger.info(f"[OK] Index charge avec succes")
            logger.info(f"  Vecteurs: {self.index.ntotal}")
            logger.info(f"  Dimension: {self.dimension}")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du chargement de l'index: {e}")
            logger.info("Création d'un nouvel index...")
            self._creer_index()

    def rechercher(
        self,
        vecteur_requete: np.ndarray,
        k: int = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recherche les k vecteurs les plus similaires.

        Args:
            vecteur_requete: Vecteur de requête (1D ou 2D avec shape [1, dimension])
            k: Nombre de résultats à retourner

        Returns:
            Tuple (distances, indices) où:
                - distances: Scores de similarité (shape: [1, k])
                - indices: Indices des vecteurs trouvés (shape: [1, k])

        Raises:
            Exception: Si la recherche échoue

        Example:
            >>> index_faiss = IndexFAISS()
            >>> vecteur = np.random.rand(768)
            >>> distances, indices = index_faiss.rechercher(vecteur, k=3)
            >>> print(f"Top-3: {indices[0]}")
        """
        k = k or FAISS_TOP_K

        try:
            # Vérifier que l'index est chargé
            if self.index is None:
                raise ValueError("Index FAISS non chargé")

            # Vérifier que k n'est pas supérieur au nombre de vecteurs
            k_effective = min(k, self.index.ntotal)

            if k_effective != k:
                logger.warning(
                    f"[ATTENTION] k={k} > ntotal={self.index.ntotal}, "
                    f"utilisation de k={k_effective}"
                )

            if k_effective == 0:
                logger.warning("[ATTENTION] Index vide, retour de resultats vides")
                return np.array([[0.0]]), np.array([[-1]])

            # Assurer que le vecteur est 2D (shape: [1, dimension])
            if vecteur_requete.ndim == 1:
                vecteur_requete = np.expand_dims(vecteur_requete, axis=0)

            # Vérifier la dimension
            if vecteur_requete.shape[1] != self.dimension:
                raise ValueError(
                    f"Dimension du vecteur ({vecteur_requete.shape[1]}) != "
                    f"dimension de l'index ({self.dimension})"
                )

            # Normaliser le vecteur de requête (pour similarité cosinus)
            faiss.normalize_L2(vecteur_requete)

            # Rechercher
            distances, indices = self.index.search(vecteur_requete, k_effective)

            return distances, indices

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la recherche FAISS: {e}")
            raise Exception(f"Erreur recherche FAISS: {e}")

    def ajouter_vecteurs(
        self,
        vecteurs: np.ndarray,
        ids: List[int],
        normaliser: bool = True
    ) -> None:
        """
        Ajoute des vecteurs à l'index.

        Args:
            vecteurs: Matrice de vecteurs (shape: [n_vecteurs, dimension])
            ids: Liste des ID MySQL correspondants
            normaliser: Normaliser les vecteurs avant ajout

        Raises:
            Exception: Si l'ajout échoue
        """
        try:
            if self.index is None:
                raise ValueError("Index FAISS non chargé")

            if len(ids) != len(vecteurs):
                raise ValueError(f"Nombre d'IDs ({len(ids)}) != nombre de vecteurs ({len(vecteurs)})")

            # Normaliser si demandé
            if normaliser:
                faiss.normalize_L2(vecteurs)

            # Ajouter les vecteurs
            self.index.add(vecteurs)

            # Mettre à jour le mapping ID
            self.id_mapping.extend(ids)

            logger.info(f"[OK] {len(vecteurs)} vecteurs ajoutes (total: {self.index.ntotal})")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de l'ajout de vecteurs: {e}")
            raise Exception(f"Erreur ajout vecteurs FAISS: {e}")

    def sauvegarder(self, chemin: Optional[str] = None) -> None:
        """
        Sauvegarde l'index et le mapping IDs sur le disque.

        Args:
            chemin: Chemin de sauvegarde (défaut: self.chemin_index)
        """
        chemin = chemin or self.chemin_index

        try:
            if self.index is None:
                raise ValueError("Index FAISS non chargé")

            # Créer le répertoire parent si nécessaire
            Path(chemin).parent.mkdir(parents=True, exist_ok=True)

            # Sauvegarder l'index FAISS
            faiss.write_index(self.index, chemin)

            # Sauvegarder le mapping IDs (CRITIQUE pour le pipeline RAG)
            chemin_mapping = str(Path(chemin).parent / "id_mapping.json")
            with open(chemin_mapping, 'w') as f:
                json.dump(self.id_mapping, f)

            size_mb = Path(chemin).stat().st_size / (1024 * 1024)
            logger.info(f"[OK] Index sauvegarde: {chemin} ({size_mb:.2f} Mo)")
            logger.info(f"[OK] Mapping IDs sauvegarde: {chemin_mapping} ({len(self.id_mapping)} entrees)")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la sauvegarde: {e}")
            raise

    def obtenir_ids_mysql(self, indices_faiss: np.ndarray) -> List[int]:
        """
        Convertit les indices FAISS en IDs MySQL.

        Args:
            indices_faiss: Array d'indices FAISS

        Returns:
            Liste d'IDs MySQL correspondants
        """
        ids_mysql = []
        for idx in indices_faiss.flatten():
            if idx >= 0 and idx < len(self.id_mapping):
                ids_mysql.append(self.id_mapping[idx])
            else:
                logger.warning(f"[ATTENTION] Index FAISS invalide: {idx}")
                ids_mysql.append(-1)

        return ids_mysql

    def rebuild_depuis_mysql(self, encodeur) -> Dict[str, any]:
        """
        Reconstruit l'index FAISS depuis la base MySQL.

        Args:
            encodeur: Instance de EncodeurSentences pour générer les embeddings

        Returns:
            Dict avec statistiques du rebuild

        Raises:
            Exception: Si le rebuild échoue
        """
        logger.info("[REBUILD] Debut du rebuild de l'index FAISS depuis MySQL...")
        start_time = time.time()

        try:
            # Connexion MySQL
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = conn.cursor(dictionary=True)

            # Récupérer toutes les entrées de la base de connaissances
            cursor.execute("""
                SELECT id, question, reponse
                FROM base_connaissances
                WHERE active = 1
                ORDER BY id
            """)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("[ATTENTION] Aucune donnee dans base_connaissances")
                return {"success": False, "raison": "Base de données vide"}

            logger.info(f"  Nombre d'entrées: {len(rows)}")

            # Créer un nouvel index vide
            self._creer_index()

            # Générer les embeddings pour chaque entrée
            textes = [f"{row['question']} {row['reponse']}" for row in rows]
            ids = [row['id'] for row in rows]

            logger.info("  Génération des embeddings...")
            embeddings = encodeur.encoder_batch(textes, show_progress_bar=True)

            # Ajouter à l'index
            self.ajouter_vecteurs(embeddings, ids, normaliser=True)

            # Sauvegarder
            self.sauvegarder()

            # Fermer connexion MySQL
            cursor.close()
            conn.close()

            elapsed_time = time.time() - start_time

            stats = {
                "success": True,
                "nombre_vecteurs": len(rows),
                "temps_secondes": round(elapsed_time, 2),
                "dimension": self.dimension,
                "taille_index_mo": round(Path(self.chemin_index).stat().st_size / (1024 * 1024), 2)
            }

            logger.info(f"[OK] Rebuild termine en {stats['temps_secondes']}s")
            logger.info(f"  Vecteurs: {stats['nombre_vecteurs']}")
            logger.info(f"  Taille: {stats['taille_index_mo']} Mo")

            return stats

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du rebuild FAISS: {e}")
            raise Exception(f"Erreur rebuild FAISS: {e}")

    @property
    def ntotal(self) -> int:
        """Retourne le nombre de vecteurs dans l'index."""
        return self.index.ntotal if self.index else 0

    def __repr__(self) -> str:
        """Représentation string de l'index."""
        return (
            f"IndexFAISS(\n"
            f"  chemin={self.chemin_index}\n"
            f"  dimension={self.dimension}\n"
            f"  ntotal={self.ntotal}\n"
            f")"
        )


# ============================================================================
# Singleton global
# ============================================================================

_index_global: IndexFAISS = None


def obtenir_index() -> IndexFAISS:
    """
    Obtient l'instance globale de l'index FAISS (singleton).

    Returns:
        Instance de IndexFAISS
    """
    global _index_global

    if _index_global is None:
        _index_global = IndexFAISS()

    return _index_global


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'IndexFAISS',
    'obtenir_index'
]
