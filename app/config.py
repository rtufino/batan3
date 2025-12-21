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

    # Se guardarán en app/static/uploads/mantenimiento
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads/mantenimiento')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Límite de 16MB por subida para seguridad
    
    # Configuración de Flask-Mail
    # Para Gmail, necesitas habilitar "Acceso de apps menos seguras" o usar "Contraseñas de aplicación"
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Tu correo
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Tu contraseña o contraseña de aplicación
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@batan3.com'
    
    # Configuración adicional para notificaciones
    MAIL_SUBJECT_PREFIX = '[EDIFICIO BATAN 3] '
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN') or 'admin@batan3.com'