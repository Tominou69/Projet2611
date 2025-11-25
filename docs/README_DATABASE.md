# Base de Données - Jeu de Morpion Avancé

## 📋 Description du Projet

Projet BDW 2025 - UCBL Lyon 1  
Développement d'une base de données pour un jeu de morpion avancé où les morpions ont des caractéristiques et peuvent combattre.

## 📁 Fichiers du Projet

### Fichiers SQL
- **`create_database.sql`** : Script de création du schéma complet de la base de données
  - Création des 6 tables principales
  - Définition des contraintes, index et clés étrangères
  - Création des triggers et fonctions
  - Création des vues pour les statistiques

- **`insert_data.sql`** : Script d'insertion de données de test
  - 20 morpions variés avec différentes caractéristiques
  - 6 équipes pré-configurées
  - 7 parties de démonstration (5 terminées, 2 en cours)
  - Entrées de journal détaillées

### Documentation
- **`diagramme_EA.txt`** : Diagramme Entité-Association complet
  - Description détaillée de toutes les entités
  - Représentation des associations
  - Diagramme ASCII
  - Notes de conception

- **`schema_relationnel.txt`** : Schéma relationnel en notation textuelle
  - Toutes les tables avec types et contraintes
  - Dépendances fonctionnelles
  - Analyse de normalisation (3FN)
  - Requêtes SQL utiles

- **`README_DATABASE.md`** : Ce fichier - Guide d'utilisation

## 🗄️ Structure de la Base de Données

### Tables Principales

1. **MORPION** : Templates de morpions réutilisables
   - Caractéristiques : vie, attaque, mana, réussite (total = 15)
   - Un morpion peut appartenir à plusieurs équipes

2. **ÉQUIPE** : Équipes de 6 à 8 morpions
   - Identifiée par un nom et une couleur unique

3. **MORPION_EQUIPE** : Table de liaison N:N
   - Associe les morpions aux équipes
   - Conserve l'ordre dans l'équipe

4. **CONFIGURATION** : Paramètres de jeu datés
   - Taille de grille (3x3 ou 4x4)
   - Nombre maximum de tours

5. **PARTIE** : Parties jouées entre deux équipes
   - Stocke les dates de début/fin
   - Référence l'équipe gagnante

6. **JOURNAL** : Historique des actions
   - Une ligne par action pendant la partie
   - Numérotation automatique

### Vues Statistiques

- **v_top_equipes** : Top 3 des équipes avec le plus de victoires
- **v_stats_parties** : Statistiques globales (durée min/max/moyenne)
- **v_journal_par_mois** : Nombre moyen de lignes de journal par mois

## 🚀 Installation et Utilisation

### Prérequis

- PostgreSQL installé
- Accès au serveur : `bd-pedago.univ-lyon1.fr`
- Identifiants de connexion (voir Tomuss)

### Méthode 1 : Via pgweb (Recommandée)

1. Allez sur https://bdw.univ-lyon1.fr/
2. Connectez-vous avec vos identifiants :
   - Serveur : `bd-pedago.univ-lyon1.fr`
   - Utilisateur : `p1234567` (votre numéro étudiant)
   - Mot de passe : (voir colonne `mdp_serveur` sur Tomuss)
   - Base de données : `p1234567`

3. Exécutez le script de création :
```sql
-- Copier-coller le contenu de create_database.sql
```

4. Exécutez le script d'insertion :
```sql
-- Copier-coller le contenu de insert_data.sql
```

5. Changez de schéma :
```sql
SET SEARCH_PATH TO morpion_avance;
```

### Méthode 2 : En ligne de commande avec psql

```bash
# Se connecter au serveur
psql -h bd-pedago.univ-lyon1.fr -U p1234567 -d p1234567 --password

# Une fois connecté, exécuter les scripts
\i create_database.sql
\i insert_data.sql

# Changer de schéma
SET SEARCH_PATH TO morpion_avance;

# Vérifier les tables créées
\dt
```

### Méthode 3 : Via DBeaver ou pgAdmin

1. Créer une nouvelle connexion PostgreSQL
2. Remplir les informations de connexion
3. Ouvrir un éditeur SQL
4. Copier-coller et exécuter `create_database.sql`
5. Copier-coller et exécuter `insert_data.sql`

## ✅ Vérification de l'Installation

### Vérifier que les tables sont créées

```sql
SET SEARCH_PATH TO morpion_avance;

-- Lister les tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'morpion_avance'
ORDER BY table_name;

-- Résultat attendu : 6 tables
-- configuration, equipe, journal, morpion, morpion_equipe, partie
```

### Vérifier les données insérées

```sql
-- Compter les enregistrements
SELECT 'Morpions' AS table_name, COUNT(*) AS nb FROM morpion
UNION ALL
SELECT 'Équipes', COUNT(*) FROM equipe
UNION ALL
SELECT 'Parties', COUNT(*) FROM partie
UNION ALL
SELECT 'Journal', COUNT(*) FROM journal;

-- Résultat attendu :
-- Morpions: 20
-- Équipes: 6
-- Parties: 7
-- Journal: ~20-30 entrées
```

### Tester les vues statistiques

```sql
-- Top 3 des équipes
SELECT * FROM v_top_equipes;

-- Statistiques des parties
SELECT * FROM v_stats_parties;

-- Journal par mois
SELECT * FROM v_journal_par_mois;
```

## 📊 Requêtes Utiles

### Afficher tous les morpions d'une équipe

```sql
SELECT 
    e.nom AS equipe,
    m.nom AS morpion,
    m.points_vie,
    m.points_attaque,
    m.points_mana,
    m.points_reussite,
    me.ordre_dans_equipe
FROM equipe e
JOIN morpion_equipe me ON e.id_equipe = me.id_equipe
JOIN morpion m ON me.id_morpion = m.id_morpion
WHERE e.nom = 'Les Flammes Éternelles'
ORDER BY me.ordre_dans_equipe;
```

### Historique complet d'une partie

```sql
SELECT 
    j.numero_ligne,
    j.date_action,
    j.texte_action
FROM journal j
JOIN partie p ON j.id_partie = p.id_partie
WHERE p.id_partie = 1
ORDER BY j.numero_ligne;
```

### Parties en cours

```sql
SELECT 
    p.id_partie,
    e1.nom AS equipe1,
    e2.nom AS equipe2,
    p.tour_actuel,
    c.taille_grille,
    c.nb_max_tours,
    p.date_debut
FROM partie p
JOIN equipe e1 ON p.id_equipe1 = e1.id_equipe
JOIN equipe e2 ON p.id_equipe2 = e2.id_equipe
JOIN configuration c ON p.id_configuration = c.id_configuration
WHERE p.date_fin IS NULL;
```

### Statistiques d'une équipe

```sql
SELECT 
    e.nom,
    e.couleur,
    COUNT(DISTINCT CASE 
        WHEN p.id_equipe1 = e.id_equipe OR p.id_equipe2 = e.id_equipe 
        THEN p.id_partie 
    END) AS nb_parties_jouees,
    COUNT(DISTINCT CASE 
        WHEN p.id_equipe_gagnante = e.id_equipe 
        THEN p.id_partie 
    END) AS nb_victoires,
    COUNT(DISTINCT me.id_morpion) AS nb_morpions
FROM equipe e
LEFT JOIN partie p ON e.id_equipe IN (p.id_equipe1, p.id_equipe2)
LEFT JOIN morpion_equipe me ON e.id_equipe = me.id_equipe
WHERE e.nom = 'Les Flammes Éternelles'
GROUP BY e.id_equipe, e.nom, e.couleur;
```

### Les morpions les plus forts (par catégorie)

```sql
-- Morpions avec le plus de points de vie
SELECT nom, points_vie, points_attaque, points_mana, points_reussite
FROM morpion
ORDER BY points_vie DESC
LIMIT 5;

-- Morpions avec le plus de points d'attaque
SELECT nom, points_vie, points_attaque, points_mana, points_reussite
FROM morpion
ORDER BY points_attaque DESC
LIMIT 5;

-- Morpions avec le plus de mana
SELECT nom, points_vie, points_attaque, points_mana, points_reussite
FROM morpion
ORDER BY points_mana DESC
LIMIT 5;
```

## 🎮 Données de Test

### Morpions Disponibles (exemples)

- **Dragon Rouge** (4,4,4,3) : Équilibré
- **Guerrier Brutal** (4,7,2,2) : Orientation attaque
- **Archimage** (3,1,8,3) : Orientation magie
- **Gardien Ancien** (8,2,2,3) : Orientation défense
- **Ninja Précis** (2,3,3,7) : Orientation réussite

### Équipes Pré-configurées

1. **Les Flammes Éternelles** (rouge) : 7 morpions, orientation attaque/feu
2. **Les Gardiens de l'Aube** (bleu) : 8 morpions, orientation défense
3. **Les Ombres Silencieuses** (noir) : 6 morpions, orientation furtivité
4. **Les Sages Mystiques** (violet) : 8 morpions, orientation magie
5. **Les Braves Chevaliers** (or) : 7 morpions, équilibrée
6. **Les Forces de la Nature** (vert) : 7 morpions, nature/équilibre

## 🔧 Configuration pour bdw-server

Dans votre fichier `config-bd.toml` :

```toml
POSTGRESQL_SERVER = "bd-pedago.univ-lyon1.fr"
POSTGRESQL_USER = "p1234567"  # Remplacer par votre numéro étudiant
POSTGRESQL_PASSWORD = "votre_mdp"  # Voir Tomuss
POSTGRESQL_DATABASE = "p1234567"  # Remplacer par votre numéro étudiant
POSTGRESQL_SCHEMA = "morpion_avance"  # Schéma du projet
```

## 📝 Pour le Rendu

### Fichiers à inclure dans l'archive

1. **Conception BD** :
   - `diagramme_EA.txt` (ou .pdf si vous créez un diagramme graphique)
   - `schema_relationnel.txt`
   - `create_database.sql`
   - `insert_data.sql`

2. **Code du site web** :
   - Répertoires : `controleurs/`, `model/`, `static/`, `templates/`
   - Fichier `config.toml`
   - Fichier `routes.json`

3. **Affiche** (1 page PDF) :
   - Noms du binôme
   - Diagramme E/A
   - Liste des fonctionnalités
   - Captures d'écran

## 🐛 Dépannage

### Erreur : "schema does not exist"

```sql
CREATE SCHEMA IF NOT EXISTS morpion_avance;
SET SEARCH_PATH TO morpion_avance;
```

### Erreur : "relation already exists"

```sql
-- Supprimer et recréer
DROP SCHEMA morpion_avance CASCADE;
-- Puis réexécuter create_database.sql
```

### Vérifier le schéma actuel

```sql
SHOW search_path;
SELECT current_schema();
```

## 📚 Ressources

- Documentation PostgreSQL : https://www.postgresql.org/docs/
- Page BDW : https://bdw.univ-lyon1.fr/
- pgweb : https://bdw.univ-lyon1.fr/

## 👥 Auteurs

Projet BDW 2025 - UCBL Lyon 1  
Département Informatique

---

**Note** : N'oubliez pas de vérifier que votre équipe a bien entre 6 et 8 morpions avant de créer une partie !

