from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
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