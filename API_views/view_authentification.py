import json
from django.shortcuts import render
from django.http import JsonResponse

from Kairos_API.core import method_awaited, SECRET
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

import jwt
import bcrypt
import datetime

# Fonction de HASH de mot de passe
def hash_password(password):
    global SALT
    return bcrypt.hashpw(bytes(password, 'utf-8'), bcrypt.gensalt())

# Fonction de vérification de mot de passe
def check_password(password, hashed):
    return bcrypt.checkpw(str(password).encode('utf-8'), str(hashed).encode('utf-8'))

@csrf_exempt
@method_awaited("POST")
def Login(request):
    global SECRET
    db = Database.get()
    sql = """
        SELECT U.idUtilisateur as id, U.Prenom AS prenom, U.Nom AS nom, U.Email AS email, R.Label AS status, U.MotDePasse AS mdp, G.Nom AS groupe, G.IdGroupe AS idGroupe
        FROM Utilisateur U
        LEFT JOIN RoleUtilisateur R ON U.IdRole = R.IdRoleUtilisateur
        LEFT JOIN Groupe G ON U.IdGroupe = G.IdGroupe
        WHERE U.Email = %s
        """
    
    # Récupération des données
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    email = body['email']
    password = body['password']

    # Vérification de l'existence du compte + mot de passe
    data = db.run([sql, (email,)]).fetch()
    data = data[0] if len(data) > 0 else None

    if data is None:
        return JsonResponse({"error": "Compte inexistant"}, safe=False)

    if not check_password(password, data['mdp']):
        return JsonResponse({"error": "Mot de passe incorrect"}, safe=False)

    # Token valide 3h
    payload = {
      "id": data['id'],
      "prenom": data['prenom'],
      "nom": data['nom'],
      "email": data['email'],
      "status": data['status'],
      "groupe": data['groupe'],
      "idGroupe": data['idGroupe'],
      "exp": int((datetime.datetime.now() + datetime.timedelta(hours=3)).timestamp())
    }

    # Renvoie du token
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    db.close()
    return JsonResponse({"token": token}, safe=False)

@csrf_exempt
@method_awaited("POST")
def Register(request):
    db = Database.get()
    sqlCompteExist = """ SELECT Email FROM Utilisateur WHERE Email = %s """
    sql = """ INSERT INTO Utilisateur (Prenom, Nom, Email, IdRole, MotDePasse, IdGroupe) VALUES (%s, %s, %s, %s, %s, %s) """
    
    # Récupération des données obligatoires pour la création d'un utilisateur
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    prenom = body['prenom'][0].upper() + body['prenom'][1::].lower()
    nom = body['nom'][0].upper() + body['nom'][1::].lower()
    email = body['email']
    idRole = str(body['idRole'])
    idGroupe = str(body['idGroupe']) if 'idGroupe' in body else None

    # Vérification de l'existence du compte
    dataCompteExist = db.run([sqlCompteExist, (email,)]).fetch()
    if len(dataCompteExist) > 0:
        return JsonResponse({"error": "Compte déjà existant"}, safe=False)
    
    # Création du mot de passe temporaire
    tempNewMdp = prenom[0].upper() + prenom[1::].lower() + "." + nom[0].upper() + nom[1::].lower() 
    tempNewMdp = hash_password(tempNewMdp)

    nb_row_affected = db.run([sql, (prenom, nom, email, idRole, tempNewMdp, idGroupe)]).fetch(rowcount=True)

    # Si l'utilisateur est un enseignant, ajout des ressources enseignées
    if idRole == "3" and 'idRessources' in body:
        sqlIdUser = """ SELECT IdUtilisateur as ID FROM Utilisateur WHERE Email = %s """
        dataIdUser = db.run([sqlIdUser, (email,)]).fetch()
        idUser = dataIdUser[0]['ID']

        # Ajout des ressources enseignées avec formatage 
        idRessources = body['idRessources']
        tempFormatValue = []
        for idRessource in idRessources:
            tempFormatValue.append((idUser, idRessource))
        
        sqlRessources = "INSERT INTO Enseigne (IdUtilisateur, IdRessource) VALUES " + ",".join(["%s"] * len(tempFormatValue))
        nb_row_affected_enseigne = db.run([sqlRessources, tempFormatValue]).fetch(rowcount=True)
        db.close()
        return JsonResponse(nb_row_affected == 1 and nb_row_affected_enseigne == len(idRessources), safe=False)

    db.close()
    return JsonResponse(nb_row_affected == 1, safe=False)

@csrf_exempt
@method_awaited("POST")
def ResetPassword(request):
    db = Database.get()
    sqlMdp = """ SELECT MotDePasse as mdp FROM Utilisateur WHERE Email = %s """
    sqlNewMdp = """ UPDATE Utilisateur SET MotDePasse = %s WHERE Email = %s """
    
    # Récupération des données
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    email = body['email']
    oldMdp = body['ancien_mdp']
    newMdp = body['nouveau_mdp']
    
    # Récupération du mot de passe actuel + vérification
    dataCurrentMdp = db.run([sqlMdp, (email,)]).fetch()
    dataCurrentMdp = dataCurrentMdp[0]['mdp']

    if len(dataCurrentMdp) == 0:
        return JsonResponse({"error": "Compte inexistant"}, safe=False)
    
    if not check_password(oldMdp, dataCurrentMdp):
        return JsonResponse({"error": "Mot de passe incorrect"}, safe=False)

    # Hashage du nouveau mot de passe + mise à jour
    hashNewMdp = hash_password(newMdp)

    nb_row_affected = db.run([sqlNewMdp, (hashNewMdp, email)]).fetch(rowcount=True)

    print(nb_row_affected)

    db.close()
    return JsonResponse(nb_row_affected == 1, safe=False)