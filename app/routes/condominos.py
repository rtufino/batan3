from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Departamento, PersonaContacto
from app.forms import DepartamentoForm, PersonaContactoForm
from app.extensions import db

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