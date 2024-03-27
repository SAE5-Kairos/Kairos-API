class Professeur2:
    ALL = []

    def __init__(self, id, nom, dispo, _copy=False) -> None:
        self.id = id
        self.nom = nom
        self.dispo = dispo

        if not _copy:
            Professeur2.ALL.append(self)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Professeur2):
            return self.id == __value.id
        elif isinstance(__value, int):
            return self.id == __value
        else:
            return False
        
    def copy(self):
        return Professeur2(self.id, self.nom, self.dispo, _copy=True)
    
    def get(id_prof):
        for prof in Professeur2.ALL:
            if prof.id == id_prof:
                return prof
        raise Exception(f"[Professeur2][get]({id_prof}) -> Professeur non trouvé")
    
    @staticmethod
    def generate_dispo(semaine: int, data: 'list[dict]'):
        """
            Permet de générer les disponibilités d'un professeur sous format binaire en fonction des données en BDD
            1 -> Disponible
            0 -> Indisponible
            :param semaine: int -> Numéro de la semaine (ISO)
            :param data: [ { DateDebut: datetime, DateFin: datetime } ] -> Absences du professeur (BDD)

            :return: [ [ int ] ] -> Disponibilités du professeur
        """
        dispo = [[ 1 for _ in range(24)] for __ in range(6)]
        for indispo in data:
            if indispo["DateFin"].isocalendar()[1] > semaine: indispo['JourFin'] = 6

            if indispo["DateDebut"].date() == indispo["DateFin"].date():
                for creneau in range((indispo["DateDebut"].hour - 8) * 60 + indispo["DateDebut"].minute, (indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                    dispo[indispo["DateDebut"].weekday()][creneau // 30] = 0

            else:
                # Si l'absence est sur la même semaine
                if indispo["DateDebut"].isocalendar()[1]  == indispo["DateFin"].isocalendar()[1]:
                    for day in range(indispo["DateDebut"].weekday(), indispo["DateFin"].weekday()):
                        dispo[day] = [ 0 for _ in range(24)]

                    for creneau in range((indispo["DateFin"].hour - 8) * 60 + indispo["DateFin"].minute, 30):
                        dispo[indispo["DateFin"].weekday()][creneau // 30] = 0

                # Si le prof est abs toute la semaine
                else: dispo = [[ 0 for _ in range(24)] for __ in range(6)]

        return dispo
