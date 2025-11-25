-- ============================================================================
-- CRÉATION DU SCHÉMA DE BASE DE DONNÉES
-- Jeu de Morpion Avancé - BDW 2025
-- ============================================================================

-- Création du schéma pour isoler nos tables
-- (Recommandé pour ne pas polluer le schéma public)
CREATE SCHEMA IF NOT EXISTS morpion;

-- Définir le schéma par défaut pour cette session
SET search_path TO morpion;


-- ============================================================================
-- TABLE: MORPION
-- ============================================================================
-- Cette table stocke les "templates" ou modèles de morpions réutilisables.
-- Un morpion peut appartenir à plusieurs équipes (réutilisabilité).
-- ============================================================================

CREATE TABLE morpion (
    id_morpion          SERIAL PRIMARY KEY,
    -- SERIAL : auto-incrémenté automatiquement pour avoir un ID unique
    
    nom                 VARCHAR(100) NOT NULL UNIQUE,
    -- UNIQUE : deux morpions ne peuvent pas avoir le même nom
    -- NOT NULL : le nom est obligatoire pour identifier le morpion
    
    image               VARCHAR(255) NOT NULL,
    -- Chemin vers l'image du morpion (obligatoire pour l'affichage)
    
    points_vie          INTEGER NOT NULL CHECK (points_vie >= 1),
    -- CHECK >= 1 : chaque morpion doit avoir au moins 1 point de vie
    -- (sinon il serait mort dès sa création)
    
    points_attaque      INTEGER NOT NULL CHECK (points_attaque >= 1),
    -- CHECK >= 1 : minimum 1 point pour pouvoir attaquer
    
    points_mana         INTEGER NOT NULL CHECK (points_mana >= 1),
    -- CHECK >= 1 : minimum 1 point pour pouvoir lancer des sorts
    
    points_reussite     INTEGER NOT NULL CHECK (points_reussite >= 1),
    -- CHECK >= 1 : minimum 1 point pour avoir une chance de réussite
    
    date_creation       TIMESTAMP DEFAULT NOW(),
    -- DEFAULT NOW() : enregistre automatiquement la date de création
    
    CONSTRAINT check_somme_caracteristiques 
        CHECK (points_vie + points_attaque + points_mana + points_reussite = 15)
    -- Cette contrainte garantit que la somme des 4 caractéristiques vaut 15
    -- C'est une règle du jeu pour l'équilibrage des morpions
);

-- Index pour accélérer les recherches par nom (utilisé fréquemment)
CREATE INDEX idx_morpion_nom ON morpion(nom);


-- ============================================================================
-- TABLE: ÉQUIPE
-- ============================================================================
-- Une équipe est composée de 6 à 8 morpions.
-- Chaque équipe a une couleur unique pour la distinguer visuellement.
-- ============================================================================

CREATE TABLE equipe (
    id_equipe           SERIAL PRIMARY KEY,
    -- SERIAL : génération automatique de l'identifiant
    
    nom                 VARCHAR(100) NOT NULL UNIQUE,
    -- UNIQUE : deux équipes ne peuvent pas avoir le même nom
    -- Permet d'identifier facilement les équipes
    
    couleur             VARCHAR(50) UNIQUE,
    -- Couleur optionnelle (peut être remplie plus tard pour distinguer visuellement)
    
    date_creation       TIMESTAMP DEFAULT NOW()
    -- Enregistre quand l'équipe a été créée
);

-- Index pour les recherches par nom et couleur
CREATE INDEX idx_equipe_nom ON equipe(nom);
CREATE INDEX idx_equipe_couleur ON equipe(couleur);


-- ============================================================================
-- TABLE: MORPION_EQUIPE (Table de liaison N:N)
-- ============================================================================
-- Cette table gère la relation plusieurs-à-plusieurs entre morpions et équipes.
-- Un morpion peut appartenir à plusieurs équipes (réutilisabilité des templates).
-- Une équipe contient plusieurs morpions (entre 6 et 8).
-- ============================================================================

CREATE TABLE morpion_equipe (
    id_equipe           INTEGER NOT NULL,
    id_morpion          INTEGER NOT NULL,
    
    ordre_dans_equipe   INTEGER NOT NULL CHECK (ordre_dans_equipe >= 1),
    -- Permet d'ordonner les morpions dans l'équipe (1er, 2ème, 3ème...)
    -- Utile pour l'affichage et la sélection durant le jeu
    
    PRIMARY KEY (id_equipe, id_morpion),
    -- Clé primaire composée : un morpion ne peut être qu'une seule fois dans une équipe
    -- Mais il peut être dans plusieurs équipes différentes
    
    FOREIGN KEY (id_equipe) REFERENCES equipe(id_equipe) 
        ON DELETE CASCADE,
    -- CASCADE : si on supprime une équipe, on supprime ses associations
    -- (logique : pas d'équipe = pas de composition d'équipe)
    
    FOREIGN KEY (id_morpion) REFERENCES morpion(id_morpion) 
        ON DELETE CASCADE,
    -- CASCADE : si on supprime un morpion, on supprime ses associations
    -- (mais attention, cela peut affecter les équipes qui l'utilisent)
    
    CONSTRAINT unique_ordre_par_equipe 
        UNIQUE (id_equipe, ordre_dans_equipe)
    -- Dans une équipe, deux morpions ne peuvent pas avoir le même ordre
    -- (pas de doublon de position 1, 2, 3...)
);

-- Index pour accélérer les recherches d'équipes d'un morpion
CREATE INDEX idx_morpion_equipe_morpion ON morpion_equipe(id_morpion);


-- ============================================================================
-- TABLE: CONFIGURATION
-- ============================================================================
-- Stocke les paramètres de configuration pour les parties.
-- Ces configurations sont datées et réutilisables.
-- ============================================================================

CREATE TABLE configuration (
    id_configuration            SERIAL PRIMARY KEY,
    
    taille_grille               INTEGER NOT NULL CHECK (taille_grille IN (3, 4)),
    -- CHECK IN (3,4) : seules les grilles 3x3 et 4x4 sont autorisées
    -- Contrainte métier du jeu
    
    nb_max_tours                INTEGER NOT NULL CHECK (nb_max_tours > 0),
    -- CHECK > 0 : une partie doit avoir au moins 1 tour
    -- Évite les configurations absurdes
    
    somme_caracteristiques      INTEGER DEFAULT 15 CHECK (somme_caracteristiques > 0),
    -- Valeur par défaut de 15 pour la somme des caractéristiques
    -- Permet de modifier cette valeur dans le futur si besoin
    
    date_creation               TIMESTAMP DEFAULT NOW()
    -- Enregistre quand la configuration a été créée
);

-- Index pour rechercher les configurations par taille de grille
CREATE INDEX idx_configuration_taille ON configuration(taille_grille);


-- ============================================================================
-- TABLE: PARTIE
-- ============================================================================
-- Représente une partie jouée entre deux équipes.
-- Stocke les informations de début, fin, et le gagnant.
-- ============================================================================

CREATE TABLE partie (
    id_partie               SERIAL PRIMARY KEY,
    
    id_equipe1              INTEGER NOT NULL,
    id_equipe2              INTEGER NOT NULL,
    
    id_equipe_gagnante      INTEGER,
    -- NULL si partie en cours ou match nul
    -- Contient l'ID de l'équipe gagnante sinon
    
    id_configuration        INTEGER NOT NULL,
    
    date_debut              TIMESTAMP DEFAULT NOW(),
    -- Enregistre automatiquement le début de la partie
    
    date_fin                TIMESTAMP,
    -- NULL tant que la partie est en cours
    -- Rempli quand la partie se termine
    
    tour_actuel             INTEGER DEFAULT 1 CHECK (tour_actuel >= 1),
    -- Compteur du tour actuel (commence à 1)
    
    FOREIGN KEY (id_equipe1) REFERENCES equipe(id_equipe),
    -- Pas de CASCADE : on ne veut pas supprimer les parties si on supprime une équipe
    -- Les parties historiques doivent être conservées
    
    FOREIGN KEY (id_equipe2) REFERENCES equipe(id_equipe),
    
    FOREIGN KEY (id_equipe_gagnante) REFERENCES equipe(id_equipe),
    -- L'équipe gagnante doit exister dans la table équipe
    
    FOREIGN KEY (id_configuration) REFERENCES configuration(id_configuration),
    
    CONSTRAINT check_equipes_differentes 
        CHECK (id_equipe1 != id_equipe2),
    -- Une équipe ne peut pas jouer contre elle-même
    -- Vérification logique obligatoire
    
    CONSTRAINT check_gagnante_valide 
        CHECK (id_equipe_gagnante IS NULL 
               OR id_equipe_gagnante = id_equipe1 
               OR id_equipe_gagnante = id_equipe2),
    -- L'équipe gagnante doit être l'une des deux équipes qui jouent
    -- Évite les incohérences (équipe 3 gagne un match entre équipe 1 et 2)
    
    CONSTRAINT check_dates_coherentes 
        CHECK (date_fin IS NULL OR date_fin >= date_debut)
    -- La date de fin doit être après la date de début
    -- Évite les absurdités temporelles
);

-- Index pour rechercher les parties d'une équipe
CREATE INDEX idx_partie_equipe1 ON partie(id_equipe1);
CREATE INDEX idx_partie_equipe2 ON partie(id_equipe2);
CREATE INDEX idx_partie_gagnante ON partie(id_equipe_gagnante);

-- Index pour rechercher les parties en cours (date_fin NULL)
CREATE INDEX idx_partie_en_cours ON partie(date_fin) WHERE date_fin IS NULL;


-- ============================================================================
-- TABLE: JOURNAL
-- ============================================================================
-- Stocke toutes les actions réalisées durant une partie.
-- Chaque ligne est numérotée automatiquement par partie.
-- ============================================================================

CREATE TABLE journal (
    id_journal          SERIAL PRIMARY KEY,
    -- ID technique pour identifier chaque ligne
    
    id_partie           INTEGER NOT NULL,
    
    numero_ligne        INTEGER NOT NULL,
    -- Numéro de ligne dans la partie (1, 2, 3, ...)
    -- Auto-incrémenté par un trigger
    
    date_action         TIMESTAMP DEFAULT NOW(),
    -- Enregistre automatiquement quand l'action a eu lieu
    
    texte_action        TEXT NOT NULL,
    -- Description textuelle de l'action
    -- TEXT au lieu de VARCHAR car les descriptions peuvent être longues
    
    FOREIGN KEY (id_partie) REFERENCES partie(id_partie) 
        ON DELETE CASCADE,
    -- CASCADE : si on supprime une partie, on supprime son journal
    -- (logique : pas de partie = pas d'historique)
    
    CONSTRAINT unique_numero_par_partie 
        UNIQUE (id_partie, numero_ligne)
    -- Dans une partie, deux lignes ne peuvent pas avoir le même numéro
    -- Garantit l'unicité de la numérotation
);

-- Index pour accélérer les recherches du journal d'une partie
CREATE INDEX idx_journal_partie ON journal(id_partie, numero_ligne);

-- Index pour les statistiques par date
CREATE INDEX idx_journal_date ON journal(date_action);


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Trigger 1 : Vérification de la taille de l'équipe (6 à 8 morpions)
-- ----------------------------------------------------------------------------
-- Ce trigger vérifie qu'une équipe ne dépasse jamais 8 morpions
-- La vérification du minimum (6) sera faite au moment de créer une partie

CREATE OR REPLACE FUNCTION check_taille_equipe()
RETURNS TRIGGER AS $$
DECLARE
    nb_morpions INTEGER;
BEGIN
    -- Compter le nombre de morpions dans l'équipe
    SELECT COUNT(*) INTO nb_morpions
    FROM morpion_equipe
    WHERE id_equipe = NEW.id_equipe;
    
    -- Si plus de 8 morpions, lever une exception
    IF nb_morpions > 8 THEN
        RAISE EXCEPTION 'Une équipe ne peut pas avoir plus de 8 morpions (actuellement: %)', nb_morpions;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Activer le trigger APRÈS chaque insertion dans morpion_equipe
CREATE TRIGGER trigger_check_taille_equipe
    AFTER INSERT ON morpion_equipe
    FOR EACH ROW
    EXECUTE FUNCTION check_taille_equipe();


-- ----------------------------------------------------------------------------
-- Trigger 2 : Auto-incrémentation du numéro de ligne dans le journal
-- ----------------------------------------------------------------------------
-- Ce trigger attribue automatiquement un numéro de ligne séquentiel
-- pour chaque action dans une partie (1, 2, 3, ...)

CREATE OR REPLACE FUNCTION set_numero_ligne()
RETURNS TRIGGER AS $$
DECLARE
    dernier_numero INTEGER;
BEGIN
    -- Trouver le dernier numéro de ligne pour cette partie
    SELECT COALESCE(MAX(numero_ligne), 0) INTO dernier_numero
    FROM journal
    WHERE id_partie = NEW.id_partie;
    
    -- Attribuer le prochain numéro
    NEW.numero_ligne := dernier_numero + 1;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Activer le trigger AVANT chaque insertion dans journal
CREATE TRIGGER trigger_set_numero_ligne
    BEFORE INSERT ON journal
    FOR EACH ROW
    EXECUTE FUNCTION set_numero_ligne();


-- ============================================================================
-- VUES POUR LES STATISTIQUES (Fonctionnalité 1)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Vue 1 : Top 3 des équipes avec le plus de victoires
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_top_equipes AS
SELECT 
    e.id_equipe,
    e.nom,
    e.couleur,
    COUNT(p.id_partie) AS nb_victoires
FROM equipe e
LEFT JOIN partie p ON e.id_equipe = p.id_equipe_gagnante
GROUP BY e.id_equipe, e.nom, e.couleur
ORDER BY nb_victoires DESC, e.nom ASC
LIMIT 3;


-- ----------------------------------------------------------------------------
-- Vue 2 : Statistiques sur les parties (plus rapide, plus longue, moyenne)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_stats_parties AS
SELECT 
    COUNT(*) AS nb_parties_totales,
    COUNT(date_fin) AS nb_parties_terminees,
    MIN(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_min_secondes,
    MAX(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_max_secondes,
    AVG(EXTRACT(EPOCH FROM (date_fin - date_debut))) AS duree_moy_secondes
FROM partie
WHERE date_fin IS NOT NULL;


-- ----------------------------------------------------------------------------
-- Vue 3 : Nombre moyen de lignes de journal par mois/année
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_journal_par_mois AS
SELECT 
    EXTRACT(YEAR FROM j.date_action) AS annee,
    EXTRACT(MONTH FROM j.date_action) AS mois,
    COUNT(j.id_journal) AS nb_lignes_total,
    COUNT(DISTINCT j.id_partie) AS nb_parties,
    CASE 
        WHEN COUNT(DISTINCT j.id_partie) > 0 
        THEN COUNT(j.id_journal)::FLOAT / COUNT(DISTINCT j.id_partie)
        ELSE 0
    END AS nb_moyen_lignes
FROM journal j
GROUP BY annee, mois
ORDER BY annee DESC, mois DESC;


-- ============================================================================
-- DONNÉES DE TEST
-- ============================================================================
-- Jeu d'exemples léger pour valider rapidement le schéma.
-- Chaque INSERT est commenté pour expliquer la logique métier.

-- ---------------------------------------------------------------------------
-- Morpions (8 modèles équilibrés, somme = 15)
-- ---------------------------------------------------------------------------
INSERT INTO morpion (nom, image, points_vie, points_attaque, points_mana, points_reussite)
VALUES
    ('Dragon Rouge', 'static/img/morpions/dragon_rouge.png', 4, 4, 4, 3),          -- profil équilibré
    ('Gardien Ancien', 'static/img/morpions/gardien_ancien.png', 6, 3, 3, 3),      -- tank
    ('Archimage', 'static/img/morpions/archimage.png', 2, 2, 8, 3),               -- spécialiste mana
    ('Ninja Précis', 'static/img/morpions/ninja_precis.png', 2, 3, 2, 8),          -- réussite élevée
    ('Berserker', 'static/img/morpions/berserker.png', 5, 7, 1, 2),                -- forte attaque
    ('Druide Serein', 'static/img/morpions/druide_serein.png', 4, 2, 6, 3),        -- soutien
    ('Chevalier Doré', 'static/img/morpions/chevalier_dore.png', 5, 4, 2, 4),      -- polyvalent défense/attaque
    ('Assassin Ombre', 'static/img/morpions/assassin_ombre.png', 3, 6, 2, 4),      -- dégâts rapides
    ('Spectre Azur', 'static/img/morpions/spectre_azur.png', 3, 5, 3, 4),          -- agile magique
    ('Titan Runique', 'static/img/morpions/titan_runique.png', 7, 4, 2, 2),        -- très résistant
    ('Oracle Stellaire', 'static/img/morpions/oracle_stellaire.png', 2, 2, 7, 4),   -- grand contrôle
    ('Guerrière Boréale', 'static/img/morpions/guerriere_boreale.png', 4, 5, 3, 3); -- offensive équilibrée

-- ---------------------------------------------------------------------------
-- Configurations disponibles
-- ---------------------------------------------------------------------------
INSERT INTO configuration (taille_grille, nb_max_tours)
VALUES
    (3, 20),
    (4, 30),
    (3, 15);


-- ============================================================================
-- COMMENTAIRES FINAUX
-- ============================================================================

COMMENT ON SCHEMA morpion IS 
'Schéma pour le jeu de morpion avancé - Projet BDW 2025';

COMMENT ON TABLE morpion IS 
'Templates de morpions réutilisables avec leurs caractéristiques';

COMMENT ON TABLE equipe IS 
'Équipes composées de 6 à 8 morpions';

COMMENT ON TABLE morpion_equipe IS 
'Table de liaison N:N entre morpions et équipes';

COMMENT ON TABLE configuration IS 
'Paramètres de configuration pour les parties (taille grille, nb tours)';

COMMENT ON TABLE partie IS 
'Parties jouées entre deux équipes avec leur état (en cours/terminée)';

COMMENT ON TABLE journal IS 
'Historique de toutes les actions réalisées durant les parties';

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================

