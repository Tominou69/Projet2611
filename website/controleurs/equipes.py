"""
ca c la page du contrôleur de la page /equipes.
"""

from psycopg import Error  

from controleurs.includes import add_activity  
from model.model_pg import execute_select_query  

add_activity(SESSION["HISTORIQUE"], "gestion des équipes") 

connexion = SESSION["CONNEXION"]  # raccourci local vers la connexion numpy psycopg

# Valeurs par défaut utilisées par le template
REQUEST_VARS.setdefault("message", None)  # message affiché dans message.html
REQUEST_VARS.setdefault("message_class", None)  # classe CSS du message
REQUEST_VARS.setdefault("form_values", {"nom": "", "morpions": []})  # champs préremplis du formulaire


MIN_MORPIONS = 6 
MAX_MORPIONS = 8  


def definir_message(text, css_class):
    """Stocke un message flash (succès / avertissement / erreur)."""
    REQUEST_VARS["message"] = text  # que dire
    REQUEST_VARS["message_class"] = css_class  # comment l'afficher (vert/rouge/jaune)


def executer_select(query, params=None):

    rows = execute_select_query(connexion, query, params or [])  
    return rows if rows is not None else []  

def lister_morpions():
    """
    Récupère tous les morpions disponibles pr la liste.
    """
    query = """
        SELECT id_morpion, nom, image, points_vie, points_attaque,
               points_mana, points_reussite
        FROM morpion
        ORDER BY nom
    """
    rows = executer_select(query)  # exécute la requête
    morpions = []  # contiendra la version Python
    for row in rows:  # pour chaque ligne du résultat
        morpions.append( # la g mis appends pr def une liste 
            {
                "id": row[0],  
                "nom": row[1], 
                "image": row[2], 
                "vie": row[3],  
                "attaque": row[4],  
                "mana": row[5], 
                "reussite": row[6],  # pts reussite 
            }
        )
    return morpions  


def lister_equipes():
    """
    Construit une structure (liste de dict) avec les équipes et leurs morpions.

    """
    equipes_rows = executer_select(  # liste des équipes enregistrées
        """
        SELECT id_equipe, nom, date_creation
        FROM equipe
        ORDER BY date_creation DESC
        """
    )
    membres_rows = executer_select(  # liste des associations (équipe, morpion)
        """
        SELECT me.id_equipe, m.nom, me.ordre_dans_equipe
        FROM morpion_equipe me
        JOIN morpion m ON m.id_morpion = me.id_morpion
        ORDER BY me.id_equipe, me.ordre_dans_equipe
        """
    )

    # On regroupe les morpions par équipe avec un simple dictionnaire {id_equipe: [ ... ]}.
    membres_par_equipe = {}  # on prepare un dico, claque clé sera ide avec la liste des morpion
    for row in membres_rows:  
        equipe_id = row[0] 
        if equipe_id not in membres_par_equipe:
            membres_par_equipe[equipe_id] = []  
        membres_par_equipe[equipe_id].append({"nom": row[1], "ordre": row[2]})  # On ajoute un petit dictionnaire contenant le nom du morpion (row[1]) et son ordre (row[2]) dans cette équipe

    equipes = []  # liste creer qui contient dc les equipes 
    for row in equipes_rows:  # on parcourt les équipes
        equipe_id = row[0]  
        equipes.append( # on associe un dico pr chaque equipe, append c pr les liste en python  
            {
                "id": equipe_id,  # identifiant
                "nom": row[1],  # nom
                "date_creation": row[2],  # date de création
                "morpions": membres_par_equipe.get(equipe_id, []),  # liste des morpions trouvée plus haut
            }
        )
    return equipes  # renvoie la liste ds teams


def extraire_morpions_selectionnes(values):
    """
    Transforme la liste de checkbox en liste d'entiers unique.
    """
    ordered_ids = []  # résultat final (dans l'ordre de sélection)
    seen = set()  # sert à éviter les doublons
    for raw_value in values:  # parcours des valeurs reçues depuis le formulaire
        try:
            morpion_id = int(raw_value)  # conversion en entier
        except ValueError:
            continue  # si ce n'est pas un entier on l'ignore
        if morpion_id not in seen:  # on accepte seulement la première occurrence
            seen.add(morpion_id)  # on garde en mémoire qu'on l'a déjà vu
            ordered_ids.append(morpion_id)  # et on l'ajoute à la liste
    return ordered_ids  # renvoie la liste filtrée


def creer_equipe():

    nom = POST.get("nom", [""])[0].strip()
    selected_ids = extraire_morpions_selectionnes(POST.get("morpions", []))

    REQUEST_VARS["form_values"] = {"nom": nom, "morpions": selected_ids}

    if not nom:
        definir_message("Merci de renseigner un nom pour l'équipe.", "alert-warning")
        return

    if len(selected_ids) < MIN_MORPIONS or len(selected_ids) > MAX_MORPIONS:  # vérifie les bornes
        definir_message(
            f"Une équipe doit contenir entre {MIN_MORPIONS} et {MAX_MORPIONS} morpions (actuellement {len(selected_ids)} sélectionnés).",
            "alert-warning",
        )
        return

    try:
        with connexion.cursor() as cursor:  # ouvre un curseur SQL
            cursor.execute(
                "INSERT INTO equipe (nom, couleur) VALUES (%s, %s) RETURNING id_equipe",
                (nom, None),
            )
            new_id = cursor.fetchone()[0]  # récupère l'identifiant créé
            ordre = 1  # ordre d'apparition de chaque morpion dans l'équipe
            for morpion_id in selected_ids:  # on ajoute chaque morpion
                cursor.execute(
                    """
                    INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe)
                    VALUES (%s, %s, %s)
                    """,
                    (new_id, morpion_id, ordre),
                )
                ordre += 1  # on incrémente l'ordre
        definir_message(f"L'équipe « {nom} » a été créée avec succès.", "alert-success")
        REQUEST_VARS["form_values"] = {"nom": "", "morpions": []}  # on vide le formulaire
    except Error as err:
        pg_msg = getattr(err, "pgerror", None) or str(err)
        definir_message(f"Impossible de créer l'équipe : {pg_msg}", "alert-error")


def supprimer_equipe():
    """
    Suppression d'une équipe :
    - on convertit l'identifiant reçu depuis le formulaire
    - on supprime les liens morpion_equipe
    - on supprime l'équipe elle-même (si elle existe encore)
    """
    raw_id = POST.get("equipe_id", [""])[0]  # récupère la valeur envoyée par le formulaire
    try:
        equipe_id = int(raw_id)  # conversion en entier
    except ValueError:
        definir_message("Identifiant d'équipe invalide.", "alert-warning")
        return

    try:
        with connexion.cursor() as cursor:
            cursor.execute("DELETE FROM morpion_equipe WHERE id_equipe = %s", (equipe_id,))
            cursor.execute("DELETE FROM equipe WHERE id_equipe = %s", (equipe_id,))
            if cursor.rowcount == 0:
                definir_message("Équipe introuvable ou déjà supprimée.", "alert-warning")
                return
        definir_message("Équipe supprimée.", "alert-success")
    except Error:
        definir_message(
            "Suppression impossible (l'équipe est peut-être liée à des parties).",
            "alert-error",
        )


if POST and "action" in POST:
    action = POST["action"][0]
    if action == "create":
        creer_equipe()
    elif action == "delete":
        supprimer_equipe()


REQUEST_VARS["morpions"] = lister_morpions()
REQUEST_VARS["morpions_total"] = len(REQUEST_VARS["morpions"])
REQUEST_VARS["morpions_min"] = MIN_MORPIONS
REQUEST_VARS["morpions_max"] = MAX_MORPIONS
REQUEST_VARS["equipes"] = lister_equipes()


