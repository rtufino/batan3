from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import Rubro, Movimiento, Proveedor
from app.forms import RubroForm, ProveedorForm
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
