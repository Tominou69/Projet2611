"""c le contrôleur de la page d'accueil, il prepare les stats a afficher sur la page d'accueil""" 

from datetime import timedelta  # pr les durrees 

from controleurs.includes import add_activity
from model.model_pg import (
    get_journal_stats,
    get_partie_par_duree,
    get_table_counts,
    get_top_equipes,
)
#ici on importe les fonctions de model

add_activity(SESSION["HISTORIQUE"], "consultation de l'accueil") #enregistrement du fait que acceuil a ete consulter


connexion = SESSION["CONNEXION"]

# Là, on prend la duree des parties en scds et on les transforme en un texte 

def formater_duree(seconds):  # en paramt j met un nombre de secondes en entrée
    if seconds is None:  
        return "—"  
    seconds = int(seconds)  # on force pr que seconds soit un entier pour eviter les floats 
    hours, remainder = divmod(seconds, 3600)  
    
    # divmod pr diviser : ici on divise le nombre total de secondes par 3600.
 #hours reçoit combien d’heures complètes on peut faire (ex : 5400 s → 1 h).
#remainder reçoit ce qu’il reste en secondes après avoir enlevé ces heures (ex : 5400 s → reste 1800 s).


    minutes, secs = divmod(remainder, 60)  # on transforme le reste en minutes et secondes


    parts = []  # j initialise la liste PARTIES du temps qu'on va afficher en tq vide 
    if hours:   # si la duree contient des heur 
        parts.append(f"{hours} h")  # append permet d'ajouter l'élement dans la liste 
        # note que f permet d'inserer des variables dans la chaine de caractères 
        # par exemple on ajoute 2h si hours vaut 2 
        # donc ici ce quon fait, cest ajouter X h a la liste 

    if minutes: 
        parts.append(f"{minutes} min")   
    if secs or not parts:                        # le or not parties cest pr etre sur d afficher au moins "0 s"
        parts.append(f"{secs} s")  
    return " ".join(parts)  # j assemble la chaîne finale
    # et " " est le séparateur : "2h" "15 min" "5 s" 


# exemple pr que tu comprennes : 
#notes = []
#notes.append(15)
#notes.append(12)
#notes vaut maintenant [15, 12]


#Fonction pour renvoyer un texte affichable pour le template

def formatter_partie(partie_dict): #prend partie_dict du model_pg avec les infos sur les equipes et les duree
    if partie_dict is None:
        return None #donc la le template affichera "Aucune partie terminée."
    return {
        "id": partie_dict["id"],
        "affiche": f"{partie_dict['equipe1']} vs {partie_dict['equipe2']}", # on genere la phrase "Equipe 1 vs Equipe 2"
        "duree": formater_duree(partie_dict["duree_sec"]),
        "date_fin": partie_dict["date_fin"],
    }






#on prépare la liste qui sera utilisée par accueil.html pour 
#afficher les statistiques 


REQUEST_VARS["table_counts"] = get_table_counts( 
    connexion, # pr aller dans psql pr executer les count * 

    # on fournit au model la liste des tables a compter 
    [
        ("Morpions", "morpion"),
        ("Équipes", "equipe"),
        ("Parties", "partie"),
    ],
)

#par exemple si tes tables contiennent :
# morpion → 12 lignes
# equipe → 3 lignes
# partie → 5 lignes
# Alors get_table_counts(connexion, [("Morpions","morpion"), ...]) renvoie :
# [("Morpions", 12), ("Équipes", 3), ("Parties", 5)]




REQUEST_VARS["top_equipes"] = get_top_equipes(connexion, limite=3)




# Parties les plus rapide et la plus longue 

REQUEST_VARS["partie_plus_rapide"] = formatter_partie(get_partie_par_duree(connexion, "ASC"))
REQUEST_VARS["partie_plus_longue"] = formatter_partie(get_partie_par_duree(connexion, "DESC"))




REQUEST_VARS["journal_stats"] = get_journal_stats(connexion)

