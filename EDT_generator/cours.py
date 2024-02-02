class Cours:
    ALL = []

    def __init__(self, professeur, duree, banque, name=None, color="#0000FF", _cpy=False, _cpy_id=None):
        """
        :param professeur: @Professeur()
        :param duree: En heure (ex. 1.5, 2, ...)
        :param name: intitulé du cours (doit être unique)
        """

        self.professeur = professeur
        self.duree = duree
        self.banque = banque
        self.name = str(_cpy_id or f"C{len(Cours.ALL) + 1}")
        self.display_name = name
        self.debut = None
        self.jour = None
        self.color = color

        if not _cpy: Cours.ALL.append(self)

    def __str___(self):
        return str(self.name)
    
    def __repr__(self):
        return str(self.name)
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Cours):
            return self.name == __value.name
        elif isinstance(__value, str):
            return self.name == __value
        else:
            return False
        
    def __hash__(self):
        return hash(self.name)
    
    def get_course_by_name(name):
        for course in Cours.ALL:
            if course.name == name: return course
        return None

    def copy(self):
        return Cours(self.professeur, self.duree, self.banque, self.display_name, self.color, _cpy=True, _cpy_id=self.name)
    