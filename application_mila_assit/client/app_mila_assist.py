#!/usr/bin/env python3
"""
Mila-Assist - Application Desktop Qt
Architecture 4 containers (Déc 2025)

Preprocessing Local (client-side):
1. Validation question (sanitize HTML, longueur 3-500 car, détection spam)
2. Détection multi-questions (3 stratégies: numérotations, connecteurs, multiples ?)
3. Nettoyage texte (normalisation casse, ponctuation, espaces)
4. Calcul embeddings local (CamemBERT FR, 768 dim)

Le client envoie la question validée + embedding vers l'API.
"""

import sys
import json
import uuid
import time
import re
import requests
import urllib3
from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox,
    QFrame, QScrollArea, QMessageBox, QDialog, QTextBrowser,
    QSpinBox, QSizePolicy, QProgressBar
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QRect, QPoint, QLocale, QTranslator, QLibraryInfo
)
from PyQt5.QtGui import (
    QFont, QTextCursor, QIcon, QPalette, QColor,
    QPainter, QPen, QBrush
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

ENVIRONMENTS = {
    "nas": {
        "name": "🌐 NAS Mila-Assist",
#        "url": "http://ezi0.synology.me:10443/api/v1",
        "url": "http://185.246.86.162:9000/api/v1",
        "description": "Environnement de production",
        "require_api_key": True,
        "api_key": "-ZuygDkEaeG)LfPy4bzetDU8cg!k1Cl2@6A#40+^B6cWiwM@",
        "use_mistral": False,
        "color": "#2196F3"
    },
    "mistral": {
        "name": "🤖 API Mistral AI",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "description": "API Mistral Large",
        "require_api_key": True,
        "api_key": "nB1iPJNT5B075wCGkAw4TYzfZTakZzdE",
        "use_mistral": True,
        "color": "#9C27B0"
    }
}

COLORS = {
    "primary": "#5B4FDE",
    "primary_light": "#7C6FE8",
    "primary_dark": "#4238B8",
    "secondary": "#00D9FF",
    "bg_main": "#F8F9FA",
    "bg_dark": "#1A1A2E",
    "text_primary": "#2C3E50",
    "text_secondary": "#7F8C8D",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "user_bubble": "#E3F2FD",
    "bot_bubble": "#F3E5F5",
}

# ============================================================================
# STYLESHEET AMÉLIORÉ
# ============================================================================

STYLESHEET = f"""
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {COLORS['bg_main']},
                                stop:1 #FFFFFF);
}}

QWidget {{
    font-family: 'Segoe UI', 'SF Pro Display', 'Arial', sans-serif;
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QLabel#title {{
    font-size: 28px;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 10px;
}}

QLabel#subtitle {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
    padding: 5px;
    font-weight: 500;
}}

QLabel#status {{
    font-size: 11px;
    padding: 8px 16px;
    border-radius: 16px;
    background-color: {COLORS['success']};
    color: white;
    font-weight: bold;
}}

QLabel#loading {{
    font-size: 16px;
    color: white;
    padding: 12px;
    font-weight: bold;
}}

QComboBox {{
    padding: 12px 20px;
    border: 2px solid {COLORS['primary_light']};
    border-radius: 12px;
    background-color: white;
    font-size: 14px;
    min-width: 220px;
    font-weight: 500;
}}

QComboBox:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['bg_main']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 15px;
}}

QComboBox QAbstractItemView {{
    border: 2px solid {COLORS['primary_light']};
    border-radius: 12px;
    background-color: white;
    selection-background-color: {COLORS['primary_light']};
    padding: 8px;
    outline: none;
}}

QTextBrowser {{
    background-color: white;
    border: 2px solid {COLORS['primary_light']};
    border-radius: 16px;
    padding: 20px;
    font-size: 14px;
}}

QLineEdit {{
    padding: 14px 20px;
    border: 2px solid {COLORS['primary_light']};
    border-radius: 28px;
    background-color: white;
    font-size: 15px;
    selection-background-color: {COLORS['primary_light']};
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['bg_main']};
    border-width: 3px;
}}

QLineEdit:disabled {{
    background-color: #F0F0F0;
    color: {COLORS['text_secondary']};
    border-color: #E0E0E0;
}}

QLineEdit::placeholder {{
    color: {COLORS['text_secondary']};
    font-style: italic;
}}

QPushButton {{
    padding: 14px 35px;
    border: none;
    border-radius: 28px;
    background-color: {COLORS['primary']};
    color: white;
    font-size: 15px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_light']};
    padding: 15px 34px 13px 36px;
}}

QPushButton:disabled {{
    background-color: #BDBDBD;
    color: #757575;
}}

QPushButton#secondary {{
    background-color: {COLORS['secondary']};
}}

QPushButton#secondary:hover {{
    background-color: #00B8D4;
}}

QPushButton#feedback {{
    padding: 10px 24px;
    font-size: 13px;
    background-color: {COLORS['warning']};
    border-radius: 20px;
}}

QPushButton#feedback:hover {{
    background-color: #F57C00;
}}

QFrame#card {{
    background-color: white;
    border: 2px solid #E8E8E8;
    border-radius: 16px;
    padding: 20px;
}}

QFrame#loading_frame {{
    background-color: {COLORS['primary']};
    border: 3px solid {COLORS['primary_dark']};
    border-radius: 16px;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_main']};
    width: 12px;
    border-radius: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['primary_light']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['primary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QSpinBox {{
    padding: 10px;
    border: 2px solid {COLORS['primary_light']};
    border-radius: 10px;
    background-color: white;
    font-size: 14px;
}}

QSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QTextEdit {{
    border: 2px solid {COLORS['primary_light']};
    border-radius: 12px;
    padding: 12px;
    background-color: white;
    font-size: 14px;
}}

QTextEdit:focus {{
    border-color: {COLORS['primary']};
    border-width: 3px;
}}
"""

# ============================================================================
# WIDGET SPINNER ANIMÉ
# ============================================================================

class SpinnerWidget(QWidget):
    """Widget spinner animé pour indiquer le chargement"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setMinimumSize(50, 50)
        self.setMaximumSize(50, 50)

    def start(self):
        """Démarrer l'animation"""
        self.timer.start(50)
        self.show()

    def stop(self):
        """Arrêter l'animation"""
        self.timer.stop()
        self.hide()

    def rotate(self):
        """Rotation du spinner"""
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        """Dessiner le spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 5

        pen = QPen(QColor("white"))
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        for i in range(8):
            angle_offset = self.angle + i * 45
            alpha = 255 - (i * 30)
            pen.setColor(QColor(255, 255, 255, alpha))
            painter.setPen(pen)

            start_angle = angle_offset * 16
            span_angle = 30 * 16

            painter.drawArc(
                center.x() - radius,
                center.y() - radius,
                radius * 2,
                radius * 2,
                start_angle,
                span_angle
            )

# ============================================================================
# PREPROCESSING LOCAL (Architecture 4 containers - 9 Déc 2025)
# ============================================================================

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
    texte = texte.strip()

    if len(texte) > 5000:
        raise ValueError("Le texte dépasse la longueur maximale autorisée de 5000 caractères")

    # Retirer les balises HTML
    texte_nettoye = re.sub(r'<[^>]+>', '', texte)

    return texte_nettoye


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


def split_questions(text: str) -> List[str]:
    """
    Détecte et sépare plusieurs questions dans un texte.

    Utilise 3 stratégies:
    1. Numérotations (1., 2., -, etc.)
    2. Connecteurs + mots interrogatifs ("et comment", "ou quel", etc.)
    3. Points d'interrogation multiples

    Args:
        text: Texte potentiellement multi-questions

    Returns:
        Liste de questions (1+ éléments)
    """
    questions = []
    text = text.strip()

    if not text:
        return [text]

    # Étape 1 : Détecter numérotations explicites (1., 2., -, etc.)
    lines = text.split('\n')
    numbered_questions = []
    current_question = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Détecter numérotation
        if re.match(r'^\d+[\.\)]\s+', line) or re.match(r'^[\-\*\•]\s+', line):
            # Sauvegarder la question précédente
            if current_question:
                q = ' '.join(current_question).strip()
                if q:
                    numbered_questions.append(q)
                current_question = []

            # Nettoyer et commencer nouvelle question
            cleaned = re.sub(r'^\d+[\.\)]\s+', '', line)
            cleaned = re.sub(r'^[\-\*\•]\s+', '', cleaned)
            current_question.append(cleaned)
        else:
            current_question.append(line)

    # Ajouter la dernière question
    if current_question:
        q = ' '.join(current_question).strip()
        if q:
            numbered_questions.append(q)

    if len(numbered_questions) > 1:
        return numbered_questions

    # Étape 2 : Détecter "et/ou" + mot interrogatif
    interrogative_words_list = [
        'qui', 'que', 'quoi', 'quand', 'où', 'comment', 'pourquoi',
        'quel', 'quelle', 'quels', 'quelles', 'combien', 'est-ce que',
        'est ce que', 'es-ce que', 'es ce que'
    ]

    text_lower = text.lower()
    split_patterns = []

    # Chercher tous les patterns "et comment", "ou quel", etc.
    for word in interrogative_words_list:
        for connector in [' et ', ' ou ', ', ']:
            pattern = connector + word
            if pattern in text_lower:
                pos = text_lower.find(pattern)
                if pos > 0:
                    split_patterns.append((pos, len(connector), word))

    # Trier par position
    split_patterns.sort(key=lambda x: x[0])

    if split_patterns:
        # Découper aux positions trouvées
        last_pos = 0
        for pos, connector_len, word in split_patterns:
            # Extraire la partie avant
            part = text[last_pos:pos].strip()
            if part and not part.endswith('?'):
                part += ' ?'
            if part:
                questions.append(part)
            # Position suivante
            last_pos = pos + connector_len

        # Ajouter la dernière partie
        last_part = text[last_pos:].strip()
        if last_part:
            if not last_part.endswith('?'):
                last_part += ' ?'
            questions.append(last_part)

        # Vérifier si certaines questions contiennent encore plusieurs ?
        if len(questions) > 1:
            interrogative_patterns = [
                r'\bqui\b', r'\bque\b', r'\bquoi\b', r'\bquand\b', r'\boù\b',
                r'\bcomment\b', r'\bpourquoi\b', r'\bquel\b', r'\bquelle\b',
                r'\bquels\b', r'\bquelles\b', r'\bcombien\b', r'\best-ce que\b',
                r'\best ce que\b', r'\bes-ce que\b', r'\bes ce que\b'
            ]

            questions_finales = []
            for q in questions:
                if q.count('?') > 1:
                    # Cette question contient plusieurs ? -> la découper
                    sub_parts = q.split('?')
                    for sub_part in sub_parts:
                        sub_part = sub_part.strip()
                        if not sub_part:
                            continue
                        # Vérifier si c'est une vraie question
                        is_question = any(re.search(pattern, sub_part.lower()) for pattern in interrogative_patterns)
                        if is_question or len(sub_part) > 5:
                            questions_finales.append(sub_part + ' ?')
                else:
                    questions_finales.append(q)

            if len(questions_finales) > len(questions):
                return questions_finales

            return questions

    # Étape 3 : Détecter par points d'interrogation multiples
    questions = []
    if '?' in text:
        question_count = text.count('?')

        if question_count > 1:
            interrogative_patterns = [
                r'\bqui\b', r'\bque\b', r'\bquoi\b', r'\bquand\b', r'\boù\b',
                r'\bcomment\b', r'\bpourquoi\b', r'\bquel\b', r'\bquelle\b',
                r'\bquels\b', r'\bquelles\b', r'\bcombien\b', r'\best-ce que\b',
                r'\best ce que\b', r'\bes-ce que\b', r'\bes ce que\b'
            ]

            parts = text.split('?')
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Vérifier si c'est une vraie question
                is_question = any(re.search(pattern, part.lower()) for pattern in interrogative_patterns)

                if is_question or len(part) > 5:
                    questions.append(part + ' ?')

            if len(questions) > 1:
                return questions

    # Aucune méthode n'a détecté plusieurs questions
    return [text]


def est_multi_questions(text: str) -> bool:
    """
    Vérifie rapidement si un texte contient plusieurs questions.

    Args:
        text: Texte à analyser

    Returns:
        True si plusieurs questions détectées
    """
    return len(split_questions(text)) > 1


def nettoyer_texte(texte: str) -> str:
    """
    Nettoyage léger du texte pour améliorer la qualité des embeddings.
    Version simplifiée sans spaCy pour le client.

    Args:
        texte: Texte à nettoyer

    Returns:
        Texte nettoyé
    """
    if not texte:
        return ""

    # Normalisation casse
    texte = texte.lower()

    # Supprimer seulement la ponctuation excessive
    texte = re.sub(r'[!?.;:,\'"(){}\[\]]', ' ', texte)

    # Normaliser espaces multiples
    texte = re.sub(r'\s+', ' ', texte).strip()

    return texte


# ============================================================================
# EMBEDDING CALCULATOR (Architecture 4 containers - 9 Déc 2025)
# ============================================================================

class EmbeddingCalculator:
    """
    Calcule les embeddings localement (Architecture 4 containers).
    Le client envoie l'embedding au serveur qui le délègue à Container 3.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            print("🤖 Chargement du modèle d'embeddings CamemBERT FR (première utilisation)...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('antoinelouis/biencoder-camembert-base-mmarcoFR')
                print("[OK] Modèle d'embeddings chargé (768 dimensions)")
            except Exception as e:
                print(f"[ERREUR] Erreur chargement modèle : {e}")
                self._model = None

    def calculate(self, text: str) -> Optional[List[float]]:
        """Calcule l'embedding pour un texte."""
        if self._model is None:
            return None

        try:
            import numpy as np
            embedding = self._model.encode([text], normalize_embeddings=True)[0]
            return embedding.tolist()
        except Exception as e:
            print(f"[ERREUR] Erreur calcul embedding : {e}")
            return None

# ============================================================================
# THREAD DE REQUÊTE
# ============================================================================

class RequestThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, client, question):
        super().__init__()
        self.client = client
        self.question = question

    def run(self):
        try:
            # Architecture 4 containers: Le calcul d'embedding se fait en arrière-plan
            # Le message "Mila réfléchit à votre question..." reste affiché
            result = self.client.ask_question(self.question)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ============================================================================
# CLIENT API
# ============================================================================

class MilaAPIClient:
    def __init__(self, environment: str = "nas"):
        self.environment = environment
        self.session_id = str(uuid.uuid4())
        self.base_url = ENVIRONMENTS[environment]["url"]
        # Architecture 4 containers: Calculateur d'embeddings local
        self.embedding_calculator = EmbeddingCalculator()

    def switch_environment(self, environment: str):
        if environment in ENVIRONMENTS:
            self.environment = environment
            self.base_url = ENVIRONMENTS[environment]["url"]
            self.session_id = str(uuid.uuid4())
            return True
        return False

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        env_config = ENVIRONMENTS[self.environment]
        if env_config.get("require_api_key"):
            headers["X-API-Key"] = env_config["api_key"]
        return headers

    def check_health(self) -> tuple[bool, str]:
        try:
            env_config = ENVIRONMENTS[self.environment]
            if env_config.get("use_mistral"):
                return True, "En ligne"

            verify_ssl = not (self.environment == "nas")
            response = requests.get(
                f"{self.base_url}/sante",
                headers=self._get_headers(),
                timeout=5,
                verify=verify_ssl
            )
            if response.status_code == 200:
                return True, "Opérationnel"
            return False, f"Erreur {response.status_code}"
        except Exception as e:
            return False, f"Hors ligne"

    def _format_error_message(self, error: Exception, environment: str) -> str:
        """Formate un message d'erreur convivial en français"""
        error_str = str(error)

        # Timeout
        if "timed out" in error_str.lower() or "timeout" in error_str.lower():
            if "Read timed out" in error_str:
                return f"⏱ La connexion au serveur {ENVIRONMENTS[environment]['name']} a expiré après 6 minutes. Le serveur met trop de temps à répondre. Veuillez réessayer ou changer d'environnement."
            return f"⏱ Le délai d'attente est dépassé. Le serveur {ENVIRONMENTS[environment]['name']} ne répond pas."

        # Connexion refusée
        if "Connection refused" in error_str or "ConnectionRefusedError" in error_str:
            return f"🔌 Impossible de se connecter au serveur {ENVIRONMENTS[environment]['name']}. Vérifiez que le serveur est démarré."

        # Erreur réseau
        if "ConnectionError" in error_str or "Network" in error_str:
            return f"🌐 Erreur de connexion réseau. Vérifiez votre connexion Internet et réessayez."

        # Serveur introuvable
        if "Name or service not known" in error_str or "getaddrinfo failed" in error_str:
            return f"🔍 Le serveur {ENVIRONMENTS[environment]['name']} est introuvable. Vérifiez l'adresse réseau."

        # Par défaut, message générique
        return f"[ERREUR] Une erreur s'est produite lors de la communication avec {ENVIRONMENTS[environment]['name']}. Veuillez réessayer."

    def ask_question(self, question: str) -> Dict[str, Any]:
        start_time = time.time()
        env_config = ENVIRONMENTS[self.environment]

        try:
            # ÉTAPE 1: Validation de la question
            try:
                question_validee = valider_question(question)
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"[ERREUR] Question invalide : {str(e)}",
                    "temps_reponse": time.time() - start_time
                }

            # ÉTAPE 2: Détection multi-questions (info seulement)
            questions_detectees = split_questions(question_validee)
            if len(questions_detectees) > 1:
                # Informer dans la console mais envoyer la question complète au serveur
                # Le LLM gérera les multi-questions
                print(f"[INFO] Détection de {len(questions_detectees)} questions multiples.")
                print(f"   Questions détectées : {questions_detectees}")
                # Ne PAS modifier question_validee - envoyer la question complète

            # ÉTAPE 3: Suite du traitement normal
            if env_config.get("use_mistral"):
                return self._ask_mistral(question_validee, start_time)
            else:
                return self._ask_local_api(question_validee, start_time)
        except Exception as e:
            return {
                "success": False,
                "error": self._format_error_message(e, self.environment),
                "temps_reponse": time.time() - start_time
            }

    def _ask_local_api(self, question: str, start_time: float) -> Dict[str, Any]:
        verify_ssl = not (self.environment == "nas")

        # ÉTAPE 3: Nettoyage du texte pour améliorer la qualité de l'embedding
        texte_nettoye = nettoyer_texte(question)

        # Architecture 4 containers: Calculer l'embedding sur le texte nettoyé
        embedding = self.embedding_calculator.calculate(texte_nettoye)
        if embedding is None:
            return {
                "success": False,
                "error": "Impossible de calculer l'embedding. Vérifiez que sentence-transformers est installé.",
                "temps_reponse": time.time() - start_time
            }

        payload = {
            "id_session": self.session_id,
            "question": question,  # Envoyer le texte original (validé)
            "embedding": embedding  # Embedding calculé sur texte nettoyé
        }

        response = requests.post(
            f"{self.base_url}/search",
            headers=self._get_headers(),
            json=payload,
            timeout=360,
            verify=verify_ssl
        )

        temps_reponse = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "reponse": data.get("reponse", ""),
                "confiance": data.get("confiance", 0),
                "sources": data.get("sources", []),
                "temps_reponse": temps_reponse,
                "id_conversation": data.get("id_conversation")
            }
        else:
            return {
                "success": False,
                "error": f"Erreur HTTP {response.status_code}: {response.text[:200]}",
                "temps_reponse": temps_reponse
            }

    def _ask_mistral(self, question: str, start_time: float) -> Dict[str, Any]:
        # ÉTAPE 3: Nettoyage du texte pour améliorer la qualité de l'embedding
        texte_nettoye = nettoyer_texte(question)

        # Architecture 4 containers: Calculer l'embedding sur le texte nettoyé
        embedding = self.embedding_calculator.calculate(texte_nettoye)

        try:
            # Appel API NAS pour récupérer le contexte (avec embedding)
            payload_nas = {
                "id_session": self.session_id,
                "question": question
            }
            # Ajouter l'embedding si disponible
            if embedding:
                payload_nas["embedding"] = embedding

            nas_response = requests.post(
                f"{ENVIRONMENTS['nas']['url']}/search",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": ENVIRONMENTS['nas']['api_key']
                },
                json=payload_nas,
                timeout=30,
                verify=False
            )
            contexte = nas_response.json().get("reponse", "Aucun contexte disponible")
            sources = nas_response.json().get("sources", [])
            id_conv = nas_response.json().get("id_conversation")
        except Exception as e:
            print(f"[ATTENTION] Erreur récupération contexte NAS: {e}")
            contexte = "Aucun contexte disponible."
            sources = []
            id_conv = None

        env_config = ENVIRONMENTS[self.environment]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env_config['api_key']}"
        }

        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es Mila, assistante AI_licia. Réponds toujours en français de manière naturelle."
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nBase de connaissances:\n{contexte}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }

        response = requests.post(
            env_config["url"],
            headers=headers,
            json=payload,
            timeout=30
        )

        temps_reponse = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            reponse = data["choices"][0]["message"]["content"]
            return {
                "success": True,
                "reponse": reponse,
                "confiance": 0.75,
                "sources": sources,
                "temps_reponse": temps_reponse,
                "id_conversation": id_conv
            }
        else:
            return {
                "success": False,
                "error": f"Erreur Mistral {response.status_code}",
                "temps_reponse": temps_reponse
            }

    def send_feedback(self, id_conversation: int, note: int, commentaire: str, suggestion: str = "") -> bool:
        try:
            verify_ssl = not (self.environment == "nas")
            payload = {
                "id_conversation": id_conversation,
                "note": note,
                "commentaire": commentaire
            }
            if suggestion:
                payload["suggestion_reponse"] = suggestion

            response = requests.post(
                f"{self.base_url}/retour-utilisateur",
                headers=self._get_headers(),
                json=payload,
                timeout=10,
                verify=verify_ssl
            )
            return response.status_code == 201
        except:
            return False

# ============================================================================
# DIALOGUE FEEDBACK
# ============================================================================

class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Donner un retour Donner un Retour")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setStyleSheet(STYLESHEET)
        self.feedback_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Cette réponse vous a-t-elle aidé ?")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        layout.addWidget(title)

        note_layout = QHBoxLayout()
        note_label = QLabel("Note (1-5) :")
        note_label.setStyleSheet("font-size: 14px;")
        self.note_spin = QSpinBox()
        self.note_spin.setRange(1, 5)
        self.note_spin.setValue(3)
        self.note_spin.setMinimumWidth(100)
        note_layout.addWidget(note_label)
        note_layout.addWidget(self.note_spin)
        note_layout.addStretch()
        layout.addLayout(note_layout)

        comment_label = QLabel("Commentaire (optionnel) :")
        comment_label.setStyleSheet("font-size: 14px;")
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Expliquez ce qui n'a pas fonctionné...")
        self.comment_edit.setMaximumHeight(100)
        layout.addWidget(comment_label)
        layout.addWidget(self.comment_edit)

        suggestion_label = QLabel("Meilleure réponse suggérée (optionnel) :")
        suggestion_label.setStyleSheet("font-size: 14px;")
        self.suggestion_edit = QTextEdit()
        self.suggestion_edit.setPlaceholderText("Si vous connaissez la bonne réponse...")
        self.suggestion_edit.setMaximumHeight(100)
        layout.addWidget(suggestion_label)
        layout.addWidget(self.suggestion_edit)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        send_btn = QPushButton("Envoyer")
        send_btn.setMinimumWidth(120)
        send_btn.clicked.connect(self.accept)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(send_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def get_feedback(self):
        return {
            "note": self.note_spin.value(),
            "commentaire": self.comment_edit.toPlainText().strip(),
            "suggestion": self.suggestion_edit.toPlainText().strip()
        }

# ============================================================================
# FENÊTRE PRINCIPALE
# ============================================================================

class MilaAssistApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = MilaAPIClient("nas")
        self.current_conversation_id = None
        self.is_processing = False
        self.init_ui()
        self.check_api_status()

    def init_ui(self):
        self.setWindowTitle("Mila-Assist - Assistant AI_licia Pro")
        self.setMinimumSize(1000, 850)
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(25, 25, 25, 25)

        header = self.create_header()
        main_layout.addWidget(header)

        # NOUVEAU : Zone de chargement EN HAUT (pas dans le chat)
        self.loading_frame = QFrame()
        self.loading_frame.setObjectName("loading_frame")
        self.loading_frame.setVisible(False)
        self.loading_frame.setFixedHeight(80)
        loading_layout = QHBoxLayout(self.loading_frame)
        loading_layout.setContentsMargins(25, 15, 25, 15)
        loading_layout.setSpacing(15)

        self.spinner = SpinnerWidget()
        self.spinner.setFixedSize(50, 50)
        loading_layout.addWidget(self.spinner, alignment=Qt.AlignVCenter)

        self.loading_label = QLabel("🤖 Mila réfléchit à votre question...")
        self.loading_label.setObjectName("loading")
        self.loading_label.setWordWrap(True)
        self.loading_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        loading_layout.addWidget(self.loading_label, alignment=Qt.AlignVCenter)
        loading_layout.addStretch()

        main_layout.addWidget(self.loading_frame)

        # Zone de chat
        chat_frame = QFrame()
        chat_frame.setObjectName("card")
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setSpacing(15)

        chat_header_layout = QHBoxLayout()
        chat_title = QLabel("💬 Conversation")
        chat_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        chat_header_layout.addWidget(chat_title)
        chat_header_layout.addStretch()

        # Bouton pour effacer la conversation
        self.clear_button = QPushButton("Effacer Effacer")
        self.clear_button.setMaximumWidth(120)
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                font-size: 12px;
                background-color: {COLORS['text_secondary']};
                border-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
            }}
        """)
        self.clear_button.clicked.connect(self.clear_conversation)
        chat_header_layout.addWidget(self.clear_button)

        chat_layout.addLayout(chat_header_layout)

        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)  # Permettre les liens cliquables
        self.chat_display.setMinimumHeight(350)
        self.chat_display.setReadOnly(True)  # Empêcher l'édition
        self.chat_display.setWordWrapMode(True)  # Retour à la ligne automatique
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        chat_layout.addWidget(self.chat_display)

        main_layout.addWidget(chat_frame)

        # Zone de saisie + bouton feedback
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(10)

        # Bouton feedback persistant
        self.feedback_button = QPushButton("Donner un retour Donner un retour sur la dernière réponse")
        self.feedback_button.setObjectName("feedback")
        self.feedback_button.setVisible(False)
        self.feedback_button.clicked.connect(self.show_feedback_dialog)
        input_layout.addWidget(self.feedback_button)

        # Champ de saisie
        send_layout = QHBoxLayout()
        send_layout.setSpacing(15)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Posez votre question ici...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setMinimumHeight(50)
        send_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Envoyer")
        self.send_button.setMinimumWidth(140)
        self.send_button.setMinimumHeight(50)
        self.send_button.clicked.connect(self.send_message)
        send_layout.addWidget(self.send_button)

        # Bouton d'annulation (caché par défaut)
        self.cancel_button = QPushButton("⏹ Annuler")
        self.cancel_button.setMinimumWidth(140)
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_request)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
            }}
        """)
        send_layout.addWidget(self.cancel_button)

        input_layout.addLayout(send_layout)
        main_layout.addWidget(input_frame)

        self.display_welcome_message()

    def create_header(self):
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(15)

        title_layout = QHBoxLayout()
        title = QLabel("Mila-Assist")
        title.setObjectName("title")
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.status_label = QLabel("🟢 En ligne")
        self.status_label.setObjectName("status")
        title_layout.addWidget(self.status_label)

        header_layout.addLayout(title_layout)

        controls_layout = QHBoxLayout()

        subtitle = QLabel("Votre assistant AI_licia intelligent")
        subtitle.setObjectName("subtitle")
        controls_layout.addWidget(subtitle)
        controls_layout.addStretch()

        env_label = QLabel("Environnement :")
        env_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        controls_layout.addWidget(env_label)

        self.env_combo = QComboBox()
        for key, env in ENVIRONMENTS.items():
            self.env_combo.addItem(env["name"], key)
        self.env_combo.currentIndexChanged.connect(self.on_environment_changed)
        controls_layout.addWidget(self.env_combo)

        header_layout.addLayout(controls_layout)

        return header

    def display_welcome_message(self):
        welcome_html = f"""
        <div style="padding: 30px; text-align: center;">
            <h1 style="color: {COLORS['primary']}; font-size: 32px; margin-bottom: 15px;">
                👋 Bienvenue dans Mila-Assist !
            </h1>
            <p style="color: {COLORS['text_secondary']}; font-size: 16px; line-height: 1.6;">
                Je suis <strong>Mila</strong>, votre assistante virtuelle pour AI_licia.<br>
                Posez-moi vos questions sur AI_licia, la configuration, les commandes, etc.
            </p>
            <div style="margin-top: 25px; padding: 20px; background-color: {COLORS['bot_bubble']};
                        border-radius: 12px; display: inline-block;">
                <p style="color: {COLORS['text_primary']}; font-size: 14px; margin: 0;">
                    💡 <em>Astuce : Vous pouvez poser plusieurs questions à la fois !</em>
                </p>
            </div>
        </div>
        """
        self.chat_display.setHtml(welcome_html)

    def check_api_status(self):
        is_online, message = self.client.check_health()
        if is_online:
            self.status_label.setText(f"🟢 {message}")
            self.status_label.setStyleSheet(f"background-color: {COLORS['success']};")
        else:
            self.status_label.setText(f"🔴 {message}")
            self.status_label.setStyleSheet(f"background-color: {COLORS['error']};")

    def on_environment_changed(self, index):
        env_key = self.env_combo.currentData()
        self.client.switch_environment(env_key)
        self.check_api_status()

        env_name = ENVIRONMENTS[env_key]["name"]
        self.append_system_message(f"Environnement changé : {env_name}")

    def send_message(self):
        question = self.input_field.text().strip()
        if not question or self.is_processing:
            return

        self.is_processing = True

        self.input_field.setEnabled(False)

        # Cacher le bouton Envoyer, afficher le bouton Annuler
        self.send_button.setVisible(False)
        self.cancel_button.setVisible(True)

        # Masquer le bouton feedback pendant le traitement
        self.feedback_button.setVisible(False)

        # Afficher la zone de chargement
        self.loading_frame.setVisible(True)
        self.spinner.start()

        self.append_user_message(question)
        self.input_field.clear()

        self.request_thread = RequestThread(self.client, question)
        self.request_thread.finished.connect(self.on_response_received)
        self.request_thread.error.connect(self.on_response_error)
        self.request_thread.progress.connect(self.update_loading_status)
        self.request_thread.start()

    def cancel_request(self):
        """Annule la requête en cours"""
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.terminate()
            self.request_thread.wait()

            self.spinner.stop()
            self.loading_frame.setVisible(False)

            self.input_field.setEnabled(True)
            self.send_button.setVisible(True)
            self.send_button.setEnabled(True)
            self.cancel_button.setVisible(False)
            self.input_field.setFocus()

            self.is_processing = False

            self.append_system_message("🛑 Requête annulée par l'utilisateur")

    def update_loading_status(self, message):
        self.loading_label.setText(f"🤖 {message}")

    def on_response_received(self, result):
        self.spinner.stop()
        self.loading_frame.setVisible(False)

        self.input_field.setEnabled(True)
        self.send_button.setVisible(True)
        self.send_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.input_field.setFocus()

        self.is_processing = False

        if result.get("success"):
            reponse = result.get("reponse", "")
            confiance = result.get("confiance", 0) * 100
            temps = result.get("temps_reponse", 0)
            sources = result.get("sources", [])
            self.current_conversation_id = result.get("id_conversation")

            self.append_bot_message(
                reponse,
                confiance=confiance,
                temps=temps,
                sources=sources
            )

            # Afficher le bouton feedback
            if self.current_conversation_id:
                self.feedback_button.setVisible(True)
        else:
            # Afficher l'erreur formatée (sans métadonnées)
            error = result.get("error", "Une erreur inconnue s'est produite.")
            self.append_error_message(error)

    def on_response_error(self, error_msg):
        self.spinner.stop()
        self.loading_frame.setVisible(False)

        self.input_field.setEnabled(True)
        self.send_button.setVisible(True)
        self.send_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.input_field.setFocus()

        self.is_processing = False

        self.append_error_message(f"Erreur de connexion : {error_msg}")

    def append_user_message(self, message):
        timestamp = datetime.now().strftime("%H:%M")
        # Échapper les caractères HTML pour éviter les problèmes d'affichage
        message_escaped = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

        html = f"""
        <div style="margin: 15px 0; text-align: right; clear: both;">
            <div style="display: inline-block; background: linear-gradient(135deg, {COLORS['user_bubble']} 0%, #BBDEFB 100%);
                        border-radius: 20px; padding: 14px 20px; max-width: 65%; text-align: left;
                        box-shadow: 0 3px 10px rgba(0,0,0,0.12); word-wrap: break-word;">
                <div style="font-size: 11px; color: {COLORS['text_secondary']}; margin-bottom: 6px; font-weight: 600;">
                    👤 Vous • {timestamp}
                </div>
                <div style="color: {COLORS['text_primary']}; font-size: 14px; line-height: 1.6;">{message_escaped}</div>
            </div>
        </div>
        """
        self.chat_display.append(html)
        # Forcer la mise à jour immédiate de l'interface
        QApplication.processEvents()
        # Force le scroll vers le bas
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        QApplication.processEvents()

    def _markdown_to_html(self, text: str) -> str:
        """Convertit le markdown simple en HTML"""
        import re

        # Nettoyer les caractères d'échappement indésirables du LLM
        text = text.replace('\\"', '"')  # Guillemets échappés
        text = text.replace("\\'", "'")  # Apostrophes échappées
        text = text.replace('\\n', '\n')  # Retours à la ligne littéraux
        text = text.replace('\\t', ' ')   # Tabulations littérales
        text = text.replace('\\/', '/')   # Slashes échappés
        text = re.sub(r'\\([<>])', r'\1', text)  # < et > échappés

        # ÉTAPE 1 : Convertir les liens AVANT d'échapper le HTML
        # Convertir [texte](url) en lien HTML cliquable
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #5B4FDE; text-decoration: underline; font-weight: 500;">\1</a>', text)

        # Convertir les URL nues en liens cliquables (HTTP/HTTPS)
        text = re.sub(r'(?<!href=")(?<!src=")(https?://[^\s<>"\']+)', r'<a href="\1" style="color: #5B4FDE; text-decoration: underline;">\1</a>', text)

        # ÉTAPE 2 : Protéger les liens créés
        links = []
        def save_link(match):
            links.append(match.group(0))
            return f"__LINK_{len(links)-1}__"
        text = re.sub(r'<a href="[^"]*"[^>]*>.*?</a>', save_link, text)

        # ÉTAPE 3 : Échapper les caractères HTML spéciaux
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # ÉTAPE 4 : Restaurer les liens
        for i, link in enumerate(links):
            text = text.replace(f"__LINK_{i}__", link)

        # ÉTAPE 5 : Convertir le formatage markdown (gras, italique)
        # Convertir **texte** en <strong>texte</strong>
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)

        # Convertir _texte_ en <em>texte</em> (avec espaces autour ou début/fin)
        text = re.sub(r'(^|\s)_([^_\s]+(?:\s+[^_\s]+)*)_(\s|$)', r'\1<em>\2</em>\3', text, flags=re.MULTILINE)

        # Convertir *texte* en <em>texte</em> (avec espaces autour, pas de ** avant/après)
        text = re.sub(r'(^|\s)(?<!\*)\*([^\*\s]+(?:\s+[^\*\s]+)*)\*(?!\*)(\s|$)', r'\1<em>\2</em>\3', text, flags=re.MULTILINE)

        # Convertir les listes numérotées (1., 2., etc.)
        text = re.sub(r'^(\d+)\.\s+(.+)$', r'<div style="margin: 8px 0;"><strong>\1.</strong> \2</div>', text, flags=re.MULTILINE)

        # Convertir les listes à puces (-, *, •)
        text = re.sub(r'^[\-\*\•]\s+(.+)$', r'<div style="margin: 8px 0; padding-left: 15px;">• \1</div>', text, flags=re.MULTILINE)

        # Convertir les retours à la ligne doubles en paragraphes
        text = text.replace('\n\n', '</p><p style="margin: 10px 0;">')

        # Convertir les retours à la ligne simples en <br>
        text = text.replace('\n', '<br>')

        # Entourer le texte de balises de paragraphe
        if not text.startswith('<div') and not text.startswith('<p'):
            text = f'<p style="margin: 10px 0;">{text}</p>'

        return text

    def append_bot_message(self, message, confiance=0, temps=0, sources=None):
        timestamp = datetime.now().strftime("%H:%M")
        sources_html = ""
        if sources and len(sources) > 0:
            sources_list = ', '.join(f"<strong>#{s}</strong>" for s in sources)
            sources_html = f"""
            <div style="margin-top: 10px; padding: 8px 12px; background-color: rgba(91, 79, 222, 0.08);
                        border-left: 3px solid {COLORS['primary']}; border-radius: 6px; font-size: 11px;
                        color: {COLORS['text_secondary']};">
                📚 <strong>Sources :</strong> {sources_list}
            </div>
            """

        # Convertir le markdown en HTML
        message_html = self._markdown_to_html(message)

        html = f"""
        <div style="margin: 15px 0; text-align: left; clear: both;">
            <div style="display: inline-block; background: linear-gradient(135deg, {COLORS['bot_bubble']} 0%, #E1BEE7 100%);
                        border-radius: 20px; padding: 14px 20px; max-width: 70%;
                        box-shadow: 0 3px 10px rgba(0,0,0,0.12); word-wrap: break-word;">
                <div style="font-size: 11px; color: {COLORS['primary']}; font-weight: 700; margin-bottom: 8px;">
                    🤖 Mila • {timestamp}
                </div>
                <div style="color: {COLORS['text_primary']}; font-size: 14px; line-height: 1.7;">
                    {message_html}
                </div>
                {sources_html}
                <div style="margin-top: 10px; font-size: 11px; color: {COLORS['text_secondary']};
                            border-top: 1px solid rgba(0,0,0,0.1); padding-top: 8px;">
                    ✓ Confiance : <strong>{confiance:.1f}%</strong> | ⏱ Temps : <strong>{temps:.2f}s</strong>
                </div>
            </div>
        </div>
        """
        self.chat_display.append(html)
        # Forcer la mise à jour immédiate de l'interface
        QApplication.processEvents()
        # Force le scroll vers le bas
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        QApplication.processEvents()

    def append_system_message(self, message):
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <div style="margin: 15px 0; text-align: center;">
            <div style="display: inline-block; background-color: rgba(91, 79, 222, 0.1);
                        border: 1px solid {COLORS['primary_light']}; border-radius: 20px;
                        padding: 10px 20px;">
                <span style="color: {COLORS['primary']}; font-size: 12px; font-weight: 500;">
                    [INFO] {message} • {timestamp}
                </span>
            </div>
        </div>
        """
        self.chat_display.append(html)

    def append_error_message(self, message):
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <div style="margin: 15px 0; text-align: center;">
            <div style="display: inline-block; background-color: #FFEBEE;
                        border-left: 4px solid {COLORS['error']};
                        padding: 15px 20px; border-radius: 12px; max-width: 80%;
                        box-shadow: 0 2px 8px rgba(244, 67, 54, 0.2);">
                <div style="font-weight: bold; color: {COLORS['error']}; margin-bottom: 8px; font-size: 14px;">
                    [ERREUR] Erreur
                </div>
                <div style="color: {COLORS['text_primary']}; font-size: 13px;">
                    {message}
                </div>
                <div style="margin-top: 8px; font-size: 11px; color: {COLORS['text_secondary']};">
                    {timestamp}
                </div>
            </div>
        </div>
        """
        self.chat_display.append(html)

    def clear_conversation(self):
        """Efface la conversation et réinitialise l'interface"""
        reply = QMessageBox.question(
            self,
            "Effacer la conversation",
            "Êtes-vous sûr de vouloir effacer toute la conversation ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.chat_display.clear()
            self.display_welcome_message()
            self.current_conversation_id = None
            self.feedback_button.setVisible(False)
            # Générer un nouvel ID de session
            self.client.session_id = str(uuid.uuid4())
            self.append_system_message("Conversation effacée - Nouvelle session créée")

    def show_feedback_dialog(self):
        if not self.current_conversation_id:
            QMessageBox.warning(self, "Erreur", "Aucune conversation active pour donner un retour.")
            return

        dialog = FeedbackDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            feedback = dialog.get_feedback()
            success = self.client.send_feedback(
                self.current_conversation_id,
                feedback["note"],
                feedback["commentaire"],
                feedback["suggestion"]
            )

            if success:
                QMessageBox.information(self, "Merci !",
                    "Votre retour a été enregistré avec succès. 🎉")
                self.append_system_message("Retour utilisateur envoyé")
                self.feedback_button.setVisible(False)
            else:
                QMessageBox.warning(self, "Erreur",
                    "Impossible d'envoyer le retour. Vérifiez votre connexion.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Configurer la locale française pour les traductions Qt
    QLocale.setDefault(QLocale(QLocale.French, QLocale.France))

    # Charger les traductions Qt en français
    translator = QTranslator()
    qt_translator_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if translator.load(QLocale(), "qtbase", "_", qt_translator_path):
        app.installTranslator(translator)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS['bg_main']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text_primary']))
    app.setPalette(palette)

    window = MilaAssistApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
