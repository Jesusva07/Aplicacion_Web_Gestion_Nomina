#!/usr/bin/env python
"""
run_tests.py — Script de ejecución de pruebas para TurnosPro.

Uso:
    python run_tests.py                    # Ejecutar todas
    python run_tests.py --coverage         # Con cobertura
    python run_tests.py --unit            # Solo unitarias
    python run_tests.py --integration     # Solo integración
    python run_tests.py --auth            # Solo autenticación
    python run_tests.py --verbose          # Verboso
    python run_tests.py --failed           # Últimas fallidas
    python run_tests.py --help             # Ver opciones
"""

import subprocess
import sys
import argparse
from pathlib import Path

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Imprime encabezado."""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Imprime mensaje de éxito."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Imprime mensaje de error."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    """Imprime mensaje informativo."""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")


def run_command(cmd, description=""):
    """Ejecuta comando y retorna código de salida."""
    if description:
        print_info(f"Ejecutando: {description}")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Script de ejecución de pruebas TurnosPro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_tests.py                    # Todas las pruebas
  python run_tests.py --coverage         # Con cobertura HTML
  python run_tests.py --unit --verbose   # Pruebas unitarias verbosas
  python run_tests.py --auth -x          # Auth, parar en fallo
  python run_tests.py --lf               # Últimas fallidas
        """
    )
    
    # Argumentos
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generar reporte de cobertura HTML"
    )
    
    parser.add_argument(
        "-u", "--unit",
        action="store_true",
        help="Ejecutar solo pruebas unitarias"
    )
    
    parser.add_argument(
        "-i", "--integration",
        action="store_true",
        help="Ejecutar solo pruebas de integración"
    )
    
    parser.add_argument(
        "-a", "--auth",
        action="store_true",
        help="Ejecutar solo pruebas de autenticación"
    )
    
    parser.add_argument(
        "-e", "--employees",
        action="store_true",
        help="Ejecutar solo pruebas de empleados"
    )
    
    parser.add_argument(
        "-p", "--payroll",
        action="store_true",
        help="Ejecutar solo pruebas de nómina"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Salida verbosa (-vv para muy verbosa)"
    )
    
    parser.add_argument(
        "-vv", "--very-verbose",
        action="store_true",
        help="Salida muy verbosa (incluyendo prints)"
    )
    
    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Parar en primer fallo"
    )
    
    parser.add_argument(
        "--lf", "--last-failed",
        action="store_true",
        help="Ejecutar últimas pruebas fallidas"
    )
    
    parser.add_argument(
        "-s", "--show",
        action="store_true",
        help="Mostrar prints y outputs (solo con -v)"
    )
    
    parser.add_argument(
        "--markers",
        action="store_true",
        help="Mostrar marcadores disponibles"
    )
    
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Solo colectar pruebas sin ejecutar"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generar reporte HTML (requiere pytest-html)"
    )
    
    args = parser.parse_args()
    
    # Mostrar marcadores
    if args.markers:
        print_header("Marcadores Disponibles")
        run_command("pytest --markers")
        return 0
    
    # Construir comando
    cmd = "pytest"
    
    # Especificar qué ejecutar
    if args.unit:
        cmd += " tests/unit/"
        test_type = "Pruebas Unitarias"
    elif args.integration:
        cmd += " tests/integration/"
        test_type = "Pruebas Integración"
    elif args.auth:
        cmd += " tests/integration/test_auth.py"
        test_type = "Pruebas Autenticación"
    elif args.employees:
        cmd += " tests/integration/test_employees.py"
        test_type = "Pruebas Empleados"
    elif args.payroll:
        cmd += " tests/integration/test_payroll.py"
        test_type = "Pruebas Nómina"
    else:
        test_type = "Todas las Pruebas"
    
    # Opciones generales
    if args.very_verbose:
        cmd += " -vv -s"
    elif args.verbose:
        cmd += " -v"
        if args.show:
            cmd += " -s"
    
    if args.exitfirst:
        cmd += " -x"
    
    if args.collect:
        cmd += " --collect-only"
    
    if args.lf or getattr(args, 'last_failed', False):
        cmd += " --lf"
    
    # Cobertura
    if args.coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term-missing"
        test_type += " (con Cobertura)"
    
    # HTML report
    if args.html:
        cmd += " --html=test-report.html --self-contained-html"
    
    # Ejecutar
    print_header(f"🧪 {test_type}")
    print_info(f"Comando: {cmd}\n")
    
    returncode = run_command(cmd, "")
    
    # Resultados
    print()
    if returncode == 0:
        print_success("¡Todas las pruebas pasaron!")
        if args.coverage:
            print_info("Reporte de cobertura: htmlcov/index.html")
        if args.html:
            print_info("Reporte HTML: test-report.html")
    else:
        print_error("Algunas pruebas fallaron")
        if args.verbose:
            print_info("Ejecuta con -x para parar en el primer fallo")
        else:
            print_info("Ejecuta con -v para ver más detalles")
    
    return returncode


if __name__ == "__main__":
    sys.exit(main())
