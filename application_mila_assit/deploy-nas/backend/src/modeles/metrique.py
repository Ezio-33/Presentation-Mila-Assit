"""
Modèles Pydantic pour les métriques et la santé de l'application.
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class StatutSante(str, Enum):
    """Statut de santé d'un composant ou de l'application."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ReponseSante(BaseModel):
    """Réponse du endpoint de santé."""
    statut: StatutSante = Field(..., description="Statut de santé global")
    version: str = Field(..., description="Version de l'application")
    composants: Dict[str, str] = Field(
        default_factory=dict,
        description="État de santé de chaque composant"
    )

    class Config:
        use_enum_values = True


class ReponseMetriques(BaseModel):
    """Réponse du endpoint de métriques."""
    latence_moyenne_ms: float = Field(..., description="Latence moyenne en millisecondes")
    latence_p95_ms: int = Field(..., description="Latence P95 en millisecondes")
    latence_p99_ms: int = Field(..., description="Latence P99 en millisecondes")
    taux_cache_hit: float = Field(..., ge=0.0, le=1.0, description="Taux de hit du cache (0.0 à 1.0)")
    utilisation_ram_go: float = Field(..., description="Utilisation RAM en Go")
    total_requetes: int = Field(..., description="Nombre total de requêtes")
    satisfaction_moyenne: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Note de satisfaction moyenne (1 à 5)"
    )
    periode: str = Field(..., description="Période des métriques (24h, 7d, 30d)")

    class Config:
        json_schema_extra = {
            "example": {
                "latence_moyenne_ms": 250.5,
                "latence_p95_ms": 450,
                "latence_p99_ms": 625,
                "taux_cache_hit": 0.75,
                "utilisation_ram_go": 1.2,
                "total_requetes": 1500,
                "satisfaction_moyenne": 4.2,
                "periode": "24h"
            }
        }
