from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import (
    Rubro, Movimiento, Proveedor, Cuenta, Parametro,
    GastoRecurrente  # Agregar el nuevo modelo
)
from app.forms import (
    RubroForm, ProveedorForm, CuentaForm, ParametroForm,
    GastoRecurrenteForm  # Agregar el nuevo formulario
)
from sqlalchemy import func

config_bp = Blueprint('config', __name__, url_prefix='/config')

@config_bp.route('/')
def index():
    """Página principal de configuración con cards para cada sección"""
    return render_template('config/index.html')

@config_bp.route('/rubros')
def lista_rubros():
    """Lista todos los rubros con información de uso"""
    # Obtener todos los rubros con conteo de movimientos
    rubros_query = db.session.query(
        Rubro,
        func.count(Movimiento.id).label('num_movimientos')
    ).outerjoin(Movimiento).group_by(Rubro.id).order_by(Rubro.tipo, Rubro.nombre).all()
    
    rubros_data = []
    for rubro, num_movimientos in rubros_query:
        rubros_data.append({
            'rubro': rubro,
            'num_movimientos': num_movimientos,
            'puede_eliminar': num_movimientos == 0 and rubro.nombre != 'Expensas Ordinarias',
            'puede_editar': rubro.nombre != 'Expensas Ordinarias'
        })
    
    return render_template('config/rubros.html', rubros_data=rubros_data)

@config_bp.route('/rubros/nuevo', methods=['GET', 'POST'])
def nuevo_rubro():
    """Crear un nuevo rubro"""
    form = RubroForm()
    
    if form.validate_on_submit():
        # Verificar que no exista un rubro con el mismo nombre
        existe = Rubro.query.filter_by(nombre=form.nombre.data).first()
        if existe:
            flash(f'Ya existe un rubro con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/rubro_form.html', form=form, titulo='Nuevo Rubro')
        
        nuevo_rubro = Rubro(
            nombre=form.nombre.data,
            tipo=form.tipo.data
        )
        
        try:
            db.session.add(nuevo_rubro)
            db.session.commit()
            flash(f'Rubro "{nuevo_rubro.nombre}" creado exitosamente', 'success')
            return redirect(url_for('config.lista_rubros'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear rubro: {str(e)}', 'danger')
    
    return render_template('config/rubro_form.html', form=form, titulo='Nuevo Rubro')

@config_bp.route('/rubros/editar/<int:id>', methods=['GET', 'POST'])
def editar_rubro(id):
    """Editar un rubro existente"""
    rubro = Rubro.query.get_or_404(id)
    
    # No permitir editar "Expensas Ordinarias"
    if rubro.nombre == 'Expensas Ordinarias':
        flash('No se puede editar el rubro "Expensas Ordinarias"', 'warning')
        return redirect(url_for('config.lista_rubros'))
    
    form = RubroForm(obj=rubro)
    
    if form.validate_on_submit():
        # Verificar que no exista otro rubro con el mismo nombre
        existe = Rubro.query.filter(
            Rubro.nombre == form.nombre.data,
            Rubro.id != id
        ).first()
        
        if existe:
            flash(f'Ya existe otro rubro con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/rubro_form.html', form=form, titulo='Editar Rubro', rubro=rubro)
        
        rubro.nombre = form.nombre.data
        rubro.tipo = form.tipo.data
        
        try:
            db.session.commit()
            flash(f'Rubro "{rubro.nombre}" actualizado exitosamente', 'success')
            return redirect(url_for('config.lista_rubros'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar rubro: {str(e)}', 'danger')
    
    return render_template('config/rubro_form.html', form=form, titulo='Editar Rubro', rubro=rubro)

@config_bp.route('/rubros/eliminar/<int:id>', methods=['POST'])
def eliminar_rubro(id):
    """Eliminar un rubro"""
    rubro = Rubro.query.get_or_404(id)
    
    # No permitir eliminar "Expensas Ordinarias"
    if rubro.nombre == 'Expensas Ordinarias':
        flash('No se puede eliminar el rubro "Expensas Ordinarias"', 'danger')
        return redirect(url_for('config.lista_rubros'))
    
    # Verificar si tiene movimientos asociados
    num_movimientos = Movimiento.query.filter_by(rubro_id=id).count()
    
    if num_movimientos > 0:
        flash(f'No se puede eliminar el rubro "{rubro.nombre}" porque tiene {num_movimientos} movimiento(s) asociado(s)', 'danger')
        return redirect(url_for('config.lista_rubros'))
    
    try:
        nombre_rubro = rubro.nombre
        db.session.delete(rubro)
        db.session.commit()
        flash(f'Rubro "{nombre_rubro}" eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar rubro: {str(e)}', 'danger')
    
    return redirect(url_for('config.lista_rubros'))

# ==================== CRUD PROVEEDORES/BENEFICIARIOS ====================

@config_bp.route('/proveedores')
def lista_proveedores():
    """Lista todos los proveedores con información de uso"""
    # Obtener todos los proveedores con conteo de movimientos
    proveedores_query = db.session.query(
        Proveedor,
        func.count(Movimiento.id).label('num_movimientos')
    ).outerjoin(Movimiento).group_by(Proveedor.id).order_by(Proveedor.categoria, Proveedor.nombre).all()
    
    proveedores_data = []
    for proveedor, num_movimientos in proveedores_query:
        proveedores_data.append({
            'proveedor': proveedor,
            'num_movimientos': num_movimientos,
            'puede_eliminar': num_movimientos == 0
        })
    
    return render_template('config/proveedores.html', proveedores_data=proveedores_data)

@config_bp.route('/proveedores/nuevo', methods=['GET', 'POST'])
def nuevo_proveedor():
    """Crear un nuevo proveedor"""
    form = ProveedorForm()
    
    if form.validate_on_submit():
        # Verificar que no exista un proveedor con el mismo nombre
        existe = Proveedor.query.filter_by(nombre=form.nombre.data).first()
        if existe:
            flash(f'Ya existe un proveedor con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/proveedor_form.html', form=form, titulo='Nuevo Proveedor')
        
        nuevo_proveedor = Proveedor(
            nombre=form.nombre.data,
            ruc_cedula=form.ruc_cedula.data,
            telefono=form.telefono.data,
            email=form.email.data,
            banco=form.banco.data,
            tipo_cuenta=form.tipo_cuenta.data,
            numero_cuenta=form.numero_cuenta.data,
            categoria=form.categoria.data
        )
        
        try:
            db.session.add(nuevo_proveedor)
            db.session.commit()
            flash(f'Proveedor "{nuevo_proveedor.nombre}" creado exitosamente', 'success')
            return redirect(url_for('config.lista_proveedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear proveedor: {str(e)}', 'danger')
    
    return render_template('config/proveedor_form.html', form=form, titulo='Nuevo Proveedor')

@config_bp.route('/proveedores/editar/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):
    """Editar un proveedor existente"""
    proveedor = Proveedor.query.get_or_404(id)
    form = ProveedorForm(obj=proveedor)
    
    if form.validate_on_submit():
        # Verificar que no exista otro proveedor con el mismo nombre
        existe = Proveedor.query.filter(
            Proveedor.nombre == form.nombre.data,
            Proveedor.id != id
        ).first()
        
        if existe:
            flash(f'Ya existe otro proveedor con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/proveedor_form.html', form=form, titulo='Editar Proveedor', proveedor=proveedor)
        
        proveedor.nombre = form.nombre.data
        proveedor.ruc_cedula = form.ruc_cedula.data
        proveedor.telefono = form.telefono.data
        proveedor.email = form.email.data
        proveedor.banco = form.banco.data
        proveedor.tipo_cuenta = form.tipo_cuenta.data
        proveedor.numero_cuenta = form.numero_cuenta.data
        proveedor.categoria = form.categoria.data
        
        try:
            db.session.commit()
            flash(f'Proveedor "{proveedor.nombre}" actualizado exitosamente', 'success')
            return redirect(url_for('config.lista_proveedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}', 'danger')
    
    return render_template('config/proveedor_form.html', form=form, titulo='Editar Proveedor', proveedor=proveedor)

@config_bp.route('/proveedores/eliminar/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    """Eliminar un proveedor"""
    proveedor = Proveedor.query.get_or_404(id)
    
    # Verificar si tiene movimientos asociados
    num_movimientos = Movimiento.query.filter_by(proveedor_id=id).count()
    
    if num_movimientos > 0:
        flash(f'No se puede eliminar el proveedor "{proveedor.nombre}" porque tiene {num_movimientos} movimiento(s) asociado(s)', 'danger')
        return redirect(url_for('config.lista_proveedores'))
    
    try:
        nombre_proveedor = proveedor.nombre
        db.session.delete(proveedor)
        db.session.commit()
        flash(f'Proveedor "{nombre_proveedor}" eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar proveedor: {str(e)}', 'danger')
    
    return redirect(url_for('config.lista_proveedores'))

# ==================== CRUD CUENTAS ====================

@config_bp.route('/cuentas')
def lista_cuentas():
    """Lista todas las cuentas con información de uso"""
    # Obtener todas las cuentas con conteo de movimientos
    cuentas_query = db.session.query(
        Cuenta,
        func.count(Movimiento.id).label('num_movimientos')
    ).outerjoin(Movimiento).group_by(Cuenta.id).order_by(Cuenta.tipo, Cuenta.nombre).all()
    
    # Cuentas protegidas del sistema
    cuentas_protegidas = ['Banco Pichincha', 'Caja Chica']
    
    cuentas_data = []
    for cuenta, num_movimientos in cuentas_query:
        es_protegida = cuenta.nombre in cuentas_protegidas
        cuentas_data.append({
            'cuenta': cuenta,
            'num_movimientos': num_movimientos,
            'puede_eliminar': num_movimientos == 0 and not es_protegida,
            'es_protegida': es_protegida
        })
    
    return render_template('config/cuentas.html', cuentas_data=cuentas_data)

@config_bp.route('/cuentas/nueva', methods=['GET', 'POST'])
def nueva_cuenta():
    """Crear una nueva cuenta"""
    form = CuentaForm()
    
    if form.validate_on_submit():
        # Verificar que no exista una cuenta con el mismo nombre
        existe = Cuenta.query.filter_by(nombre=form.nombre.data).first()
        if existe:
            flash(f'Ya existe una cuenta con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/cuenta_form.html', form=form, titulo='Nueva Cuenta')
        
        nueva_cuenta = Cuenta(
            nombre=form.nombre.data,
            tipo=form.tipo.data,
            numero=form.numero.data,
            saldo_inicial=float(form.saldo_inicial.data),
            saldo=float(form.saldo_inicial.data)  # El saldo inicial es el saldo actual al crear
        )
        
        try:
            db.session.add(nueva_cuenta)
            db.session.commit()
            flash(f'Cuenta "{nueva_cuenta.nombre}" creada exitosamente con saldo inicial de ${nueva_cuenta.saldo_inicial:.2f}', 'success')
            return redirect(url_for('config.lista_cuentas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear cuenta: {str(e)}', 'danger')
    
    return render_template('config/cuenta_form.html', form=form, titulo='Nueva Cuenta')

@config_bp.route('/cuentas/editar/<int:id>', methods=['GET', 'POST'])
def editar_cuenta(id):
    """Editar una cuenta existente"""
    cuenta = Cuenta.query.get_or_404(id)
    
    # Verificar si tiene movimientos
    num_movimientos = Movimiento.query.filter_by(cuenta_id=id).count()
    tiene_movimientos = num_movimientos > 0
    
    form = CuentaForm(obj=cuenta)
    
    # Pre-cargar el saldo inicial actual
    if request.method == 'GET':
        form.saldo_inicial.data = cuenta.saldo_inicial
    
    if form.validate_on_submit():
        # Verificar que no exista otra cuenta con el mismo nombre
        existe = Cuenta.query.filter(
            Cuenta.nombre == form.nombre.data,
            Cuenta.id != id
        ).first()
        
        if existe:
            flash(f'Ya existe otra cuenta con el nombre "{form.nombre.data}"', 'warning')
            return render_template('config/cuenta_form.html', form=form, titulo='Editar Cuenta', cuenta=cuenta, tiene_movimientos=tiene_movimientos, num_movimientos=num_movimientos)
        
        # Si tiene movimientos, no permitir cambiar el saldo inicial
        if tiene_movimientos and float(form.saldo_inicial.data) != cuenta.saldo_inicial:
            flash(f'No se puede modificar el saldo inicial porque la cuenta tiene {num_movimientos} movimiento(s) asociado(s)', 'danger')
            return render_template('config/cuenta_form.html', form=form, titulo='Editar Cuenta', cuenta=cuenta, tiene_movimientos=tiene_movimientos, num_movimientos=num_movimientos)
        
        cuenta.nombre = form.nombre.data
        cuenta.tipo = form.tipo.data
        cuenta.numero = form.numero.data
        # Solo actualizar saldo_inicial si no tiene movimientos
        if not tiene_movimientos:
            cuenta.saldo_inicial = float(form.saldo_inicial.data)
            cuenta.saldo = float(form.saldo_inicial.data)  # Ajustar saldo actual
        
        try:
            db.session.commit()
            flash(f'Cuenta "{cuenta.nombre}" actualizada exitosamente', 'success')
            return redirect(url_for('config.lista_cuentas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar cuenta: {str(e)}', 'danger')
    
    return render_template('config/cuenta_form.html', form=form, titulo='Editar Cuenta', cuenta=cuenta, tiene_movimientos=tiene_movimientos, num_movimientos=num_movimientos)

@config_bp.route('/cuentas/eliminar/<int:id>', methods=['POST'])
def eliminar_cuenta(id):
    """Eliminar una cuenta"""
    cuenta = Cuenta.query.get_or_404(id)
    
    # No permitir eliminar cuentas del sistema
    cuentas_protegidas = ['Banco Pichincha', 'Caja Chica']
    if cuenta.nombre in cuentas_protegidas:
        flash(f'No se puede eliminar la cuenta "{cuenta.nombre}" porque es una cuenta del sistema', 'danger')
        return redirect(url_for('config.lista_cuentas'))
    
    # Verificar si tiene movimientos asociados
    num_movimientos = Movimiento.query.filter_by(cuenta_id=id).count()
    
    if num_movimientos > 0:
        flash(f'No se puede eliminar la cuenta "{cuenta.nombre}" porque tiene {num_movimientos} movimiento(s) asociado(s)', 'danger')
        return redirect(url_for('config.lista_cuentas'))
    
    try:
        nombre_cuenta = cuenta.nombre
        db.session.delete(cuenta)
        db.session.commit()
        flash(f'Cuenta "{nombre_cuenta}" eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cuenta: {str(e)}', 'danger')
    
    return redirect(url_for('config.lista_cuentas'))

# ==================== CRUD PARÁMETROS ====================

@config_bp.route('/parametros')
def lista_parametros():
    """Lista todos los parámetros organizados por categoría"""
    # Obtener todos los parámetros ordenados por categoría y clave
    parametros = Parametro.query.order_by(Parametro.categoria, Parametro.clave).all()
    
    # Agrupar por categoría
    parametros_por_categoria = {}
    for param in parametros:
        categoria = param.categoria or 'SIN_CATEGORIA'
        if categoria not in parametros_por_categoria:
            parametros_por_categoria[categoria] = []
        parametros_por_categoria[categoria].append(param)
    
    return render_template('config/parametros.html', parametros_por_categoria=parametros_por_categoria)

@config_bp.route('/parametros/nuevo', methods=['GET', 'POST'])
def nuevo_parametro():
    """Crear un nuevo parámetro"""
    form = ParametroForm()
    
    if form.validate_on_submit():
        # Verificar que no exista un parámetro con la misma clave
        existe = Parametro.query.filter_by(clave=form.clave.data).first()
        if existe:
            flash(f'Ya existe un parámetro con la clave "{form.clave.data}"', 'warning')
            return render_template('config/parametro_form.html', form=form, titulo='Nuevo Parámetro')
        
        # Validar el valor según el tipo
        valor = form.valor.data
        tipo = form.tipo.data
        
        try:
            if tipo == 'NUMBER':
                float(valor)  # Validar que sea número
            elif tipo == 'BOOLEAN':
                if valor.lower() not in ('true', 'false', '1', '0', 'si', 'no', 'sí'):
                    raise ValueError('Valor booleano inválido')
            elif tipo == 'DATE':
                from datetime import datetime
                datetime.strptime(valor, '%Y-%m-%d')  # Validar formato de fecha
        except ValueError as e:
            flash(f'Valor inválido para el tipo {tipo}: {str(e)}', 'danger')
            return render_template('config/parametro_form.html', form=form, titulo='Nuevo Parámetro')
        
        nuevo_parametro = Parametro(
            clave=form.clave.data,
            valor=valor,
            tipo=tipo,
            descripcion=form.descripcion.data,
            categoria=form.categoria.data,
            editable=form.editable.data
        )
        
        try:
            db.session.add(nuevo_parametro)
            db.session.commit()
            flash(f'Parámetro "{nuevo_parametro.clave}" creado exitosamente', 'success')
            return redirect(url_for('config.lista_parametros'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear parámetro: {str(e)}', 'danger')
    
    return render_template('config/parametro_form.html', form=form, titulo='Nuevo Parámetro')

@config_bp.route('/parametros/editar/<int:id>', methods=['GET', 'POST'])
def editar_parametro(id):
    """Editar un parámetro existente"""
    parametro = Parametro.query.get_or_404(id)
    
    # Verificar si es editable
    if not parametro.editable:
        flash(f'El parámetro "{parametro.clave}" no es editable', 'warning')
        return redirect(url_for('config.lista_parametros'))
    
    form = ParametroForm(obj=parametro)
    
    if form.validate_on_submit():
        # Verificar que no exista otro parámetro con la misma clave
        existe = Parametro.query.filter(
            Parametro.clave == form.clave.data,
            Parametro.id != id
        ).first()
        
        if existe:
            flash(f'Ya existe otro parámetro con la clave "{form.clave.data}"', 'warning')
            return render_template('config/parametro_form.html', form=form, titulo='Editar Parámetro', parametro=parametro)
        
        # Validar el valor según el tipo
        valor = form.valor.data
        tipo = form.tipo.data
        
        try:
            if tipo == 'NUMBER':
                float(valor)
            elif tipo == 'BOOLEAN':
                if valor.lower() not in ('true', 'false', '1', '0', 'si', 'no', 'sí'):
                    raise ValueError('Valor booleano inválido')
            elif tipo == 'DATE':
                from datetime import datetime
                datetime.strptime(valor, '%Y-%m-%d')
        except ValueError as e:
            flash(f'Valor inválido para el tipo {tipo}: {str(e)}', 'danger')
            return render_template('config/parametro_form.html', form=form, titulo='Editar Parámetro', parametro=parametro)
        
        parametro.clave = form.clave.data
        parametro.valor = valor
        parametro.tipo = tipo
        parametro.descripcion = form.descripcion.data
        parametro.categoria = form.categoria.data
        parametro.editable = form.editable.data
        
        try:
            db.session.commit()
            flash(f'Parámetro "{parametro.clave}" actualizado exitosamente', 'success')
            return redirect(url_for('config.lista_parametros'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar parámetro: {str(e)}', 'danger')
    
    return render_template('config/parametro_form.html', form=form, titulo='Editar Parámetro', parametro=parametro)

@config_bp.route('/parametros/eliminar/<int:id>', methods=['POST'])
def eliminar_parametro(id):
    """Eliminar un parámetro"""
    parametro = Parametro.query.get_or_404(id)
    
    # Verificar si es editable (solo los editables se pueden eliminar)
    if not parametro.editable:
        flash(f'No se puede eliminar el parámetro "{parametro.clave}" porque no es editable', 'danger')
        return redirect(url_for('config.lista_parametros'))
    
    try:
        clave_parametro = parametro.clave
        db.session.delete(parametro)
        db.session.commit()
        flash(f'Parámetro "{clave_parametro}" eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar parámetro: {str(e)}', 'danger')
    
    return redirect(url_for('config.lista_parametros'))

# ==================== CRUD GASTOS RECURRENTES ====================

@config_bp.route('/gastos-recurrentes')
def lista_gastos_recurrentes():
    """Lista todos los gastos recurrentes"""
    from app.models import GastoRecurrente
    gastos = GastoRecurrente.query.order_by(GastoRecurrente.descripcion).all()
    return render_template('config/gastos_recurrentes.html', gastos=gastos)

@config_bp.route('/gastos-recurrentes/nuevo', methods=['GET', 'POST'])
def nuevo_gasto_recurrente():
    """Crear un nuevo gasto recurrente"""
    from app.models import GastoRecurrente
    from app.forms import GastoRecurrenteForm
    
    form = GastoRecurrenteForm()
    
    if form.validate_on_submit():
        # Verificar que no exista un gasto con la misma descripción
        existe = GastoRecurrente.query.filter_by(descripcion=form.descripcion.data).first()
        if existe:
            flash(f'Ya existe un gasto recurrente con la descripción "{form.descripcion.data}"', 'warning')
            return render_template('config/gasto_recurrente_form.html', form=form, titulo='Nuevo Gasto Recurrente')
        
        nuevo_gasto = GastoRecurrente(
            descripcion=form.descripcion.data,
            tipo_periodicidad=form.tipo_periodicidad.data,
            meses_base=form.meses_base.data,
            monto=form.monto.data,
            notas=form.notas.data
        )
        
        try:
            db.session.add(nuevo_gasto)
            db.session.commit()
            flash(f'Gasto Recurrente "{nuevo_gasto.descripcion}" creado exitosamente', 'success')
            return redirect(url_for('config.lista_gastos_recurrentes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear gasto recurrente: {str(e)}', 'danger')
    
    return render_template('config/gasto_recurrente_form.html', form=form, titulo='Nuevo Gasto Recurrente')

@config_bp.route('/gastos-recurrentes/editar/<int:id>', methods=['GET', 'POST'])
def editar_gasto_recurrente(id):
    """Editar un gasto recurrente existente"""
    from app.models import GastoRecurrente
    from app.forms import GastoRecurrenteForm
    
    gasto = GastoRecurrente.query.get_or_404(id)
    form = GastoRecurrenteForm(obj=gasto)
    
    if form.validate_on_submit():
        # Verificar que no exista otro gasto con la misma descripción
        existe = GastoRecurrente.query.filter(
            GastoRecurrente.descripcion == form.descripcion.data,
            GastoRecurrente.id != id
        ).first()
        
        if existe:
            flash(f'Ya existe otro gasto recurrente con la descripción "{form.descripcion.data}"', 'warning')
            return render_template('config/gasto_recurrente_form.html', form=form, titulo='Editar Gasto Recurrente', gasto=gasto)
        
        gasto.descripcion = form.descripcion.data
        gasto.tipo_periodicidad = form.tipo_periodicidad.data
        gasto.meses_base = form.meses_base.data
        gasto.monto = form.monto.data
        gasto.notas = form.notas.data
        
        try:
            db.session.commit()
            flash(f'Gasto Recurrente "{gasto.descripcion}" actualizado exitosamente', 'success')
            return redirect(url_for('config.lista_gastos_recurrentes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar gasto recurrente: {str(e)}', 'danger')
    
    return render_template('config/gasto_recurrente_form.html', form=form, titulo='Editar Gasto Recurrente', gasto=gasto)

@config_bp.route('/gastos-recurrentes/eliminar/<int:id>', methods=['POST'])
def eliminar_gasto_recurrente(id):
    """Eliminar un gasto recurrente"""
    from app.models import GastoRecurrente
    
    gasto = GastoRecurrente.query.get_or_404(id)
    
    try:
        descripcion_gasto = gasto.descripcion
        db.session.delete(gasto)
        db.session.commit()
        flash(f'Gasto Recurrente "{descripcion_gasto}" eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar gasto recurrente: {str(e)}', 'danger')
    
    return redirect(url_for('config.lista_gastos_recurrentes'))

def reiniciar_gastos_recurrentes_mensualmente():
   """
   Tarea programada para reiniciar los gastos recurrentes al inicio de cada mes.
   Esta función debe ser llamada por un sistema de tareas programadas como Celery o APScheduler.
   """
   from datetime import datetime
   from app.extensions import db
   from app.models import GastoRecurrente

   # Obtener el mes actual
   mes_actual = datetime.now().month

   try:
       # Reiniciar pagos de gastos recurrentes
       GastoRecurrente.reiniciar_pagos_mensuales(mes_actual)
       
       # Registrar log o notificación si es necesario
       print(f"Gastos recurrentes reiniciados para el mes {mes_actual}")
   except Exception as e:
       # Manejar cualquier error durante el reinicio
       print(f"Error al reiniciar gastos recurrentes: {str(e)}")
       # Opcional: enviar notificación de error

@config_bp.route('/gastos-recurrentes/marcar/<int:id>', methods=['POST'])
def marcar_gasto_recurrente(id):
    """
    Marcar o desmarcar un gasto recurrente como pagado.
    
    :param id: ID del gasto recurrente
    :return: Respuesta JSON con el estado de la operación
    """
    from flask import jsonify, request
    
    # Obtener el gasto recurrente
    gasto = GastoRecurrente.query.get_or_404(id)
    
    try:
        # Obtener el estado del checkbox del request
        pagado = request.form.get('pagado', 'false').lower() == 'true'
        
        # Actualizar directamente el estado de pago
        gasto.pagado = pagado
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Gasto "{gasto.descripcion}" {"marcado" if pagado else "desmarcado"} exitosamente',
            'pagado': gasto.pagado
        }), 200
    
    except Exception as e:
        # Revertir cambios en caso de error
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'message': f'Error al marcar gasto: {str(e)}'
        }), 500

@config_bp.route('/gastos-recurrentes/reiniciar-mensual', methods=['POST'])
def reiniciar_gastos_recurrentes():
   """
   Reiniciar los gastos recurrentes al inicio de un nuevo mes.
   
   :return: Respuesta JSON con el estado de la operación
   """
   from flask import jsonify
   from datetime import datetime
   
   try:
       # Obtener el mes actual
       mes_actual = datetime.now().month
       
       # Reiniciar pagos de gastos recurrentes
       GastoRecurrente.reiniciar_pagos_mensuales(mes_actual)
       
       return jsonify({
           'success': True,
           'message': f'Gastos recurrentes reiniciados para el mes {mes_actual}'
       }), 200
   
   except Exception as e:
       # Revertir cambios en caso de error
       db.session.rollback()
       
       return jsonify({
           'success': False,
           'message': f'Error al reiniciar gastos recurrentes: {str(e)}'
       }), 500
