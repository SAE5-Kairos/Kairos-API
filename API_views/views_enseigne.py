import json
from django.http import JsonResponse

from Kairos_API.core import method_awaited, jwt_required, Role
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("POST")
def add_enseigne(request):
    db = Database.get()

    sqlDelete = """
      DELETE FROM Enseigne WHERE IdUtilisateur = %s
        """
    
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    idUtilisateur = body['idUtilisateur']
    idRessources = body['idRessources'] # Liste d'ID des ressources

    # Suppression des anciennes ressources
    db.run([sqlDelete, (idUtilisateur)])

    if len(idRessources) > 0:
      # Ajout des nouvelles ressources
      tempFormatValue = []
      for idRessource in idRessources:
          tempFormatValue.append((idUtilisateur, idRessource))

      sqlRessources = "INSERT INTO Enseigne (IdUtilisateur, IdRessource) VALUES " + ",".join(["%s"] * len(tempFormatValue))
      nb_row_affected_enseigne = db.run([sqlRessources, tempFormatValue]).fetch(rowcount=True)

      db.close()
      return JsonResponse(nb_row_affected_enseigne == len(idRessources), safe=False)
    else:
      db.close()
      return JsonResponse(True, safe=False)