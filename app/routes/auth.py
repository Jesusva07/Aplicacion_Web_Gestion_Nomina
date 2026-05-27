"""
app/routes/auth.py — Blueprint de autenticación.

Endpoints:
  GET  /auth/login   → Formulario de inicio de sesión.
  POST /auth/login   → Procesa credenciales y crea sesión.
  GET  /auth/logout  → Cierra la sesión del usuario actual.
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request
)
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User

# Prefijo /auth registrado en create_app()
auth_bp = Blueprint("auth", __name__, template_folder="../templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Maneja el formulario de inicio de sesión.
    
    GET:  Muestra el formulario de login.
    POST: Valida credenciales. Si son correctas, crea la sesión con
          Flask-Login y redirige al dashboard.
    """
    # Si el usuario ya tiene sesión activa, ir directo al dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember_me"))

        # Buscar usuario por email
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            # Mensaje genérico para no revelar si el email existe o no
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Tu cuenta está desactivada. Contacta al administrador.", "warning")
            return render_template("auth/login.html")

        # Crear sesión de usuario con Flask-Login
        # remember=True mantiene la sesión después de cerrar el navegador
        login_user(user, remember=remember)

        # Redirigir a la página solicitada originalmente (o al dashboard)
        next_page = request.args.get("next")
        flash(f"Bienvenido, {user.email}!", "success")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario actual y redirige al login."""
    logout_user()
    flash("Sesión cerrada exitosamente.", "info")
    return redirect(url_for("auth.login"))
