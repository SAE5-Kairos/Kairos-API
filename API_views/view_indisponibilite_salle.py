import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited, jwt_required, Role
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT * FROM IndisponibiliteSalle").fetch()
    db.close()
    return JsonResponse(data, safe=False)


# Get by Id, Delete by Id, Update by Id
@csrf_exempt
@jwt_required(roles=[Role.PROFESSEUR, Role.ADMINISTRATEUR])
@method_awaited(["GET", "DELETE", "PUT"])
def by_id(request, code: int):
    db = Database.get()
    if request.method == "GET":
        sql = """
            SELECT *
            FROM IndisponibiliteSalle 
            WHERE IdIndisponibiliteSalle = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)

    elif request.method == "DELETE":
        sql = """
        DELETE
        FROM IndisponibiliteSalle 
        WHERE IdIndisponibiliteSalle = %s;
            """

        nb_row_affected = db.run([sql, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)

    else:
        date_debut = ""
        date_fin = ""
        id_utilisateur = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            date_debut = body['date_debut']
            date_fin = body['date_fin']
            id_utilisateur = body['id_utilisateur']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE IndisponibiliteSalle
                    SET DateDebut = %s,
                        DateFin = %s,
                        IdUtilisateur = %s
                    WHERE IdIndisponibiliteSalle = %s
                """
        nb_row_affected = db.run([sql, (date_debut, date_fin, id_utilisateur, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@jwt_required(roles=[Role.PROFESSEUR, Role.ADMINISTRATEUR])
@method_awaited("POST")
def add(request):
    params = []
    sql = """
        INSERT INTO IndisponibiliteSalle VALUES
    """
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        for element in body:
            sql += "(%s, %s, %s),"
            params.extend([element['date_debut'], element['date_fin'], element['id_salle']])
        sql = sql[:-1] + ";"
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()

    try:
        nb_row_affected = db.run([sql, params]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected > 0, safe=False)
    except:
        return JsonResponse({"error":"An error has occurred during the process."}, safe=False)


@csrf_exempt
@jwt_required(roles=[Role.PROFESSEUR, Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_indiponibility_by_salle_id(request, code: int):
    db = Database.get()
    # Get uniquement les indisponibilité du jour et les suivantes, les précédentes le seront pas
    sql = """
        SELECT IdIndisponibiliteSalle, DateDebut, DateFin
        FROM IndisponibiliteSalle
        WHERE DateFin > DATE_SUB(NOW(), INTERVAL 1 DAY)
        ORDER BY DateDebut
    """
    data = db.run([sql, (code,)]).fetch()
    db.close()
    return JsonResponse(data, safe=False)
