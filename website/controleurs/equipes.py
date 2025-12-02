"""
ca c la page du contrôleur de "gestion des equipes"
"""

from psycopg import Error  

from controleurs.includes import add_activity  
from model.model_pg import execute_select_query  

add_activity(SESSION["HISTORIQUE"], "gestion des équipes") 

connexion = SESSION["CONNEXION"]  

# Valeurs par défaut utilisées par le template
REQUEST_VARS.setdefault("message", None)  # message affiché dans message.html
REQUEST_VARS.setdefault("message_class", None)  # classe CSS du message
REQUEST_VARS.setdefault(
    "form_values", {"nom": "", "morpions": [], "couleur": ""}
)  # champs préremplis du formulaire (nom, couleur, cases cochées)


MIN_MORPIONS = 6
MAX_MORPIONS = 8


# fonction pour les succes, avertissement et erruer 


def definir_message(text, css_class): # le contenu du texte , la class css  

    REQUEST_VARS["message"] = text  

    # On enregistre le texte dans REQUEST_VARS,
    # pour que le template puisse l’afficher via {% include 'message.html' %}.
    #  Exemple : on met “Équipe créée avec succès”.

    REQUEST_VARS["message_class"] = css_class  # comment l'afficher (vert/rouge/jaune)





"""sert à préparer la liste des morpions disponibles pour créer une équipe."""
""" recuperer toutes les caracteristiques des morpions, transforme en une liste qui est envoye au template """

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
    rows = execute_select_query(connexion, query, []) or []  # exécute la requête
    morpions = []  # liste des morpions initialiser vide
    for row in rows:  # on parcours chauqe ligne SQL (dc id, nom, image, vie, attaque, mana, reussite
        morpions.append( # append permet d'ajouter l'élement dans la liste 
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




""" construit la liste des equipes avec leurs morpions, alimente equipes existantes dans la page """

def lister_equipes():
   
    equipes_rows = execute_select_query(  # liste des équipes enregistrées
        connexion,
        """
        SELECT id_equipe, nom, couleur, date_creation
        FROM equipe
        ORDER BY date_creation DESC
        """,
        [],
    ) or []
    membres_rows = execute_select_query(  # jointure entre morpion_equipe et morpion pour avoir 
    # le nom et les stats de chaque morpion 
        connexion,
        """
        SELECT me.id_equipe, m.nom, me.ordre_dans_equipe
        FROM morpion_equipe me
        JOIN morpion m ON m.id_morpion = me.id_morpion
        ORDER BY me.id_equipe, me.ordre_dans_equipe
        """,
        [],
    ) or []

    # On regroupe les morpions par équipe avec un simple dictionnaire {id_equipe: [ ... ]}.
    membres_par_equipe = {}  # on creer un dictionnaire vide pour stocker les morpions par equipe

    for row in membres_rows:  # on parcourt chaque ligne de la jointure
        equipe_id = row[0] # la premiere colone c l'id de l'equip
        if equipe_id not in membres_par_equipe:
            membres_par_equipe[equipe_id] = []  #liste vide pour cette equipe 
        membres_par_equipe[equipe_id].append({"nom": row[1], "ordre": row[2]})  # On ajoute 
        # un petit dictionnaire contenant le nom du morpion (row[1]) et son ordre (row[2]) dans cette équipe

    equipes = []  # liste creer qui contient les equipes 


    for row in equipes_rows:  # on parcourt les équipes
        equipe_id = row[0]  
        equipes.append(  
            {
                "id": equipe_id,  
                "nom": row[1], 
                "couleur": row[2],  
                "date_creation": row[3],  
                "morpions": membres_par_equipe.get(equipe_id, []),  # liste des morpions trouvée plus haut
            }
        )
    return equipes  # renvoie la liste ds teams qu utilise le template !! 


def extraire_morpions_selectionnes(values):  # values = liste des ids envoyés par le formulaire

    # Exemple : <input type="checkbox" name="morpions" value="{{ morpion.id }}">, morpions [1,3,5....]

    liste_vide = []  # liste vide, qui contiendra les id des morpions sélectionnés (avec doublons)


    for raw_value in values:  # parcours des valeurs reçues depuis le formulaire

    # raw values est chaque element individuel, values cest tte les valeurs 
        try:
            morpion_id = int(raw_value)  # conversion en entier
        except ValueError:
            continue  # si ce n'est pas un entier on l'ignore
        liste_vide.append(morpion_id)  
    return liste_vide  


def creer_equipe():
    nom = POST.get("nom", [""])[0].strip() 

    # POST.get("nom", [""]) renvoie une liste des valeurs du champ nom
    # [0] c la premiere valeur de la liste, strip() c pour enlever les espaces en debut et fin

    couleur = POST.get("couleur", [""])[0].strip()


    liste_ids_morpions_selectionnes = extraire_morpions_selectionnes(POST.get("morpions", []))

    #POST.get("morpions", []) renvoie la liste brute des valeurs envoyees par le formulaire
    # extraire_morpions_selectionnes(...) convertit ces valeurs en 
    # entiers, garde l’ordre, et les stocke dans une liste Python (ex. [3, 7, 7]).

    REQUEST_VARS["form_values"] = {"nom": nom, "morpions": liste_ids_morpions_selectionnes, "couleur": couleur}

    if not nom:
        definir_message("Merci de renseigner un nom pour l'équipe.", "alert-warning")
        return

    if len(liste_ids_morpions_selectionnes) < MIN_MORPIONS or len(liste_ids_morpions_selectionnes) > MAX_MORPIONS:  # vérifie les bornes
       
       # len cest une fonction qui renvoie le nombre d'elements dans la liste
       
        definir_message(
            f"Une équipe doit contenir entre {MIN_MORPIONS} et {MAX_MORPIONS} morpions (actuellement {len(liste_ids_morpions_selectionnes )} sélectionnés).",
            "alert-warning",
        )
        return

    try: #On entre dans un bloc “protégé” pour capter les erreurs SQL (par exemple une contrainte violée).

        with connexion.cursor() as cursor:  # ouvre un curseur psql, permet d'executer des requetes SQL
            cursor.execute(
                "INSERT INTO equipe (nom, couleur) VALUES (%s, %s) RETURNING id_equipe", 
                (nom, couleur or None),

                # On insère l’équipe dans la table equipe  (nom, couleur)
                # via INSERT INTO ... RETURNING id_equipe : on dmd a psql de ns donne son identifiant (new_id).
            )
            new_id = cursor.fetchone()[0]  # récupère l'identifiant créé et on le stocke ds new_id
            ordre = 1  # ordre d'apparition de chaque morpion dans l'équipe
            for morpion_id in liste_ids_morpions_selectionnes:  
                cursor.execute(
                    """
                    INSERT INTO morpion_equipe (id_equipe, id_morpion, ordre_dans_equipe)
                    VALUES (%s, %s, %s)
                    """,
                    (new_id, morpion_id, ordre),
                )
                ordre += 1  # pour garder l'ordre des morpions dans l'equipe (choisi par l'utilisateur)


                
        definir_message(f"L'équipe « {nom} » a été créée avec succès.", "alert-success")

        REQUEST_VARS["form_values"] = {"nom": "", "morpions": [], "couleur": ""}  # on vide le formulaire
        #pour éviter de réafficher l’ancienne saisie.


    except Error as err:
        definir_message(f"Impossible de créer l'équipe : {err}", "alert-error")


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
            # on supprime d'abord les parties qui utilisent cette équipe
            cursor.execute(

                # cursor execute execute la requete SQL en l envoyant au serveur psql 
                """
                SELECT id_partie
                FROM partie
                WHERE id_equipe1 = %s OR id_equipe2 = %s
                """,
                [equipe_id, equipe_id],
            )
            parties_associees = cursor.fetchall() 

            # cursor fectch all renvoie toutes les lignes restantes du résultat d’une requête SQL sous forme de liste 

            # Après SELECT id_partie ..., on appelle cursor.fetchall().
            # Ça donne une liste comme [(3,), (7,), (9,)] si l’équipe est liée à trois parties.
            # On stocke ce résultat dans parties_associees

            if parties_associees:
                for row in parties_associees:
                    part_id = row[0] # recuperer l id de la partie 
                    cursor.execute("DELETE FROM journal WHERE id_partie = %s", (part_id,))
                    cursor.execute("DELETE FROM partie WHERE id_partie = %s", (part_id,))

            cursor.execute("DELETE FROM morpion_equipe WHERE id_equipe = %s", (equipe_id,))
            cursor.execute("DELETE FROM equipe WHERE id_equipe = %s", (equipe_id,))
            if cursor.rowcount == 0: # cursor rowcount renvoie le nombre de lignes affectees par la derniere requete
            # dc si 0 c que la requete a echoue 
                definir_message("Équipe introuvable ou déjà supprimée.", "alert-warning")
                return
        definir_message("Équipe supprimée.", "alert-success")




# detection de l'action du formulaire 

if POST and "action" in POST: # est ce que le formulaire a ete soumis et action est dans POST
    action = POST["action"][0] # pr recuperer la premiere valeur de la lste
    if action == "create":
        creer_equipe()
    elif action == "delete":
        supprimer_equipe()


REQUEST_VARS["morpions"] = lister_morpions()

# pour afficher le nombre de morpions disponibles et les bornes min et max : 

REQUEST_VARS["morpions_total"] = len(REQUEST_VARS["morpions"])
REQUEST_VARS["morpions_min"] = MIN_MORPIONS
REQUEST_VARS["morpions_max"] = MAX_MORPIONS

REQUEST_VARS["equipes"] = lister_equipes()

#En gros, ce bloc :
# Exécute l’action demandée (création ou suppression) si on reçoit un formulaire.
# Re-remplit ensuite toutes les données nécessaires au template equipes.html
# (morpions pour le formulaire, équipes déjà existantes).


