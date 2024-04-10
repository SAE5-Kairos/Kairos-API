
from EDT_generator.V2.cours2 import Cours2


class EDT2:
    MALUS_NB_HEURE = 10
 
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

    def get_score(self, details=False):
        """
        score: 0 --> 100: 100 étant le meilleur score
        """
        # Nombre d'heure par jour
        nb_heure_by_day = [sum([cours.duree for cours in self.cours if cours.jour == day and cours.type_cours != "Midi"]) for day in range(6)]
        nb_heure_malus_by_day = [max(0, nb_heure - 14) for nb_heure in nb_heure_by_day]

        score_nb_heure = len([cours for cours in self.cours if cours.type_cours != "Midi"]) / (len([cours for cours in Cours2.ALL if cours.type_cours != "Midi"]) or 1)
        score_malus_nb_heure = -sum(nb_heure_malus_by_day) * EDT2.MALUS_NB_HEURE
        score_nb_heure = score_nb_heure * 100 + score_malus_nb_heure

        # Gap de l'emploi du temps
        gap_edt_by_day = [EDT2.get_nb_gap(day, get_distance_from_middle=True) for day in self.week]
        score_gap_edt = [100 - ((gap_edt[0] * 6)**2 * 100) / 24**2 for gap_edt in gap_edt_by_day]
        score_gap_edt = sum(score_gap_edt) / (len(score_gap_edt) or 1)
        score_gap_distance = 100 - sum([gap_edt[1] / (len(self.week[0]) / 2) for gap_edt in gap_edt_by_day]) / (len(gap_edt_by_day) or 1) * 100

        # Gap des profs
        gap_prof = []
        profs = []
        for course in self.cours:
            if course.professeur in profs: continue
            profs.append(course.professeur)

            for day in course.professeur.dispo:
                gap_prof.append(EDT2.get_nb_gap(day, on_type=False))

        score_gap_prof = 100 - (sum(gap_prof) * 100) / ((len(gap_prof) or 1) * 23)

        # Malus samedi
        nb_courses_samedi = sum([course.duree for course in self.cours if course.jour == 5 and course.type_cours != "Midi"])
        score_samedi = (1 - (nb_courses_samedi / 24) * 1.5) * 100

        # Bonus midi
        cours_midi = len([course for course in self.cours if course.type_cours == "Midi"])
        total_cours_midi = len([course for course in Cours2.ALL if course.type_cours == "Midi"])
        score_midi = cours_midi / (total_cours_midi or 1) * 100

        if details:
            return {
                "gap_edt_by_day": gap_edt_by_day,
                "score_nb_heure": score_nb_heure,
                "cours_midi": cours_midi,
                "score_malus_nb_heure": score_malus_nb_heure,
                "score_gap_edt": score_gap_edt,
                "score_gap_prof": score_gap_prof,
                "score_gap_distance": score_gap_distance,
                "score_samedi": score_samedi,
                "score_midi": score_midi,
                "score": (2 * score_nb_heure + 3.5 * score_gap_edt + 1 * score_gap_prof + 1 * score_gap_distance + 1.5 * score_samedi + 2 * score_midi) / 11
            }

        return (2 * score_nb_heure + 3.5 * score_gap_edt + 1 * score_gap_prof + 1 * score_gap_distance + 1.5 * score_samedi + 2 * score_midi) / 11

    @staticmethod
    def get_nb_gap(edt: list, on_type=True, get_distance_from_middle=False):
        """
        :param edt: emploi du temps d'une journée dont l'on veut connaitre le nombre de gap
        :param on_type: si les heures pleines sont des cours: Vrai sinon les heures pleines sont des 1
        :return: le nombre de gap (int)
        """

        middle = len(edt) // 2
        max_gap_distance = [0]

        day_start = False
        count_gap = 0
        total_gap = 0
        count_next_gap = False
        for index, element in enumerate(edt):
            if (on_type and type(element) == Cours2) or (not on_type and element == 1):
                day_start = True

                if not count_next_gap and not (type(element) == Cours2 and element.type_cours == "Midi"):
                    count_next_gap = True
                    max_gap_distance[-1] = 0
                    count_gap = 0
                    continue

                total_gap += count_gap
                count_gap = 0
                max_gap_distance.append(0)

            if day_start and ((on_type and type(element) != Cours2) or (not on_type and element == 0)): 
                count_gap += 1

                if get_distance_from_middle and count_next_gap:
                    max_gap_distance[-1] = max(max_gap_distance[-1], index - abs(index - middle))

        # Retirer le dernier gap si le dernier créneau est vide
        if count_gap:
            max_gap_distance.pop()

        if get_distance_from_middle:
            return total_gap, sum(max_gap_distance) / (len(max_gap_distance) or 1)
        return total_gap

    def jsonify(self):
        jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

        json_obj = {jour: [] for jour in jours}
        self.cours.sort(key=lambda x: x.heure)
        for cours in self.cours:
            if cours.type_cours == "Midi": continue
            json_obj[jours[cours.jour]].append(cours.jsonify())

        return json_obj
