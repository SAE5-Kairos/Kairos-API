import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def get_all_by_semaine(request, semaine: int, annee: int):
    db = Database.get()
    sqlDateEDT = "SELECT IdEDT as id, Semaine as semaine, Annee as annee FROM EDT WHERE Semaine = %s AND Annee = %s"
    
    dataEDT = db.run([sqlDateEDT, (semaine, annee)]).fetch()
    dataGroupe = db.run("SELECT IdGroupe as id, G.Nom as gnom, S.Nom as snom FROM Groupe as G LEFT JOIN Salle as S ON G.IdSalle = S.IdSalle").fetch()
    dataCours = db.run("SELECT IdCours as id, IdEDT as idEDT, IdGroupe as idGroupe, IdBanque as idBanque, NumeroJour as numeroJour, HeureDebut as heureDebut FROM Cours").fetch()
    dataBanqueCours = db.run("""
            SELECT IdBanque as id, Banque.IdUtilisateur as idEnseignant, CONCAT(Utilisateur.Nom, ' ', Utilisateur.Prenom) AS enseignant , Banque.Duree as duree, TypeCours.Nom AS 'type', CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS 'style'
            FROM Banque
            LEFT JOIN Utilisateur
            ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
            LEFT JOIN TypeCours
            ON Banque.IdTypeCours = TypeCours.IdTypeCours
            LEFT JOIN Ressource
            ON Banque.IdRessource = Ressource.IdRessource
            LEFT JOIN Couleur
            ON Banque.IdCouleur = Couleur.IdCouleur
            """).fetch()

    
    # [
    # idGroupe : 
    #     {
    #         idEdt: int,
    #         semaine: int,
    #         annee: int,
    #         salle: string,
    #         cours: {
    #             Lundi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ],
    #             Mardi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ],
    #             Mercredi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ],
    #             Jeudi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ],
    #             Vendredi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ],
    #             Samedi: [
    #                 {id: int, enseignant: string, type: string, libelle: string, heureDebut: string, duree: int, style: string}
    #             ]
    #         }
    #     }
    # ]
    # Je veux un tableau de groupe avec pour chaque groupe un tableau de cours
    
    # Initialisation du dictionnaire final
    groupes = {}

    # Parcourir tous les groupes
    for groupe in dataGroupe:
        if(groupe['gnom'] in ["Administrateur", "Professeur"]):
            continue

        # Initialiser le dictionnaire pour le groupe actuel
        groupes[groupe['id']] = {
            'idEdt': dataEDT[0]['id'], # TODO : On doit seulement récupérer un seul EDT
            'semaine': dataEDT[0]['semaine'], # TODO : On doit seulement récupérer un seul EDT
            'annee': dataEDT[0]['annee'], # TODO : On doit seulement récupérer un seul EDT
            'groupe': groupe['gnom'],
            'salle': groupe['snom'],
            'cours': {
                'Lundi': [],
                'Mardi': [],
                'Mercredi': [],
                'Jeudi': [],
                'Vendredi': [],
                'Samedi': []
            }
        }

    # Parcourir tous les cours
    for cours in dataCours:
        # Trouver le groupe correspondant au cours
        groupe = groupes.get(cours['idGroupe'])
        if groupe:
            # Trouver le cours correspondant dans la banque de cours
            banque = next((banque for banque in dataBanqueCours if banque["id"] == cours["idBanque"]), None)
            if banque is not None:
                tempCours = {
                    'id': cours['id'],
                    'idEnseignant': banque['idEnseignant'],
                    'enseignant': banque['enseignant'],
                    'type': banque['type'],
                    'libelle': banque['libelle'],
                    'heureDebut': cours['heureDebut'],
                    'duree': banque['duree'],
                    'style': banque['style']
                }

                # Ajouter le cours au jour correspondant
                jour = cours["numeroJour"]
                if jour == 0:
                    groupe['cours']["Lundi"].append(tempCours)
                elif jour == 1:
                    groupe['cours']["Mardi"].append(tempCours)
                elif jour == 2:
                    groupe['cours']["Mercredi"].append(tempCours)
                elif jour == 3:
                    groupe['cours']["Jeudi"].append(tempCours)
                elif jour == 4:
                    groupe['cours']["Vendredi"].append(tempCours)
                elif jour == 5:
                    groupe['cours']["Samedi"].append(tempCours)

    db.close()
    return JsonResponse(groupes, safe=False)

# Get by Semaine, Annee, idGroupe
@csrf_exempt
@method_awaited("GET")
def by_groupe(request, semaine: int, annee: int, idGroupe: int):
    db = Database.get()
    sqlDateEDT = "SELECT IdEDT as id, Semaine as semaine, Annee as annee FROM EDT WHERE Semaine = %s AND Annee = %s"
    sqlDataCours = "SELECT IdCours as id, IdEDT as idEDT, IdGroupe as idGroupe, IdBanque as idBanque, NumeroJour as numeroJour, HeureDebut as heureDebut FROM Cours WHERE IdGroupe = %s"
    dataBanqueCours = db.run("""
            SELECT IdBanque as id, Banque.IdUtilisateur as idEnseignant, CONCAT(Utilisateur.Nom, ' ', Utilisateur.Prenom) AS enseignant , Banque.Duree as duree, TypeCours.Nom AS 'type', CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS 'style'
            FROM Banque
            LEFT JOIN Utilisateur
            ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
            LEFT JOIN TypeCours
            ON Banque.IdTypeCours = TypeCours.IdTypeCours
            LEFT JOIN Ressource
            ON Banque.IdRessource = Ressource.IdRessource
            LEFT JOIN Couleur
            ON Banque.IdCouleur = Couleur.IdCouleur
            """).fetch()

    dateEDT = db.run([sqlDateEDT, (semaine, annee)]).fetch()
    dataCours = db.run([sqlDataCours, (idGroupe,)]).fetch()

    allEdt = []
    for edt in dateEDT:
        edt = dict(edt)
        edt["cours"] = {
            "Lundi": [],
            "Mardi": [],
            "Mercredi": [],
            "Jeudi": [],
            "Vendredi": [],
            "Samedi": []
        }
        for cours in dataCours:
            if cours["idEDT"] == edt["id"]:
                cours = dict(cours)
                banque = next((banque for banque in dataBanqueCours if banque["id"] == cours["idBanque"]), None)
                if banque is not None:
                    cours["idEnseignant"] = banque["idEnseignant"]
                    cours["enseignant"] = banque["enseignant"]
                    cours["type"] = banque["type"]
                    cours["libelle"] = banque["libelle"]
                    cours["duree"] = banque["duree"]
                    cours["style"] = banque["style"]
                    # del cours["idEDT"]
                    # del cours["idBanque"]

                    jour = cours["numeroJour"]
                    if jour == 0:
                        edt["cours"]["Lundi"].append(cours)
                    elif jour == 1:
                        edt["cours"]["Mardi"].append(cours)
                    elif jour == 2:
                        edt["cours"]["Mercredi"].append(cours)
                    elif jour == 3:
                        edt["cours"]["Jeudi"].append(cours)
                    elif jour == 4:
                        edt["cours"]["Vendredi"].append(cours)
                    elif jour == 5:
                        edt["cours"]["Samedi"].append(cours)

        allEdt.append(edt)

    db.close()
    return JsonResponse(allEdt, safe=False)

    


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

