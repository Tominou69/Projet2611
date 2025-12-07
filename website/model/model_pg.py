import psycopg
from psycopg import sql
from logzero import logger

def execute_select_query(connexion, query, params=[]):
    """
    Méthode générique pour exécuter une requête SELECT (qui peut retourner plusieurs instances).
    Utilisée par des fonctions plus spécifiques.
    """
    with connexion.cursor() as cursor:
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None

def execute_other_query(connexion, query, params=[]):
    """
    Méthode générique pour exécuter une requête INSERT, UPDATE, DELETE.
    Utilisée par des fonctions plus spécifiques.
    """
    with connexion.cursor() as cursor:
        try:
            cursor.execute(query, params)
            result = cursor.rowcount
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None

def get_instances(connexion, nom_table):
    """
    Retourne les instances de la table nom_table
    String nom_table : nom de la table
    """
    query = sql.SQL('SELECT * FROM {table}').format(table=sql.Identifier(nom_table), )
    return execute_select_query(connexion, query)

def count_instances(connexion, nom_table):
    """
    Retourne le nombre d'instances de la table nom_table
    String nom_table : nom de la table
    """
    query = sql.SQL('SELECT COUNT(*) AS nb FROM {table}').format(table=sql.Identifier(nom_table))
    return execute_select_query(connexion, query)

def get_episodes_for_num(connexion, numero):
    """
    Retourne le titre des épisodes numérotés numero
    Integer numero : numéro des épisodes
    """
    query = 'SELECT titre FROM episodes where numéro=%s'
    return execute_select_query(connexion, query, [numero])

def get_serie_by_name(connexion, nom_serie):
    """
    Retourne les informations sur la série nom_serie (utilisé pour vérifier qu'une série existe)
    String nom_serie : nom de la série
    """
    query = 'SELECT * FROM series where nomsérie=%s'
    return execute_select_query(connexion, query, [nom_serie])

def insert_serie(connexion, nom_serie):
    """
    Insère une nouvelle série dans la BD
    String nom_serie : nom de la série
    Retourne le nombre de tuples insérés, ou None
    """
    query = 'INSERT INTO series VALUES(%s)'
    return execute_other_query(connexion, query, [nom_serie])

def get_table_like(connexion, nom_table, like_pattern):
    """
    Retourne les instances de la table nom_table dont le nom correspond au motif like_pattern
    String nom_table : nom de la table
    String like_pattern : motif pour une requête LIKE
    """
    motif = '%' + like_pattern + '%'
    nom_att = 'nomsérie'  # nom attribut dans séries (à éviter)
    if nom_table == 'actrices':  # à éviter
        nom_att = 'nom'  # nom attribut dans actrices (à éviter)
    query = sql.SQL("SELECT * FROM {} WHERE {} ILIKE {}").format(
        sql.Identifier(nom_table),
        sql.Identifier(nom_att),
        sql.Placeholder())
    #    like_pattern=sql.Placeholder(name=like_pattern))
    return execute_select_query(connexion, query, [motif])


def get_table_counts(connexion, mappings):
    """
    Retourne une liste de dictionnaires {"label": ..., "value": ...}
    pour chaque table listée dans mappings (liste de tuples (label, nom_table)).
    """
    resultat = []
    for label, table in mappings:
        rows = count_instances(connexion, table) or []
        valeur = rows[0][0] if rows else 0
        resultat.append({"label": label, "value": valeur})
    return resultat


def get_top_equipes(connexion, limite=3):
    """
    Renvoie les équipes ordonnées par nombre de victoires (limitées à `limite`).
    Chaque élément est un dict {nom, couleur, victoires}.
    """
    query = """
        SELECT e.nom,
               e.couleur,
               COUNT(p.id_partie) AS victoires
        FROM equipe e
        LEFT JOIN partie p ON p.id_equipe_gagnante = e.id_equipe
        GROUP BY e.id_equipe, e.nom, e.couleur
        ORDER BY victoires DESC, e.nom ASC
        LIMIT %s
    """
    rows = execute_select_query(connexion, query, [limite]) or []
    return [{"nom": row[0], "couleur": row[1], "victoires": row[2]} for row in rows]


def get_partie_par_duree(connexion, ordre="ASC"):
    """
    Renvoie la partie terminée la plus courte (ordre="ASC") ou la plus longue (ordre="DESC").
    Retourne None si aucune partie terminée n'existe.
    """
    ordre = ordre.upper() # uper pr transformer la chaine en majuscule
    if ordre not in ("ASC", "DESC"):
        ordre = "ASC"
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
        ORDER BY duree_sec {ordre}
        LIMIT 1
    """
    rows = execute_select_query(connexion, query, []) or [] # [] : la liste de paramètres (vide :%s dans cette requête : NN) 
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row[0],
        "equipe1": row[1],
        "equipe2": row[2],
        "duree_sec": row[3],
        "date_fin": row[4],
    }


def get_journal_stats(connexion):
    """
    Renvoie les statistiques issues de la vue v_journal_par_mois déjà formatées pour le template.
    """
    query = """
        SELECT annee, mois, nb_lignes_total, nb_parties, nb_moyen_lignes
        FROM v_journal_par_mois
        ORDER BY annee DESC, mois DESC
    """
    rows = execute_select_query(connexion, query, []) or []
    stats = []
    for row in rows:
        stats.append(
            {
                "annee": int(row[0]),
                "mois": int(row[1]),
                "nb_lignes": int(row[2]),
                "nb_parties": int(row[3]),
                "nb_moyen": round(float(row[4]), 2), # round pr arrondir a deux decimal
            }
        )
    return stats



