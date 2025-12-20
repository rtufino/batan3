import os

# Determinamos la ruta base del proyecto para ubicar la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Llave secreta para firmar cookies y proteger contra CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-batan3-segura'
    
    # Configuración de Base de Datos
    # Prioridad: 1. Variable de Entorno (Prod) -> 2. SQLite local (Dev)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'batan3.db')
    
    # Desactivamos el rastreo de modificaciones de objetos para ahorrar memoria
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración opcional para mostrar SQL en consola (útil para debug)
    # SQLALCHEMY_ECHO = True