"""
tests/ — Suite de pruebas automatizadas para la aplicación TurnosPro.

Estructura:
  - unit/          Pruebas unitarias de modelos, servicios, utilidades.
  - integration/   Pruebas de integración entre componentes y rutas.
  - fixtures/      Datos de prueba compartidos (test data).

Ejecutar todas las pruebas:
  pytest

Ejecutar con cobertura:
  pytest --cov=app --cov-report=html

Ejecutar solo unitarias:
  pytest tests/unit/

Ejecutar con verbose:
  pytest -v

Ejecutar una prueba específica:
  pytest tests/unit/test_models.py::test_user_password_hashing
"""
