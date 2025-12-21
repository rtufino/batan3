from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from app.models import Departamento, PersonaContacto, Movimiento, Cuenta
from app.forms import DepartamentoForm, PersonaContactoForm, PagoForm
from app.extensions import db
from datetime import datetime
from sqlalchemy import extract

from app.utils import generar_pdf_aviso # Importamos la nueva función

import os
import io
from werkzeug.utils import secure_filename

condominos_bp = Blueprint('condominos', __name__, url_prefix='/condominos')

@condominos_bp.route('/')
def lista_departamentos():
    # Listado general de las 11 unidades
    departamentos = Departamento.query.order_by(Departamento.numero).all()
    return render_template('condominos/lista.html', departamentos=departamentos)

@condominos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_departamento(id):
    depto = Departamento.query.get_or_404(id)
    form = DepartamentoForm(obj=depto)
    
    if form.validate_on_submit():
        depto.numero = form.numero.data
        depto.piso = form.piso.data
        depto.alicuota = form.alicuota.data
        depto.valor_expensa = form.valor_expensa.data
        depto.esta_arrendado = form.esta_arrendado.data
        depto.responsable_pago = form.responsable_pago.data
        
        db.session.commit()
        flash(f'Departamento {depto.numero} actualizado correctamente.', 'success')
        return redirect(url_for('condominos.lista_departamentos'))
        
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
            extract('month', Movimiento.fecha) == mes_actual,
            extract('year', Movimiento.fecha) == anio_actual
        ).first()

        if not existe:
            # 1. Calculamos la deuda ANTERIOR (saldo_pendiente actual)
            deuda_previa = depto.saldo_pendiente

            # 3. Crear el cargo pendiente (Deuda para el vecino)
            nuevo_cargo = Movimiento(
                tipo='INGRESO',
                estado='PENDIENTE', # Es deuda hasta que se registre el pago
                monto=depto.valor_expensa,
                fecha=hoy,
                descripcion=f"{depto.numero} - {mes_anio_formato}",
                rubro_id=rubro_expensa.id,
                departamento_id=depto.id,
                cuenta_id=cuenta_principal.id
            )
            db.session.add(nuevo_cargo)
            db.session.flush() # Para obtener el ID del movimiento

            # 3. GENERACIÓN FÍSICA DEL PDF
            pdf_content = generar_pdf_aviso(depto, nuevo_cargo, deuda_previa)
            
            # Carpeta: static/uploads/avisos/2024/diciembre/
            ruta_carpeta = os.path.join('app/static/uploads/avisos', f"{hoy.year}", f"{hoy.month}")
            os.makedirs(ruta_carpeta, exist_ok=True)
            
            nombre_archivo = f"Aviso_{depto.numero}_{hoy.strftime('%m_%Y')}.pdf"
            with open(os.path.join(ruta_carpeta, nombre_archivo), 'wb') as f:
                f.write(pdf_content)
            
            # Guardamos la ruta en el campo comprobante para descargarlo después
            nuevo_cargo.comprobante_url = f"{hoy.year}/{hoy.month}/{nombre_archivo}"

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
    # Obtenemos todos los movimientos (Pagados y Pendientes) ordenados por fecha
    movimientos = Movimiento.query.filter_by(departamento_id=id).order_by(Movimiento.fecha.desc()).all()
    
    return render_template('condominos/estado_cuenta.html', 
                           depto=depto, 
                           movimientos=movimientos)



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
        cuenta.saldo += movimiento.monto 
        
        # 3. Actualizar los datos del movimiento
        movimiento.estado = 'PAGADO'
        movimiento.fecha = form.fecha_pago.data
        movimiento.cuenta_id = form.cuenta_id.data
        
        # Manejo de archivo (comprobante) si existe
        if form.comprobante.data:
            file = form.comprobante.data
            filename = secure_filename(f"pago_{depto.numero}_{movimiento.id}.png")
            file.save(os.path.join('app/static/uploads/pagos', filename))
            movimiento.comprobante = filename
            
        try:
            db.session.commit()
            flash(f'¡Pago registrado! El saldo de la cuenta {cuenta.nombre} ha sido actualizado.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar saldo: {e}', 'danger')
            
        return redirect(url_for('condominos.estado_cuenta', id=depto.id))

    return render_template('condominos/registrar_pago.html', form=form, movimiento=movimiento, depto=depto)

@condominos_bp.route('/reimprimir-aviso/<int:movimiento_id>')
def reimprimir_aviso(movimiento_id):
    movimiento = Movimiento.query.get_or_404(movimiento_id)
    depto = movimiento.departamento
    
    # Deuda anterior = Saldo total actual - Monto de este movimiento específico
    deuda_anterior = depto.saldo_pendiente - movimiento.monto
    
    # Obtenemos los bytes desde la función en utils.py
    pdf_content = generar_pdf_aviso(depto, movimiento, deuda_anterior)
    
    # Retornamos el stream de bytes directamente al navegador
    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=False, # False para que se abra en el navegador
        download_name=f"Aviso_{depto.numero}.pdf"
    )