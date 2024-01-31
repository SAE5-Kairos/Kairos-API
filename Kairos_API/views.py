from django.http import JsonResponse

def home(request):
    api_paths = [
        {"path": "generate_edt/", "POST": "[{'id_banque': int, 'semaine': int, 'annee': int}]"}
    ]
    # db = Database.get()
    # print(db.run("SELECT * FROM Salle").fetch())
    # db.close()
    return JsonResponse(api_paths, safe=False)

