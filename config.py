"""
config.py — Clases de configuración para los entornos de la aplicación.

Patrón: Config base → subclases por entorno (Development, Production, Testing).
Se carga dinámicamente en create_app() según la variable FLASK_ENV.
"""

import os
from dotenv import load_dotenv

# Carga las variables del archivo .env en el entorno del proceso
load_dotenv()


class Config:
    """Configuración base compartida por todos los entornos."""

    # Clave secreta para firmar sesiones y tokens CSRF.
    # CRÍTICO: En producción debe ser larga, aleatoria y única.
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-insecure-key")

    # URI de conexión a la base de datos (SQLAlchemy).
    # Por defecto usa SQLite para desarrollo local.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///nomina_dev.db"
    )

    # Deshabilita el overhead del sistema de seguimiento de modificaciones de SQLAlchemy.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Zona horaria de la aplicación (normativa colombiana: UTC-5)
    TIMEZONE = os.environ.get("TIMEZONE", "America/Bogota")

    # --- Reglas de negocio (normativa colombiana Ley 1846/2017) ---
    # Máximo de horas ordinarias por semana
    MAX_WEEKLY_HOURS = 42

    # Hora de inicio de jornada nocturna (21:00)
    NIGHT_SHIFT_START = 21

    # Hora de fin de jornada nocturna (06:00)
    NIGHT_SHIFT_END = 6

    # Recargos sobre el valor de la hora ordinaria
    NIGHT_SURCHARGE_RATE = 0.35       # +35% hora nocturna ordinaria
    EXTRA_DAYTIME_RATE = 0.25         # +25% hora extra diurna
    EXTRA_NIGHTTIME_RATE = 0.75       # +75% hora extra nocturna


class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo local."""

    DEBUG = True
    TESTING = False

    # En desarrollo se muestra SQL en consola para depuración
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Configuración para entorno de producción."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    # En producción se exige que SECRET_KEY sea una variable de entorno real
    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "fallback-insecure-key":
            raise ValueError(
                "SECRET_KEY debe configurarse como variable de entorno en producción."
            )


class TestingConfig(Config):
    """Configuración para ejecución de pruebas automatizadas."""

    TESTING = True
    DEBUG = True

    # Usa base de datos en memoria para pruebas rápidas sin persistencia
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Deshabilita protección CSRF en formularios durante pruebas
    WTF_CSRF_ENABLED = False


# Mapa de entornos para carga dinámica en create_app()
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
