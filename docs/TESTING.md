# GUÍA DE EJECUCIÓN DE PRUEBAS

**Documento:** Guía Práctica de Pruebas v1.0  
**Proyecto:** Sistema de Gestión de Nómina y Turnos  
**Última actualización:** Enero 2024  

---

## 1. REQUISITOS PREVIOS

### 1.1 Versiones Requeridas

```bash
Python          >= 3.11
pip             >= 23.0
pip --version
python --version
```

### 1.2 Dependencias

```bash
# Instalar dependencias base
pip install -r requirements.txt

# Instalar dependencias de prueba
pip install -r requirements-test.txt

# Verificar que pytest está instalado
pytest --version
```

### 1.3 Estructura del Proyecto

Asegurar que exists:
```
proyecto/
├── app/                    # Código aplicación
├── tests/                  # Pruebas
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pytest.ini              # Config pytest
├── requirements.txt
├── requirements-test.txt
└── config.py              # Config app
```

---

## 2. EJECUCIÓN RÁPIDA

### 2.1 Ejecutar Todo

```bash
# Comando básico
pytest

# Con salida verbosa
pytest -v

# Con salida muy detallada
pytest -vv
```

**Salida esperada:**
```
tests/unit/test_models.py::TestUserModel::test_user_creation PASSED
tests/unit/test_models.py::TestUserModel::test_user_password_hashing PASSED
tests/integration/test_auth.py::TestAuthRoutes::test_login_with_valid_credentials PASSED
...
======================== 45 passed in 8.23s ========================
```

### 2.2 Ejecutar Pruebas Específicas

```bash
# Solo pruebas unitarias
pytest tests/unit/

# Solo autenticación
pytest tests/integration/test_auth.py

# Una prueba específica
pytest tests/unit/test_models.py::TestUserModel::test_user_password_hashing

# Pruebas que contengan "payroll"
pytest -k payroll

# Pruebas que NOT contengan "integration"
pytest -k "not integration"
```

### 2.3 Filtrar por Marcadores

```bash
# Solo pruebas críticas (si están marcadas)
pytest -m critical

# Solo autenticación
pytest -m auth

# Solo empleados O nómina
pytest -m "employee or payroll"
```

---

## 3. ANÁLISIS DE COBERTURA

### 3.1 Generar Reporte de Cobertura

```bash
# Generar cobertura HTML
pytest --cov=app --cov-report=html

# Generar cobertura terminal
pytest --cov=app --cov-report=term

# Cobertura detallada por módulo
pytest --cov=app --cov-report=term-missing
```

**Salida esperada:**
```
Name                      Stmts   Miss  Cover   Missing
--------------------------------------------------------------
app/__init__.py               25      0   100%
app/models/__init__.py        120     8    93%   45-48, 210-215
app/routes/auth.py            45      3    93%   78-80
app/routes/employee.py        65      5    92%   120-125
app/extensions.py            12      0   100%
--------------------------------------------------------------
TOTAL                        267     16    94%
```

### 3.2 Abrir Reporte en Navegador

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

### 3.3 Interpretación de Cobertura

| Cobertura | Evaluación | Acción |
|---|---|---|
| 95-100% | Excelente | Continuar |
| 85-95% | Bueno | Aceptable |
| 75-85% | Aceptable | Mejorar |
| 50-75% | Bajo | Reforzar pruebas |
| <50% | Crítico | Detener, aumentar pruebas |

---

## 4. DEPURACIÓN Y TROUBLESHOOTING

### 4.1 Modo Verbose

```bash
# Mostrar prints y logs
pytest -v -s

# Mostrar todo incluyendo warnings
pytest -v -s --tb=long
```

### 4.2 Parar en Primer Fallo

```bash
# Detener al primer fallo
pytest -x

# Detener después de N fallos
pytest --maxfail=3
```

### 4.3 Último Fallo

```bash
# Solo re-ejecutar últimas pruebas fallidas
pytest --lf

# Fallidas primero, luego las demás
pytest --ff
```

### 4.4 Debugger interactivo

```bash
# Activar pdb en fallos
pytest --pdb

# Activar pdb en fallos (pero sin los de setup)
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### 4.5 Errores Comunes

#### Error: `ModuleNotFoundError: No module named 'pytest'`
```bash
# Solución: instalar pytest
pip install pytest pytest-flask

# Verificar
pytest --version
```

#### Error: `SQLALCHEMY_DATABASE_URI not configured`
```python
# Solución: conftest.py ya lo configura
# Si persiste, verificar que config.py está correcto
# y que TestingConfig existe
```

#### Error: `No tests found`
```bash
# Solución: verificar estructura
ls tests/
ls tests/unit/
pytest --collect-only  # Ver qué encuentra
```

#### Pruebas pasan localmente pero fallan en CI/CD
```bash
# Ejecutar exactamente como CI
pytest --tb=short -v

# Limpiar cache si hay problemas
rm -rf .pytest_cache __pycache__
pytest
```

---

## 5. CASOS DE PRUEBA PRINCIPALES

### 5.1 Autenticación

```bash
# Ejecutar todos los tests de auth
pytest tests/integration/test_auth.py -v

# Solo tests de login
pytest tests/integration/test_auth.py::TestAuthRoutes::test_login_with_valid_credentials -v
```

**Verificar:**
- Login funciona con credenciales correctas
- Login falla con contraseña incorrecta
- Logout cierra sesión
- Rutas protegidas redirigen a login

### 5.2 Gestión de Empleados

```bash
# Todos los tests de empleados
pytest tests/integration/test_employees.py -v

# Solo creación de empleados
pytest tests/integration/test_employees.py -k "create_new_employee" -v

# Solo validaciones
pytest tests/integration/test_employees.py::TestEmployeeValidation -v
```

**Verificar:**
- Se crea empleado con datos válidos
- Se previenen duplicados
- Se validan salarios
- Admin puede crear, empleado no

### 5.3 Modelos y Lógica

```bash
# Todos los tests de modelos
pytest tests/unit/test_models.py -v

# Solo cálculo de valor-hora
pytest tests/unit/test_models.py::TestEmployeeModel::test_hourly_rate_calculation -v

# Solo relaciones
pytest tests/unit/test_models.py::TestModelRelationships -v
```

**Verificar:**
- Contraseñas se hashean
- Valor-hora se calcula correctamente
- Relaciones entre modelos funcionan
- Validaciones de uniqueness funcionan

### 5.4 Nómina y Cálculos

```bash
# Todos los tests de nómina
pytest tests/integration/test_payroll.py -v

# Solo cálculos
pytest tests/integration/test_payroll.py::TestPayrollCalculations -v

# Solo normativa
pytest tests/integration/test_payroll.py::TestWorkingHoursValidation -v
```

**Verificar:**
- Horas ordinarias se calculan bien
- Horas extras diurnas (+25%)
- Recargo nocturno (+35%)
- Máximo 42h semanales

---

## 6. REPORTES PERSONALIZADOS

### 6.1 Reporte JUnit XML (para CI/CD)

```bash
pytest --junit-xml=test-results.xml
```

### 6.2 Reporte JSON

```bash
# Requiere: pip install pytest-json-report
pytest --json-report --json-report-file=report.json
```

### 6.3 Reporte HTML

```bash
# Requiere: pip install pytest-html
pytest --html=report.html --self-contained-html
```

### 6.4 Combinar Reportes

```bash
# Cobertura + HTML
pytest \
  --cov=app \
  --cov-report=html \
  --html=report.html \
  --self-contained-html \
  --junit-xml=results.xml
```

---

## 7. INTEGRACIÓN CONTINUA

### 7.1 GitHub Actions

Crear `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 7.2 Pre-commit Hook

Crear `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Ejecutando pruebas..."
pytest tests/unit/ -q
if [ $? -ne 0 ]; then
  echo "Pruebas fallaron, commit bloqueado"
  exit 1
fi
echo "Pruebas pasaron"
```

Ejecutar:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 8. MEJORES PRÁCTICAS

### 8.1 DO's (Hacer)

Ejecutar pruebas regularmente
```bash
# Después de cambios
pytest

# Antes de push
pytest --cov=app
```

Mantener cobertura alta
```bash
# Revisar regularmente
pytest --cov=app --cov-report=term-missing
```

Agregar pruebas para bugs
```bash
# Primero crear test que falla
pytest tests/unit/test_models.py::TestBugFix -v

# Luego fijar bug hasta que pase
```

Usar fixtures para datos
```python
def test_something(db_session, admin_user):
    # Usar fixtures, no crear manualmente
    assert admin_user.is_admin
```

### 8.2 DON'Ts (No Hacer)

No usar BD de producción
```bash
# MALO: usar DB real
DATABASE_URL=postgresql://prod
pytest

# BIEN: TestingConfig usa in-memory
pytest
```

No ignorar pruebas fallidas
```bash
# MALO
pytest -q  # Ver qué falla

# BIEN
pytest -v  # Revisar cada una
```

No tener pruebas sin docstring
```python
# MALO
def test_x(db_session):
    pass

# BIEN
def test_hourly_rate_calculation(db_session, employee_user):
    """Verifica que valor-hora se calcula según fórmula colombiana."""
    emp = employee_user.employee
    expected = 1500000 / (4.33 * 42)
    assert abs(emp.hourly_rate - expected) < 0.01
```

---

## 9. REFERENCIA RÁPIDA

```bash
# Test básico
pytest

# Verboso
pytest -v

# Cobertura
pytest --cov=app --cov-report=html

# Específico
pytest tests/unit/test_models.py::TestUserModel::test_user_creation

# Con prints
pytest -v -s

# Parar en fallo
pytest -x

# Últimos fallos
pytest --lf

# Marcar
pytest -m "auth"

# Palabra clave
pytest -k "password"

# HTML report
pytest --html=report.html

# XML report
pytest --junit-xml=results.xml
```

---

## 10. CONTACTO Y SOPORTE

- **Issues:** GitHub Issues
- **Questions:** Documentación en `docs/`
- **CI/CD:** `.github/workflows/`

---

**Versión:** 1.0  
**Fecha:** Enero 2024  
**Mantenedor:** Equipo de Desarrollo
