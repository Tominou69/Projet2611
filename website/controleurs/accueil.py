from datetime import timedelta

from controleurs.includes import add_activity
from model.model_pg import execute_select_query

add_activity(SESSION["HISTORIQUE"], "consultation de l'accueil")

connexion = SESSION["CONNEXION"]


def fetch_rows(query, params=None):
    """Exécute une requête SELECT et retourne toujours une liste."""
    rows = execute_select_query(connexion, query, params or [])
    return rows if rows is not None else []


def fetch_scalar(query, params=None, default=0):
    """Retourne la première valeur du premier enregistrement."""
    rows = fetch_rows(query, params)
    return rows[0][0] if rows else default


def humanize_duration(seconds):
    """Convertit une durée en secondes vers une représentation lisible."""
    if seconds is None:
        return "—"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours} h")
    if minutes:
        parts.append(f"{minutes} min")
    if secs or not parts:
        parts.append(f"{secs} s")
    return " ".join(parts)


def fetch_partie_by_duration(order_clause):
    """Récupère la partie la plus courte/longue selon l'ordre passé."""
    query = f"""
        SELECT p.id_partie,
               e1.nom AS equipe1,
               e2.nom AS equipe2,
               EXTRACT(EPOCH FROM (p.date_fin - p.date_debut))::INTEGER AS duree_sec,
               p.date_fin
        FROM partie p
        JOIN equipe e1 ON e1.id_equipe = p.id_equipe1
        JOIN equipe e2 ON e2.id_equipe = p.id_equipe2
        WHERE p.date_fin IS NOT NULL
        ORDER BY duree_sec {order_clause}
        LIMIT 1
    """
    rows = fetch_rows(query)
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row[0],
        "affiche": f"{row[1]} vs {row[2]}",
        "duree": humanize_duration(row[3]),
        "date_fin": row[4],
    }


# ---------------------------------------------------------------------------
# Comptages simples
# ---------------------------------------------------------------------------
REQUEST_VARS["table_counts"] = [
    {"label": "Morpions", "value": fetch_scalar("SELECT COUNT(*) FROM morpion")},
    {"label": "Équipes", "value": fetch_scalar("SELECT COUNT(*) FROM equipe")},
    {"label": "Parties", "value": fetch_scalar("SELECT COUNT(*) FROM partie")},
]


# ---------------------------------------------------------------------------
# Top 3 des équipes
# ---------------------------------------------------------------------------
top_equipes_query = """
    SELECT e.nom,
           e.couleur,
           COALESCE(COUNT(p.id_partie), 0) AS victoires
    FROM equipe e
    LEFT JOIN partie p ON p.id_equipe_gagnante = e.id_equipe
    GROUP BY e.id_equipe, e.nom, e.couleur
    ORDER BY victoires DESC, e.nom ASC
    LIMIT 3
"""
REQUEST_VARS["top_equipes"] = [
    {"nom": row[0], "couleur": row[1], "victoires": row[2]}
    for row in fetch_rows(top_equipes_query)
]


# ---------------------------------------------------------------------------
# Parties la plus rapide et la plus longue
# ---------------------------------------------------------------------------
REQUEST_VARS["partie_plus_rapide"] = fetch_partie_by_duration("ASC")
REQUEST_VARS["partie_plus_longue"] = fetch_partie_by_duration("DESC")


# ---------------------------------------------------------------------------
# Journalisation par mois
# ---------------------------------------------------------------------------
journal_query = """
    SELECT annee, mois, nb_lignes_total, nb_parties, nb_moyen_lignes
    FROM v_journal_par_mois
    ORDER BY annee DESC, mois DESC
"""
REQUEST_VARS["journal_stats"] = [
    {
        "annee": int(row[0]),
        "mois": int(row[1]),
        "nb_lignes": int(row[2]),
        "nb_parties": int(row[3]),
        "nb_moyen": round(float(row[4]), 2),
    }
    for row in fetch_rows(journal_query)
]


