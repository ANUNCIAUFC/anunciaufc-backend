from flask import Flask, render_template, request, jsonify, session
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Configurações do banco de dados
app.config['MYSQL_HOST'] = "127.0.0.1" #LOCALHOST GIO, MUDEM PARA O SEU POR FAVOR
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "1712" #Essa senha é do bd da Gio, se eu não tiver trocado troque por 1234 por favor!
app.config['MYSQL_DB'] = "ANUNCIAUFC"  # Certifique-se de que esse banco existe
app.config['SECRET_KEY'] = "chave"

# Inicializando MySQL e Bcrypt
mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Função para criar as tabelas
def create_tables():
    cursor = mysql.connection.cursor()

    # Criando a tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuario (
            idUser INT AUTO_INCREMENT PRIMARY KEY,
            isAdmin BOOLEAN NOT NULL DEFAULT 0,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name VARCHAR(255) NOT NULL,
            telephone VARCHAR(15) NOT NULL,
            cpf VARCHAR(20) UNIQUE NOT NULL,
            campus VARCHAR(255) NOT NULL,
            gender VARCHAR(255) NOT NULL 
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Anuncios (
            idAnnouncement INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            campus VARCHAR(255) NOT NULL,
            value FLOAT NOT NULL,
            stateProduct VARCHAR(255) NOT NULL,
            description VARCHAR(255),
            image BLOB,
            validation BOOLEAN NOT NULL DEFAULT 0
            user_email VARCHAR(255),
            FOREIGN KEY (user_email) REFERENCES Usuario(email)
        );
    ''')

    # Confirmando a execução da transação
    mysql.connection.commit()
    cursor.close()

# Rota principal para testar se a aplicação está funcionando
@app.route('/')
def home():
    return "API do Projeto Integrador está funcionando!"

# Iniciar o servidor
if __name__ == '__main__':
    with app.app_context():  # Garantindo que estamos dentro do contexto da aplicação
        create_tables()  # Cria as tabelas ao iniciar a aplicação
    app.run(debug=True)
