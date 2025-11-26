"""
Contrôleur pour la fonctionnalité "partie normale".
Le but est d'avoir un code simple et commenté, adapté à un niveau L2.
"""

from copy import deepcopy  # pour cloner facilement la grille
from datetime import datetime

from controleurs.includes import add_activity
from model.model_pg import execute_select_query

add_activity(SESSION["HISTORIQUE"], "ouverture de la page partie normale")

connexion = SESSION["CONNEXION"]  # connexion PostgreSQL fournie par le serveur

# petit raccourci pour les états de partie conservés en session
PARTIES_STATE = SESSION.setdefault("PARTIES_STATE", dict())


def executer_select(query, params=None):
    """Enveloppe simple pour récupérer une liste depuis la base."""
    rows = execute_select_query(connexion, query, params or [])
    return rows if rows else []


def charger_equipes():
    """Retourne la liste de toutes les équipes avec leur identifiant et leur nom."""
    rows = executer_select("SELECT id_equipe, nom FROM equipe ORDER BY nom")
    equipes = []
    for row in rows:
        equipes.append({"id": row[0], "nom": row[1]})
    return equipes


def charger_morpions_equipe(equipe_id):
    """Récupère les morpions associés à une équipe donnée."""
    rows = executer_select(
        """
        SELECT m.id_morpion, m.nom
        FROM morpion m
        JOIN morpion_equipe me ON me.id_morpion = m.id_morpion
        WHERE me.id_equipe = %s
        ORDER BY me.ordre_dans_equipe
        """,
        [equipe_id],
    )
    morpions = []
    for row in rows:
        morpions.append({"id": row[0], "nom": row[1]})
    return morpions


def initialiser_partie(equipe1_id, equipe2_id, taille_grille, max_tours):
    """Création de la configuration + de la partie en base, puis stockage en session."""
    # récupération des informations des équipes
    eq_rows = executer_select(
        "SELECT id_equipe, nom FROM equipe WHERE id_equipe IN (%s, %s)",
        [equipe1_id, equipe2_id],
    )
    if len(eq_rows) != 2:
        return None, "Impossible de trouver les équipes sélectionnées."

    equipe_infos = {row[0]: row[1] for row in eq_rows}
    morpions_eq1 = charger_morpions_equipe(equipe1_id)
    morpions_eq2 = charger_morpions_equipe(equipe2_id)
    if len(morpions_eq1) < 1 or len(morpions_eq2) < 1:
        return None, "Chaque équipe doit avoir au moins un morpion."

    try:
        with connexion.cursor() as cursor:
            # on crée une configuration dédiée, plus simple pour filtrer ensuite
            cursor.execute(
                """
                INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques)
                VALUES (%s, %s, %s)
                RETURNING id_configuration
                """,
                (taille_grille, max_tours, 15),
            )
            config_id = cursor.fetchone()[0]

            # on crée la partie
            cursor.execute(
                """
                INSERT INTO partie (id_equipe1, id_equipe2, id_configuration, date_debut, tour_actuel)
                VALUES (%s, %s, %s, NOW(), 1)
                RETURNING id_partie
                """,
                (equipe1_id, equipe2_id, config_id),
            )
            partie_id = cursor.fetchone()[0]
    except Exception as exc:
        return None, f"Erreur lors de la création de la partie : {exc}"

    # on prépare un plateau vide (liste de listes remplie de None)
    plateau = [[None for _ in range(taille_grille)] for _ in range(taille_grille)]
    PARTIES_STATE[partie_id] = {
        "taille": taille_grille,
        "max_tours": max_tours,
        "tour_actuel": 1,
        "cases_jouees": 0,
        "joueur_courant": 1,  # 1 pour équipe 1, 2 pour équipe 2
        "plateau": plateau,
        "equipes": {
            1: {"id": equipe1_id, "nom": equipe_infos[equipe1_id], "morpions": morpions_eq1},
            2: {"id": equipe2_id, "nom": equipe_infos[equipe2_id], "morpions": morpions_eq2},
        },
        "terminee": False,
        "message": None,
    }
    return partie_id, "La partie a bien été créée. Vous pouvez commencer à jouer."


def verifier_victoire(plateau, joueur):
    """Retourne True si le joueur a une ligne/colonne/diagonale complète."""
    taille = len(plateau)

    # lignes
    for ligne in plateau:
        if all(cell and cell["joueur"] == joueur for cell in ligne):
            return True
    # colonnes
    for col in range(taille):
        if all(plateau[row][col] and plateau[row][col]["joueur"] == joueur for row in range(taille)):
            return True
    # diagonales
    if all(plateau[i][i] and plateau[i][i]["joueur"] == joueur for i in range(taille)):
        return True
    if all(plateau[i][taille - 1 - i] and plateau[i][taille - 1 - i]["joueur"] == joueur for i in range(taille)):
        return True
    return False


def inserer_journal(partie_id, texte):
    """Ajoute une entrée dans la table journal pour tracer le coup."""
    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO journal (id_partie, texte_action)
                VALUES (%s, %s)
                """,
                (partie_id, texte),
            )
    except Exception:
        pass  # en cas d'erreur, on ignore pour ne pas bloquer la partie


def jouer_un_coup(partie_id, morpion_id, ligne, colonne):
    """Gère un coup : place un morpion si la case est vide et vérifie l'état."""
    if partie_id not in PARTIES_STATE:
        return "Partie introuvable."
    etat = PARTIES_STATE[partie_id]
    if etat.get("terminee"):
        return "Cette partie est déjà terminée."

    taille = etat["taille"]
    if not (0 <= ligne < taille and 0 <= colonne < taille):
        return "Case invalide."
    if etat["plateau"][ligne][colonne] is not None:
        return "Cette case est déjà occupée."

    joueur = etat["joueur_courant"]
    equipe = etat["equipes"][joueur]
    # on vérifie que le morpion choisi appartient bien à l'équipe du joueur courant
    morpion_trouve = None
    for m in equipe["morpions"]:
        if m["id"] == morpion_id:
            morpion_trouve = m
            break
    if morpion_trouve is None:
        return "Ce morpion n'appartient pas à votre équipe."

    # on place la valeur dans le plateau
    etat["plateau"][ligne][colonne] = {
        "joueur": joueur,
        "morpion_id": morpion_id,
        "morpion_nom": morpion_trouve["nom"],
    }
    etat["cases_jouees"] += 1
    etat["tour_actuel"] += 1

    # on insère une ligne dans le journal
    texte = f"{equipe['nom']} place {morpion_trouve['nom']} en ({ligne + 1},{colonne + 1})."
    inserer_journal(partie_id, texte)

    # on met à jour tour_actuel en base
    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                "UPDATE partie SET tour_actuel = %s WHERE id_partie = %s",
                (etat["tour_actuel"], partie_id),
            )
    except Exception:
        pass

    # vérification des conditions d'arrêt
    if verifier_victoire(etat["plateau"], joueur):
        etat["terminee"] = True
        etat["message"] = f"Victoire de {equipe['nom']} !"
        try:
            with connexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE partie
                    SET id_equipe_gagnante = %s, date_fin = NOW()
                    WHERE id_partie = %s
                    """,
                    (equipe["id"], partie_id),
                )
        except Exception:
            pass
    elif etat["cases_jouees"] >= etat["max_tours"] or etat["cases_jouees"] >= etat["taille"] ** 2:
        etat["terminee"] = True
        etat["message"] = "La partie est terminée (grille pleine ou tours max atteints)."
        try:
            with connexion.cursor() as cursor:
                cursor.execute(
                    "UPDATE partie SET date_fin = NOW() WHERE id_partie = %s",
                    (partie_id,),
                )
        except Exception:
            pass
    else:
        # on passe la main à l'autre joueur
        etat["joueur_courant"] = 2 if joueur == 1 else 1
        etat["message"] = "Coup enregistré. À l'autre joueuse !"

    return None  # pas d'erreur


# ---------------------------------------------------------------------------
# Gestion des requêtes
# ---------------------------------------------------------------------------
if POST and "action" in POST:
    action = POST["action"][0]
    if action == "creer":
        equipe1 = int(POST.get("equipe1", ["0"])[0])
        equipe2 = int(POST.get("equipe2", ["0"])[0])
        taille = int(POST.get("taille", ["3"])[0])
        max_tours = int(POST.get("max_tours", ["9"])[0])

        if equipe1 == equipe2:
            REQUEST_VARS["message"] = "Choisissez deux équipes différentes."
            REQUEST_VARS["message_class"] = "alert-warning"
        elif taille not in (3, 4):
            REQUEST_VARS["message"] = "La grille doit être de taille 3 ou 4."
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            partie_id, msg = initialiser_partie(equipe1, equipe2, taille, max_tours)
            if partie_id is None:
                REQUEST_VARS["message"] = msg
                REQUEST_VARS["message_class"] = "alert-error"
            else:
                REQUEST_VARS["message"] = msg
                REQUEST_VARS["message_class"] = "alert-success"
                REQUEST_VARS["partie_courante"] = PARTIES_STATE.get(partie_id)
                REQUEST_VARS["partie_courante_id"] = partie_id

    elif action == "jouer":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        morpion_id = int(POST.get("morpion_id", ["0"])[0])
        case = POST.get("case", ["0,0"])[0]
        try:
            ligne, colonne = map(int, case.split(","))
        except ValueError:
            ligne = colonne = -1
        erreur = jouer_un_coup(partie_id, morpion_id, ligne, colonne)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_STATE[partie_id].get("message")
            REQUEST_VARS["message_class"] = (
                "alert-success" if PARTIES_STATE[partie_id].get("terminee") else "alert-success"
            )
        REQUEST_VARS["partie_courante"] = PARTIES_STATE.get(partie_id)
        REQUEST_VARS["partie_courante_id"] = partie_id

    elif action == "abandonner":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        if partie_id in PARTIES_STATE:
            del PARTIES_STATE[partie_id]
        REQUEST_VARS["message"] = "La partie a été retirée de votre session."
        REQUEST_VARS["message_class"] = "alert-warning"


# données communes nécessaires au template
REQUEST_VARS["equipes_disponibles"] = charger_equipes()

# on passe aussi l'état courant (s'il existe) pour afficher le plateau
if REQUEST_VARS.get("partie_courante") is None and PARTIES_STATE:
    # on récupère la première partie en cours (dans ce projet on n'en gère qu'une à la fois)
    pid, state = next(iter(PARTIES_STATE.items()))
    REQUEST_VARS["partie_courante_id"] = pid
    REQUEST_VARS["partie_courante"] = state


