"""M5_Agregar_metricas_a_vets_y_pets

Revision ID: b9d925015eb2
Revises: 50a3c2e591e6
Create Date: 2025-11-07 04:15:24.864746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'b9d925015eb2'
down_revision: Union[str, Sequence[str], None] = '50a3c2e591e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# --- Nombres de tablas de backup (para downgrade) ---
pets_backup_table = f'backup_{revision}_pets'
vets_backup_table = f'backup_{revision}_vets'


def upgrade() -> None:
    # ### Paso 1: Añadir las nuevas columnas (auto-generado) ###
    
    # --- Columnas de PETS ---
    op.add_column('pets', sa.Column('last_visit_date', sa.Date(), nullable=True))
    # Añadimos la columna como nullable=True primero, la poblamos, y luego la hacemos non-nullable
    op.add_column('pets', sa.Column('visit_count', sa.Integer(), nullable=True)) 

    # --- Columnas de VETERINARIANS ---
    op.add_column('veterinarians', sa.Column('consultation_fee', sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column('veterinarians', sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True))
    # Añadimos la columna como nullable=True primero
    op.add_column('veterinarians', sa.Column('total_appointments', sa.Integer(), nullable=True))

    # ### Paso 2: Migración de Datos Históricos (Requisito Especial) ###
    
    print("Calculando y poblando métricas históricas...")

    # 1. Poner defaults (0) para todos, antes de calcular
    op.execute("UPDATE pets SET visit_count = 0 WHERE visit_count IS NULL")
    op.execute("UPDATE veterinarians SET total_appointments = 0 WHERE total_appointments IS NULL")

    # 2. Calcular 'visit_count' y 'last_visit_date' para Pets
    # Usamos solo citas 'completadas' como "visitas"
    op.execute(
        text("""
        WITH pet_stats AS (
            SELECT 
                pet_id,
                COUNT(appointment_id) AS total_visits,
                MAX(appointment_date::date) AS last_visit
            FROM 
                appointments
            WHERE 
                status = 'completed'
            GROUP BY 
                pet_id
        )
        UPDATE pets p
        SET
            visit_count = ps.total_visits,
            last_visit_date = ps.last_visit
        FROM 
            pet_stats ps
        WHERE 
            p.pet_id = ps.pet_id;
        """)
    )
    
    # 3. Calcular 'total_appointments' para Veterinarians
    # Contamos *todas* las citas (incluyendo canceladas, etc.)
    op.execute(
        text("""
        WITH vet_stats AS (
            SELECT 
                veterinarian_id,
                COUNT(appointment_id) AS total_appts
            FROM 
                appointments
            GROUP BY 
                veterinarian_id
        )
        UPDATE veterinarians v
        SET
            total_appointments = vs.total_appts
        FROM 
            vet_stats vs
        WHERE 
            v.veterinarian_id = vs.veterinarian_id;
        """)
    )

    # ### Paso 3: Alterar columnas a NOT NULL (como en el modelo) ###
    op.alter_column('pets', 'visit_count',
               existing_type=sa.INTEGER(),
               nullable=False,
               server_default='0') # Establecer default para futuras inserciones
               
    op.alter_column('veterinarians', 'total_appointments',
               existing_type=sa.INTEGER(),
               nullable=False,
               server_default='0') # Establecer default para futuras inserciones

    # ### Paso 4: Lógica de Restauración (si venimos de un downgrade) ###
    op.execute(f"""
        DO $$
        BEGIN
           IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{vets_backup_table}') THEN
              UPDATE veterinarians v
              SET 
                consultation_fee = b.consultation_fee,
                rating = b.rating,
                total_appointments = b.total_appointments
              FROM {vets_backup_table} b
              WHERE v.veterinarian_id = b.veterinarian_id;
              
              DROP TABLE {vets_backup_table};
           END IF;
           
           IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{pets_backup_table}') THEN
              UPDATE pets p
              SET 
                last_visit_date = b.last_visit_date,
                visit_count = b.visit_count
              FROM {pets_backup_table} b
              WHERE p.pet_id = b.pet_id;
              
              DROP TABLE {pets_backup_table};
           END IF;
        END $$;
    """)

def downgrade() -> None:
    # ### Requisito especial: Backup de datos ###

    # 1. Crear tablas de backup
    print(f"Creando backup de datos en {pets_backup_table} y {vets_backup_table}...")
    op.execute(f"""
        DROP TABLE IF EXISTS {pets_backup_table};
        CREATE TABLE {pets_backup_table} AS
        SELECT pet_id, last_visit_date, visit_count
        FROM pets;
    """)
    
    op.execute(f"""
        DROP TABLE IF EXISTS {vets_backup_table};
        CREATE TABLE {vets_backup_table} AS
        SELECT veterinarian_id, consultation_fee, rating, total_appointments
        FROM veterinarians;
    """)
    
    # 2. Revertir esquema (borrar columnas)
    print("Revirtiendo esquema: borrando columnas de métricas...")
    op.drop_column('veterinarians', 'total_appointments')
    op.drop_column('veterinarians', 'rating')
    op.drop_column('veterinarians', 'consultation_fee')
    op.drop_column('pets', 'visit_count')
    op.drop_column('pets', 'last_visit_date')
    
    print(f"Downgrade completado. Datos preservados en {pets_backup_table} y {vets_backup_table}.")