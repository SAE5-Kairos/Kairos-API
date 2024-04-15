import json
from django.http import JsonResponse

from EDT_generator.V2.generateur import Worker, get_worker_data, best_edt, best_score
from EDT_generator.V2.edt2 import EDT2
from EDT_generator.V2.cours2 import Cours2
from EDT_generator.V2.professeur2 import Professeur2
from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

# JSON EDT:
# - S'il y a la clef "error" cela signifie que lors de la récupération de l'EDT une erreur est survenue,
#   le message d'erreur est alors dans la valeur de la clef "error"

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

    all_edt = {}
    for groupe in groupes:
        try:
            edt = get_edt(groupe['IdGroupe'], semaine, annee, db)
        except Exception as e:
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
                },
                "error": str(e)
            }
        all_edt[groupe['IdGroupe']] = edt
    db.close()
    return JsonResponse(all_edt, safe=False)

# Get by Semaine, Annee, idGroupe
@csrf_exempt
@method_awaited("GET")
def by_groupe(request, semaine: int, annee: int, idGroupe: int):
    edt = get_edt(idGroupe, semaine, annee)
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

    all_edt = {}
    for groupe in listGroupe:
        try:
            edt = get_edt(groupe, semaine, annee)
        except Exception as e:
            edt = {
                "idGroupe": groupe,
                "cours": {
                    "Lundi": [],
                    "Mardi": [],
                    "Mercredi": [],
                    "Jeudi": [],
                    "Vendredi": [],
                    "Samedi": []
                },
                "error": str(e)
            }
        all_edt[groupe] = edt
    return JsonResponse(all_edt, safe=False)


@csrf_exempt
@method_awaited("GET")
def by_enseignant(request, semaine: int, annee: int, idProf: int):
    # TODO: à vérifier
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

    save_one_edt(groupe, annee, semaine, body)

    return JsonResponse(True, safe=False)

@csrf_exempt
@method_awaited("PUT")
def save_all_edt(request, semaine, annee):
    db = Database.get()
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    for groupe, week in body.items():
        save_one_edt(groupe, annee, semaine, week, db)
    
    db.close()
    return JsonResponse(True, safe=False)

def save_one_edt(groupe: int, annee: int, semaine: int, week: dict, db: Database=None):
    close_db = False
    
    if db is None: 
        db = Database.get()
        close_db = True

    # 1. Créer l'EDT si il n'existe pas sinon récupérer son id et supprimer les cours
    sql = """
        SELECT IdEDT FROM EDT WHERE Semaine = %s AND Annee = %s;
    """
    db.run([sql, (semaine, annee)])
    if not db.exists():
        sql = """
            INSERT INTO EDT (Semaine, Annee) VALUES (%s, %s);
        """
        db.run([sql, (semaine, annee)])
        id_edt = db.last_id()
    else:
        id_edt = db.fetch(first=True)['IdEDT']
        sql = """
            DELETE FROM Cours WHERE IdEDT = %s AND IdGroupe = %s;
        """
        db.run([sql, (id_edt, groupe)])
    
    # 2. Ajouter les cours
    sql = """
        INSERT INTO Cours (IdBanque, IdEDT, NumeroJour, HeureDebut, IdGroupe) VALUES (%s, %s, %s, %s, %s);
    """
    for jour, all_cours in enumerate(week.values()):
        for cours in all_cours:
            db.run([sql, (cours['idBanque'], id_edt, jour, cours['heureDebut'], groupe)])
    
    if close_db: db.close()


def get_edt(id_groupe: int, semaine: int, annee: int, db:Database=None):
    """
    Récupère l'emploie du temps d'un groupe
    :param id_groupe: int
    :param semaine: int
    :param annee: int
    :return: dict (json) de l'emploie du temps du groupe
    :errors: Exception si le groupe n'existe pas, si la base de donnée est corrompue
    """

    sql = """
        SELECT g1.Nom as GroupeNom, s.Nom as SalleNom
		FROM Groupe as g1
		LEFT JOIN Salle as s ON g1.IdSalle = s.IdSalle
		WHERE g1.Nom NOT IN ('Professeur', 'Administrateur') AND IdGroupe = %s 
    """
    
    close_db = False
    if db is None:
        db = Database.get()
        close_db = True

    db.run([sql, (id_groupe, )])

    if not db.exists(): raise Exception('Le groupe sélectionné n\'existe pas')
    groupe_info = db.fetch(first=True)

    edt = {
        "idGroupe": id_groupe,
        "salle": groupe_info['SalleNom'],
        "groupe": groupe_info['GroupeNom'],
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
        SELECT IdEDT
        FROM EDT
        WHERE Semaine = %s AND Annee = %s
    """
    db.run([sql, (semaine, annee)])
    
    if not db.exists(): edt["info"] = f"Aucun edt n'a été créé pour la semaine {semaine} de l'année {annee}"; return edt

    id_EDT = db.fetch(first=True)['IdEDT']
    
    # 1. Récupérer les groupes parents
    groupes = []
    """groupe enfant -> groupe parent -> groupe parent parent -> ... """

    sql_get_group = "SELECT * FROM Groupe WHERE IdGroupe = %s"
    current_groupe = db.run([sql_get_group, (id_groupe,)]).fetch(first=True)
    groupes.append(current_groupe)

    while current_groupe['IdGroupeSuperieur'] is not None:
        db.run([sql_get_group, (current_groupe['IdGroupeSuperieur'],)])

        if not db.exists():
            raise Exception(f"le groupe parent n'a pas été retrouvé, base de donnée corrompue: {current_groupe}")
        current_groupe = db.fetch(first=True)
        groupes.append(current_groupe)
    
    # 2. Créer l'emploie du temps (utilisation de la classe EDT du générateur pour se servir de son gestionnaire de contraintes)
    edt_obj = EDT2()

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
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

    for groupe in groupes:
        # 2.1 Récupérer les cours du groupes
        all_cours = db.run([sql, (groupe['IdGroupe'], id_EDT)]).fetch()

        # 3. Ajouter les cours à l'EDT
        for cours in all_cours:
            cours_obj = Cours2(
                Professeur2(cours["IdUtilisateur"], cours['enseignant']), duree=cours["Duree"], name=cours['libelle'], 
                id_banque=cours['IdBanque'], couleur=cours["style"], type_cours=cours["type"], 
                abrevaition=cours["abreviation"], groupe=cours['IdGroupe']
            )

            if edt_obj.is_free(cours['NumeroJour'], cours["HeureDebut"], cours_obj) == 1:
                edt_obj.add_cours(cours_obj, cours['NumeroJour'], cours["HeureDebut"])
            
            else:
                # Récupérer le cours déjà placé
                cours_deja_place = edt_obj.get_collided_courses(cours['NumeroJour'], cours["HeureDebut"], cours_obj)
                
                if cours['IdGroupe'] == id_groupe:
                    for placed_cours in cours_deja_place:
                        if placed_cours.id == cours_obj.id: continue
                        edt_obj.remove_cours(placed_cours)
                    
                    cours_obj.warning_message = "Ce cours est prioritaire par rapport a un certain nombre de cours parents: " + '; '.join([f'[{crs.groupe}] {crs.name}' for crs in cours_deja_place])
                    edt_obj.add_cours(cours_obj, cours['NumeroJour'], cours["HeureDebut"])
                else:
                    for placed_cours in cours_deja_place:
                        if placed_cours.id == cours_obj.id or placed_cours.groupe == cours_obj.groupe: continue
                        placed_cours.warning_message = f"Un cours ({cours['libelle']}) d'un ensemble de groupe parent ({cours['Nom']}) est placé à cette même heure mais n'a pas la priorité."
    
    for cours in edt_obj.cours:
        edt["cours"][jours[cours.jour]].append(cours.jsonify())
        
    if close_db: db.close()
    return edt
