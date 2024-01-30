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
    data = db.run("SELECT * FROM Salle").fetch()
    db.close()
    return JsonResponse(data, safe=False)


@csrf_exempt
@method_awaited(["GET", "DELETE", "PUT"])
def get_by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
            SELECT * 
            FROM Salle 
            WHERE Salle.idSalle = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0], safe=False)
    elif request.method == "DELETE":
        sql = """
        DELETE
        FROM Salle 
        WHERE Salle.IdSalle = %s;
            """

        nb_row_affected = db.run([sql, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        nom = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            nom = body['nom']
        except:
            return JsonResponse({"error":"You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Salle
                    SET Salle.Nom = %s
                    WHERE Salle.IdSalle = %s
                """
        db.run([sql, (nom, code, )]).fetch()
        db.close()
        return JsonResponse(True, safe=False)


@csrf_exempt
@method_awaited("POST")
def add(request):
    nom = ''
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        nom = body['nom']
    except:
        return JsonResponse({"error":"You must send a body"}, safe=False)


    db = Database.get()
    sql = """
        INSERT INTO Salle (Nom) VALUES
        (%s);
    """
    nb_row_affected = db.run([sql, (nom,)]).fetch(rowcount=True)
    db.close()
    return JsonResponse(nb_row_affected == 1, safe=False)
