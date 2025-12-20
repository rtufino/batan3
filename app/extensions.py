from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instanciamos el ORM y la herramienta de migración
db = SQLAlchemy()
migrate = Migrate()