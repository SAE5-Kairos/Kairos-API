from Kairos_API.database import Database


class Salle:
    ALL = []

    def __init__(self, id, label=None, dispo=None, _copy=False) -> None:
        self.id = id
        self.nom = label if label else f"Salle {id}"
        self.dispo = dispo if dispo else [[1 for _ in range(24)] for __ in range(6)]

        if not _copy:
            Salle.ALL.append(self)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Salle):
            return self.id == __value.id
        elif isinstance(__value, int):
            return self.id == __value
        else:
            return False

    def copy(self):
        return Salle(self.id, self.nom, self.dispo, _copy=True)

    def get(id_prof):
        for salle in Salle.ALL:
            if salle.id == id_prof:
                return salle
        raise Exception(f"[Salle][get]({id_prof}) -> Salle non trouvé")

    @staticmethod
    def generate_dispo(id_salle: int, annee: int, semaine: int, cours_is_indispo=False):
        """
            Permet de générer les disponibilités d'un professeur sous format binaire en fonction des données en BDD
            1 -> Disponible
            0 -> Indisponible
            {'groupe': IdGroupe du cours} -> Cours déjà présent (ou 0 si salle_is_indispo = True)

            :param id_salle: int -> ID du professeur
            :param annee: int -> Année de la semaine
            :param semaine: int -> Numéro de la semaine

            :return: [ [ int ] ] -> Disponibilités de la salle
        """

        sql_salle_indispo = """
            SELECT 
                DateDebut, DateFin, 
                WEEKDAY(DateDebut) AS JourDebut,
                WEEKDAY(DateFin) AS JourFin
            FROM 
                IndisponibiliteSalle
            WHERE 
                IdSalle = %s 
                AND WEEK(DateDebut, 1) <= %s AND WEEK(DateFin, 1) >= %s
                AND YEAR(DateDebut) <= %s AND YEAR(DateFin) >= %s
        """

        sql_prof_cours = """
            SELECT c.NumeroJour, c.HeureDebut, b.Duree, c.IdGroupe
            FROM Cours c
                JOIN Banque b ON c.IdBanque = b.IdBanque
                JOIN EDT e ON c.IdEDT = e.IdEDT
            WHERE b.IdSalle = %s AND e.Semaine = %s AND e.Annee = %s AND c.HeureDebut IS NOT NULL
        """

        db = Database.get()
        db.run([sql_salle_indispo, (id_salle, semaine, semaine, annee, annee)])
        data = db.fetch()

        dispo = [[1 for _ in range(24)] for __ in range(6)]
        for indispo in data:
            if indispo["DateFin"].isocalendar()[1] > semaine: indispo['JourFin'] = 6

            if indispo["DateDebut"].date() == indispo["DateFin"].date():
                for creneau in range((indispo["DateDebut"].hour - 8) * 60 + indispo["DateDebut"].minute,
                                     (indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                    dispo[indispo["DateDebut"].weekday()][creneau // 30] = 0

            else:
                # Si l'absence est sur la même semaine
                if indispo["DateDebut"].isocalendar()[1] == indispo["DateFin"].isocalendar()[1]:
                    for day in range(indispo["DateDebut"].weekday(), indispo["DateFin"].weekday()):
                        dispo[day] = [0 for _ in range(24)]

                    for creneau in range((indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                        dispo[indispo["DateFin"].weekday()][creneau // 30] = 0

                # Si le prof est abs toute la semaine
                else:
                    dispo = [[0 for _ in range(24)] for __ in range(6)]
        """
        prof_cours = db.run([sql_prof_cours, (id_salle, semaine, annee)]).fetch()
        for cours in prof_cours:
            heures = [cours["HeureDebut"] + i for i in range(cours["Duree"])]
            for heure in heures:
                dispo[cours["NumeroJour"]][heure] = 0 if cours_is_indispo else {'groupe': cours["IdGroupe"]}
        """
        return dispo

    @staticmethod
    def init():
        Salle.ALL = []
