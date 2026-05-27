"""
app/services/payroll_engine.py — Motor de cálculo de nómina y horas extras.

Implementa las reglas de la normativa laboral colombiana:
  - Decreto 1846 de 2017 / Código Sustantivo del Trabajo (CST)
  - Jornada máxima legal: 42 horas semanales
  - Recargo nocturno: horas entre 21:00 y 06:00
  - Horas extras diurnas: exceso sobre jornada en horario diurno (06:00-21:00)
  - Horas extras nocturnas: exceso sobre jornada en horario nocturno (21:00-06:00)

Arquitectura:
  - PayrollResult: dataclass que encapsula el resultado del cálculo.
  - PayrollEngine: clase de servicio que contiene toda la lógica de cálculo.
  - Función de fachada: calculate_attendance_payroll() para uso externo simple.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import pytz

# Zona horaria oficial de Colombia (no tiene horario de verano)
BOGOTA_TZ = pytz.timezone("America/Bogota")

# ------------------------------------------------------------------
# Constantes de negocio (normativa colombiana)
# ------------------------------------------------------------------

# Jornada máxima legal semanal en horas (Ley 1846 de 2017)
MAX_WEEKLY_HOURS: float = 42.0

# Promedio de semanas por mes (365 días / 12 meses / 7 días/semana)
WEEKS_PER_MONTH: float = 4.33

# Horas ordinarias máximas por mes
MAX_MONTHLY_HOURS: float = MAX_WEEKLY_HOURS * WEEKS_PER_MONTH  # ≈ 181.86 h

# Hora de inicio del período nocturno (21:00 = hora 21 en formato 0-23)
NIGHT_START_HOUR: int = 21

# Hora de fin del período nocturno (06:00 = hora 6 en formato 0-23)
NIGHT_END_HOUR: int = 6

# Recargos y porcentajes sobre el valor de hora ordinaria
NIGHT_SURCHARGE: float = 0.35        # +35% hora ordinaria nocturna (sin extras)
EXTRA_DAY_SURCHARGE: float = 0.25    # +25% hora extra diurna
EXTRA_NIGHT_SURCHARGE: float = 0.75  # +75% hora extra nocturna

# Horas ordinarias máximas en una sola jornada (42h / 5 días hábiles)
MAX_DAILY_ORDINARY_HOURS: float = 8.4


# ------------------------------------------------------------------
# Dataclass de resultado
# ------------------------------------------------------------------

@dataclass
class PayrollResult:
    """
    Encapsula el resultado completo del cálculo de nómina para un
    registro de asistencia (Attendance).

    Todos los valores monetarios están en COP (pesos colombianos).
    Las horas se expresan como flotantes con 2 decimales.
    """

    # ---- Horas clasificadas ----
    ordinary_daytime_hours: float = 0.0    # Horas ordinarias en jornada diurna
    ordinary_nighttime_hours: float = 0.0  # Horas ordinarias en jornada nocturna
    extra_daytime_hours: float = 0.0       # Horas extras en jornada diurna
    extra_nighttime_hours: float = 0.0     # Horas extras en jornada nocturna
    total_hours_worked: float = 0.0        # Total de horas efectivamente trabajadas

    # ---- Valores monetarios ----
    hourly_rate: float = 0.0              # Valor de una hora ordinaria en COP
    ordinary_pay: float = 0.0            # Pago por horas ordinarias (diurnas + noct.)
    extra_daytime_pay: float = 0.0       # Pago por horas extra diurnas
    extra_nighttime_pay: float = 0.0     # Pago por horas extra nocturnas
    night_surcharge_pay: float = 0.0     # Recargo nocturno sobre horas ordinarias
    total_pay: float = 0.0               # Total a pagar por este registro

    # ---- Metadatos del cálculo ----
    warnings: list[str] = field(default_factory=list)  # Alertas del motor
    errors: list[str] = field(default_factory=list)    # Errores que impiden cálculo

    @property
    def is_valid(self) -> bool:
        """El cálculo es válido si no hay errores bloqueantes."""
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        """Serializa el resultado a diccionario para APIs y templates."""
        return {
            "hours": {
                "ordinary_daytime": round(self.ordinary_daytime_hours, 2),
                "ordinary_nighttime": round(self.ordinary_nighttime_hours, 2),
                "extra_daytime": round(self.extra_daytime_hours, 2),
                "extra_nighttime": round(self.extra_nighttime_hours, 2),
                "total_worked": round(self.total_hours_worked, 2),
            },
            "pay": {
                "hourly_rate": round(self.hourly_rate, 2),
                "ordinary": round(self.ordinary_pay, 2),
                "extra_daytime": round(self.extra_daytime_pay, 2),
                "extra_nighttime": round(self.extra_nighttime_pay, 2),
                "night_surcharge": round(self.night_surcharge_pay, 2),
                "total": round(self.total_pay, 2),
            },
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ------------------------------------------------------------------
# Motor principal de cálculo
# ------------------------------------------------------------------

class PayrollEngine:
    """
    Motor de cálculo de nómina según normativa colombiana.

    Responsabilidades (Principio de Responsabilidad Única):
      1. Convertir tiempos UTC → Bogotá.
      2. Descomponer un intervalo de tiempo en segmentos diurnos/nocturnos.
      3. Clasificar cada segmento como ordinario o extra.
      4. Calcular el pago correspondiente a cada segmento.
    """

    def __init__(self, hourly_rate: float):
        """
        Inicializa el motor con el valor-hora del empleado.

        Args:
            hourly_rate: Valor de una hora ordinaria en COP.
                         Se obtiene de Employee.hourly_rate.
        """
        if hourly_rate <= 0:
            raise ValueError("hourly_rate debe ser un valor positivo.")
        self.hourly_rate = hourly_rate

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def calculate(
        self,
        clock_in_utc: datetime,
        clock_out_utc: datetime,
        scheduled_start_utc: Optional[datetime] = None,
        scheduled_end_utc: Optional[datetime] = None,
    ) -> PayrollResult:
        """
        Calcula la nómina para un intervalo de trabajo específico.

        Algoritmo general:
          1. Validar entradas.
          2. Convertir a zona horaria de Bogotá.
          3. Determinar el límite de horas ordinarias:
               - Si hay turno programado: duración del turno (hasta 8.4 h).
               - Si no hay turno: usar el máximo diario (8.4 h).
          4. Dividir el tiempo trabajado en segmentos de 1 minuto para
             clasificar cada minuto como diurno u nocturno.
          5. Aplicar el límite ordinario: los primeros N minutos son
             ordinarios y el resto son extras.
          6. Calcular el pago de cada categoría.

        Args:
            clock_in_utc:         Hora real de entrada (UTC, naive o aware).
            clock_out_utc:        Hora real de salida (UTC, naive o aware).
            scheduled_start_utc:  Inicio programado del turno (UTC). Opcional.
            scheduled_end_utc:    Fin programado del turno (UTC). Opcional.

        Returns:
            PayrollResult con el desglose completo.
        """
        result = PayrollResult(hourly_rate=self.hourly_rate)

        # ---- Paso 1: Validaciones previas ----
        clock_in_utc = self._ensure_utc(clock_in_utc)
        clock_out_utc = self._ensure_utc(clock_out_utc)

        if clock_out_utc <= clock_in_utc:
            result.errors.append(
                "clock_out debe ser posterior a clock_in."
            )
            return result

        # ---- Paso 2: Conversión a Bogotá ----
        clock_in_bog = clock_in_utc.astimezone(BOGOTA_TZ)
        clock_out_bog = clock_out_utc.astimezone(BOGOTA_TZ)

        # ---- Paso 3: Total de horas trabajadas ----
        total_seconds = (clock_out_utc - clock_in_utc).total_seconds()
        total_hours = total_seconds / 3600
        result.total_hours_worked = round(total_hours, 4)

        # Alerta si la jornada supera 16 horas (probable error de registro)
        if total_hours > 16:
            result.warnings.append(
                f"Se registraron {total_hours:.1f} horas en un solo turno. "
                "Verificar que clock_out sea correcto."
            )

        # ---- Paso 4: Determinar horas ordinarias máximas ----
        # Si hay turno programado, las horas ordinarias son las horas del turno.
        # Si no hay turno, se usa el máximo diario legal (8.4 h).
        if scheduled_start_utc and scheduled_end_utc:
            sched_start = self._ensure_utc(scheduled_start_utc)
            sched_end = self._ensure_utc(scheduled_end_utc)
            sched_seconds = (sched_end - sched_start).total_seconds()
            max_ordinary_hours = min(sched_seconds / 3600, MAX_DAILY_ORDINARY_HOURS)
        else:
            max_ordinary_hours = MAX_DAILY_ORDINARY_HOURS
            result.warnings.append(
                "No se encontró turno programado. "
                f"Se usa el máximo diario de {MAX_DAILY_ORDINARY_HOURS} h como referencia."
            )

        # ---- Paso 5: Clasificar minuto a minuto ----
        # Iterar en intervalos de 1 minuto para clasificar cada fragmento
        # de tiempo como (diurno/nocturno) × (ordinario/extra).
        # Acumuladores en minutos para mayor precisión
        ordinary_day_min: float = 0.0
        ordinary_night_min: float = 0.0
        extra_day_min: float = 0.0
        extra_night_min: float = 0.0

        # Máximo de minutos ordinarios permitidos en esta jornada
        max_ordinary_minutes: float = max_ordinary_hours * 60
        minutes_accumulated: float = 0.0  # Contador acumulado de minutos trabajados

        # Recorremos el tiempo en pasos de 1 minuto
        current = clock_in_bog
        one_minute = timedelta(minutes=1)

        while current < clock_out_bog:
            # El último segmento puede ser menor a 1 minuto
            segment_end = min(current + one_minute, clock_out_bog)
            segment_minutes = (segment_end - current).total_seconds() / 60

            # Determinar si este minuto cae en horario nocturno
            is_night = self._is_nighttime(current)

            # Determinar si este minuto es ordinario o extra
            is_ordinary = (minutes_accumulated + segment_minutes) <= max_ordinary_minutes

            # Acumular en el cubo correspondiente
            if is_ordinary:
                if is_night:
                    ordinary_night_min += segment_minutes
                else:
                    ordinary_day_min += segment_minutes
            else:
                if is_night:
                    extra_night_min += segment_minutes
                else:
                    extra_day_min += segment_minutes

            minutes_accumulated += segment_minutes
            current = segment_end

        # ---- Paso 6: Convertir minutos a horas ----
        result.ordinary_daytime_hours = round(ordinary_day_min / 60, 4)
        result.ordinary_nighttime_hours = round(ordinary_night_min / 60, 4)
        result.extra_daytime_hours = round(extra_day_min / 60, 4)
        result.extra_nighttime_hours = round(extra_night_min / 60, 4)

        # ---- Paso 7: Calcular pagos ----
        h = self.hourly_rate  # Alias corto para legibilidad

        # Pago ordinario diurno: horas × valor-hora
        ordinary_day_pay = result.ordinary_daytime_hours * h

        # Pago ordinario nocturno: horas × valor-hora
        # El recargo nocturno (+35%) se calcula APARTE para mayor transparencia
        ordinary_night_pay = result.ordinary_nighttime_hours * h
        result.night_surcharge_pay = result.ordinary_nighttime_hours * h * NIGHT_SURCHARGE

        result.ordinary_pay = round(ordinary_day_pay + ordinary_night_pay, 2)

        # Pago hora extra diurna: horas × valor-hora × (1 + 25%)
        result.extra_daytime_pay = round(
            result.extra_daytime_hours * h * (1 + EXTRA_DAY_SURCHARGE), 2
        )

        # Pago hora extra nocturna: horas × valor-hora × (1 + 75%)
        result.extra_nighttime_pay = round(
            result.extra_nighttime_hours * h * (1 + EXTRA_NIGHT_SURCHARGE), 2
        )

        # Total: ordinario + recargo nocturno + extras
        result.total_pay = round(
            result.ordinary_pay
            + result.night_surcharge_pay
            + result.extra_daytime_pay
            + result.extra_nighttime_pay,
            2,
        )

        return result

    # ------------------------------------------------------------------
    # Métodos auxiliares (privados)
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        """
        Garantiza que un datetime sea timezone-aware en UTC.

        Si el datetime es naive (sin tzinfo), se asume UTC.
        Si ya tiene timezone, se convierte a UTC.
        """
        if dt.tzinfo is None:
            # Asumir que los datetimes naive almacenados en BD son UTC
            return pytz.utc.localize(dt)
        return dt.astimezone(pytz.utc)

    @staticmethod
    def _is_nighttime(dt_bogota: datetime) -> bool:
        """
        Determina si un momento dado cae en horario nocturno colombiano.

        Horario nocturno: 21:00 – 06:00 (del día siguiente).
        
        Ejemplos:
          22:30 → True  (después de 21:00)
          02:00 → True  (antes de 06:00)
          14:00 → False (mitad del día)
          06:00 → False (exactamente las 6 AM ya no es nocturno)
        """
        hour = dt_bogota.hour
        # Rango nocturno cruza la medianoche: [21, 23] ∪ [0, 5]
        return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR


# ------------------------------------------------------------------
# Función de fachada (Facade Pattern)
# ------------------------------------------------------------------

def calculate_attendance_payroll(
    attendance,  # tipo: app.models.Attendance
    shift=None,  # tipo: app.models.Shift (opcional)
) -> PayrollResult:
    """
    Función de fachada de alto nivel para calcular la nómina de un
    registro de asistencia.

    Orquesta la creación del motor y la ejecución del cálculo, abstrayendo
    los detalles de implementación de los controladores (Blueprints).

    Args:
        attendance: Objeto Attendance con clock_in y clock_out.
        shift:      Objeto Shift con start_time y end_time (opcional).

    Returns:
        PayrollResult con el desglose completo del cálculo.

    Raises:
        ValueError: Si el registro de asistencia está incompleto (sin clock_out).
    """
    # Validar que el registro esté cerrado (tiene clock_out)
    if attendance.clock_out is None:
        result = PayrollResult()
        result.errors.append(
            "El registro de asistencia no tiene clock_out. "
            "El empleado debe marcar la salida antes de calcular."
        )
        return result

    # Obtener el valor-hora del empleado desde su perfil
    employee = attendance.employee
    if employee is None:
        result = PayrollResult()
        result.errors.append("El registro de asistencia no tiene empleado asociado.")
        return result

    hourly_rate = employee.hourly_rate

    # Inicializar el motor con el valor-hora del empleado
    engine = PayrollEngine(hourly_rate=hourly_rate)

    # Extraer tiempos del turno programado (si existe)
    scheduled_start = shift.start_time if shift else None
    scheduled_end = shift.end_time if shift else None

    # Ejecutar el cálculo y retornar el resultado
    return engine.calculate(
        clock_in_utc=attendance.clock_in,
        clock_out_utc=attendance.clock_out,
        scheduled_start_utc=scheduled_start,
        scheduled_end_utc=scheduled_end,
    )


def calculate_weekly_summary(attendances: list, employee) -> dict:
    """
    Calcula el resumen semanal de horas y pagos de un empleado.

    Agrega múltiples PayrollResult de la semana para verificar si se
    superaron las 42 horas semanales y calcular el total de extras.

    Args:
        attendances: Lista de objetos Attendance de la semana.
        employee:    Objeto Employee con base_salary.

    Returns:
        Diccionario con resumen: total_hours, ordinary_hours, extra_hours,
        total_pay, exceeded_weekly_limit.
    """
    total_ordinary = 0.0
    total_extra_day = 0.0
    total_extra_night = 0.0
    total_night_surcharge = 0.0
    total_pay = 0.0

    results = []
    for att in attendances:
        if att.clock_out is not None:
            result = calculate_attendance_payroll(att, att.shift)
            if result.is_valid:
                total_ordinary += result.ordinary_daytime_hours + result.ordinary_nighttime_hours
                total_extra_day += result.extra_daytime_hours
                total_extra_night += result.extra_nighttime_hours
                total_night_surcharge += result.night_surcharge_pay
                total_pay += result.total_pay
                results.append(result)

    total_hours = total_ordinary + total_extra_day + total_extra_night

    return {
        "total_hours_worked": round(total_hours, 2),
        "ordinary_hours": round(total_ordinary, 2),
        "extra_daytime_hours": round(total_extra_day, 2),
        "extra_nighttime_hours": round(total_extra_night, 2),
        "night_surcharge_pay": round(total_night_surcharge, 2),
        "total_pay": round(total_pay, 2),
        "exceeded_weekly_limit": total_hours > MAX_WEEKLY_HOURS,
        "weekly_limit": MAX_WEEKLY_HOURS,
        "daily_results": [r.to_dict() for r in results],
    }
