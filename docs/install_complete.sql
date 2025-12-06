-- SCRIPT D'INSTALLATION COMPLET


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
    nom VARCHAR(100) NOT NULL UNIQUE, -- varchar pr les chaines de carc --
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
        SELECT MAX(numero_ligne) INTO max_numero
        FROM journal
        WHERE id_partie = NEW.id_partie;

        IF max_numero IS NULL THEN
            NEW.numero_ligne := 1;
        ELSE
            NEW.numero_ligne := max_numero + 1;
        END IF;
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

-- Insertion des morpions (noms simples pour coller aux fichiers t1 -> t16)
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

\echo '✓ 16 morpions insérés'

-- Insertion des équipes (noms alignés avec les tests côté site)
INSERT INTO equipe (nom, couleur, date_creation) VALUES
('LYON', '#cc0000', CURRENT_TIMESTAMP - INTERVAL '30 days'),
('OM', '#004b8d', CURRENT_TIMESTAMP - INTERVAL '25 days'),
('NICE', '#111111', CURRENT_TIMESTAMP - INTERVAL '20 days'),
('RENNES', '#22884a', CURRENT_TIMESTAMP - INTERVAL '15 days'),
('MONACO', '#d4af37', CURRENT_TIMESTAMP - INTERVAL '10 days'),
('LILLE', '#6a1b9a', CURRENT_TIMESTAMP - INTERVAL '5 days');

\echo '✓ 6 équipes insérées'

-- Liaison morpions-équipes (6 à 8 morpions chacun)
INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe) VALUES
(1, 1, 1), (1, 4, 2), (1, 6, 3), (1, 9, 4), (1, 10, 5), (1, 15, 6),
(2, 2, 1), (2, 3, 2), (2, 5, 3), (2, 7, 4), (2, 11, 5), (2, 12, 6), (2, 16, 7),
(3, 4, 1), (3, 8, 2), (3, 13, 3), (3, 14, 4), (3, 15, 5), (3, 16, 6),
(4, 3, 1), (4, 9, 2), (4, 10, 3), (4, 11, 4), (4, 12, 5), (4, 13, 6), (4, 14, 7),
(5, 1, 1), (5, 2, 2), (5, 5, 3), (5, 6, 4), (5, 7, 5), (5, 8, 6), (5, 15, 7),
(6, 4, 1), (6, 9, 2), (6, 10, 3), (6, 11, 4), (6, 12, 5), (6, 13, 6), (6, 14, 7), (6, 16, 8);

\echo '✓ Morpions assignés aux équipes'

-- Insertion des configurations
INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques, date_creation) VALUES
(3, 20, 15, CURRENT_TIMESTAMP - INTERVAL '30 days'),
(4, 30, 15, CURRENT_TIMESTAMP - INTERVAL '25 days'),
(3, 15, 15, CURRENT_TIMESTAMP - INTERVAL '20 days'),
(4, 40, 15, CURRENT_TIMESTAMP - INTERVAL '15 days'),
(3, 25, 15, CURRENT_TIMESTAMP - INTERVAL '10 days');

\echo '✓ 5 configurations insérées'

-- Insertion des parties (permet de montrer les statistiques "Plus rapide" / "Plus longue")
INSERT INTO partie (id_equipe1, id_equipe2, id_equipe_gagnante, id_configuration, date_debut, date_fin, tour_actuel) VALUES
(1, 2, 1, 1, CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '56 seconds', 6),
(3, 4, 4, 2, CURRENT_TIMESTAMP - INTERVAL '36 hours', CURRENT_TIMESTAMP - INTERVAL '36 hours' + INTERVAL '25 minutes', 18),
(5, 6, NULL, 3, CURRENT_TIMESTAMP - INTERVAL '90 minutes', NULL, 5),
(2, 5, 2, 4, CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_TIMESTAMP - INTERVAL '4 days' + INTERVAL '8 minutes', 9),
(1, 3, 1, 5, CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP - INTERVAL '5 days' + INTERVAL '3 minutes', 6),
(4, 6, 4, 2, CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_TIMESTAMP - INTERVAL '3 days' + INTERVAL '18 minutes', 15),
(2, 4, 2, 1, CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_TIMESTAMP - INTERVAL '6 days' + INTERVAL '56 seconds', 7);

\echo '✓ 7 parties insérées'

-- Insertion des entrées de journal (exemples)
INSERT INTO journal (id_partie, numero_ligne, date_action, texte_action) VALUES
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days', 'Début de la partie entre LYON et OM'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '10 seconds', 'Tour 1 - LYON place Morpion 01 en (1,1)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '25 seconds', 'Tour 1 - OM place Morpion 02 en (0,0)'),
(1, NULL, CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '56 seconds', 'VICTOIRE - LYON aligne trois morpions en un temps record !'),
(3, NULL, CURRENT_TIMESTAMP - INTERVAL '90 minutes', 'Début de la partie entre MONACO et LILLE'),
(3, NULL, CURRENT_TIMESTAMP - INTERVAL '80 minutes', 'Tour 1 - MONACO place Morpion 06 en (1,1)');

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
\echo 'Pour utiliser le schéma, tu fais'
\echo '  SET SEARCH_PATH TO morpion_avance;'
\echo ''
\echo 'Pour lister les tables :'
\echo '  \dt'
\echo ''
\echo 'Consultez le fichier README_DATABASE.md pour plus d''informations'
\echo '================================================================================'

