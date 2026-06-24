"""
tests/unit/test_models.py — Pruebas unitarias para modelos de base de datos.

Cubre:
  - User: Creación, hash de contraseña, propiedades
  - Employee: Cálculo de valor-hora, validaciones
  - Shift: Duración, relaciones
  - Attendance: Cálculo de horas trabajadas
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
import pytz

from app.models import User, Employee, Shift, Attendance
from app.extensions import db


class TestUserModel:
    """Pruebas para el modelo User."""

    def test_user_creation(self, db_session, admin_user):
        """Verifica que un usuario se cree correctamente."""
        assert admin_user.id is not None
        assert admin_user.email == "admin@test.com"
        assert admin_user.role == "admin"
        assert admin_user.is_active is True

    def test_user_password_hashing(self, db_session):
        """Verifica que las contraseñas se hasheen correctamente."""
        user = User(email="test@example.com", role="employee")
        password = "MiPassword123!"
        user.set_password(password)
        
        # La contraseña no se almacena en texto plano
        assert user.password_hash != password
        # Pero se puede validar correctamente
        assert user.check_password(password) is True
        # Contraseña incorrecta retorna False
        assert user.check_password("IncorrectPassword") is False

    def test_user_is_admin_property(self, db_session):
        """Verifica la propiedad is_admin."""
        admin = User(email="admin@test.com", role="admin")
        employee = User(email="emp@test.com", role="employee")
        
        assert admin.is_admin is True
        assert employee.is_admin is False

    def test_user_email_uniqueness(self, db_session, admin_user):
        """Verifica que los emails deben ser únicos."""
        duplicate = User(email="admin@test.com", role="employee")
        duplicate.set_password("Password123!")
        db_session.add(duplicate)
        
        # Lanzar excepción de integridad
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_repr(self, admin_user):
        """Verifica la representación en string del usuario."""
        repr_str = repr(admin_user)
        assert "User" in repr_str
        assert "admin@test.com" in repr_str
        assert "admin" in repr_str


class TestEmployeeModel:
    """Pruebas para el modelo Employee."""

    def test_employee_creation(self, db_session, employee_user):
        """Verifica la creación correcta de un empleado."""
        emp = employee_user.employee
        assert emp.id is not None
        assert emp.name == "Juan Carlos Pérez"
        assert emp.document_id == "1234567890"
        assert emp.role == "Operario"
        assert emp.base_salary == Decimal("1500000.00")
        assert emp.is_active is True
        assert emp.user_id == employee_user.id

    def test_hourly_rate_calculation(self, db_session, employee_user):
        """
        Verifica el cálculo del valor-hora según normativa colombiana.
        Fórmula: salario_mensual / (4.33 semanas * 42 horas)
        """
        emp = employee_user.employee
        # Salario: 1,500,000 COP/mes
        # Valor-hora: 1,500,000 / (4.33 * 42) = 8,246.64 COP
        expected_rate = 1500000 / (4.33 * 42)
        
        assert abs(emp.hourly_rate - expected_rate) < 0.01

    def test_hourly_rate_different_salaries(self, db_session):
        """Verifica cálculo de valor-hora con diferentes salarios."""
        # Empleado 1: SMMLV colombiano (~1,300,000)
        emp1 = Employee(
            name="Empleado 1",
            document_id="111",
            role="Operario",
            base_salary=Decimal("1300000.00")
        )
        
        # Empleado 2: Salario más alto (~3,000,000)
        emp2 = Employee(
            name="Empleado 2",
            document_id="222",
            role="Supervisor",
            base_salary=Decimal("3000000.00")
        )
        
        # Verificar proporcionalidad
        ratio = emp2.hourly_rate / emp1.hourly_rate
        expected_ratio = 3000000 / 1300000
        assert abs(ratio - expected_ratio) < 0.01

    def test_employee_document_id_uniqueness(self, db_session, employee_user):
        """Verifica que la cédula debe ser única."""
        duplicate = Employee(
            name="Otro Empleado",
            document_id="1234567890",  # Mismo que employee_user
            role="Supervisor",
            base_salary=Decimal("2000000.00")
        )
        db_session.add(duplicate)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_employee_repr(self, employee_user):
        """Verifica la representación en string del empleado."""
        emp = employee_user.employee
        repr_str = repr(emp)
        assert "Employee" in repr_str
        assert "1234567890" in repr_str

    def test_employee_is_active_default(self, db_session):
        """Verifica que por defecto los empleados están activos."""
        emp = Employee(
            name="Nuevo Empleado",
            document_id="999",
            role="Operario",
            base_salary=Decimal("1500000.00")
        )
        db_session.add(emp)
        db_session.commit()
        
        assert emp.is_active is True


class TestShiftModel:
    """Pruebas para el modelo Shift (turno programado)."""

    def test_shift_creation(self, db_session, shift_morning):
        """Verifica la creación correcta de un turno."""
        assert shift_morning.id is not None
        assert shift_morning.shift_type == "Morning"
        assert shift_morning.start_time is not None
        assert shift_morning.end_time is not None

    def test_shift_duration_hours(self, db_session, shift_morning):
        """Verifica el cálculo de duración del turno."""
        # Turno matutino: 6:00 - 14:00 = 8 horas
        duration = shift_morning.duration_hours
        assert abs(duration - 8.0) < 0.01

    def test_shift_night_duration(self, db_session, shift_night):
        """Verifica duración de turno nocturno (21:00 - 6:00 = 9 horas)."""
        duration = shift_night.duration_hours
        assert abs(duration - 9.0) < 0.01

    def test_shift_repr(self, shift_morning):
        """Verifica la representación en string del turno."""
        repr_str = repr(shift_morning)
        assert "Shift" in repr_str
        assert "Morning" in repr_str

    def test_shift_types(self, db_session, employee_user):
        """Verifica que se puedan crear turnos de diferentes tipos."""
        bogota_tz = pytz.timezone("America/Bogota")
        
        for shift_type in ["Morning", "Afternoon", "Night"]:
            start = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
            end = bogota_tz.localize(datetime(2024, 1, 15, 14, 0, 0)).astimezone(pytz.UTC)
            
            shift = Shift(
                employee_id=employee_user.employee.id,
                start_time=start,
                end_time=end,
                shift_type=shift_type
            )
            db_session.add(shift)
        
        db_session.commit()
        
        # Verificar que todos se crearon
        shifts = Shift.query.all()
        assert len(shifts) == 3


class TestAttendanceModel:
    """Pruebas para el modelo Attendance (asistencia registrada)."""

    def test_attendance_creation(self, db_session, attendance_normal):
        """Verifica la creación correcta de un registro de asistencia."""
        assert attendance_normal.id is not None
        assert attendance_normal.clock_in is not None
        assert attendance_normal.clock_out is not None
        assert attendance_normal.status == "completed"

    def test_total_hours_worked_normal(self, attendance_normal):
        """Verifica cálculo de horas trabajadas (8 horas normales)."""
        hours = attendance_normal.total_hours_worked
        assert abs(hours - 8.0) < 0.01

    def test_total_hours_worked_overtime(self, attendance_overtime):
        """Verifica cálculo de horas trabajadas con extras (12 horas)."""
        hours = attendance_overtime.total_hours_worked
        assert abs(hours - 12.0) < 0.01

    def test_total_hours_worked_none_when_no_checkout(self, db_session, employee_user):
        """Verifica que retorna None si el empleado no ha marcado salida."""
        bogota_tz = pytz.timezone("America/Bogota")
        clock_in = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
        
        attendance = Attendance(
            employee_id=employee_user.employee.id,
            clock_in=clock_in,
            clock_out=None,  # Sin salida
            status="in_progress"
        )
        db_session.add(attendance)
        db_session.commit()
        
        assert attendance.total_hours_worked is None

    def test_attendance_night_hours(self, attendance_night):
        """Verifica cálculo de horas nocturnas (21:00 - 6:00 = 9 horas)."""
        hours = attendance_night.total_hours_worked
        assert abs(hours - 9.0) < 0.01

    def test_attendance_repr(self, attendance_normal):
        """Verifica la representación en string de asistencia."""
        repr_str = repr(attendance_normal)
        assert "Attendance" in repr_str
        assert "completed" in repr_str

    def test_attendance_status_values(self, db_session, employee_user):
        """Verifica que se pueden crear asistencias con diferentes estados."""
        bogota_tz = pytz.timezone("America/Bogota")
        clock_in = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
        
        for status in ["completed", "in_progress", "late", "early_checkout"]:
            attendance = Attendance(
                employee_id=employee_user.employee.id,
                clock_in=clock_in,
                clock_out=None,
                status=status
            )
            db_session.add(attendance)
        
        db_session.commit()
        
        attendances = Attendance.query.all()
        assert len(attendances) == 4


class TestModelRelationships:
    """Pruebas para las relaciones entre modelos."""

    def test_user_employee_relationship(self, db_session, employee_user):
        """Verifica la relación 1:1 entre User y Employee."""
        user = employee_user
        emp = user.employee
        
        assert emp is not None
        assert emp.user_id == user.id
        assert user.employee.id == emp.id

    def test_employee_shifts_relationship(self, db_session, employee_user, shift_morning, shift_night):
        """Verifica la relación 1:N entre Employee y Shift."""
        emp = employee_user.employee
        shifts = emp.shifts.all()
        
        assert len(shifts) == 2
        assert shift_morning in shifts
        assert shift_night in shifts

    def test_employee_attendances_relationship(self, db_session, employee_user, attendance_normal, attendance_overtime):
        """Verifica la relación 1:N entre Employee y Attendance."""
        emp = employee_user.employee
        attendances = emp.attendances.all()
        
        assert len(attendances) == 2
        assert attendance_normal in attendances
        assert attendance_overtime in attendances

    def test_cascade_delete_employee(self, db_session, employee_user, shift_morning, attendance_normal):
        """Verifica que al eliminar un empleado se eliminan sus turnos y asistencias."""
        emp_id = employee_user.employee.id
        
        # Verificar que existen datos relacionados
        assert Shift.query.filter_by(employee_id=emp_id).count() == 1
        assert Attendance.query.filter_by(employee_id=emp_id).count() == 1
        
        # Eliminar el empleado
        db_session.delete(employee_user.employee)
        db_session.commit()
        
        # Verificar cascade delete
        assert Shift.query.filter_by(employee_id=emp_id).count() == 0
        assert Attendance.query.filter_by(employee_id=emp_id).count() == 0
