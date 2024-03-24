import json
from django.shortcuts import render
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def GetAll(request):
    db = Database.get()
    data = db.run("""
            SELECT IdBanque as id, IdBanque as idBanque, Banque.IdUtilisateur as idEnseignant, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant , Banque.Duree as duree, TypeCours.Nom AS 'type', CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS 'style', Ressource.Abreviation as abreviation
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
    db.close()
    return JsonResponse(data, safe=False)

@csrf_exempt
@method_awaited(["GET", "DELETE", "PUT"])
def by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
        SELECT IdBanque as id, IdBanque as idBanque, CONCAT(Utilisateur.Prenom, ' ', Utilisateur.Nom) AS enseignant ,  Banque.Duree as duree, TypeCours.Nom AS 'type', CONCAT(Ressource.Libelle,' - ',Ressource.Nom) AS libelle, Couleur.CouleurHexa AS 'style', Ressource.Abreviation as abreviation
        FROM Banque
        LEFT JOIN Utilisateur
        ON Banque.IdUtilisateur = Utilisateur.IdUtilisateur
        LEFT JOIN TypeCours
        ON Banque.IdTypeCours = TypeCours.IdTypeCours
        LEFT JOIN Ressource
        ON Banque.IdRessource = Ressource.IdRessource
        LEFT JOIN Couleur
        ON Banque.IdCouleur = Couleur.IdCouleur
        WHERE Banque.IdBanque = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error":f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_cours = """
        DELETE
        FROM Cours 
        WHERE Cours.IdBanque = %s;
            """

        sql_banque = """
        DELETE
        FROM Banque 
        WHERE Banque.IdBanque = %s;
            """

        db.run([sql_cours, (code,)]).fetch()
        nb_row_affected = db.run([sql_banque, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        id_utilisateur = ""
        id_ressource = ""
        id_type_cours = ""
        duree = ""
        id_couleur = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            id_utilisateur = body['id_utilisateur']
            id_ressource = body['id_ressource']
            id_type_cours = body['id_type_cours']
            duree = body['duree']
            id_couleur = body['id_couleur']
        except:
            return JsonResponse({"error":"You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                UPDATE Banque
                SET Banque.IdUtilisateur = %s,
                Banque.IdRessource = %s,
                Banque.IdTypeCours = %s,
                Banque.Duree = %s,
                Banque.IdCouleur = %s
                WHERE Banque.IdBanque = %s
                """
        nb_row_affected = db.run([sql, (id_utilisateur, id_ressource, id_type_cours, duree, id_couleur, code, )]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)

@csrf_exempt
@method_awaited("POST")
def add(request):
    id_utilisateur = ""
    id_ressource = ""
    id_type_cours = ""
    duree = ""
    id_couleur = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        id_utilisateur = body['id_utilisateur']
        id_ressource = body['id_ressource']
        id_type_cours = body['id_type_cours']
        duree = body['duree']
        id_couleur = body['id_couleur']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
                    INSERT INTO Banque (IdUtilisateur, IdRessource, IdTypeCours, Duree, IdCouleur) VALUES
                    (%s,%s,%s,%s,%s);
                """
    nb_row_affected = db.run([sql, (id_utilisateur, id_ressource, id_type_cours, duree, id_couleur)]).fetch(
        rowcount=True)
    db.close()
    return JsonResponse(nb_row_affected == 1, safe=False)
