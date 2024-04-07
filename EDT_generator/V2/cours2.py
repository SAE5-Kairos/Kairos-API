from EDT_generator.V2.professeur2 import Professeur2
from Kairos_API.database import Database

class Cours2:
    AUTO_INCREMENT = 0
    ALL: 'list[Cours2]' = []

    def __init__(self, professeur:Professeur2, duree:int, name:str, id_banque:int, couleur:str, type_cours:str, groupe:int=0, abrevaition:str='undefined', warning_message:str=None, _copy=False, _id=None) -> None:
        """
        professeur: Professeur2
        duree: int (nb créneaux de 30 minutes)
        """

        if not _copy:
            self.id = Cours2.AUTO_INCREMENT
            Cours2.AUTO_INCREMENT += 1
        else:
            self.id = _id

        self.professeur = professeur
        self.duree = duree
        self.id_banque = id_banque
        self.couleur = couleur
        self.type_cours = type_cours

        self.jour = None
        self.heure = None

        self.name = name
        self.abrevaition = abrevaition
        self.groupe = groupe
        self.warning_message = warning_message

        if not _copy:
            Cours2.ALL.append(self)

    @staticmethod
    def get(id_cours: int) -> 'Cours2':
        for cours in Cours2.ALL:
            if cours.id == id_cours:
                return cours
        raise Exception(f"[Cours2][get]({id_cours}) -> Cours non trouvé")

    def __hash__(self) -> int:
        return (self.id, self.jour, self.heure).__hash__()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Cours2):
            return self.id == __value.id
        elif isinstance(__value, int):
            return self.id == __value
        elif isinstance(__value, tuple):
            return self.id == __value[0] and self.jour == __value[1] and self.heure == __value[2]
        else:
            return False

    def __str__(self) -> str:
        return f"Cours2<{self.id}>: {self.duree}*30min"

    def __repr__(self) -> str:
        return f"C{self.id}"
        
    def copy(self):
        return Cours2(professeur=self.professeur, duree=self.duree, name=self.name, id_banque=self.id_banque, couleur=self.couleur, type_cours=self.type_cours, abrevaition=self.abrevaition, warning_message=self.warning_message, _copy=True, _id=self.id)

    def save_associations(self=None):
        if self is None:
            for cours in Cours2.ALL:
                cours.save_associations()
            
            Cours2.save_creneaux()
            return
        
        db = Database.get("edt_generator")
        sql = """
            INSERT INTO ALL_ASSOCIATIONS (ID_COURS, JOUR, HEURE) VALUES (%s, %s, %s);
        """

        for jour, prof_dispo in enumerate(self.professeur.dispo):
            dispo_counter = 0
            dispo_hour = 0
            for heure, dispo in enumerate(prof_dispo):
                if dispo == 1:
                    dispo_counter += 1
                else:
                    dispo_counter = 0
                    dispo_hour = heure + 1

                if dispo_counter >= self.duree:
                    db.run([sql, (self.id, jour, dispo_hour)])
                    dispo_counter -= 1
                    dispo_hour += 1

        db.close()

    def jsonify(self):
        return {
            "id": str(self.id),
            'idBanque': str(self.id_banque),
            'idEnseignant': str(self.professeur.id),
            'enseignant': str(self.professeur.nom),
            'type': self.type_cours,
            'libelle': self.name,
            'abreviation': self.abrevaition,
            'heureDebut': self.heure,
            'duree': int(self.duree),
            'style': self.couleur,
            'groupe': str(self.groupe),
            'warning': self.warning_message
        }

    @staticmethod
    def save_creneaux():
        db = Database.get("edt_generator")
        sql = """
            UPDATE ALL_ASSOCIATIONS
            SET NB_CRENEAUX = (SELECT COUNT(*) FROM ALL_ASSOCIATIONS AS A WHERE A.ID_COURS = ALL_ASSOCIATIONS.ID_COURS);
        """
        db.run(sql)
        db.close()