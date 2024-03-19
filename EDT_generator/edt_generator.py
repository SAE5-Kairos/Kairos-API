import random, asyncio, datetime, gc
from Kairos_API.database import Database
from EDT_generator.edt import EDT
from EDT_generator.cours import Cours
from collections import defaultdict

class Ant:

    def __init__(self, dP=0.5, dV=0.5):
        self.edt = EDT()
        self.dP = dP
        self.dV = dV
        self.node_history = []
        self.score_evolution = []
        self.focused_score = None

    def __repr__(self) -> str:
        return f"Ant:\n{self.edt}"

    def choose_next_node(self, db:Database):
        """
            Node: (cours.name, cours.jour, cours.debut)

            P -> probabilité de choisir un noeud en fonction de la phéromone
            V -> probabilité de choisir un noeud en fonction de la visibilité

            P * V = probabilité de choisir un noeud en fonction de la phéromone et de la visibilité
            (P * V) / somme(P * V) = probabilité de choisir un noeud en fonction de la phéromone et de la visibilité normalisée
        """
        
        # On récupère les cours disponibles
        available_courses:list[Cours] = [course for course in Cours.ALL if course not in self.edt.placed_cours]
        if not available_courses: return None

        P = {} # Probabilité de choisir un cours, à un créneau en fonction des phéromones
        """(cours.name, cours.jour, cours.debut): probabilité)"""
        V = {} # Probabilité de choisir un cours, à un créneau en fonction de la visibilité
        """(cours.name, cours.jour, cours.debut): probabilité)"""

        # Pour chacun des cours disponibles on va récupérer sa probabilité de choix (P et V)
        for course in available_courses:
            # On récupère les créneaux disponibles pour le professeur pour ce cours
            # Un créneau est un tuple (jour, heure)

            slots = course.professeur.get_slots(self.edt.week, course)
            """[ [{'total_dispo': int, 'heures_index': [int, ...]}, ...], ...]"""

            for jour, day_slots in enumerate(slots):
                for slot in day_slots:
                    for heure in slot["heures_index"]:
                        # On récupère la probabilité de choisir ce cours en fonction des phéromones
                        P[(course.name, jour, heure)] = EDT_GENERATOR.LEARNING_TABLE.get((course.name, jour, heure), 0)

                        # On récupère la probabilité de choisir ce cours en fonction de la visibilité
                        V[(course.name, jour, heure)] = EDT_GENERATOR.get_visibility_probability((course.name, jour, heure), course, self.edt)

        if EDT_GENERATOR.RELEARNING:
            if len(V) == 1:
                return list(V.keys())[0]
            if len(V) == 0:
                return None
            return list(V.keys())[random.randint(0, len(V) - 1)]

        max_V = max(V.values()) if V else 0
        if max_V != 0:
            for node in V:
                V[node] = (max_V - V[node]) * 100 / max_V
        node_probabilities = {}

        signature = self.edt.get_signature() # On récupère la signature de l'EDT actuel

        sql = """
            SELECT SUM(NOMBRE) as n
            FROM EDT_SIGNATURES
            WHERE SIGNATURE LIKE %s
        """

        total_nb_edt_with_same_signature = int(db.run([sql, (signature + '%%',)]).fetch(first=True)['n'] or 0)
        
        # lent, à optimiser
        # On calcule la probabilité de choisir un cours en fonction de la phéromone et de la visibilité
        for node in V:
            furtur_signature = signature + f"{node[0]}-{node[1]}-{node[2]}/" # On calcule la signature de l'EDT si on place le cours

            # On cherche à connaitre le nombre de fois que l'EDT a été créé avec la signature actuel + le cours
            # Au total lors de l'ensemble des itérations
            
            times_furtur_signature = int(db.run([sql, (furtur_signature + '%%',)]).fetch(first=True)['n'] or 0)
            # On compare la signature actuel + le cours afin de voir le nombre de fois qu'il a été choisi

            # On calcule le facteur de diversité; TODO: régle de calcul à revoir
            if total_nb_edt_with_same_signature != 0 and times_furtur_signature * (1 + EDT_GENERATOR.DIVERSITY_COEF) > total_nb_edt_with_same_signature:
                diversity_factor = EDT_GENERATOR.DIVERSITY_COEF
            else:
                diversity_factor = 1

            pheromone_score = self.dP * P[node] * EDT_GENERATOR.PHEROMONE_BOOST 
            visibility_score = self.dV * V[node]
            node_probabilities[node] = (pheromone_score + visibility_score) * diversity_factor

        del P, V

        if not node_probabilities: return None
        
        # On lance un random pour choisir le prochain cours
        max_probability = sum(node_probabilities.values())
        random_value = random.uniform(0, max_probability)

        # On récupère le cours correspondant à la probabilité
        for node in node_probabilities:
            if node_probabilities[node] > random_value:
                return node
            random_value -= node_probabilities[node]
    
        return None

    async def visit(self, db:Database):
        node = self.choose_next_node(db=db)

        sql = """
            SELECT AVG(p.PHEROMONE) as p
            FROM PHEROMONES p
                    JOIN COURS c ON p.ID_COURS = c.ID
            WHERE c.COURS = %s AND c.JOUR = %s AND c.DEBUT = %s
        """

        sql_insert_p = """
            INSERT INTO PHEROMONES (ID_COURS, PHEROMONE, BOOSTED) VALUES (%s, %s, 1)
        """

        sql_insert_cours = """
            INSERT INTO COURS (COURS, JOUR, DEBUT) VALUES (%s, %s, %s)
        """

        sql_select = """
            SELECT ID FROM COURS WHERE COURS = %s AND JOUR = %s AND DEBUT = %s
        """
        while node is not None:
            before_score = self.edt.get_score()

            self.node_history.append(node)
            cours = Cours.get_course_by_name(node[0])
            self.edt.place_cours(cours, node[1], node[2])

            # On calcule le score après avoir placé le cours et on l'ajoute à la liste des phéromones
            # Prends un peu de temps, est ce vraiment utile 0.005 par cours placé * nb fourmis * nb itérations
            variation_score = self.edt.get_score() - before_score
            moy_score = db.run([sql, (node[0], node[1], node[2])]).fetch(first=True)['p'] or 0
            score = str(moy_score + variation_score)
            if moy_score == 0:
                db.run([sql_insert_cours, (node[0], node[1], node[2])])
                cours = db.last_id()
            else:
                cours = db.run([sql_select, (node[0], node[1], node[2])]).fetch(first=True)['ID']
        
            node = self.choose_next_node(db=db)

        # Vérifier si l'EDT est meilleur que le meilleur EDT
        # TODO: Swtich en BDD
        score = self.edt.get_score()
        if score > EDT_GENERATOR.BETTER_EDT_SCORE:
            async with EDT_GENERATOR.BETTER_EDT_LOCK:
                EDT_GENERATOR.BETTER_EDT_SCORE = score
                EDT_GENERATOR.BETTER_EDT = self.edt

        return self

    async def learn(self):
        score = self.edt.get_score()
        await EDT_GENERATOR.update_learning_table_list(self.node_history, score)
        #for node in self.node_history:
        #   await EDT_GENERATOR.update_learning_table(node, score)

    def __str__(self):
        return f"(*-*)"


class EDT_GENERATOR:

    PARAM_SAVE = {}
    """Utilisé pour sauvegarder les paramètres de l'EDT_GENERATOR lors du runtime"""

    LEARNING_TABLE = {}
    """{(cours.name, cours.jour, cours.debut): [scores]}"""

    CRITICAL_DAMAGES_COEF = 5
    """Coefficient de pondération des dommages critiques par rapport aux dommages normaux"""

    DIVERSITY_COEF = 0.4 # Si l'edt en conception est similaire à plus de [DIVERSITY_COEF] % des edt déjà créés, on diminue la probabilité de le choisir de [ * DIVERSITY_COEF] 
    """Diminution d'une probabilité en fonction du nombre de fois qu'elle a été choisie, 0 = pas de diminution, 1 = diminution maximale"""

    PHEROMONE_FUNC = 'mean'
    """Fonction de calcul de la phéromone, 'mean' = moyenne, 'max' = maximum, 'min' = minimum"""

    PHEROMONE_BOOST = 1
    """Coefficient fixe de pondération de la phéromone par rapport à la visibilité (utilité non prouvée / testée)""" # problème de normalisation

    RELEARNING = False
    """Change le comportement d'apprentissage, afin de pouvoir sortir d'une impasse"""

    LOW_GRANULARITY_SCORE_BONUS = 1.5
    """Bonus de score données pour les scores calculé à l'aide de variations faibles granularités"""

    LEARNING_TABLE_LOCK = None

    CREATED_EDT = {}
    """{signature: nb_times}"""

    CREATED_EDT_LOCK = None

    BETTER_EDT_SCORE = 0
    """Meilleur score d'EDT"""

    BETTER_EDT:EDT = None

    BETTER_EDT_LOCK = None

    @classmethod
    async def update_learning_table(cls, key, value):
        async with cls.LEARNING_TABLE_LOCK:            
            cls.LEARNING_TABLE[key].append(value)

    @classmethod
    async def update_learning_table_list(cls, list_of_key, value):
        sql_insert = """
            INSERT INTO PHEROMONES (COURS, PHEROMONE) VALUES (%s, %s)
        """
        sql_select = """
            SELECT ID FROM COURS WHERE COURS = %s AND JOUR = %s AND DEBUT = %s
        """

        db = Database.get("edt_generator")
        for key in list_of_key:
            COURS = db.run([sql_select, (key[0], key[1], key[2])]).fetch(first=True)['ID']
            db.run([sql_insert, (COURS, value)])

    @classmethod
    async def update_created_edt(cls, key):
        async with cls.CREATED_EDT_LOCK:
            if key in cls.CREATED_EDT:
                cls.CREATED_EDT[key] += 1
            else:
                cls.CREATED_EDT[key] = 1

    @staticmethod
    def init():
        EDT_GENERATOR.LEARNING_TABLE = defaultdict(list)
        EDT_GENERATOR.CREATED_EDT = {}
        EDT_GENERATOR.LEARNING_TABLE_LOCK = asyncio.Lock()
        EDT_GENERATOR.BETTER_EDT_LOCK = asyncio.Lock()
        EDT_GENERATOR.CREATED_EDT_LOCK = asyncio.Lock()
        EDT_GENERATOR.BETTER_EDT_SCORE = 0
        EDT_GENERATOR.BETTER_EDT = None

        # Vider les données en base de la dernière génération
        db = Database.get("edt_generator")
        sql = """
            DELETE FROM PHEROMONES
        """
        db.run(sql)
        sql = """
            DELETE FROM COURS
        """
        db.run(sql)
        db.close()

    @staticmethod
    async def generate_edts(nb_ants=50, nb_iterations=1):
        EDT_GENERATOR.init()
        EDT.set_course_probability()
        db = Database.get("edt_generator")
        
        EDT_GENERATOR.PARAM_SAVE['PHEROMONE_FUNC'] = EDT_GENERATOR.PHEROMONE_FUNC
        batch_size = 6 # Décroissant sur le temps; taille du premier batch

        last_best_score = 0
        nb_same_best_score = 0
        for iteration in range(nb_iterations):
            print(f"\nITERATION {iteration + 1}/{nb_iterations}")
            f = open('log.txt', 'a')
            f.write(f"\nITERATION {iteration + 1}/{nb_iterations}\n")
            debut_g = datetime.datetime.now()
            dV = (nb_iterations - iteration) / nb_iterations - 0.05
            dP = (iteration + 1) / nb_iterations
            dP *= 2
            dV *= 2
            print(f"  |_dP={dP}, dV={dV}")
            f.write(f"  |_dP={dP}, dV={dV}\n")
            f.close()

            nb_ants_current = nb_ants
            nb_decrease = batch_size
            decrease_factor:int = 1

            # Créer les fourmis
            all_ants = []
            while nb_ants_current > 0:
                if nb_ants_current - nb_decrease < 0:
                    nb_decrease = nb_ants_current
                
                all_ants.append([Ant(dP=dP, dV=dV) for _ in range(nb_decrease)])

                nb_ants_current -= nb_decrease
                if nb_decrease > 1 + decrease_factor:
                    nb_decrease -= decrease_factor

            # Initialiser les données de phéromones
            sql = """
                SELECT c.COURS, c.JOUR, c.DEBUT, AVG(p.PHEROMONE) as p
                FROM PHEROMONES p
                    JOIN COURS c ON p.ID_COURS = c.ID
                GROUP BY c.COURS, c.JOUR, c.DEBUT
            """
            
            if EDT_GENERATOR.PHEROMONE_FUNC == 'mean':
                sql = """
                    SELECT c.COURS, c.JOUR, c.DEBUT, AVG(p.PHEROMONE) as p
                    FROM PHEROMONES p
                            JOIN COURS c ON p.ID_COURS = c.ID
                    WHERE c.COURS IS NOT NULL AND c.JOUR IS NOT NULL AND c.DEBUT IS NOT NULL
                    GROUP BY c.COURS, c.JOUR, c.DEBUT
                """
            elif EDT_GENERATOR.PHEROMONE_FUNC == 'max':
                sql = """
                    SELECT c.COURS, c.JOUR, c.DEBUT, MAX(p.PHEROMONE) as p
                    FROM PHEROMONES p
                            JOIN COURS c ON p.ID_COURS = c.ID
                    WHERE c.COURS IS NOT NULL AND c.JOUR IS NOT NULL AND c.DEBUT IS NOT NULL
                    GROUP BY c.COURS, c.JOUR, c.DEBUT
                """
            elif EDT_GENERATOR.PHEROMONE_FUNC == 'min':
                sql = """
                    SELECT c.COURS, c.JOUR, c.DEBUT, MIN(p.PHEROMONE) as p
                    FROM PHEROMONES p
                            JOIN COURS c ON p.ID_COURS = c.ID
                    WHERE c.COURS IS NOT NULL AND c.JOUR IS NOT NULL AND c.DEBUT IS NOT NULL
                    GROUP BY c.COURS, c.JOUR, c.DEBUT
                """
            pheromones = db.run(sql).fetch()
            EDT_GENERATOR.LEARNING_TABLE = {(course['COURS'], course['JOUR'], course['DEBUT']): (course['p'] or 0) for course in pheromones}
            
            # Générer les EDTs
            loop = asyncio.get_event_loop()
            tasks = [loop.create_task(EDT_GENERATOR.visit_batch_of_ants(ants)) for ants in all_ants]
            Ants = await asyncio.gather(*tasks)
            
            # Learning
            sql_insert = """
                INSERT INTO PHEROMONES (ID_COURS, PHEROMONE, BOOSTED) VALUES (%s, %s, 0)
            """
            sql_select = """
                SELECT ID FROM COURS WHERE COURS = %s AND JOUR = %s AND DEBUT = %s
            """

            sql_insert_cours = """
                INSERT INTO COURS (COURS, JOUR, DEBUT) VALUES (%s, %s, %s)
            """
            nb_ants = 0
            for ants_list in all_ants:
                for ant in ants_list:
                    nb_ants += 1
                    score = ant.edt.get_score()
                    for node in ant.node_history:
                        cours = db.run([sql_select, (node[0], node[1], node[2])]).fetch(first=True)
                        if cours:
                            db.run([sql_insert, (cours['ID'], score)])
                        else:
                            db.run([sql_insert_cours, (node[0], node[1], node[2])])
                            cours = db.last_id()
                            db.run([sql_insert, (cours, score)])

            f = open('log.txt', 'a')
            f.write(f"  |_Nombre de fourmis: {nb_ants}\n")
            print("  |_Meilleur score:", EDT_GENERATOR.BETTER_EDT_SCORE)
            f.write(f"  |_Meilleur score: {EDT_GENERATOR.BETTER_EDT_SCORE}\n")
            print(f"  |_Temps d'execution: {datetime.datetime.now() - debut_g}")
            f.write(f"  |_Temps d'execution: {datetime.datetime.now() - debut_g}\n")
            f.close()

            if ant.edt.get_score() == last_best_score:
                nb_same_best_score += 1

                if nb_same_best_score == 3:
                    # Lecture par borne supérieure
                    EDT_GENERATOR.PARAM_SAVE['PHEROMONE_FUNC'] = EDT_GENERATOR.PHEROMONE_FUNC
                    EDT_GENERATOR.PHEROMONE_FUNC = 'max'
                    print('  |_Start-Pheromone-Up')
                
                elif nb_same_best_score == 5:
                    # Explorer d'autres possibilités
                    EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF'] = EDT_GENERATOR.DIVERSITY_COEF
                    EDT_GENERATOR.DIVERSITY_COEF = 0.1
                    EDT_GENERATOR.RELEARNING = True
                    print('  |_Relearning')

            else:
                if nb_same_best_score == 3:
                    # Fin du renforcement de la phéromone
                    EDT_GENERATOR.PHEROMONE_FUNC = EDT_GENERATOR.PARAM_SAVE['PHEROMONE_FUNC']
                    print('  |_Stop-Pheromone-Up')
                
                elif nb_same_best_score >= 5:
                    # Fin de la diminution de la diversité
                    EDT_GENERATOR.PHEROMONE_FUNC = EDT_GENERATOR.PARAM_SAVE['PHEROMONE_FUNC']
                    EDT_GENERATOR.DIVERSITY_COEF = EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF']
                    print('  |_Stop-Diversity-Decrease AND Stop-Relearning')

                nb_same_best_score = 0
                last_best_score = ant.edt.get_score()
                if EDT_GENERATOR.RELEARNING:
                    EDT_GENERATOR.RELEARNING = False
                    print('  |_Stop-Relearning')

        db.close()
        return Ants

    @staticmethod
    def get_pheromone_probability(node, db:Database, pheromone_func=None):
        if pheromone_func is None:
            pheromone_func = EDT_GENERATOR.PHEROMONE_FUNC

        if pheromone_func == 'better':
            sql = """
                SELECT MAX(p.PHEROMONE) as p
                FROM PHEROMONES p
                     JOIN COURS c ON p.ID_COURS = c.ID
                WHERE c.COURS = %s AND c.JOUR = %s AND c.DEBUT = %s AND BOOSTED = 0
            """
            return db.run([sql, (node[0], node[1], node[2])]).fetch(first=True)['p'] or 0
        
        if pheromone_func == 'mean':
            sql = """
                SELECT AVG(p.PHEROMONE) as p
                FROM PHEROMONES p
                     JOIN COURS c ON p.ID_COURS = c.ID
                WHERE c.COURS = %s AND c.JOUR = %s AND c.DEBUT = %s
            """
        elif pheromone_func == 'max':
            sql = """
                SELECT MAX(p.PHEROMONE) as p
                FROM PHEROMONES p
                     JOIN COURS c ON p.ID_COURS = c.ID
                WHERE c.COURS = %s AND c.JOUR = %s AND c.DEBUT = %s
            """
        elif pheromone_func == 'min':
            sql = """
                SELECT MIN(p.PHEROMONE) as p
                FROM PHEROMONES p
                     JOIN COURS c ON p.ID_COURS = c.ID
                WHERE c.COURS = %s AND c.JOUR = %s AND c.DEBUT = %s
            """
        else:
            raise Exception("PHEROMONE_FUNC doit être 'mean', 'max' ou 'min'")
        
        return db.run([sql, (node[0], node[1], node[2])]).fetch(first=True)['p'] or 0
    
    @staticmethod
    def get_visibility_probability(node, course, edt:EDT):
        damages = {'nb_damages': 0, 'nb_criticals_damages': 0}
        
        if course not in edt.COURSE_DAMAGES[node[1]]:
            return 0

        # Récupérer la liste des dégats du cours
        all_damages = edt.COURSE_DAMAGES[node[1]][course][node[2]]

        for other_course in all_damages:
            if other_course not in edt.COURSE_DAMAGES[node[1]]: continue
            all_slots_for_other_course = list(edt.COURSE_DAMAGES[node[1]][other_course].keys())
            damaged_slots_for_other_course = [slot for slot in all_slots_for_other_course if node[2] <= slot <= node[2] + course.duree * 2]
            damages['nb_damages'] += len(damaged_slots_for_other_course)
            damages['nb_criticals_damages'] += len(all_slots_for_other_course) == len(damaged_slots_for_other_course)

        return damages['nb_damages'] + damages['nb_criticals_damages'] * EDT_GENERATOR.CRITICAL_DAMAGES_COEF # Il faut inverser les probabilités mais on a besoin de connaitre le max pour normaliser

    @staticmethod
    async def visit_batch_of_ants(ants, dP=0.5, dV=0.5):
        db = Database.get("edt_generator")
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(EDT_GENERATOR.run_ant2(ant, db)) for ant in ants]
        await asyncio.gather(*tasks)
        db.close()
        del tasks
        del loop

    @staticmethod
    async def run_ant2(ant, db:Database):
        debut = datetime.datetime.now()
        await ant.visit(db)

        sql_insert = """
            INSERT INTO EDT_SIGNATURES VALUES (%s, 1) ON DUPLICATE KEY UPDATE NOMBRE = NOMBRE + 1;
        """
        db.run([sql_insert, (ant.edt.get_signature(), )])

        f = open('log.txt', 'a')
        print(f"  |_Temps de visite: {datetime.datetime.now() - debut}")
        f.write(f"  |_Temps de visite: {datetime.datetime.now() - debut}\n")
        f.close()
