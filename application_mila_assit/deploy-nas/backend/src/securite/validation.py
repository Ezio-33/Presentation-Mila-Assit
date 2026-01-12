"""
Module de validation et sanitization des entrées utilisateur.

Fournit des fonctions pour valider et nettoyer les données
afin de prévenir les attaques par injection et le spam.
"""

import re
from typing import Optional
from uuid import UUID


def sanitize_input(texte: str) -> str:
    """
    Nettoie une chaîne de caractères en retirant les balises HTML
    et en limitant la longueur.

    Args:
        texte: Texte à nettoyer

    Returns:
        Texte nettoyé

    Raises:
        ValueError: Si le texte dépasse 5000 caractères
    """
    # Strip des espaces
    texte = texte.strip()

    # Vérifier la longueur maximale
    if len(texte) > 5000:
        raise ValueError("Le texte dépasse la longueur maximale autorisée de 5000 caractères")

    # Retirer les balises HTML
    texte_nettoye = re.sub(r'<[^>]+>', '', texte)

    return texte_nettoye


def valider_uuid(valeur: str) -> UUID:
    """
    Valide qu'une chaîne est un UUID valide.

    Args:
        valeur: Chaîne à valider

    Returns:
        UUID validé

    Raises:
        ValueError: Si la chaîne n'est pas un UUID valide
    """
    try:
        uuid_valide = UUID(valeur)
        return uuid_valide
    except ValueError as e:
        raise ValueError(f"UUID invalide : {valeur}") from e


def detecter_spam(texte: str) -> bool:
    """
    Détecte les patterns basiques de spam dans un texte.

    Args:
        texte: Texte à analyser

    Returns:
        True si du spam est détecté, False sinon
    """
    # Détecter plusieurs URLs (plus de 3)
    urls = re.findall(r'https?://[^\s]+', texte)
    if len(urls) > 3:
        return True

    # Détecter caractères répétés plus de 10 fois
    if re.search(r'(.)\1{10,}', texte):
        return True

    # Détecter majuscules excessives (plus de 70% du texte)
    if texte.isupper() and len(texte) > 20:
        return True

    return False


def valider_note(note: int) -> None:
    """
    Valide qu'une note est dans la plage autorisée (1-5).

    Args:
        note: Note à valider

    Raises:
        ValueError: Si la note n'est pas entre 1 et 5
    """
    if not 1 <= note <= 5:
        raise ValueError(f"La note doit être comprise entre 1 et 5, reçu : {note}")


def valider_longueur_texte(texte: Optional[str], max_length: int) -> None:
    """
    Valide qu'un texte ne dépasse pas une longueur maximale.

    Args:
        texte: Texte à valider (peut être None)
        max_length: Longueur maximale autorisée

    Raises:
        ValueError: Si le texte dépasse la longueur maximale
    """
    if texte is None:
        return

    texte_nettoye = texte.strip()
    if len(texte_nettoye) > max_length:
        raise ValueError(
            f"Le texte dépasse la longueur maximale de {max_length} caractères "
            f"(longueur actuelle : {len(texte_nettoye)})"
        )


def valider_question(question: str) -> str:
    """
    Valide et nettoie une question utilisateur.

    Args:
        question: Question à valider

    Returns:
        Question nettoyée et validée

    Raises:
        ValueError: Si la question est invalide
    """
    # Nettoyer la question
    question = sanitize_input(question)

    # Vérifier la longueur minimale
    if len(question) < 3:
        raise ValueError("La question doit contenir au moins 3 caractères")

    # Vérifier la longueur maximale
    if len(question) > 500:
        raise ValueError("La question ne peut pas dépasser 500 caractères")

    # Détecter le spam
    if detecter_spam(question):
        raise ValueError("La question contient du contenu suspect (spam détecté)")

    return question
