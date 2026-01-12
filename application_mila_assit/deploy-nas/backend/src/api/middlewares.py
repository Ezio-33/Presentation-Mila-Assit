"""
Module de middlewares FastAPI.

Fournit les middlewares pour le rate limiting, le logging des requêtes,
et la gestion des erreurs.
"""

import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.utilitaires.logger import obtenir_logger

# Logger
logger = obtenir_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def configurer_rate_limit_handler(app):
    """
    Configure le gestionnaire d'erreurs pour le rate limiting.

    Args:
        app: Instance FastAPI
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Gère les exceptions de rate limiting.

    Args:
        request: Requête HTTP
        exc: Exception de rate limiting

    Returns:
        Réponse JSON avec code 429
    """
    logger.warning(
        f"Rate limit dépassé pour {get_remote_address(request)} "
        f"sur {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Trop de requêtes",
            "detail": "Vous avez dépassé la limite de requêtes autorisées. Veuillez réessayer plus tard.",
            "retry_after": exc.headers.get("Retry-After", "60")
        },
        headers=exc.headers
    )


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware pour logger toutes les requêtes et leurs durées.

    Args:
        request: Requête HTTP
        call_next: Fonction suivante dans la chaîne de middlewares

    Returns:
        Réponse HTTP
    """
    start_time = time.time()

    # Informations sur la requête
    method = request.method
    url_path = request.url.path
    client_ip = get_remote_address(request)

    logger.info(f"→ {method} {url_path} depuis {client_ip}")

    # Traiter la requête
    try:
        response = await call_next(request)
        status_code = response.status_code

        # Calculer la durée
        duration_ms = (time.time() - start_time) * 1000

        # Logger le résultat
        logger.info(
            f"← {method} {url_path} {status_code} "
            f"({duration_ms:.2f}ms)"
        )

        # Ajouter la durée dans les headers
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        return response

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"✗ {method} {url_path} erreur après {duration_ms:.2f}ms : {str(e)}",
            exc_info=True
        )
        raise


async def cors_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware CORS personnalisé (fallback si CORSMiddleware ne suffit pas).

    Args:
        request: Requête HTTP
        call_next: Fonction suivante dans la chaîne de middlewares

    Returns:
        Réponse HTTP avec headers CORS
    """
    response = await call_next(request)

    # Ajouter les headers CORS
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


def configurer_middlewares(app):
    """
    Configure tous les middlewares de l'application.

    Args:
        app: Instance FastAPI
    """
    # Rate limiting
    configurer_rate_limit_handler(app)

    # Middleware de logging
    app.middleware("http")(logging_middleware)

    logger.info("Middlewares configurés : rate limiting, logging")
