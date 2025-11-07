"""M3_Mejoras_pets_y_owners

Revision ID: b26d1d9b7890
Revises: 3c173f997576
Create Date: 2025-11-07 00:08:53.576726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b26d1d9b7890'
down_revision: Union[str, Sequence[str], None] = '3c173f997576'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Definimos los nombres de las tablas de backup
# Usamos el 'revision' para que sean únicas de esta migración
pets_backup_table = f'backup_{revision}_pets'
owners_backup_table = f'backup_{revision}_owners'


def upgrade() -> None:
    # ### Comandos auto-generados por Alembic ###
    
    # --- OWNERS ---
    # 1. Crear el nuevo tipo ENUM
    payment_method_enum = sa.Enum('cash', 'credit', 'debit', 'insurance', name='payment_method_enum')
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Añadir las nuevas columnas a 'owners'
    op.add_column('owners', sa.Column('emergency_contact', sa.String(length=50), nullable=True))
    op.add_column('owners', sa.Column('preferred_payment_method', payment_method_enum, nullable=True))

    # --- PETS ---
    # 3. Añadir las nuevas columnas a 'pets'
    op.add_column('pets', sa.Column('microchip_number', sa.String(length=50), nullable=True))
    op.add_column('pets', sa.Column('is_neutered', sa.Boolean(), nullable=True))
    op.add_column('pets', sa.Column('blood_type', sa.String(length=10), nullable=True))
    
    # 4. Establecer valores por defecto para filas existentes
    op.execute("UPDATE pets SET is_neutered = FALSE WHERE is_neutered IS NULL")
    # Cambiamos la columna para que no sea nullable en el futuro, pero primero asignamos default
    op.alter_column('pets', 'is_neutered', nullable=False, server_default='false')
    
    # 5. Crear el índice único para microchip
    op.create_index(op.f('ix_pets_microchip_number'), 'pets', ['microchip_number'], unique=True)
    
    # ### Lógica Manual de Restauración (si venimos de un downgrade) ###
    
    # 6. Intentar restaurar datos desde las tablas de backup (si existen)
    op.execute(f"""
        DO $$
        BEGIN
           IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{owners_backup_table}') THEN
              UPDATE owners o
              SET 
                emergency_contact = b.emergency_contact,
                preferred_payment_method = b.preferred_payment_method::payment_method_enum
              FROM {owners_backup_table} b
              WHERE o.owner_id = b.owner_id;
              
              DROP TABLE {owners_backup_table};
           END IF;
           
           IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{pets_backup_table}') THEN
              UPDATE pets p
              SET 
                microchip_number = b.microchip_number,
                is_neutered = b.is_neutered,
                blood_type = b.blood_type
              FROM {pets_backup_table} b
              WHERE p.pet_id = b.pet_id;
              
              DROP TABLE {pets_backup_table};
           END IF;
        END $$;
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ... (backup de pets, que está bien) ...
    op.execute(f"""
        DROP TABLE IF EXISTS {pets_backup_table};
        CREATE TABLE {pets_backup_table} AS
        SELECT pet_id, microchip_number, is_neutered, blood_type
        FROM pets;
    """)
    
    # --- MODIFICACIÓN AQUÍ ---
    # Convertimos la columna enum a TEXT al hacer el backup
    op.execute(f"""
        DROP TABLE IF EXISTS {owners_backup_table};
        CREATE TABLE {owners_backup_table} AS
        SELECT owner_id, emergency_contact, 
               preferred_payment_method::TEXT AS preferred_payment_method
        FROM owners;
    """)
    # --- FIN DE LA MODIFICACIÓN ---

    # 2. Revertir los cambios del esquema
    op.drop_index(op.f('ix_pets_microchip_number'), table_name='pets')
    op.drop_column('pets', 'blood_type')
    op.drop_column('pets', 'is_neutered')
    op.drop_column('pets', 'microchip_number')
    op.drop_column('owners', 'preferred_payment_method')
    op.drop_column('owners', 'emergency_contact')
    
    # 3. Borrar el tipo ENUM (Ahora sí funcionará)
    op.execute("DROP TYPE IF EXISTS payment_method_enum")
    
    print(f"Downgrade completado. Datos preservados en {pets_backup_table} y {owners_backup_table}.")
    # ### end Alembic commands ###