"""
Configuration de l'application Mila-Assist.

Ce module charge et valide toutes les variables d'environnement nécessaires
au fonctionnement de l'application à l'aide de Pydantic Settings.

Utilisation:
    from src.utilitaires.config import parametres
    print(parametres.MYSQL_HOST)
"""

from typing import Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Parametres(BaseSettings):
    """
    Paramètres de configuration de l'application.

    Tous les paramètres sont chargés depuis les variables d'environnement
    ou depuis un fichier .env à la racine du projet.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # =================================================================
    # Chemins et Répertoires
    # =================================================================
    BASE_DIR: Path = Field(
        default_factory=lambda: Path("/app"),
        description="Répertoire de base de l'application"
    )

    # =================================================================
    # Configuration Base de Données MySQL
    # =================================================================
    MYSQL_HOST: str = Field(
        default="mysql",
        description="Nom d'hôte ou adresse IP du serveur MySQL"
    )
    MYSQL_PORT: int = Field(
        default=3306,
        ge=1,
        le=65535,
        description="Port du serveur MySQL"
    )
    MYSQL_DATABASE: str = Field(
        default="mila_assist",
        description="Nom de la base de données"
    )
    MYSQL_USER: str = Field(
        default="mila_user",
        description="Nom d'utilisateur MySQL"
    )
    MYSQL_PASSWORD: str = Field(
        ...,
        description="Mot de passe MySQL (OBLIGATOIRE)"
    )
    MYSQL_ROOT_PASSWORD: Optional[str] = Field(
        default=None,
        description="Mot de passe root MySQL (pour migration/init)"
    )
    MYSQL_POOL_NAME: str = Field(
        default="mila_assist_pool",
        description="Nom du pool de connexions MySQL"
    )
    MYSQL_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=32,
        description="Taille du pool de connexions MySQL"
    )
    MYSQL_CHARSET: str = Field(
        default="utf8mb4",
        description="Charset utilisé pour les connexions MySQL"
    )

    # =================================================================
    # Configuration API FastAPI
    # =================================================================
    API_HOST: str = Field(
        default="0.0.0.0",
        description="Adresse d'écoute de l'API"
    )
    API_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port d'écoute de l'API"
    )
    API_WORKERS: int = Field(
        default=2,
        ge=1,
        le=8,
        description="Nombre de workers Uvicorn"
    )
    API_RELOAD: bool = Field(
        default=False,
        description="Activer le rechargement automatique (dev uniquement)"
    )

    # =================================================================
    # Sécurité et Authentification JWT
    # =================================================================
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Clé secrète pour signature JWT (min 32 caractères)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithme de signature JWT"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24 heures
        ge=1,
        description="Durée de validité du token JWT en minutes"
    )

    # =================================================================
    # Configuration Modèles IA
    # =================================================================
    MODEL_EMBEDDINGS: str = Field(
        default="antoinelouis/biencoder-camembert-base-mmarcoFR",
        description="Nom ou chemin du modèle d'embeddings (Français uniquement)"
    )
    EMBEDDINGS_MODEL_NAME: str = Field(
        default="antoinelouis/biencoder-camembert-base-mmarcoFR",
        description="Nom du modèle d'embeddings sur Hugging Face (CamemBERT MS MARCO FR)"
    )
    EMBEDDINGS_MODEL_PATH: Optional[str] = Field(
        default=None,
        description="Chemin local optionnel vers le modèle d'embeddings"
    )
    EMBEDDINGS_MAX_SEQ_LENGTH: int = Field(
        default=256,
        ge=32,
        le=512,
        description="Longueur maximale des séquences pour les embeddings"
    )
    EMBEDDINGS_BATCH_SIZE: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Taille des batches pour l'encodage des embeddings"
    )
    EMBEDDINGS_DIMENSION: int = Field(
        default=768,
        ge=128,
        le=1024,
        description="Dimension des vecteurs d'embeddings (CamemBERT: 768 dims)"
    )

    # Configuration LLM (Large Language Model)
    MODEL_LLM_PATH: str = Field(
        default="/app/modeles/gemma-2-2b-it-q4.gguf",
        description="Chemin vers le modèle LLM Gemma-2-2B quantifié"
    )
    LLM_MODEL_PATH: str = Field(
        default="modeles/gemma-2-2b-it-q4.gguf",
        description="Chemin relatif vers le modèle LLM (pour compatibilité)"
    )
    LLM_N_CTX: int = Field(
        default=4096,
        ge=512,
        le=8192,
        description="Taille du contexte du LLM en tokens"
    )
    LLM_N_THREADS: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Nombre de threads pour l'inférence du LLM"
    )
    LLM_MAX_TOKENS: int = Field(
        default=512,
        ge=1,
        le=2048,
        description="Nombre maximum de tokens à générer"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Température pour la génération (0=déterministe, 2=créatif)"
    )
    LLM_TOP_P: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling (top-p)"
    )
    LLM_TOP_K: int = Field(
        default=40,
        ge=1,
        le=100,
        description="Top-k sampling"
    )
    LLM_REPETITION_PENALTY: float = Field(
        default=1.1,
        ge=1.0,
        le=2.0,
        description="Pénalité pour les répétitions"
    )

    # Configuration FAISS (recherche vectorielle)
    FAISS_INDEX_PATH: str = Field(
        default="/app/donnees/faiss_index/intents.index",
        description="Chemin vers l'index FAISS pré-calculé"
    )
    FAISS_TOP_K: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Nombre de résultats à récupérer depuis FAISS (top-k)"
    )
    MAX_RETRIEVE_RESULTS: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Nombre de résultats à récupérer depuis FAISS (alias de FAISS_TOP_K)"
    )

    # =================================================================
    # Rate Limiting
    # =================================================================
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        ge=1,
        description="Limite de requêtes par minute et par utilisateur"
    )
    RATE_LIMIT_GLOBAL: int = Field(
        default=1000,
        ge=1,
        description="Limite de requêtes globale par minute"
    )

    # =================================================================
    # Logging
    # =================================================================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_FILE: str = Field(
        default="/app/logs/mila_assist.log",
        description="Chemin vers le fichier de logs"
    )

    # =================================================================
    # CORS (Cross-Origin Resource Sharing)
    # =================================================================
    CORS_ORIGINS: str = Field(
        default="https://ezi0.synology.me:10443,http://localhost:3000",
        description="Origines autorisées pour CORS (séparées par virgules)"
    )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def valider_cors_origins(cls, v: str) -> List[str]:
        """Transforme la chaîne CORS_ORIGINS en liste."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # =================================================================
    # Cache
    # =================================================================
    CACHE_ENABLED: bool = Field(
        default=True,
        description="Activer le cache des réponses"
    )
    CACHE_TTL_SECONDS: int = Field(
        default=3600,  # 1 heure
        ge=0,
        description="Durée de vie du cache en secondes"
    )
    CACHE_MAX_SIZE: int = Field(
        default=100,
        ge=1,
        description="Nombre maximum d'entrées dans le cache"
    )

    # =================================================================
    # Métriques et Monitoring
    # =================================================================
    METRICS_ENABLED: bool = Field(
        default=True,
        description="Activer la collecte de métriques"
    )

    # =================================================================
    # Environnement
    # =================================================================
    ENVIRONMENT: str = Field(
        default="production",
        description="Environnement d'exécution (development, production)"
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def valider_environnement(cls, v: str) -> str:
        """Valide que l'environnement est development ou production."""
        v_lower = v.lower()
        if v_lower not in ["development", "production"]:
            raise ValueError("ENVIRONMENT doit être 'development' ou 'production'")
        return v_lower

    @field_validator("LOG_LEVEL")
    @classmethod
    def valider_log_level(cls, v: str) -> str:
        """Valide le niveau de logging."""
        v_upper = v.upper()
        niveaux_valides = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v_upper not in niveaux_valides:
            raise ValueError(f"LOG_LEVEL doit être parmi {niveaux_valides}")
        return v_upper

    # =================================================================
    # Propriétés calculées
    # =================================================================
    @property
    def url_base_donnees(self) -> str:
        """
        Construit l'URL de connexion MySQL.

        Returns:
            URL de connexion au format: mysql://user:pass@host:port/db
        """
        return (
            f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def est_developpement(self) -> bool:
        """Retourne True si l'environnement est 'development'."""
        return self.ENVIRONMENT == "development"

    @property
    def est_production(self) -> bool:
        """Retourne True si l'environnement est 'production'."""
        return self.ENVIRONMENT == "production"

    def afficher_config(self, masquer_secrets: bool = True) -> dict:
        """
        Affiche la configuration actuelle (pour debug).

        Args:
            masquer_secrets: Si True, masque les mots de passe et clés

        Returns:
            Dictionnaire de configuration
        """
        config = self.model_dump()

        if masquer_secrets:
            secrets = [
                "MYSQL_PASSWORD",
                "MYSQL_ROOT_PASSWORD",
                "JWT_SECRET_KEY"
            ]
            for secret in secrets:
                if secret in config and config[secret]:
                    config[secret] = "***MASQUÉ***"

        return config


# Instance globale des paramètres (singleton)
parametres = Parametres()


def get_settings() -> Parametres:
    """
    Retourne l'instance globale des paramètres.

    Cette fonction permet d'obtenir les paramètres de configuration
    de manière compatible avec FastAPI Depends().

    Returns:
        Instance Parametres avec tous les paramètres chargés

    Example:
        from src.utilitaires.config import get_settings
        settings = get_settings()
        print(settings.MYSQL_HOST)
    """
    return parametres


def obtenir_config() -> Parametres:
    """
    Retourne l'instance globale des paramètres (alias de get_settings).

    Cette fonction permet d'obtenir les paramètres de configuration
    avec une nomenclature française cohérente avec le reste du projet.

    Returns:
        Instance Parametres avec tous les paramètres chargés

    Example:
        from src.utilitaires.config import obtenir_config
        config = obtenir_config()
        print(config.MYSQL_HOST)
    """
    return parametres


# Export pour import simplifié
__all__ = ["parametres", "Parametres", "get_settings", "obtenir_config"]
