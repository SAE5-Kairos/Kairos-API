import random, asyncio, datetime, gc
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
        
        self.CPY_CREATED_EDT = EDT_GENERATOR.CREATED_EDT.copy()

    def choose_next_node(self, get_better=False):
        """
            Node: (cours.name, cours.jour, cours.debut)

            P -> probabilité de choisir un noeud en fonction de la phéromone
            V -> probabilité de choisir un noeud en fonction de la visibilité

            P * V = probabilité de choisir un noeud en fonction de la phéromone et de la visibilité
            (P * V) / somme(P * V) = probabilité de choisir un noeud en fonction de la phéromone et de la visibilité normalisée
        """
        
        # On récupère les cours disponibles
        available_courses:list(Cours) = [course for course in self.edt.COURS if course not in self.edt.placed_cours]
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
                        P[(course.name, jour, heure)] = EDT_GENERATOR.get_pheromone_probability((course.name, jour, heure), 'better' if get_better else None)

                        # On récupère la probabilité de choisir ce cours en fonction de la visibilité
                        V[(course.name, jour, heure)] = EDT_GENERATOR.get_visibility_probability((course.name, jour, heure), course, self.edt)

        if get_better:
            better_node = max(P, key=lambda elmt: P[elmt])
            print(P[better_node])
            
            if self.focused_score is None:
                self.focused_score = P[better_node]
                return better_node
            
            elif P[better_node] >= self.focused_score:
                return better_node
            
            return None
        
        if EDT_GENERATOR.RELEARNING:
            return list(V.keys())[random.randint(0, len(V) - 1)]

        max_V = max(V.values()) if V else 0
        if max_V != 0:
            for node in V:
                V[node] = (max_V - V[node]) * 100 / max_V
        node_probabilities = {}

        signature = self.edt.get_signature() # On récupère la signature de l'EDT actuel
        total_nb_edt_with_same_signature = 0
        nb_other_signature = 0
        same_signature_calculed = False
        
        # On calcule la probabilité de choisir un cours en fonction de la phéromone et de la visibilité
        for node in P:
            furtur_signature = signature + f"{node[0]}-{node[1]}-{node[2]}/" # On calcule la signature de l'EDT si on place le cours
            times_furtur_signature = 0
            
            # On compare la signature actuel + le cours afin de voir le nombre de fois qu'il a été choisi
            for other_signature in self.CPY_CREATED_EDT:
                
                if other_signature.startswith(signature):
                    if other_signature.startswith(furtur_signature):
                        times_furtur_signature += self.CPY_CREATED_EDT[other_signature]

                    if not same_signature_calculed: # On calcule le nombre d'EDT avec la même signature que l'EDT actuel
                        total_nb_edt_with_same_signature += self.CPY_CREATED_EDT[other_signature]
                        nb_other_signature += 1
            same_signature_calculed = True

            # On calcule le facteur de diversité
            if total_nb_edt_with_same_signature != 0 and times_furtur_signature * (1 + EDT_GENERATOR.DIVERSITY_COEF) > total_nb_edt_with_same_signature and not get_better:
                diversity_factor = EDT_GENERATOR.DIVERSITY_COEF
            else:
                diversity_factor = 1

            node_probabilities[node] = (self.dP * P[node] * EDT_GENERATOR.PHEROMONE_BOOST + self.dV * V[node]) * diversity_factor

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

    async def visit(self, get_better=False):
        node = self.choose_next_node(get_better=get_better)
        while node is not None:
            before_score = self.edt.get_score()

            self.node_history.append(node)
            cours = Cours.get_course_by_name(self.node_history[-1][0])
            self.edt.place_cours(cours, self.node_history[-1][1], self.node_history[-1][2])

            # On calcule le score après avoir placé le cours et on l'ajoute à la liste des phéromones
            if node in EDT_GENERATOR.LEARNING_TABLE:
                variation_score = self.edt.get_score() - before_score
                
                scores = [float(score) for score in EDT_GENERATOR.LEARNING_TABLE[node]]
                moy_score = sum(scores) / len(scores)

                score = str(moy_score + variation_score)
                await EDT_GENERATOR.update_learning_table(node, score)

            # Update CREATED_EDT (pour la diversité) selon la signature de l'EDT
            # On cherche a limiter la taille du dico des possibilités pour ne pas faire exploser la mémoire et le temps d'execution
            signature = self.edt.get_signature()
            for other_signature in self.CPY_CREATED_EDT.copy():
                if not other_signature.startswith(signature):
                    del self.CPY_CREATED_EDT[other_signature]
        
            node = self.choose_next_node(get_better=get_better)

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

    @classmethod
    async def update_learning_table(cls, key, value):
        async with cls.LEARNING_TABLE_LOCK:            
            # Si la valeur moyenne est inférieure à la valeur actuelle, on l'ajoute à la liste
            cls.LEARNING_TABLE[key].append(value)

                # Retirer les valeurs trop faibles
                # avg = sum(cls.LEARNING_TABLE[key]) / len(cls.LEARNING_TABLE[key])
                # cls.LEARNING_TABLE[key] = [val for val in cls.LEARNING_TABLE[key] if val >= avg]

    @classmethod
    async def update_learning_table_list(cls, list_of_key, value):
        async with cls.LEARNING_TABLE_LOCK:
            for key in list_of_key:
                cls.LEARNING_TABLE: cls.LEARNING_TABLE[key].append(value)

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
        EDT_GENERATOR.CREATED_EDT_LOCK = asyncio.Lock()

    @staticmethod
    async def generate_edts(nb_ants=50, nb_iterations=1):
        EDT_GENERATOR.init()
        EDT.set_course_probability()
        
        EDT_GENERATOR.PARAM_SAVE['PHEROMONE_FUNC'] = EDT_GENERATOR.PHEROMONE_FUNC
        batch_size = 10

        last_best_score = 0
        nb_same_best_score = 0
        for iteration in range(nb_iterations):
            print(f"\nITERATION {iteration + 1}/{nb_iterations}")
            debut = datetime.datetime.now()
            dV = (nb_iterations - iteration) / nb_iterations - 0.05
            dP = (iteration + 1) / nb_iterations
            dP *= 2
            dV *= 2
            print(f"  |_dP={dP}, dV={dV}")
            
            all_ants = [[Ant(dP=dP, dV=dV) for _ in range(batch_size)] for _ in range(nb_ants // batch_size)]
            if nb_ants % batch_size != 0:
                all_ants.append([Ant(dP=dP, dV=dV) for _ in range(nb_ants % batch_size)])

            loop = asyncio.get_event_loop()
            tasks = [loop.create_task(EDT_GENERATOR.visit_batch_of_ants(ants)) for ants in all_ants]
            Ants = await asyncio.gather(*tasks)
            
            # Learning
            node_to_scores = {}
            for ants_list in all_ants:
                for ant in ants_list:
                    score = ant.edt.get_score()
                    for node in ant.node_history:
                        if node in node_to_scores:
                            node_to_scores[node].append(score)
                        else: node_to_scores[node] = [score]

            for node in node_to_scores:
                if node in EDT_GENERATOR.LEARNING_TABLE:
                    EDT_GENERATOR.LEARNING_TABLE[node].extend(node_to_scores[node])
                else: EDT_GENERATOR.LEARNING_TABLE[node] = node_to_scores[node].copy()

            #batch_visit = [asyncio.create_task(EDT_GENERATOR.visit_batch_of_ants(ants=ants, dP=dP, dV=dV)) for ants in all_ants]
            #Ants = await asyncio.gather(*batch_visit)
            ant = Ant(1, 0)
            ant = await ant.visit(get_better=True)
            print("  |_Meilleur score:", ant.edt.get_score())
            print(f"  |_Temps d'execution: {datetime.datetime.now() - debut}") 
            
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


                # elif nb_same_best_score == 3:
                #     # Diminution de la diversité
                #     EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF'] = EDT_GENERATOR.DIVERSITY_COEF
                #     EDT_GENERATOR.DIVERSITY_COEF = 0
                #     print('  |_Start-Diversity-Decrease')

                # elif nb_same_best_score == 5:
                #     # Phase de relearning
                #     EDT_GENERATOR.RELEARNING = True
                #     EDT_GENERATOR.DIVERSITY_COEF = 0.6
                #     EDT_GENERATOR.PHEROMONE_BOOST = 1
                #     print('  |_Start-Relearning [Start-Diversity-increase, Stop-Pheromone-Boost]')

                # elif nb_same_best_score == 7:
                #     # Fin de la phase de relearning
                #     EDT_GENERATOR.RELEARNING = False
                #     EDT_GENERATOR.DIVERSITY_COEF = EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF']
                #     EDT_GENERATOR.PHEROMONE_BOOST = EDT_GENERATOR.PARAM_SAVE['PHEROMONE_BOOST']
                #     print('  |_Stop-Relearning')
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
                # elif nb_same_best_score == 3:
                #     # Fin de la diminution de la diversité
                #     EDT_GENERATOR.DIVERSITY_COEF = EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF']
                #     del EDT_GENERATOR.PARAM_SAVE['DIVERSITY_COEF']
                #     print('  |_Stop-Diversity-Decrease AND Stop-Pheromone-Boost')

                nb_same_best_score = 0
                last_best_score = ant.edt.get_score()
                if EDT_GENERATOR.RELEARNING:
                    EDT_GENERATOR.RELEARNING = False
                    print('  |_Stop-Relearning')
            
        return Ants

    @staticmethod
    def get_pheromone_probability(node, pheromone_func=None):
        if (node not in EDT_GENERATOR.LEARNING_TABLE):
            return 0
    
        if pheromone_func is None:
            pheromone_func = EDT_GENERATOR.PHEROMONE_FUNC

        if pheromone_func != 'better':
            scores = [float(score) for score in EDT_GENERATOR.LEARNING_TABLE[node]]
        else:
            return max([score for score in EDT_GENERATOR.LEARNING_TABLE[node] if type(score) == float])
        
        if pheromone_func == 'mean':
            moy = sum(scores) / len(scores)
        elif pheromone_func == 'max':
            moy = max(scores)
        elif pheromone_func == 'min':
            moy = min(scores)
        else:
            raise Exception("PHEROMONE_FUNC doit être 'mean', 'max' ou 'min'")
        return moy
    
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
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(EDT_GENERATOR.run_ant2(ant)) for ant in ants]
        await asyncio.gather(*tasks)

        del tasks
        del loop
        # for ant in ants:
        #     ant.visit()
            
        #     score = ant.edt.get_score()
        #     for node in ant.node_history:
        #         # if node in EDT_GENERATOR.LEARNING_TABLE:
        #         #     EDT_GENERATOR.LEARNING_TABLE[node].append(score)
        #         # else:
        #         #     EDT_GENERATOR.LEARNING_TABLE[node] = [score]
        #         await EDT_GENERATOR.update_learning_table(node, score)

    @staticmethod
    async def run_ant2(ant):
        await ant.visit()
        #await ant.learn()
        await EDT_GENERATOR.update_created_edt(ant.edt.get_signature())
        # score = ant.edt.get_score()
        # for node in ant.node_history:
        #     await EDT_GENERATOR.update_learning_table(node, score)
