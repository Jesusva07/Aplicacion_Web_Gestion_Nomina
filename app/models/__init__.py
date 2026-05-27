"""
app/models/__init__.py — Modelos de base de datos con SQLAlchemy.

Entidades:
  - User:       Cuenta de usuario para autenticación (empleado o admin).
  - Employee:   Datos laborales del empleado (salario, rol, estado).
  - Shift:      Turno programado (entrada/salida esperada).
  - Attendance: Registro de asistencia real (clock-in / clock-out).

Relaciones:
  User 1──1 Employee ──< Shift
                      ──< Attendance
"""

from datetime import datetime
import pytz

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

# Zona horaria de Colombia (UTC-5 sin cambio de horario de verano)
BOGOTA_TZ = pytz.timezone("America/Bogota")


# ---------------------------------------------------------------------------
# Modelo: User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    """
    Cuenta de acceso al sistema.
    
    Separado de Employee para permitir que un admin sin perfil de empleado
    también pueda acceder (principio de separación de responsabilidades).
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Email único que actúa como nombre de usuario
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # Hash de la contraseña (nunca almacenar texto plano)
    password_hash = db.Column(db.String(256), nullable=False)

    # Roles disponibles: 'admin' o 'employee'
    role = db.Column(db.String(20), nullable=False, default="employee")

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación 1:1 con Employee (un usuario puede tener un perfil de empleado)
    employee = db.relationship("Employee", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        """Genera y almacena el hash bcrypt de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Propiedad de conveniencia para verificar rol de administrador."""
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ---------------------------------------------------------------------------
# Modelo: Employee
# ---------------------------------------------------------------------------
class Employee(db.Model):
    """
    Perfil laboral del empleado.
    
    Contiene datos de nómina (salario base) y organizacionales (cargo).
    El salario base se usa como referencia para calcular el valor-hora.
    """
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)

    # Cédula o número de identificación (debe ser único en la empresa)
    document_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Nombre completo del empleado
    name = db.Column(db.String(100), nullable=False)

    # Cargo o puesto de trabajo (ej: "Operario", "Supervisor", "Cajero")
    role = db.Column(db.String(80), nullable=False)

    # Salario mensual base en pesos colombianos (COP)
    # Se usa para derivar el valor-hora: salario_mensual / (42h * 4.33 semanas)
    base_salary = db.Column(db.Numeric(12, 2), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # FK hacia User — un empleado siempre tiene una cuenta de acceso
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", back_populates="employee")

    # Relaciones hacia turnos y asistencias
    shifts = db.relationship(
        "Shift", back_populates="employee", lazy="dynamic",
        cascade="all, delete-orphan"
    )
    attendances = db.relationship(
        "Attendance", back_populates="employee", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    @property
    def hourly_rate(self) -> float:
        """
        Calcula el valor de una hora ordinaria.

        Fórmula estándar colombiana:
          salario_mensual / (semanas_promedio_mes * horas_semanales_legales)
          = salario / (4.33 * 42)
        
        4.33 es el promedio de semanas por mes (365 días / 12 meses / 7 días).
        """
        return float(self.base_salary) / (4.33 * 42)

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name} doc={self.document_id}>"


# ---------------------------------------------------------------------------
# Modelo: Shift (Turno programado)
# ---------------------------------------------------------------------------
class Shift(db.Model):
    """
    Turno de trabajo programado para un empleado en una fecha específica.
    
    Define la jornada ESPERADA. Se compara con Attendance para detectar
    horas extras o ausencias.
    """
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)

    # FK hacia el empleado al que pertenece este turno
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True
    )
    employee = db.relationship("Employee", back_populates="shifts")

    # Fecha y hora programada de inicio del turno (almacenada en UTC)
    start_time = db.Column(db.DateTime, nullable=False)

    # Fecha y hora programada de fin del turno (almacenada en UTC)
    end_time = db.Column(db.DateTime, nullable=False)

    # Tipo de turno para clasificación rápida en reportes
    # Mañana: 06:00-14:00 | Tarde: 14:00-22:00 | Noche: 22:00-06:00
    SHIFT_TYPES = ["Mañana", "Tarde", "Noche", "Especial"]
    shift_type = db.Column(db.String(20), nullable=False, default="Mañana")

    # Descripción opcional del turno (ej: "Turno festivo", "Reemplazo")
    notes = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def duration_hours(self) -> float:
        """Duración total del turno programado en horas."""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600

    def __repr__(self) -> str:
        return (
            f"<Shift id={self.id} employee_id={self.employee_id} "
            f"type={self.shift_type} start={self.start_time}>"
        )


# ---------------------------------------------------------------------------
# Modelo: Attendance (Registro de asistencia real)
# ---------------------------------------------------------------------------
class Attendance(db.Model):
    """
    Registro de la asistencia REAL del empleado.
    
    clock_in y clock_out se almacenan en UTC y se convierten a
    America/Bogota al momento de mostrar o calcular.
    """
    __tablename__ = "attendances"

    id = db.Column(db.Integer, primary_key=True)

    # FK hacia el empleado
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True
    )
    employee = db.relationship("Employee", back_populates="attendances")

    # Marca de tiempo real de entrada (almacenada en UTC)
    clock_in = db.Column(db.DateTime, nullable=False)

    # Marca de tiempo real de salida (puede ser NULL si aún no ha salido)
    clock_out = db.Column(db.DateTime, nullable=True)

    # Referencia opcional al turno programado asociado
    shift_id = db.Column(
        db.Integer, db.ForeignKey("shifts.id"), nullable=True
    )
    shift = db.relationship("Shift")

    # Estado del registro: 'open' (sin clock_out) | 'closed' (completo)
    status = db.Column(db.String(10), nullable=False, default="open")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def clock_in_bogota(self) -> datetime:
        """Retorna clock_in convertido a la zona horaria de Bogotá."""
        utc_aware = pytz.utc.localize(self.clock_in)
        return utc_aware.astimezone(BOGOTA_TZ)

    @property
    def clock_out_bogota(self) -> datetime | None:
        """Retorna clock_out convertido a Bogotá, o None si aún está abierto."""
        if self.clock_out is None:
            return None
        utc_aware = pytz.utc.localize(self.clock_out)
        return utc_aware.astimezone(BOGOTA_TZ)

    @property
    def total_hours_worked(self) -> float | None:
        """
        Calcula el total de horas trabajadas en este registro.
        Retorna None si el empleado aún no ha marcado salida.
        """
        if self.clock_out is None:
            return None
        delta = self.clock_out - self.clock_in
        return round(delta.total_seconds() / 3600, 2)

    def __repr__(self) -> str:
        return (
            f"<Attendance id={self.id} employee_id={self.employee_id} "
            f"in={self.clock_in} out={self.clock_out} status={self.status}>"
        )
