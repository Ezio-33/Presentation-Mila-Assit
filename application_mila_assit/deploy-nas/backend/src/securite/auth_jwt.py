"""
Module de gestion de l'authentification JWT.

Fournit les fonctions pour créer et vérifier les tokens JWT,
ainsi que les dépendances FastAPI pour l'authentification.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.utilitaires.config import obtenir_config

# Configuration
config = obtenir_config()
SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures

# Context de hachage des mots de passe
contexte_mdp = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def creer_token_acces(donnees: Dict[str, Any], expire_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT d'accès.

    Args:
        donnees: Données à encoder dans le token
        expire_delta: Durée de validité du token (optionnel)

    Returns:
        Token JWT encodé
    """
    a_encoder = donnees.copy()

    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    a_encoder.update({"exp": expire})
    token_encode = jwt.encode(a_encoder, SECRET_KEY, algorithm=ALGORITHM)

    return token_encode


def verifier_token(token: str) -> Dict[str, Any]:
    """
    Vérifie et décode un token JWT.

    Args:
        token: Token JWT à vérifier

    Returns:
        Données décodées du token

    Raises:
        HTTPException: Si le token est invalide
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def verifier_token_admin(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Vérifie qu'un token JWT est valide et que l'utilisateur est admin.

    Args:
        token: Token JWT à vérifier

    Returns:
        Données de l'utilisateur (user_id, role)

    Raises:
        HTTPException: Si le token est invalide ou si l'utilisateur n'est pas admin
    """
    payload = verifier_token(token)

    role = payload.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : privilèges administrateur requis"
        )

    return payload


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """
    Hache un mot de passe avec bcrypt.

    Args:
        mot_de_passe: Mot de passe en clair

    Returns:
        Mot de passe haché
    """
    return contexte_mdp.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_mdp: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond à son hash.

    Args:
        mot_de_passe: Mot de passe en clair
        hash_mdp: Hash du mot de passe

    Returns:
        True si le mot de passe correspond, False sinon
    """
    return contexte_mdp.verify(mot_de_passe, hash_mdp)
