"""
Module de génération de texte avec LLM pour Container 3.

Gère la génération de réponses avec LLM en format GGUF
via llama-cpp-python. Supporte CPU et GPU (CUDA).
"""

import logging
import os
from typing import Optional
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# Variables d'environnement
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "/app/modeles/gemma/gemma-2-2b-it-q4.gguf")
LLM_N_CTX = int(os.getenv("LLM_N_CTX", "4096"))
LLM_N_THREADS = int(os.getenv("LLM_N_THREADS", "4"))
LLM_N_BATCH = int(os.getenv("LLM_N_BATCH", "512"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "512"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
LLM_TOP_K = int(os.getenv("LLM_TOP_K", "40"))
LLM_REPETITION_PENALTY = float(os.getenv("LLM_REPETITION_PENALTY", "1.3"))
LLM_FREQUENCY_PENALTY = float(os.getenv("LLM_FREQUENCY_PENALTY", "0.5"))
LLM_PRESENCE_PENALTY = float(os.getenv("LLM_PRESENCE_PENALTY", "0.5"))
# GPU : 0 = CPU only, -1 = toutes les couches GPU, ou nombre specifique de couches
LLM_N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "0"))


# ============================================================================
# Classe GenerateurLLM
# ============================================================================

class GenerateurLLM:
    """Générateur de texte avec LLM (Gemma-2-2B)."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: Optional[int] = None,
        n_threads: Optional[int] = None,
        n_batch: Optional[int] = None,
        verbose: bool = False
    ):
        """Initialise le générateur LLM."""
        self.model_path = model_path or LLM_MODEL_PATH
        self.n_ctx = n_ctx or LLM_N_CTX
        self.n_threads = n_threads or LLM_N_THREADS
        self.n_batch = n_batch or LLM_N_BATCH
        self.verbose = verbose

        logger.info(f"Initialisation du générateur LLM...")
        logger.info(f"  Modèle: {self.model_path}")
        logger.info(f"  Contexte: {self.n_ctx} tokens")
        logger.info(f"  Threads: {self.n_threads}")
        logger.info(f"  Batch: {self.n_batch}")
        logger.info(f"  GPU Layers: {LLM_N_GPU_LAYERS} {'(GPU actif)' if LLM_N_GPU_LAYERS != 0 else '(CPU only)'}")

        try:
            from llama_cpp import Llama

            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"Modèle introuvable: {self.model_path}")

            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_batch=self.n_batch,
                n_gpu_layers=LLM_N_GPU_LAYERS,  # 0=CPU, >0=GPU
                verbose=self.verbose
            )

            mode = "GPU" if LLM_N_GPU_LAYERS != 0 else "CPU"
            logger.info(f"[OK] Modèle LLM chargé avec succès (mode {mode})")

        except Exception as e:
            logger.error(f"[ERREUR] Échec du chargement du modèle LLM: {e}")
            raise Exception(f"Erreur chargement LLM: {e}")

    def generer_reponse_chatbot(
        self,
        question: str,
        contexte: str,
        max_tokens: int = None
    ) -> str:
        """Génère une réponse de chatbot."""
        max_tokens = max_tokens or LLM_MAX_TOKENS

        # Format Instruct : [INST]...[/INST]
        # Prompt renforcé pour forcer le français et inclure les liens
        prompt = f"""<s>[INST] Tu es Mila, une assistante virtuelle francophone.

=== REGLE ABSOLUE ===
LANGUE OBLIGATOIRE: FRANCAIS SEULEMENT
- Tu dois repondre EXCLUSIVEMENT en francais
- AUCUN mot anglais n'est autorise dans ta reponse
- Si le contexte contient de l'anglais, tu le traduis en francais
- Tu es une assistante FRANCAISE qui parle FRANCAIS

=== REGLE CRITIQUE SUR LES LIENS - INTERDICTION STRICTE ===
ATTENTION: Cette regle est ABSOLUE et NON NEGOCIABLE.

SI le contexte contient des URLs:
- COPIE EXACTEMENT l'URL complete du contexte (caractere par caractere)
- Format: [texte descriptif](URL EXACTE DU CONTEXTE)
- Exemple: si contexte dit "https://dashboard.getailicia.com/signup"
  Tu ecris: [inscription](https://dashboard.getailicia.com/signup)

SI le contexte ne contient PAS d'URL:
- N'inclus AUCUN lien dans ta reponse
- Ne mentionne PAS de site web
- Reste factuel sans suggerer de liens

INTERDICTIONS ABSOLUES:
- N'invente JAMAIS d'URL (comme https://www.ailicia.io/)
- Ne devine JAMAIS une URL
- Ne raccourcis JAMAIS une URL
- N'ecris AUCUNE URL qui n'est pas dans le contexte
- Si tu n'es pas sur a 100% qu'une URL est dans le contexte, NE L'UTILISE PAS

=== INSTRUCTIONS ===
- Reponds en francais a partir du contexte fourni
- Utilise toutes les informations pertinentes du contexte
- Donne une reponse complete, claire et utile
- Reste naturelle et professionnelle

=== FORMATAGE ===
- Fait un formatage du texte professionnel.
- N'utilise PAS plus de 2 retours a la ligne consecutifs.
- Formate les listes proprement avec un retour simple entre chaque item.
- Evite les espaces vides ou retours a la ligne excessifs
=== CONTEXTE ===
{contexte}

=== QUESTION DE L'UTILISATEUR ===
{question}

=== TA REPONSE (EN FRANCAIS, LIENS UNIQUEMENT SI DANS LE CONTEXTE) ===
[/INST]"""

        try:
            output = self.model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=LLM_TEMPERATURE,
                top_p=LLM_TOP_P,
                top_k=LLM_TOP_K,
                repeat_penalty=LLM_REPETITION_PENALTY,
                frequency_penalty=LLM_FREQUENCY_PENALTY,
                presence_penalty=LLM_PRESENCE_PENALTY,
                stop=[
                    "</s>", "[INST]", "[/INST]",
                    "Question:", "User:", "Utilisateur:", 
                    "QUESTION:", "Answer:", "Response:",
                    " | ", " |", "| ",
                    "\n\n", "Analyse:", "Note:"
                ],
                echo=False
            )

            texte_genere = output['choices'][0]['text'].strip()
            return texte_genere

        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la génération: {e}")
            raise Exception(f"Erreur génération texte: {e}")


# ============================================================================
# Singleton global
# ============================================================================

_generateur_global: GenerateurLLM = None
_llm_disponible: bool = False


def obtenir_generateur(optionnel: bool = False) -> Optional[GenerateurLLM]:
    """
    Obtient l'instance globale du générateur (singleton).
    
    Args:
        optionnel: Si True, retourne None si LLM indisponible au lieu de lever une exception
    
    Returns:
        Instance de GenerateurLLM ou None si optionnel et indisponible
    """
    global _generateur_global, _llm_disponible

    if _generateur_global is None and not _llm_disponible:
        try:
            _generateur_global = GenerateurLLM()
            _llm_disponible = True
        except Exception as e:
            if optionnel:
                logger.warning(f"[ATTENTION] LLM non disponible (mode RAG seul): {e}")
                _llm_disponible = False
                return None
            raise

    return _generateur_global


def llm_est_disponible() -> bool:
    """Vérifie si le LLM est disponible."""
    return _llm_disponible


__all__ = ['GenerateurLLM', 'obtenir_generateur', 'llm_est_disponible']
