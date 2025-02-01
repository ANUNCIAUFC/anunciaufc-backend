import bcrypt
import firebase_admin #Biblioteca para adminstração do bd no fb
from firebase_admin import credentials, firestore, auth #cred para ter acesso as credenciais em js e db para interagir com realtime database
from flask import Flask, jsonify, request #fremeork flask

cred = credentials.Certificate("anunciaufc-firebase-adminsdk-3ohj7-ae16174503.json") #acesso as credenciais do proj no fire
firebase_admin.initialize_app(cred)

# Inicializar o cliente Firestore
db = firestore.client()

# Inicializa a aplicação Flask
app = Flask(__name__)

@app.route('/register', methods = ['POST', 'OPTIONS'])
def register():
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['email', 'password', 'name', 'telephone', 'cpf', 'campus', 'gender']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'}), 400

        
        email = data['email']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        name = data['name']
        telephone = data['telephone']
        cpf = data['cpf']
        campus = data['campus']
        gender = data['gender']
        
        # Adicionar dados em uma coleção 'usuarios'
        user = auth.create_user(
            email=email, 
            password=data['password']
            )

        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email': email,
            'password': password.decode('utf-8'),
            'name': name,
            'telephone': telephone,
            'cpf': cpf,
            'campus': campus,
            'gender': gender
        })

        # Retornar a resposta com o token
        return jsonify({
            'message': 'Registrado com Sucesso',
            }), 200
        
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Internal Server Error'}), 500
    
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        email = data['email']
        password = data['password']
    
        user = auth.get_user_by_email(email) 
        
        if user is None:
            return jsonify({'error': 'Email não cadastrado'}), 401
        
        user_ref = db.collection('users').document(user.uid)
        user_data = user_ref.get().to_dict()
        stored_password_hash = user_data.get('password')
        
        custom_token = auth.create_custom_token(user.uid)
        
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return jsonify({
                    'message': 'Login bem-sucedido',
                    'token': str(custom_token)
                }), 200
        else:
            return jsonify({'error': 'Senha incorreta'}), 401
        
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Internal Server Error'}), 500
    
@app.route('/update', methods=['POST'])
def update():
    try:
        # Obter o token da requisição (geralmente no cabeçalho Authorization)
        token = request.headers.get('Authorization')
        
        # Remover o prefixo 'Bearer ' se presente
        token = token.replace('Bearer ', '')
       
        # Verificar o token com o Firebase Admin SDK
        decodedToken = auth.verify_id_token(token) 
    
        if decodedToken is None:
                return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        # UID do usuário autenticado
        uid = decodedToken['uid']
        
        data = request.get_json()
        
        email = data['email']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        name = data['name']
        telephone = data['telephone']
        cpf = data['cpf']
        campus = data['campus']
        gender = data['gender']
        
        user_ref = db.collection('users').document(uid)
        user_ref.update({
            'email': email,
            'password': password.decode('utf-8'),
            'name': name,
            'telephone': telephone,
            'cpf': cpf,
            'campus': campus,
            'gender': gender
        })
        
        return jsonify({
                'message': 'Atualizado com Sucesso', 
                'token': token.decode('utf-8')
                }), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)


