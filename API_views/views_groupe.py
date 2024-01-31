import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT * FROM Groupe").fetch()
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
            FROM Groupe 
            WHERE Groupe.IdGroupe = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_quota = """
        DELETE
        FROM Quota 
        WHERE Quota.IdGroupe = %s;
            """
        sql_groupe = """
        DELETE
        FROM Groupe 
        WHERE Groupe.IdGroupe = %s;
            """

        db.run([sql_quota, (code,)]).fetch()
        nb_row_affected = db.run([sql_groupe, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        nom = ""
        id_salle = ""
        id_groupe_superieur = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            nom = body['Nom']
            id_salle = body['IdSalle']
            id_groupe_superieur = body['IdGroupeSuperieur']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Groupe
                    SET Groupe.Nom = %s,
                        Groupe.IdSalle = %s,
                        Groupe.IdGroupeSuperieur = %s
                    WHERE Groupe.IdGroupe = %s
                """
        nb_row_affected = db.run([sql, (nom, id_salle, id_groupe_superieur, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@method_awaited("POST")
def add(request):
    nom = ""
    id_salle = ""
    id_groupe_superieur = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        nom = body['Nom']
        id_salle = body['IdSalle']
        id_groupe_superieur = body['IdGroupeSuperieur']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
        INSERT INTO Groupe (Nom, IdSalle, IdGroupeSuperieur) VALUES
        (%s,%s,%s);
    """
    try:
        nb_row_affected = db.run([sql, (nom, id_salle, id_groupe_superieur)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error":"An error has occurred during the process."}, safe=False)

