from flask import Blueprint, render_template, redirect, url_for, flash
from app.extensions import db
from app.models import Movimiento, Departamento, Rubro, Cuenta, Proveedor
from app.forms import IngresoForm, GastoForm
from datetime import datetime

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

@finanzas_bp.route('/ingreso/nuevo', methods=['GET', 'POST'])
def nuevo_ingreso():
    form = IngresoForm()
    
    # 1. Cargar las opciones de los SelectFields dinámicamente desde la BD
    # (Tuplas: valor, etiqueta)
    form.departamento_id.choices = [(d.id, f"Depto {d.numero} - {d.propietarios[0].nombre}") for d in Departamento.query.all()]
    
    # Filtramos solo rubros de tipo INGRESO
    form.rubro_id.choices = [(r.id, r.nombre) for r in Rubro.query.filter_by(tipo='INGRESO').all()]
    
    # Cargar cuentas
    form.cuenta_id.choices = [(c.id, f"{c.nombre} ({c.tipo})") for c in Cuenta.query.all()]

    # 2. Si el formulario se envió y es válido
    if form.validate_on_submit():
        # 1. Crear el movimiento
        nuevo_pago = Movimiento(
            tipo='INGRESO',
            estado='PAGADO', # Asumimos que si registras un ingreso, ya tienes el dinero
            monto=form.monto.data,
            fecha=datetime.combine(form.fecha.data, datetime.min.time()),
            descripcion=form.descripcion.data,
            rubro_id=form.rubro_id.data,
            departamento_id=form.departamento_id.data,
            cuenta_id=form.cuenta_id.data
        )

        # 2. ACTUALIZAR EL SALDO DE LA CUENTA
        cuenta = Cuenta.query.get(form.cuenta_id.data)
        cuenta.saldo += float(form.monto.data) # Sumamos porque es Ingreso
        
        try:
            db.session.add(nuevo_pago)
            db.session.commit()
            flash(f'Cobro registrado exitosamente: ${form.monto.data}', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar en base de datos: {str(e)}', 'danger')

    # 3. Si es GET o hubo error, mostramos el formulario
    # Pre-llenamos la fecha con el día de hoy
    if not form.fecha.data:
        form.fecha.data = datetime.now().date()

    return render_template('finanzas/nuevo_ingreso.html', form=form)

@finanzas_bp.route('/gasto/nuevo', methods=['GET', 'POST'])
def nuevo_gasto():
    form = GastoForm()
    
    # 1. Cargar opciones
    form.proveedor_id.choices = [(p.id, f"{p.nombre} ({p.categoria})") for p in Proveedor.query.all()]
    form.rubro_id.choices = [(r.id, r.nombre) for r in Rubro.query.filter_by(tipo='EGRESO').all()]
    form.cuenta_id.choices = [(c.id, f"{c.nombre} - ${c.saldo:.2f}") for c in Cuenta.query.all()]

    if form.validate_on_submit():
        # Validar fondos (Ahora es más fácil, usamos el campo directo)
        cuenta = Cuenta.query.get(form.cuenta_id.data)

        # Validar si hay saldo suficiente (Solo si el estado es PAGADO)
        if form.estado.data == 'PAGADO':
            if cuenta.saldo < float(form.monto.data):
                flash(f'Fondos insuficientes. Tienes ${cuenta.saldo:.2f}', 'danger')
                return render_template('finanzas/nuevo_gasto.html', form=form)

        nuevo_movimiento = Movimiento(
            tipo='EGRESO',
            estado=form.estado.data, # Puede ser PAGADO o PENDIENTE
            monto=form.monto.data,
            fecha=datetime.combine(form.fecha.data, datetime.min.time()),
            descripcion=form.descripcion.data,
            rubro_id=form.rubro_id.data,
            proveedor_id=form.proveedor_id.data,
            cuenta_id=form.cuenta_id.data
        )

        # ACTUALIZAR SALDO SOLO SI ESTÁ PAGADO
        if form.estado.data == 'PAGADO':
            cuenta.saldo -= float(form.monto.data) # Restamos porque es Gasto
        
        try:
            db.session.add(nuevo_movimiento)
            db.session.commit()
            
            msg_tipo = 'Pago registrado' if form.estado.data == 'PAGADO' else 'Deuda registrada'
            flash(f'{msg_tipo} exitosamente: -${form.monto.data}', 'warning') # Warning para color amarillo/naranja
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    if not form.fecha.data:
        form.fecha.data = datetime.now().date()

    return render_template('finanzas/nuevo_gasto.html', form=form)