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
    
    # Relación para saber qué movimientos afectaron esta cuenta
    movimientos = db.relationship('Movimiento', backref='cuenta', lazy=True)

    def __repr__(self):
        return f'<Cuenta {self.nombre}>'

# --- 2. INMUEBLE Y PERSONAS ---

class Departamento(db.Model):
    __tablename__ = 'departamento'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False) # Ej: "201"
    piso = db.Column(db.Integer, nullable=False)
    alicuota = db.Column(db.Float, nullable=False, default=0.0) # Porcentaje de participación
    
    # Relaciones
    propietarios = db.relationship('Propietario', backref='departamento', lazy=True)
    pagos = db.relationship('Movimiento', backref='departamento', lazy=True)

    def __repr__(self):
        return f'<Depto {self.numero}>'

class Propietario(db.Model):
    __tablename__ = 'propietario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True) # Clave para enviar recibos
    telefono = db.Column(db.String(20), nullable=True)
    es_inquilino = db.Column(db.Boolean, default=False)
    
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)

    def __repr__(self):
        return f'<Propietario {self.nombre}>'

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
    fecha = db.Column(db.DateTime, default=datetime.now)
    tipo = db.Column(db.String(10), nullable=False) # 'INGRESO' o 'EGRESO'
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    comprobante_url = db.Column(db.String(200), nullable=True)
    
    # NUEVO: ¿Es una transferencia interna entre cuentas?
    es_transferencia = db.Column(db.Boolean, default=False)

    # Relaciones
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubro.id'), nullable=False)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=True)
    
    # NUEVO: Relación con la Cuenta (Caja o Banco)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), nullable=False)

    def __repr__(self):
        return f'<{self.tipo} ${self.monto} - {self.fecha.date()}>'