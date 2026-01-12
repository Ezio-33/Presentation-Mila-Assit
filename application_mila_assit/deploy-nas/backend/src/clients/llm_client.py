"""
Client HTTP pour communiquer avec Container 3 (LLM + FAISS Service).

Le Container 2 (API Backend) délègue la recherche FAISS et génération LLM
au Container 3 via HTTP.
"""

import logging
import os
from typing import Dict, List, Any, Optional
import requests

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Variables d'environnement
LLM_SERVICE_HOST = os.getenv("LLM_SERVICE_HOST", "llm")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", "8001"))
LLM_SERVICE_TIMEOUT = int(os.getenv("LLM_SERVICE_TIMEOUT", "300"))  # 5 minutes pour génération LLM


# ============================================================================
# Classe LLMClient
# ============================================================================

class LLMClient:
    """
    Client HTTP pour communiquer avec Container 3 (LLM + FAISS Service).
    
    Architecture:
    Container 2 (API) → HTTP POST → Container 3 (LLM+FAISS) → Réponse générée
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        timeout: int = None
    ):
        """
        Initialise le client HTTP vers Container 3.

        Args:
            host: Hostname du Container 3 (défaut: llm-service)
            port: Port du Container 3 (défaut: 8001)
            timeout: Timeout requêtes HTTP (défaut: 30s)
        """
        self.host = host or LLM_SERVICE_HOST
        self.port = port or LLM_SERVICE_PORT
        self.timeout = timeout or LLM_SERVICE_TIMEOUT
        self.base_url = f"http://{self.host}:{self.port}"

        logger.info(f"LLMClient initialisé: {self.base_url}")

    def rechercher_et_generer(
        self,
        embedding: Optional[List[float]],
        question: str,
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Envoie une requête au Container 3 pour recherche FAISS + génération LLM.

        Args:
            embedding: Vecteur embedding (768 dimensions CamemBERT) ou None (Container 3 le calcule)
            question: Question originale de l'utilisateur
            k: Nombre de résultats FAISS (défaut: 3)

        Returns:
            Dict avec:
                - reponse: str (texte généré par LLM)
                - confiance: float (score top-1)
                - sources: List[int] (IDs base_connaissances)
                - temps_ms: int (temps traitement Container 3)

        Raises:
            Exception: Si la requête échoue
        """
        endpoint = f"{self.base_url}/search"

        payload = {
            "question": question,
            "k": k
        }
        
        # N'inclure l'embedding que s'il est fourni
        if embedding is not None:
            payload["embedding"] = embedding

        try:
            logger.debug(f"Envoi requête à Container 3: {endpoint}")
            embedding_info = f"{len(embedding)}d" if embedding else "auto"
            logger.debug(f"  Payload: question={question[:50]}..., k={k}, embedding={embedding_info}")

            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            data = response.json()

            logger.info(
                f"[OK] Reponse Container 3: confiance={data['confiance']:.3f}, "
                f"temps={data['temps_ms']}ms, sources={data['sources']}"
            )

            return {
                "reponse": data["reponse"],
                "confiance": data["confiance"],
                "sources": data["sources"],
                "temps_ms": data["temps_ms"]
            }

        except requests.exceptions.Timeout:
            logger.error(f"[ERREUR] Timeout connexion Container 3 ({self.timeout}s)")
            logger.error(f"   Vérifier: Container 3 est-il démarré ? docker ps | grep llm")
            raise Exception(f"Timeout Container 3 après {self.timeout}s")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"[ERREUR] Erreur connexion Container 3: {e}")
            logger.error(f"   Debug: host={self.host}, port={self.port}")
            logger.error(f"   Vérifier: 1) Container 3 running ? 2) Réseau Docker 3) Healthcheck")
            raise Exception(f"Container 3 inaccessible: {e}")

        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if response else "N/A"
            logger.error(f"[ERREUR] Erreur HTTP Container 3: {e} (status={status_code})")
            error_detail = response.json().get("detail", str(e)) if response else str(e)
            if status_code == 500:
                logger.error(f"   Container 3 crash interne - Vérifier logs: docker logs mila_llm_faiss")
            raise Exception(f"Erreur Container 3: {error_detail}")

        except Exception as e:
            logger.error(f"[ERREUR] Erreur inattendue Container 3: {e}")
            raise Exception(f"Erreur Container 3: {e}")

    def healthcheck(self) -> Dict[str, Any]:
        """
        Vérifie la santé du Container 3.

        Returns:
            Dict avec statut et composants

        Raises:
            Exception: Si le healthcheck échoue
        """
        endpoint = f"{self.base_url}/health"

        try:
            #response = requests.get(endpoint, timeout=5) test de timeout plus long pour les tests
            response = requests.get(endpoint, timeout=15)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"[ERREUR] Healthcheck Container 3 echoue: {e}")
            raise Exception(f"Container 3 unhealthy: {e}")

    def forcer_rebuild_faiss(self) -> Dict[str, Any]:
        """
        Force un rebuild de l'index FAISS (endpoint admin).

        Returns:
            Dict avec statistiques du rebuild

        Raises:
            Exception: Si le rebuild échoue
        """
        endpoint = f"{self.base_url}/faiss/rebuild"

        try:
            logger.info("[REBUILD] Demande rebuild FAISS au Container 3...")

            response = requests.post(endpoint, timeout=300)  # 5 min timeout
            response.raise_for_status()

            data = response.json()
            logger.info(f"[OK] Rebuild termine: {data}")

            return data

        except Exception as e:
            logger.error(f"[ERREUR] Erreur rebuild FAISS: {e}")
            raise Exception(f"Rebuild FAISS echoue: {e}")

    def obtenir_statut_autosync(self) -> Dict[str, Any]:
        """
        Obtient le statut de l'auto-sync FAISS.

        Returns:
            Dict avec statut auto-sync

        Raises:
            Exception: Si la requête échoue
        """
        endpoint = f"{self.base_url}/faiss/status"

        try:
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"[ERREUR] Erreur statut auto-sync: {e}")
            raise Exception(f"Statut auto-sync echoue: {e}")


# ============================================================================
# Singleton global
# ============================================================================

_client_global: LLMClient = None


def obtenir_llm_client() -> LLMClient:
    """
    Obtient l'instance globale du client LLM (singleton).

    Returns:
        Instance de LLMClient
    """
    global _client_global

    if _client_global is None:
        _client_global = LLMClient()

    return _client_global


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'LLMClient',
    'obtenir_llm_client'
]
