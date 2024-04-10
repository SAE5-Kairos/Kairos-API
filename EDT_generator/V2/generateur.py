import datetime, multiprocessing, random, asyncio
from typing import Union
from EDT_generator.V2.cours2 import Cours2
from EDT_generator.V2.edt2 import EDT2
from Kairos_API.database import Database

best_score = multiprocessing.Value('d', 0)
global_var_lock = multiprocessing.Lock()

data_manager = multiprocessing.Manager()
best_edt = data_manager.list()

class Manager:
    NB_WORKERS = 15
    COEF_GAMMA_OVER_EPSILON = 0.95
    PROFONDEUR_VOISINAGE = 3
    NB_VOISINS = 3

    def __init__(self, data) -> None:
        self.data = data
            
    async def start(self, gamma, epsilon):
        loop = asyncio.get_event_loop()
        debut = datetime.datetime.now()

        try:
            workers = [Worker(gamma, epsilon, self.data['on_max'] if index % 2 == 0 else self.data['on_avg']) for index in range(self.NB_WORKERS)]
            tasks = [loop.create_task(worker.run()) for worker in workers]
            result = await asyncio.gather(*tasks)
        except Exception as e:
            print("Lors des workers:", e)
            return False

        if not all(result) or len(result) != len(tasks):
            print("Un Worker a rencontré une erreur")
            return False

        try:
            db = Database.get("edt_generator")
            all_inserts = []
            for worker in workers:
                all_inserts.extend(worker.global_pheromones_inserts)
            
            global_pheromones_inserts = [val for insert in all_inserts for val in insert]
            sql_insert_pheromone = """
                INSERT INTO PHEROMONES2 (ID_ASSOCIATION, PHEROMONE, FROM_SUPER_WORKER) VALUES 
            """
            sql = sql_insert_pheromone + ', '.join("(%s, %s, %s)" for _ in range(int(len(global_pheromones_inserts) / 3))) + ";"
            db.run([sql, global_pheromones_inserts])
        except Exception as e:
            print("Lors de l'insertion des phéromones:", e)
            return False

        print(f"Un Manager a fini de faire travailler ses {Manager.NB_WORKERS} workers en {datetime.datetime.now() - debut}")
        return True
    
    def run(self, gamma, epsilon):
        try: return asyncio.run(self.start(gamma, epsilon))
        except Exception as e:
            print("Manager:", e)
        
        return False


class Worker:

    def __init__(self, gamma, epsilon, data) -> None:
        self.edt = EDT2()
        self.gamma = gamma      # Coefficient d'exploration
        self.epsilon = epsilon  # Coefficient de phéromones

        self.omega = data[0].copy()      # Univers des possibilitées
        self.available_slots: 'dict[int, list]' = data[1].copy() # Dictionnaire des slots pour amélioration par voisinage

        self.global_pheromones_inserts: 'list[tuple]' = []

    async def run(self):
        while True:
            node = self.choose_node()
            if node is None:
                break
            try:
                self.edt.add_cours(node['COURS'], node['JOUR'], node['HEURE'])
                self.rm_from_omega(node['JOUR'], node['HEURE'], node['COURS'].duree, node['COURS'])
            except Exception as e:
                print("Worker running:", e)
                break

        # Sauvegarder les Phéromones
        for _ in range(Manager.PROFONDEUR_VOISINAGE):
            try: self.upgrade_edt_with_local_search()
            except Exception as e: print("Worker local search:", e)
        score = self.edt.get_score()

        for cours in self.edt.cours:
            assoc_id = cours.get_association()
            self.global_pheromones_inserts.append((assoc_id, score, 0))

        if score > best_score.value:
            with global_var_lock:
                if score > best_score.value:
                    best_score.value = score
                    best_edt[:] = self.edt.cours

        return True

    def choose_node(self):
        """
        Renvoi un noeud en fonction de la probabilité de chaque noeud (ou None si aucun noeud n'a été choisi)
        Noeud = { 'ID': int, 'COURS': Cours2, 'JOUR': int, 'HEURE': int, 'PERCENT_CRENEAUX': float, 'PHEROMONE': float }
        :return: None si aucun noeud n'a été choisi
        """
        if not self.omega:
            return None
        
        P = []
        max_pheromone = 0
        for node in self.omega:
            if node['PHEROMONE'] > max_pheromone:
                max_pheromone = node['PHEROMONE']
            P.append(self.gamma * node['PERCENT_CRENEAUX'] + self.epsilon * (node['PHEROMONE']**2 / 100**2))

        # P0: Arrêt de l'algorithme s'il ne semble pas y avoir mieux
        # if max_pheromone * self.epsilon < self.edt.get_score() * self.gamma:
        #     return None
        
        # Soit P les probabilités de chaque noeud; choisir un noeud aléatoire en fonction de P
        total = sum(P)
        choosen_proba = random.uniform(0, total)

        current_proba = 0
        for index, proba in enumerate(P):
            current_proba += proba
            if choosen_proba <= current_proba:
                return self.omega[index]
        raise Exception("Aucun noeud n'a été choisi")

    def rm_from_omega(self, jour, heure, duree=0, cours=None):
        self.new_omega = []
        heures = [heure + i for i in range(duree)]
        for node in self.omega:
            if node['JOUR'] == jour:
                heures_node = [node['HEURE'] + i for i in range(node['COURS'].duree)]
                if any([heure in heures_node for heure in heures]):
                    continue
            if cours is not None and node['COURS'] == cours:
                continue
            
            self.new_omega.append(node)
        self.omega = self.new_omega

        # On mets à jour les slots disponibles sans retirer le cours (pour amélioration par voisinage)
        for other_cours_id in self.available_slots:
            slots = []

            for slot in self.available_slots[other_cours_id]:
                if slot['JOUR'] != jour:
                    slots.append(slot)
                    continue

                slot_hours = [slot['HEURE'] + i for i in range(slot['COURS'].duree)]
                if any([heure in slot_hours for heure in heures]):
                    continue
                slots.append(slot)
            self.available_slots[other_cours_id] = slots.copy()

    def upgrade_edt_with_local_search(self):
        midi_dispo = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        starting_slots = [index for index, value in enumerate(midi_dispo) if value == 1]

        # Focer la pose des heures du midi
        for cours in Cours2.ALL:
            if cours.type_cours == "Midi" and cours not in self.edt.cours:
                
                # Retirer un cours pour placer le cours du midi
                for critical_cours in self.edt.cours:
                    if critical_cours.jour != cours.jour or critical_cours.type_cours == "Midi": continue
                    
                    # Si le cours bloque le midi
                    if any([heure in midi_dispo for heure in range(critical_cours.heure, critical_cours.heure + critical_cours.duree)]):
                        self.edt.remove_cours(critical_cours)
                    
                    slot_to_place = None
                    # Si on le peux, on place le cours du midi
                    for starting_slot in starting_slots:
                        if self.edt.is_free(cours.jour, starting_slot, cours) == 1:
                            slot_to_place = starting_slot
                            break
                    
                    if slot_to_place is not None:
                        try:self.edt.add_cours(cours, cours.jour, slot_to_place)
                        except Exception as e: print("wtf ====>", e)
                        self.rm_from_omega(cours.jour, slot_to_place, cours.duree, cours)
                        break
        
        node = self.choose_node()
        while node is not None:
            try:
                self.edt.add_cours(node['COURS'], node['JOUR'], node['HEURE'])
                self.rm_from_omega(node['JOUR'], node['HEURE'], node['COURS'].duree, node['COURS'])
            except Exception as e:
                print("Worker running:", e)
                break

            node = self.choose_node()

        # Essayer de retirer les heures du samedi
        for samedi_cours in self.edt.cours.copy():
            if samedi_cours.jour == 5:
                self.edt.remove_cours(samedi_cours)

                best_day = None
                best_hour = None
                max_score = 0
                # Essayer toutes les autres places possibles et récupérer la meilleure
                for slot in self.available_slots[samedi_cours.id]:
                    if slot['JOUR'] == 5: continue
                    if self.edt.is_free(slot['JOUR'], slot['HEURE'], samedi_cours) != 1: continue
                    self.edt.add_cours(samedi_cours, slot['JOUR'], slot['HEURE'])
                    
                    new_score = self.edt.get_score()
                    if new_score > max_score:
                        max_score = new_score
                        best_day = slot['JOUR']
                        best_hour = slot['HEURE']
                    
                    tmp_cours: Cours2 = samedi_cours.copy()
                    tmp_cours.jour = slot['JOUR']
                    tmp_cours.heure = slot['HEURE']
                    self.edt.remove_cours(tmp_cours)
                
                if best_day is not None:
                    self.edt.add_cours(samedi_cours, best_day, best_hour)
                    self.rm_from_omega(best_day, best_hour, samedi_cours.duree, samedi_cours)
                else:
                    self.edt.add_cours(samedi_cours, 5, samedi_cours.heure)

        score = self.edt.get_score()

        # Sauvegarder les Phéromones
        for cours in self.edt.cours:
            assoc_id = cours.get_association()
            self.global_pheromones_inserts.append((assoc_id, score, 0))

        for cours in self.edt.cours.copy():
            if not cours or cours.id not in self.available_slots or not self.available_slots[cours.id]:
                continue

            # 1. Libérer le slots pour essayer des nouvelles associations
            self.edt.remove_cours(cours)
            best_assocs = []

            # Récupérer les associations à tester
            voisins = []
            
            # Ajouter les 2 voisins minimum (1 avant et 1 après)
            voisin_before = None
            voisin_after = None
            for assoc in self.available_slots[cours.id]:
                if assoc['JOUR'] == cours.jour:
                    if assoc['HEURE'] < cours.heure and (voisin_before is None or assoc['HEURE'] > voisin_before['HEURE']):
                        voisin_before = assoc
                    if assoc['HEURE'] > cours.heure and (voisin_after is None or assoc['HEURE'] < voisin_after['HEURE']):
                        voisin_after = assoc

            # Ajouter des voisins aléatoirement
            for _ in range(Manager.NB_VOISINS):
                voisin = random.choice(self.available_slots[cours.id])
                voisins.append(voisin)

            if voisin_before is not None:
                voisins.append(voisin_before)

            if voisin_after is not None:
                voisins.append(voisin_after)

            # Ajouter les voisins
            for voisin in voisins:
                # 1. Ajouter le cours à l'association
                try: self.edt.add_cours(cours, voisin['JOUR'], voisin['HEURE'])
                except Exception as e: print("X; Upgrade EDT:", e)

                # 2. Essayer de placer tous les cours non placé sur le jour libéré
                new_assocs = []
                for other_cours_id in self.available_slots:
                    if other_cours_id == cours.id: continue
                    if other_cours_id in self.edt.cours: continue

                    for slot in self.available_slots[other_cours_id]:
                        if slot['JOUR'] != cours.jour: continue
                        try:
                            self.edt.add_cours(slot['COURS'], slot['JOUR'], slot['HEURE'])
                            new_assocs.append(slot)
                        except: pass

                # 3. Vérifier si la nouvelle association est meilleure
                new_score = self.edt.get_score()
                if new_score >= score:
                    score = new_score
                    best_assocs = new_assocs.copy()
                    best_assocs.append(voisin)

                # 4. Enregister les Phéromones des nouvelles associations
                # 5. Retirer les nouvelles associations
                for new_assoc in new_assocs:
                    self.global_pheromones_inserts.append((new_assoc['ID'], new_score, 1))
                    tmp_cours: Cours2 = new_assoc['COURS'].copy()
                    tmp_cours.jour = new_assoc['JOUR']
                    tmp_cours.heure = new_assoc['HEURE']
                    self.edt.remove_cours(tmp_cours)

                # 6. Retirer le cours ajouté
                self.global_pheromones_inserts.append((voisin['ID'], new_score, 1))
                main_cours = cours.copy()
                main_cours.jour = voisin['JOUR']
                main_cours.heure = voisin['HEURE']
                self.edt.remove_cours(main_cours)

            # 7. Ajouter la meilleure association
            if len(best_assocs) > 0 and score >= best_score.value:
                for best_assoc in best_assocs:
                    self.edt.add_cours(cours, best_assoc['JOUR'], best_assoc['HEURE'])
                    self.rm_from_omega(best_assoc['JOUR'], best_assoc['HEURE'], best_assoc['COURS'].duree, best_assoc['COURS'])
                
                # 8. Update best_score & best_edt
                with global_var_lock:
                    if score > best_score.value:
                        best_score.value = score
                        best_edt[:] = self.edt.cours
            else:
                self.edt.add_cours(cours, cours.jour, cours.heure)
                
       
def generate():
    num_cores = multiprocessing.cpu_count()
    print("Nombre de coeurs:", num_cores)
    total_workers = len(Cours2.ALL) * 25
    total_managers = total_workers // Manager.NB_WORKERS
    total_iterations = total_managers // num_cores + 1

    best_score.value = 0
    best_edt[:] = []

    db = Database.get("edt_generator")

    for index_iteration in range(total_iterations):
        if best_score.value == 100:
            print("===> Meilleur score trouvé")
            break
        results = []

        data = get_worker_data(db)

        print(f"Iteration {index_iteration + 1} / {total_iterations}")
        gamma = index_iteration / total_iterations
        epsilon = 1 - gamma

        with multiprocessing.Pool(num_cores) as pool:
            print(f"===> Lancement des {num_cores} Managers")
            # Multi-processing ####################################################################################
            for __ in range(num_cores):
                # On veut créer un manager par core soit num_cores
                results.append(pool.apply_async(Manager(data).run, (gamma, epsilon)))

            pool.close()
            pool.join()

        # Récupérer les résultats des tâches
        results = [result.get() for result in results]

        print(f"===> {num_cores * Manager.NB_WORKERS} workers ont fini de travailler")
        print(f"===> Meilleur score: {best_score.value}")

    edt = EDT2(_from_cours=best_edt)
    db.close()
    print(f"===> {Manager.NB_WORKERS * num_cores * total_iterations} workers ont fini de travailler")
    print(f"===> Meilleur score: {edt.get_score()}")
    return edt

def get_worker_data(db:Database, aggreg_func=None):
    """
    Récupère les données pour les workers
    
    :param aggreg_func: Fonction d'aggrégation des phéromones (MAX ou AVG ou None pour les deux)
    :return: Dictionnaire des données contenant les valeurs pour MAX et AVG OU un tuple quand aggreg_func est spécifié
    """
    # Initialisation des données ########################################################################
    available_slots_on_max: 'dict[int, list]' = {} # Dictionnaire des slots pour amélioration par voisinage
    available_slots_on_avg: 'dict[int, list]' = {} # Dictionnaire des slots pour amélioration par voisinage
    omega_on_max = [] # Univers des possibilitées
    omega_on_avg = [] # Univers des possibilitées

    # Récupérer les données de la base de données #######################################################
    min_pheromone = db.run("SELECT IFNULL(AVG(PHEROMONE), 0) AS 'P' FROM PHEROMONES2;").fetch(first=True)['P'] * Manager.COEF_GAMMA_OVER_EPSILON
    
    sql_agglo_on_max = f"""
        SELECT ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX, MAX(IFNULL(PHEROMONE, {min_pheromone})) AS PHEROMONE
        FROM ALL_ASSOCIATIONS
            LEFT JOIN PHEROMONES2 ON ID = ID_ASSOCIATION
        GROUP BY ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX;
    """
    sql_agglo_on_avg = f"""
        SELECT ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX, AVG(IFNULL(PHEROMONE, {min_pheromone})) AS PHEROMONE
        FROM ALL_ASSOCIATIONS
            LEFT JOIN PHEROMONES2 ON ID = ID_ASSOCIATION
        GROUP BY ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX;
    """
    
    max_creneaux = db.run("SELECT MAX(NB_CRENEAUX) AS MAX FROM ALL_ASSOCIATIONS").fetch(first=True)['MAX']
    
    # Mise en forme des données ##########################################################################
    def format_data(data):
        omega = []
        available_slots = {}

        for node in data:
            cours = Cours2.get(node['ID_COURS'])
            omega_node = {
                'ID': node['ID'], 'COURS': cours, 
                'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 
                'PERCENT_CRENEAUX': 1 - (node['NB_CRENEAUX'] / max_creneaux), 
                'PHEROMONE': node['PHEROMONE']
            }
            omega.append(omega_node)

            if cours.id not in available_slots:
                available_slots[cours.id] = []
            available_slots[cours.id].append({'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 'ID': node['ID'], 'COURS': cours})
        return omega, available_slots

    if aggreg_func == 'MAX' or aggreg_func is None: omega_on_max, available_slots_on_max = format_data(db.run(sql_agglo_on_max).fetch())
    if aggreg_func == 'AVG' or aggreg_func is None: omega_on_avg, available_slots_on_avg = format_data(db.run(sql_agglo_on_avg).fetch())

    if aggreg_func == 'MAX': return omega_on_max, available_slots_on_max
    if aggreg_func == 'AVG': return omega_on_avg, available_slots_on_avg
    return {'on_max': (omega_on_max, available_slots_on_max), 'on_avg': (omega_on_avg, available_slots_on_avg)}