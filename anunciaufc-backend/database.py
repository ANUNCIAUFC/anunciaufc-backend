from flask_mysqldb import MySQL

class Database:
    def __init__(self, app):
        self.mysql = MySQL(app)
        
    def query(self, sql, params=None):
        cursor = self.mysql.connection.cursor()
        cursor.execute(sql, params if params else [])
        result = cursor.fetchall()
        cursor.close()
        return result

    
    def execute(self, sql, params=None):
        cursor = self.mysql.connection.cursor()
        cursor.execute(sql, params if params else [])
        self.mysql.connection.commit()
        cursor.close()