"""
app/extensions.py — Instancias de extensiones Flask (patrón de extensiones sin app).

Al separar las extensiones del factory, evitamos importaciones circulares.
Se inicializan sin app aquí y se vinculan al app en create_app() con .init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# ORM principal — instancia global sin app vinculada aún
db = SQLAlchemy()

# Gestión de migraciones de esquema de BD (Alembic bajo el capó)
migrate = Migrate()

# Gestor de sesiones de usuario y autenticación
login_manager = LoginManager()

# Redirección cuando se accede a una ruta @login_required sin autenticarse
login_manager.login_view = "auth.login"
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
login_manager.login_message_category = "warning"
