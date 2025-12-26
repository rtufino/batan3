from app.extensions import db
from datetime import datetime

# --- 1. CONFIGURACIÓN Y PARAMETRIZACIÓN ---

class ConfiguracionFiscal(db.Model):
    """
    Almacena el Salario Básico Unificado (SBU) por año.
    Vital para calcular décimos y jubilación patronal en Ecuador.
    """
    __tablename__ = 'configuracion_fiscal'
    
    id = db.Column(db.Integer, primary_key=True)
    anio = db.Column(db.Integer, unique=True, nullable=False)  # Ej: 2025
    valor_sbu = db.Column(db.Float, nullable=False)            # Ej: 460.00
    
    def __repr__(self):
        return f'<SBU {self.anio}: ${self.valor_sbu}>'

class Parametro(db.Model):
    """
    Tabla de parámetros del sistema para controlar aspectos configurables.
    Permite almacenar valores de diferentes tipos (texto, número, booleano, fecha).
    """
    __tablename__ = 'parametro'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)  # Identificador único del parámetro
    valor = db.Column(db.Text, nullable=True)  # Valor almacenado como texto
    tipo = db.Column(db.String(20), nullable=False, default='TEXT')  # TEXT, NUMBER, BOOLEAN, DATE, JSON
    descripcion = db.Column(db.String(255), nullable=True)  # Descripción del parámetro
    categoria = db.Column(db.String(50), nullable=True)  # Para agrupar parámetros: GENERAL, NOTIFICACIONES, FINANZAS, etc.
    editable = db.Column(db.Boolean, default=True)  # Si el usuario puede editarlo desde la interfaz
    fecha_modificacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Parametro {self.clave}: {self.valor}>'
    
    def get_valor_typed(self):
        """Retorna el valor convertido al tipo correcto"""
        if self.valor is None:
            return None
        
        if self.tipo == 'NUMBER':
            try:
                return float(self.valor)
            except (ValueError, TypeError):
                return 0.0
        elif self.tipo == 'BOOLEAN':
            return self.valor.lower() in ('true', '1', 'yes', 'si', 'sí')
        elif self.tipo == 'DATE':
            try:
                return datetime.strptime(self.valor, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None
        elif self.tipo == 'JSON':
            try:
                import json
                return json.loads(self.valor)
            except (ValueError, TypeError):
                return {}
        else:  # TEXT
            return self.valor
    
    @staticmethod
    def get_parametro(clave, default=None):
        """Método helper para obtener un parámetro por su clave"""
        param = Parametro.query.filter_by(clave=clave).first()
        if param:
            return param.get_valor_typed()
        return default
    
    @staticmethod
    def set_parametro(clave, valor, tipo='TEXT', descripcion=None, categoria='GENERAL'):
        """Método helper para crear o actualizar un parámetro"""
        param = Parametro.query.filter_by(clave=clave).first()
        
        # Convertir el valor a string para almacenamiento
        if tipo == 'BOOLEAN':
            valor_str = 'true' if valor else 'false'
        elif tipo == 'DATE':
            valor_str = valor.strftime('%Y-%m-%d') if hasattr(valor, 'strftime') else str(valor)
        elif tipo == 'JSON':
            import json
            valor_str = json.dumps(valor)
        else:
            valor_str = str(valor)
        
        if param:
            param.valor = valor_str
            param.tipo = tipo
            if descripcion:
                param.descripcion = descripcion
            param.fecha_modificacion = datetime.now()
        else:
            param = Parametro(
                clave=clave,
                valor=valor_str,
                tipo=tipo,
                descripcion=descripcion,
                categoria=categoria
            )
            db.session.add(param)
        
        return param

class Rubro(db.Model):
    """
    Categorías para ingresos y egresos.
    Ej: 'Expensas Ordinarias', 'Agua Potable', 'Mantenimiento Ascensor', 'Nómina'.
    """
    __tablename__ = 'rubro'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'INGRESO' o 'EGRESO'
    
    # Relación para saber cuántos movimientos tiene este rubro
    movimientos = db.relationship('Movimiento', backref='rubro', lazy=True)

    def __repr__(self):
        return f'<{self.nombre} ({self.tipo})>'
    
class Cuenta(db.Model):
    """
    NUEVA ENTIDAD: Representa dónde está el dinero.
    Ej: Caja Chica (Efectivo), Cuenta Bancaria.
    """
    __tablename__ = 'cuenta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) # Ej: "Banco Pichincha", "Caja Fuerte"
    tipo = db.Column(db.String(20), nullable=False)    # 'BANCO' o 'EFECTIVO'
    numero = db.Column(db.String(50), nullable=True)   # Para número de cuenta bancaria
    saldo_inicial = db.Column(db.Float, default=0.0)   # Saldo al arrancar el sistema
    saldo = db.Column(db.Float, default=0.0)           # Saldo de la cuenta 
    
    # Relación para saber qué movimientos afectaron esta cuenta
    movimientos = db.relationship('Movimiento', backref='cuenta', lazy=True)

    # En app/models.py dentro de la clase Cuenta

    # @property
    # def saldo_actual(self):
    #     """Suma ingresos pagados y resta egresos pagados"""
    #     from app.models import Movimiento
        
    #     ingresos = db.session.query(db.func.sum(Movimiento.monto)).filter(
    #         Movimiento.cuenta_id == self.id,
    #         Movimiento.tipo == 'INGRESO',
    #         Movimiento.estado == 'PAGADO'
    #     ).scalar() or 0.0
        
    #     egresos = db.session.query(db.func.sum(Movimiento.monto)).filter(
    #         Movimiento.cuenta_id == self.id,
    #         Movimiento.tipo == 'EGRESO',
    #         Movimiento.estado == 'PAGADO'
    #     ).scalar() or 0.0
        
    #    return ingresos - egresos

    def __repr__(self):
        return f'<Cuenta {self.nombre}>'

# --- 2. INMUEBLE Y PERSONAS ---

class Departamento(db.Model):
    __tablename__ = 'departamento'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False) # Ej: "201"
    piso = db.Column(db.Integer, nullable=False)
    alicuota = db.Column(db.Float, nullable=False, default=0.0) # Porcentaje de participación
    esta_arrendado = db.Column(db.Boolean, default=False)
    responsable_pago = db.Column(db.String(20), default='PROPIETARIO')
    valor_expensa = db.Column(db.Float, nullable=False, default=0.0) # Valor monetario fijo


    # Relaciones
    personas = db.relationship('PersonaContacto', backref='departamento', lazy=True)
    pagos = db.relationship('Movimiento', backref='departamento', lazy=True)

    @property
    def saldo_pendiente(self):
        """Calcula el total de movimientos tipo INGRESO que están PENDIENTES"""
        from app.models import Movimiento
        # Sumamos todos los ingresos pendientes (deuda actual)
        total_deuda = db.session.query(db.func.sum(Movimiento.monto)).filter(
            Movimiento.departamento_id == self.id,
            Movimiento.tipo == 'INGRESO',
            Movimiento.estado == 'PENDIENTE'
        ).scalar() or 0.0
        
        return total_deuda

    def __repr__(self):
        return f'<Depto {self.numero}>'

class PersonaContacto(db.Model): 
    __tablename__ = 'persona_contacto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    
    # ROLES: 'PROPIETARIO' o 'ARRENDATARIO'
    rol = db.Column(db.String(20), nullable=False, default='PROPIETARIO')
    recibe_notificaciones = db.Column(db.Boolean, default=True)
    
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)

class Proveedor(db.Model):
    """
    Sirve para proveedores externos (Ej. Empresa Eléctrica) 
    y para empleados (Ej. Conserje, Jubilado Patronal).
    """
    __tablename__ = 'proveedor'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc_cedula = db.Column(db.String(20), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    
    # Categoría: 'SERVICIOS_BASICOS', 'MANTENIMIENTO', 'NOMINA', 'OTROS'
    categoria = db.Column(db.String(50), nullable=False, default='OTROS')
    
    pagos = db.relationship('Movimiento', backref='proveedor', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'

# --- 3. MANTENIMIENTO Y ACTIVOS ---

class Equipo(db.Model):
    """
    Inventario del edificio: Ascensor, Bombas, Extintores.
    """
    __tablename__ = 'equipo'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) # Ej: "Bomba Agua 1"
    ubicacion = db.Column(db.String(100), nullable=True)
    fecha_instalacion = db.Column(db.Date, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    mantenimientos = db.relationship('Mantenimiento', backref='equipo', lazy=True)

    def __repr__(self):
        return f'<Equipo {self.nombre}>'

class Mantenimiento(db.Model):
    """
    Bitácora técnica de lo que se hizo.
    """
    __tablename__ = 'mantenimiento'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.Text, nullable=False)
    costo_referencial = db.Column(db.Float, default=0.0)
    
    # Rutas a las imágenes (Guardaremos solo el path)
    foto_antes = db.Column(db.String(200), nullable=True)
    foto_despues = db.Column(db.String(200), nullable=True)
    
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    
    # Opcional: Vincular con un movimiento financiero si ya se pagó
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimiento.id'), nullable=True)

# --- 4. FINANZAS (CORE) ---

class Movimiento(db.Model):
    """
    Tabla central de contabilidad. Registra TODO el dinero que entra y sale.
    """
    __tablename__ = 'movimiento'
    id = db.Column(db.Integer, primary_key=True)
    
    # FECHAS SEPARADAS:
    # fecha_emision: Cuando se genera el documento/obligación (siempre se registra)
    fecha_emision = db.Column(db.DateTime, default=datetime.now, nullable=False)
    # fecha_pago: Cuando realmente se efectúa el pago (NULL si está PENDIENTE)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    
    tipo = db.Column(db.String(10), nullable=False) # 'INGRESO' o 'EGRESO'
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    comprobante_url = db.Column(db.String(200), nullable=True)
    
    # NUEVO: ¿Es una transferencia interna entre cuentas?
    es_transferencia = db.Column(db.Boolean, default=False)

    # NUEVO CAMPO: Estado del pago
    # 'PAGADO': El dinero ya se movió de la cuenta (afecta saldo real).
    # 'PENDIENTE': Es una deuda o cuenta por cobrar (NO afecta saldo real, pero sí el balance).
    estado = db.Column(db.String(20), nullable=False, default='PAGADO')

    # Relaciones
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubro.id'), nullable=False)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=True)
    
    # NUEVO: Relación con la Cuenta (Caja o Banco)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), nullable=False)

    def __repr__(self):
        fecha_mostrar = self.fecha_pago if self.fecha_pago else self.fecha_emision
        return f'<{self.tipo} ${self.monto} - Emitido: {self.fecha_emision.date()} - Pagado: {fecha_mostrar.date() if self.fecha_pago else "PENDIENTE"}>'