from Kairos_API.database import Database

class Cours2:
    AUTO_INCREMENT = 0
    ALL: 'list[Cours2]' = []

    def __init__(self, professeur, duree:int, name:str, id_banque:int, couleur, type_cours, _copy=False, _id=None) -> None:
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

        if not _copy:
            Cours2.ALL.append(self)

    @staticmethod
    def get(id_cours: int) -> 'Cours2':
        for cours in Cours2.ALL:
            if cours.id == id_cours:
                return cours
        raise Exception(f"[Cours2][get]({id_cours}) -> Cours non trouvé")

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Cours2):
            return self.id == __value.id
        elif isinstance(__value, int):
            return self.id == __value
        else:
            return False

    def __str__(self) -> str:
        return f"Cours2<{self.id}>: {self.duree}"

    def __repr__(self) -> str:
        return f"C{self.id}"
        
    def copy(self):
        return Cours2(professeur=self.professeur, duree=self.duree, name=self.name, id_banque=self.id_banque, couleur=self.couleur, type_cours=self.type_cours, _copy=True, _id=self.id)

    def save_associations(self=None):
        if self is None:
            for cours in Cours2.ALL:
                cours.save_associations()
            
            Cours2.save_damages()
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

                if dispo_counter == self.duree:
                    db.run([sql, (self.id, jour, dispo_hour)])
                    dispo_counter -= 1
                    dispo_hour += 1

        db.close()

    def jsonify(self):
        # {'id': f'{cours.name}', 'idBanque': f'{cours.banque}', 'idEnseignant': f'{cours.id_prof}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'abreviation': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 0 and not cours.display_name.startswith('Midi')
        return {
            "id": self.id,
            'idBanque': str(self.id_banque),
            'idEnseignant': str(self.professeur.id),
            'enseignant': str(self.professeur.nom),
            'type': self.type_cours,
            'abreviation': self.name,
            'heureDebut': self.heure,
            'duree': int(self.duree),
            'style': self.couleur
        }

    @staticmethod
    def save_damages():
        db = Database.get("edt_generator")
        sql = """
            UPDATE ALL_ASSOCIATIONS
            SET DAMAGES = (SELECT COUNT(*) FROM ALL_ASSOCIATIONS AS A WHERE A.JOUR = ALL_ASSOCIATIONS.JOUR AND A.HEURE = ALL_ASSOCIATIONS.HEURE) - 1;
        """
        db.run(sql)
        db.close()
