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

    if len(body) == 0: raise Exception("Impossible de générer un emploi du temps sans cours")
    db = Database.get()
    
    profs = {}
    Cours.ALL = []

    for cours_data in body:
        id_banque = cours_data['id_banque']

        sql = """
            SELECT b.IdUtilisateur, u.Prenom, u.Nom, Duree, CouleurHexa, CONCAT(r.Libelle, ' ', r.Nom) AS 'NomCours'
            FROM 
                Banque b
                LEFT JOIN Couleur c ON  b.IdCouleur = c.IdCouleur
                JOIN Ressource r ON b.IdRessource = r.IdRessource
                LEFT JOIN Utilisateur u ON b.IdUtilisateur = u.IdUtilisateur
            WHERE IdBanque = %s;
        """
        data = db.run([sql, (id_banque, )]).fetch(first=True)
        if len(data) == 0:
            raise Exception(f"Aucune informations retrouvées pour l'id de banque {id_banque}")

        id_prof = int(data['IdUtilisateur'])
        duree = int(data['Duree'])
        color = data['CouleurHexa'] or '#bbbbbb'
        nom_cours = data['NomCours'].capitalize()

        if id_prof in profs:
            prof = profs[id_prof]
        else:
            dispo = [[ 1 for _ in range(24)] for __ in range(6)]
            name = data['Prenom'][0].upper() + ". " + data['Nom'].capitalize()
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
            
        Cours(prof, duree / 2, id_banque, nom_cours, color)
    
    debut = datetime.datetime.now()
    async def edt_generator_async(): await EDT_GENERATOR.generate_edts(25, int(len(Cours.ALL) * 2))
    ants = asyncio.run(edt_generator_async())
    print("> Durée totale: " + str(datetime.datetime.now() - debut))
    f = open('log.txt', 'a')
    f.write('durée tot: ' + str(datetime.datetime.now() - debut) + '\n')
    f.close()

    # Créer l'EDT:
    week_date = f'{body[0]["annee"]}-W{body[0]["semaine"]}'
    week_date = datetime.datetime.strptime(week_date + '-1', "%Y-W%W-%w")

    version_edt = db.run(["SELECT COUNT(IdEDT) + 1 AS 'Version' FROM EDT WHERE DateEDT = %s", (week_date, )]).fetch(first=True)['Version']

    sql = """
        INSERT INTO EDT (DateEDT, Version) VALUES
        (%s,%s);
    """
    
    db.run([sql, (week_date, version_edt)])
    edt_id = db.last_id()

    # Stocker les cours en base
    for course in EDT_GENERATOR.BETTER_EDT.placed_cours:
        if course.debut is not None:
            sql = """
                INSERT INTO Cours (NumeroJour, HeureDebut, IdBanque, IdEDT, IdGroupe) 
                VALUES (%s,%s,%s,%s,%s);
            """

            params = (course.jour, course.debut, course.banque, edt_id, 1)
            db.run([sql, params])
            course.name = db.last_id()
    db.close()

    return JsonResponse(EDT_GENERATOR.BETTER_EDT.jsonify(), safe=False)