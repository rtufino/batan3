from flask import Blueprint, render_template, redirect, url_for, flash, send_file, request
from app.models import Departamento, PersonaContacto, Movimiento, Cuenta, Rubro
from app.forms import DepartamentoForm, DepartamentoEditForm, PersonaContactoForm, PagoForm, CargoManualForm
from app.extensions import db
from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError

from app.utils import generar_pdf_aviso, notificar_aviso_cobro, notificar_recibo_pago, generar_pdf_recibo

import os
import io
from werkzeug.utils import secure_filename

condominos_bp = Blueprint('condominos', __name__, url_prefix='/condominos')

@condominos_bp.route('/')
def lista_departamentos():
    # Listado general de las 11 unidades
    departamentos = Departamento.query.order_by(Departamento.numero).all()
    return render_template('condominos/lista.html', departamentos=departamentos)

@condominos_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_departamento():
    form = DepartamentoForm()
    
    if form.validate_on_submit():
        # Verificar si el número ya existe
        numero_existente = Departamento.query.filter_by(numero=form.numero.data).first()
        
        if numero_existente:
            flash(f'El número de departamento "{form.numero.data}" ya está en uso. Por favor, elija otro número.', 'danger')
            return render_template('condominos/nuevo.html', form=form)
        
        try:
            nuevo_depto = Departamento(
                numero=form.numero.data,
                piso=int(form.piso.data),
                alicuota=form.alicuota.data,
                valor_expensa=form.valor_expensa.data,
                esta_arrendado=form.esta_arrendado.data,
                responsable_pago=form.responsable_pago.data
            )
            
            db.session.add(nuevo_depto)
            db.session.commit()
            flash(f'Departamento {nuevo_depto.numero} creado correctamente.', 'success')
            return redirect(url_for('condominos.lista_departamentos'))
        except IntegrityError:
            db.session.rollback()
            flash(f'Error: El número de departamento "{form.numero.data}" ya existe. Por favor, elija otro número.', 'danger')
            return render_template('condominos/nuevo.html', form=form)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear departamento: {str(e)}', 'danger')
            return render_template('condominos/nuevo.html', form=form)
        
    return render_template('condominos/nuevo.html', form=form)

@condominos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_departamento(id):
    depto = Departamento.query.get_or_404(id)
    form = DepartamentoEditForm(obj=depto)
    
    if form.validate_on_submit():
        try:
            depto.piso = int(form.piso.data)
            depto.alicuota = form.alicuota.data
            depto.valor_expensa = form.valor_expensa.data
            depto.esta_arrendado = form.esta_arrendado.data
            depto.responsable_pago = form.responsable_pago.data
            
            db.session.commit()
            flash(f'Departamento {depto.numero} actualizado correctamente.', 'success')
            return redirect(url_for('condominos.lista_departamentos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar departamento: {str(e)}', 'danger')
            return render_template('condominos/editar.html', form=form, depto=depto)
        
    return render_template('condominos/editar.html', form=form, depto=depto)

#3. GESTIONAR PERSONAS (Agregar/Editar)
@condominos_bp.route('/persona/<int:depto_id>', methods=['GET', 'POST'])
@condominos_bp.route('/persona/editar/<int:persona_id>', methods=['GET', 'POST'])
def gestionar_persona(depto_id=None, persona_id=None):
    if persona_id:
        persona = PersonaContacto.query.get_or_404(persona_id)
        depto = persona.departamento
        form = PersonaContactoForm(obj=persona)
    else:
        depto = Departamento.query.get_or_404(depto_id)
        persona = PersonaContacto(departamento_id=depto.id)
        form = PersonaContactoForm()

    if form.validate_on_submit():
        persona.nombre = form.nombre.data
        persona.email = form.email.data
        persona.telefono = form.telefono.data
        persona.rol = form.rol.data
        persona.recibe_notificaciones = form.recibe_notificaciones.data
        
        if not persona_id:
            db.session.add(persona)
            
        db.session.commit()
        flash('Contacto actualizado correctamente.', 'success')
        return redirect(url_for('condominos.editar_departamento', id=depto.id))
        
    return render_template('condominos/persona_form.html', form=form, depto=depto)

@condominos_bp.route('/generar-mensualidad', methods=['POST'])
def generar_mensualidad():
    hoy = datetime.now()
    # Formateamos el mes y año como "MM / YYYY"
    mes_anio_formato = hoy.strftime('%m / %Y') 

    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # 1. Obtener el rubro de "Expensas Ordinarias"
    from app.models import Rubro, Cuenta
    rubro_expensa = Rubro.query.filter_by(nombre="Expensas Ordinarias").first()
    # Usaremos la cuenta principal para proyectar el ingreso
    cuenta_principal = Cuenta.query.first() 
    
    if not rubro_expensa:
        flash("Error: No existe el rubro 'Expensas Ordinarias'.", "danger")
        return redirect(url_for('condominos.lista_departamentos'))

    departamentos = Departamento.query.all()
    generados = 0
    omitidos = 0

    for depto in departamentos:
        # 2. Verificar si ya se generó el cargo este mes para este depto
        existe = Movimiento.query.filter(
            Movimiento.departamento_id == depto.id,
            Movimiento.rubro_id == rubro_expensa.id,
            extract('month', Movimiento.fecha_emision) == mes_actual,
            extract('year', Movimiento.fecha_emision) == anio_actual
        ).first()

        if not existe:
            # 1. Calculamos la deuda ANTERIOR (saldo_pendiente actual)
            deuda_previa = depto.saldo_pendiente

            # 3. Crear el cargo pendiente (Deuda para el vecino)
            nuevo_cargo = Movimiento(
                tipo='INGRESO',
                estado='PENDIENTE', # Es deuda hasta que se registre el pago
                monto=depto.valor_expensa,
                fecha_emision=hoy,  # Fecha de generación de la expensa
                fecha_pago=None,    # Aún no pagado
                descripcion=f"{depto.numero} - {mes_anio_formato}",
                rubro_id=rubro_expensa.id,
                departamento_id=depto.id,
                cuenta_id=cuenta_principal.id
            )
            db.session.add(nuevo_cargo)
            db.session.flush() # Para obtener el ID del movimiento

            # 2. Generar PDF
            pdf_bytes = generar_pdf_aviso(depto, nuevo_cargo, deuda_previa)
            
            # Carpeta estática: app/static/uploads/avisos/2025/12/
            folder_rel = f"{hoy.year}/{hoy.month}"
            folder_abs = os.path.join('app', 'static', 'uploads', 'avisos', folder_rel)
            os.makedirs(folder_abs, exist_ok=True)
            
            mes_anio_file = hoy.strftime('%m_%Y') # Para el nombre de archivo

            filename = f"Aviso_{depto.numero}_{mes_anio_file}.pdf"
            with open(os.path.join(folder_abs, filename), 'wb') as f:
                f.write(pdf_bytes)
            
            # 3. Guardar la URL relativa en el modelo
            nuevo_cargo.comprobante_url = f"{folder_rel}/{filename}"
            db.session.commit()

            # 4. ENVIAR NOTIFICACIÓN POR EMAIL
            try:
                notificar_aviso_cobro(depto, nuevo_cargo, pdf_bytes)
            except Exception as e:
                # Si falla el email, no interrumpimos el proceso
                print(f"Error al enviar email a {depto.numero}: {str(e)}")

            generados += 1
        else:
            omitidos += 1

    db.session.commit()
    
    if generados > 0:
        flash(f"Se generaron {generados} avisos de cobro con éxito. {omitidos} ya existían.", "success")
    else:
        flash(f"Las expensas de este mes ya fueron generadas anteriormente.", "info")
        
    return redirect(url_for('condominos.lista_departamentos'))

@condominos_bp.route('/estado-cuenta/<int:id>')
def estado_cuenta(id):
    depto = Departamento.query.get_or_404(id)
    
    # Obtener parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validar per_page
    if per_page not in [10, 25, 50]:
        per_page = 10
    
    # Obtenemos los movimientos con paginación
    pagination = Movimiento.query.filter_by(departamento_id=id)\
        .order_by(Movimiento.fecha_emision.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    movimientos = pagination.items
    
    return render_template('condominos/estado_cuenta.html',
                           depto=depto,
                           movimientos=movimientos,
                           pagination=pagination,
                           per_page=per_page)



@condominos_bp.route('/registrar-pago/<int:movimiento_id>', methods=['GET', 'POST'])
def registrar_pago(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    form = PagoForm()
    
    # Llenamos el select de cuentas bancarias
    form.cuenta_id.choices = [(c.id, c.nombre) for c in Cuenta.query.all()]

    if form.validate_on_submit():
        # 1. Identificar la cuenta bancaria seleccionada
        cuenta = Cuenta.query.get(form.cuenta_id.data)
        
        # 2. ACTUALIZACIÓN DEL SALDO DE LA CUENTA
        # Como el movimiento pasa de PENDIENTE a PAGADO, el dinero "entra" hoy.
        cuenta.saldo += float(movimiento.monto)
        
        # 3. Actualizar los datos del movimiento
        movimiento.estado = 'PAGADO'
        movimiento.fecha_pago = datetime.combine(form.fecha_pago.data, datetime.min.time())
        movimiento.cuenta_id = form.cuenta_id.data
        
        # Manejo de archivo (comprobante) si existe
        if form.comprobante.data:
            file = form.comprobante.data
            filename = secure_filename(f"pago_{depto.numero}_{movimiento.id}.png")
            file.save(os.path.join('app/static/uploads/pagos', filename))
            movimiento.comprobante = filename
            
        try:
            db.session.commit()
            
            # 4. GENERAR Y ENVIAR RECIBO POR EMAIL
            try:
                # Generar el PDF del recibo
                pdf_buffer = generar_pdf_recibo(movimiento)
                pdf_bytes = pdf_buffer.getvalue()
                
                # Enviar notificación con el recibo adjunto
                notificar_recibo_pago(depto, movimiento, pdf_bytes)
            except Exception as e:
                # Si falla el email, no interrumpimos el proceso
                print(f"Error al enviar recibo por email: {str(e)}")
            
            flash(f'¡Pago registrado! El saldo de la cuenta {cuenta.nombre} ha sido actualizado. Se ha enviado el recibo por email.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar saldo: {e}', 'danger')
            
        return redirect(url_for('condominos.estado_cuenta', id=depto.id))

    return render_template('condominos/registrar_pago.html', form=form, movimiento=movimiento, depto=depto)

@condominos_bp.route('/reimprimir-aviso/<int:movimiento_id>')
def reimprimir_aviso(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    
    # Deuda anterior = Saldo total actual - Monto de este movimiento específico (convertir a float)
    deuda_anterior = depto.saldo_pendiente - float(movimiento.monto)
    
    # Obtenemos los bytes desde la función en utils.py
    pdf_content = generar_pdf_aviso(depto, movimiento, deuda_anterior)
    
    # Retornamos el stream de bytes directamente al navegador
    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=False, # False para que se abra en el navegador
        download_name=f"Aviso_{depto.numero}.pdf"
    )

@condominos_bp.route('/enviar-aviso/<int:movimiento_id>', methods=['POST'])
def enviar_aviso_email(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    
    # Verificar que el movimiento esté pendiente
    if movimiento.estado != 'PENDIENTE':
        flash('Solo se pueden enviar avisos de movimientos pendientes.', 'warning')
        return redirect(url_for('condominos.estado_cuenta', id=depto.id))
    
    try:
        # Calcular deuda anterior
        deuda_anterior = depto.saldo_pendiente - float(movimiento.monto)
        
        # Generar PDF
        pdf_bytes = generar_pdf_aviso(depto, movimiento, deuda_anterior)
        
        # Enviar email
        notificar_aviso_cobro(depto, movimiento, pdf_bytes)
        
        flash(f'Aviso de cobro enviado por email exitosamente al departamento {depto.numero}', 'success')
    except Exception as e:
        flash(f'Error al enviar email: {str(e)}', 'danger')
    
    return redirect(url_for('condominos.estado_cuenta', id=depto.id))

@condominos_bp.route('/enviar-recibo/<int:movimiento_id>', methods=['POST'])
def enviar_recibo_email(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    
    # Verificar que el movimiento esté pagado
    if movimiento.estado != 'PAGADO':
        flash('Solo se pueden enviar recibos de movimientos pagados.', 'warning')
        return redirect(url_for('condominos.estado_cuenta', id=depto.id))
    
    try:
        # Generar PDF del recibo
        pdf_buffer = generar_pdf_recibo(movimiento)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Enviar email con recibo
        notificar_recibo_pago(depto, movimiento, pdf_bytes)
        
        flash(f'Recibo de pago reenviado por email exitosamente al departamento {depto.numero}', 'success')
    except Exception as e:
        flash(f'Error al enviar email: {str(e)}', 'danger')
    
    return redirect(url_for('condominos.estado_cuenta', id=depto.id))

@condominos_bp.route('/eliminar-cargo/<int:movimiento_id>', methods=['POST'])
def eliminar_cargo(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    
    # Verificar que el movimiento esté pendiente
    if movimiento.estado != 'PENDIENTE':
        flash('Solo se pueden eliminar movimientos pendientes.', 'warning')
        return redirect(url_for('condominos.estado_cuenta', id=depto.id))
    
    try:
        # Guardar información para el mensaje
        descripcion = movimiento.descripcion
        monto = float(movimiento.monto)
        
        # Eliminar el movimiento
        db.session.delete(movimiento)
        db.session.commit()
        
        flash(f'Cargo eliminado exitosamente: {descripcion} - ${monto:.2f}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cargo: {str(e)}', 'danger')
    
    return redirect(url_for('condominos.estado_cuenta', id=depto.id))

@condominos_bp.route('/agregar-cargo/<int:depto_id>', methods=['GET', 'POST'])
def agregar_cargo_manual(depto_id):
    depto = Departamento.query.get_or_404(depto_id)
    form = CargoManualForm()
    
    # Cargar opciones dinámicas
    form.rubro_id.choices = [(r.id, r.nombre) for r in Rubro.query.filter_by(tipo='INGRESO').all()]
    form.cuenta_id.choices = [(c.id, f"{c.nombre} (${c.saldo:.2f})") for c in Cuenta.query.all()]
    
    # Generar opciones de años (últimos 2 años y próximos 2)
    anio_actual = datetime.now().year
    form.anio.choices = [(y, str(y)) for y in range(anio_actual - 2, anio_actual + 3)]
    
    if form.validate_on_submit():
        # 1. Verificar duplicados
        existe = Movimiento.query.filter(
            Movimiento.departamento_id == depto.id,
            Movimiento.rubro_id == form.rubro_id.data,
            extract('month', Movimiento.fecha_emision) == form.mes.data,
            extract('year', Movimiento.fecha_emision) == form.anio.data
        ).first()
        
        if existe:
            rubro = Rubro.query.get(form.rubro_id.data)
            flash(f'Ya existe un cargo de "{rubro.nombre}" para {form.mes.data}/{form.anio.data}. No se pueden registrar cargos duplicados del mismo rubro en el mismo mes.', 'warning')
            return render_template('condominos/agregar_cargo.html', form=form, depto=depto)
        
        # 2. Validar que si está PAGADO, tenga cuenta y fecha
        if form.estado.data == 'PAGADO':
            if not form.cuenta_id.data or not form.fecha_pago.data:
                flash('Para estado PAGADO debe seleccionar cuenta y fecha de pago', 'danger')
                return render_template('condominos/agregar_cargo.html', form=form, depto=depto)
        
        # 3. Crear fecha de emisión (primer día del mes seleccionado)
        fecha_emision = datetime(form.anio.data, form.mes.data, 1)
        
        # 4. Obtener el monto del formulario
        monto = form.monto.data
        
        # 5. Crear descripción
        if form.descripcion.data:
            descripcion = form.descripcion.data
        else:
            descripcion = f"{depto.numero} - {form.mes.data:02d} / {form.anio.data}"
        
        # 6. Crear movimiento
        nuevo_cargo = Movimiento(
            tipo='INGRESO',
            estado=form.estado.data,
            monto=monto,
            fecha_emision=fecha_emision,
            fecha_pago=datetime.combine(form.fecha_pago.data, datetime.min.time()) if form.estado.data == 'PAGADO' and form.fecha_pago.data else None,
            descripcion=descripcion,
            rubro_id=form.rubro_id.data,
            departamento_id=depto.id,
            cuenta_id=form.cuenta_id.data if form.estado.data == 'PAGADO' else Cuenta.query.first().id
        )
        
        # 7. Si está PAGADO, actualizar saldo de cuenta
        if form.estado.data == 'PAGADO':
            cuenta = Cuenta.query.get(form.cuenta_id.data)
            cuenta.saldo += float(monto)
        
        # 8. Si está PENDIENTE, generar PDF y enviar email
        if form.estado.data == 'PENDIENTE':
            db.session.add(nuevo_cargo)
            db.session.flush()
            
            # Calcular deuda anterior (convertir a float para evitar error de tipos)
            deuda_anterior = depto.saldo_pendiente - float(nuevo_cargo.monto)
            
            # Generar PDF
            pdf_bytes = generar_pdf_aviso(depto, nuevo_cargo, deuda_anterior)
            
            # Guardar PDF
            folder_rel = f"{form.anio.data}/{form.mes.data}"
            folder_abs = os.path.join('app', 'static', 'uploads', 'avisos', folder_rel)
            os.makedirs(folder_abs, exist_ok=True)
            
            filename = f"Aviso_{depto.numero}_{form.mes.data:02d}_{form.anio.data}.pdf"
            with open(os.path.join(folder_abs, filename), 'wb') as f:
                f.write(pdf_bytes)
            
            nuevo_cargo.comprobante_url = f"{folder_rel}/{filename}"
            
            # Enviar email
            try:
                notificar_aviso_cobro(depto, nuevo_cargo, pdf_bytes)
            except Exception as e:
                print(f"Error al enviar email: {str(e)}")
        
        try:
            db.session.add(nuevo_cargo)
            db.session.commit()
            flash(f'Cargo registrado exitosamente ({form.estado.data})', 'success')
            return redirect(url_for('condominos.estado_cuenta', id=depto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')
    
    # Pre-llenar valores por defecto
    if not form.mes.data:
        form.mes.data = datetime.now().month
    if not form.anio.data:
        form.anio.data = datetime.now().year
    if not form.monto.data:
        form.monto.data = depto.valor_expensa
    if not form.fecha_pago.data:
        form.fecha_pago.data = datetime.now().date()
    
    return render_template('condominos/agregar_cargo.html', form=form, depto=depto)