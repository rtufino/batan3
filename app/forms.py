from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, NumberRange, Optional
from app.models import Proveedor

class IngresoForm(FlaskForm):
    # Selección del Departamento que paga
    departamento_id = SelectField('Departamento', validators=[DataRequired()], coerce=int)
    
    # Tipo de Ingreso (Expensa Ordinaria, Extra, Alquiler Terraza, etc.)
    rubro_id = SelectField('Concepto (Rubro)', validators=[DataRequired()], coerce=int)
    
    # A qué cuenta entra el dinero (Banco o Efectivo)
    cuenta_id = SelectField('Cuenta de Destino', validators=[DataRequired()], coerce=int)
    
    # Datos del pago
    monto = DecimalField('Monto ($)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    fecha = DateField('Fecha del Pago', validators=[DataRequired()], format='%Y-%m-%d')
    descripcion = StringField('Detalle / Notas', default='Pago de expensas')
    
    submit = SubmitField('Registrar Ingreso')

class GastoForm(FlaskForm):
    # A quién le pagamos (Empresa eléctrica, Conserje, Ferretería)
    proveedor_id = SelectField('Proveedor / Beneficiario', validators=[DataRequired()], coerce=int)
    
    # Qué estamos pagando (Luz, Agua, Mantenimiento)
    rubro_id = SelectField('Concepto (Rubro)', validators=[DataRequired()], coerce=int)
    
    # De dónde sale el dinero (o de dónde saldrá si es deuda)
    cuenta_id = SelectField('Cuenta de Origen', validators=[DataRequired()], coerce=int)
    
    # Estado del Gasto: ¿Lo pagué ya o es una deuda?
    estado = SelectField('Estado del Pago', choices=[('PAGADO', 'Pagado Inmediatamente'), ('PENDIENTE', 'Por Pagar (Deuda)')], validators=[DataRequired()])
    
    monto = DecimalField('Monto ($)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    fecha = DateField('Fecha de Emisión', validators=[DataRequired()], format='%Y-%m-%d')
    descripcion = StringField('Detalle / Notas', default='Pago de servicios')
    
    submit = SubmitField('Registrar Gasto')

class MantenimientoForm(FlaskForm):
    # Selección del Equipo (Ascensor, Bomba, etc.)
    equipo_id = SelectField('Equipo / Activo', validators=[DataRequired()], coerce=int)
    
    fecha = DateField('Fecha del Trabajo', validators=[DataRequired()], format='%Y-%m-%d')
    descripcion = StringField('Descripción del Trabajo', validators=[DataRequired()])
    
    # Costo referencial (no afecta caja, es solo informativo para el historial técnico)
    costo_referencial = DecimalField('Costo Referencial ($)', places=2, default=0.0)
    
    # Archivos de evidencia
    foto_antes = FileField('Foto Antes (Opcional)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes!')
    ])
    foto_despues = FileField('Foto Después (Opcional)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes!')
    ])
    
    submit = SubmitField('Registrar Mantenimiento')

class EquipoForm(FlaskForm):
    nombre = StringField('Nombre del Equipo', validators=[DataRequired()])
    ubicacion = StringField('Ubicación Física', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción / Detalles Técnicos', validators=[DataRequired()])
    fecha_instalacion = DateField('Fecha Instalación (Aprox)', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Guardar Equipo')