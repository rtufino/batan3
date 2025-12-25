from flask import Blueprint, render_template, redirect, url_for, flash, make_response, request
from app.extensions import db
from app.models import Movimiento, Departamento, Rubro, Cuenta, Proveedor
from app.forms import ConfirmarPagoForm, GastoForm, TransferenciaForm
from app.utils import generar_pdf_recibo
from datetime import datetime
from sqlalchemy import func, extract

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')

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
    # Obtener parámetros de la URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    tipo_filter = request.args.get('tipo', '')
    estado_filter = request.args.get('estado', '')
    sort_by = request.args.get('sort_by', 'fecha_emision')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Validar per_page
    if per_page not in [10, 12, 25, 50]:
        per_page = 12
    
    # Construir la consulta base
    query = Movimiento.query
    
    # Aplicar filtros
    if tipo_filter:
        query = query.filter_by(tipo=tipo_filter)
    
    if estado_filter:
        query = query.filter_by(estado=estado_filter)
    
    # Aplicar ordenamiento
    if sort_by == 'fecha_emision':
        order_column = Movimiento.fecha_emision
    elif sort_by == 'fecha_pago':
        order_column = Movimiento.fecha_pago
    else:
        order_column = Movimiento.fecha_emision
    
    if sort_order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # Ejecutar paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movimientos = pagination.items
    
    return render_template('finanzas/historial.html',
                         movimientos=movimientos,
                         pagination=pagination,
                         tipo_filter=tipo_filter,
                         estado_filter=estado_filter,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         per_page=per_page)

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
        monto = float(movimiento.monto)  # Convertir Decimal a float
        
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

@finanzas_bp.route('/transferencia', methods=['GET', 'POST'])
def nueva_transferencia():
    form = TransferenciaForm()
    cuentas = Cuenta.query.all()
    form.cuenta_origen_id.choices = [(c.id, f"{c.nombre} (${c.saldo:.2f})") for c in cuentas]
    form.cuenta_destino_id.choices = [(c.id, c.nombre) for c in cuentas]

    if form.validate_on_submit():
        if form.cuenta_origen_id.data == form.cuenta_destino_id.data:
            flash('La cuenta de origen y destino no pueden ser la misma.', 'danger')
            return render_template('finanzas/transferencia.html', form=form)

        c_origen = Cuenta.query.get(form.cuenta_origen_id.data)
        c_destino = Cuenta.query.get(form.cuenta_destino_id.data)
        monto = float(form.monto.data)

        if c_origen.saldo < monto:
            flash(f'Saldo insuficiente en {c_origen.nombre}.', 'danger')
            return render_template('finanzas/transferencia.html', form=form)

        try:
            # 1. Movimiento de Salida (EGRESO)
            salida = Movimiento(
                tipo='EGRESO', estado='PAGADO', monto=monto,
                descripcion=f"{c_origen.nombre} -> {c_destino.nombre}",
                fecha_emision=datetime.combine(form.fecha.data, datetime.min.time()),
                fecha_pago=datetime.combine(form.fecha.data, datetime.min.time()),
                es_transferencia=True, cuenta_id=c_origen.id,
                rubro_id=Rubro.query.filter_by(nombre="Transferencia Interna").first().id
            )
            # 2. Movimiento de Entrada (INGRESO)
            entrada = Movimiento(
                tipo='INGRESO', estado='PAGADO', monto=monto,
                descripcion=f"{c_origen.nombre} -> {c_destino.nombre}",
                fecha_emision=datetime.combine(form.fecha.data, datetime.min.time()),
                fecha_pago=datetime.combine(form.fecha.data, datetime.min.time()),
                es_transferencia=True, cuenta_id=c_destino.id,
                rubro_id=Rubro.query.filter_by(nombre="Transferencia Interna").first().id
            )
            
            # 3. Actualizar Saldos Físicos
            c_origen.saldo -= monto
            c_destino.saldo += monto

            db.session.add_all([salida, entrada])
            db.session.commit()
            flash('Transferencia realizada con éxito.', 'success')
            return redirect(url_for('finanzas.historial'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('finanzas/transferencia.html', form=form)

@finanzas_bp.route('/reportes')
def reportes():
    hoy = datetime.now()
    
    # 1. GASTOS POR RUBRO (Mes Actual - Solo lo ya PAGADO)
    # Filtramos por Egreso, Pagado y el mes/año en curso
    gastos_query = db.session.query(
        Rubro.nombre,
        func.sum(Movimiento.monto).label('total')
    ).join(Movimiento).filter(
        Movimiento.tipo == 'EGRESO',
        Movimiento.estado == 'PAGADO',
        extract('month', Movimiento.fecha_pago) == hoy.month,
        extract('year', Movimiento.fecha_pago) == hoy.year
    ).group_by(Rubro.nombre).all()

    # Preparamos las listas para Chart.js
    labels_gastos = [g.nombre for g in gastos_query]
    values_gastos = [float(g.total) for g in gastos_query]

    # 2. AUDITORÍA DE MOROSIDAD (Para comparar)
    # Departamentos que más deben (Ingresos Pendientes)
    morosidad = db.session.query(
        Departamento.numero,
        func.sum(Movimiento.monto).label('total_deuda')
    ).join(Movimiento).filter(
        Movimiento.tipo == 'INGRESO',
        Movimiento.estado == 'PENDIENTE'
    ).group_by(Departamento.numero).order_by(func.sum(Movimiento.monto).desc()).limit(5).all()

    return render_template('finanzas/reportes.html', 
                           labels_gastos=labels_gastos, 
                           values_gastos=values_gastos,
                           morosidad=morosidad,
                           mes_anio=hoy.strftime('%m / %Y'))