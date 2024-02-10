from django.http import JsonResponse

def home(request):
    api_paths = [
        {"path": "generate_edt/", "POST": "[{'id_banque': int, 'semaine': int, 'annee': int}]"},
        {"path": "admin/", "POST": "[{'id_banque': int, 'semaine': int, 'annee': int}]"},

        {"path": "login/", "POST": "{'email': string, 'password': string}"},
        {"path": "register/", "POST": "{'prenom': string, 'nom': string, 'email': string, 'mot_de_passe': string, 'id_role': int}"},
        {"path": "reset_password/", "POST": "{'email': string, 'ancien_mdp': string, 'nouveau_mdp': string}"},

        {"path": "enseignes/", "POST": "{'idUtilisateur': int, 'idRessources': [int]}"},

        {"path": "salles/", "GET": ""},
        {"path": "salle/<int:code>/", "GET": ""},
        {"path": "salle/<int:code>/", "PUT": "{'nom': string}"},
        {"path": "salle/<int:code>/", "DETETE": ""},
        {"path": "salle/", "POST": "{'nom': string}"},

        {"path": "utilisateurs/", "GET": ""},
        {"path": "utilisateurs/professeur/", "GET": ""},
        {"path": "utilisateurs/professeur/<int:code>/ressource/", "GET": ""},
        {"path": "utilisateurs/professeurs/ressources/", "GET": ""},
        {"path": "utilisateurs/etudiant/", "GET": ""},
        {"path": "utilisateur/<int:code>/", "GET": ""},
        {"path": "utilisateur/<int:code>/", "PUT": "{'prenom': string,'nom': string,'email': string,'mot_de_passe': string,'id_role': int,'id_groupe': int}"},
        {"path": "utilisateur/<int:code>/", "DELETE": ""},
        {"path": "utilisateur/", "POST": "{'prenom': string,'nom': string,'email': string,'mot_de_passe': string,'id_role': int,'id_groupe': int}"},

        {"path": "indisponibilites/", "GET": ""},
        {"path": "indisponibilite/<int:code>/", "GET": ""},
        {"path": "indisponibilite/<int:code>/", "PUT": "{'date_debut': string,'date_fin': string,'id_utilisateur': int}"},
        {"path": "indisponibilite/<int:code>/", "DELETE": ""},
        {"path": "indisponibilite/", "POST": "[{'date_debut': string,'date_fin': string,'id_utilisateur': int}]"},

        {"path": "ressources/", "GET": ""},
        {"path": "ressource/<int:code>/", "GET": ""},
        {"path": "ressource/<int:code>/", "PUT": "{'libelle': string,'nom': string}"},
        {"path": "ressource/<int:code>/", "DELETE": ""},
        {"path": "ressource/", "POST": "{'libelle': string,'nom': string}"},

        {"path": "cours/", "GET": ""},
        {"path": "cours/<int:code>/", "GET": ""},
        {"path": "cours/<int:code>/", "PUT": "{'numero_jour': string,'heure_debut': string,'id_banque': int,'id_edt': int,'id_groupe': int}"},
        {"path": "cours/<int:code>/", "DELETE": ""},
        {"path": "cours/", "POST": "{'numero_jour': string,'heure_debut': string,'id_banque': int,'id_edt': int,'id_groupe': int}"},

        {"path": "groupes/", "GET": ""},
        {"path": "groupe/<int:code>/", "GET": ""},
        {"path": "groupe/<int:code>/", "PUT": "{'nom': string,'id_salle': int,'id_groupe_superieur': int}"},
        {"path": "groupe/<int:code>/", "DELETE": ""},
        {"path": "groupe/", "POST": "{'nom': string,'id_salle': int,'id_groupe_superieur': int}"},

        {"path": "emploidutemps/", "GET": ""},
        {"path": "emploidutemp/<int:code>/", "GET": ""},
        {"path": "emploidutemp/<int:code>/", "PUT": "{'date': string,'version': int}"},
        {"path": "emploidutemp/<int:code>/", "DELETE": ""},
        {"path": "emploidutemp/", "POST": "{'date': string,'version': int}"},

        {"path": "banques/", "GET": ""},
        {"path": "banque/<int:code>/", "GET": ""},
        {"path": "banque/<int:code>/", "PUT": "{'id_utilisateur': int,'id_ressource': int,'id_type_cours': int,'duree': int,'id_couleur': int}"},
        {"path": "banque/<int:code>/", "DELETE": ""},
        {"path": "banque/", "POST": "{'id_utilisateur': int,'id_ressource': int,'id_type_cours': int,'duree': int,'id_couleur': int}"},

        {"path": "typecours/", "GET": ""},
        {"path": "typecour/<int:code>/", "GET": ""},
        {"path": "typecour/<int:code>/", "PUT": "{'nom': string}"},
        {"path": "typecour/<int:code>/", "DELETE": ""},
        {"path": "typecour/", "POST": "{'nom': string}"},

        {"path": "couleurs/", "GET": ""},
        {"path": "couleur/<int:code>/", "GET": ""},
        {"path": "couleur/<int:code>/", "PUT": "{'nom': string, 'couleur_hexa': string}"},
        {"path": "couleur/<int:code>/", "DELETE": ""},
        {"path": "couleur/", "POST": "{'nom': string, 'couleur_hexa': string}"},
    ]
    # db = Database.get()
    # print(db.run("SELECT * FROM Salle").fetch())
    # db.close()
    return JsonResponse(api_paths, safe=False)

