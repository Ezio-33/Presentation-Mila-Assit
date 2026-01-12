"""
Module d'embeddings pour Container 3 (LLM + FAISS Service).

Gère le calcul des embeddings de texte avec sentence-transformers
pour la construction de l'index FAISS.
"""

import logging
import os
from typing import Union, List
import numpy as np

from sentence_transformers import SentenceTransformer

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Variables d'environnement
EMBEDDINGS_MODEL_NAME = os.getenv("EMBEDDINGS_MODEL_NAME", "antoinelouis/biencoder-camembert-base-mmarcoFR")
EMBEDDINGS_MODEL_PATH = os.getenv("EMBEDDINGS_MODEL_PATH", "/app/modeles/embeddings")
EMBEDDINGS_MAX_SEQ_LENGTH = int(os.getenv("EMBEDDINGS_MAX_SEQ_LENGTH", "256"))
EMBEDDINGS_BATCH_SIZE = int(os.getenv("EMBEDDINGS_BATCH_SIZE", "32"))
EMBEDDINGS_DEVICE = os.getenv("EMBEDDINGS_DEVICE", "cpu")


# ============================================================================
# Classe EncodeurSentences
# ============================================================================

class EncodeurSentences:
    """
    Encodeur de phrases en embeddings vectoriels.

    Utilise sentence-transformers pour générer des représentations
    vectorielles denses à partir de texte.

    Attributes:
        model: Modèle SentenceTransformer chargé
        dimension: Dimension des vecteurs d'embeddings
        max_seq_length: Longueur maximale des séquences
    """

    def __init__(
        self,
        model_name: str = None,
        model_path: str = None,
        max_seq_length: int = None,
        device: str = None
    ):
        """
        Initialise l'encodeur de sentences.

        Args:
            model_name: Nom du modèle sur Hugging Face
            model_path: Chemin local du modèle (prioritaire sur model_name)
            max_seq_length: Longueur maximale des séquences (défaut: 256)
            device: Device à utiliser ('cpu', 'cuda', 'mps')

        Raises:
            Exception: Si le chargement du modèle échoue
        """
        self.model_name = model_name or EMBEDDINGS_MODEL_NAME
        self.model_path = model_path or EMBEDDINGS_MODEL_PATH
        self.max_seq_length = max_seq_length or EMBEDDINGS_MAX_SEQ_LENGTH
        self.device = device or EMBEDDINGS_DEVICE

        logger.info(f"Initialisation de l'encodeur de sentences...")
        logger.info(f"  Modèle: {self.model_name}")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Max sequence length: {self.max_seq_length}")

        try:
            # Charger le modèle (local prioritaire SI LE MODÈLE EST COMPLET)
            # Vérifier si le dossier contient un modèle complet (config.json + poids)
            model_config_path = os.path.join(self.model_path, "config.json")
            model_weights_bin = os.path.join(self.model_path, "pytorch_model.bin")
            model_weights_safetensors = os.path.join(self.model_path, "model.safetensors")
            
            # Le modèle est complet si config.json ET (pytorch_model.bin OU model.safetensors) existent
            has_config = os.path.isfile(model_config_path)
            has_weights = os.path.isfile(model_weights_bin) or os.path.isfile(model_weights_safetensors)
            model_local_complet = has_config and has_weights

            logger.info(f"  Debug - Vérification modèle local:")
            logger.info(f"    Path: {self.model_path}")
            logger.info(f"    Existe: {os.path.exists(self.model_path)}")
            if os.path.exists(self.model_path):
                logger.info(f"    Contenu: {os.listdir(self.model_path) if os.path.isdir(self.model_path) else 'N/A'}")
                logger.info(f"    config.json présent: {has_config}")
                logger.info(f"    Poids modèle présents: {has_weights}")
                logger.info(f"    Modèle complet: {model_local_complet}")

            if os.path.exists(self.model_path) and model_local_complet:
                logger.info(f"  ✓ Modèle local COMPLET détecté - Chargement depuis: {self.model_path}")
                self.model = SentenceTransformer(
                    self.model_path,
                    device=self.device
                )
            else:
                # Si le dossier n'existe pas ou est incomplet, télécharger depuis HuggingFace
                if os.path.exists(self.model_path):
                    if not has_config:
                        logger.info(f"  [ATTENTION] Dossier {self.model_path} existe mais ne contient pas config.json")
                    elif not has_weights:
                        logger.warning(f"  [ATTENTION] Dossier {self.model_path} existe mais manque les poids du modèle (pytorch_model.bin ou model.safetensors)")
                logger.info(f"  → Téléchargement depuis Hugging Face: {self.model_name}")
                logger.info(f"  → Cache destination: {os.getenv('HF_HOME', 'default')}")

                # Vérifier permissions cache avant téléchargement
                cache_dir = os.getenv('HF_HOME', '/app/cache_huggingface')
                logger.info(f"  Debug - Vérification cache HuggingFace:")
                logger.info(f"    HF_HOME: {os.getenv('HF_HOME', 'non défini')}")
                logger.info(f"    TRANSFORMERS_CACHE: {os.getenv('TRANSFORMERS_CACHE', 'non défini')}")
                logger.info(f"    Cache dir existe: {os.path.exists(cache_dir)}")
                if os.path.exists(cache_dir):
                    import stat
                    cache_stat = os.stat(cache_dir)
                    cache_perms = oct(cache_stat.st_mode)[-3:]
                    logger.info(f"    Permissions cache: {cache_perms}")
                    logger.info(f"    Owner cache: {cache_stat.st_uid}:{cache_stat.st_gid}")
                    # Tester écriture
                    test_file = os.path.join(cache_dir, '.write_test')
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        logger.info(f"    ✓ Test écriture cache: OK")
                    except Exception as e:
                        logger.error(f"    ✗ Test écriture cache: ÉCHEC - {e}")

                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )

            # Configurer la longueur maximale
            self.model.max_seq_length = self.max_seq_length

            # Obtenir la dimension des embeddings
            self.dimension = self.model.get_sentence_embedding_dimension()

            logger.info(f"[OK] Modèle chargé avec succès")
            logger.info(f"  Dimension: {self.dimension}")

        except Exception as e:
            logger.error(f"[ERREUR] Échec du chargement du modèle d'embeddings: {e}")
            raise Exception(f"Erreur chargement modèle embeddings: {e}")

    def encoder(
        self,
        texte: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = None,
        show_progress_bar: bool = False
    ) -> np.ndarray:
        """
        Encode un texte ou une liste de textes en embeddings.

        Args:
            texte: Texte ou liste de textes à encoder
            normalize: Normaliser les vecteurs (L2 norm) pour similarité cosinus
            batch_size: Taille des batchs pour traitement par lots
            show_progress_bar: Afficher la barre de progression

        Returns:
            Vecteur numpy d'embeddings (1D si texte unique, 2D si liste)

        Raises:
            ValueError: Si le texte est vide
            Exception: Si l'encodage échoue

        Example:
            >>> encodeur = EncodeurSentences()
            >>> embedding = encodeur.encoder("Bonjour le monde")
            >>> print(embedding.shape)
            (768,)
        """
        batch_size = batch_size or EMBEDDINGS_BATCH_SIZE

        try:
            # Vérifier que le texte n'est pas vide
            if isinstance(texte, str):
                if not texte.strip():
                    raise ValueError("Le texte ne peut pas être vide")
            elif isinstance(texte, list):
                if not texte or all(not t.strip() for t in texte):
                    raise ValueError("La liste de textes ne peut pas être vide")

            # Encoder
            embeddings = self.model.encode(
                texte,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )

            return embeddings

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de l'encodage: {e}")
            texte_str = texte if isinstance(texte, str) else f"Liste de {len(texte)} textes"
            raise Exception(f"Erreur encodage texte '{texte_str}': {e}")

    def encoder_batch(
        self,
        textes: List[str],
        batch_size: int = None,
        show_progress_bar: bool = True
    ) -> np.ndarray:
        """
        Encode une liste de textes en batch.

        Args:
            textes: Liste de textes à encoder
            batch_size: Taille des batchs
            show_progress_bar: Afficher la progression

        Returns:
            Matrice numpy d'embeddings (shape: [n_textes, dimension])

        Example:
            >>> encodeur = EncodeurSentences()
            >>> embeddings = encodeur.encoder_batch(["Texte 1", "Texte 2", "Texte 3"])
            >>> print(embeddings.shape)
            (3, 768)
        """
        return self.encoder(
            textes,
            normalize=True,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar
        )

    def similarite_cosinus(
        self,
        texte1: Union[str, np.ndarray],
        texte2: Union[str, np.ndarray]
    ) -> float:
        """
        Calcule la similarité cosinus entre deux textes.

        Args:
            texte1: Premier texte ou embedding
            texte2: Deuxième texte ou embedding

        Returns:
            Score de similarité entre -1 et 1 (1 = identique)

        Example:
            >>> encodeur = EncodeurSentences()
            >>> score = encodeur.similarite_cosinus("Bonjour", "Hello")
            >>> print(f"Similarité: {score:.3f}")
        """
        # Encoder si ce sont des strings
        if isinstance(texte1, str):
            emb1 = self.encoder(texte1, normalize=True)
        else:
            emb1 = texte1

        if isinstance(texte2, str):
            emb2 = self.encoder(texte2, normalize=True)
        else:
            emb2 = texte2

        # Calculer la similarité cosinus (produit scalaire si normalisé)
        similarite = np.dot(emb1, emb2)

        return float(similarite)

    def __repr__(self) -> str:
        """Représentation string de l'encodeur."""
        return (
            f"EncodeurSentences(\n"
            f"  model_name={self.model_name}\n"
            f"  dimension={self.dimension}\n"
            f"  max_seq_length={self.max_seq_length}\n"
            f"  device={self.device}\n"
            f")"
        )


# ============================================================================
# Singleton global
# ============================================================================

_encodeur_global: EncodeurSentences = None


def obtenir_encodeur() -> EncodeurSentences:
    """
    Obtient l'instance globale de l'encodeur (singleton).

    Returns:
        Instance de EncodeurSentences

    Example:
        >>> encodeur = obtenir_encodeur()
        >>> embedding = encodeur.encoder("Test")
    """
    global _encodeur_global

    if _encodeur_global is None:
        _encodeur_global = EncodeurSentences()

    return _encodeur_global


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'EncodeurSentences',
    'obtenir_encodeur'
]
