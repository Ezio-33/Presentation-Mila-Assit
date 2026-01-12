-- ========================================================
-- TRIGGERS MYSQL - Mila-Assist
-- Automatisations de la base de données
-- ========================================================

USE mila_assist_db;

-- ========================================================
-- TRIGGER 1 : Alerte automatique sur retours qualité faible
-- ========================================================
-- Déclenché après l'insertion d'un nouveau retour utilisateur
-- Crée automatiquement une alerte si la note est inférieure à 3

DELIMITER $$

DROP TRIGGER IF EXISTS alerte_reponse_qualite_faible$$

CREATE TRIGGER alerte_reponse_qualite_faible
AFTER INSERT ON retours_utilisateurs
FOR EACH ROW
BEGIN
    -- Vérifier si la note est faible (< 3)
    IF NEW.note < 3 THEN
        -- Déterminer la sévérité selon la note
        SET @severite = CASE
            WHEN NEW.note = 1 THEN 'critique'
            WHEN NEW.note = 2 THEN 'elevee'
            ELSE 'moyenne'
        END;

        -- Construire les détails JSON
        SET @details = JSON_OBJECT(
            'note', NEW.note,
            'categorie', NEW.categorie_probleme,
            'commentaire_present', IF(NEW.commentaire IS NOT NULL, TRUE, FALSE),
            'suggestion_presente', IF(NEW.suggestion_reponse IS NOT NULL, TRUE, FALSE)
        );

        -- Insérer l'alerte dans la table alertes_qualite
        INSERT INTO alertes_qualite (
            type_alerte,
            severite,
            id_conversation,
            id_feedback,
            details,
            date_creation
        ) VALUES (
            'note_faible',
            @severite,
            NEW.id_conversation,
            NEW.id,
            @details,
            NOW()
        );
    END IF;
END$$

DELIMITER ;

-- ========================================================
-- TRIGGER 2 : Mise à jour automatique des métriques
-- ========================================================
-- Optionnel : Peut être ajouté plus tard pour tracking automatique

-- DELIMITER $$

-- DROP TRIGGER IF EXISTS maj_metriques_satisfaction$$

-- CREATE TRIGGER maj_metriques_satisfaction
-- AFTER INSERT ON retours_utilisateurs
-- FOR EACH ROW
-- BEGIN
--     -- Insérer une métrique pour suivre la satisfaction
--     INSERT INTO metriques (
--         type_metrique,
--         valeur,
--         details,
--         date_creation
--     ) VALUES (
--         'satisfaction_utilisateur',
--         NEW.note,
--         JSON_OBJECT('id_conversation', NEW.id_conversation, 'categorie', NEW.categorie_probleme),
--         NOW()
--     );
-- END$$

-- DELIMITER ;

-- ========================================================
-- VÉRIFICATION DES TRIGGERS CRÉÉS
-- ========================================================

-- Afficher tous les triggers de la base
SHOW TRIGGERS;

-- ========================================================
-- NOTES D'UTILISATION
-- ========================================================
--
-- Ce trigger est exécuté automatiquement après chaque
-- insertion dans retours_utilisateurs.
--
-- Fonctionnement :
-- 1. Un utilisateur soumet un feedback avec note < 3
-- 2. Le trigger s'active automatiquement
-- 3. Une alerte est créée dans alertes_qualite avec :
--    - Type : 'note_faible'
--    - Sévérité : 'critique' (note=1), 'elevee' (note=2), 'moyenne' (autre)
--    - Référence à la conversation et au feedback
--    - Détails JSON (note, catégorie, présence commentaire/suggestion)
--
-- Les alertes peuvent ensuite être consultées par les admins via :
-- SELECT * FROM alertes_qualite WHERE severite = 'critique';
--
-- ========================================================
