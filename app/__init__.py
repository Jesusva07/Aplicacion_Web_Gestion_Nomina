"""
app/__init__.py — Application Factory de Flask.

El patrón Application Factory (create_app) permite:
  1. Crear múltiples instancias de la app con distintas configuraciones.
  2. Evitar importaciones circulares al inicializar extensiones sin app.
  3. Facilitar las pruebas unitarias con configuración de testing.
"""

import os
from flask import Flask

from config import config_map
from app.extensions import db, migrate, login_manager


def create_app(config_name: str | None = None) -> Flask:
    """
    Factory que construye y configura la instancia de Flask.

    Args:
        config_name: Nombre del entorno ('development', 'production', 'testing').
                     Si es None, usa la variable de entorno FLASK_ENV o 'development'.

    Returns:
        Instancia de Flask completamente configurada.
    """
    app = Flask(__name__)

    # ----------------------------------------------------------------
    # 1. Carga de configuración
    # ----------------------------------------------------------------
    # Determina el entorno: parámetro > variable de entorno > defecto
    env = config_name or os.environ.get("FLASK_ENV", "development")
    config_class = config_map.get(env, config_map["default"])
    app.config.from_object(config_class)

    # ----------------------------------------------------------------
    # 2. Inicialización de extensiones
    # ----------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ----------------------------------------------------------------
    # 3. Registro del user_loader para Flask-Login
    # ----------------------------------------------------------------
    # Flask-Login necesita saber cómo cargar un usuario desde su ID
    # almacenado en la sesión.
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Carga el usuario por su PK para la sesión de Flask-Login."""
        return db.session.get(User, int(user_id))

    # ----------------------------------------------------------------
    # 4. Registro de Blueprints
    # ----------------------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.attendance import attendance_bp
    from app.routes.employee import employee_bp
    from app.routes.payroll import payroll_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(employee_bp, url_prefix="/employees")
    app.register_blueprint(payroll_bp, url_prefix="/payroll")

    # ----------------------------------------------------------------
    # 5. Registro de la ruta raíz (dashboard principal)
    # ----------------------------------------------------------------
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    # ----------------------------------------------------------------
    # 6. Creación de tablas en entorno de desarrollo (sin migraciones)
    # ----------------------------------------------------------------
    # En producción se usa: flask db upgrade
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app: Flask) -> None:
    """
    Crea el usuario administrador inicial si no existe.
    Credenciales tomadas de variables de entorno (.env).
    """
    from app.models import User

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@empresa.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    # Solo crea el admin si no existe ningún usuario en la tabla
    existing = User.query.filter_by(email=admin_email).first()
    if existing is None:
        admin = User(email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Admin inicial creado: {admin_email}")
