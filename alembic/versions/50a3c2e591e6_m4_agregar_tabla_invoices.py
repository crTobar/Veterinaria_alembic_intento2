"""M4_Agregar_tabla_invoices

Revision ID: 50a3c2e591e6
Revises: b26d1d9b7890
Create Date: 2025-11-07 01:04:11.010309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text # Necesario para ejecutar SQL


# revision identifiers, used by Alembic.
revision: str = '50a3c2e591e6'
down_revision: Union[str, Sequence[str], None] = 'b26d1d9b7890'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Definición del nuevo ENUM ---
# Lo definimos aquí para usarlo en la columna, pero NO lo crearemos manualmente.
invoice_payment_status_enum = sa.Enum('pending', 'partial', 'paid', 'overdue', name='invoice_payment_status_enum')

# --- Nombre de la tabla de Backup ---
backup_table_name = f'backup_{revision}_invoices'


def upgrade() -> None:
    """
    Paso 1: Aplica la Migración 4 (Facturación).
    """
    
    # --- CREAR TABLA ---
    # Alembic auto-generó esto. El cambio clave es añadir 'create_type=False' al Enum.
    print("Creando tabla 'invoices'...")
    
    op.create_table('invoices',
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        
        # --- CAMBIO IMPORTANTE AQUÍ ---
        # Le decimos a la columna que use el TIPO ENUM,
        # pero que NO intente crearlo (create_type=False).
        # Asumimos que SQLAlchemy/PostgreSQL ya lo conoce o lo creará.
        sa.Column('payment_status', sa.Enum('pending', 'partial', 'paid', 'overdue', name='invoice_payment_status_enum', create_type=False), nullable=True),
        # --- FIN DEL CAMBIO ---

        sa.Column('payment_date', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.appointment_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('invoice_id'),
        sa.UniqueConstraint('appointment_id'),
        sa.UniqueConstraint('invoice_number')
    )
    op.create_index(op.f('ix_invoices_invoice_id'), 'invoices', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=True)

    # --- MIGRACIÓN DE DATOS (Requisito Especial) ---
    print("Generando facturas retroactivas para citas completadas...")
    op.execute(
        text("""
        INSERT INTO invoices (appointment_id, invoice_number, issue_date, 
                              subtotal, tax_amount, total_amount, 
                              payment_status, payment_date)
        SELECT 
            app.appointment_id,
            'INV-HIST-' || app.appointment_id::text,
            DATE(app.appointment_date),
            150.00, 0.00, 150.00, -- Valores de ejemplo
            'paid', app.appointment_date
        FROM 
            appointments AS app
        WHERE 
            app.status = 'completed'
            AND NOT EXISTS (
                SELECT 1 FROM invoices inv 
                WHERE inv.appointment_id = app.appointment_id
            );
        """)
    )


def downgrade() -> None:
    """
    Paso 2: Revierte la Migración 4 (vuelve a M3).
    Guarda los datos de 'invoices' en una tabla de backup
    antes de borrar la estructura.
    """
    
    # 1. Crear tabla de backup
    print(f"Creando backup de datos en {backup_table_name}...")
    op.execute(f"""
        DROP TABLE IF EXISTS {backup_table_name};
        CREATE TABLE {backup_table_name} AS
        SELECT 
            invoice_id,  -- <--- ¡AQUÍ ESTÁ LA CORRECCIÓN!
            appointment_id, 
            invoice_number, 
            issue_date, 
            subtotal, 
            tax_amount, 
            total_amount, 
            payment_status::TEXT AS payment_status, -- Convertir ENUM a TEXT
            payment_date
        FROM invoices;
    """)

    # 2. Revertir esquema (borrar tabla original)
    op.drop_index(op.f('ix_invoices_invoice_number'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_invoice_id'), table_name='invoices')
    op.drop_table('invoices')
    
    # 3. Borrar el tipo ENUM (ahora que nada lo usa)
    op.execute("DROP TYPE IF EXISTS invoice_payment_status_enum")
    
    print(f"Downgrade completado. Datos preservados en {backup_table_name}.")