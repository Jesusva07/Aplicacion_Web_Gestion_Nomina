"""
app/routes/main.py — Blueprint principal (raíz y dashboard).

Endpoints:
  GET / → Redirige al dashboard (o login si no autenticado).
  GET /dashboard → Panel principal del empleado.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timezone

import pytz

from app.models import Attendance, Employee

main_bp = Blueprint("main", __name__, template_folder="../templates")

BOGOTA_TZ = pytz.timezone("America/Bogota")


@main_bp.route("/")
def index():
    """Ruta raíz — redirige según estado de autenticación."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Panel principal del empleado.
    
    Muestra:
    - Hora actual en Bogotá.
    - Estado actual (¿ya marcó entrada hoy?).
    - Botón de clock-in o clock-out según el estado.
    - Últimas 5 asistencias del empleado.
    """
    now_bogota = datetime.now(BOGOTA_TZ)
    today_start = now_bogota.replace(hour=0, minute=0, second=0, microsecond=0)

    # Obtener perfil de empleado asociado al usuario actual
    employee = None
    open_attendance = None
    recent_attendances = []

    if current_user.employee:
        employee = current_user.employee

        # Buscar si hay un registro abierto (sin clock_out) hoy
        open_attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            status="open"
        ).order_by(Attendance.clock_in.desc()).first()

        # Últimas 5 asistencias (cerradas) para el historial
        recent_attendances = (
            Attendance.query
            .filter_by(employee_id=employee.id, status="closed")
            .order_by(Attendance.clock_in.desc())
            .limit(5)
            .all()
        )

    return render_template(
        "dashboard.html",
        employee=employee,
        open_attendance=open_attendance,
        recent_attendances=recent_attendances,
        now_bogota=now_bogota,
    )
