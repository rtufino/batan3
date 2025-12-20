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