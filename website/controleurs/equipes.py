from collections import defaultdict

from psycopg import Error

from controleurs.includes import add_activity
from model.model_pg import execute_select_query

add_activity(SESSION["HISTORIQUE"], "gestion des équipes")

connexion = SESSION["CONNEXION"]

REQUEST_VARS.setdefault("message", None)
REQUEST_VARS.setdefault("message_class", None)
REQUEST_VARS.setdefault(
    "form_values", {"nom": "", "couleur": "", "morpions": []}
)

MIN_MORPIONS = 6
MAX_MORPIONS = 8


def set_message(text, css_class):
    REQUEST_VARS["message"] = text
    REQUEST_VARS["message_class"] = css_class


def fetch_rows(query, params=None):
    rows = execute_select_query(connexion, query, params or [])
    return rows if rows is not None else []


def get_morpions():
    query = """
        SELECT id_morpion, nom, image, points_vie, points_attaque,
               points_mana, points_reussite
        FROM morpion
        ORDER BY nom
    """
    cols = (
        "id",
        "nom",
        "image",
        "vie",
        "attaque",
        "mana",
        "reussite",
    )
    return [dict(zip(cols, row)) for row in fetch_rows(query)]


def get_equipes():
    equipes_query = """
        SELECT id_equipe, nom, couleur, date_creation
        FROM equipe
        ORDER BY date_creation DESC
    """
    membres_query = """
        SELECT me.id_equipe,
               m.nom,
               me.ordre_dans_equipe
        FROM morpion_equipe me
        JOIN morpion m ON m.id_morpion = me.id_morpion
        ORDER BY me.id_equipe, me.ordre_dans_equipe
    """
    members_map = defaultdict(list)
    for row in fetch_rows(membres_query):
        members_map[row[0]].append(
            {"nom": row[1], "ordre": row[2]}
        )
    equipes = []
    for row in fetch_rows(equipes_query):
        equipe = {
            "id": row[0],
            "nom": row[1],
            "couleur": row[2],
            "date_creation": row[3],
            "morpions": members_map.get(row[0], []),
        }
        equipes.append(equipe)
    return equipes


def parse_selected_morpions(values):
    seen = set()
    ordered = []
    for raw in values:
        try:
            mid = int(raw)
        except ValueError:
            continue
        if mid not in seen:
            seen.add(mid)
            ordered.append(mid)
    return ordered


def handle_creation():
    nom = POST.get("nom", [""])[0].strip()
    couleur = ""
    selected_ids = parse_selected_morpions(POST.get("morpions", []))

    REQUEST_VARS["form_values"] = {
        "nom": nom,
        "couleur": couleur,
        "morpions": selected_ids,
    }

    if not nom:
        set_message("Merci de renseigner un nom pour l'équipe.", "alert-warning")
        return

    if len(selected_ids) < MIN_MORPIONS or len(selected_ids) > MAX_MORPIONS:
        set_message(
            f"Une équipe doit contenir entre {MIN_MORPIONS} et {MAX_MORPIONS} morpions (actuellement {len(selected_ids)} sélectionnés).",
            "alert-warning",
        )
        return

    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO equipe (nom, couleur) VALUES (%s, %s) RETURNING id_equipe",
                (nom, None),
            )
            new_id = cursor.fetchone()[0]
            ordre = 1
            for mid in selected_ids:
                cursor.execute(
                    """
                    INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe)
                    VALUES (%s, %s, %s)
                    """,
                    (new_id, mid, ordre),
                )
                ordre += 1
        set_message(
            f"L'équipe « {nom} » a été créée avec succès.",
            "alert-success",
        )
        REQUEST_VARS["form_values"] = {"nom": "", "couleur": "", "morpions": []}
    except Error as err:
        pg_msg = getattr(err, "pgerror", None) or str(err)
        set_message(
            f"Impossible de créer l'équipe : {pg_msg}",
            "alert-error",
        )


def handle_deletion():
    equipe_id = POST.get("equipe_id", [""])[0]
    try:
        equipe_id = int(equipe_id)
    except ValueError:
        set_message("Identifiant d'équipe invalide.", "alert-warning")
        return

    try:
        with connexion.cursor() as cursor:
            cursor.execute("DELETE FROM morpion_equipe WHERE id_equipe = %s", (equipe_id,))
            cursor.execute("DELETE FROM equipe WHERE id_equipe = %s", (equipe_id,))
            if cursor.rowcount == 0:
                set_message("Équipe introuvable ou déjà supprimée.", "alert-warning")
                return
        set_message("Équipe supprimée.", "alert-success")
    except Error as err:
        set_message(
            "Suppression impossible (l'équipe est peut-être liée à des parties).",
            "alert-error",
        )


if POST and "action" in POST:
    action = POST["action"][0]
    if action == "create":
        handle_creation()
    elif action == "delete":
        handle_deletion()


morpions = get_morpions()
REQUEST_VARS["morpions"] = morpions
REQUEST_VARS["morpions_total"] = len(morpions)
REQUEST_VARS["morpions_min"] = MIN_MORPIONS
REQUEST_VARS["morpions_max"] = MAX_MORPIONS
REQUEST_VARS["equipes"] = get_equipes()


