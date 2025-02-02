from flask import Flask, render_template, request, jsonify, session
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from abc import ABC, abstractmethod
import random
import mysql.connector
import os
import base64
import jwt  
import os
import datetime

app = Flask (__name__)
app.secret_key = os.urandom(24)  #Gera uma chave secreta aleatória
JWT_SECRET_KEY = os.urandom(32).hex() #chave secreta JWT

app.config['MYSQL_HOST'] = '' #LOCALHOST 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' #SENHA 
app.config['MYSQL_DB'] = 'ANUNCIAUFC' #FAÇA O BANCO DE DADOS COM ESSE NOME
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'chave'

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'anunciaufc@gmail.com'  # Insira seu e-mail
app.config['MAIL_PASSWORD'] = 'msgn mgxl itmm kghd'           # Insira sua senha ou app password
app.config['MAIL_DEFAULT_SENDER'] = 'anunciaufc@gmail.com'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

mail = Mail(app)
temp_codes = {}

cors = CORS(app, supports_credentials=True, origins='http://localhost:5173')

def options():
    response = app.response_class()
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.status_code = 200
    return response

class USERS:
    def __init__(self, name, telephone, email, cpf, campus, gender):
        self.name = name
        self.telephone = telephone
        self.email = email
        self.cpf = cpf
        self.campus = campus
        self.gender = gender
        
def create_jwt_token(user):
    try:
        payload = { 
                'name': user[3],          
                'campus': user[6],      
                'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)
            }
            
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

        return token
    
    except Exception as e:
        return None
        
def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None #token foi expirado
    except jwt.InvalidTokenError:
        return None #token inválido

"""
Caso  tenha filtros e ordenação, envie assim:
Exemplo:
GET /?category=eletronicos&az=true
"""
@app.route('/', methods=['GET'])
def home():
    try:
        cursor = mysql.connection.cursor()
        
        category = request.args.get('category')
        campus = request.args.get('campus')
        state = request.args.get('state')
        order_az = request.args.get('az') #mude caso não seja assim o nome
        order_price = request.args.get('price')
       
        query = "SELECT * FROM Announcement"
        
        params = []
        conditions = [] 
        if category:
            conditions.append("category = %s")
            params.append(category)
        if campus:
            conditions.append("campus = %s")
            params.append(campus)
        if state:
            conditions.append("state = %s")
            params.append(state) 
        if order_az and order_az.lower() == 'true':
            query += " ORDER BY title ASC"
        
        
        if order_price and order_price.lower() == 'true':
            if 'ORDER BY' in query:
                query += ", price ASC"
            else:
                query += " ORDER BY price ASC"
        
       
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, tuple(params))
        announcements = cursor.fetchall()
        cursor.close()
        
        return jsonify([
        {
            'title': announcement[2],
            'campus': announcement[3],
            'price': announcement[5],
            'images': announcement[8], #por enquanto é null
            'date': announcement[9]
        } for announcement in announcements
        ])
        
    except Exception as e:
        return jsonify ({'error': str(e)}), 500

@app.route('/register', methods=['POST', 'OPTIONS'])
def cadastro():
    try:
        if request.method == 'OPTIONS':
            response = app.response_class()
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.status_code = 200
            return response

        data = request.get_json()
        cursor = mysql.connection.cursor()

        name = data['name']
        password = bcrypt.generate_password_hash(data['password'])
        telephone = data['telephone']
        email = data['email']
        cpf = data['cpf']
        campus = data['campus']
        gender = data['gender']

        cursor.execute("SELECT email FROM USERS WHERE email = %s", (email,))
        user_existe = cursor.fetchone()

        if user_existe:
            cursor.close()
            return jsonify({'message': "E-mail existente, digite outro!", 'code': "EMAIL_ALREADY_EXISTS"}), 409

        cursor.execute("""
            INSERT INTO USERS (name, password, telephone, email, cpf, campus, gender) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, password, telephone, email, cpf, campus, gender))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Registrado com sucesso'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/confirmaemail', methods=['POST'])
def send_confirmation_email():
    data = request.get_json()
    email = data.get('email')  # E-mail fornecido pelo usuário

    # Gere um código de verificação (exemplo: 6 dígitos)
    confirmation_code = random.randint(100000, 999999)
    temp_codes[email] = confirmation_code

    print(confirmation_code)

    # Enviar o e-mail
    try:
        msg = Message(
            'Confirmação de Cadastro',
            recipients=[email]  # Lista de destinatários
        )
        msg.body = f"Seu código de verificação é: {confirmation_code}"
        mail.send(msg)
        
        return jsonify({'message': 'E-mail enviado com sucesso!', 'code': confirmation_code}), 200

    except Exception as e:
        return jsonify({'message': 'Erro ao enviar o e-mail.', 'error': str(e)}), 500
    

@app.route('/verifyemail', methods=['POST'])
def verifyemail():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if temp_codes[email] == int(code):
        del temp_codes[email]
        return jsonify({'message':'Code validated successfully.'}), 200
    else:
        return jsonify({'message':'Invalid code.'}), 400

 
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email e senha são obrigatórios'}), 400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM USERS WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'message': 'Usuário não encontrado'}), 404
        if not bcrypt.check_password_hash(user[2], password):
            return jsonify({'message': 'Senha inválida'}), 401
        
        token = create_jwt_token(user)
        
        if token is None:
            return jsonify({'error': 'Erro ao criar o token JWT'}), 500
        
        session['email'] = email

        return jsonify({'message': 'Login realizado com sucesso',
                        'token': token}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)

