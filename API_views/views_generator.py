import datetime
import json, asyncio
from django.shortcuts import render
from django.http import JsonResponse

from EDT_generator.V2.generateur import generate
from API_views.views_EDT import get_edt
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

from EDT_generator.professeur import Professeur
from EDT_generator.cours import Cours
from EDT_generator.edt_generator import EDT_GENERATOR, Ant

from EDT_generator.V2.professeur2 import Professeur2
from EDT_generator.V2.cours2 import Cours2

from Kairos_API.core import method_awaited, jwt_required, Role


@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("PUT")
def generate_edt(request, id_groupe, semaine, annee, id_admin):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if len(body) == 0: return JsonResponse({"error": "Aucune donnée fournie"}, status=400)
    db = Database.get()

    sql = """
        SELECT
            CONCAT(u.Prenom, ' ', u.Nom) AS NomAdmin, IdInstanceGeneration, DHDebut
        FROM
            InstanceGeneration ig
            JOIN Utilisateur u ON ig.IdUtilisateur = u.IdUtilisateur
        WHERE
            EnCours = 1
    """

    db.run(sql)
    if db.exists():
        data = db.fetch(first=True)
        #return JsonResponse({"error": f"Une génération est déjà en cours par {data['NomAdmin']} depuis le {data['DHDebut']} (ID: {data['IdInstanceGeneration']})"}, status=400)

    sql = """
        INSERT INTO InstanceGeneration (IdUtilisateur, DHDebut, EnCours)
        VALUES (%s, NOW(), 1);
    """
    db.run([sql, (id_admin, )])
    id_generation = db.last_id()

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

    db_local = db.get('edt_generator')
    db_local.run("DELETE FROM ALL_ASSOCIATIONS;")
    db_local.run("DELETE FROM PHEROMONES2;")
    db_local.close()
    print("Ready to generate EDT")

    
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
            dispo = Professeur2.generate_dispo(id_prof, cours_data['annee'], cours_data['semaine'], cours_is_indispo=True)
            prof = Professeur2(id_prof, nom_prof, dispo)
        else: prof = Professeur2.get(id_prof)

        Cours2(professeur=prof, duree=duree, name=nom_cours, id_banque=cours_data['id_banque'], couleur=color, type_cours=banque_data['TypeCours'], abrevaition=banque_data['Abreviation'])
    
    # Récupérer les cours des parents (obligatoires, position bloquée)
    edt_cours = get_edt(id_groupe, semaine, annee, only_parent=True, as_edt=True)
    fixed_cours: 'list[Cours2]' = edt_cours.cours
    for cours in fixed_cours:
        racine = Cours2.get(cours.id)
        racine.jour = cours.jour
        racine.heure = cours.heure
        racine.fixed = True
   
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

    edt = generate(id_generation, fixed_cours)
    return JsonResponse(edt.jsonify(), safe=False)

@csrf_exempt
@jwt_required(roles=[Role.PROFESSEUR, Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_prof_dispo(request, id_prof, semaine, annee):
    dispo = Professeur2.generate_dispo(id_prof, annee, semaine)
    return JsonResponse(dispo, safe=False)

@csrf_exempt
@jwt_required(roles=[Role.ADMINISTRATEUR])
@method_awaited("GET")
def get_prof_dispo_all(request, semaine, annee):
    db = Database.get()
    sqlIdUtilisateur= """
        SELECT DISTINCT
            u.IdUtilisateur as idEnseignant
        FROM 
            Utilisateur u
            JOIN RoleUtilisateur ru ON u.IdUtilisateur = ru.IdUtilisateur
        WHERE
            ru.Label = 'Professeur'
    """
    profs = db.run(sqlIdUtilisateur).fetch()
    db.close()

    allIndispo = {}
    for prof in profs:
        id_enseignant = prof["idEnseignant"]
        allIndispo[id_enseignant] = Professeur2.generate_dispo(id_enseignant, annee, semaine)

    return JsonResponse(allIndispo, safe=False)

