import datetime, multiprocessing, random, asyncio
from EDT_generator.V2.cours2 import Cours2
from EDT_generator.V2.edt2 import EDT2
from Kairos_API.database import Database

best_score = multiprocessing.Value('d', 0)
best_score_lock = multiprocessing.Lock()

data_manager = multiprocessing.Manager()
best_edt = data_manager.list()
best_edt_lock = multiprocessing.Lock()

class Manager:
    NB_WORKERS = 50

    async def start(self, gamma, epsilon):
        loop = asyncio.get_event_loop()
        workers = [Worker(gamma, epsilon) for _ in range(self.NB_WORKERS)]
        tasks = [loop.create_task(worker.run()) for worker in workers]

        debut = datetime.datetime.now()
        result = await asyncio.gather(*tasks)
        with open("result.txt", "a") as f:
            f.write(f"Un Manager a fini de faire travailler ses workers en {datetime.datetime.now() - debut}\n")

        print(f"Un Manager a fini de faire travailler ses {Manager.NB_WORKERS} workers en {datetime.datetime.now() - debut}")
        return result
    
    def run(self, gamma, epsilon):
        asyncio.run(self.start(gamma, epsilon))


class Worker:

    def __init__(self, gamma, epsilon) -> None:
        self.edt = EDT2()
        self.gamma = gamma      # Coefficient d'exploration
        self.epsilon = epsilon  # Coefficient de phéromones

        self.omega = None       # Univers des possibilitées

        db = Database.get("edt_generator")
        sql = """
            SELECT ID, ID_COURS, JOUR, HEURE, DAMAGES, AVG(IFNULL(PHEROMONE, 0)) AS PHEROMONE
            FROM ALL_ASSOCIATIONS
                 LEFT JOIN PHEROMONES2 ON ID = ID_ASSOCIATION
            GROUP BY ID, ID_COURS, JOUR, HEURE, DAMAGES;
        """ # TODO: Globaliser omega
        max_damages = db.run("SELECT MAX(DAMAGES) AS MAX FROM ALL_ASSOCIATIONS").fetch(first=True)['MAX']
        self.omega = [{'ID': node['ID'], 'COURS': Cours2.get(node['ID_COURS']), 'JOUR': node['JOUR'], 'HEURE': node['HEURE'], 'DAMAGES': max_damages / node['DAMAGES'], 'PHEROMONE': node['PHEROMONE']} for node in db.run(sql).fetch()]

        db.close()

    async def run(self):
        while True:
            node = self.choose_node()
            if node is None:
                break
            self.edt.add_cours(node['COURS'], node['JOUR'], node['HEURE'])
            self.rm_from_omega(node['JOUR'], node['HEURE'], node['COURS'].duree, node['COURS'])

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
                    while best_edt:
                        best_edt.pop()
                    best_edt.extend(self.edt.cours)


        db.close()
        return self.edt

    def choose_node(self):
        if not self.omega:
            return None
        
        P = []
        max_pheromone = 0
        for node in self.omega:
            if node['PHEROMONE'] > max_pheromone:
                max_pheromone = node['PHEROMONE']
            P.append(self.gamma * node['DAMAGES'] + self.epsilon * 1 / (101 - node['PHEROMONE']))

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
            if cours and node['COURS'] == cours:
                continue
            
            self.new_omega.append(node)
        self.omega = self.new_omega

def generate():
    num_cores = multiprocessing.cpu_count()

    total_workers = len(Cours2.ALL) * 300
    total_managers = total_workers // Manager.NB_WORKERS
    total_iterations = total_managers // num_cores + 1

    results = []

    best_score.value = 0
    while best_edt:
        best_edt.pop()

    for index_iteration in range(total_iterations):
        with open("result.txt", "a") as f:
            f.write(f"\nIteration {index_iteration}\n")  

        print(f"Iteration {index_iteration + 1} / {total_iterations}") 
        with multiprocessing.Pool(processes=num_cores) as pool:
            for __ in range(num_cores):
                # On veut créer un manager par core soit num_cores
                results.append(pool.apply_async(Manager().run, (0.5, 0.5)))
            
            # Fermer le pool pour empêcher l'ajout de nouvelles tâches
            pool.close()
            # Attendre que toutes les tâches soient terminées
            pool.join()

            print(f"---> {Manager.NB_WORKERS * num_cores} workers ont fini de travailler")

    print(f"===> {Manager.NB_WORKERS * num_cores * total_iterations} workers ont fini de travailler")

    print(f"Meilleur score: {best_score.value}")
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