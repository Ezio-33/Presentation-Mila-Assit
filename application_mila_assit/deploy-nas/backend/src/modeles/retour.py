"""
Modèles Pydantic pour les retours utilisateurs (feedback).
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class StatutRetour(str, Enum):
    """Statut de traitement d'un retour."""
    NOUVEAU = "nouveau"
    EN_COURS = "en_cours"
    TRAITE = "traite"
    ARCHIVE = "archive"


class CategorieProbleme(str, Enum):
    """Catégories de problèmes signalés."""
    REPONSE_INCORRECTE = "reponse_incorrecte"
    REPONSE_INCOMPLETE = "reponse_incomplete"
    REPONSE_NON_PERTINENTE = "reponse_non_pertinente"
    PROBLEME_TECHNIQUE = "probleme_technique"
    AUTRE = "autre"


class RequeteRetour(BaseModel):
    """Requête pour soumettre un retour utilisateur."""
    id_conversation: int = Field(..., gt=0, description="ID de la conversation concernée")
    note: int = Field(..., ge=1, le=5, description="Note de 1 à 5")
    commentaire: Optional[str] = Field(None, max_length=2000, description="Commentaire optionnel")
    categorie_probleme: Optional[CategorieProbleme] = Field(
        None,
        description="Catégorie du problème (si note < 4)"
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "id_conversation": 123,
                "note": 4,
                "commentaire": "Bonne réponse mais un peu longue",
                "categorie_probleme": None
            }
        }


class ReponseRetour(BaseModel):
    """Réponse après soumission d'un retour."""
    id_retour: int = Field(..., description="ID unique du retour")
    id_conversation: int = Field(..., description="ID de la conversation")
    note: int = Field(..., description="Note donnée")
    message: str = Field(..., description="Message de confirmation")

    class Config:
        json_schema_extra = {
            "example": {
                "id_retour": 456,
                "id_conversation": 123,
                "note": 4,
                "message": "Merci pour votre retour !"
            }
        }


class FeedbackAdmin(BaseModel):
    """Détails d'un feedback pour l'interface admin."""
    id_retour: int = Field(..., description="ID du retour")
    id_conversation: int = Field(..., description="ID de la conversation")
    id_session: str = Field(..., description="ID de session")
    question: str = Field(..., description="Question posée")
    reponse: str = Field(..., description="Réponse donnée")
    note: int = Field(..., description="Note (1-5)")
    commentaire: Optional[str] = Field(None, description="Commentaire utilisateur")
    categorie_probleme: Optional[str] = Field(None, description="Catégorie du problème")
    statut: StatutRetour = Field(..., description="Statut de traitement")
    date_creation: datetime = Field(..., description="Date de création du retour")
    date_traitement: Optional[datetime] = Field(None, description="Date de traitement")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "id_retour": 456,
                "id_conversation": 123,
                "id_session": "12345678-1234-4567-8901-234567890123",
                "question": "Comment installer AI_licia ?",
                "reponse": "Pour installer AI_licia...",
                "note": 2,
                "commentaire": "La réponse n'est pas claire",
                "categorie_probleme": "reponse_incomplete",
                "statut": "nouveau",
                "date_creation": "2026-01-05T20:00:00",
                "date_traitement": None
            }
        }


class ReponseFeedbacksAdmin(BaseModel):
    """Réponse paginée de feedbacks pour l'admin."""
    feedbacks: List[FeedbackAdmin] = Field(..., description="Liste des feedbacks")
    total: int = Field(..., description="Nombre total de feedbacks")
    page: int = Field(..., description="Page actuelle")
    taille_page: int = Field(..., description="Taille de la page")

    class Config:
        json_schema_extra = {
            "example": {
                "feedbacks": [],
                "total": 42,
                "page": 1,
                "taille_page": 20
            }
        }
