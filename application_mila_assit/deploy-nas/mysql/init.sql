-- ===================================================================
-- Script d'initialisation de la base de données Mila-Assist
-- Version: 1.0.0
-- Date: 2025-01-18
-- Encodage: UTF-8 (utf8mb4)
-- ===================================================================

-- CRITIQUE: Forcer l'encodage UTF-8 AVANT toute autre commande
/*!40101 SET NAMES utf8mb4 */;
/*!40101 SET CHARACTER_SET_CLIENT=utf8mb4 */;
/*!40101 SET CHARACTER_SET_RESULTS=utf8mb4 */;
/*!40101 SET COLLATION_CONNECTION=utf8mb4_unicode_ci */;

-- Création de la base de données si elle n'existe pas
CREATE DATABASE IF NOT EXISTS mila_assist_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE mila_assist_db;

-- ===================================================================
-- Table: base_connaissances
-- Description: Base de connaissances migrée depuis intents.json
--              Contient les paires question-réponse pour le RAG
-- ===================================================================
CREATE TABLE IF NOT EXISTS base_connaissances (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique',
    etiquette VARCHAR(100) NOT NULL COMMENT 'Tag de catégorisation (ex: salutations, aide_streaming)',
    question TEXT NOT NULL COMMENT 'Question / phrase utilisateur (anciennement motif)',
    reponse TEXT NOT NULL COMMENT 'Réponse associée à la question',
    contexte VARCHAR(255) DEFAULT NULL COMMENT 'Contexte d''utilisation (optionnel)',
    active BOOLEAN DEFAULT 1 COMMENT 'Indique si l''entrée est active (1) ou désactivée (0)',
    id_embedding INT DEFAULT NULL COMMENT 'ID dans l''index FAISS correspondant',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création de l''entrée',
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Date de dernière modification',
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Alias de date_modification pour auto-sync',

    INDEX idx_etiquette (etiquette) COMMENT 'Index pour recherche par tag',
    INDEX idx_embedding (id_embedding) COMMENT 'Index pour liaison avec FAISS',
    INDEX idx_active (active) COMMENT 'Index pour filtrer les entrées actives',
    FULLTEXT INDEX idx_question_fulltext (question) COMMENT 'Index fulltext pour recherche textuelle',

    CONSTRAINT chk_etiquette_non_vide CHECK (CHAR_LENGTH(etiquette) > 0),
    CONSTRAINT chk_question_non_vide CHECK (CHAR_LENGTH(question) >= 3)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Base de connaissances AI_licia et streaming (migration intents.json)';

-- ===================================================================
-- Table: conversations
-- Description: Historique complet des échanges utilisateur-chatbot
--              Utilisé pour analytics, amélioration continue, et debugging
-- ===================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique de la conversation',
    id_session VARCHAR(36) NOT NULL COMMENT 'UUID de session utilisateur',
    question_utilisateur TEXT NOT NULL COMMENT 'Question posée par l''utilisateur',
    reponse_bot TEXT NOT NULL COMMENT 'Réponse générée par le chatbot',
    ids_connaissances_recuperees JSON DEFAULT NULL COMMENT 'IDs des entrées KB utilisées (top-3 FAISS)',
    score_confiance FLOAT DEFAULT NULL COMMENT 'Score de similarité FAISS (0-1)',
    temps_reponse_ms INT DEFAULT NULL COMMENT 'Temps de traitement total en millisecondes',
    temps_embedding_ms INT DEFAULT NULL COMMENT 'Temps calcul embedding',
    temps_retrieval_ms INT DEFAULT NULL COMMENT 'Temps recherche FAISS',
    temps_generation_ms INT DEFAULT NULL COMMENT 'Temps génération LLM',
    cache_hit BOOLEAN DEFAULT FALSE COMMENT 'Indique si la réponse vient du cache',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date/heure de la conversation',

    INDEX idx_session (id_session) COMMENT 'Index pour regrouper par session',
    INDEX idx_date (date_creation) COMMENT 'Index pour tri chronologique',
    INDEX idx_confiance (score_confiance) COMMENT 'Index pour analyses de qualité',
    INDEX idx_temps_reponse (temps_reponse_ms) COMMENT 'Index pour analyses de performance',

    CONSTRAINT chk_score_confiance_range CHECK (score_confiance IS NULL OR (score_confiance BETWEEN 0.0 AND 1.0)),
    CONSTRAINT chk_temps_reponse_positif CHECK (temps_reponse_ms IS NULL OR temps_reponse_ms >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Historique des conversations utilisateur-chatbot';

-- ===================================================================
-- Table: retours_utilisateurs
-- Description: Système de feedback pour évaluation qualité réponses
--              Notes de 1 à 5 étoiles + commentaires optionnels
-- ===================================================================
CREATE TABLE IF NOT EXISTS retours_utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique du retour',
    id_conversation INT NOT NULL COMMENT 'Référence à la conversation évaluée',
    note TINYINT NOT NULL COMMENT 'Note de satisfaction (1=Très mauvais, 5=Excellent)',
    commentaire TEXT DEFAULT NULL COMMENT 'Commentaire libre de l''utilisateur',
    suggestion_reponse TEXT DEFAULT NULL COMMENT 'Suggestion de meilleure réponse',
    categorie_probleme ENUM(
        'reponse_incorrecte',
        'reponse_incomplete',
        'ton_inapproprie',
        'reponse_obsolete',
        'hors_sujet',
        'autre'
    ) DEFAULT 'autre' COMMENT 'Classification du problème si note < 3',
    statut ENUM('nouveau', 'en_cours', 'traite', 'ignore') DEFAULT 'nouveau' COMMENT 'Statut de traitement du feedback',
    id_admin_traitement INT DEFAULT NULL COMMENT 'ID de l''admin qui a traité le feedback',
    justification TEXT DEFAULT NULL COMMENT 'Justification du traitement admin',
    date_traitement TIMESTAMP NULL DEFAULT NULL COMMENT 'Date de traitement du feedback',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date du feedback',

    FOREIGN KEY (id_conversation) REFERENCES conversations(id)
        ON DELETE CASCADE,

    INDEX idx_note (note) COMMENT 'Index pour analyses satisfaction',
    INDEX idx_date (date_creation) COMMENT 'Index pour tri chronologique',
    INDEX idx_categorie (categorie_probleme) COMMENT 'Index pour analyses par type',
    INDEX idx_statut (statut) COMMENT 'Index pour filtrage par statut',

    CONSTRAINT chk_note CHECK (note BETWEEN 1 AND 5)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Feedback utilisateurs sur les réponses du chatbot';

-- ===================================================================
-- Table: metriques
-- Description: Logs de performance et métriques système
--              Pour monitoring, alertes, et optimisations
-- ===================================================================
CREATE TABLE IF NOT EXISTS metriques (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique',
    type_metrique ENUM(
        'precision_recherche',
        'temps_reponse',
        'performance_modele',
        'utilisation_ram',
        'erreur',
        'cache_hit_rate',
        'satisfaction_moyenne'
    ) NOT NULL COMMENT 'Type de métrique enregistrée',
    valeur_metrique FLOAT NOT NULL COMMENT 'Valeur numérique de la métrique',
    details JSON DEFAULT NULL COMMENT 'Détails additionnels en JSON (ex: stack trace, contexte)',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date/heure de la mesure',

    INDEX idx_type (type_metrique) COMMENT 'Index pour filtrage par type',
    INDEX idx_date (date_creation) COMMENT 'Index pour analyses temporelles',
    INDEX idx_type_date (type_metrique, date_creation) COMMENT 'Index composite pour agrégations'
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Métriques de performance et monitoring système';

-- ===================================================================
-- Table: modifications_admin
-- Description: Historique des modifications admin de la base de connaissances
-- ===================================================================
CREATE TABLE IF NOT EXISTS modifications_admin (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique',
    id_feedback_source INT DEFAULT NULL COMMENT 'ID du feedback à l''origine de la modification',
    id_entree_kb INT NOT NULL COMMENT 'ID de l''entrée modifiée dans base_connaissances',
    ancien_contenu JSON NOT NULL COMMENT 'Ancien contenu (motif + réponse)',
    nouveau_contenu JSON NOT NULL COMMENT 'Nouveau contenu (motif + réponse)',
    diff_summary TEXT DEFAULT NULL COMMENT 'Résumé des changements',
    id_admin INT NOT NULL COMMENT 'ID de l''admin ayant effectué la modification',
    justification TEXT NOT NULL COMMENT 'Justification de la modification',
    type_modification ENUM('correction','mise_a_jour','ajout','suppression') DEFAULT 'correction' COMMENT 'Type de modification',
    nb_conversations_affectees INT DEFAULT 0 COMMENT 'Nombre de conversations affectées',
    amelioration_note_moyenne FLOAT DEFAULT NULL COMMENT 'Amélioration de la note moyenne après modification',
    peut_rollback BOOLEAN DEFAULT TRUE COMMENT 'Indique si la modification peut être annulée',
    rollback_de INT DEFAULT NULL COMMENT 'ID de la modification annulée (si rollback)',
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de la modification',

    FOREIGN KEY (id_feedback_source) REFERENCES retours_utilisateurs(id) ON DELETE SET NULL,
    FOREIGN KEY (id_entree_kb) REFERENCES base_connaissances(id) ON DELETE CASCADE,

    INDEX idx_admin (id_admin) COMMENT 'Index pour recherche par admin',
    INDEX idx_date (date_modification) COMMENT 'Index pour tri chronologique',
    INDEX idx_type (type_modification) COMMENT 'Index pour filtrage par type'
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Historique des modifications admin de la base de connaissances';

-- ===================================================================
-- Table: alertes_qualite
-- Description: Alertes générées automatiquement pour les feedbacks négatifs
-- ===================================================================
CREATE TABLE IF NOT EXISTS alertes_qualite (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identifiant unique',
    type_alerte VARCHAR(100) NOT NULL COMMENT 'Type d''alerte (ex: note_faible)',
    severite ENUM('critique','elevee','moyenne','faible') NOT NULL COMMENT 'Niveau de sévérité',
    id_conversation INT DEFAULT NULL COMMENT 'ID de la conversation concernée',
    id_feedback INT DEFAULT NULL COMMENT 'ID du feedback à l''origine de l''alerte',
    details JSON DEFAULT NULL COMMENT 'Détails additionnels',
    statut ENUM('nouveau','en_cours','resolu','ignore') DEFAULT 'nouveau' COMMENT 'Statut de l''alerte',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création de l''alerte',
    date_resolution TIMESTAMP NULL DEFAULT NULL COMMENT 'Date de résolution',

    FOREIGN KEY (id_conversation) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (id_feedback) REFERENCES retours_utilisateurs(id) ON DELETE CASCADE,

    INDEX idx_severite (severite) COMMENT 'Index pour filtrage par sévérité',
    INDEX idx_date (date_creation) COMMENT 'Index pour tri chronologique',
    INDEX idx_statut (statut) COMMENT 'Index pour filtrage par statut'
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Alertes qualité générées automatiquement';

-- ===================================================================
-- Données de test optionnelles (à décommenter pour dev/test)
-- ===================================================================

-- INSERT INTO base_connaissances (etiquette, motif, reponse, contexte) VALUES
-- ('salutations', 'bonjour', 'Bonjour ! Comment puis-je vous aider aujourd''hui ?', ''),
-- ('salutations', 'salut', 'Salut ! Prêt à streamer ? 😊', ''),
-- ('aide_ai_licia', 'comment obtenir AI_licia', 'AI_licia est disponible sur votre plateforme favorite. Besoin d''un lien ?', 'obtention');

-- ===================================================================
-- Vues utiles pour analytics
-- ===================================================================

-- Vue: satisfaction_globale (note moyenne, nombre total de feedbacks)
CREATE OR REPLACE VIEW v_satisfaction_globale AS
SELECT
    COUNT(*) AS total_feedbacks,
    AVG(note) AS note_moyenne,
    SUM(CASE WHEN note >= 4 THEN 1 ELSE 0 END) AS feedbacks_positifs,
    SUM(CASE WHEN note <= 2 THEN 1 ELSE 0 END) AS feedbacks_negatifs,
    DATE(date_creation) AS date
FROM retours_utilisateurs
GROUP BY DATE(date_creation)
ORDER BY date DESC;

-- Vue: performance_quotidienne (temps réponse moyen, taux cache)
CREATE OR REPLACE VIEW v_performance_quotidienne AS
SELECT
    DATE(date_creation) AS date,
    COUNT(*) AS total_conversations,
    AVG(temps_reponse_ms) AS temps_moyen_ms,
    AVG(score_confiance) AS confiance_moyenne,
    SUM(CASE WHEN cache_hit = TRUE THEN 1 ELSE 0 END) / COUNT(*) AS taux_cache_hit
FROM conversations
GROUP BY DATE(date_creation)
ORDER BY date DESC;

-- ===================================================================
-- Procédures stockées pour maintenance
-- ===================================================================

-- Procédure: purge_anciennes_conversations (RGPD - conservation 90 jours)
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS purger_anciennes_conversations(
    IN jours_retention INT
)
BEGIN
    DECLARE nb_supprimees INT DEFAULT 0;

    DELETE FROM conversations
    WHERE date_creation < DATE_SUB(NOW(), INTERVAL jours_retention DAY);

    SET nb_supprimees = ROW_COUNT();

    INSERT INTO metriques (type_metrique, valeur_metrique, details)
    VALUES (
        'maintenance',
        nb_supprimees,
        JSON_OBJECT('operation', 'purge_conversations', 'jours_retention', jours_retention)
    );

    SELECT CONCAT('Conversations supprimées: ', nb_supprimees) AS resultat;
END //

DELIMITER ;

-- ===================================================================
-- Event scheduler pour purge automatique (RGPD)
-- ===================================================================

-- Activer l'event scheduler si nécessaire
-- SET GLOBAL event_scheduler = ON;

-- Event: purge automatique tous les jours à 2h du matin
CREATE EVENT IF NOT EXISTS evt_purge_quotidienne
ON SCHEDULE EVERY 1 DAY
STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 1 DAY + INTERVAL 2 HOUR)
DO
    CALL purger_anciennes_conversations(90);

-- ===================================================================
-- Permissions et sécurité
-- ===================================================================

-- Créer l'utilisateur applicatif avec privilèges appropriés
CREATE USER IF NOT EXISTS 'mila_user'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';

-- Accorder les permissions nécessaires
GRANT SELECT, INSERT, UPDATE, DELETE ON mila_assist_db.* TO 'mila_user'@'%';
GRANT EXECUTE ON PROCEDURE mila_assist_db.purger_anciennes_conversations TO 'mila_user'@'%';

-- Appliquer les changements
FLUSH PRIVILEGES;

-- ===================================================================
-- Fin du script d'initialisation
-- ===================================================================

-- Afficher les tables créées
SHOW TABLES;

-- Afficher le statut final
SELECT
    'Base de données Mila-Assist initialisée avec succès !' AS statut,
    NOW() AS date_initialisation;
