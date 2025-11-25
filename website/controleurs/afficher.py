from collections import defaultdict

from model.model_pg import execute_select_query
from controleurs.includes import add_activity

add_activity(SESSION['HISTORIQUE'], "consultation des données principales")

connexion = SESSION['CONNEXION']


def fetch_rows(query, params=None):
    """Exécute une requête SELECT et retourne toujours une liste."""
    rows = execute_select_query(connexion, query, params or [])
    return rows if rows is not None else []


# ---------------------------------------------------------------------------
# Morpions disponibles
# ---------------------------------------------------------------------------
morpions_query = """
    SELECT id_morpion, nom, image, points_vie, points_attaque,
           points_mana, points_reussite, date_creation
    FROM morpion
    ORDER BY nom
"""
morpions_cols = (
    "id",
    "nom",
    "image",
    "vie",
    "attaque",
    "mana",
    "reussite",
    "date_creation",
)
REQUEST_VARS["morpions"] = [
    dict(zip(morpions_cols, row)) for row in fetch_rows(morpions_query)
]


# ---------------------------------------------------------------------------
# Équipes + composition
# ---------------------------------------------------------------------------
equipes_query = """
    SELECT id_equipe, nom, couleur, date_creation
    FROM equipe
    ORDER BY nom
"""
membres_query = """
    SELECT me.id_equipe,
           m.nom,
           m.points_vie,
           m.points_attaque,
           m.points_mana,
           m.points_reussite,
           me.ordre_dans_equipe
    FROM morpion_equipe me
    JOIN morpion m ON m.id_morpion = me.id_morpion
    ORDER BY me.id_equipe, me.ordre_dans_equipe
"""
members_map = defaultdict(list)
for row in fetch_rows(membres_query):
    members_map[row[0]].append(
        {
            "nom": row[1],
            "vie": row[2],
            "attaque": row[3],
            "mana": row[4],
            "reussite": row[5],
            "ordre": row[6],
        }
    )

REQUEST_VARS["equipes"] = []
for row in fetch_rows(equipes_query):
    equipe = {
        "id": row[0],
        "nom": row[1],
        "couleur": row[2],
        "date_creation": row[3],
        "morpions": members_map.get(row[0], []),
    }
    REQUEST_VARS["equipes"].append(equipe)


# ---------------------------------------------------------------------------
# Configurations
# ---------------------------------------------------------------------------
config_query = """
    SELECT id_configuration, taille_grille, nb_max_tours,
           somme_caracteristiques, date_creation
    FROM configuration
    ORDER BY date_creation DESC
"""
config_cols = (
    "id",
    "taille_grille",
    "nb_max_tours",
    "somme_caracteristiques",
    "date_creation",
)
REQUEST_VARS["configurations"] = [
    dict(zip(config_cols, row)) for row in fetch_rows(config_query)
]


# ---------------------------------------------------------------------------
# Parties récentes
# ---------------------------------------------------------------------------
parties_query = """
    SELECT p.id_partie,
           e1.nom AS equipe1,
           e2.nom AS equipe2,
           eg.nom AS gagnante,
           p.date_debut,
           p.date_fin,
           p.tour_actuel
    FROM partie p
    JOIN equipe e1 ON e1.id_equipe = p.id_equipe1
    JOIN equipe e2 ON e2.id_equipe = p.id_equipe2
    LEFT JOIN equipe eg ON eg.id_equipe = p.id_equipe_gagnante
    ORDER BY p.date_debut DESC
    LIMIT 5
"""
partie_cols = (
    "id",
    "equipe1",
    "equipe2",
    "gagnante",
    "date_debut",
    "date_fin",
    "tour",
)
REQUEST_VARS["parties"] = [
    dict(zip(partie_cols, row)) for row in fetch_rows(parties_query)
]


# ---------------------------------------------------------------------------
# Journal récent
# ---------------------------------------------------------------------------
journal_query = """
    SELECT j.id_partie, j.numero_ligne, j.date_action, j.texte_action
    FROM journal j
    ORDER BY j.date_action DESC
    LIMIT 5
"""
journal_cols = ("id_partie", "numero", "date_action", "texte")
REQUEST_VARS["journal_recent"] = [
    dict(zip(journal_cols, row)) for row in fetch_rows(journal_query)
]
