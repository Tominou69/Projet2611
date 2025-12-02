
""" c le controleur qui liste en detail morpions, equipes, config et partie recents """

from collections import defaultdict  # import pour créer des listes par clé

from model.model_pg import execute_select_query  # fonction  pour lancer un SELECT
from controleurs.includes import add_activity  # utilitaire pour tracer l'activité

add_activity(SESSION['HISTORIQUE'], "consultation des données principales")  # on enregistre la visite de /afficher

connexion = SESSION['CONNEXION']  # on récupère la connexion à la BD stockée dans la session





# Morpions disponibles

morpions_query = """  # requête pour récupérer tous les morpions avec leurs caractéristiques
    SELECT id_morpion, nom, image, points_vie, points_attaque,
           points_mana, points_reussite, date_creation
    FROM morpion
    ORDER BY nom
"""
morpions_cols = (  # noms des colonnes qu'on va associer aux résultats
    "id",
    "nom",
    "image",
    "vie",
    "attaque",
    "mana",
    "reussite",
    "date_creation",
)
REQUEST_VARS["morpions"] = [  # pr stocke la liste de morpions pour le template
    dict(zip(morpions_cols, row)) for row in execute_select_query(connexion, morpions_query, []) or []
]



# Équipes et  composition
equipes_query = """  # requête pour récupérer les infos principales des équipes
    SELECT id_equipe, nom, couleur, date_creation
    FROM equipe
    ORDER BY nom
"""
membres_query = """  # requête pour récupérer la composition des équipes (jointure)
    SELECT me.id_equipe,
           m.nom,
           m.points_vie,
           m.points_attaque,
           m.points_mana,
           m.points_reussite,
           me.ordre_dans_equipe
    FROM morpion_equipe me
    JOIN morpion m ON m.id_morpion = me.id_morpion
    ORDER BY me.id_equipe, me.ordre_dans_equipe
"""
# row c une ligne de la requete 
# mtn on prepare la composition d equipe 
members_map = defaultdict(list)  # dcq id equipe est initialiser a vide
for row in (execute_select_query(connexion, membres_query, []) or []):  # pr av la ligne de mrèequipe av les infos du mrp 
    members_map[row[0]].append(
        {
            "nom": row[1],  # nom du morpion
            "vie": row[2],  # pt de vie
            "attaque": row[3],  # pt d'attaque
            "mana": row[4],  # pt de mana
            "reussite": row[5],  # c une reussite pr pts 
            "ordre": row[6],  
        }
    )

REQUEST_VARS["equipes"] = []  # ce truc sera envoyé dans le template 
for row in (execute_select_query(connexion, equipes_query, []) or []):  # on parcourt toutes les équipes
    equipe = {
        "id": row[0],  
        "nom": row[1],  
        "couleur": row[2], 
        "date_creation": row[3],  
        "morpions": members_map.get(row[0], []),  
    }
    REQUEST_VARS["equipes"].append(equipe)  # on ajoute l'équipe préparée
    # append c pr ajouter un element a la liste 


# Configurations
config_query = """  # requête pour lister les configurations de jeu disponibles
    SELECT id_configuration, taille_grille, nb_max_tours,
           somme_caracteristiques, date_creation
    FROM configuration
    ORDER BY date_creation DESC
"""
config_cols = (  # noms des colonnes pour zip
    "id",
    "taille_grille",
    "nb_max_tours",
    "somme_caracteristiques",
    "date_creation",
)
REQUEST_VARS["configurations"] = [  # la liste de configurations affichées dans le template
    dict(zip(config_cols, row)) for row in (execute_select_query(connexion, config_query, []) or [])
] # dict c pr faire que l asso soit pythonable 



# Parties récentes

parties_query = """  # requête qui sélectionne les 5 parties les plus récentes
    SELECT p.id_partie,
           e1.nom AS equipe1,
           e2.nom AS equipe2,
           eg.nom AS gagnante,
           p.date_debut,
           p.date_fin,
           p.tour_actuel
    FROM partie p
    JOIN equipe e1 ON e1.id_equipe = p.id_equipe1
    JOIN equipe e2 ON e2.id_equipe = p.id_equipe2
    LEFT JOIN equipe eg ON eg.id_equipe = p.id_equipe_gagnante
    ORDER BY p.date_debut DESC
    LIMIT 5
"""
partie_cols = (  # noms des colonnes utilisés pour le truc d apres 
    "id",
    "equipe1",
    "equipe2",
    "gagnante",
    "date_debut",
    "date_fin",
    "tour",
)
REQUEST_VARS["parties"] = [  # liste des parties affichées
    dict(zip(partie_cols, row)) for row in (execute_select_query(connexion, parties_query, []) or [])
    # zip ... c pr associer chaque nom de colonne a la valeur ds row (la ligne) 
    # dict transforme cela en un dico python du style "id partie = 1, "date = ..." " .. 

]


# Journal récent
journal_query = """  # requête qui récupère les 5 dernières entrées du journal
    SELECT j.id_partie, j.numero_ligne, j.date_action, j.texte_action
    FROM journal j
    ORDER BY j.date_action DESC
    LIMIT 5
"""
journal_cols = ("id_partie", "numero", "date_action", "texte")  # noms des colonnes
REQUEST_VARS["journal_recent"] = [  # liste des lignes de journal récentes pr le template 
    dict(zip(journal_cols, row)) for row in (execute_select_query(connexion, journal_query, []) or [])  # zip colonnes/valeurs
]
