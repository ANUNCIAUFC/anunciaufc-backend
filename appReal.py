from flask import Flask, render_template, request, jsonify, session
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_bcrypt import Bcrypt
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

mysql = MySQL(app)
bcrypt = Bcrypt(app)


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
def raiz():
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
            'price': announcement[4],
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


@app.route('/users', methods=['GET'])
def listar_users():
    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT * FROM USERS")
    
    users = cursor.fetchall()

    cursor.close()

    return jsonify([
        {
            'idUser': user[0],
            'isAdmin': user[1],
            'email': user[2],
            'name': user[3],
            'telephone': user[4],
            'cpf': user[5],
            'campus': user[6],
            'gender': user[7]
        } for user in users
    ])

    
@app.route('/update_user', methods=['PUT'])
def update_user():
    try:
        if 'email' not in session:
            return jsonify({'message': 'Usuário não autenticado'}), 401

        email = session['email']
        
        token = request.headers.get('Authorization')

        data = request.get_json()

        cur = mysql.connection.cursor()

        cur.execute("SELECT name, telephone, email, cpf, campus, gender FROM USERS WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        payload = verify_jwt_token(token)
        
        if not payload:
            cur.close()
            return jsonify({'error': 'Token expirado ou inválido'}), 404
        
        name = data.get('name', user[0])
        telephone = data.get('telephone', user[1])
        cpf = data.get('cpf', user[3])
        campus = data.get('campus', user[4])
        gender = data.get('gender', user[5])

        cur.execute("""
            UPDATE USERS
            SET name = %s, telephone = %s, cpf = %s, campus = %s, gender = %s
            WHERE email = %s
        """, (name, telephone, cpf, campus, gender, email))
        
        mysql.connection.commit()
        cur.execute("SELECT * FROM USERS WHERE email = %s", (email,))
        user_update = cur.fetchone()
        cur.close()
        
        token_update = create_jwt_token(user_update)
        
        return jsonify({'message': 'Dados atualizados com sucesso!',
                        'token': token_update}), 200 #envio o novo token com as informações atualizadas
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        

@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    if 'email' not in session:
        return jsonify({'message': 'Usuário não autenticado'}), 401

    email_usuario = session['email']
    
    token = request.headers.get('Authorization')
    
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({'error': 'Token expirado ou inválido'}), 404

    cur = mysql.connection.cursor()

    query = "DELETE FROM USERS WHERE email=%s"
    values = (email_usuario,)

    cur.execute(query, values)
    mysql.connection.commit()
    cur.close()

    session.pop('email', None)

    return jsonify({'message': 'Conta excluída com sucesso!'}), 200


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


@app.route('/logout', methods=['POST'])
def logout():
    if 'email' not in session:
        return jsonify({'message': 'Usuário não autenticado'}), 401

    session.pop('email', None)

    return jsonify({'message': 'Logout realizado com sucesso!'}), 200


@app.route('/anuncio', methods=['POST'])
def criar_anuncio():
    if 'email' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401

    data = request.get_json()
    cursor = mysql.connection.cursor()

    title = data['title']
    category = data['category']
    campus = data['campus']
    value = data['value']
    stateProduct = data['stateProduct']
    description = data['description']
    image = data['image']
    validation = data.get('validation', 0)

    user_email = session['email']

    cursor.execute(''' 
        INSERT INTO Anuncios (title, category, campus, value, stateProduct, description, image, validation, user_email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (title, category, campus, value, stateProduct, description, image, validation, user_email))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Anúncio criado com sucesso!'}), 201


@app.route('/anuncios', methods=['GET'])
def listar_anuncios():
    if 'email' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401

    email = session['email']

    try:
        cursor = mysql.connection.cursor()

        cursor.execute('SELECT * FROM Anuncios WHERE user_email = %s', (email,))
        result = cursor.fetchall()
        cursor.close()

        if not result:
            return jsonify({'message': 'Nenhum anúncio encontrado'}), 404

        anuncios = []
        for row in result:
            anuncio = {
                'idAnnouncement': row[0],
                'title': row[1],
                'category': row[2],
                'campus': row[3],
                'value': row[4],
                'stateProduct': row[5],
                'description': row[6],
                'validation': row[8]
            }

            if row[7]:
                try:
                    anuncio['image'] = base64.b64encode(row[7]).decode('utf-8')
                except Exception as e:
                    print("Erro ao converter imagem para base64:", e)
                    anuncio['image'] = None
            else:
                anuncio['image'] = None
            anuncios.append(anuncio)

        return jsonify(anuncios), 200

    except Exception as e:
        print("Erro ao listar anúncios:", e)
        return jsonify({'error': f'Erro ao listar anúncios: {str(e)}'}), 500

@app.route('/update_announcement', methods=['PUT'])
def atualizar_anuncio():
    if 'email' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401

    data = request.get_json()
    cursor = mysql.connection.cursor()

    email = session['email'] 
    idAnnouncement = data.get('idAnnouncement')

    if not idAnnouncement:
        return jsonify({'error': 'O identificador do anúncio é necessário'}), 400

    cursor.execute('SELECT * FROM Anuncios WHERE idAnnouncement = %s AND user_email = %s', (idAnnouncement, email))
    result = cursor.fetchone()

    if not result:
        return jsonify({'error': 'Anúncio não encontrado ou você não tem permissão para modificá-lo'}), 403

    title = data.get('title', result[1])
    category = data.get('category', result[2])
    campus = data.get('campus', result[3])
    value = data.get('value', result[4])
    stateProduct = data.get('stateProduct', result[5])
    description = data.get('description', result[6])
    image = data.get('image', result[7])
    validation = data.get('validation', result[8])

    cursor.execute('''
        UPDATE Anuncios
        SET title = %s, category = %s, campus = %s, value = %s, stateProduct = %s, 
            description = %s, image = %s, validation = %s
        WHERE idAnnouncement = %s AND user_email = %s
    ''', (title, category, campus, value, stateProduct, description, image, validation, idAnnouncement, email))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Anúncio atualizado com sucesso!'}), 200


@app.route('/deletar', methods=['DELETE'])
def deletar_anuncio():
    if 'email' not in session: 
        return jsonify({'error': 'Usuário não autenticado'}), 401

    data = request.get_json()
    cursor = mysql.connection.cursor()

    email = session['email']
    idAnnouncement = data['idAnnouncement']

    cursor.execute('SELECT * FROM Anuncios WHERE idAnnouncement = %s AND user_email = %s', (idAnnouncement, email))
    result = cursor.fetchone()

    if not result:
        return jsonify({'error': 'Anúncio não encontrado ou você não tem permissão para deletá-lo'}), 403

    cursor.execute('DELETE FROM Anuncios WHERE idAnnouncement = %s AND user_email = %s', (idAnnouncement, email))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Anúncio deletado com sucesso!'}), 200


# Iniciar o servidor
if __name__ == '__main__':
    app.run(debug=True)

    