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
-- Morpions équilibrés
('Dragon Rouge', 'static/images/morpions/dragon_rouge.png', 4, 4, 4, 3),
('Chevalier Noble', 'static/images/morpions/chevalier_noble.png', 5, 4, 3, 3),
('Mage Sage', 'static/images/morpions/mage_sage.png', 3, 2, 6, 4),

-- Morpions orientés attaque
('Guerrier Brutal', 'static/images/morpions/guerrier_brutal.png', 4, 7, 2, 2),
('Assassin Sombre', 'static/images/morpions/assassin_sombre.png', 3, 6, 2, 4),
('Berserker', 'static/images/morpions/berserker.png', 6, 6, 1, 2),

-- Morpions orientés magie
('Archimage', 'static/images/morpions/archimage.png', 3, 1, 8, 3),
('Sorcier Mystique', 'static/images/morpions/sorcier_mystique.png', 2, 2, 7, 4),
('Enchanteur', 'static/images/morpions/enchanteur.png', 4, 2, 6, 3),

-- Morpions orientés défense/vie
('Paladin Sacré', 'static/images/morpions/paladin_sacre.png', 7, 3, 3, 2),
('Gardien Ancien', 'static/images/morpions/gardien_ancien.png', 8, 2, 2, 3),
('Prêtre Guérisseur', 'static/images/morpions/pretre_guerisseur.png', 5, 1, 7, 2),

-- Morpions orientés réussite
('Maître d\'Armes', 'static/images/morpions/maitre_armes.png', 3, 4, 2, 6),
('Ninja Précis', 'static/images/morpions/ninja_precis.png', 2, 3, 3, 7),
('Archer Elfe', 'static/images/morpions/archer_elfe.png', 3, 3, 4, 5),

-- Morpions variés
('Golem de Pierre', 'static/images/morpions/golem_pierre.png', 7, 4, 1, 3),
('Esprit Éthéré', 'static/images/morpions/esprit_ethere.png', 2, 3, 6, 4),
('Druide Naturel', 'static/images/morpions/druide_naturel.png', 4, 3, 5, 3),
('Vampire Nocturne', 'static/images/morpions/vampire_nocturne.png', 5, 5, 2, 3),
('Phoenix Éternel', 'static/images/morpions/phoenix_eternel.png', 4, 4, 5, 2);

-- ============================================================================
-- INSERTION DES ÉQUIPES
-- ============================================================================

INSERT INTO equipe (nom, couleur, date_creation) VALUES
('Les Flammes Éternelles', 'red', CURRENT_TIMESTAMP - INTERVAL '30 days'),
('Les Gardiens de l\'Aube', 'blue', CURRENT_TIMESTAMP - INTERVAL '25 days'),
('Les Ombres Silencieuses', 'black', CURRENT_TIMESTAMP - INTERVAL '20 days'),
('Les Sages Mystiques', 'purple', CURRENT_TIMESTAMP - INTERVAL '15 days'),
('Les Braves Chevaliers', 'gold', CURRENT_TIMESTAMP - INTERVAL '10 days'),
('Les Forces de la Nature', 'green', CURRENT_TIMESTAMP - INTERVAL '5 days');

-- ============================================================================
-- LIAISON MORPIONS-ÉQUIPES
-- ============================================================================
-- Chaque équipe doit avoir entre 6 et 8 morpions

-- Équipe 1: Les Flammes Éternelles (orientation attaque/feu)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(1, 1, 1),  -- Dragon Rouge
(1, 4, 2),  -- Guerrier Brutal
(1, 6, 3),  -- Berserker
(1, 19, 4), -- Vampire Nocturne
(1, 20, 5), -- Phoenix Éternel
(1, 16, 6), -- Golem de Pierre
(1, 5, 7);  -- Assassin Sombre

-- Équipe 2: Les Gardiens de l'Aube (orientation défense/soin)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(2, 2, 1),  -- Chevalier Noble
(2, 10, 2), -- Paladin Sacré
(2, 11, 3), -- Gardien Ancien
(2, 12, 4), -- Prêtre Guérisseur
(2, 13, 5), -- Maître d'Armes
(2, 15, 6), -- Archer Elfe
(2, 16, 7), -- Golem de Pierre
(2, 3, 8);  -- Mage Sage

-- Équipe 3: Les Ombres Silencieuses (orientation précision/furtivité)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(3, 5, 1),  -- Assassin Sombre
(3, 14, 2), -- Ninja Précis
(3, 15, 3), -- Archer Elfe
(3, 13, 4), -- Maître d'Armes
(3, 19, 5), -- Vampire Nocturne
(3, 17, 6); -- Esprit Éthéré

-- Équipe 4: Les Sages Mystiques (orientation magie)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(4, 3, 1),  -- Mage Sage
(4, 7, 2),  -- Archimage
(4, 8, 3),  -- Sorcier Mystique
(4, 9, 4),  -- Enchanteur
(4, 17, 5), -- Esprit Éthéré
(4, 18, 6), -- Druide Naturel
(4, 12, 7), -- Prêtre Guérisseur
(4, 20, 8); -- Phoenix Éternel

-- Équipe 5: Les Braves Chevaliers (orientation équilibrée)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(5, 2, 1),  -- Chevalier Noble
(5, 1, 2),  -- Dragon Rouge
(5, 10, 3), -- Paladin Sacré
(5, 4, 4),  -- Guerrier Brutal
(5, 13, 5), -- Maître d'Armes
(5, 3, 6),  -- Mage Sage
(5, 18, 7); -- Druide Naturel

-- Équipe 6: Les Forces de la Nature (orientation nature/équilibre)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(6, 18, 1), -- Druide Naturel
(6, 20, 2), -- Phoenix Éternel
(6, 11, 3), -- Gardien Ancien
(6, 17, 4), -- Esprit Éthéré
(6, 15, 5), -- Archer Elfe
(6, 9, 6),  -- Enchanteur
(6, 16, 7); -- Golem de Pierre

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
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 2, 1, 1, 
 CURRENT_TIMESTAMP - INTERVAL '10 days',
 CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '5 minutes',
 8);

-- Partie 2: Terminée, victoire équipe 4 (longue)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(3, 4, 4, 2,
 CURRENT_TIMESTAMP - INTERVAL '8 days',
 CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '45 minutes',
 28);

-- Partie 3: Terminée, victoire équipe 2
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 5, 2, 3,
 CURRENT_TIMESTAMP - INTERVAL '6 days',
 CURRENT_TIMESTAMP - INTERVAL '6 days' + INTERVAL '12 minutes',
 10);

-- Partie 4: En cours
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(5, 6, NULL, 1,
 CURRENT_TIMESTAMP - INTERVAL '1 hour',
 NULL,
 5);

-- Partie 5: Terminée, victoire équipe 1 (partie rapide - pour stats)
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 3, 1, 3,
 CURRENT_TIMESTAMP - INTERVAL '5 days',
 CURRENT_TIMESTAMP - INTERVAL '5 days' + INTERVAL '3 minutes',
 6);

-- Partie 6: Terminée, victoire équipe 4
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(2, 4, 4, 2,
 CURRENT_TIMESTAMP - INTERVAL '4 days',
 CURRENT_TIMESTAMP - INTERVAL '4 days' + INTERVAL '20 minutes',
 15);

-- Partie 7: Terminée, victoire équipe 1
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 6, 1, 1,
 CURRENT_TIMESTAMP - INTERVAL '3 days',
 CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '8 minutes',
 9);

-- ============================================================================
-- INSERTION DES ENTRÉES DE JOURNAL
-- ============================================================================

-- Journal pour la partie 1 (victoire rapide de l'équipe 1)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days', 'Début de la partie entre Les Flammes Éternelles et Les Gardiens de l''Aube'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '30 seconds', 'Tour 1 - Les Flammes Éternelles placent Dragon Rouge en position (1,1)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '1 minute', 'Tour 1 - Les Gardiens de l''Aube placent Chevalier Noble en position (0,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '90 seconds', 'Tour 2 - Les Flammes Éternelles placent Guerrier Brutal en position (1,2)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '2 minutes', 'Tour 2 - Les Gardiens de l''Aube placent Paladin Sacré en position (2,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '150 seconds', 'Tour 3 - Dragon Rouge attaque Chevalier Noble et inflige 4 points de dégâts'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '3 minutes', 'Tour 3 - Les Gardiens de l''Aube placent Gardien Ancien en position (0,2)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '210 seconds', 'Tour 4 - Les Flammes Éternelles placent Berserker en position (1,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '4 minutes', 'Tour 4 - Paladin Sacré attaque Dragon Rouge mais échoue (probabilité insuffisante)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '270 seconds', 'Tour 5 - Berserker attaque Chevalier Noble et inflige 6 points de dégâts'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '4 minutes 30 seconds', 'Tour 5 - Chevalier Noble est éliminé !'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '5 minutes', 'VICTOIRE - Les Flammes Éternelles ont aligné 3 morpions !');

-- Journal pour la partie 2 (partie longue avec magie)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days', 'Début de la partie entre Les Ombres Silencieuses et Les Sages Mystiques (grille 4x4)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '1 minute', 'Tour 1 - Les Ombres Silencieuses placent Assassin Sombre en position (1,1)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '2 minutes', 'Tour 1 - Les Sages Mystiques placent Archimage en position (2,2)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '5 minutes', 'Tour 3 - Archimage lance Boule de Feu sur Assassin Sombre et inflige 3 dégâts'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '10 minutes', 'Tour 6 - Ninja Précis attaque Mage Sage avec succès et inflige 3 dégâts'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '20 minutes', 'Tour 12 - Sorcier Mystique lance Sort de Soin sur Archimage (+2 PV)'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '35 minutes', 'Tour 22 - Enchanteur lance Armageddon sur la case (0,0) - case détruite !'),
(2, NULL, CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '45 minutes', 'VICTOIRE - Les Sages Mystiques ont aligné 4 morpions !');

-- Journal pour la partie 4 (en cours)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '1 hour', 'Début de la partie entre Les Braves Chevaliers et Les Forces de la Nature'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '55 minutes', 'Tour 1 - Les Braves Chevaliers placent Chevalier Noble en position (1,1)'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '50 minutes', 'Tour 1 - Les Forces de la Nature placent Druide Naturel en position (0,0)'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '45 minutes', 'Tour 2 - Les Braves Chevaliers placent Dragon Rouge en position (2,1)'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '40 minutes', 'Tour 2 - Les Forces de la Nature placent Phoenix Éternel en position (0,2)');

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

