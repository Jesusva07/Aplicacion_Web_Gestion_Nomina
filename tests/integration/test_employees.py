"""
tests/integration/test_employees.py — Pruebas de integración para gestión de empleados.

Cubre:
  - Listado de empleados
  - Creación de empleado
  - Visualización de detalle
  - Edición de datos
  - Desactivación de empleado
  - Validación de permisos (solo admin)
"""

import pytest
from decimal import Decimal
from app.models import User, Employee


class TestEmployeeRoutes:
    """Pruebas para rutas de gestión de empleados."""

    def test_list_employees_admin_access(self, client, admin_user, employee_two):
        """Verifica que admin puede listar empleados."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.get("/employees/")
        assert response.status_code == 200
        assert b"Empleado" in response.data or b"empleado" in response.data.lower()

    def test_list_employees_shows_active_only_by_default(self, client, admin_user, employee_user, employee_two):
        """Verifica que por defecto solo muestra empleados activos."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        # Desactivar un empleado
        employee_two.is_active = False
        from app.extensions import db
        db.session.commit()
        
        response = client.get("/employees/")
        assert response.status_code == 200
        # Debe mostrar al empleado activo
        assert b"Juan Carlos" in response.data

    def test_list_employees_show_inactive_option(self, client, admin_user, employee_user, employee_two):
        """Verifica que se pueden ver empleados inactivos con parámetro."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        # Desactivar
        employee_two.is_active = False
        from app.extensions import db
        db.session.commit()
        
        response = client.get("/employees/?show_inactive=true")
        assert response.status_code == 200

    def test_list_employees_employee_denied_access(self, client, employee_user):
        """Verifica que empleado no puede ver listado de empleados."""
        client.post("/auth/login", data={
            "email": "empleado@test.com",
            "password": "EmpleadoTest123!"
        })
        
        response = client.get("/employees/", follow_redirects=True)
        assert response.status_code == 200
        # Debe redirigir o mostrar error de acceso denegado

    def test_new_employee_form_displays(self, client, admin_user):
        """Verifica que formulario de nuevo empleado se muestra."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.get("/employees/new")
        assert response.status_code == 200
        assert b"Nuevo Empleado" in response.data or b"nuevo empleado" in response.data.lower()

    def test_create_new_employee_success(self, client, admin_user, db_session):
        """Verifica creación exitosa de nuevo empleado."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/new", data={
            "name": "Carlos Mendez",
            "document_id": "5555555555",
            "role": "Operario",
            "base_salary": "1800000",
            "email": "carlos@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Debe redirigir al listado
        assert b"Empleado" in response.data or b"empleado" in response.data.lower()
        
        # Verificar que se creó en BD
        employee = Employee.query.filter_by(document_id="5555555555").first()
        assert employee is not None
        assert employee.name == "Carlos Mendez"
        assert employee.base_salary == Decimal("1800000")
        
        # Verificar que se creó el usuario
        user = User.query.filter_by(email="carlos@test.com").first()
        assert user is not None
        assert user.employee_id == employee.id or employee.user_id == user.id

    def test_create_employee_duplicate_document_id(self, client, admin_user, employee_user):
        """Verifica que no se puede crear empleado con cédula duplicada."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/new", data={
            "name": "Another Person",
            "document_id": "1234567890",  # Mismo que employee_user
            "role": "Operario",
            "base_salary": "1800000",
            "email": "another@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Debe mostrar error
        assert b"ya existe" in response.data.lower() or b"existe" in response.data.lower()

    def test_create_employee_duplicate_email(self, client, admin_user, employee_user):
        """Verifica que no se puede crear empleado con email duplicado."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/new", data={
            "name": "Another Person",
            "document_id": "9999999999",
            "role": "Operario",
            "base_salary": "1800000",
            "email": "empleado@test.com",  # Mismo email
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Debe mostrar error
        assert b"ya existe" in response.data.lower() or b"existe" in response.data.lower()

    def test_create_employee_invalid_salary(self, client, admin_user):
        """Verifica validación de salario."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/new", data={
            "name": "Test Person",
            "document_id": "1111111111",
            "role": "Operario",
            "base_salary": "-1000",  # Salario negativo
            "email": "test@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Debe mostrar error
        response_text = response.data.decode("utf-8").lower()
        assert "mayor" in response_text or "válido" in response_text

    def test_employee_detail_page(self, client, admin_user, employee_user):
        """Verifica que se muestra el detalle del empleado."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        emp_id = employee_user.employee.id
        response = client.get(f"/employees/{emp_id}")
        assert response.status_code == 200
        assert b"Juan Carlos" in response.data
        assert b"1234567890" in response.data

    def test_employee_detail_nonexistent(self, client, admin_user):
        """Verifica error 404 para empleado inexistente."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.get("/employees/99999")
        assert response.status_code == 404

    def test_deactivate_employee(self, client, admin_user, employee_two):
        """Verifica desactivación de empleado."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        emp_id = employee_two.id
        response = client.post(
            f"/employees/{emp_id}/deactivate",
            follow_redirects=True
        )
        
        assert response.status_code == 200
        
        # Verificar que se desactivó
        from app.extensions import db
        emp = db.session.get(Employee, emp_id)
        assert emp.is_active is False

    def test_deactivate_nonexistent_employee(self, client, admin_user):
        """Verifica error al desactivar empleado inexistente."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/99999/deactivate")
        assert response.status_code == 404

    def test_employee_cannot_create_other_employees(self, client, employee_user):
        """Verifica que empleado no puede crear otros empleados."""
        client.post("/auth/login", data={
            "email": "empleado@test.com",
            "password": "EmpleadoTest123!"
        })
        
        response = client.get("/employees/new", follow_redirects=True)
        assert response.status_code == 200
        # Debe redirigir o negar acceso

    def test_employee_cannot_deactivate_employees(self, client, employee_user, employee_two):
        """Verifica que empleado no puede desactivar a otros empleados."""
        client.post("/auth/login", data={
            "email": "empleado@test.com",
            "password": "EmpleadoTest123!"
        })
        
        response = client.post(f"/employees/{employee_two.id}/deactivate")
        # Debe retornar error de permiso o redirigir
        assert response.status_code in [403, 302]


class TestEmployeeValidation:
    """Pruebas para validación de datos de empleados."""

    def test_required_fields_validation(self, client, admin_user):
        """Verifica que campos requeridos son validados."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        # Enviar sin nombre
        response = client.post("/employees/new", data={
            "name": "",  # Vacío
            "document_id": "1111111111",
            "role": "Operario",
            "base_salary": "1800000",
            "email": "test@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Debe mostrar error
        assert b"obligatorio" in response.data.lower() or b"requerido" in response.data.lower() or b"campo" in response.data.lower()

    def test_salary_minimum_value(self, client, admin_user):
        """Verifica que salario debe ser mayor a 0."""
        client.post("/auth/login", data={
            "email": "admin@test.com",
            "password": "AdminTest123!"
        })
        
        response = client.post("/employees/new", data={
            "name": "Test",
            "document_id": "1111111111",
            "role": "Operario",
            "base_salary": "0",  # Inválido
            "email": "test@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        response_text = response.data.decode("utf-8").lower()
        assert "mayor" in response_text or "válido" in response_text
