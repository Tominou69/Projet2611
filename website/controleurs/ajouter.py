from model.model_pg import get_serie_by_name, insert_serie
from controleurs.includes import add_activity


add_activity(SESSION['HISTORIQUE'], "consultation de la page ajouter série")

if POST and 'bouton_valider' in POST:  # formulaire soumis
    nom_serie = POST['nom_serie'][0]  # attention, un <input> retourne une liste
    serie_existe = get_serie_by_name(SESSION['CONNEXION'], nom_serie)
    print(serie_existe)
    if serie_existe is not None and len(serie_existe) == 0:  # pas de série avec ce nom
        serie_ajout = insert_serie(SESSION['CONNEXION'], nom_serie)
        if serie_ajout and serie_ajout > 0:  # insertion réussie
            REQUEST_VARS['message'] = f"La série {nom_serie} a bien été ajoutée !"
            REQUEST_VARS['message_class'] = "alert-success"
        else:  # erreur insertion
            REQUEST_VARS['message'] = f"Erreur lors de l'insertion de la série {nom_serie}."
            REQUEST_VARS['message_class'] = "alert-error"
    else:  # série déjà existante
        REQUEST_VARS['message'] = f"Erreur : une série existe déjà avec ce nom ({nom_serie})."
        REQUEST_VARS['message_class'] = "alert-error"


