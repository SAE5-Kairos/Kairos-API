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
    data = db.run("SELECT * FROM TypeCours").fetch()
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
            SELECT *
            FROM TypeCours 
            WHERE TypeCours.IdTypeCours = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql_quota = """
        DELETE
        FROM Quota 
        WHERE Quota.IdTypeCours = %s;
            """

        sql_type_cours = """
        DELETE
        FROM TypeCours 
        WHERE TypeCours.IdTypeCours = %s;
            """

        db.run([sql_quota, (code,)]).fetch()
        nb_row_affected = db.run([sql_type_cours, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        nom = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            nom = body['nom']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE TypeCours
                    SET TypeCours.Nom = %s
                    WHERE TypeCours.IdTypeCours = %s
                """
        nb_row_affected = db.run([sql, (nom, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)



@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("POST")
def add(request):
    nom = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        nom = body['nom']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
                INSERT INTO TypeCours (Nom) VALUES
                (%s);
            """
    try:
        nb_row_affected = db.run([sql, (nom,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error": "An error has occurred during the process."}, safe=False)