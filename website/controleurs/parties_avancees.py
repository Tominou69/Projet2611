from model.model_pg import execute_select_query
import random

# setdefault 
# recuperer la valeur d’une clé, et si la clé n’existe pas, à la créer avec une valeur par défaut.
connexion = SESSION["CONNEXION"]
PARTIES_AVANCEES = SESSION.setdefault("PARTIES_AVANCEES", {})

# setdefault : i "PARTIES_AVANCEES" existe dans la session → tu l’utilises
# sinon → tu créés un dictionnaire vide, puis tu l’enregistres dans la session

REQUEST_VARS.setdefault("message", "")
REQUEST_VARS.setdefault("message_class", "") # pr les mess
REQUEST_VARS.setdefault("partie_avancee", None)
REQUEST_VARS.setdefault("partie_avancee_id", None)

#stockent l’ID de la partie en cours
#stockent la description de la partie courante (l’état complet)

REQUEST_VARS.setdefault("options_sort", {"lanceurs": [], "cibles": [], "allies": []})

# Ici tu prépares un “panier de données” pour l’interface de lancement de sorts

""" fonction qui va lire les equipes existantes dans la base de donnees """

def charger_equipes():
    rows = execute_select_query(connexion, "SELECT id_equipe, nom, couleur FROM equipe ORDER BY nom", []) or []
    return [{"id": row[0], "nom": row[1], "couleur": row[2]} for row in rows] # for row in row :parocurs  lignes de la requete SQL


# Exemple : (3, "Les Flèches", "#ff0000") devient {"id": 3, "nom": "Les Flèches", "couleur": "#ff0000"}.








""" fonction qui prend en entree l'id dune equipe et retourne les morpions de cette equipe """ 

#%s cest pour indiquer "met la valeur foruni en parametre"

def charger_morpions_complets(equipe_id):
    rows = execute_select_query(
        connexion,
        """
        SELECT m.id_morpion, m.nom, m.points_vie, m.points_attaque,
               m.points_mana, m.points_reussite
        FROM morpion m
        JOIN morpion_equipe me ON me.id_morpion = m.id_morpion
        WHERE me.id_equipe = %s 
        ORDER BY me.ordre_dans_equipe
        """,
        [equipe_id],
    ) or []
    data = []  
    for row in rows: # on parcourt les lignes de la requete SQL
        data.append({
            "id": row[0],
            "nom": row[1],
            "vie": row[2],
            "attaque": row[3],
            "mana": row[4],
            "reussite": row[5],
        })
    return data

# l interet de cette fonction est de convertir les lignes sql en structure python pour pouvoir les utiliser dans le template






""" fonction qui transforme la liste des morpions en un dictionnaire des caracteristiques """

def creer_caracs(morpions, camp):
    caracs = {} # on prepare un dictionnaire vide pour stocker les caracteristique
    for m in morpions: # m est un dicto avec id nom mana 
        instance_id = f"{camp}-{m['id']}"  # identifiant unique par équipe
        m["instance_id"] = instance_id  # on mémorise cet id pour les menus déroulants
        caracs[instance_id] = {  # on crée une entrée dans le dictionnaire final caracs
            "nom": m["nom"],
            "camp": camp, # car camp nest pas dans morpion 
            "etat": "reserve",
            "position": None,
            "mana_max": m["mana"],
            "mana_restante": m["mana"],
            "vie_max": m["vie"],
            "vie_actuelle": m["vie"],
            "attaque": m["attaque"],
            "reussite": m["reussite"],
        }
    return caracs

# par exemple on aura : 5 : { nom : ..., camp : ..., etat : ..., position : ..., mana : ..., mana_restante : ...}


#.get : recuper la valeur associée a une clé "reussite" dans le idctionnaire carac 
"""carac est chaque dico decrivant un morpion"""

def action_reussie(carac):
    chance = carac.get("reussite", 1) * 10  
    tirage = random.randint(0, 100) # randit pour tirer un nombre aleatoire entre 0 et 100
    return tirage < chance




def retirer_morpion_du_plateau(etat, morpion_id):
    """Marque un morpion comme KO et libère sa case."""
    carac = etat["caracteristiques"][morpion_id] # va ds les caracteristique et donne moi le dico entier du morpion id
    carac["position"] = None  # on note qu'il est hors jeu et qu'il n'a plus de coordonne 

    # On supprime sa présence sur le plateau
    for lig in range(etat["taille"]): # on parcourt toutes les lignes de la grille
        for col in range(etat["taille"]): # on parcourt toutes les colonnes de la grille
            case = etat["plateau"][lig][col] 
            if case and case.get("morpion_id") == morpion_id: # si la case est occupée par le morpion a retirer
                etat["plateau"][lig][col] = None # on la vide


# interet de get : peut renvoyer none si la clé n'existe pas

def verifier_elimination(etat, camp_adverse):
    """Vérifie si l'équipe adverse n'a plus de morpions en vie."""
    for carac in etat["caracteristiques"].values():
        if carac["camp"] == camp_adverse and carac["etat"] != "KO":
            return False
    return True

"""carac est chaque dico decrivant un morpion"""

# utile pr lancer sort magique

def conclure_action(etat, partie_id, texte):
    """Enregistrer le texte, avancer les compteurs et tester les fins de partie."""
    inserer_journal(partie_id, texte)  # on note l'action dans le journal
    etat["message"] = texte  # message affiché sur la page
    etat["actions"] += 1  # on compte l'action
    etat["tour_actuel"] += 1  # on incrémente le numéro de tour

    joueur = etat["joueur_courant"]
    equipe = etat["equipes"][joueur]
    # vérification des fins possibles après l'action
    gagnante_id = None
    if verifier_victoire(etat["plateau"], joueur):
        etat["terminee"] = True
        etat["message"] = f"Victoire de {equipe['nom']} !"
        gagnante_id = equipe["id"]
    elif verifier_elimination(etat, 2 if joueur == 1 else 1):
        etat["terminee"] = True
        etat["message"] = f"Tous les morpions adverses sont éliminés. {equipe['nom']} gagne."
        gagnante_id = equipe["id"]
    elif etat["actions"] >= etat["max_tours"] or etat["actions"] >= etat["taille"] ** 2:
        etat["terminee"] = True
        etat["message"] = "Fin de partie (tours ou cases épuisés)."
    else:
        basculer_tour(etat)  # on passe la main à l'autre équipe si la partie continue
    # mise à jour de la table partie pour refléter l'état actuel
    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                "UPDATE partie SET tour_actuel = %s WHERE id_partie = %s",
                (etat["tour_actuel"], partie_id),
            )
            if etat["terminee"]:
                cursor.execute(
                    """
                    UPDATE partie
                    SET id_equipe_gagnante = %s,
                        date_fin = CURRENT_TIMESTAMP
                    WHERE id_partie = %s
                    """,
                    (gagnante_id, partie_id),
                )
                connexion.commit()
    except Exception:
        connexion.rollback()
        pass  # si la mise à jour échoue, on n'empêche pas la partie de continuer
    return None


def basculer_tour(etat):
    """Passe au joueur suivant."""
    etat["joueur_courant"] = 2 if etat["joueur_courant"] == 1 else 1



#lire_coordonnees sert à prendre la valeur envoyée par les formulaires 
#(format texte "ligne,colonne") et à la transformer en deux entiers sûrs (ligne, colonne) 
#pour le contrôleur. C’est utilisé partout où on doit cibler une case (combat, sorts, quiz).


def lire_coordonnees(texte, taille):
    """Convertit 'lig,col' en entiers et vérifie les bornes."""
    try: # try exept pour gerer les cas ou la valeur nesr pas un nb
        lig, col = map(int, (texte or "").split(",")) # or " " pr avoir une chaine vide
        # map int pr appliquer int  a chaucn des morceau 
    except ValueError:
        return None, None, "Case invalide."
    if not (0 <= lig < taille and 0 <= col < taille): 
        return None, None, "Case invalide."
    return lig, col, None # none pr dire que y a aucune erreur 


def rafraichir_partie_active(partie_id):
    """Met à jour les variables REQUEST_VARS avec la partie courante."""
    REQUEST_VARS["partie_avancee"] = PARTIES_AVANCEES.get(partie_id) # va ds le dico partie avancee et recuperer partie id
    REQUEST_VARS["partie_avancee_id"] = partie_id







# Fonction : créer une nouvelle partie avancée (config + enregistrement en mémoire).
def initialiser_partie_avancee(equipe1_id, equipe2_id, taille_grille, max_tours):
    eq_rows = execute_select_query(
        connexion,
        "SELECT id_equipe, nom, couleur FROM equipe WHERE id_equipe IN (%s,%s)",
        [equipe1_id, equipe2_id],
    ) or []
    if len(eq_rows) != 2:
        return None, "Impossible de trouver les deux équipes."

    infos = {row[0]: {"nom": row[1], "couleur": row[2]} for row in eq_rows}
     # car eq rows conteint duex lignes 
    morpions_eq1 = charger_morpions_complets(equipe1_id)
    morpions_eq2 = charger_morpions_complets(equipe2_id)
    if not morpions_eq1 or not morpions_eq2:
        return None, "Chaque équipe doit avoir au moins un morpion."

    try:
        with connexion.cursor() as cursor: # on ouvre un curseur sql pour executer les requetes SQL
            cursor.execute(
                """
                INSERT INTO configuration (taille_grille, nb_max_tours, somme_caracteristiques)
                VALUES (%s, %s, %s)
                RETURNING id_configuration
                """,
                (taille_grille, max_tours, 15),
            )
            config_id = cursor.fetchone()[0] 
            
            
# fetchone() récupère la première ligne de la requête (un tuple), 
# et [0] prend la première colonne, c’est-à-dire l’id. On stocke ce nombre dans config_id.





            cursor.execute(
                """
                INSERT INTO partie (id_equipe1, id_equipe2, id_configuration, tour_actuel)
                VALUES (%s, %s, %s, 1)
                RETURNING id_partie
                """,
                (equipe1_id, equipe2_id, config_id),
            )
            partie_id = cursor.fetchone()[0] 

            #  PostgreSQL renvoie une ligne contenant l’identifiant de la partie qu’on vient de créer. fetchone() récupère cette ligne (un tuple), 
            #et [0] prend la première colonne, c’est-à-dire l’id. On stocke ce nombre dans partie_id.
    except Exception as exc:
        return None, f"Erreur lors de la création : {exc}"



    caracs = {} # on prepare un dictionnaire vide pour stocker l etat des morpions engager dans la partie 
    caracs.update(creer_caracs(morpions_eq1, 1))
    caracs.update(creer_caracs(morpions_eq2, 2))

    # update ajoute tte les paires de valeru retoruner par creer_caracs dans le dictionnaire caracs

    # On ajoute maintenant une entrée dans PARTIES_AVANCEES.
    # La clé est l'identifiant de la partie, et la valeur est un dictionnaire
    # qui décrit tout l'état courant de cette partie.
    PARTIES_AVANCEES[partie_id] = {
        "taille": taille_grille,
        "max_tours": max_tours,
        "tour_actuel": 1,
        "actions": 0,
        "joueur_courant": 1, #cest lequipe 1 qui commence 

        # plateau est une grille vide de taille taille_grille x taille_grille. Rempli de none car plateau vide.
        # none for .. creer une ligne de taille grille case toute a none 
        # on repete laction taille_grille fois pour chaque ligne et colonne
        "plateau": [[None for _ in range(taille_grille)] for _ in range(taille_grille)],

        #on stocke les infos sur les deux equipes 
        "equipes": {
            1: {"id": equipe1_id, "nom": infos[equipe1_id]["nom"], "couleur": infos[equipe1_id]["couleur"], "morpions": morpions_eq1},
            2: {"id": equipe2_id, "nom": infos[equipe2_id]["nom"], "couleur": infos[equipe2_id]["couleur"], "morpions": morpions_eq2},
        },
        "caracteristiques": caracs, # reference vers le dico caracs preparer avant pr suivre letat des morpions
        "terminee": False,
        "message": "Partie avancée prête. Placez un morpion.",
    }
    return partie_id, "La partie avancée a bien été créée."











# fonction qui verifie si une equipe a gagne la partie

# Fonction : vérifier si une équipe a aligné toute une ligne, colonne ou diagonale.
def verifier_victoire(plateau, joueur):
    taille = len(plateau)  # taille de la grille (3 ou 4)

    for ligne in plateau:  # vérifie ligne par ligne
        # si toutes les cases de la ligne appartiennent au même joueur -> victoire
        if all(cell and cell["joueur"] == joueur for cell in ligne):
            return True

    for col in range(taille):  # vérifie colonne par colonne
        if all(plateau[row][col] and plateau[row][col]["joueur"] == joueur for row in range(taille)):
            return True
# row ce sont les lignes
    # diagonale principale (haut gauche -> bas droite)
    if all(plateau[i][i] and plateau[i][i]["joueur"] == joueur for i in range(taille)):
        return True

    # diagonale secondaire (haut droite -> bas gauche)
    if all(plateau[i][taille - 1 - i] and plateau[i][taille - 1 - i]["joueur"] == joueur for i in range(taille)):
        return True

    return False


# Fonction : ajouter une ligne dans la table journal sans bloquer la partie en cas d'erreur SQL.
def inserer_journal(partie_id, texte):
    try: #On entoure les instructions SQL d’un try pour éviter qu’une erreur casse la partie
        with connexion.cursor() as cursor: # on ouvre un curseur sql pour executer les requetes SQL
            cursor.execute("INSERT INTO journal (id_partie, texte_action) VALUES (%s, %s)", (partie_id, texte))
    except Exception:
        pass # si l'INSERT échoue, on n'empêche pas la partie de continuer



"""gere tout le cycle placer un morpion sur la grille"""

def jouer_un_coup_avance(partie_id, morpion_id, ligne, colonne):
    if partie_id not in PARTIES_AVANCEES:
        return "Partie introuvable."
    etat = PARTIES_AVANCEES[partie_id]
    if etat["terminee"]:
        return "Cette partie est déjà terminée."
    taille = etat["taille"]
    if not (0 <= ligne < taille and 0 <= colonne < taille):
        return "Case invalide."
    case = etat["plateau"][ligne][colonne]
    if case is not None:
        return "Cette case est déjà occupée."
    carac = etat["caracteristiques"].get(morpion_id) # avoir tt les infos du morpion que l on veut jouer
    if not carac or carac["camp"] != etat["joueur_courant"]:
        return "Ce morpion n'appartient pas à votre équipe."
    if carac["etat"] == "sur grille":
        return "Ce morpion est déjà posé."


    # on récupère l'équipe (1 ou 2) qui joue ce tour
    joueur = etat["joueur_courant"]
    # on récupère le dictionnaire avec id, nom, couleur et morpions de cette équipe
    equipe = etat["equipes"][joueur]
    # on place le morpion sur la grille
    etat["plateau"][ligne][colonne] = { # on rempli la case ligne colone du plateau avec un dico 
        "joueur": joueur,
        "morpion_id": morpion_id,
        "morpion_nom": carac["nom"],
        "couleur": equipe.get("couleur") or "#111111",
    }

    # on incrémente le nombre d'actions et le tour actuel
    etat["actions"] += 1
    etat["tour_actuel"] += 1

    # on met à jour l'état du morpion pour indiquer qu'il est sur la grille
    carac["etat"] = "sur grille"

    # on memorise sa positiion 
    carac["position"] = (ligne, colonne)

    inserer_journal(partie_id, f"{carac['nom']} est placé en ({ligne + 1},{colonne + 1}).")

    # on appelle verifier_victoire pour voir si la partie est gagnee
    gagnante_id = None
    if verifier_victoire(etat["plateau"], joueur):
        etat["terminee"] = True
        etat["message"] = f"Victoire de {equipe['nom']} !"
        gagnante_id = equipe["id"]
    elif verifier_elimination(etat, 2 if joueur == 1 else 1):
        etat["terminee"] = True
        etat["message"] = f"Tous les morpions adverses sont éliminés. {equipe['nom']} gagne."
        gagnante_id = equipe["id"]
    # on vérifie si la limite est atteinte
    elif etat["actions"] >= etat["max_tours"] or etat["actions"] >= etat["taille"] ** 2:
        etat["terminee"] = True
        etat["message"] = "Fin de partie (tours ou cases épuisés)."

    # si la partie continue, on donne la main à l'autre equipe et on affiche un message
    else:
        etat["joueur_courant"] = 2 if joueur == 1 else 1
        etat["message"] = "Coup enregistré. À l'autre équipe."

    # Synchronise l'état de la partie avec la base de données
    try:
        with connexion.cursor() as cursor:
            cursor.execute(
                "UPDATE partie SET tour_actuel = %s WHERE id_partie = %s",
                (etat["tour_actuel"], partie_id),
            )
            if etat["terminee"]:
                cursor.execute(
                    """
                    UPDATE partie
                    SET id_equipe_gagnante = %s,
                        date_fin = CURRENT_TIMESTAMP
                    WHERE id_partie = %s
                    """,
                    (gagnante_id, partie_id),
                )
                connexion.commit()
            else:
                connexion.commit()
    except Exception:
        connexion.rollback()

    return None

#carac désigne donc le dictionnaire contenant l’état complet du morpion choisi (nom, camp, mana, état, position…)








#Cette fonction prépare ce que la page doit afficher dans le formulaire du sort :
#elle dresse la liste des morpions de mon équipe qui sont déjà posés (ce sont les seuls qui peuvent lancer le sort) ;
# elle dresse la liste des cases occupées par l’équipe adverse (ce sont les seules cibles possibles).
#Elle renvoie ces deux listes au template pour qu’on puisse choisir facilement un lanceur et une cible dans les menus déroulants.



# Fonction : préparer les listes déroulantes (lanceurs/cibles/allies) pour les formulaires de sorts.
def construire_options_sort(etat):
    courant = etat["joueur_courant"]  # on retient le joueur qui doit jouer
    lanceurs = []  # initialiser une liste vide pour stocker les morpions alliés autorise pour le sort 
    cibles = []  # liste vide qui contiendra les cases adverses disponibles 
    allies = []  # liste des cases allies (utile pour le sort de soin)

    for morpion_id in etat["caracteristiques"]:  # on parcourt tous les morpions connus de la partie
        carac = etat["caracteristiques"][morpion_id]  # RECUPERER les caract des morpions de la partir
        if carac["camp"] != courant:  # si le morpion n'appartient pas au joueur courant
            continue  # on passe directement au suivan
        if carac["etat"] != "sur grille":  # on filtre ceux qui ne sont pas deja poses sur la grille
            continue
        if not carac["position"]:  #  sécurité si la position n’a pas été stockée.
            continue # on saute si la position manque 
        ligne, colonne = carac["position"]  # on recupere les coordonnees du morpion sur la grille
        label = f"{carac['nom']} (L{ligne + 1}-C{colonne + 1})"  # texte lisible pour le menu déroulant
        lanceurs.append({  # on ajoute ce morpion dans la liste des lanceurs possiblles
            "id": morpion_id,  
            "label": label,  
            "mana": carac["mana_restante"],  
        })

    lig = 0  # on démarre à la première ligne du plateau car on va parcourir le plateau
    while lig < etat["taille"]:  # boucle tant qu'il reste des lignes
        col = 0  # on repart à la première colonne pour chaque nouvelle ligne
        while col < etat["taille"]:  # boucle sur toutes les colonnes
            case = etat["plateau"][lig][col]  # on recupere le contenue de la case
            if case and case.get("morpion_id") and case["joueur"] != courant:  # on ne garde que les cases occupees par l'equipe advere
                label = f"L{lig + 1} - C{col + 1} ({case['morpion_nom']})"  # texte d'affichage l/c + nom du morpion cible
                cibles.append({  
                    "value": f"{lig},{col}",  
                    "label": label,  # texte lisible dans la liste deroulante 
                })
            if case and case.get("morpion_id") and case.get("joueur") == courant:
                label_allie = f"L{lig + 1} - C{col + 1} ({case['morpion_nom']})"
                allies.append({
                    "value": f"{lig},{col}",
                    "label": label_allie,
                })
            col += 1  # case suivante sur la ligne
        lig += 1  # ligne suivante

    return {"lanceurs": lanceurs, "cibles": cibles, "allies": allies}  # on renvoie les listes au template



 





#C’est la fonction qui fait tourner le sort quiz. Quand on clique sur “Lancer le sort” dans la partie avancée, 
#on appelle cette fonction avec :
#partie_id : la partie concernée,
#morpion_id : le morpion allié qui pose la question,
#case_adverse : la case ennemie visée (ex. "1,2"),
#reponse : ce que l’adversaire a tapé pour répondre à la question “1899 ?”.
#La fonction valide ces infos, vérifie si la réponse est bonne ou pas, retire éventuellement le morpion adverse,
# écrit dans le journal et passe la main au joueur suivant.

#get permet de recuperer la valeur asssocié a une clé

# Fonction : appliquer le sort « quiz Jean Moulin » (question/réponse 1899).
def lancer_sort_quiz(partie_id, morpion_id, case_adverse, reponse):
    etat = PARTIES_AVANCEES.get(partie_id) # va ds partie avancee et recupere partie id, donc etat = partie actuel
    if not etat:
        return "Partie introuvable."
    if etat["terminee"]:                 #si la partie existe mais quelle est terminer 
        return "La partie est terminée."

    lanceur = etat["caracteristiques"].get(morpion_id) 
# lanceur c'est celui qui lance le sort 
 

    if not lanceur:
        return "Morpion inconnu."
    if lanceur["camp"] != etat["joueur_courant"]:
        return "Ce lanceur ne vous appartient pas."
    if lanceur["etat"] != "sur grille":
        return "Le lanceur doit être posé."
    if lanceur["mana_restante"] <= 0:
        return "Plus de mana."

    try:
        lig, col = map(int, (case_adverse or "").split(","))  # map pour convertir chaque morceau en entier, split pr separer
    except ValueError:
        return "Case invalide."
    if not (0 <= lig < etat["taille"] and 0 <= col < etat["taille"]): # entre 0 et taille -1
        return "Case invalide."

           #grille        #ligne   #colonne
    case = etat["plateau"][lig][col] # lis le contenu de la case cible
    if not case or case["joueur"] == etat["joueur_courant"]: # si la case est vide ou cible appartient a l'equipe courante
        return "Il faut viser un adversaire."

    cible = etat["caracteristiques"][case["morpion_id"]] # a partir de la case cible on recupere le dico carac qui contient les infos (nom, camp, position…)
    lanceur["mana_restante"] -= 1
    bonne_reponse = (reponse or "").strip() == "1899" 


    # etat["caracteristiques"] est un dictionnaire qui contient l’état détaillé de tous
    # les morpions de la partie, indexés par leur identifiant (id_morpion).
# case["morpion_id"] te donne justement l’identifiant du morpion qui occupe la case visée.
# En combinant les deux :
# case["morpion_id"] → par exemple 12
# etat["caracteristiques"][12] → renvoie le dictionnaire complet de ce morpion (nom, vie, mana, etc.)

    if bonne_reponse: # rappel : F POUR inserer des variables dans le texte
        texte = f"{lanceur['nom']} pose la question. Bonne réponse : {cible['nom']} reste."
    else:
        texte = f"{lanceur['nom']} pose la question. Mauvaise réponse : {cible['nom']} disparaît."
        etat["plateau"][lig][col] = None
        cible["etat"] = "KO"
        cible["position"] = None

    inserer_journal(partie_id, texte)
    etat["tour_actuel"] += 1
    etat["message"] = texte # par ex : sort reussi ! 


    # passage de tours : 

    if not verifier_victoire(etat["plateau"], etat["joueur_courant"]):
        etat["joueur_courant"] = 2 if etat["joueur_courant"] == 1 else 1 
    return None


# Fonction : gérer un combat rapproché entre un morpion allié et une cible adjacente.
def lancer_combat(partie_id, attaquant_id, case_adverse):
    etat = PARTIES_AVANCEES.get(partie_id) # partie actuelle = num de partie id 
    if not etat:
        return "Partie introuvable."
    if etat["terminee"]:
        return "La partie est terminée."

    attaquant = etat["caracteristiques"].get(attaquant_id) # comme pr la fonction quiz
    if not attaquant:
        return "Morpion inconnu."
    if attaquant["camp"] != etat["joueur_courant"]:
        return "Ce morpion ne vous appartient pas."
    if attaquant["etat"] != "sur grille":
        return "Le morpion doit être posé."

    lig, col, erreur = lire_coordonnees(case_adverse, etat["taille"])
    if erreur:
        return erreur
    case = etat["plateau"][lig][col]
    if not case:
        return "Il faut viser un morpion adverse."
    if case["joueur"] == etat["joueur_courant"]: # si le num d equipe du morpion de la case est egal a l equipe qui joue ce tour 
        return "On n'attaque pas ses propres morpions."
    if not attaquant["position"]: # verfier que l attaquant a bien ete poser sur la grille
        return "Position du morpion inconnue."
    lig_att, col_att = attaquant["position"]
    distance = abs(lig - lig_att) + abs(col - col_att) #valeur absolue pour ne pas avoir de negatif
    if distance != 1:
        return "On ne peut frapper que les cases qui sont cote à cote."

    cible = etat["caracteristiques"][case["morpion_id"]]
    # case["morpion_id"] lit l’identifiant du morpion qui occupe la case ciblée.
    # etat["caracteristiques"][12] → renvoie le dictionnaire complet de ce morpion (nom, vie, mana, etc.)
    if not action_reussie(attaquant):
        texte = f"{attaquant['nom']} tente un combat mais rate son coup."
    else:
        cible["vie_actuelle"] -= attaquant["attaque"]
        if cible["vie_actuelle"] <= 0:
            texte = f"{attaquant['nom']} élimine {cible['nom']} en combat."
            retirer_morpion_du_plateau(etat, case["morpion_id"])
        else:
            texte = f"{attaquant['nom']} inflige {attaquant['attaque']} dégâts à {cible['nom']}."

    inserer_journal(partie_id, texte)
    etat["actions"] += 1
    etat["tour_actuel"] += 1
    joueur = etat["joueur_courant"]
    equipe = etat["equipes"][joueur]
    if verifier_victoire(etat["plateau"], joueur):
        etat["terminee"] = True
        etat["message"] = f"Victoire de {equipe['nom']} !"
    elif verifier_elimination(etat, 2 if joueur == 1 else 1):
        etat["terminee"] = True
        etat["message"] = f"Tous les morpions adverses sont éliminés. {equipe['nom']} gagne."
    elif etat["actions"] >= etat["max_tours"] or etat["actions"] >= etat["taille"] ** 2:
        etat["terminee"] = True
        etat["message"] = "Fin de partie (tours ou cases épuisés)."
    else:
        basculer_tour(etat)
        etat["message"] = texte
    return None


# Fonction : gérer les sorts officiels (feu, soin, armageddon) décrits dans le sujet.
def lancer_sort_magique(partie_id, morpion_id, case_cible, case_allie, sort_type):
    etat = PARTIES_AVANCEES.get(partie_id) # partie avancee contient tte les parties en cours, et on extrait 
    # l etat correspondant a la partie id
    if not etat:
        return "Partie introuvable."
    if etat["terminee"]:
        return "La partie est terminée."

    lanceur = etat["caracteristiques"].get(morpion_id)
    #Donc, cette ligne signifie : “Va dans l’état de la partie, puis dans le 
# sous-dictionnaire des caractéristiques, et récupère 
# (avec get) le dictionnaire de la morpion dont l’id vaut morpion_id. (par ex 5)
# Range-le dans la variable lanceur.
    if not lanceur:
        return "Morpion inconnu."
    if lanceur["camp"] != etat["joueur_courant"]:
        return "Ce lanceur ne vous appartient pas."
    if lanceur["etat"] != "sur grille":
        return "Le lanceur doit être posé."

    couts = {"feu": 2, "soin": 1, "arme": 5} # associe les sorts a leur cout en mana
    cout = couts.get(sort_type) # on recupere le cout du sort 
    if cout is None:
        return "Type de sort inconnu."
    if lanceur["mana_restante"] < cout:
        return "Pas assez de mana."

    if sort_type == "soin":
        if not case_allie:
            return "Choisissez une case alliée."
        lig, col, erreur = lire_coordonnees(case_allie, etat["taille"])
        if erreur:
            return erreur
        case = etat["plateau"][lig][col]
        if not case:
            return "Il faut cibler un allié présent sur la grille."
        if case["joueur"] != etat["joueur_courant"]: #si le num d equipe du morpion de la case est egal a l equipe qui joue ce tour
            return "Le soin ne fonctionne que sur vos morpions."
    else:
        if not case_cible:
            return "Choisissez une case ennemie."
        lig, col, erreur = lire_coordonnees(case_cible, etat["taille"])
        if erreur:
            return erreur
        case = etat["plateau"][lig][col]
        if sort_type != "arme":
            if not case:
                return "Il faut viser un adversaire."
            if case["joueur"] == etat["joueur_courant"]:
                return "Ce sort ne vise que l'adversaire."
        if sort_type == "arme" and case and case.get("morpion_id") and case["joueur"] == etat["joueur_courant"]:
            return "Armageddon ne peut pas viser son équipe."

    lanceur["mana_restante"] -= cout
    if not action_reussie(lanceur):
        texte = f"{lanceur['nom']} tente le sort mais échoue."
        return conclure_action(etat, partie_id, texte)

    if sort_type == "feu":
        cible = etat["caracteristiques"][case["morpion_id"]]
        cible["vie_actuelle"] -= 3
        if cible["vie_actuelle"] <= 0:
            texte = f"Boule de feu réussie : {cible['nom']} est détruit."
            retirer_morpion_du_plateau(etat, case["morpion_id"])
        else:
            texte = f"Boule de feu : {cible['nom']} perd 3 points de vie."
    elif sort_type == "soin":
        cible = etat["caracteristiques"][case["morpion_id"]]
        nouvelle_vie = min(cible["vie_max"], cible["vie_actuelle"] + 2) # prend le plus pt des deux nb 
        gain = nouvelle_vie - cible["vie_actuelle"]
        cible["vie_actuelle"] = nouvelle_vie
        texte = f"{lanceur['nom']} soigne {cible['nom']} (+{gain} PV)."
    else:
        texte = f"{lanceur['nom']} lance Armageddon : la case L{lig + 1}-C{col + 1} est détruite."
        if case and case.get("morpion_id"):
            retirer_morpion_du_plateau(etat, case["morpion_id"])
        etat["plateau"][lig][col] = {"joueur": None, "morpion_nom": "X"}

    return conclure_action(etat, partie_id, texte)



    # ce bloc il traite les actions envoyées par un formulaire HTML POST.
# Chaque fois que l'utilisateur clique sur un bouton (créer partie, jouer, lancer un sort, etc.), 
# le formulaire envoie une action, et ce code exécute la bonne fonction en réponse.

if POST and "action" in POST:  # si un formulaire a été soumis avec un champ "action"
    action = POST["action"][0]  # on lit la valeur de l’action (chaîne provenant du POST)

    if action == "creer":  # création d’une nouvelle partie avancée
        equipe1 = int(POST.get("equipe1", ["0"])[0])  # identifiant de la première équipe (ou 0 si absent)
        equipe2 = int(POST.get("equipe2", ["0"])[0])  # identifiant de la deuxième équipe
        taille = int(POST.get("taille", ["3"])[0])  # taille de la grille (3x3 ou 4x4)
        max_tours = int(POST.get("max_tours", ["12"])[0])  # limite de tours saisie
        if equipe1 == equipe2:
            REQUEST_VARS["message"] = "Choisissez deux équipes différentes."
            REQUEST_VARS["message_class"] = "alert-warning"
        elif taille not in (3, 4):
            REQUEST_VARS["message"] = "La grille doit être 3x3 ou 4x4."
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            partie_id, msg = initialiser_partie_avancee(equipe1, equipe2, taille, max_tours)
            if partie_id is None:
                REQUEST_VARS["message"] = msg
                REQUEST_VARS["message_class"] = "alert-error"
            else:
                REQUEST_VARS["message"] = msg
                REQUEST_VARS["message_class"] = "alert-success"
                rafraichir_partie_active(partie_id)

    elif action == "jouer":  # placement classique d’un morpion
        partie_id = int(POST.get("partie_id", ["0"])[0])  # partie concernée
        morpion_id = POST.get("morpion_id", [""])[0]  # identifiant unique du morpion choisi
        case = POST.get("case", ["0,0"])[0]  # coordonnées reçues sous forme "lig,col"
        try:
            lig, col = map(int, case.split(",")) # split pour decouper la chaine en deux morceau // map pr cvt en entier
        except ValueError:
            lig = col = -1
        erreur = jouer_un_coup_avance(partie_id, morpion_id, lig, col)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"] # on prend le dernier mess et on le stock ds rv 
            REQUEST_VARS["message_class"] = "alert-success"
        rafraichir_partie_active(partie_id)

    elif action == "sort_quiz":  # utilisation du sort quiz Jean Moulin
        partie_id = int(POST.get("partie_id", ["0"])[0])  # partie en cours
        morpion_id = POST.get("morpion_id", [""])[0]  # morpion lanceur
        case_adverse = POST.get("case_adverse", ["0,0"])[0]  # cible sélectionnée
        reponse = POST.get("reponse_quiz", [""])[0]  # réponse saisie par l’adversaire
        erreur = lancer_sort_quiz(partie_id, morpion_id, case_adverse, reponse)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        rafraichir_partie_active(partie_id)

    elif action == "combat":  # combat rapproché classique
        partie_id = int(POST.get("partie_id", ["0"])[0])  # partie en cours
        attaquant_id = POST.get("attaquant_id", [""])[0]  # morpion qui attaque
        case_adverse = POST.get("case_adverse", [""])[0]  # coordonnée de la cible
        erreur = lancer_combat(partie_id, attaquant_id, case_adverse)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        rafraichir_partie_active(partie_id)

    elif action == "sort_magique":  # sorts feu / soin / armageddon
        partie_id = int(POST.get("partie_id", ["0"])[0])  # partie cible
        morpion_id = POST.get("morpion_id", [""])[0]  # lanceur sélectionné
        type_sort = POST.get("type_sort", ["feu"])[0]  # type de sort choisi
        case_adverse = POST.get("case_adverse", [""])[0]  # coordonnées ennemies éventuellement nécessaires
        case_allie = POST.get("case_allie", [""])[0]  # coordonnées alliées (sort de soin)
        erreur = lancer_sort_magique(partie_id, morpion_id, case_adverse, case_allie, type_sort)
        if erreur:
            REQUEST_VARS["message"] = erreur
            REQUEST_VARS["message_class"] = "alert-warning"
        else:
            REQUEST_VARS["message"] = PARTIES_AVANCEES[partie_id]["message"]
            REQUEST_VARS["message_class"] = "alert-success"
        rafraichir_partie_active(partie_id)

    elif action == "abandonner":  # suppression de la partie en mémoire
        partie_id = int(POST.get("partie_id", ["0"])[0])  # identifiant à retirer
        if partie_id in PARTIES_AVANCEES:  # on vérifie que la partie existe en session
            del PARTIES_AVANCEES[partie_id]  # suppression de l’état conservé
        REQUEST_VARS["message"] = "Partie avancée retirée de votre session."  # message d’information
        REQUEST_VARS["message_class"] = "alert-warning"  # couleur d’alerte douce
        REQUEST_VARS["partie_avancee"] = None  # on vide les variables affichées
        REQUEST_VARS["partie_avancee_id"] = None  # plus de partie courante

REQUEST_VARS["equipes_disponibles"] = charger_equipes()  # toujours afficher la liste des équipes dans le formulaire

if REQUEST_VARS.get("partie_avancee"):  # si une partie est déjà affichée côté interface
    REQUEST_VARS["options_sort"] = construire_options_sort(REQUEST_VARS["partie_avancee"])  # on calcule les menus déroulants
elif PARTIES_AVANCEES:  # sinon, s'il existe au moins une partie en mémoire
    pid, etat = next(iter(PARTIES_AVANCEES.items()))  # on prend la première partie du dictionnaire
    rafraichir_partie_active(pid)  # on synchronise REQUEST_VARS avec cette partie
    REQUEST_VARS["options_sort"] = construire_options_sort(etat)  # et on prépare les options
else:  # sinon aucune partie n’est disponible
    REQUEST_VARS["options_sort"] = {"lanceurs": [], "cibles": [], "allies": []}  # on renvoie des listes vides pour éviter les erreurs


# next iter : PARTIES_AVANCEES.items() renvoie un itérateur de couples (clé, valeur) où la clé est l’identifiant de partie (partie_id) et la valeur est l’état complet (plateau, équipes, etc.).
# iter(...) construit l’itérateur explicite.
# next(...) prend le premier élément de cet itérateur.

# Cela évite de laisser l’interface vide quand aucune partie n’est explicitement sélectionnée. Si REQUEST_VARS["partie_avancee"] est vide mais qu’il reste au moins une partie avancée stockée en session,