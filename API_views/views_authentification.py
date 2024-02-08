import json
from django.shortcuts import render
from django.http import JsonResponse

from Kairos_API.core import method_awaited
from Kairos_API.database import Database
from django.views.decorators.csrf import csrf_exempt

import jwt
import bcrypt

SECRET = "jesuislaphraseextremementsecretedelamortquituenormalementpersonneestsenseletrouvemaisbononsaitjamais"

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
            SELECT U.Prenom as prenom, U.Nom as nom, U.Email as email, R.Label as status, U.MotDePasse as mdp
            FROM Utilisateur as U
            RIGHT JOIN RoleUtilisateur as R ON U.IdRole = R.IdRoleUtilisateur
            WHERE email = %s
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
      "prenom": data['prenom'],
      "nom": data['nom'],
      "email": data['email'],
      "status": data['status'],
      "exp": 10800
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
    
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    prenom = body['prenom']
    nom = body['nom']
    email = body['email']
    idRole = str(body['idRole'])

    # Vérification de l'existence du compte
    dataCompteExist = db.run([sqlCompteExist, (email,)]).fetch()
    if len(dataCompteExist) > 0:
        return JsonResponse({"error": "Compte déjà existant"}, safe=False)
    
    # Création du mot de passe temporaire
    tempNewMdp = prenom[0].upper() + prenom[1::].lower() + "." + nom[0].upper() + nom[1::].lower() 
    tempNewMdp = hash_password(tempNewMdp)

    nb_row_affected = db.run([sql, (prenom, nom, email, idRole, tempNewMdp, None)]).fetch(rowcount=True)

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