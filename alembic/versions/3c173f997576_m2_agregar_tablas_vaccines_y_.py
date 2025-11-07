"""M2_Agregar_tablas_vaccines_y_vaccination_records

Revision ID: 3c173f997576
Revises: 4501f9a711d1
Create Date: 2025-11-06 22:05:45.504216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text # Importante para sa.text()


# revision identifiers, used by Alembic.
revision: str = '3c173f997576'
down_revision: Union[str, Sequence[str], None] = '4501f9a711d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Paso 1: Aplica la Migración 2.
    Revisa si existen backups. Si existen, los restaura. Si no, crea las tablas.
    """
    
    # Obtener la conexión actual de Alembic
    conn = op.get_bind()

    # --- PRIMERO, la tabla "padre" (vaccines) ---
    
    # 1. Revisar si el backup '_alembic_backup_vaccines' existe
    result_vaccines = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '_alembic_backup_vaccines')"
    )).scalar() # .scalar() devuelve el primer resultado (True o False)

    if result_vaccines:
        # 2a. Si existe (True), restauramos la tabla
        print("Restaurando tabla 'vaccines' desde el backup.")
        op.rename_table('_alembic_backup_vaccines', 'vaccines')
    else:
        # 2b. Si no existe (False), creamos la tabla desde cero
        print("Creando tabla 'vaccines' desde cero.")
        op.create_table('vaccines',
            sa.Column('vaccine_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('manufacturer', sa.String(length=200), nullable=True),
            sa.Column('species_applicable', sa.String(length=100), nullable=True),
            sa.PrimaryKeyConstraint('vaccine_id'),
            sa.UniqueConstraint('name')
        )
        op.create_index(op.f('ix_vaccines_vaccine_id'), 'vaccines', ['vaccine_id'], unique=False)

    # --- SEGUNDO, la tabla "hija" (vaccination_records) ---

    # 1. Revisar si el backup '_alembic_backup_vaccination_records' existe
    result_records = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '_alembic_backup_vaccination_records')"
    )).scalar()

    if result_records:
        # 2a. Si existe (True), restauramos
        print("Restaurando tabla 'vaccination_records' desde el backup.")
        op.rename_table('_alembic_backup_vaccination_records', 'vaccination_records')
    else:
        # 2b. Si no existe (False), creamos
        print("Creando tabla 'vaccination_records' desde cero.")
        op.create_table('vaccination_records',
            sa.Column('vaccination_id', sa.Integer(), nullable=False),
            sa.Column('pet_id', sa.Integer(), nullable=False),
            sa.Column('vaccine_id', sa.Integer(), nullable=False),
            sa.Column('veterinarian_id', sa.Integer(), nullable=False),
            sa.Column('vaccination_date', sa.Date(), nullable=False),
            sa.Column('next_dose_date', sa.Date(), nullable=True),
            sa.Column('batch_number', sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(['pet_id'], ['pets.pet_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['vaccine_id'], ['vaccines.vaccine_id'], ),
            sa.ForeignKeyConstraint(['veterinarian_id'], ['veterinarians.veterinarian_id'], ),
            sa.PrimaryKeyConstraint('vaccination_id')
        )
        op.create_index(op.f('ix_vaccination_records_vaccination_id'), 'vaccination_records', ['vaccination_id'], unique=False)


def downgrade() -> None:
    """
    Paso 2: Revierte la Migración 2 (vuelve a v1.0).
    """
    print("Iniciando downgrade... Renombrando tablas para preservar datos.")
    
    # El orden aquí estaba bien (primero hija, luego padre)
    op.rename_table('vaccination_records', '_alembic_backup_vaccination_records')
    op.rename_table('vaccines', '_alembic_backup_vaccines')
    
    print("Downgrade completado. Datos preservados en tablas '_alembic_backup_...'.")