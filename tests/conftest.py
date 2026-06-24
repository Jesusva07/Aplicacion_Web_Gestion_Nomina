"""
tests/conftest.py — Configuración global de pytest y fixtures compartidas.

Proporciona:
  - Instancia de aplicación Flask configurada para testing.
  - Cliente HTTP para hacer peticiones.
  - Base de datos temporal aislada por prueba.
  - Fixtures de usuarios y empleados de prueba.

Patrón: Cada prueba obtiene una base de datos limpia y aislada.
"""

import pytest
import os
from datetime import datetime
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import User, Employee, Shift, Attendance
import pytz

BOGOTA_TZ = pytz.timezone("America/Bogota")


@pytest.fixture(scope="session")
def app():
    """
    Crea la instancia de aplicación para toda la sesión de pruebas.
    Configurada en modo testing con base de datos en memoria (SQLite).
    """
    app = create_app(config_name="testing")
    
    # Configuración adicional para testing
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    
    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Cliente HTTP para realizar peticiones a la aplicación.
    Se reinicia antes de cada prueba.
    """
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        yield app.test_client()
        # Limpiar después de la prueba
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Sesión de base de datos aislada para pruebas unitarias.
    Permite acceso directo a la BD sin hacer peticiones HTTP.
    """
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def admin_user(db_session):
    """
    Crea un usuario administrador de prueba.
    
    Credenciales:
      - Email: admin@test.com
      - Password: AdminTest123!
      - Rol: admin
    """
    admin = User(
        email="admin@test.com",
        role="admin",
        is_active=True
    )
    admin.set_password("AdminTest123!")
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def employee_user(db_session):
    """
    Crea un usuario empleado de prueba con perfil de empleado.
    
    Credenciales:
      - Email: empleado@test.com
      - Password: EmpleadoTest123!
      - Rol: employee
    """
    user = User(
        email="empleado@test.com",
        role="employee",
        is_active=True
    )
    user.set_password("EmpleadoTest123!")
    db_session.add(user)
    db_session.flush()  # Obtener el ID antes de crear el Employee
    
    employee = Employee(
        name="Juan Carlos Pérez",
        document_id="1234567890",
        role="Operario",
        base_salary=Decimal("1500000.00"),  # 1.5M COP/mes
        is_active=True,
        user_id=user.id
    )
    db_session.add(employee)
    db_session.commit()
    
    # Refrescar para obtener relaciones
    user.employee = employee
    return user


@pytest.fixture
def employee_two(db_session):
    """
    Crea un segundo empleado para pruebas de listados.
    Sin usuario asociado (solo perfil de empleado).
    """
    employee = Employee(
        name="María González López",
        document_id="9876543210",
        role="Supervisor",
        base_salary=Decimal("2000000.00"),  # 2M COP/mes
        is_active=True,
        user_id=None
    )
    db_session.add(employee)
    db_session.commit()
    return employee


@pytest.fixture
def shift_morning(db_session, employee_user):
    """
    Crea un turno matutino programado (6:00 - 14:00).
    Zona: America/Bogota (UTC-5).
    """
    # Crear fecha en Bogotá y convertir a UTC para almacenamiento
    bogota_tz = pytz.timezone("America/Bogota")
    naive_start = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0))
    naive_end = bogota_tz.localize(datetime(2024, 1, 15, 14, 0, 0))
    
    shift = Shift(
        employee_id=employee_user.employee.id,
        start_time=naive_start.astimezone(pytz.UTC),
        end_time=naive_end.astimezone(pytz.UTC),
        shift_type="Morning"
    )
    db_session.add(shift)
    db_session.commit()
    return shift


@pytest.fixture
def shift_night(db_session, employee_user):
    """
    Crea un turno nocturno programado (21:00 - 6:00 siguiente día).
    Zona: America/Bogota (UTC-5).
    Importante para probar recargos nocturnos.
    """
    bogota_tz = pytz.timezone("America/Bogota")
    naive_start = bogota_tz.localize(datetime(2024, 1, 15, 21, 0, 0))
    naive_end = bogota_tz.localize(datetime(2024, 1, 16, 6, 0, 0))
    
    shift = Shift(
        employee_id=employee_user.employee.id,
        start_time=naive_start.astimezone(pytz.UTC),
        end_time=naive_end.astimezone(pytz.UTC),
        shift_type="Night"
    )
    db_session.add(shift)
    db_session.commit()
    return shift


@pytest.fixture
def attendance_normal(db_session, employee_user):
    """
    Crea un registro de asistencia normal (8 horas trabajadas).
    Marca entrada 6:00 y salida 14:00.
    """
    bogota_tz = pytz.timezone("America/Bogota")
    clock_in = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
    clock_out = bogota_tz.localize(datetime(2024, 1, 15, 14, 0, 0)).astimezone(pytz.UTC)
    
    attendance = Attendance(
        employee_id=employee_user.employee.id,
        clock_in=clock_in,
        clock_out=clock_out,
        status="completed"
    )
    db_session.add(attendance)
    db_session.commit()
    return attendance


@pytest.fixture
def attendance_overtime(db_session, employee_user):
    """
    Crea un registro de asistencia con horas extras diurnas.
    Marca entrada 6:00 y salida 18:00 (12 horas = 4 extras).
    """
    bogota_tz = pytz.timezone("America/Bogota")
    clock_in = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
    clock_out = bogota_tz.localize(datetime(2024, 1, 15, 18, 0, 0)).astimezone(pytz.UTC)
    
    attendance = Attendance(
        employee_id=employee_user.employee.id,
        clock_in=clock_in,
        clock_out=clock_out,
        status="completed"
    )
    db_session.add(attendance)
    db_session.commit()
    return attendance


@pytest.fixture
def attendance_night(db_session, employee_user):
    """
    Crea un registro de asistencia nocturna.
    Marca entrada 21:00 y salida 6:00 siguiente día (9 horas).
    Importante para probar recargos nocturnos del 35%.
    """
    bogota_tz = pytz.timezone("America/Bogota")
    clock_in = bogota_tz.localize(datetime(2024, 1, 15, 21, 0, 0)).astimezone(pytz.UTC)
    clock_out = bogota_tz.localize(datetime(2024, 1, 16, 6, 0, 0)).astimezone(pytz.UTC)
    
    attendance = Attendance(
        employee_id=employee_user.employee.id,
        clock_in=clock_in,
        clock_out=clock_out,
        status="completed"
    )
    db_session.add(attendance)
    db_session.commit()
    return attendance


# ===================================================================
# HELPERS PARA PRUEBAS
# ===================================================================

def login_admin(client, admin_user):
    """
    Realiza login con credenciales de admin.
    Retorna el cliente autenticado.
    """
    client.post("/auth/login", data={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })
    return client


def login_employee(client, employee_user):
    """
    Realiza login con credenciales de empleado.
    Retorna el cliente autenticado.
    """
    client.post("/auth/login", data={
        "email": "empleado@test.com",
        "password": "EmpleadoTest123!"
    })
    return client
