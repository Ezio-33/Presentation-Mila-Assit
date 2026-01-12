"""
Module des exceptions personnalisées pour Mila-Assist.

Définit toutes les exceptions métier de l'application pour une gestion
d'erreurs cohérente et informative.
"""

from typing import Optional, Any, Dict


# ============================================================================
# Classe de base
# ============================================================================

class MilaAssistException(Exception):
    """
    Classe de base pour toutes les exceptions de Mila-Assist.

    Attributes:
        message: Message d'erreur descriptif
        code: Code d'erreur optionnel
        details: Détails additionnels optionnels
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialise l'exception.

        Args:
            message: Message d'erreur
            code: Code d'erreur optionnel (ex: "DB_CONNECTION_FAILED")
            details: Détails additionnels sous forme de dictionnaire
        """
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Représentation string de l'exception."""
        if self.details:
            return f"[{self.code}] {self.message} - Details: {self.details}"
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'exception en dictionnaire pour sérialisation JSON.

        Returns:
            Dictionnaire avec les informations de l'exception
        """
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# Exceptions Embeddings
# ============================================================================

class ErreurEmbedding(MilaAssistException):
    """Exception levée lors d'erreurs liées aux embeddings."""

    def __init__(
        self,
        message: str = "Erreur lors du calcul des embeddings",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class ErreurChargementModeleEmbedding(ErreurEmbedding):
    """Exception levée lors du chargement du modèle d'embeddings."""

    def __init__(
        self,
        model_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Échec du chargement du modèle d'embeddings: {model_name}"
        super().__init__(
            message,
            code="EMBEDDING_MODEL_LOAD_FAILED",
            details=details or {"model_name": model_name}
        )


class ErreurEncodageTexte(ErreurEmbedding):
    """Exception levée lors de l'encodage d'un texte en embedding."""

    def __init__(
        self,
        texte: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Échec de l'encodage du texte"
        if raison:
            message += f": {raison}"

        details = kwargs.get('details', {})
        details['texte_longueur'] = len(texte)

        super().__init__(
            message,
            code="TEXT_ENCODING_FAILED",
            details=details
        )


# ============================================================================
# Exceptions Base de Données
# ============================================================================

class ErreurBaseDeDonnees(MilaAssistException):
    """Exception levée lors d'erreurs liées à la base de données."""

    def __init__(
        self,
        message: str = "Erreur de base de données",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=code or "DATABASE_ERROR", details=details)


class ErreurConnexionBD(ErreurBaseDeDonnees):
    """Exception levée lors d'échecs de connexion à la base de données."""

    def __init__(
        self,
        host: str,
        database: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Échec de connexion à MySQL ({host}/{database})"
        if raison:
            message += f": {raison}"

        details = kwargs.get('details', {})
        details.update({'host': host, 'database': database})

        super().__init__(
            message,
            code="DB_CONNECTION_FAILED",
            details=details
        )


class ErreurRequeteBD(ErreurBaseDeDonnees):
    """Exception levée lors d'erreurs d'exécution de requêtes SQL."""

    def __init__(
        self,
        requete: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Échec d'exécution de la requête SQL"
        if raison:
            message += f": {raison}"

        details = kwargs.get('details', {})
        # Limiter la taille de la requête dans les détails
        details['requete'] = requete[:200] + ('...' if len(requete) > 200 else '')

        super().__init__(
            message,
            code="SQL_QUERY_FAILED",
            details=details
        )


class ErreurIntegriteBD(ErreurBaseDeDonnees):
    """Exception levée lors de violations de contraintes d'intégrité."""

    def __init__(
        self,
        contrainte: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Violation de contrainte d'intégrité: {contrainte}"
        if raison:
            message += f" - {raison}"

        super().__init__(
            message,
            code="DB_INTEGRITY_ERROR",
            **kwargs
        )


class ErreurEnregistrementIntrouvable(ErreurBaseDeDonnees):
    """Exception levée quand un enregistrement demandé n'existe pas."""

    def __init__(
        self,
        table: str,
        identifiant: Any,
        **kwargs
    ):
        message = f"Enregistrement introuvable dans {table} (id={identifiant})"

        details = kwargs.get('details', {})
        details.update({'table': table, 'id': identifiant})

        super().__init__(
            message,
            code="RECORD_NOT_FOUND",
            details=details
        )


# ============================================================================
# Exceptions LLM (Large Language Model)
# ============================================================================

class ErreurLLM(MilaAssistException):
    """Exception levée lors d'erreurs liées au modèle de langage."""

    def __init__(
        self,
        message: str = "Erreur du modèle de langage",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=code or "LLM_ERROR", details=details)


class ErreurChargementModeleLLM(ErreurLLM):
    """Exception levée lors du chargement du modèle LLM."""

    def __init__(
        self,
        model_path: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Échec du chargement du modèle LLM: {model_path}"
        if raison:
            message += f" - {raison}"

        details = kwargs.get('details', {})
        details['model_path'] = model_path

        super().__init__(
            message,
            code="LLM_MODEL_LOAD_FAILED",
            details=details
        )


class ErreurGenerationTexte(ErreurLLM):
    """Exception levée lors de la génération de texte par le LLM."""

    def __init__(
        self,
        prompt: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = "Échec de la génération de texte par le LLM"
        if raison:
            message += f": {raison}"

        details = kwargs.get('details', {})
        # Limiter la taille du prompt dans les détails
        details['prompt'] = prompt[:200] + ('...' if len(prompt) > 200 else '')

        super().__init__(
            message,
            code="TEXT_GENERATION_FAILED",
            details=details
        )


class ErreurTimeoutLLM(ErreurLLM):
    """Exception levée lorsque le LLM dépasse le timeout."""

    def __init__(
        self,
        timeout_seconds: int,
        **kwargs
    ):
        message = f"Le LLM a dépassé le timeout de {timeout_seconds}s"

        details = kwargs.get('details', {})
        details['timeout_seconds'] = timeout_seconds

        super().__init__(
            message,
            code="LLM_TIMEOUT",
            details=details
        )


# ============================================================================
# Exceptions FAISS
# ============================================================================

class ErreurFAISS(MilaAssistException):
    """Exception levée lors d'erreurs liées à FAISS."""

    def __init__(
        self,
        message: str = "Erreur FAISS",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=code or "FAISS_ERROR", details=details)


class ErreurChargementIndexFAISS(ErreurFAISS):
    """Exception levée lors du chargement de l'index FAISS."""

    def __init__(
        self,
        index_path: str,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = f"Échec du chargement de l'index FAISS: {index_path}"
        if raison:
            message += f" - {raison}"

        details = kwargs.get('details', {})
        details['index_path'] = index_path

        super().__init__(
            message,
            code="FAISS_INDEX_LOAD_FAILED",
            details=details
        )


class ErreurRechercheFAISS(ErreurFAISS):
    """Exception levée lors d'une recherche FAISS."""

    def __init__(
        self,
        raison: Optional[str] = None,
        **kwargs
    ):
        message = "Échec de la recherche FAISS"
        if raison:
            message += f": {raison}"

        super().__init__(
            message,
            code="FAISS_SEARCH_FAILED",
            **kwargs
        )


# ============================================================================
# Exceptions Validation
# ============================================================================

class ErreurValidation(MilaAssistException):
    """Exception levée lors d'erreurs de validation de données."""

    def __init__(
        self,
        message: str = "Erreur de validation",
        champ: Optional[str] = None,
        **kwargs
    ):
        if champ:
            message = f"Validation échouée pour le champ '{champ}': {message}"

        details = kwargs.get('details', {})
        if champ:
            details['champ'] = champ

        super().__init__(message, code="VALIDATION_ERROR", details=details)


class ErreurValidationQuestion(ErreurValidation):
    """Exception levée lors de la validation d'une question utilisateur."""

    def __init__(
        self,
        question: str,
        raison: str,
        **kwargs
    ):
        super().__init__(
            message=raison,
            champ="question",
            details={'question_longueur': len(question)}
        )


# ============================================================================
# Exceptions Configuration
# ============================================================================

class ErreurConfiguration(MilaAssistException):
    """Exception levée lors d'erreurs de configuration."""

    def __init__(
        self,
        message: str = "Erreur de configuration",
        parametre: Optional[str] = None,
        **kwargs
    ):
        if parametre:
            message = f"Paramètre de configuration invalide '{parametre}': {message}"

        details = kwargs.get('details', {})
        if parametre:
            details['parametre'] = parametre

        super().__init__(message, code="CONFIG_ERROR", details=details)


# ============================================================================
# Exceptions API
# ============================================================================

class ErreurAPI(MilaAssistException):
    """Exception levée lors d'erreurs API."""

    def __init__(
        self,
        message: str = "Erreur API",
        status_code: int = 500,
        code: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details['status_code'] = status_code

        super().__init__(message, code=code or "API_ERROR", details=details)


class ErreurRateLimiting(ErreurAPI):
    """Exception levée lorsque la limite de requêtes est atteinte."""

    def __init__(
        self,
        limite: int,
        periode: str = "minute",
        **kwargs
    ):
        message = f"Limite de {limite} requêtes par {periode} atteinte"

        details = kwargs.get('details', {})
        details.update({'limite': limite, 'periode': periode})

        super().__init__(
            message,
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class ErreurAuthentification(ErreurAPI):
    """Exception levée lors d'erreurs d'authentification."""

    def __init__(
        self,
        message: str = "Authentification échouée",
        **kwargs
    ):
        super().__init__(
            message,
            status_code=401,
            code="AUTHENTICATION_FAILED",
            **kwargs
        )


class ErreurAutorisation(ErreurAPI):
    """Exception levée lors d'erreurs d'autorisation."""

    def __init__(
        self,
        message: str = "Accès non autorisé",
        ressource: Optional[str] = None,
        **kwargs
    ):
        if ressource:
            message += f" à la ressource: {ressource}"

        details = kwargs.get('details', {})
        if ressource:
            details['ressource'] = ressource

        super().__init__(
            message,
            status_code=403,
            code="AUTHORIZATION_FAILED",
            details=details
        )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Base
    'MilaAssistException',

    # Embeddings
    'ErreurEmbedding',
    'ErreurChargementModeleEmbedding',
    'ErreurEncodageTexte',

    # Base de données
    'ErreurBaseDeDonnees',
    'ErreurConnexionBD',
    'ErreurRequeteBD',
    'ErreurIntegriteBD',
    'ErreurEnregistrementIntrouvable',

    # LLM
    'ErreurLLM',
    'ErreurChargementModeleLLM',
    'ErreurGenerationTexte',
    'ErreurTimeoutLLM',

    # FAISS
    'ErreurFAISS',
    'ErreurChargementIndexFAISS',
    'ErreurRechercheFAISS',

    # Validation
    'ErreurValidation',
    'ErreurValidationQuestion',

    # Configuration
    'ErreurConfiguration',

    # API
    'ErreurAPI',
    'ErreurRateLimiting',
    'ErreurAuthentification',
    'ErreurAutorisation',
]
