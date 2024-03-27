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
    NB_SUPER_WORKERS = 0
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

        try:
            super_workers = [SuperWorker() for _ in range(self.NB_SUPER_WORKERS)]
            tasks = [loop.create_task(super_worker.run()) for super_worker in super_workers]
            result = await asyncio.gather(*tasks)
        except Exception as e:
            print("Lors des superworker:", e)
            return False

        if not all(result) or len(result) != len(tasks):
            print("Un SuperWorker a rencontré une erreur")
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

        self.omega = None       # Univers des possibilitées

        db = Database.get("edt_generator")
        min_pheromone = db.run("SELECT IFNULL(AVG(PHEROMONE), 0) AS 'P' FROM PHEROMONES2;").fetch(first=True)['P'] * Manager.COEF_GAMMA_OVER_EPSILON
        sql = f"""
            SELECT ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX, {agglo_func}(IFNULL(PHEROMONE, {min_pheromone})) AS PHEROMONE
            FROM ALL_ASSOCIATIONS
                 LEFT JOIN PHEROMONES2 ON ID = ID_ASSOCIATION
            GROUP BY ID, ID_COURS, JOUR, HEURE, NB_CRENEAUX;
        """
        try:
            max_creneaux = db.run("SELECT MAX(NB_CRENEAUX) AS MAX FROM ALL_ASSOCIATIONS").fetch(first=True)['MAX']
            self.omega = [{'ID': node['ID'], 'COURS': Cours2.get(node['ID_COURS']), 'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 'PERCENT_CRENEAUX': 1 - (node['NB_CRENEAUX'] / max_creneaux), 'PHEROMONE': node['PHEROMONE']} for node in db.run(sql).fetch()]
        except Exception as e:
            print("Worker:", e)
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
                print("Worker:", e)
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


class SuperWorker:

    def __init__(self) -> None:
        self.initial_score = best_score.value
        self.edt = EDT2(_from_cours=best_edt)
        
        self.omega = {'others': []}

        db = Database.get("edt_generator")
        for cours in Cours2.ALL:
            if cours in self.edt.cours:
                cours = self.edt.cours[self.edt.cours.index(cours)]
                self.omega[cours] = db.run(f"SELECT * FROM ALL_ASSOCIATIONS WHERE ID_COURS = {cours.id} AND JOUR = {cours.jour}").fetch()
            else:
                self.omega['others'].extend(db.run(f"SELECT * FROM ALL_ASSOCIATIONS WHERE ID_COURS = {cours.id} ORDER BY NB_CRENEAUX").fetch())
        db.close()

        for cours in self.omega:
            if cours == 'others':
                continue
            new_omega = []
            for assoc in self.omega[cours]:
                keep = True
                for other_assoc in self.omega['others']:
                    if assoc['JOUR'] == other_assoc['JOUR'] and assoc['HEURE'] == other_assoc['HEURE']:
                        keep = False
                if keep: new_omega.append(assoc)
            self.omega[cours] = new_omega
    
    async def run(self):
        for cours in self.edt.cours.copy():
            if cours not in self.omega:
                continue
            
            free_assoc = []
            try: self.edt.remove_cours(cours)
            except: return False

            for assoc in self.omega[cours]:
                if self.edt.is_free(assoc['JOUR'], assoc['HEURE'], cours) == 1:
                    free_assoc.append(assoc)

            if not free_assoc:
                try: self.edt.add_cours(cours, cours.jour, cours.heure)
                except: return False
                continue

            assoc = random.choice(free_assoc)
            try:
                self.edt.add_cours(cours, assoc['JOUR'], assoc['HEURE'])
                while True:
                    node = self.choose_node()
                    if node is None:
                        break
                    self.edt.add_cours(node['COURS'], node['JOUR'], node['HEURE'])
                    print("Hello from active SuperWorker")
            except Exception as e:
                print("SuperWorker:", e)
                continue
        
        score = self.edt.get_score()
        if self.initial_score == score:
            return True
        
        # Sauvegarder les Phéromones
        sql_insert_pheromone = """
            INSERT INTO PHEROMONES2 (ID_ASSOCIATION, PHEROMONE, FROM_SUPER_WORKER) VALUES (%s, %s, 1)
        """
        db = Database.get("edt_generator")
        for cours in self.edt.cours:
            assoc_id = db.run(f"SELECT ID FROM ALL_ASSOCIATIONS WHERE ID_COURS = {cours.id} AND JOUR = {cours.jour} AND HEURE = {cours.heure}").fetch(first=True)['ID']
            db.run([sql_insert_pheromone, (assoc_id, score)])
        
        db.close()

        if self.edt.get_score() > best_score.value:
            with best_score_lock:
                if self.edt.get_score() > best_score.value:
                    best_score.value = self.edt.get_score()
                    best_edt[:] = self.edt.cours
        
        return True
    
    def choose_node(self):
        for node in self.omega['others']:
            if self.edt.is_free(node['JOUR'], node['HEURE'], node['COURS']) == 1:
                return node
        return None

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

            print(f"---> {Manager.NB_WORKERS * num_cores} workers et {Manager.NB_SUPER_WORKERS * num_cores} SuperWorkers ont fini de travailler")
            print(f"---> Meilleur score: {best_score}")

    print(f"===> {Manager.NB_WORKERS * num_cores * total_iterations} workers et {Manager.NB_SUPER_WORKERS * num_cores * total_iterations} SuperWorkers ont fini de travailler")
    return EDT2(_from_cours=best_edt)

# def process_loop(start, end):
#     for i in range(start, end): ...
#         # Faites quelque chose avec la variable i

# if __name__ == '__main__':
#     num_cores = multiprocessing.cpu_count()
#     pool = multiprocessing.Pool(processes=num_cores)

#     total_iterations = 1_000_000_000_000_000
#     chunk_size = total_iterations // num_cores

#     start = 0
#     end = chunk_size

#     results = []

#     for _ in range(num_cores):
#         results.append(pool.apply_async(process_loop, (start, end)))
#         start = end
#         end += chunk_size

#     pool.close()
#     pool.join()

#     # Récupérez les résultats si nécessaire
#     for result in results:
#         result.get()