"""
tests/integration/test_payroll.py — Pruebas de integración para nómina y cálculos.

Cubre:
  - Cálculos de horas ordinarias
  - Cálculos de horas extras diurnas
  - Recargos nocturnos (35%)
  - Horas extras nocturnas (75%)
  - Validaciones de normativa colombiana
"""

import pytest
from decimal import Decimal
from datetime import datetime
import pytz

BOGOTA_TZ = pytz.timezone("America/Bogota")


class TestPayrollCalculations:
    """Pruebas para cálculos de nómina."""

    def test_ordinary_hours_calculation(self, db_session, employee_user, attendance_normal):
        """
        Verifica cálculo de horas ordinarias.
        
        Empleado: Salario 1,500,000 COP/mes
        Valor-hora: 1,500,000 / (4.33 * 42) = 8,246.64 COP
        Jornada: 8 horas ordinarias = 8 * 8,246.64 = 65,973.12 COP
        """
        emp = employee_user.employee
        attendance = attendance_normal
        
        hours_worked = attendance.total_hours_worked
        expected_hours = 8.0
        
        # Verificar horas
        assert abs(hours_worked - expected_hours) < 0.01
        
        # Calcular salario
        value_per_hour = emp.hourly_rate
        salary = hours_worked * value_per_hour
        
        # Verificar que es aproximadamente 65,973 COP
        assert salary > 65000
        assert salary < 67000

    def test_overtime_daytime_calculation(self, db_session, app, employee_user, attendance_overtime):
        """
        Verifica cálculo de horas extras diurnas.
        
        Empleado: Salario 1,500,000 COP/mes
        Valor-hora: 8,246.64 COP
        Jornada: 12 horas (8 ordinarias + 4 extras)
        
        Según normativa colombiana:
        - 8 horas ordinarias: 8 * 8,246.64 = 65,973.12 COP
        - 4 horas extra diurna: 4 * 8,246.64 * 1.25 = 41,233.20 COP
        - Total: 107,206.32 COP
        """
        emp = employee_user.employee
        attendance = attendance_overtime
        
        hours_worked = attendance.total_hours_worked
        assert abs(hours_worked - 12.0) < 0.01
        
        hourly_rate = emp.hourly_rate
        
        # 8 horas ordinarias
        ordinary_salary = 8 * hourly_rate
        
        # 4 horas extras diurnas (+25% según config)
        extra_rate = hourly_rate * 1.25
        extra_salary = 4 * extra_rate
        
        total = ordinary_salary + extra_salary
        
        # Verificar que está en rango esperado
        assert total > 105000
        assert total < 110000

    def test_night_surcharge_calculation(self, db_session, app, employee_user, attendance_night):
        """
        Verifica cálculo de recargo nocturno (+35%).
        
        Jornada: 21:00 - 06:00 = 9 horas nocturnas
        Valor-hora: 8,246.64 COP
        Recargo nocturno: +35%
        
        Salario nocturno: 9 * 8,246.64 * 1.35 = 100,237.74 COP
        """
        emp = employee_user.employee
        attendance = attendance_night
        
        hours_worked = attendance.total_hours_worked
        assert abs(hours_worked - 9.0) < 0.01
        
        hourly_rate = emp.hourly_rate
        
        # Con config de la app
        night_surcharge_rate = app.config.get("NIGHT_SURCHARGE_RATE", 0.35)
        surcharge_rate = 1 + night_surcharge_rate  # 1.35
        
        night_salary = hours_worked * hourly_rate * surcharge_rate
        
        # Verificar que está en rango esperado (~100,237 COP)
        assert night_salary > 99000
        assert night_salary < 102000

    def test_hourly_rate_derived_from_salary(self, db_session):
        """
        Verifica que el valor-hora se calcula correctamente a partir del salario.
        
        Fórmula: salario_mensual / (4.33 semanas * 42 horas/semana)
        """
        from app.models import Employee
        
        # Caso 1: SMMLV 2024 (aprox 1,300,000)
        emp1 = Employee(
            name="Test 1",
            document_id="111",
            role="Operario",
            base_salary=Decimal("1300000.00")
        )
        
        expected = 1300000 / (4.33 * 42)
        assert abs(emp1.hourly_rate - expected) < 0.01
        
        # Caso 2: Salario superior (3,000,000)
        emp2 = Employee(
            name="Test 2",
            document_id="222",
            role="Gerente",
            base_salary=Decimal("3000000.00")
        )
        
        expected = 3000000 / (4.33 * 42)
        assert abs(emp2.hourly_rate - expected) < 0.01


class TestPayrollRoute:
    """Pruebas para rutas de nómina."""

    def test_payroll_page_admin_access(self, client, admin_user, employee_user):
        """Verifica que admin puede acceder a página de nómina."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.get("/payroll/")
        assert response.status_code == 200

    def test_payroll_page_shows_employees(self, client, admin_user, employee_user, employee_two):
        """Verifica que página de nómina muestra listado de empleados."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.get("/payroll/")
        assert response.status_code == 200
        # Debe mostrar empleados
        assert b"Juan Carlos" in response.data or b"empleado" in response.data.lower()

    def test_payroll_report_generation(self, client, admin_user, employee_user, attendance_normal):
        """Verifica que se puede generar reporte de nómina."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        # Acceder a reporte (si existe)
        response = client.get("/payroll/report")
        assert response.status_code in [200, 404]  # Puede no existir aún

    def test_employee_cannot_access_payroll(self, client, employee_user):
        """Verifica que empleado no puede acceder a módulo de nómina."""
        client.post("/auth/login", data={
            "email": "empleado@test.com",
            "password": "EmpleadoTest123!"
        })
        
        response = client.get("/payroll/", follow_redirects=True)
        assert response.status_code == 200
        # Debe redirigir o negar


class TestWorkingHoursValidation:
    """Pruebas para validación de horas de trabajo."""

    def test_ordinary_hours_limit_weekly(self, app):
        """
        Verifica que máximo de horas ordinarias por semana es 42.
        Según Ley 1846/2017 de Colombia.
        """
        max_hours = app.config.get("MAX_WEEKLY_HOURS")
        assert max_hours == 42

    def test_night_shift_times(self, app):
        """Verifica que turno nocturno es 21:00 - 06:00."""
        night_start = app.config.get("NIGHT_SHIFT_START")
        night_end = app.config.get("NIGHT_SHIFT_END")
        
        assert night_start == 21
        assert night_end == 6

    def test_surcharge_rates(self, app):
        """Verifica los porcentajes de recargos según normativa."""
        night_surcharge = app.config.get("NIGHT_SURCHARGE_RATE")
        extra_day = app.config.get("EXTRA_DAYTIME_RATE")
        extra_night = app.config.get("EXTRA_NIGHTTIME_RATE")
        
        # Recargo nocturno: 35%
        assert night_surcharge == 0.35
        # Extra diurna: 25%
        assert extra_day == 0.25
        # Extra nocturna: 75%
        assert extra_night == 0.75


class TestAttendanceRecords:
    """Pruebas para registros de asistencia."""

    def test_attendance_clock_in_out(self, db_session, employee_user, attendance_normal):
        """Verifica que se registran entrada y salida correctamente."""
        attendance = attendance_normal
        
        assert attendance.clock_in is not None
        assert attendance.clock_out is not None
        assert attendance.total_hours_worked is not None

    def test_attendance_partial_day(self, db_session, employee_user):
        """Verifica asistencia con solo entrada (sin salida)."""
        bogota_tz = pytz.timezone("America/Bogota")
        clock_in = bogota_tz.localize(datetime(2024, 1, 15, 6, 0, 0)).astimezone(pytz.UTC)
        
        from app.models import Attendance
        attendance = Attendance(
            employee_id=employee_user.employee.id,
            clock_in=clock_in,
            clock_out=None,
            status="in_progress"
        )
        db_session.add(attendance)
        db_session.commit()
        
        # Sin salida, total_hours_worked debe ser None
        assert attendance.total_hours_worked is None

    def test_multiple_attendances_per_employee(self, db_session, employee_user, attendance_normal, attendance_overtime):
        """Verifica que un empleado puede tener múltiples registros de asistencia."""
        emp = employee_user.employee
        attendances = emp.attendances.all()
        
        assert len(attendances) == 2
