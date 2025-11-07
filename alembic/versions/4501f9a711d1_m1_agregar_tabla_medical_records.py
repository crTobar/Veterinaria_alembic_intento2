"""M1_Agregar_tabla_medical_records

Revision ID: 4501f9a711d1
Revises: 63590237cb51
Create Date: 2025-11-03 17:14:55.128133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text # Necesario para ejecutar SQL crudo

# revision identifiers, used by Alembic.
revision: str = '4501f9a711d1'
down_revision: Union[str, Sequence[str], None] = '63590237cb51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Comandos auto-generados por Alembic - Paso 1: Crear Esquema ###
    op.create_table('medical_records',
    sa.Column('record_id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('diagnosis', sa.Text(), nullable=False),
    sa.Column('treatment', sa.Text(), nullable=False),
    sa.Column('prescription', sa.Text(), nullable=True),
    sa.Column('follow_up_required', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.appointment_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('record_id'),
    sa.UniqueConstraint('appointment_id')
    )
    op.create_index(op.f('ix_medical_records_record_id'), 'medical_records', ['record_id'], unique=False)
    # ### end Alembic commands ###

    # --- INICIO DE TU LÓGICA MANUAL (Paso 2: Migración de Datos Históricos) ---
    # Requisito especial: Popular esta tabla con datos históricos basados en las citas completadas existentes.
    
    # Asumimos que el 'diagnosis' inicial puede venir de las 'notes' de la cita
    # y el 'treatment' será un texto por defecto ya que no existía antes.
    # 'prescription' será NULL por defecto.
    
    # Ejecutamos una sentencia SQL directa.
    op.execute(
        text("""
        INSERT INTO medical_records (appointment_id, diagnosis, treatment, prescription, follow_up_required, created_at)
        SELECT 
            app.appointment_id,
            COALESCE(app.notes, 'Diagnóstico preliminar basado en cita completada'),
            'Tratamiento inicial no especificado',
            NULL,
            FALSE,
            app.created_at
        FROM 
            appointments AS app
        WHERE 
            app.status = 'completed';
        """)
    )
    # --- FIN DE TU LÓGICA MANUAL ---


def downgrade() -> None:
    # ### Comandos auto-generados por Alembic - Reversión de Esquema ###
    # Para downgrade, simplemente borramos la tabla y sus índices.
    # No hay necesidad de "des-popular" los datos, ya que la tabla se va.
    op.drop_index(op.f('ix_medical_records_record_id'), table_name='medical_records')
    op.drop_table('medical_records')
    # ### end Alembic commands ###