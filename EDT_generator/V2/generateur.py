import datetime, multiprocessing, random, asyncio, math
from EDT_generator.V2.cours2 import Cours2
from EDT_generator.V2.edt2 import EDT2
from Kairos_API.database import Database

best_score = multiprocessing.Value('d', 0)
best_score_lock = multiprocessing.Lock()

data_manager = multiprocessing.Manager()
best_edt = data_manager.list()
best_edt_lock = multiprocessing.Lock()

class Manager:
    NB_WORKERS = 30
    COEF_GAMMA_OVER_EPSILON = 0.95

    async def start(self, gamma, epsilon):
        loop = asyncio.get_event_loop()
        debut = datetime.datetime.now()

        try:
            workers = [Worker(gamma, epsilon, 'MAX' if index % 2 == 0 else 'AVG') for index in range(self.NB_WORKERS)]
            tasks = [loop.create_task(worker.run()) for worker in workers]
            result = await asyncio.gather(*tasks)
        except Exception as e:
            print("Lors des workers:", e)
            return False

        if not all(result) or len(result) != len(tasks):
            print("Un Worker a rencontré une erreur")
            return False
        
        with open("result.txt", "a") as f:
            f.write(f"Un Manager a fini de faire travailler ses workers en {datetime.datetime.now() - debut}\n")

        print(f"Un Manager a fini de faire travailler ses {Manager.NB_WORKERS} workers en {datetime.datetime.now() - debut}")
        return True
    
    def run(self, gamma, epsilon):
        try: ended = asyncio.run(self.start(gamma, epsilon))
        except Exception as e:
            print("Manager:", e)
            ended = False
        if not ended:
            print("Une erreur est survenue")
        return ended


class Worker:

    def __init__(self, gamma, epsilon, agglo_func) -> None:
        self.edt = EDT2()
        self.gamma = gamma      # Coefficient d'exploration
        self.epsilon = epsilon  # Coefficient de phéromones

        self.omega = []       # Univers des possibilitées
        self.available_slots: 'dict[int, list]' = {} # Dictionnaire des slots pour amélioration par voisinage

        db = Database.get("edt_generator")
        min_pheromone = db.run("SELECT IFNULL(AVG(PHEROMONE), 0) AS 'P' FROM PHEROMONES2;").fetch(first=True)['P'] * Manager.COEF_GAMMA_OVER_EPSILON
        sql = f"""
            SELECT ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX, {agglo_func}(IFNULL(PHEROMONE, {min_pheromone})) AS PHEROMONE
            FROM ALL_ASSOCIATIONS
                 LEFT JOIN PHEROMONES2 ON ID = ID_ASSOCIATION
            GROUP BY ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX;
        """
        max_creneaux = db.run("SELECT MAX(NB_CRENEAUX) AS MAX FROM ALL_ASSOCIATIONS").fetch(first=True)['MAX']
        for node in db.run(sql).fetch():
            cours = Cours2.get(node['ID_COURS'])
            omega_node = {
                'ID': node['ID'], 'COURS': cours, 
                'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 
                'PERCENT_CRENEAUX': 1 - (node['NB_CRENEAUX'] / max_creneaux), 
                'PHEROMONE': node['PHEROMONE']
            }
            self.omega.append(omega_node)

            if cours not in self.available_slots:
                self.available_slots[cours.id] = []
            self.available_slots[cours.id].append({'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 'ID': node['ID'], 'COURS': cours})

        db.close()

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
        db = Database.get("edt_generator")
        sql_insert_pheromone = """
            INSERT INTO PHEROMONES2 (ID_ASSOCIATION, PHEROMONE) VALUES (%s, %s)
        """

        sql_get_association = """
            SELECT ID FROM ALL_ASSOCIATIONS WHERE ID_COURS = %s AND JOUR = %s AND HEURE = %s;
        """

        score = self.edt.get_score()
        try: self.upgrade_edt_with_local_search()
        except Exception as e: print("Worker local search:", e)
        #print("Worker score:", self.edt.get_score() - score)
        score = self.edt.get_score()

        for cours in self.edt.cours:
            assoc_id = db.run([sql_get_association, (cours.id, cours.jour, cours.heure)]).fetch(first=True)['ID']
            db.run([sql_insert_pheromone, (assoc_id, score)])

        if score > best_score.value:
            with best_score_lock:
                if score > best_score.value:
                    best_score.value = score
                    best_edt[:] = self.edt.cours
                
        db.close()
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
            self.available_slots[other_cours_id] = [slot for slot in self.available_slots[other_cours_id] if slot['JOUR'] != jour or slot['HEURE'] not in heures]


    def upgrade_edt_with_local_search(self):
        self.edt.get_score()
        db = Database.get("edt_generator")

        score = self.edt.get_score()
        sql_insert_pheromone = """
            INSERT INTO PHEROMONES2 (ID_ASSOCIATION, PHEROMONE, FROM_SUPER_WORKER) VALUES (%s, %s, 1)
        """

        for cours in self.edt.cours.copy():
            if not cours or not self.available_slots[cours.id]:
                continue

            # Historiques des déplacements
            # 1. -> retirer le main.cours
            # 2. Pour chaque association possible,
            #    2.1 -> ajouter le main.cours à l'association
            #    2.2 -> Compléter l'edt avec choose_node
            #        2.2.1 -> Ajouter le nodes à la liste des associations utilisées
            #    2.3 -> Retirer les nodes ajoutés
            #    2.4 -> Retirer le main.cours déplacé de l'association
            # 3. -> Reposer le main.cours à sa place initiale si aucune association n'a été trouvée
            
            # 1. Libérer le slots pour essayer des nouvelles associations
            self.edt.remove_cours(cours)
            best_assocs = []

            # Tester toutes les possibilitées pour un cours
            for assoc in self.available_slots[cours.id]:
                if self.edt.is_free(assoc['JOUR'], assoc['HEURE'], cours) != 1:
                    continue
                
                # 2. Créer une nouvelle association
                try: self.edt.add_cours(cours, assoc['JOUR'], assoc['HEURE'])
                except Exception as e:
                    print("Upgrade EDT 2: Impossible d'ajouter le cours", e)

                # 3. Essayer de faire des associations avec les autres cours
                node = self.choose_node()
                new_assocs = []
                while node is not None:
                    self.edt.add_cours(node['COURS'], node['JOUR'], node['HEURE'])
                    new_assocs.append((node['JOUR'], node['HEURE'], node['COURS'], node['ID']))
                    node = self.choose_node()
                
                # 4. Vérifier si la nouvelle association est meilleure
                new_score = self.edt.get_score()
                if new_score > score:
                    score = new_score
                    best_assocs = new_assocs.copy()
                    best_assocs.append(assoc)

                # 5. Enregister les Phéromones des nouvelles associations
                # 6. Retirer les nouvelles associations
                for new_assoc in new_assocs:
                    db.run([sql_insert_pheromone, (new_assoc[3], new_score)])
                    tmp_cours: Cours2 = new_assoc[2].copy()
                    tmp_cours.jour = new_assoc[0]
                    tmp_cours.heure = new_assoc[1]
                    self.edt.remove_cours(tmp_cours)
                
                # 7. Retirer le cours ajouté
                db.run([sql_insert_pheromone, (assoc['ID'], new_score)])
                main_cours = cours.copy()
                main_cours.jour = assoc['JOUR']
                main_cours.heure = assoc['HEURE']
                self.edt.remove_cours(main_cours)
    
            # 7. Ajouter la meilleure association
            if len(best_assocs) > 0:
                for best_assoc in best_assocs:
                    self.edt.add_cours(cours, best_assoc['JOUR'], best_assoc['HEURE'])
            else:
                self.edt.add_cours(cours, cours.jour, cours.heure)
        db.close()
       
def generate():
    num_cores = multiprocessing.cpu_count() - 1

    total_workers = len(Cours2.ALL) * 300
    total_managers = total_workers // (Manager.NB_WORKERS + Manager.NB_SUPER_WORKERS)
    total_iterations = total_managers // num_cores + 1

    results = []

    best_score.value = 0
    best_edt[:] = []

    for index_iteration in range(total_iterations):
        with open("result.txt", "a") as f:
            f.write(f"\nIteration {index_iteration}\n")  

        print(f"Iteration {index_iteration + 1} / {total_iterations}")
        gamma = index_iteration / total_iterations
        epsilon = 1 - gamma
        with multiprocessing.Pool(processes=num_cores) as pool:
            for __ in range(num_cores):
                # On veut créer un manager par core soit num_cores
                results.append(pool.apply_async(Manager().run, (gamma, epsilon)))
            
            # Fermer le pool pour empêcher l'ajout de nouvelles tâches
            pool.close()
            # Attendre que toutes les tâches soient terminées
            pool.join()

            print(f"---> {Manager.NB_WORKERS * num_cores} workers ont fini de travailler")
            print(f"---> Meilleur score: {best_score}")

    print(f"===> {Manager.NB_WORKERS * num_cores * total_iterations} workers ont fini de travailler")
    return EDT2(_from_cours=best_edt)
