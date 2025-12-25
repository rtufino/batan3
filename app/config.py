import os
from dotenv import load_dotenv

# Determinamos la ruta base del proyecto para ubicar la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Llave secreta para firmar cookies y proteger contra CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-batan3-segura'
    
    # Configuración de Base de Datos
    # Prioridad: 1. Variable de Entorno (Prod) -> 2. SQLite local (Dev)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Desactivamos el rastreo de modificaciones de objetos para ahorrar memoria
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración opcional para mostrar SQL en consola (útil para debug)
    # SQLALCHEMY_ECHO = True

    # Se guardarán en app/static/uploads/mantenimiento
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads/mantenimiento')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de 16MB por subida para seguridad
    
    # --- CONFIGURACIÓN DE CORREO (Optimizada para Puerto 465) ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    
    # Forzamos la lectura de los valores del .env con tipos correctos
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    
    # Para puerto 465: TLS debe ser False y SSL debe ser True
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    MAIL_SUBJECT_PREFIX = '[EDIFICIO BATAN 3] '
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN')