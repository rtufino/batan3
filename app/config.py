import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Determinamos la ruta base del proyecto (un nivel arriba de app/)
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(basedir)  # Subir un nivel desde app/ a la raíz
load_dotenv(os.path.join(project_root, '.env'))

class Config:
    # Llave secreta para firmar cookies y proteger contra CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-batan3-segura'
    
    # Determinar el entorno de ejecución
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Generar código de compilación
    @classmethod
    def get_compilation_code(cls):
        # Primero intentamos obtener el hash de git
        git_hash = None
        try:
            # Intentar obtener el hash de git usando diferentes métodos
            git_methods = [
                # Método 1: Usando subprocess directamente
                lambda: subprocess.check_output(
                    ['git', 'rev-parse', '--short', 'HEAD'], 
                    cwd=project_root, 
                    stderr=subprocess.DEVNULL
                ).decode('ascii').strip(),
                
                # Método 2: Usando shell=True
                lambda: subprocess.check_output(
                    'git rev-parse --short HEAD', 
                    cwd=project_root, 
                    shell=True, 
                    stderr=subprocess.DEVNULL
                ).decode('ascii').strip(),
                
                # Método 3: Usando os.popen
                lambda: os.popen('git rev-parse --short HEAD').read().strip()
            ]
            
            # Probar cada método hasta que uno funcione
            for method in git_methods:
                try:
                    git_hash = method()
                    if git_hash:
                        break
                except Exception:
                    continue
        except Exception:
            git_hash = None
        
        # Obtener el entorno
        env = os.environ.get('FLASK_ENV', 'development').upper()
        
        # Si estamos en producción y no hay hash de git, usar información de despliegue
        if env == 'PRODUCTION':
            if git_hash:
                return f"PROD: {git_hash}"
            else:
                # Usar una combinación de fecha y hora para producción
                deployment_info = datetime.now().strftime('%Y%m%d%H%M')
                return f"PROD: {deployment_info}"
        
        # Para desarrollo, mantener el formato anterior
        if git_hash:
            return f"DEV: {git_hash}"
        else:
            return f"DEV: {datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Código de compilación
    COMPILATION_CODE = os.environ.get('COMPILATION_CODE') or get_compilation_code.__func__(None)
    
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
    
    MAIL_SUBJECT_PREFIX = '[EDIFICIO BATAN III] '
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN')