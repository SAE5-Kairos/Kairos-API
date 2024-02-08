import asyncio, random

from EDT_generator.cours import Cours

class EDT:
    SAMEDI_MALUS = 10
    MIDI_BONUS = 5
    MIDI_MALUS = 10

    # Listes des slots possibles par jour pour les cours ainsi que les dégats sur les autres cours
    COURSE_DAMAGES = [
        {}, # Lundi
        {}, # Mardi
        {}, # Mercredi
        {}, # Jeudi
        {}, # Vendredi
        {}, # Samedi
    ]
    """[ {Cours: {slot: [damages], ...}, ...}, ...], ...]"""

    week = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Lundi
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Mardi
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Mercredi
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Jeudi
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Vendredi
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
    ]

    def __init__(self):
        self.placed_cours:list(Cours) = []
        self.day_index = 0
        self.tree_index = 0
        self.final = False
        self.week = [day.copy() for day in self.week]
        self.COURS = [cours.copy() for cours in Cours.ALL]
        self.COURSE_DAMAGES = [ {course: damages.copy() for course, damages in day.items()} for day in self.COURSE_DAMAGES]

        #self.set_course_probability()

    def get_signature(self):
        singature = []
        for course in self.placed_cours:
            singature.append(f"{course.name}-{course.jour}-{course.debut}/")
        return ''.join(sorted(singature))

    @staticmethod
    def set_course_probability():
        courses_slots = {}
        for course in Cours.ALL:

            # Récupérer les slots disponibles pour un cours
            slots = course.professeur.get_slots(EDT.week, course)
            hours_slot_by_days = [
                [], # Lundi
                [], # Mardi
                [], # Mercredi
                [], # Jeudi
                [], # Vendredi
                [], # Samedi
            ]

            for day_index, day_slots in enumerate(slots):
                for slot in day_slots:
                    hours_slot_by_days[day_index].extend(slot['heures_index'])
                    hours_slot_by_days[day_index].extend([slot['heures_index'][-1] + index for index in range(1, int(course.duree * 2))])

            # Comparer ce slots avec tous les autres afin de calculer les damages
            for other_course, other_slots in courses_slots.items():
                for day_index, day_slots in enumerate(other_slots):
                    if not hours_slot_by_days[day_index]: continue

                    other_slots_hours = []
                    for other_slot in day_slots:
                        other_slots_hours.extend(other_slot['heures_index'])
                        other_slots_hours.extend([other_slot['heures_index'][-1] + index for index in range(1, int(other_course.duree * 2) + 1)])

                    if course not in EDT.COURSE_DAMAGES[day_index]:
                        EDT.COURSE_DAMAGES[day_index][course] = {}

                    if other_course not in EDT.COURSE_DAMAGES[day_index]:
                        EDT.COURSE_DAMAGES[day_index][other_course] = {}

                    for slot_hour in hours_slot_by_days[day_index]:
                        if slot_hour in other_slots_hours and slot_hour in EDT.COURSE_DAMAGES[day_index][course]:
                            EDT.COURSE_DAMAGES[day_index][course][slot_hour].append(other_course)
                        elif slot_hour in other_slots_hours:
                            EDT.COURSE_DAMAGES[day_index][course][slot_hour] = [other_course]

                        if slot_hour in other_slots_hours and slot_hour in EDT.COURSE_DAMAGES[day_index][other_course]:
                            EDT.COURSE_DAMAGES[day_index][other_course][slot_hour].append(course)
                        elif slot_hour in other_slots_hours:
                            EDT.COURSE_DAMAGES[day_index][other_course][slot_hour] = [course]

            courses_slots[course] = slots

    def update_course_probability(self, remove_course:Cours):
        for day_index in range(len(self.COURSE_DAMAGES)):
            self.COURSE_DAMAGES[day_index].pop(remove_course, None)

            for course in self.COURSE_DAMAGES[day_index]:
                for slot in self.COURSE_DAMAGES[day_index][course]:
                    if remove_course in self.COURSE_DAMAGES[day_index][course][slot]:
                        self.COURSE_DAMAGES[day_index][course][slot].remove(remove_course)

    def get_courses_damages_on(self, source, start, on):
        """
        On intersect le nombre de créneaux en commun entre l'interval [start; source.duree_demi_heure + start] et les créneaux du cours on
        :param source: @Cours()
        :param start: heure de début du cours source
        :param on: @Cours()
        :return: % de dommage sur le cours on
        """
        damages = 0
        creneaux_on = on.professeur.count_creneaux(intersect_dispo=self.week[self.day_index], creneau_list=True, creneau_size=int(on.duree * 2))
        for index in range(start, int(start + source.duree * 2)): # la durée est en heure, on la passe en nombre de demi-heure
            if index in creneaux_on: damages += 1
        return damages / (len(creneaux_on) or 1)

    def get_courses_damages(self):
        """
        L'idée de fonctionnement est de créer un dictionnaire de dommages pour chaque cours non placé
        On va d'abord instancier chaque cours dans le dictionnaire, puis
        on va regarder pour se cours, si certaines de ses heures de début son génées par celles d'autres cours

        Pour calculer les damages on va devoir procéder en deux étapes:
        Associer chaque heure de début d'un cours à une liste de pourcentage de dommage pour chaque autre cours:
        {Cours: {Heure_debut: [5_cours1_impacté_sur_5->100%, ...], ...}, ...}}

        Il faut placer en priorité les heures qui on un max damages le plus petit
        """
        damages = dict()
        """{Cours: {Heure_debut: [% aux autres cours non placés], ...}, ...}}"""
        for course in self.COURS:
            if course in self.placed_cours: continue
            damages[course] = {heure: [] for heure in course.professeur.count_creneaux(intersect_dispo=self.week[self.day_index], creneau_list=True, creneau_size=int(course.duree * 2))}

        for course in damages:
            for heure in damages[course]:
                for course_to_compare in damages:
                    if course_to_compare == course: continue
                    damages[course][heure].append(self.get_courses_damages_on(source=course, start=heure, on=course_to_compare))

        return damages

    def get_courses_pool(self, pool_size=2, randomize=True):
        creneaux = []

        # On va récupérer les cours non placés
        for cours in self.COURS:
            if cours.name in map(str, self.placed_cours): continue
            creneaux.append((cours, cours.professeur.count_creneaux(intersect_dispo=self.week[self.day_index], creneau_list=True, creneau_size=int(cours.duree * 2))))

        creneaux = sorted(creneaux, key=lambda tpl: len(tpl[1]))

        # Choisir le nombre de créneaux demandé avec une pondération aléatoire
        # NOTE: pour le moment la pondération est commune à tous les cours sans considération (la liste reste triée)
        chosen_creneaux = []
        index = 0
        max_tours = 3
        if len(creneaux) <= pool_size: return [creneau[0] for creneau in creneaux]
        while len(chosen_creneaux) < pool_size and max_tours > 0:
            if index >= len(creneaux): index = 0; max_tours -= 1
            if creneaux[index][1] in chosen_creneaux: index += 1; continue

            # Le cours est choisit s'il tombe entre 0, le nombre de point supérieur à la moyenne de son score
            # Le cours n'est pas choisit s'il tombe entre le nombre de point supérieur à la moyenne de son score, la distance de son score à 100 divisée par 2

            # Si le cours n'a pas encore de score, on le choisit par rapport au pourcentage de munation
            if not randomize:
                chosen_creneaux.append(creneaux[index])
                continue

            cours_tuple = (creneaux[index][0].name, 0, tuple((cours.name, 0, cours.debut) for cours in self.placed_cours))
            if cours_tuple in EDT.LEARNING_TABLE:
                cours_score = [sum(EDT.LEARNING_TABLE[cours_tuple][debut]) / (len(EDT.LEARNING_TABLE[cours_tuple][debut]) or 1) for debut in EDT.LEARNING_TABLE[cours_tuple]]
                cours_score = sum(cours_score) / (len(cours_score) or 1)

                bonus_point = cours_score - EDT.AVG_SCORE if cours_score > EDT.AVG_SCORE else 0
                distance_to_100 = 100 - cours_score

                if random.randint(0, int(distance_to_100 * 2)) <= bonus_point:
                    chosen_creneaux.append(creneaux[index])
            else:
                if random.randint(0, 100) <= 100 - EDT.MUTATION_RATE:
                    chosen_creneaux.append(creneaux[index])
            index += 1
        return [creneau[0] for creneau in chosen_creneaux]

    def get_courses_hour_pool(self, course, pool_size=2, randomize=True):
        # on a besoin de savoir combien de disponibilités chaque cours condamne
        damages = self.get_courses_damages()[course]

        # Récupérer les meilleurs heures de début pour le cours
        # NOTE: pour le moment on prend les deux premières heures de début les plus probables
        sorted_hour = sorted(damages, key=lambda heure: max(damages[heure]) if damages[heure] else 0)
        chosen_hours = []
        if len(sorted_hour) <= pool_size: return sorted_hour

        index = 0
        max_tours = 3
        while len(chosen_hours) < pool_size and max_tours > 0:
            if index >= len(sorted_hour): index = 0; max_tours -= 1
            if sorted_hour[index] in chosen_hours: index += 1; continue

            if not randomize:
                chosen_hours.append(sorted_hour[index])
                continue

            # S'il y a des phéromones
            course_tuple = (course.name, 0, tuple((cours.name, 0, cours.debut) for cours in self.placed_cours))
            if course_tuple in EDT.LEARNING_TABLE:
                hour_score = EDT.LEARNING_TABLE[course_tuple][sorted_hour[index]] if sorted_hour[index] in EDT.LEARNING_TABLE[course_tuple] else []
                if hour_score:
                    hour_score = sum(hour_score) / (len(hour_score) or 1)

                    bonus_point = hour_score - EDT.AVG_SCORE if hour_score > EDT.AVG_SCORE else 0
                    distance_to_100 = 100 - hour_score

                    if random.randint(0, int(distance_to_100 * 2)) <= bonus_point:
                        chosen_hours.append(sorted_hour[index])
                else:
                    if random.randint(0, 100) <= 100 - EDT.MUTATION_RATE:
                        chosen_hours.append(sorted_hour[index])
            else:
                if random.randint(0, 100) <= 100 - EDT.MUTATION_RATE:
                    chosen_hours.append(sorted_hour[index])
            index += 1
        return chosen_hours

    def parcours_1_profondeur(self):
        pool = self.get_courses_pool()

        # On va créer des instances sous forme d'arbre pour chaque cours du pool afin de parcourir
        # un grand nombre de possibilités
        # NOTE: on utilise un algorithme fourmilière pour parcourir l'arbre car le génétique n'est pas viable
        # On va créer plusieurs instances par cours pour pouvoir faire des arbres avec des cours à différentes heures de début
        # Il faut choisir les deux heures de début les plus probables pour chaque cours
        for course in pool:
            # Créer une instance de l'EDT pour chaque cours
            hours = self.get_courses_hour_pool(course)
            for hour in hours:
                instance = EDT()
                instance.day_index = self.day_index
                instance.tree_index = len(EDT.TREES)
                instance.week = [day.copy() for day in self.week]
                instance.placed_cours = self.placed_cours.copy()
                try:
                    instance.place_cours(course, hour)
                    EDT.TREES.append([edt for edt in EDT.TREES[self.tree_index]])
                    EDT.TREES[-1].append(instance)
                    instance.parcours_1_profondeur()
                except Exception as e:
                    print(e)
                    self.final = True

        if len(pool) == 0: self.final = True

    def place_cours(self, course, jour_index, heure_index):
        if heure_index + 2 * course.duree > 25: raise Exception(f"Le cours ne peut pas être placé à cette heure: {heure_index} - {2 * course.duree}\n" + str(course.professeur.get_slots(self.week, course)))
        for index in range(heure_index, int(heure_index + course.duree * 2)):
            if self.week[jour_index][index] != 1: 
                raise Exception(f"Le cours ne peut pas être placé à cette heure: {self.week[jour_index][index]} - {2 * course.duree}, {jour_index}j {index}\n" + str(course.professeur.get_slots(self.week, course)))
            self.week[jour_index][index] = course

        course.debut = heure_index
        course.jour = jour_index
        self.placed_cours.append(course)
        self.update_course_probability(course)

    def get_score(self):
        """
        score: 0 --> 100: 100 étant le meilleur score
        """
        nb_heure_by_day = [sum([0.5 for course in jour if type(course) == Cours and not course.name.startswith('Midi')]) for jour in self.week]
        score_nb_heure = [100 - (nb_heure - 8) * 30 if nb_heure > 8 else (nb_heure * 100) / 8 for nb_heure in nb_heure_by_day]
        score_nb_heure = sum(score_nb_heure) / (len(score_nb_heure) or 1)

        gap_edt_by_day = [EDT.get_nb_gap(day) for day in self.week]
        score_gap_edt = [100 - (gap_edt * 100) / 23 for gap_edt in gap_edt_by_day]
        score_gap_edt = sum(score_gap_edt) / (len(score_gap_edt) or 1)

        gap_prof = []
        profs = []
        for course in self.placed_cours:
            if course.professeur in profs: continue
            profs.append(course.professeur)

            for day in course.professeur.dispo:
                gap_prof.append(EDT.get_nb_gap(day, on_type=False))

        score_gap_prof = 100 - (sum(gap_prof) * 100) / ((len(gap_prof) or 1) * 23)

        # Malus samedi
        nb_courses_samedi = sum([1 for course in self.placed_cours if course.jour == 5])
        nb_dispo_same_samedi = sum([1 for course in self.week[5] if course != 0])
        malus_samedi = EDT.SAMEDI_MALUS * (nb_courses_samedi / (nb_dispo_same_samedi or 1))

        cours_midi = len([course for course in self.placed_cours if course.name.startswith('Midi')])
        total_cours_midi = sum([1 for course in self.COURS if course.name.startswith('Midi')])
        bonus_midi = EDT.MIDI_BONUS * (cours_midi / (total_cours_midi or 1))
        malus_midi = EDT.MIDI_MALUS * (cours_midi - total_cours_midi)

        return  (4.5 * score_nb_heure + 4 * score_gap_edt + 2 * score_gap_prof) / 10.5 - malus_samedi + bonus_midi - malus_midi

    def __repr__(self) -> str:
        return "\n".join([str(day) for day in self.week])

    def jsonify(self):
        json_obj = {
            'Lundi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 0 and not cours.display_name.startswith('Midi')
            ],

            'Mardi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 1 and not cours.display_name.startswith('Midi')
            ],

            'Mercredi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 2 and not cours.display_name.startswith('Midi')
            ],

            'Jeudi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 3 and not cours.display_name.startswith('Midi')
            ],

            'Vendredi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 4 and not cours.display_name.startswith('Midi')
            ],

            'Samedi': [
                {'id': f'c{cours.name}', 'enseignant': f'{cours.professeur}', 'type': 'TD', 'libelle': cours.display_name, 'heureDebut': cours.debut, 'duree': int(cours.duree * 2), 'style': cours.color} for cours in sorted(self.placed_cours, key=lambda c: c.debut or 0) if cours.jour == 5 and not cours.display_name.startswith('Midi')
            ],
        }
        return json_obj

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
            if (on_type and type(element) == Cours) or (not on_type and element == 1):
                day_start = True
                total_gap += count_gap
                count_gap = 0

            if day_start and ((on_type and type(element) != Cours) or (not on_type and element == 0)): count_gap += 1

        return total_gap

    @staticmethod
    def get_glouton_solution():
        edt = EDT()

        while True:

            # On récupère les cours non placés
            course = edt.get_courses_pool(1, False)
            if len(course) == 0: break
            else: course = course[0]
            hour = edt.get_courses_hour_pool(course, 1, False)
            if len(hour) == 0: break
            else: hour = hour[0]

            try:
                edt.place_cours(course, hour)
            except:
                break

        return edt

