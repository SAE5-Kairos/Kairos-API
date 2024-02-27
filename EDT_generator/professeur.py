class Professeur:
    ALL = []

    def __init__(self, dispo, name=None):
        self.dispo: list[list[int]] = dispo
        self.creneaux: dict = dict()
        self.name = name if name is not None else f"Professeur {len(Professeur.ALL) + 1}"

        Professeur.ALL.append(self)

    def count_creneaux(self, intersect_dispo=None, creneau_list: bool = False, creneau_size: int = 0):
        """
        On veut récupérer le nombre de créneaux disponibles pour le professeur selon ses disponibilités.

        par exemple: [1, 1, 1, 0]
                    | >-->-->
                    | >-->
                    | >
        Dans cet exemple il y a donc 1 créneau de 3, 2 créneaux de 2 et 3 de 1

        :param intersect_dispo : Permet d'intersect les dispo de l'EDT journalier à celles du professeur
        :param creneau_list: Vrai | Faux, Indique si la fonction doit retourner une liste de creneaux (index heure debut)
        :param creneau_size: défini la taille des créneaux dans la liste des créneaux retournée (creneau_list = Vrai)
        :return: Met à jour self.creneaux | liste de creneaux de taille indiquée
        """

        if intersect_dispo is not None and len(intersect_dispo) < 25:
            raise Exception("intersect_dispo doit contenir 25 éléments")

        last_element = 0
        creneaux = []

        # On parcours la liste des dispo du professeur
        for index, element in enumerate(self.dispo):

            # Si l'ensemble des conditions de disponibilité sont réunies
            if element == 1 and (intersect_dispo is None or intersect_dispo[index] == 1):
                last_element += 1

                if creneau_list and last_element >= creneau_size: creneaux += [index - creneau_size + 1]
                for sub_creneaux in range(1, last_element + 1):
                    if sub_creneaux in self.creneaux:
                        self.creneaux[sub_creneaux] += 1
                    else:
                        self.creneaux[sub_creneaux] = 1
            else:
                last_element = 0

        if creneau_list: return creneaux

    def get_slots(self, intersect_dispo, cours):
        """
        Récupère les créneaux disponibles pour le professeur pour un cours donné

        :param intersect_dispo: Permet d'intersect les dispo de l'EDT journalier à celles du professeur
        :param cours: Cours pour lequel on veut récupérer les créneaux disponibles

        :return: Liste de créneaux disponibles pour le professeur pour le cours donné
        """
        slots = []
        """[ [slots jour i], ...]"""

        # Créer le resultat de l'intesection des dispo du professeur et de l'EDT

        # On parcours la liste des horraires de la semaine avec un compteur, 
        # si le compteur atteint la taille du cours, on ajoute le créneau du début du compteur à la liste des créneaux
        # On décale le créneau du début du compteur a +1 et on retire 1 au compteur

        # Intersecter les dispo du professeur avec celles de l'EDT
        week_intersect_dispo = []

        for jour, prof_dispo_calendrier in enumerate(self.dispo):
            week_intersect_dispo.append([])
            for heure, prof_dispo in enumerate(prof_dispo_calendrier):
                week_intersect_dispo[-1].append(prof_dispo * intersect_dispo[jour][heure])

        # On récupère les créneaux disponibles
        for jour, dispo_calendrier in enumerate(week_intersect_dispo):
            compteur = 0
            debut_creneau = 0

            for heure, dispo in enumerate(dispo_calendrier):
                if dispo == 1:
                    compteur += 1
                    if compteur == cours.duree * 2:
                        slots.append((jour, debut_creneau))
                        compteur -= 1
                        debut_creneau += 1
                else:
                    compteur = 0
                    debut_creneau = heure + 1

        return slots


        for jour, prof_dispo_calendrier in enumerate(self.dispo):
            on_slot = False
            slots.append([])

            for heure, prof_dispo in enumerate(prof_dispo_calendrier):
                if prof_dispo == 1 and intersect_dispo[jour][heure] == 1:
                    if not on_slot:
                        slots[-1].append({"total_dispo": 1, "heures_index": [heure]})
                        on_slot = True
                    else:
                        slots[-1][-1]["total_dispo"] += 1
                        slots[-1][-1]["heures_index"].append(heure)
                else:
                    # Retirer les créneaux ne permettant pas de placer le cours
                    nb_creneaux = int(cours.duree * 2) - 1
                    if on_slot and slots[-1][-1]["total_dispo"] <= nb_creneaux:
                        del slots[-1][-1]

                    elif on_slot and slots[-1][-1]["total_dispo"] > nb_creneaux and nb_creneaux > 0:
                        slots[-1][-1]["heures_index"] = slots[-1][-1]["heures_index"][:-nb_creneaux]
                        slots[-1][-1]["total_dispo"] -= nb_creneaux
                    on_slot = False
        
            # Retirer les créneaux ne permettant pas de placer le cours
            nb_creneaux = int(cours.duree * 2) - 1
            if on_slot and slots[-1][-1]["total_dispo"] <= nb_creneaux:
                del slots[-1][-1]

            elif on_slot and slots[-1][-1]["total_dispo"] > nb_creneaux and nb_creneaux > 0:
                slots[-1][-1]["heures_index"] = slots[-1][-1]["heures_index"][:-nb_creneaux]
                slots[-1][-1]["total_dispo"] -= nb_creneaux 

        return slots

    def __repr__(self):
        return self.name
    
