"""
run.py — Punto de entrada de la aplicación TurnosPro.

Uso:
    python run.py                  # Inicia el servidor de desarrollo
    flask run                      # Alternativa usando Flask CLI
    flask run --host=0.0.0.0       # Accesible desde la red local

Variables de entorno requeridas:
    FLASK_ENV: 'development' | 'production' | 'testing'
    SECRET_KEY: Clave secreta para sesiones
    DATABASE_URL: URI de conexión a la base de datos
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env antes de importar la app
load_dotenv()

from app import create_app

# Crear la instancia de la aplicación usando la variable de entorno FLASK_ENV
app = create_app()

if __name__ == "__main__":
    # Puerto por defecto: 5000 (o el que defina la variable PORT)
    port = int(os.environ.get("PORT", 5000))

    print(f"""
+--------------------------------------------------+
|         TurnosPro -- Sistema de Nomina           |
+--------------------------------------------------+
|  Entorno:   {os.environ.get('FLASK_ENV', 'development'):<36}|
|  DB:        {str(os.environ.get('DATABASE_URL', 'sqlite:///nomina_dev.db'))[:36]:<36}|
|  Servidor:  http://localhost:{port:<19}|
+--------------------------------------------------+
    """)


    app.run(
        host="0.0.0.0",
        port=port,
        debug=(os.environ.get("FLASK_ENV", "development") == "development"),
    )
