import time
import pymysql, mariadb, Kairos_API.conn as conn

class Database:

    def __init__(self, host, user, password, database, port, driver=None) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.driver = driver

        self.cnx = None
        self.cursor = None

    def __str__(self):
        return self.host
    
    def connect(self):
        nb_try = 0
        while self.cnx is None and nb_try < 5:
            try:
                if self.driver == 'mariadb':
                    self.cnx = mariadb.connect(user=self.user, database=self.database, password=self.password, host=self.host,
                                            port=int(self.port), autocommit=True)
                else:
                    self.cnx = pymysql.connect(user=self.user, database=self.database, password=self.password, host=self.host,
                                            port=int(self.port), autocommit=True)
            except Exception as e:
                nb_try += 1
                print(e)
                print(f"Impossible de se connecter à la base de données {self.database} sur {self.host}:{self.port} avec l'utilisateur {self.user}.")
                print("Réessai dans 3 secondes...")
                time.sleep(3)
        if nb_try == 5:
            print('--> Impossible de se connecter à la base de données')
            return None
        self.cursor = self.cnx.cursor()
    
    @staticmethod
    def get(name=None):
        if name is None:
            database = Database(conn.HOST, conn.USER, conn.PWD, conn.DB, conn.PORT)
        elif name == "edt_generator":
            database = Database(host='db', user='root', password='root', database='db_edt_generator', port=3306, driver='mariadb')
        database.connect()
        return database
    
    def run(self, query):

        # Si la requête est une string, on l'exécute directement
        if type(query) == str:
            self.cursor.execute(query)
        
        # Si la requête est un tuple, on l'exécute avec les paramètres
        else:

            # S'il y a plusieurs requêtes, on les exécute toutes
            if type(query[0]) == tuple or len(query) > 2:
                for q in query:

                    # Gérer les requêtes avec et sans paramètres
                    if type(q) == tuple:
                        self.cursor.execute(q[0], q[1])
                    else:
                        self.cursor.execute(q)
            
            # Sinon on exécute la requête
            else:
                self.cursor.execute(query[0], query[1])

        return self
    
    def fetch(self, encapsulate=False, rowcount=False, description=False, as_list=False, first=False):
        if rowcount:
            return self.cursor.rowcount
        
        columns = [column[0] for column in self.cursor.description if column is not None] if self.cursor.description is not None else []
        results = []

        if description:
            return self.cursor.description

        if as_list:
            return list(self.cursor.fetchall() or [])

        if first:
            return dict(zip(columns, self.cursor.fetchone() or []))

        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        if encapsulate:
            result = {'result': results}
            if rowcount:
                result['rowcount'] = self.cursor.rowcount
            
            if description:
                result['description'] = self.cursor.description

            return results
        
        return results
    
    def exists(self, qtt=1):
        return self.cursor.rowcount > qtt - 1

    def last_id(self):
        return self.cursor.lastrowid

    def close(self):
        if self.cnx:
            self.cnx.commit()
            self.cnx.close()

            self.cnx = None

try:
    # Initialisation de la db de génération d'emploi du temps
    db_edt_generator = Database.get("edt_generator")
    sql = """
        DROP TABLE IF EXISTS COURS;
    """
    db_edt_generator.run(sql)

    sql = """
        DROP TABLE IF EXISTS PHEROMONES;
    """
    db_edt_generator.run(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS COURS (
        ID INT AUTO_INCREMENT PRIMARY KEY,
        COURS VARCHAR(10),
        JOUR INT,
        HEURE INT,
        INDEX idx_cours (COURS, JOUR, HEURE)
    );
    """
    db_edt_generator.run(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS PHEROMONES (
        ID_COURS INT,
        PHEROMONE FLOAT,
        BOOSTED TINYINT,
        INDEX idx_pheromones (ID_COURS)
    );
    """

    db_edt_generator.run(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS EDT_SIGNATURES (
        SIGNATURE VARCHAR(528) PRIMARY KEY,
        NOMBRE INT,
        INDEX idx_signatures (SIGNATURE)
    );
    """
    db_edt_generator.run(sql)

    # V2 ALGO

    sql = """
    CREATE TABLE IF NOT EXISTS ALL_ASSOCIATIONS (
        ID INT PRIMARY KEY AUTO_INCREMENT,
        ID_COURS INT,
        JOUR INT,
        HEURE INT,
        DAMAGES FLOAT,
        INDEX idx_all_associations (ID_COURS, JOUR, HEURE)
    );
    """
    db_edt_generator.run(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS PHEROMONES2 (
        ID_ASSOCIATION INT,
        PHEROMONE FLOAT,
        INDEX idx_pheromones2 (ID_ASSOCIATION)
    );
    """

    db_edt_generator.run(sql)

    sql = """
    CREATE TABLE IF NOT EXISTS SHARED_DATA (
        SCORE FLOAT,
        ASSOCIATIONS VARCHAR(528),
    );
    """

    db_edt_generator.run(sql)

    db_edt_generator.close()
except Exception as e:
    print(e)
