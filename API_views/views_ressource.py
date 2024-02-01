import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT * FROM Ressource").fetch()
    db.close()
    return JsonResponse(data, safe=False)


# Get by Id, Delete by Id, Update by Id
@csrf_exempt
@method_awaited(["GET", "DELETE", "PUT"])
def by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
            SELECT *
            FROM Ressource 
            WHERE Ressource.IdRessource = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_quota = """
        DELETE
        FROM Quota 
        WHERE Quota.IdRessource = ANY(
            SELECT IdRessource
            FROM Ressource
            WHERE Ressource.IdRessource = %s
        );
        """
        sql_cours = """
        DELETE
        FROM Cours 
        WHERE Cours.IdBanque = ANY(
            SELECT IdBanque 
            FROM Banque 
            WHERE Banque.IdRessource = ANY(
                SELECT IdRessource
                FROM Ressource
                WHERE Ressource.IdRessource = %s
        ));
        """
        sql_banque = """
        DELETE
        FROM Banque 
        WHERE Banque.IdRessource = ANY(
            SELECT IdRessource
            FROM Ressource
            WHERE Ressource.IdRessource = %s
        );
        """

        sql_ressource = """
        DELETE
        FROM Ressource 
        WHERE Ressource.IdRessource = %s;
            """

        db.run([sql_quota, (code,)]).fetch()
        db.run([sql_cours, (code,)]).fetch()
        db.run([sql_banque, (code,)]).fetch()
        nb_row_affected = db.run([sql_ressource, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        libelle = ""
        nom = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            libelle = body['libelle']
            nom = body['nom']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Ressource
                    SET Ressource.Libelle = %s,
                        Ressource.Nom = %s
                    WHERE Ressource.IdRessource = %s
                """
        nb_row_affected = db.run([sql, (libelle, nom, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@method_awaited("POST")
def add(request):
    libelle = ""
    nom = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        libelle = body['libelle']
        nom = body['nom']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
        INSERT INTO Ressource (Libelle,Nom) VALUES
        (%s,%s);
    """
    nb_row_affected = db.run([sql, (libelle,nom)]).fetch(rowcount=True)
    db.close()
    return JsonResponse(nb_row_affected == 1, safe=False)
