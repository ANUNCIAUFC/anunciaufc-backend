from flask import Flask
from database import Database

app = Flask(__name__)

# Configurações do banco de dados
app.config['MYSQL_HOST'] = "localhost" #localhost
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "" # SENHA 
app.config['MYSQL_DB'] = "ANUNCIAUFC"  

db = Database(app)

@app.route('/create_tables', methods=['GET'])
def create_tables():
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS USERS(
                id INT PRIMARY KEY AUTO_INCREMENT,
                email VARCHAR(100) UNIQUE,
                password VARCHAR(100),
                name VARCHAR(100),
                telephone VARCHAR(20),
                cpf VARCHAR(14),
                campus VARCHAR(100),
                gender VARCHAR(20)
            )
        """)
        
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS ANNOUNCEMENT(
                id INT PRIMARY KEY AUTO_INCREMENT,
                userId INT NOT NULL,
                title VARCHAR(100),
                campus VARCHAR(100),
                category VARCHAR(50),
                price VARCHAR(20),
                state ENUM('new', 'used') DEFAULT 'new',
                description VARCHAR(2028),
                image1 LONGBLOB,
                image2 LONGBLOB,
                image3 LONGBLOB,
                image4 LONGBLOB,
                validation Int,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userId) REFERENCES USERS(id)
            )
        """)
        return "Tabelas criadas com sucesso!"
    
    except Exception as e:
        return f"Erro ao criar tabelas: {e}"


if __name__ == '__main__':
    app.run(debug=True)