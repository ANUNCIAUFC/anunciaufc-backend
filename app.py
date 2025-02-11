from flask import Flask, render_template, request, jsonify, session
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from database import Database
from mail import MailService
from abc import ABC, abstractmethod
import random
import mysql.connector
import base64
import jwt  
import datetime
import os

app = Flask (__name__)
app.config.from_object(Config)

app.config['MAIL_USERNAME'] = "anunciaufc@gmail.com"
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')   # Use a senha gerada pelo Google


SECRET_KEY = os.urandom(24)
JWT_SECRET_KEY = os.urandom(32).hex()

db = Database(app)
bcrypt = Bcrypt(app)
mail = MailService(app)

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

class CodeGenerator:
    @staticmethod
    def generate_code():
        return random.randint(100000, 999999)
    
class CodeVerifier:
    @staticmethod
    def verify_code(email, code):
        if email in temp_codes and temp_codes[email] == int(code):
            del temp_codes[email]  
            return True
        return False

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


@app.route('/home', methods=['GET'])
def home():
    try:
        quant = 8  
        announcements = db.query("SELECT * FROM ANNOUNCEMENT WHERE validation = 1 ORDER BY RAND() LIMIT %s", (quant,))
        
        return jsonify([
        {
            'id': announcement[0],
            'description': announcement[7],
            'campus': announcement[3],
            'price': announcement[5],
            'images': announcement[8], #por enquanto é null
            'date': announcement[9]
        } for announcement in announcements
        ])
        
    except Exception as e:
        return jsonify ({'error': str(e)}), 500
    

@app.route('/products', methods = ['GET'])
def products():
    try:
        category = request.args.get('category')
        campus = request.args.get('campus')
        state = request.args.get('state')
        order_az = request.args.get('order_az')
        order_price = request.args.get('order_price')

        query = "SELECT * FROM ANNOUNCEMENT WHERE 1=1"
        params = []

        if category:
            query += " AND category = %s"
            params.append(category)
        if state:
            query += " AND state = %s"
            params.append(state)
        if campus:
            query += " AND campus = %s"
            params.append(campus)


        order_clauses = []

        if order_az and order_az.lower() == 'true':
            order_clauses.append(" title ASC")

        if order_price and order_price.lower() == 'true':
            order_clauses.append(" price + 0 ASC")
        
        if order_clauses:
            query += " ORDER BY " + " , ".join(order_clauses)

        
        productsbd = db.query(query, params)

        products_list = [
        {
            "id": p[0],
            "userId": p[1],
            "title": p[2],
            "campus": p[3],
            "category": p[4],
            "price": p[5],
            "state": p[6],
            "description": p[7],
            "images": p[8],
            "date": p[9]
        }
        for p in productsbd
    ]

        return jsonify(products_list), 200


    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


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

        name = data['name']
        password = bcrypt.generate_password_hash(data['password'])
        telephone = data['telephone']
        email = data['email']
        cpf = data['cpf']
        campus = data['campus']
        gender = data['gender']

        user_existe = db.query("SELECT email FROM USERS WHERE email = %s", (email,))

        if user_existe:
            return jsonify({'message': "E-mail existente, digite outro!", 'code': "EMAIL_ALREADY_EXISTS"}), 409

        db.execute("""
            INSERT INTO USERS (name, password, telephone, email, cpf, campus, gender) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, password, telephone, email, cpf, campus, gender))

        return jsonify({'message': 'Registrado com sucesso'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/confirmaemail', methods=['POST'])
def send_confirmation_email():
    data = request.get_json()
    email = data.get('email')

    confirmation_code = CodeGenerator.generate_code()
    temp_codes[email] = confirmation_code

    try:
        
        mail.sendmail(email, confirmation_code)
        return jsonify({'message': 'E-mail enviado com sucesso!'}), 200

    except Exception as e:
        return jsonify({'message': 'Erro ao enviar o e-mail.', 'error': str(e)}), 500
    

@app.route('/verifyemail', methods=['POST'])
def verifyemail():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if CodeVerifier.verify_code(email, int(code)):
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

        user = db.query("SELECT * FROM USERS WHERE email = %s", (email,))[0]
        
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
        return jsonify({'error': str(e)}), 500


@app.route('/forgotpassword', methods=['PUT'])
def fargotpassword():
    try:
        data = request.get_json()
        email = data.get('email')
        password = bcrypt.generate_password_hash(data.get('password'))
        
        db.execute("""
            UPDATE USERS SET password = %s WHERE email = %s
        """, (password, email))
    

        return jsonify({'message': 'Senha modificada com sucesso'}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/createannouncement', methods=['POST'])
def criar_anuncio():
    if 'email' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    token = request.headers.get('Authorization')
    
    payload = verify_jwt_token(token)
        
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 404
    
    data = request.get_json() 
    images = request.files.getlist("images")
    
    if len(images) > 4:
        return jsonify({'error': 'Máximo de 4 imagens permitidas'}), 400
    
    
    title = data['title']
    category = data['category']
    campus = data['campus']
    value = data['value']
    stateProduct = data['stateProduct']
    description = data['description']
    validation = 1 #Quando a parte do adm estiver implementado deve inicializar em 0
    
    image_bytes = [None] * 4  
    for i in range(len(images)):  
        image_bytes[i] = base64.b64decode(images[i])
    
    try:
        email = session['email']
        
        idUser = db.query('SELECT * FROM USERS WHERE email = %s', (email,))[0][0]
        
        db.execute(''' 
            INSERT INTO ANNOUNCEMENT(userId, title, category, campus, price, state, description, image1, image2, image3, image4, validation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (idUser, title, category, campus, value, stateProduct, description, image_bytes[0], image_bytes[1], image_bytes[2], image_bytes[3], validation))
        
        
        return jsonify({'message': 'Anúncio criado com sucesso!'}), 201
    
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


@app.route('/getannouncement', methods=['GET'])
def get_announcement(announcement_id):
    
    id = request.args.get('id')
    
    try:
        query = "SELECT title, category, campus, price, state, description, image1, image2, image3, image4 FROM ANNOUNCEMENT WHERE id = %s"
        anuncio = db.query(query, (id,))

        if not anuncio:
            return jsonify({'error': 'Anúncio não encontrado'}), 404

        # Converter imagens binárias para base64 para facilitar a exibição no front-end
        def convert_image(image_data):
            return None if image_data is None else f"data:image/jpeg;base64,{image_data.hex()}"

        images = [convert_image(anuncio[f'image{i}']) for i in range(1, 5)]
        
        return jsonify({
            'title': anuncio['title'],
            'category': anuncio['category'],
            'campus': anuncio['campus'],
            'price': anuncio['price'],
            'state': anuncio['state'],
            'description': anuncio['description'],
            'images': images
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

