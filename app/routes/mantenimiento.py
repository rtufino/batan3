import os
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Equipo, Mantenimiento
from app.forms import MantenimientoForm, EquipoForm
from datetime import datetime

mantenimiento_bp = Blueprint('mantenimiento', __name__, url_prefix='/operaciones')

def guardar_imagen(archivo):
    """
    Recibe un archivo, le cambia el nombre para que sea seguro y único,
    lo guarda en la carpeta configurada y retorna el nombre del archivo.
    """
    if not archivo:
        return None
        
    nombre_original = secure_filename(archivo.filename)
    # Generamos un timestamp para evitar nombres duplicados
    nombre_unico = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_original}"
    
    ruta_completa = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_unico)
    archivo.save(ruta_completa)
    
    return nombre_unico

@mantenimiento_bp.route('/')
def inventario():
    # Listado de todos los equipos y sus últimos mantenimientos
    equipos = Equipo.query.filter_by(activo=True).all()
    return render_template('mantenimiento/inventario.html', equipos=equipos)

@mantenimiento_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_registro():
    form = MantenimientoForm()
    # Cargar equipos en el select
    form.equipo_id.choices = [(e.id, f"{e.nombre} ({e.ubicacion})") for e in Equipo.query.all()]
    
    if form.validate_on_submit():
        # 1. Guardar fotos físicamente
        foto_antes_nombre = guardar_imagen(form.foto_antes.data)
        foto_despues_nombre = guardar_imagen(form.foto_despues.data)
        
        # 2. Guardar registro en BD
        nuevo_mant = Mantenimiento(
            equipo_id=form.equipo_id.data,
            fecha=datetime.combine(form.fecha.data, datetime.min.time()),
            descripcion=form.descripcion.data,
            costo_referencial=form.costo_referencial.data,
            foto_antes=foto_antes_nombre,
            foto_despues=foto_despues_nombre
        )
        
        try:
            db.session.add(nuevo_mant)
            db.session.commit()
            flash('Mantenimiento registrado con éxito.', 'success')
            return redirect(url_for('mantenimiento.inventario'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')

    if not form.fecha.data:
        form.fecha.data = datetime.now().date()

    return render_template('mantenimiento/nuevo_registro.html', form=form)

@mantenimiento_bp.route('/equipo/<int:id>')
def detalle_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    # Historial de este equipo específico
    historial = Mantenimiento.query.filter_by(equipo_id=id).order_by(Mantenimiento.fecha.desc()).all()
    return render_template('mantenimiento/detalle_equipo.html', equipo=equipo, historial=historial)

# --- CRUD DE EQUIPOS ---

@mantenimiento_bp.route('/equipos/nuevo', methods=['GET', 'POST'])
def crear_equipo():
    form = EquipoForm()
    if form.validate_on_submit():
        nuevo_equipo = Equipo(
            nombre=form.nombre.data,
            ubicacion=form.ubicacion.data,
            descripcion=form.descripcion.data,
            fecha_instalacion=form.fecha_instalacion.data
        )
        try:
            db.session.add(nuevo_equipo)
            db.session.commit()
            flash('Equipo creado exitosamente.', 'success')
            return redirect(url_for('mantenimiento.inventario'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear: {e}', 'danger')
            
    return render_template('mantenimiento/gestion_equipo.html', form=form, titulo="Nuevo Equipo")

@mantenimiento_bp.route('/equipos/editar/<int:id>', methods=['GET', 'POST'])
def editar_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    form = EquipoForm(obj=equipo) # Pre-llenamos el formulario con datos existentes
    
    if form.validate_on_submit():
        equipo.nombre = form.nombre.data
        equipo.ubicacion = form.ubicacion.data
        equipo.descripcion = form.descripcion.data
        equipo.fecha_instalacion = form.fecha_instalacion.data
        
        try:
            db.session.commit()
            flash('Datos del equipo actualizados.', 'success')
            return redirect(url_for('mantenimiento.inventario'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {e}', 'danger')
            
    return render_template('mantenimiento/gestion_equipo.html', form=form, titulo="Editar Equipo")

@mantenimiento_bp.route('/equipos/eliminar/<int:id>', methods=['POST'])
def desactivar_equipo(id):
    equipo = Equipo.query.get_or_404(id)
    
    # En lugar de db.session.delete(equipo), hacemos esto:
    equipo.activo = False
    
    try:
        db.session.commit()
        flash(f'El equipo "{equipo.nombre}" ha sido archivado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar: {e}', 'danger')
        
    return redirect(url_for('mantenimiento.inventario'))