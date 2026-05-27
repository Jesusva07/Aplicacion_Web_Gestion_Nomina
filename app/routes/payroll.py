"""
app/routes/payroll.py — Blueprint de cálculo y reporte de nómina.

Endpoints:
  GET  /payroll/              → Formulario de selección (empleado + período).
  GET  /payroll/report        → Reporte detallado de nómina del período.
  GET  /payroll/weekly/<id>   → Resumen semanal de un empleado.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

import pytz

from app.extensions import db
from app.models import Employee, Attendance, Shift
from app.services.payroll_engine import calculate_attendance_payroll, calculate_weekly_summary
from app.routes.employee import admin_required

payroll_bp = Blueprint("payroll", __name__, template_folder="../templates")
BOGOTA_TZ = pytz.timezone("America/Bogota")


@payroll_bp.route("/")
@login_required
@admin_required
def index():
    """Formulario para seleccionar empleado y período de nómina."""
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
    return render_template("payroll/index.html", employees=employees)


@payroll_bp.route("/report")
@login_required
@admin_required
def report():
    """
    Genera el reporte de nómina para un empleado en un período dado.
    
    Query params:
      - employee_id: ID del empleado.
      - start_date:  Fecha inicio (YYYY-MM-DD).
      - end_date:    Fecha fin (YYYY-MM-DD).
    """
    employee_id = request.args.get("employee_id", type=int)
    start_str = request.args.get("start_date", "")
    end_str = request.args.get("end_date", "")

    if not all([employee_id, start_str, end_str]):
        flash("Debes seleccionar un empleado y un período de fechas.", "warning")
        return redirect(url_for("payroll.index"))

    employee = db.get_or_404(Employee, employee_id)

    try:
        # Parsear fechas y convertir a UTC para consultar la BD
        start_bogota = BOGOTA_TZ.localize(
            datetime.strptime(start_str, "%Y-%m-%d")
        )
        end_bogota = BOGOTA_TZ.localize(
            datetime.strptime(end_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
        )
    except ValueError:
        flash("Formato de fecha inválido. Usa YYYY-MM-DD.", "danger")
        return redirect(url_for("payroll.index"))

    # Convertir a UTC para consultar la base de datos (almacenada en UTC)
    start_utc = start_bogota.astimezone(pytz.utc).replace(tzinfo=None)
    end_utc = end_bogota.astimezone(pytz.utc).replace(tzinfo=None)

    # Obtener registros de asistencia del período
    attendances = (
        Attendance.query
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.clock_in >= start_utc,
            Attendance.clock_in <= end_utc,
            Attendance.status == "closed"
        )
        .order_by(Attendance.clock_in)
        .all()
    )

    # Calcular nómina para cada registro
    payroll_details = []
    for att in attendances:
        result = calculate_attendance_payroll(att, att.shift)
        payroll_details.append({
            "attendance": att,
            "result": result,
            "result_dict": result.to_dict(),
        })

    # Totales del período
    totals = {
        "total_hours": sum(d["result"].total_hours_worked for d in payroll_details),
        "ordinary_hours": sum(
            d["result"].ordinary_daytime_hours + d["result"].ordinary_nighttime_hours
            for d in payroll_details
        ),
        "extra_day_hours": sum(d["result"].extra_daytime_hours for d in payroll_details),
        "extra_night_hours": sum(d["result"].extra_nighttime_hours for d in payroll_details),
        "total_pay": sum(d["result"].total_pay for d in payroll_details),
        "ordinary_pay": sum(d["result"].ordinary_pay for d in payroll_details),
        "extra_day_pay": sum(d["result"].extra_daytime_pay for d in payroll_details),
        "extra_night_pay": sum(d["result"].extra_nighttime_pay for d in payroll_details),
        "night_surcharge_pay": sum(d["result"].night_surcharge_pay for d in payroll_details),
    }

    return render_template(
        "payroll/report.html",
        employee=employee,
        payroll_details=payroll_details,
        totals=totals,
        start_date=start_bogota,
        end_date=end_bogota,
    )
