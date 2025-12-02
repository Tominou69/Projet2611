

from copy import deepcopy   
from datetime import datetime  

from controleurs.includes import add_activity  
from model.model_pg import execute_select_query   

add_activity(SESSION["HISTORIQUE"], "ouverture de la page partie normale")  

connexion = SESSION["CONNEXION"]   
PARTIES_STATE = SESSION.setdefault("PARTIES_STATE", dict())  # dictionnaire conservé entre les requêtes


def charger_equipes():
     
    rows = execute_select_query(connexion, "SELECT id_equipe, nom, couleur FROM equipe ORDER BY nom", []) or []
    equipes = []  # liste finale
    for row in rows:  # chaque row = (id, nom)
        equipes.append({"id": row[0], "nom": row[1], "couleur": row[2]})  # on convertit en dictionnaire lisible
    return equipes


def charger_morpions_equipe(equipe_id):
     
    rows = execute_select_query(
        connexion,
        """
        SELECT m.id_morpion, m.nom
        FROM morpion m
        JOIN morpion_equipe me ON me.id_morpion = m.id_morpion
        WHERE me.id_equipe = %s
        ORDER BY me.ordre_dans_equipe
        """,
        [equipe_id],
    ) or []
    morpions = []
    for row in rows:
        morpions.append({"id": row[0], "nom": row[1]})  # même logique : conversion tuple -> dict
    return morpions


def initialiser_partie(equipe1_id, equipe2_id, taille_grille, max_tours):
    """
    Crée l'entrée de configuration + l'entrée de partie dans la base,
    puis initialise l'état Python (plateau, messages, etc.).
    """
    eq_rows = execute_select_query(  # on vérifie que les deux équipes existent
        connexion,
        "SELECT id_equipe, nom, couleur FROM equipe WHERE id_equipe IN (%s, %s)",
        [equipe1_id, equipe2_id],
    ) or []
    if len(eq_rows) != 2:  # si l'une des deux équipes est introuvable
        return None, "Impossible de trouver les équipes sélectionnées."

    equipe_infos = {
        row[0]: {"nom": row[1], "couleur": row[2]}
        for row in eq_rows
    }  # dictionnaire rapide {id: infos}
    morpions_eq1 = charger_morpions_equipe(equipe1_id)  # liste des morpions de l'équipe 1
    morpions_eq2 = charger_morpions_equipe(equipe2_id)  # liste des morpions de l'équipe 2
    if len(morpions_eq1) < 1 or len(morpions_eq2) < 1:  # une équipe vide n'a pas de sens
        return None, "Chaque équipe doit avoir au moins un morpion."

    try:
        with connexion.cursor() as cursor:  # toutes les écritures se font dans un curseur
            cursor.execute(  # création de la configuration (taille + nb max de tours)
                """
                INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques)
                VALUES (%s, %s, %s)
                RETURNING id_configuration
                """,
                (taille_grille, max_tours, 15),
            )
            config_id = cursor.fetchone()[0]  # on récupère l'identifiant généré

            cursor.execute(  # création de la partie elle-même
                """
                INSERT INTO partie (id_equipe1, id_equipe2, id_configuration, date_debut, tour_actuel)
                VALUES (%s, %s, %s, NOW(), 1)
                RETURNING id_partie
                """,
                (equipe1_id, equipe2_id, config_id),
            )
            partie_id = cursor.fetchone()[0]  # on garde l'id pour la suite
    except Exception as exc:  # en cas d'erreur SQL, on renvoie le message
        return None, f"Erreur lors de la création de la partie : {exc}"

    plateau = [[None for _ in range(taille_grille)] for _ in range(taille_grille)]  # grille vide
    PARTIES_STATE[partie_id] = {  # on stocke l'état initial dans la session
        "taille": taille_grille,
        "max_tours": max_tours,
        "tour_actuel": 1,
        "cases_jouees": 0,
        "joueur_courant": 1,  # 1 = équipe 1 joue en premier
        "plateau": plateau,
        "equipes": {
            1: {
                "id": equipe1_id,
                "nom": equipe_infos[equipe1_id]["nom"],
                "couleur": equipe_infos[equipe1_id]["couleur"],
                "morpions": morpions_eq1,
            },
            2: {
                "id": equipe2_id,
                "nom": equipe_infos[equipe2_id]["nom"],
                "couleur": equipe_infos[equipe2_id]["couleur"],
                "morpions": morpions_eq2,
            },
        },
        "terminee": False,
        "message": None,
    }
    return partie_id, "La partie a bien été créée. Vous pouvez commencer à jouer."


def verifier_victoire(plateau, joueur):
    """Teste lignes, colonnes et diagonales pour savoir si un joueur a gagné."""
    taille = len(plateau)
    for ligne in plateau:  # test des lignes
        if all(cell and cell["joueur"] == joueur for cell in ligne):
            return True
    for col in range(taille):  # test des colonnes
        if all(plateau[row][col] and plateau[row][col]["joueur"] == joueur for row in range(taille)):
            return True
    if all(plateau[i][i] and plateau[i][i]["joueur"] == joueur for i in range(taille)):  # diagonale principale
        return True
    if all(plateau[i][taille - 1 - i] and plateau[i][taille - 1 - i]["joueur"] == joueur for i in range(taille)):
        return True  # diagonale secondaire
    return False  # aucune victoire détectée


def inserer_journal(partie_id, texte):
    """Ajoute une ligne dans la table journal (on ignore les erreurs pour ne pas bloquer)."""
    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO journal (id_partie, texte_action) VALUES (%s, %s)",
                (partie_id, texte),
            )
    except Exception:
        pass  # erreur silencieuse : la partie peut continuer même si l'écriture échoue


def jouer_un_coup(partie_id, morpion_id, ligne, colonne):
    """Place un morpion sur la grille si la case est libre et met à jour l'état."""
    if partie_id not in PARTIES_STATE:
        return "Partie introuvable."
    etat = PARTIES_STATE[partie_id]  # raccourci
    if etat.get("terminee"):
        return "Cette partie est déjà terminée."

    taille = etat["taille"]
    if not (0 <= ligne < taille and 0 <= colonne < taille):  # case en dehors du plateau
        return "Case invalide."
    if etat["plateau"][ligne][colonne] is not None:  # case déjà occupée
        return "Cette case est déjà occupée."

    joueur = etat["joueur_courant"]
    equipe = etat["equipes"][joueur]
    morpion_trouve = None
    for m in equipe["morpions"]:  # on cherche le morpion choisi dans la liste autorisée
        if m["id"] == morpion_id:
            morpion_trouve = m
            break
    if morpion_trouve is None:
        return "Ce morpion n'appartient pas à votre équipe."

    etat["plateau"][ligne][colonne] = {  # on place concrètement le morpion
        "joueur": joueur,
        "morpion_id": morpion_id,
        "morpion_nom": morpion_trouve["nom"],
        "couleur": etat["equipes"][joueur].get("couleur") or "#111111",
    }
    etat["cases_jouees"] += 1  # on compte les coups
    etat["tour_actuel"] += 1  # on passe au tour suivant (même si la partie se termine ensuite)

    texte = f"{equipe['nom']} place {morpion_trouve['nom']} en ({ligne + 1},{colonne + 1})."
    inserer_journal(partie_id, texte)  # historique persistant

    try:
        with connexion.cursor() as cursor:
            cursor.execute(  # on garde tour_actuel synchro dans la table partie
                "UPDATE partie SET tour_actuel = %s WHERE id_partie = %s",
                (etat["tour_actuel"], partie_id),
            )
    except Exception:
        pass  # si l'UPDATE échoue, on n'empêche pas la partie de continuer

    if verifier_victoire(etat["plateau"], joueur):  # victoire détectée
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
        # soit la limite de tours est atteinte, soit la grille est pleine
        etat["terminee"] = True
        etat["message"] = "La partie est terminée (grille pleine ou tours max atteints)."
        try:
            with connexion.cursor() as cursor:
                cursor.execute("UPDATE partie SET date_fin = NOW() WHERE id_partie = %s", (partie_id,))
        except Exception:
            pass
    else:
        etat["joueur_courant"] = 2 if joueur == 1 else 1  # on alterne l'équipe active
        etat["message"] = "Coup enregistré. À l'autre joueuse !"  # petit feedback utilisateur

    return None  # retourner None signifie “pas d’erreur bloquante”


if POST and "action" in POST:  # on traite les formulaires envoyés depuis parties.html
    action = POST["action"][0]  # valeur de l'input hidden “action”
    if action == "creer":
        equipe1 = int(POST.get("equipe1", ["0"])[0])  # identifiants des équipes
        equipe2 = int(POST.get("equipe2", ["0"])[0])
        taille = int(POST.get("taille", ["3"])[0])  # taille du plateau (3 ou 4)
        max_tours = int(POST.get("max_tours", ["9"])[0])  # limite choisie par l'utilisateur

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
        case = POST.get("case", ["0,0"])[0]  # la case est envoyée sous la forme "ligne,colonne"
        try:
            ligne, colonne = map(int, case.split(","))
        except ValueError:
            ligne = colonne = -1  # valeurs impossibles déclenchant une erreur plus bas
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
            del PARTIES_STATE[partie_id]  # on supprime simplement l'entrée en session
        REQUEST_VARS["message"] = "La partie a été retirée de votre session."
        REQUEST_VARS["message_class"] = "alert-warning"

# données nécessaires au template dans tous les cas
REQUEST_VARS["equipes_disponibles"] = charger_equipes()

# si on recharge la page alors qu'une partie existe encore en session, on la ré-affiche
if REQUEST_VARS.get("partie_courante") is None and PARTIES_STATE:
    pid, state = next(iter(PARTIES_STATE.items()))  # on prend la première partie en cours
    REQUEST_VARS["partie_courante_id"] = pid
    REQUEST_VARS["partie_courante"] = state


