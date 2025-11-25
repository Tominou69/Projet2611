-- ============================================================================
-- Script SQL pour la création de la base de données du jeu de morpion avancé
-- UCBL - BDW - 2025
-- ============================================================================

-- Créer le schéma s'il n'existe pas déjà
CREATE SCHEMA IF NOT EXISTS morpion_avance;
SET SEARCH_PATH TO morpion_avance;

-- ============================================================================
-- SUPPRESSION DES TABLES (si elles existent déjà)
-- ============================================================================

DROP TABLE IF EXISTS journal CASCADE;
DROP TABLE IF EXISTS partie CASCADE;
DROP TABLE IF EXISTS morpion_equipe CASCADE;
DROP TABLE IF EXISTS equipe CASCADE;
DROP TABLE IF EXISTS morpion CASCADE;
DROP TABLE IF EXISTS configuration CASCADE;

-- ============================================================================
-- CRÉATION DES TABLES
-- ============================================================================

-- Table MORPION
-- Un morpion est un template réutilisable dans plusieurs équipes
CREATE TABLE morpion (
    id_morpion SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    image VARCHAR(255) NOT NULL, -- chemin vers l'image
    points_vie INTEGER NOT NULL CHECK (points_vie >= 1),
    points_attaque INTEGER NOT NULL CHECK (points_attaque >= 1),
    points_mana INTEGER NOT NULL CHECK (points_mana >= 1),
    points_reussite INTEGER NOT NULL CHECK (points_reussite >= 1),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Contrainte : la somme des points doit être égale à 15 (paramètre par défaut)
    CONSTRAINT check_total_points CHECK (
        points_vie + points_attaque + points_mana + points_reussite = 15
    )
);

-- Index sur le nom pour les recherches
CREATE INDEX idx_morpion_nom ON morpion(nom);

-- Table EQUIPE
CREATE TABLE equipe (
    id_equipe SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    couleur VARCHAR(50) NOT NULL UNIQUE, -- couleur unique pour distinguer les équipes
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index sur le nom et la couleur
CREATE INDEX idx_equipe_nom ON equipe(nom);
CREATE INDEX idx_equipe_couleur ON equipe(couleur);

-- Table de liaison MORPION_EQUIPE (relation N:N)
-- Une équipe contient entre 6 et 8 morpions
-- Un morpion peut appartenir à plusieurs équipes
CREATE TABLE morpion_equipe (
    id_equipe INTEGER NOT NULL REFERENCES equipe(id_equipe) ON DELETE CASCADE,
    id_morpion INTEGER NOT NULL REFERENCES morpion(id_morpion) ON DELETE CASCADE,
    ordre_dans_equipe INTEGER NOT NULL, -- pour garder l'ordre des morpions dans l'équipe
    PRIMARY KEY (id_equipe, id_morpion),
    CONSTRAINT check_ordre UNIQUE (id_equipe, ordre_dans_equipe)
);

-- Table CONFIGURATION
-- Stocke les paramètres de configuration datés
CREATE TABLE configuration (
    id_configuration SERIAL PRIMARY KEY,
    taille_grille INTEGER NOT NULL CHECK (taille_grille IN (3, 4)), -- 3x3 ou 4x4
    nb_max_tours INTEGER NOT NULL CHECK (nb_max_tours > 0),
    somme_caracteristiques INTEGER DEFAULT 15 CHECK (somme_caracteristiques > 0),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table PARTIE
-- Une partie oppose deux équipes avec une configuration donnée
CREATE TABLE partie (
    id_partie SERIAL PRIMARY KEY,
    id_equipe1 INTEGER NOT NULL REFERENCES equipe(id_equipe),
    id_equipe2 INTEGER NOT NULL REFERENCES equipe(id_equipe),
    id_equipe_gagnante INTEGER REFERENCES equipe(id_equipe), -- NULL si partie pas terminée ou match nul
    id_configuration INTEGER NOT NULL REFERENCES configuration(id_configuration),
    date_debut TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_fin TIMESTAMP,
    tour_actuel INTEGER DEFAULT 1,
    -- Contraintes : les deux équipes doivent être différentes
    CONSTRAINT check_equipes_differentes CHECK (id_equipe1 != id_equipe2),
    -- L'équipe gagnante doit être l'une des deux équipes en jeu
    CONSTRAINT check_equipe_gagnante CHECK (
        id_equipe_gagnante IS NULL OR 
        id_equipe_gagnante = id_equipe1 OR 
        id_equipe_gagnante = id_equipe2
    ),
    -- La date de fin doit être après la date de début
    CONSTRAINT check_dates CHECK (date_fin IS NULL OR date_fin >= date_debut)
);

-- Index pour les recherches de parties
CREATE INDEX idx_partie_dates ON partie(date_debut, date_fin);
CREATE INDEX idx_partie_equipe1 ON partie(id_equipe1);
CREATE INDEX idx_partie_equipe2 ON partie(id_equipe2);
CREATE INDEX idx_partie_gagnante ON partie(id_equipe_gagnante);

-- Table JOURNAL
-- Stocke toutes les actions réalisées pendant une partie
CREATE TABLE journal (
    id_journal SERIAL PRIMARY KEY,
    id_partie INTEGER NOT NULL REFERENCES partie(id_partie) ON DELETE CASCADE,
    numero_ligne INTEGER NOT NULL, -- numéro unique au niveau de la partie
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    texte_action TEXT NOT NULL,
    -- Combinaison unique : une ligne est unique pour une partie donnée
    CONSTRAINT unique_ligne_partie UNIQUE (id_partie, numero_ligne)
);

-- Index pour accélérer les recherches de journal par partie
CREATE INDEX idx_journal_partie ON journal(id_partie, numero_ligne);
CREATE INDEX idx_journal_date ON journal(date_action);

-- ============================================================================
-- FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction pour vérifier qu'une équipe a entre 6 et 8 morpions
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

-- Trigger pour vérifier la taille de l'équipe à chaque insertion
CREATE TRIGGER trigger_check_taille_equipe
AFTER INSERT ON morpion_equipe
FOR EACH ROW
EXECUTE FUNCTION check_taille_equipe();

-- Fonction pour calculer automatiquement le prochain numéro de ligne dans le journal
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

-- Trigger pour auto-incrémenter le numéro de ligne
CREATE TRIGGER trigger_set_numero_ligne
BEFORE INSERT ON journal
FOR EACH ROW
EXECUTE FUNCTION set_numero_ligne();

-- ============================================================================
-- VUES UTILES POUR LES STATISTIQUES
-- ============================================================================

-- Vue pour le top 3 des équipes avec le plus de victoires
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

-- Vue pour les statistiques des parties
CREATE OR REPLACE VIEW v_stats_parties AS
SELECT 
    COUNT(*) AS nb_parties_totales,
    COUNT(CASE WHEN date_fin IS NOT NULL THEN 1 END) AS nb_parties_terminees,
    MIN(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_min_secondes,
    MAX(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_max_secondes,
    AVG(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_moy_secondes
FROM partie
WHERE date_fin IS NOT NULL;

-- Vue pour le nombre moyen de lignes de journal par mois/année
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

-- ============================================================================
-- COMMENTAIRES SUR LES TABLES
-- ============================================================================

COMMENT ON TABLE morpion IS 'Table des morpions (templates réutilisables)';
COMMENT ON TABLE equipe IS 'Table des équipes, chaque équipe a 6-8 morpions';
COMMENT ON TABLE morpion_equipe IS 'Table de liaison entre morpions et équipes (N:N)';
COMMENT ON TABLE configuration IS 'Table des configurations de partie (taille grille, nb tours)';
COMMENT ON TABLE partie IS 'Table des parties jouées';
COMMENT ON TABLE journal IS 'Table du journal d\'actions pour chaque partie';

-- ============================================================================
-- AFFICHAGE DU RÉSUMÉ
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Base de données créée avec succès !';
    RAISE NOTICE 'Schéma: morpion_avance';
    RAISE NOTICE 'Tables créées: 6';
    RAISE NOTICE 'Vues créées: 3';
    RAISE NOTICE 'Fonctions/Triggers créés: 2';
    RAISE NOTICE '========================================';
END $$;

