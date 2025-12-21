"""separar_fecha_emision_y_fecha_pago

Revision ID: 220a77227795
Revises: 7645a7a15c56
Create Date: 2025-12-20 21:45:34.445700

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '220a77227795'
down_revision = '7645a7a15c56'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Agregar nuevas columnas como nullable temporalmente
    with op.batch_alter_table('movimiento', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha_emision', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('fecha_pago', sa.DateTime(), nullable=True))
    
    # 2. Migrar datos existentes
    # Para movimientos PAGADOS: ambas fechas = fecha actual
    # Para movimientos PENDIENTES: solo fecha_emision, fecha_pago = NULL
    op.execute("""
        UPDATE movimiento
        SET fecha_emision = fecha,
            fecha_pago = CASE
                WHEN estado = 'PAGADO' THEN fecha
                ELSE NULL
            END
    """)
    
    # 3. Hacer fecha_emision obligatoria y eliminar fecha antigua
    with op.batch_alter_table('movimiento', schema=None) as batch_op:
        batch_op.alter_column('fecha_emision', nullable=False)
        batch_op.drop_column('fecha')


def downgrade():
    # Rollback: restaurar columna fecha original
    with op.batch_alter_table('movimiento', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha', sa.DATETIME(), nullable=True))
    
    # Copiar fecha_emision de vuelta a fecha
    op.execute("UPDATE movimiento SET fecha = fecha_emision")
    
    # Eliminar las nuevas columnas
    with op.batch_alter_table('movimiento', schema=None) as batch_op:
        batch_op.drop_column('fecha_pago')
        batch_op.drop_column('fecha_emision')
