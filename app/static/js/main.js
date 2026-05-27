/**
 * main.js — Utilidades globales del frontend de TurnosPro
 *
 * Funcionalidades:
 *  1. Auto-dismiss de alertas flash después de 5 segundos.
 *  2. Animación de entrada escalonada para filas de tabla.
 *  3. Tooltips de Bootstrap.
 *  4. Confirmación antes de acciones destructivas.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ----------------------------------------------------------------
    // 1. Auto-dismiss de alertas flash (5 segundos)
    // ----------------------------------------------------------------
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(function (alert, index) {
        // Ocultar escalonado: cada alerta espera 200ms más que la anterior
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000 + index * 200);
    });

    // ----------------------------------------------------------------
    // 2. Animación escalonada en filas de tabla
    // ----------------------------------------------------------------
    const tableRows = document.querySelectorAll('.table-row-animate');
    tableRows.forEach(function (row, index) {
        row.style.animationDelay = `${index * 40}ms`;
    });

    // ----------------------------------------------------------------
    // 3. Inicializar tooltips de Bootstrap
    // ----------------------------------------------------------------
    const tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggers.forEach(function (el) {
        new bootstrap.Tooltip(el, { placement: 'top' });
    });

    // ----------------------------------------------------------------
    // 4. Feedback visual en botones de formulario al hacer submit
    // ----------------------------------------------------------------
    const clockForms = document.querySelectorAll('#clockInForm, #clockOutForm');
    clockForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.style.opacity = '0.7';
                btn.style.cursor = 'wait';
                btn.disabled = true;
            }
        });
    });

    // ----------------------------------------------------------------
    // 5. Formato de números con separadores de miles (COP)
    // ----------------------------------------------------------------
    document.querySelectorAll('[data-currency]').forEach(function (el) {
        const value = parseFloat(el.dataset.currency);
        if (!isNaN(value)) {
            el.textContent = '$ ' + value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
    });

});
