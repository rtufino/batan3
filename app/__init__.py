from flask import Flask
from app.config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    # 1. Inicializar Flask
    app = Flask(__name__)
    
    # 2. Cargar configuración
    app.config.from_object(config_class)

    # 3. Inicializar extensiones con la app creada
    db.init_app(app)
    migrate.init_app(app, db)

    # 4. Registrar Blueprints (Rutas)
    # Nota: Los crearemos más adelante, por ahora dejo el espacio comentado
    # from app.routes.main import main_bp
    # app.register_blueprint(main_bp)

    # 5. Shell Context (Opcional)
    # Permite que al usar 'flask shell' ya tengas 'db' y 'app' importados
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'app': app}

    return app