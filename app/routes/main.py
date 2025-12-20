from flask import Blueprint, render_template
from app.models import Movimiento, Cuenta, Equipo
from app.extensions import db
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    # --- 1. TESORERÍA (Lectura directa súper rápida) ---
    cuentas = Cuenta.query.all()
    resumen_cuentas = []
    saldo_liquido_total = 0.0

    for cta in cuentas:
        saldo_liquido_total += cta.saldo # ¡Lectura directa!
        
        resumen_cuentas.append({
            'nombre': cta.nombre,
            'tipo': cta.tipo,
            'saldo': cta.saldo # ¡Lectura directa!
        })

    # --- 2. DEUDAS (Cuentas por Pagar) ---
    # Sumamos Egresos que están en estado 'PENDIENTE'
    deuda_por_pagar = db.session.query(func.sum(Movimiento.monto)).filter_by(
        tipo='EGRESO', estado='PENDIENTE').scalar() or 0

    # --- 3. COBRANZAS (Cuentas por Cobrar) ---
    # Sumamos Ingresos (Expensas) que están en estado 'PENDIENTE'
    # (Si en el seed no pusiste ingresos pendientes, esto será 0, pero el código queda listo)
    por_cobrar = db.session.query(func.sum(Movimiento.monto)).filter_by(
        tipo='INGRESO', estado='PENDIENTE').scalar() or 0

    # --- 4. BALANCE REAL (Patrimonio) ---
    # Lo que tengo + Lo que me deben - Lo que debo
    balance_patrimonial = saldo_liquido_total + por_cobrar - deuda_por_pagar
    
    # --- 5. OPERATIVO ---
    alertas_mantenimiento = Equipo.query.count()

    context = {
        'titulo': 'Panel Financiero',
        'cuentas': resumen_cuentas,
        'saldo_disponible': saldo_liquido_total,
        'deuda_por_pagar': deuda_por_pagar,
        'por_cobrar': por_cobrar,
        'balance_real': balance_patrimonial,
        'alertas_mantenimiento': alertas_mantenimiento
    }
    return render_template('admin/dashboard.html', **context)