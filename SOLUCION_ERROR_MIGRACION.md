# Solución: Error "Target database is not up to date"

## 🔴 Error Encontrado

```
ERROR [flask_migrate] Error: Target database is not up to date.
```

## 📋 Causa del Error

Este error ocurre cuando:
1. La base de datos tiene un estado diferente al esperado por Alembic
2. Hay migraciones pendientes que no se han aplicado
3. El historial de migraciones en la base de datos no coincide con los archivos de migración

## ✅ Solución Paso a Paso

### Paso 1: Verificar el Estado Actual

Primero, verifica qué migraciones están aplicadas y cuáles están pendientes:

```bash
flask db current
```

Esto mostrará la revisión actual de la base de datos.

Luego, verifica el historial completo:

```bash
flask db history
```

### Paso 2: Aplicar Migraciones Pendientes

Si hay migraciones pendientes, aplícalas primero:

```bash
flask db upgrade
```

Este comando aplicará todas las migraciones pendientes y sincronizará la base de datos.

### Paso 3: Verificar Nuevamente

Después de aplicar las migraciones, verifica que todo esté actualizado:

```bash
flask db current
```

Deberías ver algo como:
```
9c36dff2886c (head)
```

### Paso 4: Ahora Sí, Crear la Nueva Migración

Una vez que la base de datos esté actualizada, crea la migración para la tabla de parámetros:

```bash
flask db migrate -m "Agregar tabla de parametros del sistema"
```

### Paso 5: Aplicar la Nueva Migración

```bash
flask db upgrade
```

### Paso 6: Poblar Parámetros Iniciales

```bash
python seed_parametros.py
```

## 🔧 Solución Alternativa: Si el Problema Persiste

Si después de `flask db upgrade` el error persiste, puede haber un desajuste en el historial. Aquí hay opciones:

### Opción A: Verificar en PostgreSQL

Conéctate a PostgreSQL y verifica la tabla de versiones de Alembic:

```sql
\c batan3_db

-- Ver la versión actual registrada
SELECT * FROM alembic_version;

-- Ver todas las tablas existentes
\dt
```

### Opción B: Sincronizar Manualmente (Solo si es necesario)

Si la base de datos tiene todas las tablas pero Alembic no lo sabe:

```bash
# Marcar la base de datos como actualizada a la última migración conocida
flask db stamp head
```

⚠️ **ADVERTENCIA**: Solo usa `stamp` si estás seguro de que la base de datos tiene todas las tablas correctas.

### Opción C: Recrear desde Cero (Desarrollo)

**SOLO EN DESARROLLO** - Si tienes datos de prueba que puedes perder:

```bash
# 1. Eliminar todas las tablas en PostgreSQL
psql -U postgres
\c batan3_db
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
\q

# 2. Recrear las migraciones
flask db upgrade

# 3. Ejecutar el seed principal
python seed.py

# 4. Ahora crear la migración de parámetros
flask db migrate -m "Agregar tabla de parametros del sistema"
flask db upgrade

# 5. Ejecutar el seed de parámetros
python seed_parametros.py
```

## 📊 Verificación Final

Después de resolver el error, verifica que todo funcione:

```bash
# 1. Ver el estado actual
flask db current

# 2. Ver el historial
flask db history

# 3. Verificar en PostgreSQL
psql -U postgres -d batan3_db -c "\dt"

# 4. Verificar que la tabla parametro existe
psql -U postgres -d batan3_db -c "\d parametro"

# 5. Verificar los parámetros creados
psql -U postgres -d batan3_db -c "SELECT categoria, COUNT(*) FROM parametro GROUP BY categoria;"
```

## 🎯 Comandos Resumidos (Solución Rápida)

```bash
# 1. Actualizar base de datos con migraciones pendientes
flask db upgrade

# 2. Crear nueva migración
flask db migrate -m "Agregar tabla de parametros del sistema"

# 3. Aplicar nueva migración
flask db upgrade

# 4. Poblar parámetros
python seed_parametros.py

# 5. Verificar
flask db current
```

## 📝 Notas Importantes

1. **Siempre haz backup** antes de ejecutar migraciones en producción
2. **No uses `stamp`** a menos que sepas exactamente lo que haces
3. **No uses DROP SCHEMA** en producción - perderás todos los datos
4. Si estás en producción y tienes este error, contacta al administrador de base de datos

## 🆘 Si Nada Funciona

Si ninguna solución funciona, proporciona la siguiente información:

```bash
# Ejecuta estos comandos y comparte la salida:
flask db current
flask db history
psql -U postgres -d batan3_db -c "SELECT * FROM alembic_version;"
psql -U postgres -d batan3_db -c "\dt"
```

Esto ayudará a diagnosticar el problema específico.
