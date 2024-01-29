import pymysql, Kairos_API.conn as conn

class Database:

    def __init__(self, host, user, password, database, port) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

        self.cursor = None

    def __str__(self):
        return self.host
    
    def connect(self):
        self.cnx = pymysql.connect(user=self.user, database=self.database, password=self.password, host=self.host,
                                    port=int(self.port), autocommit=True)
        self.cursor = self.cnx.cursor()
    
    @staticmethod
    def get():
        database = Database(conn.HOST, conn.USER, conn.PWD, conn.DB, conn.PORT)
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

        if as_list:
            return list(self.cursor.fetchall())

        if first:
            return dict(zip(columns, self.cursor.fetchone()))

        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        if encapsulate:
            result = {'result': results}
            if rowcount:
                result['rowcount'] = self.cursor.rowcount
            
            if description:
                result['description'] = self.cursor.description

            return results

        if description:
            return self.cursor.description
        
        return results
    
    def exists(self, qtt=1):
        return self.cursor.rowcount > qtt - 1

    def last_id(self):
        return self.cursor.lastrowid

    def close(self):
        if self.cnx:
            self.cnx.commit()
            self.cnx.close()

