-- ============================================================================
-- Script SQL pour l'insertion de données de test
-- Jeu de morpion avancé - BDW 2025
-- ============================================================================

SET SEARCH_PATH TO morpion_avance;

-- ============================================================================
-- INSERTION DES MORPIONS
-- ============================================================================
-- Note: La somme des caractéristiques doit être égale à 15
-- Chaque caractéristique doit être >= 1

INSERT INTO morpion (nom, image, points_vie, points_attaque, points_mana, points_reussite) VALUES
('Morpion 01', 'static/img/morpions/t1.png', 4, 4, 4, 3),
('Morpion 02', 'static/img/morpions/t2.png', 5, 4, 3, 3),
('Morpion 03', 'static/img/morpions/t3.png', 3, 2, 6, 4),
('Morpion 04', 'static/img/morpions/t4.png', 4, 7, 2, 2),
('Morpion 05', 'static/img/morpions/t5.png', 3, 6, 2, 4),
('Morpion 06', 'static/img/morpions/t6.png', 6, 6, 1, 2),
('Morpion 07', 'static/img/morpions/t7.png', 3, 1, 8, 3),
('Morpion 08', 'static/img/morpions/t8.png', 2, 2, 7, 4),
('Morpion 09', 'static/img/morpions/t9.png', 4, 2, 6, 3),
('Morpion 10', 'static/img/morpions/t10.png', 7, 3, 3, 2),
('Morpion 11', 'static/img/morpions/t11.png', 8, 2, 2, 3),
('Morpion 12', 'static/img/morpions/t12.png', 5, 1, 7, 2),
('Morpion 13', 'static/img/morpions/t13.png', 3, 4, 2, 6),
('Morpion 14', 'static/img/morpions/t14.png', 2, 3, 3, 7),
('Morpion 15', 'static/img/morpions/t15.png', 3, 3, 4, 5),
('Morpion 16', 'static/img/morpions/t16.png', 7, 4, 1, 3);

-- ============================================================================
-- INSERTION DES ÉQUIPES
-- ============================================================================

INSERT INTO equipe (nom, couleur, date_creation) VALUES
('LYON', '#cc0000', CURRENT_TIMESTAMP - INTERVAL '30 days'),
('OM', '#004b8d', CURRENT_TIMESTAMP - INTERVAL '25 days'),
('NICE', '#111111', CURRENT_TIMESTAMP - INTERVAL '20 days'),
('RENNES', '#22884a', CURRENT_TIMESTAMP - INTERVAL '15 days'),
('MONACO', '#d4af37', CURRENT_TIMESTAMP - INTERVAL '10 days'),
('LILLE', '#6a1b9a', CURRENT_TIMESTAMP - INTERVAL '5 days');

-- ============================================================================
-- LIAISON MORPIONS-ÉQUIPES
-- ============================================================================
-- Chaque équipe doit avoir entre 6 et 8 morpions

-- Équipe 1: LYON
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(1, 1, 1),
(1, 4, 2),
(1, 6, 3),
(1, 9, 4),
(1, 10, 5),
(1, 15, 6);

-- Équipe 2: OM
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(2, 2, 1),
(2, 3, 2),
(2, 5, 3),
(2, 7, 4),
(2, 11, 5),
(2, 12, 6),
(2, 16, 7);

-- Équipe 3: NICE
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(3, 4, 1),
(3, 8, 2),
(3, 13, 3),
(3, 14, 4),
(3, 15, 5),
(3, 16, 6);

-- Équipe 4: RENNES
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(4, 3, 1),
(4, 9, 2),
(4, 10, 3),
(4, 11, 4),
(4, 12, 5),
(4, 13, 6),
(4, 14, 7);

-- Équipe 5: MONACO
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(5, 1, 1),
(5, 2, 2),
(5, 5, 3),
(5, 6, 4),
(5, 7, 5),
(5, 8, 6),
(5, 15, 7);

-- Équipe 6: LILLE
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(6, 4, 1),
(6, 9, 2),
(6, 10, 3),
(6, 11, 4),
(6, 12, 5),
(6, 13, 6),
(6, 14, 7),
(6, 16, 8);

-- ============================================================================
-- INSERTION DES CONFIGURATIONS
-- ============================================================================

INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques, date_creation) VALUES
(3, 20, 15, CURRENT_TIMESTAMP - INTERVAL '30 days'),  -- Config classique 3x3
(4, 30, 15, CURRENT_TIMESTAMP - INTERVAL '25 days'),  -- Config grande grille
(3, 15, 15, CURRENT_TIMESTAMP - INTERVAL '20 days'),  -- Config rapide
(4, 40, 15, CURRENT_TIMESTAMP - INTERVAL '15 days'),  -- Config longue
(3, 25, 15, CURRENT_TIMESTAMP - INTERVAL '10 days');  -- Config intermédiaire

-- ============================================================================
-- INSERTION DE PARTIES DE DÉMONSTRATION
-- ============================================================================

-- Partie 1: Terminée, victoire équipe 1 (rapide)
-- Partie 1: LYON vs OM (56 secondes, victoire LYON)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 2, 1, 1,
 CURRENT_TIMESTAMP - INTERVAL '2 days',
 CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '56 seconds',
 6);

-- Partie 2: NICE vs RENNES (partie longue)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(3, 4, 4, 2,
 CURRENT_TIMESTAMP - INTERVAL '36 hours',
 CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '25 minutes',
 18);

-- Partie 3: MONACO vs LILLE (partie en cours)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(5, 6, NULL, 3,
 CURRENT_TIMESTAMP - INTERVAL '90 minutes',
 NULL,
 5);

-- Partie 4: OM vs MONACO (victoire OM)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(2, 5, 2, 4,
 CURRENT_TIMESTAMP - INTERVAL '4 days',
 CURRENT_TIMESTAMP - INTERVAL '4 days' + INTERVAL '8 minutes',
 9);

-- Partie 5: LYON vs NICE (partie rapide)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 3, 1, 5,
 CURRENT_TIMESTAMP - INTERVAL '5 days',
 CURRENT_TIMESTAMP - INTERVAL '5 days' + INTERVAL '3 minutes',
 6);

-- Partie 6: RENNES vs LILLE
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(4, 6, 4, 2,
 CURRENT_TIMESTAMP - INTERVAL '3 days',
 CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '18 minutes',
 15);

-- Partie 7: OM vs RENNES (victoire OM en 56s)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(2, 4, 2, 1,
 CURRENT_TIMESTAMP - INTERVAL '6 days',
 CURRENT_TIMESTAMP - INTERVAL '6 days' + INTERVAL '56 seconds',
 7);

-- ============================================================================
-- INSERTION DES ENTRÉES DE JOURNAL
-- ============================================================================

-- Journal pour la partie 1 (LYON vs OM, 56 secondes)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days', 'Début de la partie entre LYON et OM'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '10 seconds', 'Tour 1 - LYON place Morpion 01 en (1,1)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '25 seconds', 'Tour 1 - OM place Morpion 02 en (0,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '40 seconds', 'Tour 2 - LYON place Morpion 04 en (1,2)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '56 seconds', 'VICTOIRE - LYON aligne trois morpions en un temps record !');

-- Journal pour la partie 2 (NICE vs RENNES, partie longue)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours', 'Début de la partie entre NICE et RENNES (grille 4x4)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '1 minute', 'Tour 1 - NICE place Morpion 04 en (1,1)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '2 minutes', 'Tour 1 - RENNES place Morpion 09 en (2,2)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '6 minutes', 'Tour 3 - RENNES lance un sort de soin sur Morpion 10'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '20 minutes', 'Tour 10 - NICE rate un combat contre Morpion 09'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '25 minutes', 'VICTOIRE - RENNES aligne quatre morpions !');

-- Journal pour la partie 3 (MONACO vs LILLE, en cours)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(3, NULL, CURRENT_TIMESTAMP - INTERVAL '90 minutes', 'Début de la partie entre MONACO et LILLE'),
(3, NULL, CURRENT_TIMESTAMP - INTERVAL '80 minutes', 'Tour 1 - MONACO place Morpion 06 en (1,1)'),
(3, NULL, CURRENT_TIMESTAMP - INTERVAL '75 minutes', 'Tour 1 - LILLE place Morpion 09 en (0,0)');

-- ============================================================================
-- VÉRIFICATIONS ET STATISTIQUES
-- ============================================================================

-- Compter les enregistrements
DO $$
DECLARE
    nb_morpions INTEGER;
    nb_equipes INTEGER;
    nb_parties INTEGER;
    nb_journal INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_morpions FROM morpion;
    SELECT COUNT(*) INTO nb_equipes FROM equipe;
    SELECT COUNT(*) INTO nb_parties FROM partie;
    SELECT COUNT(*) INTO nb_journal FROM journal;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Données insérées avec succès !';
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'Morpions : %', nb_morpions;
    RAISE NOTICE 'Équipes : %', nb_equipes;
    RAISE NOTICE 'Parties : %', nb_parties;
    RAISE NOTICE 'Entrées de journal : %', nb_journal;
    RAISE NOTICE '========================================';
END $$;

-- Afficher quelques statistiques
SELECT '=== TOP 3 DES ÉQUIPES ===' AS info;
SELECT nom, couleur, nb_victoires FROM v_top_equipes;

SELECT '=== STATISTIQUES DES PARTIES ===' AS info;
SELECT * FROM v_stats_parties;

