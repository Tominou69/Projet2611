"""c le contrôleur de la page d'accueil""" 

from datetime import timedelta  # pr les durrees 

from controleurs.includes import add_activity  
from model.model_pg import execute_select_query 


add_activity(SESSION["HISTORIQUE"], "consultation de l'accueil")


connexion = SESSION["CONNEXION"]


def executer_select(query, params=None): #fonction pr executer une rqt select 
    rows = execute_select_query(connexion, query, params or [])  # lance la requête
    return rows if rows is not None else []  


def recuperer_entier(query, params=None, default=0): #pr avoir la 1re vlrs de la requete 

    rows = executer_select(query, params)  # récupère les lignes
    return rows[0][0] if rows else default  # renvoie la première valeur ou le défaut

#fct pr convertir une duree en seconde
def formater_duree(seconds):  # en paramt j met un nombre de secondes en entrée
    if seconds is None:  
        return "—"  
    seconds = int(seconds)  # j initialise secondes en entier (c plus pratique que de mettre un float)
    hours, remainder = divmod(seconds, 3600)  # divmod c une fonction pr av le nombre d'heures et le reste
    minutes, secs = divmod(remainder, 60)  # divmod pr av minutes et secondes
    parts = []  # j initialise la liste en tq vide 
    if hours:   # si la duree contient des heur 
        parts.append(f"{hours} h")  #part c pour stocker le txt 
    if minutes:  
        parts.append(f"{minutes} min")  # j ajoute x min a la lsite 
    if secs or not parts:  
        parts.append(f"{secs} s")  
    return " ".join(parts)  # j  assemble la chaîne finale


def recuperer_partie_selon_duree(order_clause):  # order_clause cest en gros soit "ASC" ou "DESC"
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
    rows = executer_select(query)
    if not rows:
        return None  # si g aucune partie qui est terminée
    row = rows[0]
    return {
        "id": row[0],  # identifiant de la partie (ca c trouvable dans le psql)
        "affiche": f"{row[1]} vs {row[2]}",  # qui vs qui genre OL VS PSG 
        "duree": formater_duree(row[3]),  
        "date_fin": row[4],  # temps fin de la partie 
    }



# Comptages simples (nombre de lignes dans quelques tables)

REQUEST_VARS["table_counts"] = [
    {"label": "Morpions", "value": recuperer_entier("SELECT COUNT(*) FROM morpion")},
    {"label": "Équipes", "value": recuperer_entier("SELECT COUNT(*) FROM equipe")},
    {"label": "Parties", "value": recuperer_entier("SELECT COUNT(*) FROM partie")},
]



# ca c pour av le nb de victoire par equipe et garder que le top 3
# g fais un left join pr avoir les equipe qui n'ont pas encore gagné de partie


top_equipes_query = """
    SELECT e.nom,
           e.couleur,
           COUNT(p.id_partie) AS victoires
    FROM equipe e
    LEFT JOIN partie p ON p.id_equipe_gagnante = e.id_equipe
    GROUP BY e.id_equipe, e.nom, e.couleur
    ORDER BY victoires DESC, e.nom ASC
    LIMIT 3
"""
REQUEST_VARS["top_equipes"] = [
    {"nom": row[0], "couleur": row[1], "victoires": row[2]} # j construit pr chq ligne trois parametre 
    for row in executer_select(top_equipes_query) # bh la j excute la rqt 
]

# pr que le templates puisse afficher les equipe et leur nb de victoire



# Parties les plus rapide et la plus longue 

REQUEST_VARS["partie_plus_rapide"] = recuperer_partie_selon_duree("ASC")
REQUEST_VARS["partie_plus_longue"] = recuperer_partie_selon_duree("DESC")


# Journalisation par mois  
# g prefere trier par + recent jusqu au moins ancien pcq c comme ca que j'ai tjr fais ds ma vie 

journal_query = """
    SELECT annee, mois, nb_lignes_total, nb_parties, nb_moyen_lignes
    FROM v_journal_par_mois
    ORDER BY annee DESC, mois DESC
"""
REQUEST_VARS["journal_stats"] = [ # la lisre sera utiliser dans le template 
    {
        "annee": int(row[0]),  # l'année du regroupement
        "mois": int(row[1]),  # le mois
        "nb_lignes": int(row[2]),  # nombre total de lignes de journal
        "nb_parties": int(row[3]),  # nombre de parties concernées
        "nb_moyen": round(float(row[4]), 2),  # moyenne de lignes par partie(arrondi a 2 chiffres apres la virgule)
    }
    for row in executer_select(journal_query)
]

#row représente une ligne 
#renvoyée par la requête SQL journal_query. 
#Cette ligne esst une liste de valeurs