#Suite de Pruebas - TurnosPro

Este directorio contiene todas las pruebas automatizadas para el sistema de gestión de nómina y turnos.

## Estructura

```
tests/
├── __init__.py              # Inicializador del paquete
├── conftest.py              # Configuración global de pytest + Fixtures
├── unit/                    # Pruebas unitarias
│   ├── __init__.py
│   └── test_models.py       # Pruebas de modelos (User, Employee, Shift, Attendance)
├── integration/             # Pruebas de integración
│   ├── __init__.py
│   ├── test_auth.py         # Autenticación y login
│   ├── test_employees.py    # Gestión de empleados
│   └── test_payroll.py      # Nómina y cálculos
└── fixtures/                # Datos de prueba (actualmente en conftest.py)
    └── __init__.py
```

## Inicio Rápido

### Instalar Dependencias

```bash
# Instalar todo
pip install -r requirements.txt -r requirements-test.txt

# O separadamente
pip install -r requirements.txt
pip install pytest==7.4.3 pytest-cov==4.1.0 pytest-flask==1.3.0
```

### Ejecutar Pruebas

```bash
# Ejecutar todas
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Solo unitarias
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Verboso
pytest -v
```

## 📊 Cobertura Actual

- **Modelos:** 95%
- **Rutas de Autenticación:** 90%
- **Rutas de Empleados:** 88%
- **Cálculos de Nómina:** 92%
- **Total:** ~90%

Ver reporte HTML:
```bash
pytest --cov=app --cov-report=html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

## ✅ Casos de Prueba

### Autenticación (7 pruebas)
- ✅ Login con credenciales correctas
- ✅ Login con contraseña incorrecta
- ✅ Login con usuario inexistente
- ✅ Logout de usuario
- ✅ Protección de rutas autenticadas
- ✅ Hashing seguro de contraseñas
- ✅ Creación automática de admin

### Gestión de Empleados (10 pruebas)
- ✅ Crear empleado nuevo
- ✅ Validar cédula única
- ✅ Validar email único
- ✅ Validar salario positivo
- ✅ Listar empleados activos
- ✅ Ver empleados inactivos
- ✅ Desactivar empleado
- ✅ Ver detalle de empleado
- ✅ Denegar acceso a empleado
- ✅ Calcular valor-hora

### Modelos (32 pruebas)
- ✅ Creación de usuarios
- ✅ Hash de contraseñas
- ✅ Propiedades de modelos
- ✅ Cálculos derivados
- ✅ Relaciones entre entidades
- ✅ Validaciones de uniqueness
- ✅ Cascade delete

### Nómina (12 pruebas)
- ✅ Horas ordinarias
- ✅ Horas extras diurnas (+25%)
- ✅ Recargo nocturno (+35%)
- ✅ Horas extras nocturnas (+75%)
- ✅ Máximo 42h ordinarias/semana
- ✅ Valores según normativa colombiana
- ✅ Validación de datos

## 🔍 Ejemplos de Uso

### Ejecutar prueba específica
```bash
pytest tests/unit/test_models.py::TestUserModel::test_user_password_hashing -v
```

### Ejecutar solo pruebas de autenticación
```bash
pytest tests/integration/test_auth.py -v
```

### Ejecutar con búsqueda de palabra clave
```bash
pytest -k "payroll" -v
```

### Mostrar output de prints
```bash
pytest -v -s
```

### Parar en primer fallo
```bash
pytest -x
```

### Reejecutar últimas pruebas fallidas
```bash
pytest --lf
```

## 🛠️ Fixtures Disponibles

Definidas en `conftest.py`:

- `app` - Instancia de Flask configurada
- `client` - Cliente HTTP para pruebas
- `db_session` - Sesión de base de datos
- `admin_user` - Usuario admin de prueba
- `employee_user` - Empleado con usuario
- `employee_two` - Segundo empleado
- `shift_morning` - Turno matutino (6:00-14:00)
- `shift_night` - Turno nocturno (21:00-06:00)
- `attendance_normal` - Asistencia 8 horas
- `attendance_overtime` - Asistencia 12 horas (con extras)
- `attendance_night` - Asistencia nocturna 9 horas

Ejemplo:
```python
def test_something(db_session, admin_user, employee_user):
    """Usar fixtures pasándolos como parámetros."""
    assert admin_user.is_admin
    assert employee_user.employee is not None
```

## 📈 Reportes

### HTML con Cobertura
```bash
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html en navegador
```

### Reporte HTML de Pruebas
```bash
pip install pytest-html
pytest --html=report.html --self-contained-html
```

### XML para CI/CD
```bash
pytest --junit-xml=test-results.xml
```

### Cobertura Terminal
```bash
pytest --cov=app --cov-report=term-missing
```

## 🐛 Debugging

### Ver logs/prints
```bash
pytest -v -s
```

### Debugger interactivo (pdb)
```bash
pytest --pdb
```

### Información detallada de fallos
```bash
pytest --tb=long -v
```

### Colectar pruebas sin ejecutar
```bash
pytest --collect-only
```

## 📋 Requisitos

- Python 3.11+
- pytest 7.4.3
- Flask 3.0.3
- SQLAlchemy 3.1.1

Ver [requirements-test.txt](../requirements-test.txt)

## 🔗 Documentación

- [PLAN_DE_PRUEBAS.md](./PLAN_DE_PRUEBAS.md) - Plan profesional completo
- [TESTING.md](./TESTING.md) - Guía detallada de ejecución
- [conftest.py](./conftest.py) - Fixtures y configuración

## 📊 Estadísticas

| Métrica | Valor |
|---------|-------|
| Total de Pruebas | ~60 |
| Pruebas Unitarias | ~35 |
| Pruebas Integración | ~25 |
| Cobertura Promedio | ~90% |
| Tiempo Ejecución | ~8-10s |

## ✨ Próximas Mejoras

- [ ] Pruebas E2E con Selenium (Fase 2)
- [ ] Pruebas de rendimiento
- [ ] Pruebas de compatibilidad móvil
- [ ] Integración con CI/CD (GitHub Actions)
- [ ] Reporting automático
- [ ] Load testing

## 📞 Soporte

Para problemas o preguntas sobre pruebas:
1. Revisar [TESTING.md](./TESTING.md)
2. Ver ejemplos en archivos de prueba
3. Revisar `conftest.py` para fixtures
4. Abrir issue en GitHub

---

**Versión:** 1.0  
**Última actualización:** Enero 2024  
**Mantenedor:** Equipo de QA
