from dotenv import load_dotenv
import os

load_dotenv()  # Carrega o arquivo .env por padrão

class Config:
    SECRET_KEY = os.urandom(24)
    JWT_SECRET_KEY = os.urandom(32).hex()


    #MYSQL CONFIG
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = 'ANUNCIAUFC'


    CORS_HEADERS = 'Content-Type'

    #SECRET_KEY = 'chave'

    
    #MAIL CONFIG
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'anunciaufc@gmail.com'  # Insira seu e-mail
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')  # Insira sua senha ou app password
    MAIL_DEFAULT_SENDER = 'anunciaufc@gmail.com'