from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

# Instanciamos el ORM y la herramienta de migración
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()