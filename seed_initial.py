from faker import Faker
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from datetime import date, datetime, timedelta
import random
from decimal import Decimal

# ¡MUY IMPORTANTE!
# Este script asume que las tablas YA EXISTEN (creadas por Alembic)
# No ejecuta create_all()

fake = Faker()
db: Session = SessionLocal()

try:
    print("Iniciando población v1.0...")

    # --- 1. Crear Veterinarios ---
    print("Creando veterinarios...")
    vets = []
    for i in range(10):
        vet = models.Veterinarian(
            license_number=fake.unique.bothify(text='VET-#####-??'),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            specialization=random.choice(['Cirugía', 'Dermatología', 'Medicina Interna', 'Oncología', 'General']),
            hire_date=fake.date_between(start_date='-5y', end_date='today')
        )
        vets.append(vet)
    db.add_all(vets)
    db.commit()
    for v in vets: db.refresh(v) # Obtener IDs
    print(f"{len(vets)} veterinarios creados.")

    # --- 2. Crear Dueños ---
    print("Creando dueños...")
    owners = []
    for i in range(20):
        owner = models.Owner(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            address=fake.address()
        )
        owners.append(owner)
    db.add_all(owners)
    db.commit()
    for o in owners: db.refresh(o) # Obtener IDs
    print(f"{len(owners)} dueños creados.")

    # --- 3. Crear Mascotas ---
    print("Creando mascotas...")
    pets = []
    owner_ids = [o.owner_id for o in owners]
    for i in range(30):
        pet = models.Pet(
            name=fake.first_name(),
            species=random.choice(['dog', 'cat', 'bird', 'rabbit', 'other']),
            breed=random.choice(['Labrador', 'Siamese', 'Parakeet', 'Angora', 'Mixto', 'N/A']),
            birth_date=fake.date_of_birth(minimum_age=0, maximum_age=15),
            weight=Decimal(random.uniform(0.5, 40.0)).quantize(Decimal('0.01')),
            owner_id=random.choice(owner_ids)
        )
        pets.append(pet)
    db.add_all(pets)
    db.commit()
    for p in pets: db.refresh(p) # Obtener IDs
    print(f"{len(pets)} mascotas creadas.")

    # --- 4. Crear Citas ---
    print("Creando citas...")
    appointments = []
    pet_ids = [p.pet_id for p in pets]
    vet_ids = [v.veterinarian_id for v in vets]
    vet_ids = [v.veterinarian_id for v in vets]
    
    for i in range(50):
        # Asegurarse de que el pet_id y vet_id sean válidos
        if not pet_ids or not vet_ids:
            print("No hay suficientes mascotas o veterinarios para crear citas.")
            break
            
        pet_id = random.choice(pet_ids)
        
        # Lógica de fechas
        loan_date = fake.date_time_between(start_date='-1y', end_date='now')
        due_date = (loan_date + timedelta(days=random.randint(7, 30))).date()
        status = random.choice(['scheduled', 'completed', 'cancelled', 'no_show'])
        
        appointment = models.Appointment(
            pet_id=pet_id,
            veterinarian_id=random.choice(vet_ids),
            appointment_date=loan_date,
            reason=fake.sentence(nb_words=6),
            status=status,
            notes=fake.paragraph(nb_sentences=2) if status == 'completed' else None
        )
        appointments.append(appointment)
        
    db.add_all(appointments)
    db.commit()
    print(f"{len(appointments)} citas creadas.")

    print("\n¡Población inicial completada!")

except Exception as e:
    print(f"Error durante la población: {e}")
    db.rollback() # Deshacer cambios si algo falló

finally:
    db.close() # Siempre cerrar la sesión