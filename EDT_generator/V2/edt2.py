
from EDT_generator.V2.cours2 import Cours2


class EDT2:
    SAMEDI_MALUS = 8
    MIDI_BONUS = 15

    def __init__(self, _from_cours=None):
        self.cours: 'list[Cours2]' = []
        self.week = [[1 for _ in range(24)] for __ in range(6)]

        if _from_cours:
            for cours in _from_cours:
                self.add_cours(cours, cours.jour, cours.heure)

    def __str__(self):
        return f"{self.week}"

    def add_cours(self, cours:Cours2, jour, heure):
        # 1. Vérifier que le cours n'est pas déjà présent
        if cours in self.cours:
            raise Exception(f"[EDT][add_cours]({cours}) -> Cours déjà présent dans l'emploi du temps")
        
        # 2. Vérifier que le prof est disponible et que le cours ne chevauche pas un autre
        is_free = self.is_free(jour, heure, cours)
        if is_free == -1:
            raise Exception(f"[EDT][add_cours]({cours}, j:{jour}, h:{heure}) -> Cours impossible à ajouter; Chevauchement \n{self.week[jour]}")
        if is_free == -2:
            raise Exception(f"[EDT][add_cours]({cours}, j:{jour}, h:{heure}) -> Cours impossible à ajouter; Indisponibilité du professeur")
        
        # 3. Ajouter le cours
        cours = cours.copy()
        self.cours.append(cours)
        for i in range(cours.duree):
            self.week[jour][heure + i] = cours
        
        cours.jour = jour
        cours.heure = heure

    def is_free(self, jour, heure, cours):
        """
        :param jour: int -> Jour de la semaine
        :param heure: int -> Heure de début du cours
        :param cours: Cours2 -> Cours à ajouter
        :return int: -1: Cours impossible à ajouter; Chevauchement
                     -2: Cours impossible à ajouter; Indisponibilité du professeur
                      1: Cours possible à ajouter
        """
        duree = cours.duree
        for i in range(duree):
            if self.week[jour][heure + i] != 1:
                return -1
            if cours.professeur.dispo[jour][heure + i] != 1:
                return -2
        return 1
    
    def get_collided_courses(self, jour: int, heure: int, cours: Cours2):
        """
        :param jour: int -> Jour de la semaine
        :param heure: int -> Heure de début du cours
        :param cours: Cours2 -> Cours à ajouter
        :return list[Cours2]: Liste des cours qui chevauchent
        """
        duree = cours.duree
        collided_courses: list[Cours2] = []
        for i in range(duree):
            if self.week[jour][heure + i] != 1 and self.week[jour][heure + i] not in collided_courses:
                collided_courses.append(self.week[jour][heure + i])
        return collided_courses

    def remove_cours(self, cours:Cours2):
        if cours not in self.cours:
            raise Exception(f"[EDT][remove_cours]({cours}) -> Cours non présent dans l'emploi du temps")
        
        for i in range(cours.duree):
            self.week[cours.jour][cours.heure + i] = 1
        self.cours.remove(cours)

    def get_score(self):
        """
        score: 0 --> 100: 100 étant le meilleur score
        """
        nb_heure_by_day = [sum([0.5 for course in jour if type(course) == Cours2 and not course.type_cours != "Midi"]) for jour in self.week]
        score_nb_heure = [100 - (nb_heure - 8) * 35 if nb_heure > 8 else (nb_heure * 100) / 8 for nb_heure in nb_heure_by_day]
        score_nb_heure = sum(score_nb_heure) / (len(score_nb_heure) or 1)

        gap_edt_by_day = [EDT2.get_nb_gap(day) for day in self.week]
        score_gap_edt = [100 - (gap_edt**1.5 * 100) / 22**1.5 for gap_edt in gap_edt_by_day]
        score_gap_edt = sum(score_gap_edt) / (len(score_gap_edt) or 1)

        gap_prof = []
        profs = []
        for course in self.cours:
            if course.professeur in profs: continue
            profs.append(course.professeur)

            for day in course.professeur.dispo:
                gap_prof.append(EDT2.get_nb_gap(day, on_type=False))

        score_gap_prof = 100 - (sum(gap_prof) * 100) / ((len(gap_prof) or 1) * 23)

        # Malus samedi
        nb_courses_samedi = sum([1 for course in self.cours if course.jour == 5])
        nb_dispo_same_samedi = sum([1 for course in self.week[5] if course != 0])
        malus_samedi = EDT2.SAMEDI_MALUS * (nb_courses_samedi / (nb_dispo_same_samedi or 1))

        cours_midi = len([course for course in self.cours if course.type_cours == "Midi"])
        total_cours_midi = sum([1 for course in Cours2.ALL if course.type_cours == "Midi"])
        bonus_midi = EDT2.MIDI_BONUS * (cours_midi / (total_cours_midi or 1))

        return  (3.5 * score_nb_heure + 2 * score_gap_edt + 1 * score_gap_prof) / 6.5 - malus_samedi + bonus_midi

    @staticmethod
    def get_nb_gap(edt: list, on_type=True):
        """
        :param edt: emploi du temps d'une journée dont l'on veut connaitre le nombre de gap
        :param on_type: si les heures pleines sont des cours: Vrai sinon les heures pleines sont des 1
        :return: le nombre de gap (int)
        """

        day_start = False
        count_gap = 0
        total_gap = 0

        for index, element in enumerate(edt):
            if (on_type and type(element) == Cours2) or (not on_type and element == 1):
                day_start = True
                total_gap += count_gap
                count_gap = 0

            if day_start and ((on_type and type(element) != Cours2) or (not on_type and element == 0)): count_gap += 1

        return total_gap

    def jsonify(self):
        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

        json_obj = {jour: [] for jour in jours}
        self.cours.sort(key=lambda x: x.heure)
        for cours in self.cours:
            if cours.type_cours == "Midi": continue
            json_obj[jours[cours.jour]].append(cours.jsonify())

        return json_obj