-- ============================================================================
-- SCRIPT D'INSTALLATION COMPLET
-- Base de données du jeu de morpion avancé - BDW 2025
-- ============================================================================
-- 
-- Ce script combine :
-- 1. Création du schéma et des tables (create_database.sql)
-- 2. Insertion des données de test (insert_data.sql)
--
-- Pour exécuter ce script :
-- psql -h bd-pedago.univ-lyon1.fr -U p1234567 -d p1234567 -f install_complete.sql
-- (Remplacer p1234567 par votre numéro étudiant)
--
-- Ou via pgweb : copier-coller tout le contenu et exécuter
-- ============================================================================

\echo '================================================================================'
\echo 'INSTALLATION DE LA BASE DE DONNÉES - JEU DE MORPION AVANCÉ'
\echo '================================================================================'
\echo ''

-- ============================================================================
-- PARTIE 1 : CRÉATION DU SCHÉMA ET DES TABLES
-- ============================================================================

\echo 'Étape 1/3 : Création du schéma et des tables...'
\echo ''

-- Créer le schéma s'il n'existe pas déjà
CREATE SCHEMA IF NOT EXISTS morpion_avance;
SET SEARCH_PATH TO morpion_avance;

-- Suppression des tables si elles existent
DROP TABLE IF EXISTS journal CASCADE;
DROP TABLE IF EXISTS partie CASCADE;
DROP TABLE IF EXISTS morpion_equipe CASCADE;
DROP TABLE IF EXISTS equipe CASCADE;
DROP TABLE IF EXISTS morpion CASCADE;
DROP TABLE IF EXISTS configuration CASCADE;

-- Table MORPION
CREATE TABLE morpion (
    id_morpion SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    image VARCHAR(255) NOT NULL,
    points_vie INTEGER NOT NULL CHECK (points_vie >= 1),
    points_attaque INTEGER NOT NULL CHECK (points_attaque >= 1),
    points_mana INTEGER NOT NULL CHECK (points_mana >= 1),
    points_reussite INTEGER NOT NULL CHECK (points_reussite >= 1),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_total_points CHECK (
        points_vie + points_attaque + points_mana + points_reussite = 15
    )
);

CREATE INDEX idx_morpion_nom ON morpion(nom);

-- Table EQUIPE
CREATE TABLE equipe (
    id_equipe SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    couleur VARCHAR(50) NOT NULL UNIQUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_equipe_nom ON equipe(nom);
CREATE INDEX idx_equipe_couleur ON equipe(couleur);

-- Table MORPION_EQUIPE
CREATE TABLE morpion_equipe (
    id_equipe INTEGER NOT NULL REFERENCES equipe(id_equipe) ON DELETE CASCADE,
    id_morpion INTEGER NOT NULL REFERENCES morpion(id_morpion) ON DELETE CASCADE,
    ordre_dans_equipe INTEGER NOT NULL,
    PRIMARY KEY (id_equipe, id_morpion),
    CONSTRAINT check_ordre UNIQUE (id_equipe, ordre_dans_equipe)
);

-- Table CONFIGURATION
CREATE TABLE configuration (
    id_configuration SERIAL PRIMARY KEY,
    taille_grille INTEGER NOT NULL CHECK (taille_grille IN (3, 4)),
    nb_max_tours INTEGER NOT NULL CHECK (nb_max_tours > 0),
    somme_caracteristiques INTEGER DEFAULT 15 CHECK (somme_caracteristiques > 0),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table PARTIE
CREATE TABLE partie (
    id_partie SERIAL PRIMARY KEY,
    id_equipe1 INTEGER NOT NULL REFERENCES equipe(id_equipe),
    id_equipe2 INTEGER NOT NULL REFERENCES equipe(id_equipe),
    id_equipe_gagnante INTEGER REFERENCES equipe(id_equipe),
    id_configuration INTEGER NOT NULL REFERENCES configuration(id_configuration),
    date_debut TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_fin TIMESTAMP,
    tour_actuel INTEGER DEFAULT 1,
    CONSTRAINT check_equipes_differentes CHECK (id_equipe1 != id_equipe2),
    CONSTRAINT check_equipe_gagnante CHECK (
        id_equipe_gagnante IS NULL OR 
        id_equipe_gagnante = id_equipe1 OR 
        id_equipe_gagnante = id_equipe2
    ),
    CONSTRAINT check_dates CHECK (date_fin IS NULL OR date_fin >= date_debut)
);

CREATE INDEX idx_partie_dates ON partie(date_debut, date_fin);
CREATE INDEX idx_partie_equipe1 ON partie(id_equipe1);
CREATE INDEX idx_partie_equipe2 ON partie(id_equipe2);
CREATE INDEX idx_partie_gagnante ON partie(id_equipe_gagnante);

-- Table JOURNAL
CREATE TABLE journal (
    id_journal SERIAL PRIMARY KEY,
    id_partie INTEGER NOT NULL REFERENCES partie(id_partie) ON DELETE CASCADE,
    numero_ligne INTEGER NOT NULL,
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    texte_action TEXT NOT NULL,
    CONSTRAINT unique_ligne_partie UNIQUE (id_partie, numero_ligne)
);

CREATE INDEX idx_journal_partie ON journal(id_partie, numero_ligne);
CREATE INDEX idx_journal_date ON journal(date_action);

\echo '✓ Tables créées'
\echo ''

-- Fonctions et Triggers
CREATE OR REPLACE FUNCTION check_taille_equipe()
RETURNS TRIGGER AS $$
DECLARE
    nb_morpions INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_morpions
    FROM morpion_equipe
    WHERE id_equipe = NEW.id_equipe;
    
    IF nb_morpions > 8 THEN
        RAISE EXCEPTION 'Une équipe ne peut pas avoir plus de 8 morpions';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_taille_equipe
AFTER INSERT ON morpion_equipe
FOR EACH ROW
EXECUTE FUNCTION check_taille_equipe();

CREATE OR REPLACE FUNCTION set_numero_ligne()
RETURNS TRIGGER AS $$
DECLARE
    max_numero INTEGER;
BEGIN
    IF NEW.numero_ligne IS NULL THEN
        SELECT COALESCE(MAX(numero_ligne), 0) + 1 INTO max_numero
        FROM journal
        WHERE id_partie = NEW.id_partie;
        
        NEW.numero_ligne := max_numero;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_numero_ligne
BEFORE INSERT ON journal
FOR EACH ROW
EXECUTE FUNCTION set_numero_ligne();

\echo '✓ Triggers et fonctions créés'
\echo ''

-- Vues
CREATE OR REPLACE VIEW v_top_equipes AS
SELECT 
    e.id_equipe,
    e.nom,
    e.couleur,
    COUNT(p.id_partie) AS nb_victoires
FROM equipe e
LEFT JOIN partie p ON e.id_equipe = p.id_equipe_gagnante
GROUP BY e.id_equipe, e.nom, e.couleur
ORDER BY nb_victoires DESC
LIMIT 3;

CREATE OR REPLACE VIEW v_stats_parties AS
SELECT 
    COUNT(*) AS nb_parties_totales,
    COUNT(CASE WHEN date_fin IS NOT NULL THEN 1 END) AS nb_parties_terminees,
    MIN(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_min_secondes,
    MAX(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_max_secondes,
    AVG(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_moy_secondes
FROM partie
WHERE date_fin IS NOT NULL;

CREATE OR REPLACE VIEW v_journal_par_mois AS
SELECT 
    EXTRACT(YEAR FROM j.date_action) AS annee,
    EXTRACT(MONTH FROM j.date_action) AS mois,
    COUNT(*) AS nb_lignes_total,
    COUNT(DISTINCT j.id_partie) AS nb_parties,
    CAST(COUNT(*) AS FLOAT) / NULLIF(COUNT(DISTINCT j.id_partie), 0) AS nb_moyen_lignes
FROM journal j
GROUP BY 
    EXTRACT(YEAR FROM j.date_action),
    EXTRACT(MONTH FROM j.date_action)
ORDER BY annee DESC, mois DESC;

\echo '✓ Vues créées'
\echo ''

-- ============================================================================
-- PARTIE 2 : INSERTION DES DONNÉES DE TEST
-- ============================================================================

\echo 'Étape 2/3 : Insertion des données de test...'
\echo ''

-- Insertion des morpions
INSERT INTO morpion (nom, image, points_vie, points_attaque, points_mana, points_reussite) VALUES
('Dragon Rouge', 'static/images/morpions/dragon_rouge.png', 4, 4, 4, 3),
('Chevalier Noble', 'static/images/morpions/chevalier_noble.png', 5, 4, 3, 3),
('Mage Sage', 'static/images/morpions/mage_sage.png', 3, 2, 6, 4),
('Guerrier Brutal', 'static/images/morpions/guerrier_brutal.png', 4, 7, 2, 2),
('Assassin Sombre', 'static/images/morpions/assassin_sombre.png', 3, 6, 2, 4),
('Berserker', 'static/images/morpions/berserker.png', 6, 6, 1, 2),
('Archimage', 'static/images/morpions/archimage.png', 3, 1, 8, 3),
('Sorcier Mystique', 'static/images/morpions/sorcier_mystique.png', 2, 2, 7, 4),
('Enchanteur', 'static/images/morpions/enchanteur.png', 4, 2, 6, 3),
('Paladin Sacré', 'static/images/morpions/paladin_sacre.png', 7, 3, 3, 2),
('Gardien Ancien', 'static/images/morpions/gardien_ancien.png', 8, 2, 2, 3),
('Prêtre Guérisseur', 'static/images/morpions/pretre_guerisseur.png', 5, 1, 7, 2),
('Maître d''Armes', 'static/images/morpions/maitre_armes.png', 3, 4, 2, 6),
('Ninja Précis', 'static/images/morpions/ninja_precis.png', 2, 3, 3, 7),
('Archer Elfe', 'static/images/morpions/archer_elfe.png', 3, 3, 4, 5),
('Golem de Pierre', 'static/images/morpions/golem_pierre.png', 7, 4, 1, 3),
('Esprit Éthéré', 'static/images/morpions/esprit_ethere.png', 2, 3, 6, 4),
('Druide Naturel', 'static/images/morpions/druide_naturel.png', 4, 3, 5, 3),
('Vampire Nocturne', 'static/images/morpions/vampire_nocturne.png', 5, 5, 2, 3),
('Phoenix Éternel', 'static/images/morpions/phoenix_eternel.png', 4, 4, 5, 2);

\echo '✓ 20 morpions insérés'

-- Insertion des équipes
INSERT INTO equipe (nom, couleur, date_creation) VALUES
('Les Flammes Éternelles', 'red', CURRENT_TIMESTAMP - INTERVAL '30 days'),
('Les Gardiens de l''Aube', 'blue', CURRENT_TIMESTAMP - INTERVAL '25 days'),
('Les Ombres Silencieuses', 'black', CURRENT_TIMESTAMP - INTERVAL '20 days'),
('Les Sages Mystiques', 'purple', CURRENT_TIMESTAMP - INTERVAL '15 days'),
('Les Braves Chevaliers', 'gold', CURRENT_TIMESTAMP - INTERVAL '10 days'),
('Les Forces de la Nature', 'green', CURRENT_TIMESTAMP - INTERVAL '5 days');

\echo '✓ 6 équipes insérées'

-- Liaison morpions-équipes
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(1, 1, 1), (1, 4, 2), (1, 6, 3), (1, 19, 4), (1, 20, 5), (1, 16, 6), (1, 5, 7),
(2, 2, 1), (2, 10, 2), (2, 11, 3), (2, 12, 4), (2, 13, 5), (2, 15, 6), (2, 16, 7), (2, 3, 8),
(3, 5, 1), (3, 14, 2), (3, 15, 3), (3, 13, 4), (3, 19, 5), (3, 17, 6),
(4, 3, 1), (4, 7, 2), (4, 8, 3), (4, 9, 4), (4, 17, 5), (4, 18, 6), (4, 12, 7), (4, 20, 8),
(5, 2, 1), (5, 1, 2), (5, 10, 3), (5, 4, 4), (5, 13, 5), (5, 3, 6), (5, 18, 7),
(6, 18, 1), (6, 20, 2), (6, 11, 3), (6, 17, 4), (6, 15, 5), (6, 9, 6), (6, 16, 7);

\echo '✓ Morpions assignés aux équipes'

-- Insertion des configurations
INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques, date_creation) VALUES
(3, 20, 15, CURRENT_TIMESTAMP - INTERVAL '30 days'),
(4, 30, 15, CURRENT_TIMESTAMP - INTERVAL '25 days'),
(3, 15, 15, CURRENT_TIMESTAMP - INTERVAL '20 days'),
(4, 40, 15, CURRENT_TIMESTAMP - INTERVAL '15 days'),
(3, 25, 15, CURRENT_TIMESTAMP - INTERVAL '10 days');

\echo '✓ 5 configurations insérées'

-- Insertion des parties
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 2, 1, 1, CURRENT_TIMESTAMP - INTERVAL '10 days', CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '5 minutes', 8),
(3, 4, 4, 2, CURRENT_TIMESTAMP - INTERVAL '8 days', CURRENT_TIMESTAMP - INTERVAL '8 days' + INTERVAL '45 minutes', 28),
(1, 5, 2, 3, CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_TIMESTAMP - INTERVAL '6 days' + INTERVAL '12 minutes', 10),
(5, 6, NULL, 1, CURRENT_TIMESTAMP - INTERVAL '1 hour', NULL, 5),
(1, 3, 1, 3, CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP - INTERVAL '5 days' + INTERVAL '3 minutes', 6),
(2, 4, 4, 2, CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_TIMESTAMP - INTERVAL '4 days' + INTERVAL '20 minutes', 15),
(1, 6, 1, 1, CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '8 minutes', 9);

\echo '✓ 7 parties insérées'

-- Insertion des entrées de journal (exemples)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days', 'Début de la partie entre Les Flammes Éternelles et Les Gardiens de l''Aube'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '30 seconds', 'Tour 1 - Les Flammes Éternelles placent Dragon Rouge en position (1,1)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '1 minute', 'Tour 1 - Les Gardiens de l''Aube placent Chevalier Noble en position (0,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '5 minutes', 'VICTOIRE - Les Flammes Éternelles ont aligné 3 morpions !'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '1 hour', 'Début de la partie entre Les Braves Chevaliers et Les Forces de la Nature'),
(4, NULL, CURRENT_TIMESTAMP - INTERVAL '55 minutes', 'Tour 1 - Les Braves Chevaliers placent Chevalier Noble en position (1,1)');

\echo '✓ Entrées de journal insérées'
\echo ''

-- ============================================================================
-- PARTIE 3 : VÉRIFICATIONS ET STATISTIQUES
-- ============================================================================

\echo 'Étape 3/3 : Vérifications...'
\echo ''

-- Statistiques
\echo '================================================================================'
\echo 'INSTALLATION TERMINÉE AVEC SUCCÈS !'
\echo '================================================================================'
\echo ''
\echo 'Résumé des données insérées :'

SELECT 
    'Morpions' AS table_name, 
    COUNT(*)::text AS nombre 
FROM morpion
UNION ALL
SELECT 'Équipes', COUNT(*)::text FROM equipe
UNION ALL
SELECT 'Configurations', COUNT(*)::text FROM configuration
UNION ALL
SELECT 'Parties', COUNT(*)::text FROM partie
UNION ALL
SELECT 'Entrées de journal', COUNT(*)::text FROM journal;

\echo ''
\echo 'Top 3 des équipes :'
SELECT nom, nb_victoires FROM v_top_equipes;

\echo ''
\echo '================================================================================'
\echo 'Pour utiliser le schéma, exécutez :'
\echo '  SET SEARCH_PATH TO morpion_avance;'
\echo ''
\echo 'Pour lister les tables :'
\echo '  \dt'
\echo ''
\echo 'Consultez le fichier README_DATABASE.md pour plus d''informations'
\echo '================================================================================'

