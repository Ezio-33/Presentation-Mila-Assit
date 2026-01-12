"""
Modèles Pydantic pour les conversations.

Architecture 4 containers (Déc 2025):
- Le client peut optionnellement fournir un embedding pré-calculé (768 dimensions)
- Si absent, le Container 3 le calcule automatiquement
"""

from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class RequeteConversation(BaseModel):
    """
    Modèle pour une requête de conversation (question utilisateur).

    Attributes:
        id_session: UUID de session utilisateur (généré automatiquement si non fourni)
        question: Question posée par l'utilisateur
        embedding: Vecteur embedding calculé côté client (optionnel pour rétrocompatibilité)
    """
    id_session: Optional[str] = Field(
        default_factory=lambda: str(uuid4()),
        description="UUID de session utilisateur (v4)"
    )
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Question posée par l'utilisateur"
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vecteur embedding (768 dimensions CamemBERT) - Architecture 4 containers (Déc 2025)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_session": "550e8400-e29b-41d4-a716-446655440000",
                "question": "Comment configurer le TTS sur AI_licia ?"
            }
        }


class SourceConnaissance(BaseModel):
    """Detail d'une source de la base de connaissances."""
    id: int = Field(..., description="ID de l'entree dans base_connaissances")
    question: str = Field(..., description="Question de reference")
    extrait: str = Field(..., description="Extrait de la reponse (100 premiers caracteres)")


class ReponseConversation(BaseModel):
    """Réponse à une requête de conversation."""
    id_conversation: int = Field(..., description="ID unique de la conversation")
    reponse: str = Field(..., min_length=1, description="Réponse générée par le chatbot")
    confiance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confiance (0-1)"
    )
    sources: List[int] = Field(..., description="IDs base_connaissances utilisés")
    sources_details: Optional[List[SourceConnaissance]] = Field(
        default=None,
        description="Details des sources (question + extrait reponse)"
    )
    temps_ms: int = Field(..., description="Temps de traitement en millisecondes")

    class Config:
        json_schema_extra = {
            "example": {
                "id_conversation": 123,
                "reponse": "Pour configurer le TTS, vous devez...",
                "confiance": 0.85,
                "sources": [42, 156, 89],
                "sources_details": [
                    {"id": 42, "question": "Comment configurer le TTS ?", "extrait": "Pour configurer le TTS, allez dans..."}
                ],
                "temps_ms": 1250
            }
        }
