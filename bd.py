from flask import Flask
from database import Database
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
import os

load_dotenv()


app = Flask(__name__)

# Configurações do banco de dados
app.config['MYSQL_HOST'] = "localhost" #localhost
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = "ANUNCIAUFC"  

db = Database(app)
bcrypt = Bcrypt(app)

@app.route('/create_tables', methods=['GET'])
def create_tables():
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS USERS(
                id INT PRIMARY KEY AUTO_INCREMENT,
                email VARCHAR(100) UNIQUE,
                password VARCHAR(100),
                name VARCHAR(100)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS CUSTOMERS(
                id INT PRIMARY KEY AUTO_INCREMENT,
                userId INT,
                telephone VARCHAR(20),
                cpf VARCHAR(14),
                campus VARCHAR(100),
                gender VARCHAR(20),
                FOREIGN KEY (userId) REFERENCES USERS(id) ON DELETE CASCADE    
            )""")
        db.execute("""
            CREATE TABLE IF NOT EXISTS ADMINISTRATORS(
                id INT PRIMARY KEY AUTO_INCREMENT,
                userId INT,
                FOREIGN KEY (userId) REFERENCES USERS(id) ON DELETE CASCADE 
            )
            """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS ANNOUNCEMENTS(
                id INT PRIMARY KEY AUTO_INCREMENT,
                customerId INT NOT NULL,
                title VARCHAR(100),
                campus VARCHAR(100),
                category VARCHAR(50),
                price VARCHAR(20),
                state ENUM('novo', 'usado') DEFAULT 'novo',
                description VARCHAR(2028),
                validation Int,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customerId) REFERENCES CUSTOMERS(id) ON DELETE CASCADE
            )
        """)
       
        db.execute("""
            CREATE TABLE IF NOT EXISTS IMAGES( 
                id INT PRIMARY KEY AUTO_INCREMENT,
                announcementId INT NOT NULL,
                image LONGBLOB, 
                imageDescription VARCHAR(255), 
                FOREIGN KEY (announcementId) REFERENCES ANNOUNCEMENTS(id) ON DELETE CASCADE
            )
        """)
        
        senha = bcrypt.generate_password_hash(os.getenv("ADMIN_PASSWORD"))
        email = os.getenv("ADMIN_EMAIL")
        name = os.getenv("ADMIN_NAME")
        
        db.execute("""
                   INSERT INTO USERS (email, password, name)
                   VALUE(%s, %s, %s)""", (email, senha, name))
        
        db.execute("""
                   INSERT INTO ADMINISTRATORS (userId)
                   VALUE(1)""")
        
        return "Tabelas criadas com sucesso!"
    
    except Exception as e:
        return f"Erro ao criar tabelas: {e}"


if __name__ == '__main__':
    app.run(debug=True)
    
    
