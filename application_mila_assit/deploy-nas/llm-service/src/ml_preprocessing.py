"""
Module de preprocessing ML pour Container 3 (LLM + FAISS Service).

Fournit :
- Stopwords français complets
- Nettoyage de texte avancé
- Calcul de métriques ML (F1, Precision, Recall)
- Tokenization française
"""

import logging
import re
from typing import List, Set, Dict, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# ============================================================================
# STOPWORDS FRANÇAIS COMPLETS
# ============================================================================

STOPWORDS_FRANCAIS: Set[str] = {
    # Articles définis et indéfinis
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d",
    
    # Prépositions
    "à", "a", "au", "aux", "avec", "chez", "dans", "en", "entre", "par",
    "pour", "sans", "sous", "sur", "vers", "contre", "depuis", "durant",
    "pendant", "jusque", "jusqu", "dès", "avant", "après", "derrière",
    "devant", "près", "loin", "autour", "hors", "malgré", "selon", "sauf",
    
    # Conjonctions
    "et", "ou", "mais", "donc", "or", "ni", "car", "que", "quand", "si",
    "lorsque", "puisque", "comme", "parce", "alors", "puis", "ensuite",
    "cependant", "pourtant", "toutefois", "néanmoins",
    
    # Pronoms personnels
    "je", "j", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "me", "m", "te", "t", "se", "s", "lui", "leur", "eux", "moi", "toi",
    "soi", "en", "y",
    
    # Pronoms démonstratifs
    "ce", "c", "ceci", "cela", "ça", "celui", "celle", "ceux", "celles",
    "ci", "là",
    
    # Pronoms relatifs et interrogatifs
    "qui", "que", "quoi", "dont", "où", "lequel", "laquelle", "lesquels",
    "lesquelles", "duquel", "auquel", "auxquels", "auxquelles",
    
    # Pronoms possessifs
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
    "notre", "nos", "votre", "vos", "leur", "leurs",
    
    # Verbes auxiliaires (formes courantes)
    "suis", "es", "est", "sommes", "êtes", "sont", "étais", "était",
    "étions", "étiez", "étaient", "serai", "seras", "sera", "serons",
    "serez", "seront", "serais", "serait", "serions", "seriez", "seraient",
    "sois", "soit", "soyons", "soyez", "soient", "fus", "fut", "fûmes",
    "fûtes", "furent", "été", "être",
    "ai", "as", "a", "avons", "avez", "ont", "avais", "avait", "avions",
    "aviez", "avaient", "aurai", "auras", "aura", "aurons", "aurez",
    "auront", "aurais", "aurait", "aurions", "auriez", "auraient",
    "aie", "aies", "ait", "ayons", "ayez", "aient", "eus", "eut", "eûmes",
    "eûtes", "eurent", "eu", "avoir",
    
    # Verbes modaux et courants
    "fait", "faire", "fais", "font", "vais", "vas", "va", "allons", "allez",
    "vont", "aller", "venir", "viens", "vient", "venons", "venez", "viennent",
    "pouvoir", "peux", "peut", "pouvons", "pouvez", "peuvent",
    "devoir", "dois", "doit", "devons", "devez", "doivent",
    "vouloir", "veux", "veut", "voulons", "voulez", "veulent",
    "savoir", "sais", "sait", "savons", "savez", "savent",
    "falloir", "faut", "dit", "dire", "dis", "disons", "disent",
    
    # Adverbes courants
    "ne", "n", "pas", "plus", "moins", "très", "trop", "assez", "bien",
    "mal", "mieux", "pire", "aussi", "encore", "toujours", "jamais",
    "souvent", "parfois", "quelquefois", "déjà", "bientôt", "maintenant",
    "ici", "là", "partout", "ailleurs", "dedans", "dehors", "dessus",
    "dessous", "oui", "non", "peut-être", "vraiment", "certainement",
    "probablement", "seulement", "surtout", "ensemble", "beaucoup",
    
    # Mots interrogatifs
    "comment", "pourquoi", "quand", "combien", "quel", "quelle", "quels",
    "quelles",
    
    # Autres mots très fréquents
    "tout", "tous", "toute", "toutes", "aucun", "aucune", "chaque",
    "même", "mêmes", "autre", "autres", "tel", "telle", "tels", "telles",
    "certain", "certaine", "certains", "certaines", "plusieurs",
    "quelque", "quelques", "peu", "beaucoup", "trop", "assez",
    "tant", "autant", "plus", "moins", "rien", "personne", "chose",
    "fois", "cas", "temps", "an", "année", "jour", "heure",
    
    # Nombres (optionnel)
    "zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
    "huit", "neuf", "dix", "premier", "première", "dernier", "dernière",
}


# ============================================================================
# FONCTIONS DE NETTOYAGE DE TEXTE
# ============================================================================

def nettoyer_texte(
    texte: str,
    supprimer_stopwords: bool = True,
    normaliser_accents: bool = False,
    conserver_nombres: bool = True
) -> str:
    """
    Nettoie et normalise un texte pour le traitement ML.
    
    Args:
        texte: Texte à nettoyer
        supprimer_stopwords: Retirer les mots vides français
        normaliser_accents: Convertir é→e, è→e, etc. (utile pour matching)
        conserver_nombres: Garder les nombres dans le texte
    
    Returns:
        Texte nettoyé et normalisé
    
    Example:
        >>> nettoyer_texte("Comment configurer le TTS sur AI_licia ?")
        'configurer tts ai_licia'
    """
    if not texte:
        return ""
    
    # Mise en minuscules
    texte = texte.lower()
    
    # Normaliser les accents si demandé
    if normaliser_accents:
        texte = _normaliser_accents(texte)
    
    # Supprimer la ponctuation (sauf underscore pour les noms techniques)
    if conserver_nombres:
        texte = re.sub(r'[^\w\s_]', ' ', texte)
    else:
        texte = re.sub(r'[^\w\s_]|[\d]', ' ', texte)
    
    # Tokenizer
    tokens = texte.split()
    
    # Supprimer les stopwords si demandé
    if supprimer_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS_FRANCAIS and len(t) > 1]
    
    # Reconstruire le texte
    texte_nettoye = ' '.join(tokens)
    
    # Normaliser les espaces multiples
    texte_nettoye = re.sub(r'\s+', ' ', texte_nettoye).strip()
    
    return texte_nettoye


def _normaliser_accents(texte: str) -> str:
    """Remplace les caractères accentués par leurs équivalents non-accentués."""
    remplacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'î': 'i', 'ï': 'i',
        'ç': 'c', 'ñ': 'n',
        'œ': 'oe', 'æ': 'ae'
    }
    for accent, normal in remplacements.items():
        texte = texte.replace(accent, normal)
    return texte


def tokenizer_francais(texte: str) -> List[str]:
    """
    Tokenize un texte français en conservant les mots significatifs.
    
    Args:
        texte: Texte à tokenizer
    
    Returns:
        Liste de tokens
    """
    texte_nettoye = nettoyer_texte(texte, supprimer_stopwords=True)
    return texte_nettoye.split() if texte_nettoye else []


# ============================================================================
# MÉTRIQUES ML (F1, Precision, Recall)
# ============================================================================

def calculer_metriques_retrieval(
    predictions: List[int],
    ground_truth: List[int],
    k: int = None
) -> Dict[str, float]:
    """
    Calcule les métriques de retrieval : Precision@K, Recall@K, F1@K.
    
    Args:
        predictions: Liste des IDs prédits (top-K results)
        ground_truth: Liste des IDs corrects (vérité terrain)
        k: Limiter à top-K (si None, utilise toutes les predictions)
    
    Returns:
        Dictionnaire avec precision, recall, f1
    
    Example:
        >>> metriques = calculer_metriques_retrieval(
        ...     predictions=[1, 5, 3, 7],
        ...     ground_truth=[1, 2, 3],
        ...     k=3
        ... )
        >>> print(metriques)
        {'precision': 0.667, 'recall': 0.667, 'f1': 0.667}
    """
    if k is not None:
        predictions = predictions[:k]
    
    predictions_set = set(predictions)
    ground_truth_set = set(ground_truth)
    
    if not predictions:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
    
    if not ground_truth:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
    
    # Vrais positifs = intersection des ensembles
    vrais_positifs = len(predictions_set & ground_truth_set)
    
    # Precision = TP / (TP + FP) = TP / len(predictions)
    precision = vrais_positifs / len(predictions) if predictions else 0.0
    
    # Recall = TP / (TP + FN) = TP / len(ground_truth)
    recall = vrais_positifs / len(ground_truth) if ground_truth else 0.0
    
    # F1 = 2 * (precision * recall) / (precision + recall)
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
    
    return {
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4)
    }


def calculer_mrr(predictions_ranked: List[List[int]], ground_truths: List[int]) -> float:
    """
    Calcule le Mean Reciprocal Rank (MRR).
    
    Args:
        predictions_ranked: Liste de listes de prédictions ordonnées
        ground_truths: Liste des réponses correctes correspondantes
    
    Returns:
        Score MRR (0 à 1)
    
    Example:
        >>> mrr = calculer_mrr(
        ...     predictions_ranked=[[3, 1, 2], [1, 2, 3]],
        ...     ground_truths=[1, 1]
        ... )
        >>> print(mrr)  # (1/2 + 1/1) / 2 = 0.75
        0.75
    """
    if len(predictions_ranked) != len(ground_truths):
        raise ValueError("Les listes doivent avoir la même longueur")
    
    if not predictions_ranked:
        return 0.0
    
    reciprocal_ranks = []
    
    for preds, gt in zip(predictions_ranked, ground_truths):
        if gt in preds:
            rank = preds.index(gt) + 1  # Rang commence à 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    
    return round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4)


def calculer_ndcg(predictions_ranked: List[int], relevances: Dict[int, float], k: int = None) -> float:
    """
    Calcule le Normalized Discounted Cumulative Gain (NDCG).
    
    Args:
        predictions_ranked: Liste d'IDs prédits (ordonnée par score décroissant)
        relevances: Dictionnaire {id: score_relevance} avec scores de pertinence
        k: Limiter à top-K
    
    Returns:
        Score NDCG (0 à 1)
    """
    import math
    
    if k is not None:
        predictions_ranked = predictions_ranked[:k]
    
    if not predictions_ranked or not relevances:
        return 0.0
    
    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(predictions_ranked):
        rel = relevances.get(doc_id, 0.0)
        dcg += rel / math.log2(i + 2)  # i+2 car log2(1) = 0
    
    # IDCG (DCG idéal avec docs triés par pertinence)
    sorted_rels = sorted(relevances.values(), reverse=True)
    if k is not None:
        sorted_rels = sorted_rels[:k]
    
    idcg = 0.0
    for i, rel in enumerate(sorted_rels):
        idcg += rel / math.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return round(dcg / idcg, 4)


# ============================================================================
# ANALYSE DE SIMILARITÉ TEXTUELLE
# ============================================================================

def jaccard_similarity(texte1: str, texte2: str) -> float:
    """
    Calcule la similarité de Jaccard entre deux textes.
    
    Args:
        texte1: Premier texte
        texte2: Deuxième texte
    
    Returns:
        Score de similarité (0 à 1)
    """
    tokens1 = set(tokenizer_francais(texte1))
    tokens2 = set(tokenizer_francais(texte2))
    
    if not tokens1 and not tokens2:
        return 1.0  # Deux textes vides sont identiques
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union)


def cosine_similarity_tokens(texte1: str, texte2: str) -> float:
    """
    Calcule la similarité cosinus basée sur les fréquences de tokens.
    (Bag of Words simple)
    
    Args:
        texte1: Premier texte
        texte2: Deuxième texte
    
    Returns:
        Score de similarité (0 à 1)
    """
    import math
    
    tokens1 = tokenizer_francais(texte1)
    tokens2 = tokenizer_francais(texte2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Compter les fréquences
    freq1 = Counter(tokens1)
    freq2 = Counter(tokens2)
    
    # Vocabulaire commun
    vocab = set(freq1.keys()) | set(freq2.keys())
    
    # Vecteurs
    vec1 = [freq1.get(t, 0) for t in vocab]
    vec2 = [freq2.get(t, 0) for t in vocab]
    
    # Produit scalaire
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Normes
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Stopwords
    'STOPWORDS_FRANCAIS',
    
    # Nettoyage
    'nettoyer_texte',
    'tokenizer_francais',
    
    # Métriques
    'calculer_metriques_retrieval',
    'calculer_mrr',
    'calculer_ndcg',
    
    # Similarité
    'jaccard_similarity',
    'cosine_similarity_tokens',
]

