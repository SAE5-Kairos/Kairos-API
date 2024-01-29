from django.http import JsonResponse

def home(request):
    api_paths = [
        {"path": "generate_edt/", "POST": "[{'id': int, 'id_prof': int, 'duree': int}]"}
    ]
    # db = Database.get()
    # print(db.run("SELECT * FROM Salle").fetch())
    # db.close()
    [
        {"id": 1, "id_prof": 1, "duree": 2},
        {"id": 2, "id_prof": 1, "duree": 4},
        {"id": 3, "id_prof": 2, "duree": 2},
        {"id": 4, "id_prof": 2, "duree": 3},
        {"id": 5, "id_prof": 3, "duree": 2},
        {"id": 6, "id_prof": 4, "duree": 2},
        {"id": 7, "id_prof": 4, "duree": 3}
    ]
    return JsonResponse(api_paths, safe=False)

