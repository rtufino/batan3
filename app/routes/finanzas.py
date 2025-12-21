from flask import Blueprint, render_template, redirect, url_for, flash, make_response
from app.extensions import db
from app.models import Movimiento, Departamento, Rubro, Cuenta, Proveedor
from app.forms import ConfirmarPagoForm, IngresoForm, GastoForm
from app.utils import generar_pdf_recibo
from datetime import datetime

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

@finanzas_bp.route('/ingreso/nuevo', methods=['GET', 'POST'])
def nuevo_ingreso():
    form = IngresoForm()
    
    # 1. Cargar las opciones de los SelectFields dinámicamente desde la BD
    # (Tuplas: valor, etiqueta)
    form.departamento_id.choices = [(d.id, f"Depto {d.numero} - {d.personas[0].nombre}") for d in Departamento.query.all()]
    
    # Filtramos solo rubros de tipo INGRESO
    form.rubro_id.choices = [(r.id, r.nombre) for r in Rubro.query.filter_by(tipo='INGRESO').all()]
    
    # Cargar cuentas
    form.cuenta_id.choices = [(c.id, f"{c.nombre} ({c.tipo})") for c in Cuenta.query.all()]

    # 2. Si el formulario se envió y es válido
    if form.validate_on_submit():
        # 1. Crear el movimiento
        fecha_pago_dt = datetime.combine(form.fecha_pago.data, datetime.min.time())
        nuevo_pago = Movimiento(
            tipo='INGRESO',
            estado='PAGADO', # Asumimos que si registras un ingreso, ya tienes el dinero
            monto=form.monto.data,
            fecha_emision=fecha_pago_dt,  # Para ingresos inmediatos, emisión = pago
            fecha_pago=fecha_pago_dt,
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
    if not form.fecha_pago.data:
        form.fecha_pago.data = datetime.now().date()

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

        # Determinar fechas según el estado
        fecha_emision_dt = datetime.combine(form.fecha_emision.data, datetime.min.time())
        fecha_pago_dt = None
        
        if form.estado.data == 'PAGADO':
            # Si está pagado, usar la fecha_pago del formulario o la fecha_emision
            if form.fecha_pago.data:
                fecha_pago_dt = datetime.combine(form.fecha_pago.data, datetime.min.time())
            else:
                fecha_pago_dt = fecha_emision_dt  # Pago inmediato

        nuevo_movimiento = Movimiento(
            tipo='EGRESO',
            estado=form.estado.data, # Puede ser PAGADO o PENDIENTE
            monto=form.monto.data,
            fecha_emision=fecha_emision_dt,
            fecha_pago=fecha_pago_dt,
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

    if not form.fecha_emision.data:
        form.fecha_emision.data = datetime.now().date()
    if not form.fecha_pago.data and form.estado.data == 'PAGADO':
        form.fecha_pago.data = datetime.now().date()

    return render_template('finanzas/nuevo_gasto.html', form=form)

# 1. RUTA PARA VER EL HISTORIAL
@finanzas_bp.route('/historial')
def historial():
    # Obtenemos los últimos 50 movimientos ordenados por fecha de emisión descendente
    movimientos = Movimiento.query.order_by(Movimiento.fecha_emision.desc()).limit(50).all()
    return render_template('finanzas/historial.html', movimientos=movimientos)

# 2. RUTA PARA DESCARGAR RECIBO INDIVIDUAL
@finanzas_bp.route('/recibo/<int:id>')
def descargar_recibo(id):
    movimiento = Movimiento.query.get_or_404(id)
    
    # Generamos el PDF en memoria usando FPDF2
    pdf_buffer = generar_pdf_recibo(movimiento)
    
    # Preparamos la respuesta HTTP con los bytes del PDF
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    # 'inline' lo abre en el navegador. 'attachment' lo descarga.
    response.headers['Content-Disposition'] = f'inline; filename=Recibo_Batan3_{id}.pdf'
    
    return response

# RUTA PARA REGISTRAR PAGO DE MOVIMIENTO PENDIENTE
@finanzas_bp.route('/registrar-pago/<int:id>', methods=['GET', 'POST'])
def registrar_pago(id):
    movimiento = Movimiento.query.get_or_404(id)
    
    if movimiento.estado != 'PENDIENTE':
        flash('Este movimiento ya ha sido pagado.', 'warning')
        return redirect(url_for('finanzas.historial'))

    # REDIRECCIÓN SI ES EXPENSA:
    if movimiento.rubro and "Expensas Ordinarias" in movimiento.rubro.nombre:
        return redirect(url_for('condominos.registrar_pago', movimiento_id=movimiento.id))

    # FLUJO GENERAL PARA OTROS RUBROS:
    form = ConfirmarPagoForm()
    form.cuenta_id.choices = [(c.id, f"{c.nombre} (${c.saldo:.2f})") for c in Cuenta.query.all()]

    if form.validate_on_submit():
        cuenta = Cuenta.query.get(form.cuenta_id.data)
        monto = movimiento.monto
        
        try:
            movimiento.estado = 'PAGADO'
            movimiento.cuenta_id = cuenta.id
            # Convertimos date a datetime
            movimiento.fecha_pago = datetime.combine(form.fecha_pago.data, datetime.min.time())
            
            if form.observacion.data:
                movimiento.descripcion = f"{movimiento.descripcion} | Obs: {form.observacion.data}"
            
            # Afectar saldo según tipo
            if movimiento.tipo == 'INGRESO':
                cuenta.saldo += monto
            else: # EGRESO
                if cuenta.saldo < monto:
                    flash(f'Saldo insuficiente en {cuenta.nombre}', 'danger')
                    return render_template('finanzas/confirmar_pago.html', form=form, movimiento=movimiento)
                cuenta.saldo -= monto
            
            db.session.commit()
            flash('Transacción confirmada y saldo actualizado.', 'success')
            return redirect(url_for('finanzas.historial'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('finanzas/confirmar_pago.html', form=form, movimiento=movimiento)