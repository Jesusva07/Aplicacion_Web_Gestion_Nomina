# PLAN DE PRUEBAS - SISTEMA DE GESTIÓN DE NÓMINA Y TURNOS

**Documento:** Plan de Pruebas v1.0  
**Proyecto:** Aplicación Web de Gestión de Nómina y Turnos (TurnosPro)  
**Fecha:** Enero 2024  
**Estado:** En Implementación  
**Autor:** Equipo de Desarrollo  

---

## 1. INTRODUCCIÓN

### 1.1 Propósito

Este documento define la estrategia, alcance y procedimientos para las pruebas automatizadas del sistema de gestión de nómina y turnos. Las pruebas garantizan que la aplicación cumple con:

- Requisitos funcionales especificados
- Normativa laboral colombiana (Ley 1846/2017)
- Estándares de seguridad y validación de datos
- Cálculos precisos de nómina y horas de trabajo
- Integridad de la base de datos

### 1.2 Alcance

Módulos Incluidos:
- Autenticación y gestión de usuarios (Login/Logout)
- Gestión de empleados (CRUD)
- Gestión de turnos y asistencia
- Cálculos de nómina y recargos
- Control de acceso basado en roles (RBAC)

Módulos Excluidos (Fase 2):
- Integración con sistema de nómina externo
- Exportación avanzada de reportes (PDF/Excel)
- Sincronización con base de datos de producción

### 1.3 Objetivos de Pruebas

1. Confiabilidad: Garantizar que el sistema funciona sin errores
2. Exactitud: Validar cálculos de nómina según normativa colombiana
3. Seguridad: Verificar control de acceso y validación de datos
4. Mantenibilidad: Facilitar cambios futuros sin regresiones
5. Cobertura: Alcanzar mínimo 80% de cobertura de código

---

## 2. ESTRATEGIA DE PRUEBAS

### 2.1 Niveles de Pruebas

#### 2.1.1 Pruebas Unitarias
**Objetivo:** Validar componentes individuales en aislamiento.

**Alcance:**
- Modelos ORM (User, Employee, Shift, Attendance)
- Cálculos de nómina y conversiones
- Validaciones de datos
- Propiedades derivadas

**Herramientas:** pytest + SQLAlchemy in-memory

**Criterio de Éxito:** 
- Todas las pruebas pasan sin errores
- Cobertura ≥ 90% en lógica de modelos

#### 2.1.2 Pruebas de Integración
**Objetivo:** Validar interacción entre componentes.

**Alcance:**
- Flujos de autenticación (login/logout)
- Operaciones CRUD de empleados
- Registros de asistencia
- Generación de reportes de nómina

**Herramientas:** pytest + Flask test client

**Criterio de Éxito:**
- Casos de éxito y error se manejan correctamente
- Base de datos se actualiza correctamente
- Redirecciones y permisos funcionan

#### 2.1.3 Pruebas de Sistema
**Objetivo:** Validar flujos de usuario end-to-end.

**Alcance:**
- Flujo completo de creación de empleado
- Procesamiento de nómina con múltiples empleados
- Casos de excepción y errores
- Validaciones de normativa

**Herramientas:** pytest + Simulación manual o Selenium (fase 2)

**Criterio de Éxito:**
- Sistema completa tareas sin fallos
- Datos se procesan correctamente
- Mensajes de error son claros

### 2.2 Tipos de Pruebas

#### 2.2.1 Pruebas Funcionales
Verifican que cada función cumple requisitos especificados.

Ejemplos:
- Admin puede crear empleados
- Empleado no puede acceder a nómina
- Salario-hora se calcula correctamente

#### 2.2.2 Pruebas de Validación
Verifican validación de datos de entrada.

Ejemplos:
- No permite salario negativo
- No permite empleados sin nombre
- No permite emails duplicados

#### 2.2.3 Pruebas de Seguridad
Verifican control de acceso y protección de datos.

Ejemplos:
- Login con contraseña incorrecta falla
- Empleado no puede ver nómina de otros
- Sesión expira después de inactividad

#### 2.2.4 Pruebas de Rendimiento (Fase 2)
Verifican tiempo de respuesta y carga.

Objetivos:
- Login < 500ms
- Listado 1000 empleados < 2s
- Cálculo nómina < 5s

#### 2.2.5 Pruebas de Compatibilidad
Verifican funcionamiento en diferentes navegadores/plataformas.

**Plataformas:**
- Windows (Chrome, Firefox, Edge)
- Navegadores móviles (fase 2)

---

## 3. CASOS DE PRUEBA

### 3.1 Autenticación

| ID | Caso de Prueba | Entrada | Salida Esperada | Prioridad |
|-----|---|---|---|---|
| AUTH-001 | Login exitoso admin | email: admin@empresa.com, password: correcto | Redirección a dashboard | CRÍTICA |
| AUTH-002 | Login con contraseña incorrecta | email: admin@empresa.com, password: incorrecto | Mensaje error, permanece en login | CRÍTICA |
| AUTH-003 | Login con usuario inexistente | email: noexiste@empresa.com | Mensaje error | CRÍTICA |
| AUTH-004 | Logout | Usuario autenticado hace click logout | Sesión finaliza, redirige a login | CRÍTICA |
| AUTH-005 | Acceso a ruta protegida sin autenticación | GET /employees/ sin session | Redirige a login | CRÍTICA |
| AUTH-006 | Contraseña se hashea correctamente | Crear usuario con password | Password no se almacena en texto plano | ALTA |
| AUTH-007 | Admin es creado automáticamente | Startup aplicación | Admin existe en BD | ALTA |

### 3.2 Gestión de Empleados

| ID | Caso de Prueba | Entrada | Salida Esperada | Prioridad |
|-----|---|---|---|---|
| EMP-001 | Crear empleado | Datos válidos (nombre, cedula, salario, email) | Empleado se crea, usuario se vincula | CRÍTICA |
| EMP-002 | Impedir duplicado cédula | Crear empleado con cédula existente | Mensaje error "cédula existe" | CRÍTICA |
| EMP-003 | Impedir email duplicado | Crear con email existente | Mensaje error "email existe" | CRÍTICA |
| EMP-004 | Validar salario positivo | Salario = 0 o negativo | Mensaje error "salario debe ser mayor a 0" | ALTA |
| EMP-005 | Listar empleados activos | Admin accede /employees/ | Muestra solo empleados activos | ALTA |
| EMP-006 | Ver inactivos | Admin selecciona "ver inactivos" | Muestra empleados inactivos también | MEDIA |
| EMP-007 | Desactivar empleado | Admin selecciona desactivar | is_active = False, usuario desactivado | ALTA |
| EMP-008 | Ver detalle empleado | Admin accede /employees/{id} | Muestra datos, turnos, asistencias | MEDIA |
| EMP-009 | Empleado no puede crear | Empleado intenta /employees/new | Redirección o error 403 | CRÍTICA |
| EMP-010 | Calcular valor-hora | Salario 1,500,000 | valor-hora = 8,246.64 COP | CRÍTICA |

### 3.3 Asistencia

| ID | Caso de Prueba | Entrada | Salida Esperada | Prioridad |
|-----|---|---|---|---|
| ATT-001 | Registrar entrada | Empleado marca entrada 6:00 | clock_in se registra, status=in_progress | CRÍTICA |
| ATT-002 | Registrar salida | Empleado marca salida 14:00 | clock_out se registra, total_hours = 8 | CRÍTICA |
| ATT-003 | Horas trabajadas = NULL sin salida | Entrada sin salida | total_hours_worked retorna None | ALTA |
| ATT-004 | Ver historial asistencia | Empleado accede /attendance/history | Muestra últimas asistencias | MEDIA |

### 3.4 Nómina y Cálculos

| ID | Caso de Prueba | Entrada | Salida Esperada | Prioridad |
|-----|---|---|---|---|
| PAY-001 | Horas ordinarias (8h) | Jornada 6:00-14:00, salario 1.5M | Salario = 65,973.12 COP | CRÍTICA |
| PAY-002 | Extra diurna (4h, +25%) | Jornada 6:00-18:00, salario 1.5M | Extra = 41,233.20 COP | CRÍTICA |
| PAY-003 | Recargo nocturno (+35%) | Jornada 21:00-6:00, salario 1.5M | Salario = 100,237.74 COP | CRÍTICA |
| PAY-004 | Extra nocturna (+75%) | Jornada 21:00-12:00 siguiente (15h), salario 1.5M | Recargo aplicado correctamente | ALTA |
| PAY-005 | Máximo 42h ordinarias/semana | 42h ordinarias + extras | Solo 42h como ordinarias | CRÍTICA |
| PAY-006 | Admin puede ver nómina | Admin accede /payroll/ | Muestra empleados y opciones | MEDIA |
| PAY-007 | Empleado no puede ver nómina | Empleado intenta /payroll/ | Redirección o error 403 | CRÍTICA |

### 3.5 Validaciones y Errores

| ID | Caso de Prueba | Entrada | Salida Esperada | Prioridad |
|-----|---|---|---|---|
| VAL-001 | Campo requerido vacío | Nombre vacío en formulario | Mensaje "campo requerido" | ALTA |
| VAL-002 | Email inválido | Formato incorrecto | Validación falla | MEDIA |
| VAL-003 | Contraseña muy corta | Password < 6 caracteres | Mensaje error, crea con mínimo | MEDIA |
| VAL-004 | Acceso 404 | Intenta recurso inexistente | Página 404 | MEDIA |
| VAL-005 | Permiso denegado (403) | Empleado accede admin route | Error 403 | ALTA |

---

## 4. DATOS DE PRUEBA

### 4.1 Usuarios Test

```
Admin:
  Email: admin@test.com
  Password: AdminTest123!
  Rol: admin

Empleado 1:
  Email: empleado@test.com
  Password: EmpleadoTest123!
  Rol: employee
  Nombre: Juan Carlos Pérez
  Cédula: 1234567890
  Salario: $1,500,000 COP/mes
  Valor-hora: $8,246.64

Empleado 2:
  Nombre: María González López
  Cédula: 9876543210
  Salario: $2,000,000 COP/mes
  Valor-hora: $10,995.53
```

### 4.2 Datos de Turno

```
Turno Matutino:
  Fecha: 15/01/2024
  Hora Inicio: 06:00
  Hora Fin: 14:00
  Duración: 8 horas
  Tipo: Morning

Turno Nocturno:
  Fecha: 15/01/2024
  Hora Inicio: 21:00
  Hora Fin: 06:00 (16/01/2024)
  Duración: 9 horas
  Tipo: Night

Turno Vespertino:
  Hora Inicio: 14:00
  Hora Fin: 22:00
  Duración: 8 horas
```

### 4.3 Datos de Asistencia

```
Asistencia Normal (8h):
  Entrada: 06:00
  Salida: 14:00
  Estado: completed

Asistencia Overtime (12h):
  Entrada: 06:00
  Salida: 18:00
  Estado: completed

Asistencia Nocturna (9h):
  Entrada: 21:00
  Salida: 06:00 siguiente
  Estado: completed

Asistencia Sin Salida:
  Entrada: 06:00
  Salida: NULL
  Estado: in_progress
```

---

## 5. COBERTURA ESPERADA

### 5.1 Cobertura de Código

| Componente | Cobertura Esperada | Herramienta |
|---|---|---|
| Modelos (models/) | 95% | pytest --cov |
| Rutas (routes/) | 85% | pytest --cov |
| Servicios (services/) | 90% | pytest --cov |
| Utilidades (utils/) | 80% | pytest --cov |
| **Total** | **85%** | **pytest-cov** |

### 5.2 Cobertura de Requisitos

| Requisito | Pruebas | Estado |
|---|---|---|
| Autenticación segura | AUTH-001 a AUTH-007 | En Pruebas |
| CRUD de empleados | EMP-001 a EMP-010 | En Pruebas |
| Gestión de asistencia | ATT-001 a ATT-004 | En Pruebas |
| Cálculos de nómina | PAY-001 a PAY-007 | En Pruebas |
| Normativa colombiana | PAY-001 a PAY-005 | En Pruebas |
| Control de acceso | EMP-009, PAY-007 | En Pruebas |

---

## 6. AMBIENTE DE PRUEBAS

### 6.1 Configuración

```
Sistema Operativo: Windows 10+
Python: 3.11+
Base de Datos: SQLite in-memory
Navegador: Chrome/Firefox (para manual)
```

### 6.2 Herramientas

| Herramienta | Versión | Propósito |
|---|---|---|
| pytest | 7.4.3 | Framework de pruebas |
| pytest-cov | 4.1.0 | Cobertura de código |
| pytest-flask | 1.3.0 | Integración con Flask |
| Flask | 3.0.3 | Aplicación web |
| SQLAlchemy | 3.1.1 | ORM |

### 6.3 Estructura de Archivos

```
tests/
├── __init__.py
├── conftest.py              # Configuración global pytest
├── pytest.ini               # Opciones pytest
├── unit/                    # Pruebas unitarias
│   ├── __init__.py
│   └── test_models.py
├── integration/             # Pruebas integración
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_employees.py
│   └── test_payroll.py
└── fixtures/                # Datos de prueba
    └── __init__.py
```

---

## 7. PROCEDIMIENTOS DE EJECUCIÓN

### 7.1 Instalación

```bash
# 1. Instalar dependencias base
pip install -r requirements.txt

# 2. Instalar dependencias de prueba
pip install -r requirements-test.txt

# 3. Verificar instalación
pytest --version
python -m pytest --version
```

### 7.2 Ejecución de Pruebas

#### Ejecutar todas las pruebas
```bash
pytest
```

#### Ejecutar solo pruebas unitarias
```bash
pytest tests/unit/ -v
```

#### Ejecutar solo pruebas de integración
```bash
pytest tests/integration/ -v
```

#### Ejecutar prueba específica
```bash
pytest tests/unit/test_models.py::TestUserModel::test_user_password_hashing -v
```

#### Ejecutar con cobertura
```bash
pytest --cov=app --cov-report=html
```

#### Ejecutar con marcadores
```bash
# Solo pruebas críticas
pytest -m "critical"

# Solo autenticación
pytest -m "auth"

# Solo empleados
pytest -m "employee"
```

### 7.3 Reporte de Cobertura

```bash
# Generar reporte HTML
pytest --cov=app --cov-report=html

# Abrir reporte en navegador
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### 7.4 Análisis de Código

```bash
# Verificar estilo (PEP8)
flake8 app/ tests/

# Formatear código
black app/ tests/

# Análisis estático
pylint app/

# Type checking
mypy app/
```

---

## 8. CRITERIOS DE ÉXITO

### 8.1 Criterios de Aceptación

Funcional
- Todas las pruebas unitarias pasan (100%)
- Todas las pruebas de integración pasan (100%)
- Cobertura mínima 85% de código

Normativa
- Cálculos cumplen Ley 1846/2017 colombiana
- Validaciones previenen datos inválidos
- Control de acceso funciona correctamente

Calidad
- Código sigue PEP8
- Sin warnings en linter
- Documentación actualizada

### 8.2 Criterios de Liberación

- 100% de pruebas pasan
- Cobertura ≥ 85%
- 0 errores críticos/bloqueadores
- Revisión de código completada

### 8.3 Métricas

| Métrica | Objetivo | Actual |
|---|---|---|
| Pruebas Totales | 50+ | ~45 |
| Cobertura Líneas | 85%+ | Por calcular |
| Pruebas Críticas | 100% paso | En progreso |
| Tiempo Ejecución | < 30s | Por calcular |

---

## 9. GESTIÓN DE DEFECTOS

### 9.1 Severidad

| Nivel | Descripción | Ejemplo |
|---|---|---|
| CRÍTICA | Bloquea funcionalidad | Falla en login, cálculo nómina incorrecto |
| ALTA | Afecta múltiples usuarios | Permiso incorrecto, validación falla |
| MEDIA | Afecta funcionalidad específica | Error en reporte, UI mal alineada |
| BAJA | Mejora/cosmético | Typo, color incorrecto |

### 9.2 Flujo de Defectos

1. **Descubierto:** Se abre issue con reproducción
2. **Asignado:** Dev asignado para investigación
3. **En Progreso:** Dev trabaja en fix
4. **Verificado:** QA verifica que fix resuelve
5. **Cerrado:** Integrado en main branch

### 9.3 Seguimiento

Usar GitHub Issues o similar con etiquetas:
- `bug` - Defecto confirmado
- `critical` - Bloquea release
- `test-failure` - Falla en prueba
- `in-progress` - Siendo corregido

---

## 10. REPORTES Y DOCUMENTACIÓN

### 10.1 Reportes Automáticos

```bash
# Reporte de pruebas JSON
pytest --json-report --json-report-file=report.json

# Reporte HTML
pytest --html=report.html --self-contained-html
```

### 10.2 Documentación

- [README.md](../README.md) - Instrucciones de uso
- [TESTING.md](./TESTING.md) - Guía de pruebas
- [tests/conftest.py](./conftest.py) - Fixtures disponibles
- Docstrings en código

### 10.3 Registro de Ejecución

Cada ejecución debe registrar:
- Fecha y hora
- Versión del código
- Pruebas ejecutadas
- Resultados (pass/fail)
- Cobertura alcanzada
- Defectos encontrados

---

## 11. MANTENIMIENTO Y EVOLUCIÓN

### 11.1 Actualización de Pruebas

Cuando se agregue funcionalidad:
1. Crear casos de prueba en este documento
2. Implementar pruebas en código
3. Actualizar fixtures si necesario
4. Ejecutar cobertura
5. Actualizar métricas

### 11.2 Refactorización

Cada trimestre:
- Revisar cobertura de código
- Eliminar pruebas obsoletas
- Consolidar duplicadas
- Optimizar rendimiento

### 11.3 Integración Continua

Configurar en GitHub Actions:
```yaml
- Ejecutar pytest en cada push
- Validar cobertura mínima
- Fallar si cobertura baja
- Generar reporte
```

---

## 12. CONCLUSIÓN

Este plan define una estrategia completa de pruebas para garantizar calidad, confiabilidad y cumplimiento normativo del sistema de gestión de nómina. La ejecución rigurosa de estos casos asegura que:

- El sistema cumple funcionalidad requerida
- Los cálculos son precisos según normativa
- La seguridad y control de acceso funcionan
- Los datos se mantienen íntegros
- Se facilita mantenimiento futuro

---

Aprobado por: [Nombre]  
Fecha: Enero 2024  
Versión: 1.0  
Próxima revisión: Abril 2024
