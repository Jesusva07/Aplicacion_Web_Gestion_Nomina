"""
app/routes/attendance.py — Blueprint de registro de asistencia (clock-in/clock-out).

Endpoints:
  POST /attendance/clock-in   → Registra la entrada del empleado.
  POST /attendance/clock-out  → Registra la salida del empleado.
  GET  /attendance/history    → Historial de asistencias del empleado.

IMPORTANTE: Las marcas de tiempo se toman del SERVIDOR (UTC),
nunca del cliente, para garantizar integridad temporal.
Luego se muestran convertidas a America/Bogota en el frontend.
"""

from datetime import datetime, timezone

from flask import Blueprint, redirect, url_for, flash, jsonify, request, render_template
from flask_login import login_required, current_user

import pytz

from app.extensions import db
from app.models import Attendance, Employee

attendance_bp = Blueprint("attendance", __name__, template_folder="../templates")

BOGOTA_TZ = pytz.timezone("America/Bogota")


def _get_employee_or_abort() -> Employee | None:
    """
    Retorna el Employee asociado al usuario actual.
    Flash error si el usuario no tiene perfil de empleado.
    """
    if not current_user.employee:
        flash(
            "Tu usuario no tiene un perfil de empleado asociado. "
            "Contacta al administrador.",
            "danger"
        )
        return None
    return current_user.employee


@attendance_bp.route("/clock-in", methods=["POST"])
@login_required
def clock_in():
    """
    Registra la entrada (clock-in) del empleado.

    Reglas:
    - Solo puede haber UN registro abierto por empleado a la vez.
    - La marca de tiempo es UTC del servidor, no del cliente.
    - La hora se guarda en UTC y se convierte a Bogotá para display.
    """
    employee = _get_employee_or_abort()
    if employee is None:
        return redirect(url_for("main.dashboard"))

    # Verificar si ya hay un registro abierto (sin clock_out)
    existing_open = Attendance.query.filter_by(
        employee_id=employee.id,
        status="open"
    ).first()

    if existing_open:
        flash(
            "Ya tienes una entrada registrada sin salida. "
            "Debes marcar la salida antes de registrar una nueva entrada.",
            "warning"
        )
        return redirect(url_for("main.dashboard"))

    # Capturar la hora actual del SERVIDOR en UTC (naive → se almacena en BD)
    # Se usa datetime.utcnow() para SQLite; en PostgreSQL podría usarse timezone.utc
    now_utc = datetime.utcnow()

    # Crear el registro de asistencia
    attendance = Attendance(
        employee_id=employee.id,
        clock_in=now_utc,
        status="open"
    )
    db.session.add(attendance)
    db.session.commit()

    # Mostrar la hora en zona Bogotá para el mensaje de confirmación
    now_bogota = pytz.utc.localize(now_utc).astimezone(BOGOTA_TZ)
    hora_display = now_bogota.strftime("%H:%M:%S")

    flash(
        f"✅ Entrada registrada a las {hora_display} (hora Colombia). "
        "¡Buen turno!",
        "success"
    )
    return redirect(url_for("main.dashboard"))


@attendance_bp.route("/clock-out", methods=["POST"])
@login_required
def clock_out():
    """
    Registra la salida (clock-out) del empleado.

    Reglas:
    - Solo cierra el registro más reciente abierto del empleado.
    - La marca de tiempo es UTC del servidor.
    - Cambia el status del registro a 'closed'.
    """
    employee = _get_employee_or_abort()
    if employee is None:
        return redirect(url_for("main.dashboard"))

    # Buscar el registro abierto más reciente
    open_attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        status="open"
    ).order_by(Attendance.clock_in.desc()).first()

    if open_attendance is None:
        flash(
            "No tienes una entrada activa. "
            "Debes marcar la entrada primero.",
            "warning"
        )
        return redirect(url_for("main.dashboard"))

    # Capturar hora de salida del servidor en UTC
    now_utc = datetime.utcnow()

    # Actualizar el registro existente
    open_attendance.clock_out = now_utc
    open_attendance.status = "closed"
    db.session.commit()

    # Calcular tiempo trabajado para mostrar en el mensaje
    delta = open_attendance.clock_out - open_attendance.clock_in
    total_minutes = int(delta.total_seconds() / 60)
    hours, minutes = divmod(total_minutes, 60)

    now_bogota = pytz.utc.localize(now_utc).astimezone(BOGOTA_TZ)
    hora_display = now_bogota.strftime("%H:%M:%S")

    flash(
        f"👋 Salida registrada a las {hora_display} (hora Colombia). "
        f"Tiempo trabajado: {hours}h {minutes}min.",
        "success"
    )
    return redirect(url_for("main.dashboard"))


@attendance_bp.route("/history")
@login_required
def history():
    """
    Muestra el historial completo de asistencias del empleado con paginación.
    """
    employee = _get_employee_or_abort()
    if employee is None:
        return redirect(url_for("main.dashboard"))

    page = request.args.get("page", 1, type=int)
    per_page = 20

    pagination = (
        Attendance.query
        .filter_by(employee_id=employee.id)
        .order_by(Attendance.clock_in.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "attendance/history.html",
        employee=employee,
        pagination=pagination,
        attendances=pagination.items,
    )


@attendance_bp.route("/status", methods=["GET"])
@login_required
def status():
    """
    Endpoint JSON para que el frontend consulte el estado actual de asistencia.
    Usado por el JavaScript del dashboard para actualizar la UI sin recarga.
    """
    employee = current_user.employee
    if not employee:
        return jsonify({"status": "no_employee"}), 200

    open_att = Attendance.query.filter_by(
        employee_id=employee.id,
        status="open"
    ).first()

    if open_att:
        now_bogota = datetime.now(BOGOTA_TZ)
        clock_in_bogota = pytz.utc.localize(open_att.clock_in).astimezone(BOGOTA_TZ)
        elapsed_seconds = (now_bogota - clock_in_bogota).total_seconds()

        return jsonify({
            "status": "clocked_in",
            "clock_in": clock_in_bogota.strftime("%H:%M:%S"),
            "elapsed_seconds": int(elapsed_seconds),
            "attendance_id": open_att.id,
        })

    return jsonify({"status": "clocked_out"})
