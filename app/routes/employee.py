"""
app/routes/employee.py — Blueprint de gestión de empleados (admin).

Endpoints:
  GET  /employees/          → Lista todos los empleados activos.
  GET  /employees/new       → Formulario para crear empleado.
  POST /employees/new       → Crea nuevo empleado + cuenta de usuario.
  GET  /employees/<id>      → Detalle del empleado.
  POST /employees/<id>/edit → Edita datos del empleado.
  POST /employees/<id>/deactivate → Desactiva el empleado.
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request
)
from flask_login import login_required, current_user
from functools import wraps

from app.extensions import db
from app.models import User, Employee

employee_bp = Blueprint("employee", __name__, template_folder="../templates")


def admin_required(f):
    """
    Decorador que restringe el acceso a usuarios con rol 'admin'.
    Retorna 403 si el usuario no es administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Acceso denegado. Se requieren permisos de administrador.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated_function


@employee_bp.route("/")
@login_required
@admin_required
def list_employees():
    """Lista todos los empleados con opción de filtrar por estado."""
    show_inactive = request.args.get("show_inactive", "false") == "true"

    query = Employee.query
    if not show_inactive:
        query = query.filter_by(is_active=True)

    employees = query.order_by(Employee.name).all()

    return render_template(
        "employees/list.html",
        employees=employees,
        show_inactive=show_inactive
    )


@employee_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_employee():
    """
    Crea un nuevo empleado y su cuenta de usuario asociada.
    
    El formulario recopila tanto datos laborales (salary, role) como
    credenciales de acceso (email, password).
    """
    if request.method == "POST":
        # Extraer datos del formulario
        name = request.form.get("name", "").strip()
        document_id = request.form.get("document_id", "").strip()
        role = request.form.get("role", "").strip()
        base_salary = request.form.get("base_salary", "0")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validaciones básicas
        errors = []
        if not all([name, document_id, role, email, password]):
            errors.append("Todos los campos son obligatorios.")
        if Employee.query.filter_by(document_id=document_id).first():
            errors.append(f"Ya existe un empleado con cédula {document_id}.")
        if User.query.filter_by(email=email).first():
            errors.append(f"Ya existe una cuenta con el correo {email}.")

        try:
            salary = float(base_salary)
            if salary <= 0:
                errors.append("El salario base debe ser mayor a 0.")
        except ValueError:
            errors.append("El salario base debe ser un número válido.")
            salary = 0.0

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("employees/new.html")

        # Crear cuenta de usuario
        user = User(email=email, role="employee")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Obtener el ID del usuario antes de commit

        # Crear perfil de empleado vinculado al usuario
        employee = Employee(
            name=name,
            document_id=document_id,
            role=role,
            base_salary=salary,
            user_id=user.id
        )
        db.session.add(employee)
        db.session.commit()

        flash(
            f"✅ Empleado '{name}' creado exitosamente. "
            f"Puede iniciar sesión con {email}.",
            "success"
        )
        return redirect(url_for("employee.list_employees"))

    return render_template("employees/new.html")


@employee_bp.route("/<int:employee_id>")
@login_required
@admin_required
def detail(employee_id: int):
    """Muestra el detalle completo de un empleado."""
    employee = db.get_or_404(Employee, employee_id)
    return render_template("employees/detail.html", employee=employee)


@employee_bp.route("/<int:employee_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def deactivate(employee_id: int):
    """Desactiva un empleado (soft delete — no elimina el registro)."""
    employee = db.get_or_404(Employee, employee_id)
    employee.is_active = False
    if employee.user:
        employee.user.is_active = False
    db.session.commit()
    flash(f"Empleado '{employee.name}' desactivado.", "warning")
    return redirect(url_for("employee.list_employees"))
