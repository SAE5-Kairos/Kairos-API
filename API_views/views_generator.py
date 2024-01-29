import json, asyncio
from django.shortcuts import render
from django.http import JsonResponse
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

from EDT_generator.professeur import Professeur
from EDT_generator.cours import Cours
from EDT_generator.edt import EDT
from EDT_generator.edt_generator import EDT_GENERATOR, Ant

@csrf_exempt
def generate_edt(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        
        Cours.ALL = []
        for cours_data in body:
            Cours(0, cours_data['duree'], cours_data['id'])
        
        async def main(): await EDT_GENERATOR.generate_edts(15, int(len(Cours.ALL) * 2.2))
        ants = asyncio.run(main())

        ant = Ant(1, 0)
        ant = asyncio.run(ant.visit(get_better=True))

        return JsonResponse(ant.edt.jsonify(), safe=False)
    else: return JsonResponse({"error": "Request POST awaited"})