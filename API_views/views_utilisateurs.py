import json
from django.shortcuts import render
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT IdUtilisateur, Prenom, Nom, Email, IdRole, IdGroupe FROM Utilisateur").fetch()
    db.close()
    return JsonResponse(data, safe=False)

@csrf_exempt
@method_awaited("GET")
def get_all_professors(request):
    db = Database.get()
    data = db.run("""
    SELECT IdUtilisateur, Prenom, Nom, Email, IdRole, IdGroupe 
        FROM Utilisateur
        LEFT JOIN RoleUtilisateur
        ON RoleUtilisateur.IdRoleUtilisateur = Utilisateur.IdRole
        WHERE RoleUtilisateur.Label = 'Professeur'
        """).fetch()
    db.close()
    return JsonResponse(data, safe=False)

@csrf_exempt
@method_awaited("GET")
def get_all_students(request):
    db = Database.get()
    data = db.run("""
    SELECT IdUtilisateur as id, Prenom as prenom, Nom as nom, Email as email, IdGroupe as idGroupe
        FROM Utilisateur
        LEFT JOIN RoleUtilisateur ON RoleUtilisateur.IdRoleUtilisateur = Utilisateur.IdRole
        WHERE RoleUtilisateur.Label = 'Etudiant'
        """).fetch()
    db.close()
    return JsonResponse(data, safe=False)


# Get by Id, Delete by Id, Update by Id
@csrf_exempt
@method_awaited(["GET", "DELETE", "PUT"])
def by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
            SELECT IdUtilisateur, Prenom, Nom, Email, IdRole, IdGroupe
            FROM Utilisateur 
            WHERE Utilisateur.IdUtilisateur = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_utilisateur = """
        DELETE
        FROM Utilisateur 
        WHERE Utilisateur.IdUtilisateur = %s;
            """

        sql_indisponibilite = """
        DELETE
        FROM Indisponibilite 
        WHERE Indisponibilite.IdUtilisateur = %s;
            """

        sql_cours = """
        DELETE
        FROM Cours 
        WHERE Cours.IdBanque = ANY(
            SELECT Banque.IdBanque
            FROM Banque
            WHERE Banque.IdUtilisateur = %s)
            """

        sql_banque = """
        DELETE
        FROM Banque 
        WHERE Banque.IdUtilisateur = %s;
            """

        db.run([sql_indisponibilite, (code,)]).fetch(rowcount=True)
        db.run([sql_cours, (code,)]).fetch(rowcount=True)
        db.run([sql_banque, (code,)]).fetch(rowcount=True)
        nb_row_affected = db.run([sql_utilisateur, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        prenom = ""
        nom = ""
        email = ""
        mot_de_passe = ""
        id_role = ""
        id_groupe = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            prenom = body['prenom']
            nom = body['nom']
            email = body['email']
            mot_de_passe = body['mot_de_passe']
            id_role = body['id_role']
            id_groupe = body['id_groupe']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Utilisateur
                    SET Utilisateur.Prenom = %s,
                        Utilisateur.Nom = %s,
                        Utilisateur.Email = %s,
                        Utilisateur.MotDePasse = %s,
                        Utilisateur.IdRole = %s,
                        Utilisateur.IdGroupe = %s
                    WHERE Utilisateur.IdUtilisateur = %s
                """
        nb_row_affected = db.run([sql, (prenom, nom, email, mot_de_passe, id_role, id_groupe, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@method_awaited("POST")
def add(request):
    prenom = ""
    nom = ""
    email = ""
    mot_de_passe = ""
    id_role = ""
    id_groupe = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        prenom = body['prenom']
        nom = body['nom']
        email = body['email']
        mot_de_passe = body['mot_de_passe']
        id_role = body['id_role']
        id_groupe = body['id_groupe']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
        INSERT INTO Utilisateur (Prenom, Nom, Email, MotDePasse, IdRole, IdGroupe) VALUES
        (%s,%s,%s,%s,%s,%s);
    """
    try:
        nb_row_affected = db.run([sql, (prenom, nom, email, mot_de_passe, id_role, id_groupe)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error":"An error has occurred during the process."}, safe=False)


@csrf_exempt
@method_awaited("GET")
def get_ressourcesByUser(request, code:int):
    db = Database.get()
    sql = """
        SELECT DISTINCT Ressource.IdRessource as id_ressource, Ressource.Libelle as libelle, Ressource.Nom as nom
        FROM Banque
        LEFT JOIN Ressource ON Banque.IdRessource = Ressource.IdRessource
        WHERE Banque.IdUtilisateur = %s 
    """
    data = db.run([sql, (code,)]).fetch()
    db.close()
    result = {'id_utilisateur' : code, 'ressources' : data }
    return JsonResponse(result, safe=False)

@csrf_exempt
@method_awaited("GET")
def get_ressourcesAllUsers(request):
    db = Database.get()
    data = db.run("""
        SELECT DISTINCT U.IdUtilisateur as id_enseignant, U.Prenom as prenom, U.Nom as nomUser, U.Email as email, R.IdRessource as id_ressource, R.Libelle as libelle, R.Nom as nomRes
        FROM Banque as B
        LEFT JOIN Ressource as R ON B.IdRessource = R.IdRessource
        LEFT JOIN Utilisateur as U ON B.IdUtilisateur = U.IdUtilisateur
    """).fetch()
    db.close()

    newData = []

    for row in data:
        rowJson = {
            "id_enseignant": row['id_enseignant'],
            "prenom": row['prenom'],
            "nom": row['nomUser'],
            "email": row['email'],
            "ressources": [
                {
                    "id_ressource": row['id_ressource'],
                    "libelle": row['libelle'],
                    "nom": row['nomRes']
                }
            ]
        }

        alreadyExist = False
        for enseignant in newData:
            if enseignant['id_enseignant'] == rowJson['id_enseignant']:
                alreadyExist = True
                enseignant['ressources'].append(rowJson['ressources'][0])
        
        if not alreadyExist:
            newData.append(rowJson)

    return JsonResponse(newData, safe=False)