import datetime
import json, asyncio
from django.shortcuts import render
from django.http import JsonResponse

from EDT_generator.V2.generateur import generate
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

from EDT_generator.professeur import Professeur
from EDT_generator.cours import Cours
from EDT_generator.edt_generator import EDT_GENERATOR, Ant

from EDT_generator.V2.professeur2 import Professeur2
from EDT_generator.V2.cours2 import Cours2

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
            cours_data['semaine'] -= 1 # Pour s'accorder avec la norme ISO du calendrier
            params = (id_prof, cours_data['semaine'], cours_data['semaine'], cours_data['annee'], cours_data['annee'])
            data = db.run([sql, params]).fetch()
            
            for indispo in data:
                if indispo["DateFin"].isocalendar()[1] > cours_data['semaine']: indispo['JourFin'] = 6

                if indispo["DateDebut"].date() == indispo["DateFin"].date():
                    for creneau in range((indispo["DateDebut"].hour - 8) * 60 + indispo["DateDebut"].minute, (indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                        dispo[indispo["DateDebut"].weekday()][creneau // 30] = 0

                else:
                    # Si l'absence est sur la même semaine
                    if indispo["DateDebut"].isocalendar()[1]  == indispo["DateFin"].isocalendar()[1]:
                        for day in range(indispo["DateDebut"].weekday(), indispo["DateFin"].weekday()): # Fin exclue
                            dispo[day] = [ 0 for _ in range(24)]

                        for creneau in range((indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                            dispo[indispo["DateFin"].weekday()][creneau // 30] = 0
                    
                    # Si le prof est abs toute la semaine
                    else: dispo = [[ 0 for _ in range(24)] for __ in range(6)]

            prof = Professeur(dispo, name)
            profs[id_prof] = prof
            
        Cours(id_prof, prof, duree / 2, id_banque, nom_cours, color)
    
    debut = datetime.datetime.now()
    async def edt_generator_async(): await EDT_GENERATOR.generate_edts(15, int(len(Cours.ALL) * 2))
    ants = asyncio.run(edt_generator_async())
    print("> Durée totale: " + str(datetime.datetime.now() - debut))
    f = open('log.txt', 'a')
    f.write('durée tot: ' + str(datetime.datetime.now() - debut) + '\n')
    f.close()

    # Créer l'EDT:
    week_date = f'{body[0]["annee"]}-W{body[0]["semaine"]}'
    week_date = datetime.datetime.strptime(week_date + '-1', "%Y-W%W-%w")

    return JsonResponse(EDT_GENERATOR.BETTER_EDT.jsonify(), safe=False)

@csrf_exempt
@method_awaited("POST")
def generate_edt_v2(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if len(body) == 0: raise Exception("[API][generate_edt]() -> Impossible de générer un emploi du temps sans cours")

    sql_get_banque = """
        SELECT b.IdUtilisateur, u.Prenom, u.Nom, Duree, CouleurHexa, CONCAT(r.Libelle, ' - ', r.Nom) AS NomCours, t.Nom AS TypeCours, CONCAT(r.Libelle, ' - ', r.Abreviation) AS Abreviation
        FROM 
            Banque b
            LEFT JOIN Couleur c ON  b.IdCouleur = c.IdCouleur
            JOIN Ressource r ON b.IdRessource = r.IdRessource
            LEFT JOIN Utilisateur u ON b.IdUtilisateur = u.IdUtilisateur
            LEFT JOIN TypeCours t ON b.IdTypeCours = t.IdTypeCours
        WHERE IdBanque = %s;
    """

    db = Database.get('edt_generator')
    db.run("DELETE FROM ALL_ASSOCIATIONS;")
    db.run("DELETE FROM PHEROMONES2;")
    db.close()
    print("Ready to generate EDT")

    
    db = Database.get()
    Cours2.ALL = []
    Professeur2.ALL = []

    # 1. Unpack les données en Professeurs et Cours
    for cours_data in body:
        """cours_data = {'id_banque': 1, 'semaine': 1, 'annee': 2022}"""

        db.run([sql_get_banque, (cours_data['id_banque'], )])
        if db.exists():
            banque_data = db.fetch(first=True)
        else:
            raise Exception(f"[API][generate_edt]() -> Aucune informations retrouvées pour l'id de banque {cours_data['id_banque']}")

        id_prof = int(banque_data['IdUtilisateur'])
        nom_prof = banque_data['Prenom'][0].upper() + ". " + banque_data['Nom'].capitalize()
        duree = int(banque_data['Duree'])
        color = banque_data['CouleurHexa'] or '#bbbbbb'
        nom_cours = banque_data['NomCours'].capitalize()

        # Créer le professeur si il n'existe pas
        if id_prof not in Professeur2.ALL:
            dispo = Professeur2.generate_dispo(id_prof, cours_data['annnee'], cours_data['semaine'], cours_is_indispo=True)
            prof = Professeur2(id_prof, nom_prof, dispo)
        else: prof = Professeur2.get(id_prof)

        Cours2(professeur=prof, duree=duree, name=nom_cours, id_banque=cours_data['id_banque'], couleur=color, type_cours=banque_data['TypeCours'], abrevaition=banque_data['Abreviation'])
    db.close()

    # 2. Créer les cours et profs du midi
    midi = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    midi_lundi = [[0 for _ in range(24)] for __ in range(6)]; midi_lundi[0] = midi
    midi_mardi = [[0 for _ in range(24)] for __ in range(6)]; midi_mardi[1] = midi
    midi_mercredi = [[0 for _ in range(24)] for __ in range(6)]; midi_mercredi[2] = midi
    midi_jeudi = [[0 for _ in range(24)] for __ in range(6)]; midi_jeudi[3] = midi
    midi_vendredi = [[0 for _ in range(24)] for __ in range(6)]; midi_vendredi[4] = midi
    midi_samedi = [[0 for _ in range(24)] for __ in range(6)]; midi_samedi[5] = midi
    midi_lundi = Professeur2(-1, "Midi Lundi", midi_lundi)
    midi_mardi = Professeur2(-2, "Midi Mardi", midi_mardi)
    midi_mercredi = Professeur2(-3, "Midi Mercredi", midi_mercredi)
    midi_jeudi = Professeur2(-4, "Midi Jeudi", midi_jeudi)
    midi_vendredi = Professeur2(-5, "Midi Vendredi", midi_vendredi)
    midi_samedi = Professeur2(-6, "Midi Samedi", midi_samedi)

    Cours2(professeur=midi_lundi, duree=2, name="Midi Lundi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 0
    Cours2(professeur=midi_mardi, duree=2, name="Midi Mardi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 1
    Cours2(professeur=midi_mercredi, duree=2, name="Midi Mercredi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 2
    Cours2(professeur=midi_jeudi, duree=2, name="Midi Jeudi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 3
    Cours2(professeur=midi_vendredi, duree=2, name="Midi Vendredi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 4
    Cours2(professeur=midi_samedi, duree=2, name="Midi Samedi", id_banque=0, couleur="#bbbbbb", type_cours="Midi").jour = 5

    # 3. Générer les emplois du temps
    Cours2.save_associations()

    edt = generate()
    return JsonResponse(edt.jsonify(), safe=False)

@csrf_exempt
@method_awaited("GET")
def get_prof_dispo(request, id_prof, semaine, annee):
    dispo = Professeur2.generate_dispo(id_prof, annee, semaine)
    return JsonResponse(dispo, safe=False)

@csrf_exempt
@method_awaited("GET")
def get_prof_dispo_all(request, semaine, annee):
    db = Database.get()
    semaine -= 1 # Pour s'accorder avec la norme ISO du calendrier
    sqlIdUtilisateur= """
        SELECT 
            IdUtilisateur as idEnseignant, DateDebut, DateFin, WEEKDAY(DateDebut) AS JourDebut, WEEKDAY(DateFin) AS JourFin
        FROM 
            Indisponibilite 
        WHERE
            WEEK(DateDebut) <= %s AND WEEK(DateFin) >= %s
            AND YEAR(DateDebut) <= %s AND YEAR(DateFin) >= %s
    """
    data = db.run([sqlIdUtilisateur, (semaine, semaine, annee, annee)]).fetch()
    db.close()

    allIndispo = {}
    for indispo in data:
        id_enseignant = indispo["idEnseignant"]
        # Si l'enseignant n'est pas déjà dans le dictionnaire
        if id_enseignant not in allIndispo.keys():
            allIndispo[id_enseignant] = [indispo]
        else:
            allIndispo[id_enseignant].append(indispo)

    for id_enseignant, data in allIndispo.items():
        dispo = Professeur2.generate_dispo(id_enseignant, annee, semaine)
        allIndispo[id_enseignant] = dispo

    return JsonResponse(allIndispo, safe=False)

