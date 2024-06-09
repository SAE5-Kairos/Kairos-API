import json
from django.shortcuts import render
from django.http import JsonResponse

from Kairos_API.core import method_awaited, jwt_required, Role
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT IdUtilisateur, Prenom, Nom, Email, IdRole, IdGroupe FROM Utilisateur").fetch()
    db.close()
    return JsonResponse(data, safe=False)

@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
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
@jwt_required(roles=[Role.ADMINISTRATEUR])
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
@jwt_required(roles=[Role.ADMINISTRATEUR])
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
        FROM IndisponibiliteProf 
        WHERE IndisponibiliteProf.IdUtilisateur = %s;
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
        
        sql_enseigne = """
        DELETE
        FROM Enseigne
        WHERE Enseigne.IdUtilisateur = %s;
            """

        db.run([sql_indisponibilite, (code,)]).fetch(rowcount=True)
        db.run([sql_cours, (code,)]).fetch(rowcount=True)
        db.run([sql_banque, (code,)]).fetch(rowcount=True)
        db.run([sql_enseigne, (code,)]).fetch(rowcount=True)
        nb_row_affected = db.run([sql_utilisateur, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        prenom = ""
        nom = ""
        email = ""
        id_role = ""
        id_groupe = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            prenom = body['prenom']
            nom = body['nom']
            email = body['email']
            id_role = body['id_role']
            id_groupe = str(body['id_groupe']) if 'id_groupe' in body else None
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Utilisateur
                    SET Utilisateur.Prenom = %s,
                        Utilisateur.Nom = %s,
                        Utilisateur.Email = %s,
                        Utilisateur.IdRole = %s,
                        Utilisateur.IdGroupe = %s
                    WHERE Utilisateur.IdUtilisateur = %s
                """
        nb_row_affected = db.run([sql, (prenom, nom, email, id_role, id_groupe, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
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
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_ressourcesByUser(request, code:int):
    db = Database.get()
    sql = """
        SELECT DISTINCT R.IdRessource as id_ressource, R.Libelle as libelle, R.Nom as nom
        FROM Enseigne as E
        RIGHT JOIN Ressource as R ON E.IdRessource = R.IdRessource
        RIGHT JOIN Utilisateur as U ON E.IdUtilisateur = U.IdUtilisateur
        WHERE Enseigne.IdUtilisateur = %s 
    """
    data = db.run([sql, (code,)]).fetch()
    db.close()
    result = {'id_utilisateur' : code, 'ressources' : data }
    return JsonResponse(result, safe=False)

@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_ressourcesAllUsers(request):
    db = Database.get()
    data = db.run("""                  
        SELECT DISTINCT U.IdUtilisateur as id_enseignant, U.Prenom as prenom, U.Nom as nomUser, U.Email as email, R.IdRessource as id_ressource, R.Libelle as libelle, R.Nom as nomRes
        FROM Enseigne as E
        RIGHT JOIN Ressource as R ON E.IdRessource = R.IdRessource
        RIGHT JOIN Utilisateur as U ON E.IdUtilisateur = U.IdUtilisateur
        WHERE U.IdRole = 3
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
                    "id": row['id_ressource'],
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

    # Suppression des ressources "null" dans les enseignants
    for enseignant in newData:
        enseignant['ressources'] = [ressource for ressource in enseignant['ressources'] if ressource['id'] is not None]

    return JsonResponse(newData, safe=False)