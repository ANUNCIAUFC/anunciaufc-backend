from flask import Flask, json, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config
from database import Database
from mail import MailService
import random
import base64
import jwt  
import datetime
import os
import base64

app = Flask (__name__)
app.config.from_object(Config)

app.config['MAIL_USERNAME'] = "anunciaufc@gmail.com"
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')  


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
        
def create_jwt_token(user, tipo):
    try:
        payload = { 
                'tipo': tipo,
                'email': user[1],     
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
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

def encode_image(image_data):
    if image_data:
        return base64.b64encode(image_data).decode('utf-8')
    return None  # Retorna None se a imagem for None

@app.route('/home', methods=['GET'])
def home():
    try:
        quant = 8  
        query = """
            SELECT a.id, a.description, a.campus, a.price, a.date, 
                COALESCE(i.image, '') AS image
            FROM ANNOUNCEMENTS a
            LEFT JOIN IMAGES i ON i.announcementId = a.id 
                    AND i.id = (SELECT MIN(id) FROM IMAGES WHERE announcementId = a.id)
            WHERE a.validation = 1
            ORDER BY RAND()
            LIMIT %s
        """
        
        announcements = db.query(query, (quant,))

        result = [
            {
                'id': announcement[0],
                'description': announcement[1],
                'campus': announcement[2],
                'price': announcement[3],
                'date': announcement[4],
                'image': encode_image(announcement[5])  
            }
            for announcement in announcements
        ]
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/products', methods = ['GET'])
def products():
    try:
        category = request.args.get('category')
        campus = request.args.get('campus')
        state = request.args.get('state')
        order_az = request.args.get('order_az')
        order_price = request.args.get('order_price')

        query = """
            SELECT 
                a.id, a.customerId, a.title, a.campus, a.category, 
                a.price, a.state, a.description, a.date, 
                i.image 
            FROM ANNOUNCEMENTS a
            LEFT JOIN IMAGES i ON a.id = i.announcementId
            WHERE a.validation = 1
        """
        params = []

        if category:
            query += " AND a.category = %s"
            params.append(category)
        if state:
            query += " AND a.state = %s"
            params.append(state)
        if campus:
            query += " AND a.campus = %s"
            params.append(campus)


        order_clauses = []

        if order_az and order_az.lower() == 'true':
            order_clauses.append(" a.title ASC")

        if order_price and order_price.lower() == 'true':
            order_clauses.append(" a.price + 0 ASC")
        
        if order_clauses:
            query += " ORDER BY " + " , ".join(order_clauses)

        
        productsbd = db.query(query, params)

        products_dict = {}

        for p in productsbd:
            announcement_id = p[0]
            if announcement_id not in products_dict:
                products_dict[announcement_id] = {
                    "id": p[0],
                    "campus": p[3],
                    "price": p[5],
                    "description": p[7],
                    "date": p[8],
                    "image": encode_image(p[9])
                }

        return jsonify(list(products_dict.values())), 200


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
            INSERT INTO USERS (name, password, email) 
            VALUES (%s, %s, %s)
        """, (name, password, email,))

        userId = db.query("SELECT id FROM USERS WHERE email = %s", (email,))
        
        db.execute("""
            INSERT INTO CUSTOMERS (userId, telephone, cpf, campus, gender)
            VALUES (%s, %s, %s, %s, %s)
        """, (userId, telephone, cpf, campus, gender,))

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
    

@app.route('/get_user', methods=['GET'])
def get_user():
    try:
        token = request.headers.get('Authorization').strip('"')
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Token expirado ou inválido'}), 401
        
        if payload.get('tipo') == 'admin':
            return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
        
        email = payload['email']
        
        user = db.query("""
                            SELECT 
                                u.name, 
                                u.email, 
                                c.telephone, 
                                c.cpf, 
                                c.campus, 
                                c.gender 
                            FROM USERS u
                            JOIN CUSTOMERS c ON u.id = c.userId
                            WHERE u.email = %s
                        """, (email,))[0]
        
        print(user)

        
        return jsonify({'name': user[0],
                        'telephone': user[2],
                        'email': user[1],
                        'cpf': user[3],
                        'campus': user[4],
                        'gender': user[5]}), 200 
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_user', methods=['PUT'])
def update_user():
    try:
        token = request.headers.get('Authorization').strip('"')
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Token expirado ou inválido'}), 401
        
        if payload.get('tipo') == 'admin':
            return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
        
        email = payload['email'] 
         
        data = request.get_json()
        user = db.query("""
                            SELECT 
                                u.id,
                                u.name, 
                                c.telephone, 
                                c.campus, 
                                c.gender 
                            FROM USERS u 
                            JOIN CUSTOMERS c
                                ON u.id = c.userId 
                            WHERE u.email = %s
                        """, (email,))[0]

        
        name = data.get('name', user[1])
        telephone = data.get('telephone', user[2])
        campus = data.get('campus', user[3])
        gender = data.get('gender', user[4])
        
        db.execute("""
            UPDATE USERS
            SET name = %s
            WHERE email = %s
        """, (name, email))
        
        db.execute("""
            UPDATE CUSTOMERS
            SET telephone = %s, campus = %s, gender = %s
            WHERE userId = %s
        """, (telephone, campus, gender, user[0]))
        
        user_update = db.query("SELECT * FROM USERS WHERE email = %s", (email,))[0]
        
        token_update = create_jwt_token(user_update, 'customer')
        
        return jsonify({'message': 'Dados atualizados com sucesso!',
                        'token': token_update}), 200 
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
       
@app.route('/delete_user', methods=['DELETE'])
def delete_user():
     
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)
     
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401
    
    try:
        email = payload['email']
        
        db.execute("DELETE FROM USERS WHERE email = %s", (email,))

        return jsonify({'message': 'Conta excluída com sucesso!'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

 
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
        
        admin = db.query('SELECT * FROM ADMINISTRATORS WHERE userId = %s', (user[0],))
        
        if admin:
            token = create_jwt_token(user, 'admin')
            return jsonify({'message': 'Login realizado com sucesso do administrador',
                            'type': 'admin',
                            'token': token}), 200
        
        
        token = create_jwt_token(user, 'customer')
        
        if token is None:
            return jsonify({'error': 'Erro ao criar o token JWT'}), 500
        

        return jsonify({'message': 'Login realizado com sucesso',
                        'type': 'customer',
                        'token': token,
                        'email': email}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500
    


@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization').strip('"')

    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401
    
    return jsonify({'message': 'Logout realizado com sucesso!'}), 200


@app.route('/forgot_password', methods=['PUT'])
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
    

    
@app.route('/create_announcement', methods=['POST', 'OPTIONS'])
def criar_anuncio():
    if request.method == 'OPTIONS':
        response = app.response_class()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.status_code = 200
        return response
    
    token = request.headers.get('Authorization').strip('"')

    if not token:
        response = jsonify({'error': 'Token não enviado'}), 401
        return response

    payload = verify_jwt_token(token)


    if not payload:
        response = jsonify({'error': 'Token expirado ou inválido'}), 401
        return response
    
    if payload.get('tipo') == 'admin':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403

    email = payload.get('email') 
    print(request.files.getlist("images"))
    data = json.loads(request.form['data'])
    images = request.files.getlist("images")

    if len(images) > 4:
        response = jsonify({'error': 'Máximo de 4 imagens permitidas'}), 400
        return response
    
    image_bytes = [img.read() for img in images] + [None] * (4 - len(images))
    
    title = data['title']
    category = data['category']
    campus = data['campus']
    value = data['price']
    stateProduct = data['state']
    description = data['description']
    validation = 0
    
    try:
        
        # Buscar o 'customerId' em 'CUSTOMERS' usando o 'userId' de 'USERS'
        customer = db.query('SELECT id FROM CUSTOMERS WHERE userId = (SELECT id FROM USERS WHERE email = %s)', (email,))
        if not customer:
            return jsonify({'error': 'Usuário não cadastrado como cliente'}), 400
        customerId = customer[0][0]  # Obter o 'customerId' da consulta

        db.execute(''' 
            INSERT INTO ANNOUNCEMENTS(customerId, title, category, campus, price, state, description, validation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (customerId, title, category, campus, value, stateProduct, description, validation))

        idAnnouncement = db.query('SELECT LAST_INSERT_ID()')[0][0]

        for i, img in enumerate(image_bytes):
            if img:
                db.execute('''
                    INSERT INTO IMAGES(announcementId, image)
                    VALUES (%s, %s)
                ''', (idAnnouncement, img))

        return jsonify({'message': 'Anúncio criado com sucesso!'}), 200
    
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


@app.route('/get_announcement', methods=['GET'])
def get_announcement():
    id = request.args.get('id')
    print(id)
    
    try:
        # Obtendo o anúncio da tabela ANNOUNCEMENT
        query = "SELECT * FROM ANNOUNCEMENTS WHERE id = %s"
        anuncio = db.query(query, (id,))
        
        if not anuncio:
            return jsonify({'error': 'Anúncio não encontrado'}), 404
        
        anuncio = anuncio[0] 

        
        query_images = "SELECT image FROM IMAGES WHERE announcementId = %s"
        images_data = db.query(query_images, (id,))

        query_user = "SELECT telephone FROM CUSTOMERS WHERE id = %s"
        user_telephone = db.query(query_user, (anuncio[1],))[0][0]

        
        images = [encode_image(image[0]) for image in images_data]

        return jsonify({
            'title': anuncio[2],
            'category': anuncio[4],
            'campus': anuncio[3],
            'price': anuncio[5],
            'state': anuncio[6],
            'description': anuncio[7],
            'user_telephone': user_telephone,
            'date': anuncio[9],
            'images': images
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/my_announcements', methods=['GET'])
def meus_anuncios():
    
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401
    
    if payload.get('tipo') == 'admin':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
    
    try:
        email = payload['email']
        result = db.query(""" 
            SELECT a.*, 
                (SELECT i.image 
                    FROM IMAGES i 
                    WHERE i.announcementId = a.id 
                    ORDER BY i.id ASC 
                    LIMIT 1) AS first_image
            FROM ANNOUNCEMENTS a
            JOIN CUSTOMERS c ON a.customerId = c.id
            JOIN USERS u ON c.userId = u.id
            WHERE u.email = %s
        """, (email,))
        
        print(result[0])


        if not result:
            return jsonify({'message': 'Nenhum anúncio encontrado'}), 404
        
        announcements = [
            {
                "id": a[0],
                "title": a[2],
                "campus": a[3],
                "price": a[5],
                "description": a[7],
                "date": a[9],
                "image": encode_image(a[10]) if a[10] else None  
            }
            for a in result
        ]
            
        return jsonify(announcements), 200
    
    except Exception as e:
        print("Erro ao listar anúncios:", e)
        return jsonify({'error': f'Erro ao listar anúncios: {str(e)}'}), 500
    

@app.route('/update_announcement', methods=['PUT'])
def atualizar_anuncio():
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)

    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401

    if payload.get('tipo') == 'admin':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
    
    try:
        data = json.loads(request.form['data'])
        email = payload['email']
        announcementId = data.get('announcementId')

        result = db.query("""
                            SELECT a.*
                            FROM ANNOUNCEMENTS a
                            JOIN CUSTOMERS c ON a.customerId = c.id
                            JOIN USERS u ON c.userId = u.id
                            WHERE a.id = %s AND u.email = %s
                            """, (announcementId, email))


        if not result:
            return jsonify({'error': 'Anúncio não encontrado ou você não tem permissão para modificá-lo'}), 403

        result = result[0]
        print(result)

        title = data.get('title', result[2])
        category = data.get('category', result[4])
        campus = data.get('campus', result[3])
        price = data.get('price', result[5])
        state = data.get('state', result[6])
        description = data.get('description', result[8])
        validation = 0 

        db.execute('''
            UPDATE ANNOUNCEMENTS
            SET title = %s, category = %s, campus = %s, price = %s, state = %s, 
                description = %s, validation = %s
            WHERE id = %s
        ''', (title, category, campus, price, state, description, validation, announcementId))

        images = request.files.getlist("images")

        if images:
            if len(images) > 4:
                return jsonify({'error': 'Máximo de 4 imagens permitidas'}), 400

            db.execute("DELETE FROM IMAGES WHERE announcementId = %s", (announcementId,))

            for image in images:
                image_data = image.read()
                db.execute("INSERT INTO IMAGES (announcementId, image) VALUES (%s, %s)", (announcementId, image_data))

        return jsonify({'message': 'Anúncio atualizado com sucesso!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_announcement', methods=['DELETE'])
def deletar_anuncio():
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401
    
    if payload.get('tipo') == 'admin':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
    
    try:
        data = request.get_json()
        email = payload['email']
        announcementId = data.get('announcementId')
        
        result = db.query("""
            SELECT a.*
                FROM ANNOUNCEMENTS a
                JOIN CUSTOMERS c ON a.customerId = c.id
                JOIN USERS u ON c.userId = u.id
            WHERE a.id = %s AND u.email = %s
            """, (announcementId, email))
        
        if not result:
            return jsonify({'error': 'Anúncio não encontrado ou você não tem permissão para deletá-lo'}), 403
        
        db.execute('DELETE FROM ANNOUNCEMENTS WHERE id = %s', (announcementId,))
        
        return jsonify({'message': 'Anúncio deletado com sucesso!'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_announcement_no_verify', methods=['GET'])
def anuncios_nao_verificado():
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)

    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 401

    if payload.get('tipo') == 'customer':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403

    try:
        query = """
            SELECT a.id, a.customerId, a.date, u.email, u.name
            FROM ANNOUNCEMENTS a
            JOIN CUSTOMERS c ON a.customerId = c.id
            JOIN USERS u ON c.userId = u.id
            WHERE a.validation = %s
        """
        
        announcements = db.query(query, (0,))

        if not announcements:
            return jsonify([]), 200

        result = [
            {
                'id': announcement[0],           
                'customer_id': announcement[1],  
                'created_at': announcement[2],   
                'email': announcement[3],       
                'name': announcement[4]         
            }
            for announcement in announcements
        ]
    
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/verify_annoucement', methods=['PUT'])
def anuncios_verificados():
    data = request.get_json()
    print(data)
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)
    print(payload)

    id = data['id']
    status = data['status']
    email = data['email']

    if payload.get('tipo') == 'customer':
        return jsonify({'error': 'Usuário não autorizado para esta requisição'}), 403
    
    if status == 'accept':
        db.execute('UPDATE ANNOUNCEMENTS SET validation = %s WHERE id = %s', (1, id,))
        mail.send_accept_mail(email)
        return jsonify({'message':'Anuncio aceito com sucesso!'})
    
    if status == 'refused':
        db.execute('DELETE FROM ANNOUNCEMENTS WHERE id = %s', (id,))
        mail.send_refused_mail(email)
        return jsonify({'message':'Anuncio deletado com sucesso!'})
    
@app.route("/verify_type", methods=['GET'])
def verify_type():
    token = request.headers.get('Authorization').strip('"')
    payload = verify_jwt_token(token)

    if payload.get('tipo') == 'customer':
        return jsonify({'type':'customer'}), 200
    else:
        return jsonify({'type':'admin'}), 200

    
    
if __name__ == '__main__':
    app.run(debug=True)

