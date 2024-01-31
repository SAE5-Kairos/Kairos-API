import datetime
import json, asyncio
from django.shortcuts import render
from django.http import JsonResponse
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

from EDT_generator.professeur import Professeur
from EDT_generator.cours import Cours
from EDT_generator.edt_generator import EDT_GENERATOR, Ant

from Kairos_API.core import method_awaited

@csrf_exempt
@method_awaited("POST")
def generate_edt(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    
    profs = {}
    Cours.ALL = []
    for cours_data in body:
        id_prof = cours_data['id_prof']
        if id_prof in profs:
            prof = profs[id_prof]
        else:
            dispo = [[ 1 for _ in range(24)] for __ in range(6)]
            name = ""
            db = Database.get()
            sql = """
                SELECT 
                    DateDebut, DateFin, 
                    WEEKDAY(DateDebut) AS JourDebut,
                    WEEKDAY(DateFin) AS JourFin
                FROM 
                    Indisponibilite 
                WHERE 
                    IdUtilisateur = %s AND WEEK(DateDebut) <= %s AND WEEK(DateFin) >= %s 
                    AND YEAR(DateDebut) <= %s AND YEAR(DateFin) >= %s
            """
            params = (id_prof, cours_data['semaine'], cours_data['semaine'], cours_data['annee'], cours_data['annee'])
            data = db.run([sql, params]).fetch()
            db.close()
            for indispo in data:
                if indispo["DateFin"].isocalendar().week > cours_data['semaine']: indispo['JourFin'] = 6

                if indispo["DateDebut"].date() == indispo["DateFin"].date():
                    for creneau in range((indispo["DateDebut"].hour - 8) * 60 + indispo["DateDebut"].minute, (indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                        dispo[indispo["DateDebut"].weekday()][creneau // 30] = 0

                else:
                    # Si l'absence est sur la même semaine
                    if indispo["DateDebut"].isocalendar().week  == indispo["DateFin"].isocalendar().week:
                        for day in range(indispo["DateDebut"].weekday(), indispo["DateFin"].weekday()): # Fin exclue
                            dispo[day] = [ 0 for _ in range(24)]

                        for creneau in range((indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                            dispo[indispo["DateFin"].weekday()][creneau // 30] = 0
                    
                    # Si le prof est abs toute la semaine
                    else: dispo = [[ 0 for _ in range(24)] for __ in range(6)]

            prof = Professeur(dispo, name)
            profs[id_prof] = prof

        Cours(prof, cours_data['duree'] )
    
    async def edt_generator_async(): await EDT_GENERATOR.generate_edts(15, int(len(Cours.ALL) * 2.2))
    ants = asyncio.run(edt_generator_async())

    ant = Ant(1, 0)
    ant = asyncio.run(ant.visit(get_better=True))

    return JsonResponse(ant.edt.jsonify(), safe=False)