from flask import Blueprint, render_template
from app.models import Movimiento, Cuenta
from app.extensions import db
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    # Obtenemos las cuentas
    cuentas = Cuenta.query.all()
    
    # Estructura para pasar al template
    resumen_cuentas = []
    saldo_total_global = 0.0

    for cta in cuentas:
        # Sumar ingresos de esta cuenta
        ingresos = db.session.query(func.sum(Movimiento.monto)).filter_by(cuenta_id=cta.id, tipo='INGRESO').scalar() or 0
        # Sumar egresos de esta cuenta
        egresos = db.session.query(func.sum(Movimiento.monto)).filter_by(cuenta_id=cta.id, tipo='EGRESO').scalar() or 0
        
        saldo_actual = cta.saldo_inicial + ingresos - egresos
        saldo_total_global += saldo_actual
        
        resumen_cuentas.append({
            'nombre': cta.nombre,
            'tipo': cta.tipo,
            'saldo': saldo_actual
        })

    context = {
        'titulo': 'Panel de Control',
        'cuentas': resumen_cuentas,
        'saldo_total': saldo_total_global,
        # 'alertas_mantenimiento': ... (puedes mantener lo previo)
    }
    return render_template('admin/dashboard.html', **context)