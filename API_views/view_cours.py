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
    data = db.run("SELECT * FROM Cours").fetch()
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
            FROM Cours 
            WHERE Cours.IdCours = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql = """
        DELETE
        FROM Cours 
        WHERE Cours.IdCours = %s;
            """

        nb_row_affected = db.run([sql, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        numero_jour = ""
        heure_debut = ""
        id_banque = ""
        id_edt = ""
        id_groupe = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            numero_jour = body['numero_jour']
            heure_debut = body['heure_debut']
            id_banque = body['id_banque']
            id_edt = body['id_edt']
            id_groupe = body['id_groupe']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Cours
                    SET Cours.NumeroJour = %s,
                        Cours.HeureDebut = %s,
                        Cours.IdBanque = %s,
                        Cours.IdEDT = %s,
                        Cours.IdGroupe = %s
                    WHERE Cours.IdCours = %s
                """
        nb_row_affected = db.run([sql, (numero_jour, heure_debut, id_banque, id_edt, id_groupe, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)


@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("POST")
def add(request):
    numero_jour = ""
    heure_debut = ""
    id_banque = ""
    id_edt = ""
    id_groupe = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        numero_jour = body['numero_jour']
        heure_debut = body['heure_debut']
        id_banque = body['id_banque']
        id_edt = body['id_edt']
        id_groupe = body['id_groupe']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
        INSERT INTO Cours (NumeroJour, HeureDebut, IdBanque, IdEDT, IdGroupe) VALUES
        (%s,%s,%s,%s,%s);
    """
    try:
        nb_row_affected = db.run([sql, (numero_jour, heure_debut, id_banque, id_edt, id_groupe)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error":"An error has occurred during the process."}, safe=False)

