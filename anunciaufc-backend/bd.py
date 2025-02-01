from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configurações do banco de dados
app.config['MYSQL_HOST'] = "" #localhost
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "" # SENHA 
app.config['MYSQL_DB'] = "ANUNCIAUFC"  


mysql = MySQL(app)


@app.route('/create_tables', methods=['GET'])
def create_tables():
    try:
        cursor = mysql.connection.cursor()
        
        
        cursor.execute("""
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
        
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ANNOUNCEMENT(
                id INT PRIMARY KEY AUTO_INCREMENT,
                userId INT NOT NULL,
                title VARCHAR(100),
                campus VARCHAR(100),
                category VARCHAR(50),
                price VARCHAR(20),
                state ENUM('new', 'used') DEFAULT 'new',
                description VARCHAR(2028),
                images LONGBLOB,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userId) REFERENCES USERS(id)
            )
        """)
        cursor.execute('''
        INSERT INTO USERS (email, password, name, telephone, cpf, campus, gender)
        VALUE
        ('joao.silva@email.com', 'senha123', 'João Silva', '123456789', '123.456.789-00', 'Campus A', 'Masculino')
        ''')

        cursor.execute('''
        INSERT INTO ANNOUNCEMENT (userId, title, campus, category, price, state, description, images)
        VALUES
        (1, 'Notebook Dell Inspiron', 'Campus A', 'Electronics', '2500', 'new', 'Notebook Dell Inspiron com 8GB RAM e 512GB SSD.', NULL),
        (1, 'Cadeira Gamer', 'Campus B', 'Furniture', '600', 'used', 'Cadeira gamer usada, boa condição.', NULL),
        (1, 'Livro de Python', 'Campus C', 'Books', '50', 'new', 'Livro de introdução à programação com Python.', NULL),
        (1, 'Smartphone Samsung Galaxy S21', 'Campus A', 'Electronics', '3500', 'new', 'Smartphone Samsung Galaxy S21 com 128GB de armazenamento.', NULL),
        (1, 'Mesa de Escritório', 'Campus B', 'Furniture', '400', 'used', 'Mesa de escritório usada em bom estado.', NULL);''')

        
        mysql.connection.commit()  
        return "Tabelas criadas com sucesso!"
    
    except Exception as e:
        return f"Erro ao criar tabelas: {e}"
    
    finally:
        cursor.close()


if __name__ == '__main__':
    app.run(debug=True)
