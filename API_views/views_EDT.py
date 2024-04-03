import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@method_awaited("GET")
def get_all_by_semaine(request, semaine: int, annee: int):
    db = Database.get()
	# Faire comme dans by_groupe mais pour tous les groupes
    sql = """
        SELECT g1.IdGroupe, g1.Nom as GroupeNom, s.Nom as SalleNom
		FROM Groupe as g1
		LEFT JOIN Salle as s ON g1.IdSalle = s.IdSalle
		WHERE g1.Nom NOT IN ('Professeur', 'Administrateur') 
    """
    groupes = db.run(sql).fetch()

    sql = """
        SELECT IdEDT
        FROM EDT
        WHERE Semaine = %s AND Annee = %s
    """
    db.run([sql, (semaine, annee)])
    if db.exists():
        id_EDT = db.fetch(first=True)['IdEDT']
    else:
        all_edt = {}
        for groupe in groupes:
            all_edt[groupe['IdGroupe']] = {
                "idGroupe": groupe['IdGroupe'],
                "salle": groupe['SalleNom'],
                "groupe": groupe['GroupeNom'],
                "cours": {
                    "Lundi": [],
                    "Mardi": [],
                    "Mercredi": [],
                    "Jeudi": [],
                    "Vendredi": [],
                    "Samedi": []
                }
            }
        return JsonResponse(all_edt, safe=False)

    all_edt = {}
    for groupe in groupes:
        edt = {
            "idGroupe": groupe['IdGroupe'],
            "salle": groupe['SalleNom'],
            "groupe": groupe['GroupeNom'],
            "cours": {
                "Lundi": [],
                "Mardi": [],
                "Mercredi": [],
                "Jeudi": [],
                "Vendredi": [],
                "Samedi": []
            }
        }
        
        sql = """
            SELECT IdCours, IdEDT, Groupe.IdGroupe, Groupe.Nom, Cours.IdBanque, NumeroJour, HeureDebut, Utilisateur.IdUtilisateur, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant, Duree, TypeCours.Nom AS type, CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS style, CONCAT(Ressource.Libelle,' - ',Ressource.Abreviation) AS abreviation
            FROM Cours
            JOIN Banque ON Cours.IdBanque = Banque.IdBanque
            JOIN Utilisateur ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
            JOIN TypeCours ON Banque.IdTypeCours = TypeCours.IdTypeCours
            JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
            JOIN Couleur ON Banque.IdCouleur = Couleur.IdCouleur 
            JOIN Groupe ON Cours.IdGroupe = Groupe.IdGroupe
            WHERE Groupe.IdGroupe = %s AND IdEDT = %s
        """
        cours = db.run([sql, (groupe['IdGroupe'], id_EDT)]).fetch()

        if not db.exists():
            all_edt[groupe['IdGroupe']] = edt.copy()
            continue

        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

        placed_courses = [ [None for _ in range(25)] for __ in range(6) ]
        for cours in cours:
            jour = days[cours["NumeroJour"]]
            cours_slots = [slot for slot in range(cours["HeureDebut"], cours["HeureDebut"] + cours["Duree"])]

            warning = None
            warning_message = None

            not_free_slots = [slot for slot in cours_slots if placed_courses[cours["NumeroJour"]][slot] is not None]
            if len(not_free_slots) > 0:
                if any([not_free_slot == groupe['IdGroupe'] for not_free_slot in not_free_slots]):
                    for not_free_slot in not_free_slots:
                        edt['cours'][jour][not_free_slot['index']]['warning'] = "Cours en conflit"
                        edt['cours'][jour][not_free_slot['index']]['warning_message'] = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."
                    continue
                else:
                    cours_to_remove = [not_free_slot['index'] for not_free_slot in not_free_slots]
                    correct_day = []
                    placed_courses[cours["NumeroJour"]] = [None for _ in range(25)]
                    for index, other_cours in enumerate(edt['cours'][jour]):
                        if index not in cours_to_remove:
                            correct_day.append(other_cours)
                            placed_courses[other_cours["NumeroJour"]][other_cours["HeureDebut"]] = {"groupe": other_cours["idGroupe"], "index": index}

                    edt['cours'][jour] = correct_day
                    warning = "Cours en conflit"
                    warning_message = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."
                
            for slot_index in cours_slots:
                placed_courses[cours["NumeroJour"]][slot_index] = {"groupe": cours["IdGroupe"], "index": len(edt['cours'][jour])}

            cours = {
                "id": "c" + str(cours["IdCours"]),
                "idEnseignant": cours["IdUtilisateur"],
                "idBanque": cours["IdBanque"],
                "enseignant": cours["enseignant"],
                "type": cours["type"],
                "libelle": cours["libelle"],
                "abreviation": cours["abreviation"],
                "heureDebut": cours["HeureDebut"],
                "duree": cours["Duree"],
                "style": cours["style"],
                "warning": warning,
                "warning_message": warning_message,
            }
            edt['cours'][jour].append(cours)
        
        all_edt[groupe['IdGroupe']] = edt.copy()


    db.close()
    return JsonResponse(all_edt, safe=False)


# Get by Semaine, Annee, idGroupe
@csrf_exempt
@method_awaited("GET")
def by_groupe(request, semaine: int, annee: int, idGroupe: int):
    db = Database.get()

    # Récupération de la salle
    sql_get_salle = "SELECT s.Nom as snom FROM Groupe as g1 LEFT JOIN Salle as s ON g1.IdSalle = s.IdSalle WHERE g1.IdGroupe = %s"
    salle_name = db.run([sql_get_salle, (idGroupe,)]).fetch(first=True)['snom']
    
    edt = {
        "salle": salle_name,
        "groupe": "", # TODO : Récupérer le nom du groupe
        "cours": {
            "Lundi": [],
            "Mardi": [],
            "Mercredi": [],
            "Jeudi": [],
            "Vendredi": [],
            "Samedi": []
        }
    }
    
	# Récupération de l'ID EDT
    sqlDateEDT = "SELECT IdEDT as id FROM EDT WHERE Semaine = %s AND Annee = %s"
    db.run([sqlDateEDT, (semaine, annee)])
    	
    if db.exists():
        id_EDT = db.fetch(first=True)['id']
    else:
        db.close()
        return JsonResponse(edt, safe=False)
    
    # Le nom du groupe
    sql_get_groupe = "SELECT * FROM Groupe WHERE IdGroupe = %s"
    db.run([sql_get_groupe, (idGroupe,)])

    if not db.exists():
        return JsonResponse({"error": "data not found", "message": "le groupe n'a pas été retrouvé"}, safe=False)
    edt["groupe"] = db.fetch(first=True)['Nom']

    # Il faut récupérer les cours des parents aussi
    # On va refaire la requête avec un Union
    # Etape 1: Récupérer les parents du groupe
    # Groupe Parent: None --> 1 --> 13 --> 4 --> feuille;
    # On connait la feuille, on remonte jusqu'à None
    sql_get_group = "SELECT * FROM Groupe WHERE IdGroupe = %s"
    all_groupes = []
    current_groupe = db.run([sql_get_group, (idGroupe,)]).fetch(first=True)
    all_groupes.append(str(current_groupe['IdGroupe']))

    while current_groupe['IdGroupeSuperieur'] is not None:
        db.run([sql_get_group, (current_groupe['IdGroupeSuperieur'],)])

        if not db.exists():
            return JsonResponse({"error": "data not found", "message": f"le groupe parent n'a pas été retrouvé, base de donnée corrompue: {current_groupe}"}, safe=False)
        current_groupe = db.fetch(first=True)
        all_groupes.append(str(current_groupe['IdGroupe']))
    
    # Etape 2: Récupérer les cours et les banques de cours
    sql_get_parents_cours = f"""
        SELECT IdCours, IdEDT, Groupe.IdGroupe, Groupe.Nom, Cours.IdBanque, NumeroJour, HeureDebut, Utilisateur.IdUtilisateur, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant, Duree, TypeCours.Nom AS type, CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS style, CONCAT(Ressource.Libelle,' - ',Ressource.Abreviation) AS abreviation
        FROM Cours
        JOIN Banque ON Cours.IdBanque = Banque.IdBanque
        JOIN Utilisateur ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
        JOIN TypeCours ON Banque.IdTypeCours = TypeCours.IdTypeCours
        JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
        JOIN Couleur ON Banque.IdCouleur = Couleur.IdCouleur 
        JOIN Groupe ON Cours.IdGroupe = Groupe.IdGroupe
        WHERE Groupe.IdGroupe IN ({", ".join(all_groupes)}) AND IdEDT = %s
    """
    cours = db.run([sql_get_parents_cours, (id_EDT,)]).fetch()

    if not db.exists():
        return JsonResponse(edt, safe=False)

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    placed_courses = [ [None for _ in range(25)] for __ in range(6) ]
    for cours in cours:
        jour = days[cours["NumeroJour"]]
        cours_slots = [slot for slot in range(cours["HeureDebut"], cours["HeureDebut"] + cours["Duree"])]
        
        warning = None
        warning_message = None

        not_free_slots = [slot for slot in cours_slots if placed_courses[cours["NumeroJour"]][slot] is not None]
        conflicts_groupes = [placed_courses[cours["NumeroJour"]][slot]['groupe'] for slot in not_free_slots]
        """Liste des slots déjà utilisés par un autre cours [4, 5] superposé à cours_slots"""
        if len(not_free_slots) > 0:

            # On cherche à savoir si le cours a priorité (enfant) ou si à l'inverse avec des parents
            if any([conflict_groupe == idGroupe for conflict_groupe in conflicts_groupes]):
                for not_free_slot in not_free_slots:
                    edt['cours'][jour][not_free_slot['index']]['warning'] = "Cours en conflit"
                    edt['cours'][jour][not_free_slot['index']]['warning_message'] = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."
                    continue
            else:
                cours_to_remove = [not_free_slot['index'] for not_free_slot in not_free_slots]
                correct_day = []
                placed_courses[cours["NumeroJour"]] = [None for _ in range(25)]
                for index, other_cours in enumerate(edt['cours'][jour]):
                    if index not in cours_to_remove:
                        correct_day.append(other_cours)
                        placed_courses[other_cours["NumeroJour"]][other_cours["HeureDebut"]] = {"groupe": other_cours["idGroupe"], "index": index}

                edt['cours'][jour] = correct_day
                warning = "Cours en conflit"
                warning_message = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."

        for slot_index in cours_slots:
            placed_courses[cours["NumeroJour"]][slot_index] = {"groupe": cours["IdGroupe"], "index": len(edt['cours'][jour])}

        cours = {
            "id": "c" + str(cours["IdCours"]),
            "idEnseignant": cours["IdUtilisateur"],
            "idBanque": cours["IdBanque"],
            "enseignant": cours["enseignant"],
            "type": cours["type"],
            "libelle": cours["libelle"],
            "abreviation": cours["abreviation"],
            "heureDebut": cours["HeureDebut"],
            "duree": cours["Duree"],
            "style": cours["style"],
            "warning": warning,
            "warning_message": warning_message,
        }
        edt['cours'][jour].append(cours)

    db.close()
    return JsonResponse(edt, safe=False)

# Get by Semaine, Annee, idGroupe
@csrf_exempt
@method_awaited("PUT")
def by_list_groupe(request, semaine: int, annee: int):
    # {
    #     "listGroupe": [1, 10, 16, 17]
    # }
    listGroupe = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        listGroupe = body['listGroupe']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()

    # Récupération de la salle
    formatListGroupe = ', '.join([str(int(groupe)) for groupe in listGroupe])
    sql_get_salle = f"SELECT IdGroupe, s.Nom as snom FROM Groupe as g1 LEFT JOIN Salle as s ON g1.IdSalle = s.IdSalle WHERE g1.IdGroupe IN ({formatListGroupe})"
    salle_name = db.run(sql_get_salle).fetch()
    
    # Récupération des groupes
    sql_get_groupe = f"SELECT * FROM Groupe WHERE IdGroupe IN ({formatListGroupe})"
    groupes_data = db.run(sql_get_groupe).fetch()

    all_edt = {}
    for groupe in groupes_data:
        all_edt[groupe['IdGroupe']] = {
            "idGroupe": groupe['IdGroupe'],
            "salle": next((item for item in salle_name if item["IdGroupe"] == groupe["IdGroupe"]), None)['snom'],
            "groupe": groupe['Nom'],
            "cours": {
                "Lundi": [],
                "Mardi": [],
                "Mercredi": [],
                "Jeudi": [],
                "Vendredi": [],
                "Samedi": []
            }
        }
    
	# Récupération de l'ID EDT
    sqlDateEDT = "SELECT IdEDT as id FROM EDT WHERE Semaine = %s AND Annee = %s"
    db.run([sqlDateEDT, (semaine, annee)])
    	
    if db.exists():
        id_EDT = db.fetch(first=True)['id']
    else:
        db.close()
        return JsonResponse(all_edt, safe=False)

    # Etape 2: Récupérer les cours et les banques de cours
    sql_get_cours = f"""
        SELECT IdCours, IdEDT, Groupe.IdGroupe, Groupe.Nom, Cours.IdBanque, NumeroJour, HeureDebut, Utilisateur.IdUtilisateur, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant, Duree, TypeCours.Nom AS type, CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS style, CONCAT(Ressource.Libelle,' - ',Ressource.Abreviation) AS abreviation
        FROM Cours
        JOIN Banque ON Cours.IdBanque = Banque.IdBanque
        JOIN Utilisateur ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
        JOIN TypeCours ON Banque.IdTypeCours = TypeCours.IdTypeCours
        JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
        JOIN Couleur ON Banque.IdCouleur = Couleur.IdCouleur 
        JOIN Groupe ON Cours.IdGroupe = Groupe.IdGroupe
        WHERE Groupe.IdGroupe IN ({formatListGroupe}) AND IdEDT = %s
    """
    all_cours = db.run([sql_get_cours, (id_EDT,)]).fetch()

    if not db.exists():
        return JsonResponse(all_edt, safe=False)

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    for groupe in groupes_data:
        placed_courses = [ [None for _ in range(25)] for __ in range(6) ]
        idGroupe = groupe['IdGroupe']
        for cours in all_cours:
            jour = days[cours["NumeroJour"]]
            cours_slots = [slot for slot in range(cours["HeureDebut"], cours["HeureDebut"] + cours["Duree"])]
            """Liste des slots utilisés par le cours [3, 4, 5, 6]"""
            
            warning = None
            warning_message = None

            not_free_slots = [slot for slot in cours_slots if placed_courses[cours["NumeroJour"]][slot] is not None]
            conflicts_groupes = [placed_courses[cours["NumeroJour"]][slot]['groupe'] for slot in not_free_slots]
            """Liste des slots déjà utilisés par un autre cours [4, 5] superposé à cours_slots"""
            if len(not_free_slots) > 0:
                # On cherche à savoir si le cours a priorité (enfant) ou si à l'inverse avec des parents
                if any([conflict_groupe == idGroupe for conflict_groupe in conflicts_groupes]):
                    for other_cours in all_edt[idGroupe]['cours'][jour]:
                        other_cours_hours = [slot for slot in range(other_cours["heureDebut"], other_cours["heureDebut"] + other_cours["duree"])]
                        if any([slot in other_cours_hours for slot in not_free_slots]):
                            other_cours['warning'] = "Cours en conflit"
                            other_cours['warning_message'] = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."
                else:
                    correct_day = []
                    placed_courses[cours["NumeroJour"]] = [None for _ in range(25)]

                    for index, other_cours in enumerate(all_edt[idGroupe]['cours'][jour]):
                        other_cours_hours = [slot for slot in range(other_cours["heureDebut"], other_cours["heureDebut"] + other_cours["duree"])]
                        if any([slot in other_cours_hours for slot in not_free_slots]):
                            correct_day.append(other_cours)
                            placed_courses[cours["NumeroJour"]][other_cours["heureDebut"]] = {"groupe": idGroupe, "index": index}

                    all_edt[idGroupe]['cours'][jour] = correct_day
                    warning = "Cours en conflit"
                    warning_message = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette heure."

            for slot_index in cours_slots:
                placed_courses[cours["NumeroJour"]][slot_index] = {"groupe": cours["IdGroupe"], "index": len(all_edt[idGroupe]['cours'][jour])}

            cours = {
                "id": "c" + str(cours["IdCours"]),
                "idEnseignant": cours["IdUtilisateur"],
                "idBanque": cours["IdBanque"],
                "enseignant": cours["enseignant"],
                "type": cours["type"],
                "libelle": cours["libelle"],
                "abreviation": cours["abreviation"],
                "heureDebut": cours["HeureDebut"],
                "duree": cours["Duree"],
                "style": cours["style"],
                "warning": warning,
                "warning_message": warning_message,
            }
            all_edt[idGroupe]['cours'][jour].append(cours)

    db.close()
    return JsonResponse(all_edt, safe=False)


@csrf_exempt
@method_awaited("GET")
def by_enseignant(request, semaine: int, annee: int, idProf: int):
    db = Database.get()
    
    edt = {
        "cours": {
            "Lundi": [],
            "Mardi": [],
            "Mercredi": [],
            "Jeudi": [],
            "Vendredi": [],
            "Samedi": []
        }
    }
    
	# Récupération de l'ID EDT
    sqlDateEDT = "SELECT IdEDT as id FROM EDT WHERE Semaine = %s AND Annee = %s"
    db.run([sqlDateEDT, (semaine, annee)])
    	
    if db.exists():
        id_EDT = db.fetch(first=True)['id']
    else:
        db.close()
        return JsonResponse(edt, safe=False)
    
    # Etape 1: Récupérer les cours et les banques de cours
    sql_get_parents_cours = f"""
        SELECT IdCours, IdEDT, Groupe.nom as gnom, Salle.nom as snom, Cours.IdBanque, NumeroJour, HeureDebut, Utilisateur.IdUtilisateur, Duree, TypeCours.Nom AS type, CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant, Couleur.CouleurHexa AS style, CONCAT(Ressource.Libelle,' - ',Ressource.Abreviation) AS abreviation
        FROM Cours
        JOIN Banque ON Cours.IdBanque = Banque.IdBanque
        JOIN Utilisateur ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
        JOIN TypeCours ON Banque.IdTypeCours = TypeCours.IdTypeCours
        JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
        JOIN Couleur ON Banque.IdCouleur = Couleur.IdCouleur 
        JOIN Groupe ON Cours.IdGroupe = Groupe.IdGroupe
        JOIN Salle ON Groupe.IdSalle = Salle.IdSalle
        WHERE IdEDT = %s AND Utilisateur.IdUtilisateur = %s
    """
    cours = db.run([sql_get_parents_cours, (id_EDT, idProf,)]).fetch()

    if not db.exists():
        return JsonResponse(edt, safe=False)

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    for cours in cours:
        jour = days[cours["NumeroJour"]]

        cours = {
            "id": "c" + str(cours["IdCours"]),
            "enseignant": cours["enseignant"],
            "idBanque": cours["IdBanque"],
            "groupe": cours["gnom"],
            "salle": cours["snom"],
            "type": cours["type"],
            "libelle": cours["libelle"],
            "abreviation": cours["abreviation"],
            "heureDebut": cours["HeureDebut"],
            "duree": cours["Duree"],
            "style": cours["style"],
        }
        edt['cours'][jour].append(cours)

    db.close()
    return JsonResponse(edt, safe=False)


@csrf_exempt
@method_awaited("GET")
def by_enseignant(request, semaine: int, annee: int, idProf: int):
    db = Database.get()
    
    edt = {
        "cours": {
            "Lundi": [],
            "Mardi": [],
            "Mercredi": [],
            "Jeudi": [],
            "Vendredi": [],
            "Samedi": []
        }
    }
    
	# Récupération de l'ID EDT
    sqlDateEDT = "SELECT IdEDT as id FROM EDT WHERE Semaine = %s AND Annee = %s"
    db.run([sqlDateEDT, (semaine, annee)])
    	
    if db.exists():
        id_EDT = db.fetch(first=True)['id']
    else:
        db.close()
        return JsonResponse(edt, safe=False)
    
    # Etape 1: Récupérer les cours et les banques de cours
    sql_get_parents_cours = f"""
        SELECT IdCours, IdEDT, Groupe.nom as gnom, Salle.nom as snom, Cours.IdBanque, NumeroJour, HeureDebut, Utilisateur.IdUtilisateur, Duree, TypeCours.Nom AS type, CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS style, CONCAT(Ressource.Libelle,' - ',Ressource.Abreviation) AS abreviation
        FROM Cours
        JOIN Banque ON Cours.IdBanque = Banque.IdBanque
        JOIN Utilisateur ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
        JOIN TypeCours ON Banque.IdTypeCours = TypeCours.IdTypeCours
        JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
        JOIN Couleur ON Banque.IdCouleur = Couleur.IdCouleur 
        JOIN Groupe ON Cours.IdGroupe = Groupe.IdGroupe
        JOIN Salle ON Groupe.IdSalle = Salle.IdSalle
        WHERE IdEDT = %s AND Utilisateur.IdUtilisateur = %s
    """
    cours = db.run([sql_get_parents_cours, (id_EDT, idProf,)]).fetch()

    if not db.exists():
        return JsonResponse(edt, safe=False)

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    for cours in cours:
        jour = days[cours["NumeroJour"]]

        cours = {
            "id": "c" + str(cours["IdCours"]),
            "idBanque": cours["IdBanque"],
            "groupe": cours["gnom"],
            "salle": cours["snom"],
            "type": cours["type"],
            "libelle": cours["libelle"],
            "abreviation": cours["abreviation"],
            "heureDebut": cours["HeureDebut"],
            "duree": cours["Duree"],
            "style": cours["style"],
        }
        edt['cours'][jour].append(cours)

    db.close()
    return JsonResponse(edt, safe=False)


# Get by Id, Delete by Id, Update by Id
@csrf_exempt
@method_awaited(["GET", "DELETE", "PUT"])
def by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
            SELECT *
            FROM EDT 
            WHERE EDT.IdEDT = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_edt = """
        DELETE
        FROM EDT 
        WHERE EDT.IdEDT = %s;
        """
        sql_cours = """
        DELETE
        FROM Cours 
        WHERE Cours.IdEDT = %s;
            """

        db.run([sql_cours, (code,)]).fetch()
        nb_row_affected = db.run([sql_edt, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        date = ""
        version = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            date = body['date']
            version = body['version']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE EDT
                    SET EDT.DateEDT = %s,
                        EDT.Version = %s
                    WHERE EDT.IdEDT = %s
                """
        nb_row_affected = db.run([sql, (date, version, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@method_awaited("POST")
def add(request):
    date = ""
    version = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        date = body['date']
        version = body['version']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
        INSERT INTO EDT (DateEDT, Version) VALUES
        (%s,%s);
    """
    try:
        nb_row_affected = db.run([sql, (date, version)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error":"An error has occurred during the process."}, safe=False)


@csrf_exempt
@method_awaited("PUT")
def save_edt(request, groupe, semaine, annee):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    sql = """
        SELECT IdEDT FROM EDT WHERE Semaine = %s AND Annee = %s;
    """

    db = Database.get()
    db.run([sql, (semaine, annee)])
    if not db.exists():
        sql = """
            INSERT INTO EDT (Semaine, Annee) VALUES (%s, %s);
        """

        db.run([sql, (semaine, annee)])
        edt_id = db.last_id()
    else:
        edt_id = db.fetch(first=True)['IdEDT']
        sql = """
            DELETE FROM Cours WHERE IdEDT = %s AND IdGroupe = %s;
        """
        db.run([sql, (edt_id, groupe)])

    jours_id = {
        "Lundi": 0,
        "Mardi": 1,
        "Mercredi": 2,
        "Jeudi": 3,
        "Vendredi": 4,
        "Samedi": 5
    }

    sql = """
        INSERT INTO Cours (NumeroJour, HeureDebut, IdBanque, IdEDT, IdGroupe)
        VALUES (%s, %s, %s, %s, %s);
    """
    for jour, cours in body.items():
        for cours_data in cours:
            db.run([sql, (jours_id[jour], cours_data['heureDebut'], cours_data['idBanque'], edt_id, groupe)])
    db.close()
    return JsonResponse(True, safe=False)
