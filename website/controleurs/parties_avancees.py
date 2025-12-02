from controleurs.includes import add_activity  # pour consigner les visites
from model.model_pg import execute_select_query  # passerelle simple vers PostgreSQL

# On consigne immédiatement l'ouverture de la page (utile en soutenance).
add_activity(SESSION["HISTORIQUE"], "ouverture de la page partie avancée")

# Accès rapides vers la connexion PostgreSQL et les structures persistées dans SESSION.
connexion = SESSION["CONNEXION"]
PARTIES_AVANCEES = SESSION.setdefault("PARTIES_AVANCEES", dict())

# Valeurs par défaut pour éviter les KeyError dans le template.
REQUEST_VARS.setdefault("message", "")
REQUEST_VARS.setdefault("message_class", "")
REQUEST_VARS.setdefault("partie_avancee", None)
REQUEST_VARS.setdefault("partie_avancee_id", None)
REQUEST_VARS.setdefault(
    "options_avancees",
    {"reserve": [], "poses": [], "cases_vides": [], "cases_alliees": [], "cases_adverses": []},
)


def charger_equipes():
    """Récupère les équipes disponibles pour alimenter les <select>."""
    lignes = execute_select_query(connexion, "SELECT id_equipe, nom, couleur FROM equipe ORDER BY nom", []) or []
    equipes = []
    for ligne in lignes:
        equipes.append({"id": ligne[0], "nom": ligne[1], "couleur": ligne[2]})
    return equipes


def charger_morpions_complets(equipe_id):
    """Charge les morpions d'une équipe avec toutes les caractéristiques utiles."""
    lignes = execute_select_query(
        connexion,
        """
        SELECT m.id_morpion,
               m.nom,
               m.points_vie,
               m.points_attaque,
               m.points_mana,
               m.points_reussite
        FROM morpion m
        JOIN morpion_equipe me ON me.id_morpion = m.id_morpion
        WHERE me.id_equipe = %s
        ORDER BY me.ordre_dans_equipe
        """,
        [equipe_id],
    ) or []
    morpions = []
    for row in lignes:
        morpions.append(
            {
                "id": row[0],
                "nom": row[1],
                "vie": row[2],
                "attaque": row[3],
                "mana": row[4],
                "reussite": row[5],
            }
        )
    return morpions


def creer_caracteristiques(morpions, numero_equipe):
    """Transforme la liste de morpions en dictionnaire d'état détaillé."""
    caracs = {}
    for morpion in morpions:
        caracs[morpion["id"]] = {
            "nom": morpion["nom"],
            "camp": numero_equipe,
            "vie_max": morpion["vie"],
            "vie": morpion["vie"],
            "attaque": morpion["attaque"],
            "mana": morpion["mana"],
            "mana_restante": morpion["mana"],
            "reussite": morpion["reussite"],
            "etat": "réserve",
            "position": None,
        }
    return caracs


def inserer_journal(partie_id, texte):
    """Ajoute silencieusement une ligne dans la table journal."""
    try:
        with connexion.cursor() as cursor:
            cursor.execute("INSERT INTO journal (id_partie, texte_action) VALUES (%s, %s)", (partie_id, texte))
    except Exception:
        pass


def verifier_victoire(plateau, joueur):
    """Copie simplifiée de la logique de victoire (lignes, colonnes, diagonales)."""
    taille = len(plateau)
    for ligne in plateau:
        if all(case and case["joueur"] == joueur for case in ligne):
            return True
    for col in range(taille):
        if all(plateau[row][col] and plateau[row][col]["joueur"] == joueur for row in range(taille)):
            return True
    if all(plateau[i][i] and plateau[i][i]["joueur"] == joueur for i in range(taille)):
        return True
    if all(plateau[i][taille - 1 - i] and plateau[i][taille - 1 - i]["joueur"] == joueur for i in range(taille)):
        return True
    return False


def initialiser_partie_avancee(equipe1_id, equipe2_id, taille_grille, max_tours):
    """Crée la partie côté base + l'état Python (plateau, caractéristiques, etc.)."""
    equipes_sql = execute_select_query(
        connexion,
        "SELECT id_equipe, nom, couleur FROM equipe WHERE id_equipe IN (%s,%s)",
        [equipe1_id, equipe2_id],
    ) or []
    if len(equipes_sql) != 2:
        return None, "Impossible de trouver les deux équipes."

    eq_infos = {row[0]: {"nom": row[1], "couleur": row[2]} for row in equipes_sql}
    morpions_eq1 = charger_morpions_complets(equipe1_id)
    morpions_eq2 = charger_morpions_complets(equipe2_id)
    if len(morpions_eq1) < 1 or len(morpions_eq2) < 1:
        return None, "Chaque équipe doit avoir des morpions actifs."

    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques)
                VALUES (%s, %s, %s)
                RETURNING id_configuration
                """,
                (taille_grille, max_tours, 15),
            )
            config_id = cursor.fetchone()[0]

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
        return None, f"Impossible de créer la partie avancée : {exc}"

    caracs = {}
    caracs.update(creer_caracteristiques(morpions_eq1, 1))
    caracs.update(creer_caracteristiques(morpions_eq2, 2))

    PARTIES_AVANCEES[partie_id] = {
        "taille": taille_grille,
        "max_tours": max_tours,
        "actions": 0,
        "tour_actuel": 1,
        "joueur_courant": 1,
        "plateau": [[None for _ in range(taille_grille)] for _ in range(taille_grille)],
        "equipes": {
            1: {
                "id": equipe1_id,
                "nom": eq_infos[equipe1_id]["nom"],
                "couleur": eq_infos[equipe1_id]["couleur"],
                "morpions": [{"id": m["id"], "nom": m["nom"]} for m in morpions_eq1],
            },
            2: {
                "id": equipe2_id,
                "nom": eq_infos[equipe2_id]["nom"],
                "couleur": eq_infos[equipe2_id]["couleur"],
                "morpions": [{"id": m["id"], "nom": m["nom"]} for m in morpions_eq2],
            },
        },
        "caracteristiques": caracs,
        "terminee": False,
        "message": "La partie avancée vient de commencer.",
        "journal_local": [],
    }
    return partie_id, "Partie avancée créée. Bonne chance !"


def pousser_etat_vers_template(partie_id):
    """Synchronise REQUEST_VARS avec l'état courant (ou met des valeurs vides)."""
    etat = PARTIES_AVANCEES.get(partie_id)
    if etat:
        REQUEST_VARS["partie_avancee_id"] = partie_id
        REQUEST_VARS["partie_avancee"] = etat
        REQUEST_VARS["options_avancees"] = construire_options_avancees(etat)
    else:
        REQUEST_VARS["partie_avancee_id"] = None
        REQUEST_VARS["partie_avancee"] = None
        REQUEST_VARS["options_avancees"] = {
            "reserve": [],
            "poses": [],
            "cases_vides": [],
            "cases_alliees": [],
            "cases_adverses": [],
        }


def enregistrer_etat_base(partie_id, etat, gagnant=None):
    """Synchronise les colonnes importantes (tour, fin, gagnant) dans la table partie."""
    try:
        with connexion.cursor() as cursor:
            cursor.execute("UPDATE partie SET tour_actuel = %s WHERE id_partie = %s", (etat["tour_actuel"], partie_id))
            if gagnant:
                cursor.execute(
                    """
                    UPDATE partie
                    SET id_equipe_gagnante = %s, date_fin = NOW()
                    WHERE id_partie = %s
                    """,
                    (gagnant, partie_id),
                )
            elif etat["terminee"]:
                cursor.execute("UPDATE partie SET date_fin = NOW() WHERE id_partie = %s", (partie_id,))
    except Exception:
        pass


def construire_options_avancees(etat):
    """Prépare les listes utilisées par le template (cases libres, réserves, etc.)."""
    opts = {"reserve": [], "poses": [], "cases_vides": [], "cases_alliees": [], "cases_adverses": []}
    joueur = etat["joueur_courant"]
    equipe = etat["equipes"][joueur]

    # Réserves et morpions déjà posés.
    for morpion in equipe["morpions"]:
        infos = etat["caracteristiques"][morpion["id"]]
        if infos["etat"] == "réserve":
            opts["reserve"].append({"id": morpion["id"], "nom": infos["nom"]})
        elif infos["etat"] == "sur grille" and infos["position"]:
            pos = infos["position"]
            opts["poses"].append(
                {
                    "id": morpion["id"],
                    "nom": infos["nom"],
                    "position": f"{pos[0] + 1},{pos[1] + 1}",
                    "mana": infos["mana_restante"],
                }
            )

    # Balayage du plateau pour les cases.
    taille = etat["taille"]
    for lig in range(taille):
        for col in range(taille):
            case = etat["plateau"][lig][col]
            if case is None:
                opts["cases_vides"].append({"value": f"{lig},{col}", "label": f"Ligne {lig + 1} - Colonne {col + 1}"})
            else:
                cible = {"value": f"{lig},{col}", "label": f"Ligne {lig + 1} - Colonne {col + 1}", "nom": case["morpion_nom"]}
                if case["joueur"] == joueur:
                    opts["cases_alliees"].append(cible)
                else:
                    opts["cases_adverses"].append(cible)
    return opts


def basculer_joueuse(etat):
    """Passe la main à l'autre équipe."""
    etat["joueur_courant"] = 2 if etat["joueur_courant"] == 1 else 1


def verifier_fin_de_partie(partie_id, etat, joueur):
    """Teste toutes les conditions de fin et met à jour les messages."""
    if verifier_victoire(etat["plateau"], joueur):
        etat["terminee"] = True
        etat["message"] = f"Victoire de {etat['equipes'][joueur]['nom']} !"
        enregistrer_etat_base(partie_id, etat, etat["equipes"][joueur]["id"])
        return True
    if etat["actions"] >= etat["max_tours"] or etat["actions"] >= etat["taille"] ** 2:
        etat["terminee"] = True
        etat["message"] = "Fin de partie : actions ou cases épuisées."
        enregistrer_etat_base(partie_id, etat)
        return True
    return False


def placer_morpion(partie_id, morpion_id, ligne, colonne):
    """Placer un morpion de la réserve sur une case libre."""
    if partie_id not in PARTIES_AVANCEES:
        return "Partie introuvable."
    etat = PARTIES_AVANCEES[partie_id]
    if etat["terminee"]:
        return "La partie est terminée."

    if not (0 <= ligne < etat["taille"] and 0 <= colonne < etat["taille"]):
        return "Case invalide."
    if etat["plateau"][ligne][colonne] is not None:
        return "La case est déjà occupée."

    infos = etat["caracteristiques"].get(morpion_id)
    if not infos or infos["camp"] != etat["joueur_courant"]:
        return "Ce morpion n'appartient pas à votre équipe."
    if infos["etat"] != "réserve":
        return "Ce morpion est déjà en jeu ou KO."

    infos["etat"] = "sur grille"
    infos["position"] = (ligne, colonne)
    etat["plateau"][ligne][colonne] = {
        "joueur": etat["joueur_courant"],
        "morpion_id": morpion_id,
        "morpion_nom": infos["nom"],
        "couleur": etat["equipes"][etat["joueur_courant"]].get("couleur") or "#111111",
    }
    etat["actions"] += 1
    etat["tour_actuel"] += 1
    inserer_journal(partie_id, f"{infos['nom']} est placé en ({ligne + 1},{colonne + 1}).")
    enregistrer_etat_base(partie_id, etat)

    if not verifier_fin_de_partie(partie_id, etat, etat["joueur_courant"]):
        basculer_joueuse(etat)
        etat["message"] = "Placement effectué. À l'autre équipe."
    return None


def lancer_combat(partie_id, morpion_id, ligne_cible, colonne_cible):
    """Gère une attaque entre un morpion posé et une cible ennemie."""
    if partie_id not in PARTIES_AVANCEES:
        return "Partie introuvable."
    etat = PARTIES_AVANCEES[partie_id]
    if etat["terminee"]:
        return "La partie est terminée."

    infos = etat["caracteristiques"].get(morpion_id)
    if not infos or infos["camp"] != etat["joueur_courant"]:
        return "Ce morpion ne vous appartient pas."
    if infos["etat"] != "sur grille" or not infos["position"]:
        return "Ce morpion doit être posé pour attaquer."

    if not (0 <= ligne_cible < etat["taille"] and 0 <= colonne_cible < etat["taille"]):
        return "Cible invalide."
    case = etat["plateau"][ligne_cible][colonne_cible]
    if not case or case["joueur"] == etat["joueur_courant"]:
        return "Il faut viser une case occupée par l'ennemi."

    cible_infos = etat["caracteristiques"][case["morpion_id"]]
    degats = max(1, infos["attaque"])
    cible_infos["vie"] -= degats
    texte = f"{infos['nom']} attaque {cible_infos['nom']} pour {degats} dégâts."
    if cible_infos["vie"] <= 0:
        etat["plateau"][ligne_cible][colonne_cible] = None
        cible_infos["etat"] = "KO"
        cible_infos["position"] = None
        texte += " Le morpion adverse est KO."
    inserer_journal(partie_id, texte)
    etat["journal_local"].append(texte)

    etat["actions"] += 1
    etat["tour_actuel"] += 1
    enregistrer_etat_base(partie_id, etat)

    if not verifier_fin_de_partie(partie_id, etat, etat["joueur_courant"]):
        basculer_joueuse(etat)
        etat["message"] = "Combat enregistré."
    return None


def lancer_sort(partie_id, morpion_id, ligne_cible, colonne_cible):
    """Petit sort de soin qui coûte du mana."""
    if partie_id not in PARTIES_AVANCEES:
        return "Partie introuvable."
    etat = PARTIES_AVANCEES[partie_id]
    if etat["terminee"]:
        return "La partie est terminée."

    lanceur = etat["caracteristiques"].get(morpion_id)
    if not lanceur or lanceur["camp"] != etat["joueur_courant"]:
        return "Ce lanceur ne vous appartient pas."
    if lanceur["etat"] != "sur grille" or not lanceur["position"]:
        return "Le lanceur doit déjà être posé."
    if lanceur["mana_restante"] <= 0:
        return "Ce morpion n'a plus de mana."

    if not (0 <= ligne_cible < etat["taille"] and 0 <= colonne_cible < etat["taille"]):
        return "La case visée est incorrecte."
    case = etat["plateau"][ligne_cible][colonne_cible]
    if not case or case["joueur"] != etat["joueur_courant"]:
        return "Il faut cibler un allié posé."

    cible = etat["caracteristiques"][case["morpion_id"]]
    soin = max(1, lanceur["reussite"] // 2)
    cible["vie"] = min(cible["vie"] + soin, cible["vie_max"])
    lanceur["mana_restante"] -= 1
    texte = f"{lanceur['nom']} soigne {cible['nom']} de {soin} PV."
    inserer_journal(partie_id, texte)
    etat["journal_local"].append(texte)

    etat["actions"] += 1
    etat["tour_actuel"] += 1
    enregistrer_etat_base(partie_id, etat)

    if not verifier_fin_de_partie(partie_id, etat, etat["joueur_courant"]):
        basculer_joueuse(etat)
        etat["message"] = "Sort lancé avec succès."
    return None


# Traitement des formulaires envoyés depuis le template.
if POST and "action" in POST:
    action = POST["action"][0]

    if action == "creer":
        equipe1 = int(POST.get("equipe1", ["0"])[0])
        equipe2 = int(POST.get("equipe2", ["0"])[0])
        taille = int(POST.get("taille", ["3"])[0])
        max_tours = int(POST.get("max_tours", ["12"])[0])

        if equipe1 == equipe2:
            REQUEST_VARS["message"] = "Choisissez deux équipes différentes."
            REQUEST_VARS["message_class"] = "alert-warning"
        elif taille not in (3, 4):
            REQUEST_VARS["message"] = "La grille doit être 3x3 ou 4x4."
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            partie_id, message = initialiser_partie_avancee(equipe1, equipe2, taille, max_tours)
            if partie_id is None:
                REQUEST_VARS["message"] = message
                REQUEST_VARS["message_class"] = "alert-error"
            else:
                pousser_etat_vers_template(partie_id)
                REQUEST_VARS["message"] = message
                REQUEST_VARS["message_class"] = "alert-success"

    elif action == "placer":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        morpion_id = int(POST.get("morpion_id", ["0"])[0])
        case_libre = POST.get("case_libre", ["0,0"])[0]
        try:
            lig, col = map(int, case_libre.split(","))
        except ValueError:
            lig = col = -1
        erreur = placer_morpion(partie_id, morpion_id, lig, col)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        pousser_etat_vers_template(partie_id)

    elif action == "combat":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        morpion_id = int(POST.get("morpion_id", ["0"])[0])
        case_adverse = POST.get("case_adverse", ["0,0"])[0]
        try:
            lig, col = map(int, case_adverse.split(","))
        except ValueError:
            lig = col = -1
        erreur = lancer_combat(partie_id, morpion_id, lig, col)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        pousser_etat_vers_template(partie_id)

    elif action == "sort":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        morpion_id = int(POST.get("morpion_id", ["0"])[0])
        case_alliee = POST.get("case_alliee", ["0,0"])[0]
        try:
            lig, col = map(int, case_alliee.split(","))
        except ValueError:
            lig = col = -1
        erreur = lancer_sort(partie_id, morpion_id, lig, col)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        pousser_etat_vers_template(partie_id)

    elif action == "abandonner":
        partie_id = int(POST.get("partie_id", ["0"])[0])
        if partie_id in PARTIES_AVANCEES:
            del PARTIES_AVANCEES[partie_id]
        REQUEST_VARS["message"] = "Partie avancée retirée de votre session."
        REQUEST_VARS["message_class"] = "alert-warning"
        pousser_etat_vers_template(partie_id)

# Alimente toujours le menu déroulant principal.
REQUEST_VARS["equipes_disponibles"] = charger_equipes()

# Si une partie existe déjà en session, on la renvoie automatiquement au template.
if REQUEST_VARS.get("partie_avancee") is None and PARTIES_AVANCEES:
    pid, etat = next(iter(PARTIES_AVANCEES.items()))
    REQUEST_VARS["partie_avancee_id"] = pid
    REQUEST_VARS["partie_avancee"] = etat
    REQUEST_VARS["options_avancees"] = construire_options_avancees(etat)


