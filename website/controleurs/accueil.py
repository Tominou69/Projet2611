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

def formater_duree(seconds): 
    if seconds is None:  
        return "—"  
    seconds = int(seconds)  
    hours, remainder = divmod(seconds, 3600)  
    
#hours reçoit combien d’heures complètes on peut faire (ex : 5400 s → 1 h).

#remainder reçoit ce qu’il reste en secondes après avoir enlevé ces heures (ex : 5400 s → reste 1800 s).


    minutes, secs = divmod(remainder, 60)  


    parts = []  
    if hours:  
        parts.append(f"{hours} h")  
       

    if minutes: 
        parts.append(f"{minutes} min")   
    if secs or not parts:                        # le or not parties cest pr etre sur d afficher au moins "0 s"
        parts.append(f"{secs} s")  
    return " ".join(parts)




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

#afficher les statistiques express  


REQUEST_VARS["table_counts"] = get_table_counts( # on appel la fct du model qui sait faire des count * sr pls tables 
    connexion, # pr aller dans psql pr executer les count * (on donne la connexion a la fct)

    # on fournit au model la liste des tables a compter 
    [
        ("Morpions", "morpion"), #  select count(*) from morpion
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





REQUEST_VARS["partie_plus_rapide"] = formatter_partie(get_partie_par_duree(connexion, "ASC"))
REQUEST_VARS["partie_plus_longue"] = formatter_partie(get_partie_par_duree(connexion, "DESC"))




REQUEST_VARS["journal_stats"] = get_journal_stats(connexion)

