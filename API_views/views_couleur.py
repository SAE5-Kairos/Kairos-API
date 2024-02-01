import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@method_awaited("GET")
def get_all(request):
    db = Database.get()
    data = db.run("SELECT * FROM Couleur").fetch()
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
            FROM Couleur 
            WHERE Couleur.IdCouleur = %s
        """
        data = db.run([sql, (code,)]).fetch()
        db.close()
        return JsonResponse(data[0] if len(data) > 0 else {"error": f"Data not found for key {code}"}, safe=False)
    elif request.method == "DELETE":
        sql = """
        DELETE
        FROM Couleur 
        WHERE Couleur.IdCouleur = %s;
            """

        nb_row_affected = db.run([sql, (code,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    else:
        couleur_hexa = ""
        nom = ""
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            couleur_hexa = body['couleur_hexa']
            nom = body['nom']
        except:
            return JsonResponse({"error": "You must send a body"}, safe=False)

        db = Database.get()
        sql = """
                    UPDATE Couleur
                    SET Couleur.CouleurHexa = %s
                    WHERE Couleur.IdCouleur = %s
                """
        nb_row_affected = db.run([sql, (couleur_hexa, code)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)

@csrf_exempt
@method_awaited("POST")
def add(request):
    couleur_hexa = ""
    nom = ""
    try:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        couleur_hexa = body['couleur_hexa']
        nom = body['nom']
    except:
        return JsonResponse({"error": "You must send a body"}, safe=False)

    db = Database.get()
    sql = """
           INSERT INTO Couleur (Nom, CouleurHexa) VALUES
           (%s, %s);
       """
    try:
        nb_row_affected = db.run([sql, (nom, couleur_hexa,)]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1, safe=False)
    except:
        return JsonResponse({"error": "An error has occurred during the process."}, safe=False)