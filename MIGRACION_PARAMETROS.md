# Migración de Base de Datos - Tabla de Parámetros

## 📋 Descripción

Se ha agregado un nuevo modelo `Parametro` al sistema para controlar aspectos configurables del funcionamiento. Esta tabla permite almacenar parámetros del sistema de forma flexible con soporte para diferentes tipos de datos.

## 🗂️ Estructura del Modelo

### Tabla: `parametro`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | Clave primaria |
| `clave` | String(100) | Identificador único del parámetro (UNIQUE) |
| `valor` | Text | Valor almacenado como texto |
| `tipo` | String(20) | Tipo de dato: TEXT, NUMBER, BOOLEAN, DATE, JSON |
| `descripcion` | String(255) | Descripción del parámetro |
| `categoria` | String(50) | Categoría para agrupar: GENERAL, NOTIFICACIONES, FINANZAS, etc. |
| `editable` | Boolean | Si el usuario puede editarlo desde la interfaz |
| `fecha_modificacion` | DateTime | Fecha de última modificación |

### Métodos Útiles

- `get_valor_typed()`: Retorna el valor convertido al tipo correcto
- `Parametro.get_parametro(clave, default)`: Obtiene un parámetro por su clave
- `Parametro.set_parametro(clave, valor, tipo, descripcion, categoria)`: Crea o actualiza un parámetro

## 🚀 Instrucciones de Migración

### Paso 1: Verificar el Modelo

El modelo ya ha sido agregado a `app/models.py`. Verifica que el archivo contenga la clase `Parametro`.

### Paso 2: Generar la Migración

Ejecuta el siguiente comando para generar el script de migración:

```bash
flask db migrate -m "Agregar tabla de parametros del sistema"
```

Este comando:
- Detectará automáticamente el nuevo modelo `Parametro`
- Generará un archivo de migración en `migrations/versions/`
- El archivo contendrá las instrucciones SQL para crear la tabla

### Paso 3: Revisar el Script de Migración

Abre el archivo generado en `migrations/versions/` y verifica que contenga:

```python
def upgrade():
    op.create_table('parametro',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('clave', sa.String(length=100), nullable=False),
        sa.Column('valor', sa.Text(), nullable=True),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('categoria', sa.String(length=50), nullable=True),
        sa.Column('editable', sa.Boolean(), nullable=True),
        sa.Column('fecha_modificacion', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clave')
    )
```

### Paso 4: Aplicar la Migración

Ejecuta el siguiente comando para aplicar la migración a la base de datos:

```bash
flask db upgrade
```

Este comando:
- Ejecutará el script de migración
- Creará la tabla `parametro` en PostgreSQL
- Actualizará el historial de migraciones

### Paso 5: Verificar la Migración

Conéctate a PostgreSQL y verifica que la tabla se creó correctamente:

```sql
-- Conectar a la base de datos
\c batan3_db

-- Listar tablas
\dt

-- Ver estructura de la tabla parametro
\d parametro

-- Verificar que está vacía
SELECT * FROM parametro;
```

## 📝 Poblar Parámetros Iniciales (Opcional)

Puedes crear un script para poblar parámetros iniciales. Crea un archivo `seed_parametros.py`:

```python
from app import create_app, db
from app.models import Parametro

app = create_app()

with app.app_context():
    # Parámetros Generales
    Parametro.set_parametro(
        'nombre_edificio', 
        'Edificio Batan 3', 
        'TEXT', 
        'Nombre del edificio o condominio',
        'GENERAL'
    )
    
    Parametro.set_parametro(
        'direccion', 
        'Av. Principal #123', 
        'TEXT', 
        'Dirección física del edificio',
        'GENERAL'
    )
    
    # Parámetros de Notificaciones
    Parametro.set_parametro(
        'enviar_emails_automaticos', 
        True, 
        'BOOLEAN', 
        'Activar envío automático de emails',
        'NOTIFICACIONES'
    )
    
    Parametro.set_parametro(
        'dias_antes_vencimiento', 
        5, 
        'NUMBER', 
        'Días antes del vencimiento para enviar recordatorio',
        'NOTIFICACIONES'
    )
    
    # Parámetros Financieros
    Parametro.set_parametro(
        'dia_vencimiento_expensas', 
        10, 
        'NUMBER', 
        'Día del mes en que vencen las expensas',
        'FINANZAS'
    )
    
    Parametro.set_parametro(
        'interes_mora_mensual', 
        2.5, 
        'NUMBER', 
        'Porcentaje de interés por mora mensual',
        'FINANZAS'
    )
    
    Parametro.set_parametro(
        'cuenta_predeterminada_ingresos', 
        'Banco Pichincha', 
        'TEXT', 
        'Cuenta predeterminada para registrar ingresos',
        'FINANZAS'
    )
    
    # Parámetros de Contacto
    Parametro.set_parametro(
        'telefono_administracion', 
        '0987654321', 
        'TEXT', 
        'Teléfono de contacto de la administración',
        'CONTACTO'
    )
    
    Parametro.set_parametro(
        'email_administracion', 
        'admin@batan3.com', 
        'TEXT', 
        'Email de contacto de la administración',
        'CONTACTO'
    )
    
    Parametro.set_parametro(
        'whatsapp_administracion', 
        '593987654321', 
        'TEXT', 
        'WhatsApp de la administración (con código de país)',
        'CONTACTO'
    )
    
    db.session.commit()
    print("✅ Parámetros iniciales creados exitosamente")
```

Ejecutar el script:

```bash
python seed_parametros.py
```

## 🔧 Uso en el Código

### Obtener un Parámetro

```python
from app.models import Parametro

# Método 1: Usando el helper estático
nombre_edificio = Parametro.get_parametro('nombre_edificio', 'Edificio Sin Nombre')

# Método 2: Query directo
param = Parametro.query.filter_by(clave='enviar_emails_automaticos').first()
if param:
    valor = param.get_valor_typed()  # Retorna True/False si es BOOLEAN
```

### Actualizar un Parámetro

```python
from app import db
from app.models import Parametro

# Método 1: Usando el helper estático
Parametro.set_parametro('dias_antes_vencimiento', 7, 'NUMBER')
db.session.commit()

# Método 2: Query directo
param = Parametro.query.filter_by(clave='interes_mora_mensual').first()
if param:
    param.valor = '3.0'
    param.fecha_modificacion = datetime.now()
    db.session.commit()
```

## 🎯 Ejemplos de Uso Práctico

### En Rutas (Routes)

```python
from app.models import Parametro

@app.route('/enviar-notificacion')
def enviar_notificacion():
    # Verificar si las notificaciones están activadas
    if Parametro.get_parametro('enviar_emails_automaticos', False):
        dias_antes = Parametro.get_parametro('dias_antes_vencimiento', 5)
        # Lógica de envío...
```

### En Templates (Jinja2)

Primero, pasar el parámetro desde la ruta:

```python
@app.route('/contacto')
def contacto():
    telefono = Parametro.get_parametro('telefono_administracion', 'N/A')
    email = Parametro.get_parametro('email_administracion', 'N/A')
    return render_template('contacto.html', telefono=telefono, email=email)
```

## ⚠️ Notas Importantes

1. **Backup**: Siempre haz un backup de la base de datos antes de ejecutar migraciones
2. **Entorno**: Asegúrate de estar en el entorno correcto (desarrollo/producción)
3. **Permisos**: Verifica que el usuario de PostgreSQL tenga permisos para crear tablas
4. **Rollback**: Si algo sale mal, puedes revertir con `flask db downgrade`

## 🔄 Rollback (Si es necesario)

Si necesitas revertir la migración:

```bash
flask db downgrade
```

Esto eliminará la tabla `parametro` y revertirá al estado anterior.

## ✅ Verificación Final

Después de la migración, verifica:

1. ✅ La tabla `parametro` existe en la base de datos
2. ✅ Tiene todos los campos correctos
3. ✅ El constraint UNIQUE en `clave` funciona
4. ✅ Puedes insertar y consultar registros
5. ✅ Los métodos helper funcionan correctamente

## 📞 Soporte

Si encuentras problemas durante la migración:
- Revisa los logs de Flask: `flask run --debug`
- Revisa los logs de PostgreSQL
- Verifica las variables de entorno en `.env`
- Asegúrate de que la conexión a la base de datos funciona
