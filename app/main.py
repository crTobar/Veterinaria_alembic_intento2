from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from decimal import Decimal

# Importaciones locales
from . import crud, models, schemas
from .database import engine, get_db

app = FastAPI(title="API Clínica Veterinaria")

# --- Alias de Dependencia ---
DbDep = Depends(get_db)

# === Endpoints Veterinarians ===
@app.post("/veterinarians/", response_model=schemas.Veterinarian, status_code=status.HTTP_201_CREATED, tags=["Veterinarians"])
def create_veterinarian(vet: schemas.VeterinarianCreate, db: Session = DbDep):
    if crud.get_veterinarian_by_email(db, email=vet.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_veterinarian_by_license(db, license_number=vet.license_number):
        raise HTTPException(status_code=400, detail="License number already registered")
    return crud.create_veterinarian(db=db, vet=vet)

@app.get("/veterinarians/", response_model=List[schemas.Veterinarian], tags=["Veterinarians"])
def read_veterinarians(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_veterinarians(db, skip=skip, limit=limit)

@app.get("/veterinarians/{vet_id}", response_model=schemas.Veterinarian, tags=["Veterinarians"])
def read_veterinarian(vet_id: int, db: Session = DbDep):
    db_vet = crud.get_veterinarian(db, vet_id=vet_id)
    if db_vet is None:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return db_vet

@app.put("/veterinarians/{vet_id}", response_model=schemas.Veterinarian, tags=["Veterinarians"])
def update_veterinarian(vet_id: int, vet: schemas.VeterinarianUpdate, db: Session = DbDep):
    db_vet = crud.get_veterinarian(db, vet_id=vet_id)
    if db_vet is None:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    if vet.email and vet.email != db_vet.email and crud.get_veterinarian_by_email(db, email=vet.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if vet.license_number and vet.license_number != db_vet.license_number and crud.get_veterinarian_by_license(db, license_number=vet.license_number):
        raise HTTPException(status_code=400, detail="License number already registered")
    return crud.update_veterinarian(db=db, db_vet=db_vet, vet_update=vet)

@app.delete("/veterinarians/{vet_id}", response_model=schemas.Veterinarian, tags=["Veterinarians"])
def delete_veterinarian(vet_id: int, db: Session = DbDep):
    db_vet = crud.get_veterinarian(db, vet_id=vet_id)
    if db_vet is None:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    deleted_vet = crud.delete_veterinarian(db=db, db_vet=db_vet)
    if deleted_vet is None:
        raise HTTPException(status_code=400, detail="Cannot delete veterinarian with active appointments")
    return deleted_vet

@app.get("/veterinarians/{vet_id}/appointments", response_model=List[schemas.Appointment], tags=["Veterinarians"])
def read_vet_appointments(vet_id: int, db: Session = DbDep):
    if not crud.get_veterinarian(db, vet_id=vet_id):
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return crud.get_appointments_by_veterinarian(db=db, vet_id=vet_id)

@app.get("/veterinarians/{vet_id}/schedule", response_model=List[schemas.Appointment], tags=["Veterinarians"])
def read_vet_schedule(vet_id: int, date: date, db: Session = DbDep):
    if not crud.get_veterinarian(db, vet_id=vet_id):
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return crud.get_appointments_by_vet_and_date(db=db, vet_id=vet_id, date=date)

# === Endpoints Owners ===
@app.post("/owners/", response_model=schemas.Owner, status_code=status.HTTP_201_CREATED, tags=["Owners"])
def create_owner(owner: schemas.OwnerCreate, db: Session = DbDep):
    if crud.get_owner_by_email(db, email=owner.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_owner(db=db, owner=owner)

@app.get("/owners/", response_model=List[schemas.Owner], tags=["Owners"])
def read_owners(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_owners(db, skip=skip, limit=limit)

@app.get("/owners/{owner_id}", response_model=schemas.Owner, tags=["Owners"])
def read_owner(owner_id: int, db: Session = DbDep):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    return db_owner

@app.put("/owners/{owner_id}", response_model=schemas.Owner, tags=["Owners"])
def update_owner(owner_id: int, owner: schemas.OwnerUpdate, db: Session = DbDep):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    if owner.email and owner.email != db_owner.email and crud.get_owner_by_email(db, email=owner.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.update_owner(db=db, db_owner=db_owner, owner_update=owner)

@app.delete("/owners/{owner_id}", response_model=schemas.Owner, tags=["Owners"])
def delete_owner(owner_id: int, db: Session = DbDep):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    deleted_owner = crud.delete_owner(db=db, db_owner=db_owner)
    if deleted_owner is None:
        raise HTTPException(status_code=400, detail="Cannot delete owner with associated pets")
    return deleted_owner

@app.get("/owners/{owner_id}/pets", response_model=List[schemas.Pet], tags=["Owners"])
def read_owner_pets(owner_id: int, db: Session = DbDep):
    if not crud.get_owner(db, owner_id=owner_id):
        raise HTTPException(status_code=404, detail="Owner not found")
    return crud.get_pets_by_owner(db=db, owner_id=owner_id)

@app.get("/owners/{owner_id}/appointments", response_model=List[schemas.Appointment], tags=["Owners"])
def read_owner_appointments(owner_id: int, db: Session = DbDep):
    if not crud.get_owner(db, owner_id=owner_id):
        raise HTTPException(status_code=404, detail="Owner not found")
    return crud.get_appointments_by_owner(db=db, owner_id=owner_id)

# === Endpoints Pets ===
@app.post("/pets/", response_model=schemas.Pet, status_code=status.HTTP_201_CREATED, tags=["Pets"])
def create_pet(pet: schemas.PetCreate, db: Session = DbDep):
    if not crud.get_owner(db, owner_id=pet.owner_id):
        raise HTTPException(status_code=400, detail=f"Owner with id {pet.owner_id} not found")
    created_pet = crud.create_pet(db=db, pet=pet)
    return crud.get_pet(db, created_pet.pet_id)

@app.get("/pets/", response_model=List[schemas.Pet], tags=["Pets"])
def read_pets(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_pets(db, skip=skip, limit=limit)

@app.get("/pets/{pet_id}", response_model=schemas.Pet, tags=["Pets"])
def read_pet(pet_id: int, db: Session = DbDep):
    db_pet = crud.get_pet(db, pet_id=pet_id)
    if db_pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return db_pet

@app.put("/pets/{pet_id}", response_model=schemas.Pet, tags=["Pets"])
def update_pet(pet_id: int, pet: schemas.PetUpdate, db: Session = DbDep):
    db_pet = crud.get_pet(db, pet_id=pet_id)
    if db_pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    if pet.owner_id and pet.owner_id != db_pet.owner_id and not crud.get_owner(db, owner_id=pet.owner_id):
        raise HTTPException(status_code=400, detail=f"Owner with id {pet.owner_id} not found")
    updated_pet = crud.update_pet(db=db, db_pet=db_pet, pet_update=pet)
    return crud.get_pet(db, updated_pet.pet_id)

@app.delete("/pets/{pet_id}", response_model=schemas.Pet, tags=["Pets"])
def delete_pet(pet_id: int, db: Session = DbDep):
    db_pet = crud.get_pet(db, pet_id=pet_id)
    if db_pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    deleted_pet = crud.delete_pet(db=db, db_pet=db_pet)
    if deleted_pet is None:
        raise HTTPException(status_code=400, detail="Cannot delete pet with active appointments")
    return deleted_pet

# --- Endpoints Relacionales de Pets (M1, M2) ---
@app.get("/pets/{pet_id}/medical-history", response_model=List[schemas.MedicalRecord], tags=["Pets", "Medical Records"])
def read_pet_medical_history(pet_id: int, db: Session = DbDep):
    if not crud.get_pet(db, pet_id=pet_id):
        raise HTTPException(status_code=404, detail="Pet not found")
    return crud.get_medical_records_by_pet(db=db, pet_id=pet_id)

@app.get("/pets/{pet_id}/vaccinations", response_model=List[schemas.VaccinationRecord], tags=["Pets", "Vaccination Records"])
def read_pet_vaccinations(pet_id: int, db: Session = DbDep):
    if not crud.get_pet(db, pet_id=pet_id):
        raise HTTPException(status_code=404, detail="Pet not found")
    return crud.get_vaccinations_by_pet(db=db, pet_id=pet_id)

@app.get("/pets/{pet_id}/vaccination-schedule", response_model=List[schemas.VaccinationRecord], tags=["Pets", "Vaccination Records"])
def read_pet_vaccination_schedule(pet_id: int, db: Session = DbDep):
    if not crud.get_pet(db, pet_id=pet_id):
        raise HTTPException(status_code=404, detail="Pet not found")
    return crud.get_vaccination_schedule_by_pet(db=db, pet_id=pet_id)


# === Endpoints Appointments ===
@app.post("/appointments/", response_model=schemas.Appointment, status_code=status.HTTP_201_CREATED, tags=["Appointments"])
def create_appointment(appt: schemas.AppointmentCreate, db: Session = DbDep):
    created_appt = crud.create_appointment(db=db, appt=appt)
    if created_appt is None:
        raise HTTPException(status_code=404, detail="Pet or Veterinarian not found")
    # Recargar para obtener relaciones
    return crud.get_appointment(db, created_appt.appointment_id)

@app.get("/appointments/", response_model=List[schemas.Appointment], tags=["Appointments"])
def read_appointments(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_appointments(db, skip=skip, limit=limit)

@app.get("/appointments/today", response_model=List[schemas.Appointment], tags=["Appointments"])
def read_appointments_today(db: Session = DbDep):
    return crud.get_appointments_by_status_or_date(db=db, date=date.today())

@app.get("/appointments/pending", response_model=List[schemas.Appointment], tags=["Appointments"])
def read_pending_appointments(db: Session = DbDep):
    return crud.get_appointments_by_status_or_date(db=db, status='scheduled')

@app.get("/appointments/{appt_id}", response_model=schemas.Appointment, tags=["Appointments"])
def read_appointment(appt_id: int, db: Session = DbDep):
    db_appt = crud.get_appointment(db, appt_id=appt_id)
    if db_appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appt

@app.put("/appointments/{appt_id}", response_model=schemas.Appointment, tags=["Appointments"])
def update_appointment(appt_id: int, appt: schemas.AppointmentUpdate, db: Session = DbDep):
    db_appt = crud.get_appointment(db, appt_id=appt_id)
    if db_appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.pet_id and appt.pet_id != db_appt.pet_id and not crud.get_pet(db, pet_id=appt.pet_id):
        raise HTTPException(status_code=400, detail=f"Pet with id {appt.pet_id} not found")
    if appt.veterinarian_id and appt.veterinarian_id != db_appt.veterinarian_id and not crud.get_veterinarian(db, vet_id=appt.veterinarian_id):
        raise HTTPException(status_code=400, detail=f"Veterinarian with id {appt.veterinarian_id} not found")
    
    updated_appt = crud.update_appointment(db=db, db_appt=db_appt, appt_update=appt)
    return crud.get_appointment(db, updated_appt.appointment_id) # Recargar

@app.put("/appointments/{appt_id}/complete", response_model=schemas.Appointment, tags=["Appointments"])
def complete_appointment(appt_id: int, db: Session = DbDep):
    db_appt = crud.get_appointment(db, appt_id=appt_id)
    if db_appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    update_data = schemas.AppointmentUpdate(status=schemas.AppointmentStatusEnum.completed)
    return crud.update_appointment(db=db, db_appt=db_appt, appt_update=update_data)

@app.put("/appointments/{appt_id}/cancel", response_model=schemas.Appointment, tags=["Appointments"])
def cancel_appointment(appt_id: int, db: Session = DbDep):
    db_appt = crud.get_appointment(db, appt_id=appt_id)
    if db_appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Lógica de negocio: revertir métricas si se cancela
    # (Asumiendo que delete_appointment hace lo mismo)
    deleted_appt = crud.delete_appointment(db=db, db_appt=db_appt)
    # Marcarla como cancelada en lugar de borrarla (mejor)
    # update_data = schemas.AppointmentUpdate(status=schemas.AppointmentStatusEnum.cancelled)
    # return crud.update_appointment(db=db, db_appt=db_appt, appt_update=update_data)
    
    # Para este ejercicio, seguir el delete_appointment que revierte métricas
    return deleted_appt 

@app.delete("/appointments/{appt_id}", response_model=schemas.Appointment, tags=["Appointments"])
def delete_appointment(appt_id: int, db: Session = DbDep):
    db_appt = crud.get_appointment(db, appt_id=appt_id)
    if db_appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return crud.delete_appointment(db=db, db_appt=db_appt)


# === Endpoints Medical Records (M1) ===
@app.post("/medical-records/", response_model=schemas.MedicalRecord, status_code=status.HTTP_201_CREATED, tags=["Medical Records"])
def create_medical_record(record: schemas.MedicalRecordCreate, db: Session = DbDep):
    db_appointment = crud.get_appointment(db, appt_id=record.appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if db_appointment.status != 'completed':
        raise HTTPException(status_code=400, detail="Cannot create medical record for an appointment that is not completed")
    if crud.get_medical_record_by_appointment(db, appointment_id=record.appointment_id):
        raise HTTPException(status_code=400, detail="A medical record already exists for this appointment")
    return crud.create_medical_record(db=db, record=record)

@app.get("/medical-records/", response_model=List[schemas.MedicalRecord], tags=["Medical Records"])
def read_medical_records(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return db.query(models.MedicalRecord).offset(skip).limit(limit).all()

@app.get("/medical-records/{record_id}", response_model=schemas.MedicalRecord, tags=["Medical Records"])
def read_medical_record(record_id: int, db: Session = DbDep):
    db_record = crud.get_medical_record(db, record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return db_record

@app.put("/medical-records/{record_id}", response_model=schemas.MedicalRecord, tags=["Medical Records"])
def update_medical_record(record_id: int, record: schemas.MedicalRecordUpdate, db: Session = DbDep):
    db_record = crud.get_medical_record(db, record_id=record_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return crud.update_medical_record(db=db, db_record=db_record, record_update=record)


# === Endpoints Vaccines (M2) ===
@app.post("/vaccines/", response_model=schemas.Vaccine, status_code=status.HTTP_201_CREATED, tags=["Vaccines"])
def create_vaccine(vaccine: schemas.VaccineCreate, db: Session = DbDep):
    db_vaccine = crud.get_vaccine_by_name(db, name=vaccine.name)
    if db_vaccine:
        raise HTTPException(status_code=400, detail="Vaccine name already registered")
    return crud.create_vaccine(db=db, vaccine=vaccine)

@app.get("/vaccines/", response_model=List[schemas.Vaccine], tags=["Vaccines"])
def read_vaccines(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_vaccines(db, skip=skip, limit=limit)


# === Endpoints Vaccination Records (M2) ===
@app.post("/vaccination-records/", response_model=schemas.VaccinationRecord, status_code=status.HTTP_201_CREATED, tags=["Vaccination Records"])
def create_vaccination_record(record: schemas.VaccinationRecordCreate, db: Session = DbDep):
    if not crud.get_pet(db, pet_id=record.pet_id):
        raise HTTPException(status_code=404, detail="Pet not found")
    if not crud.get_vaccine(db, vaccine_id=record.vaccine_id):
        raise HTTPException(status_code=404, detail="Vaccine not found")
    if not crud.get_veterinarian(db, vet_id=record.veterinarian_id):
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    
    created_record = crud.create_vaccination_record(db=db, record=record)
    return crud.get_vaccination_record(db, record_id=created_record.vaccination_id)

@app.get("/vaccination-records/", response_model=List[schemas.VaccinationRecord], tags=["Vaccination Records"])
def read_vaccination_records(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_vaccination_records(db, skip=skip, limit=limit)


# === Endpoints Invoices (M4) ===
@app.get("/invoices/", response_model=List[schemas.Invoice], tags=["Invoices"])
def read_invoices(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_invoices(db, skip=skip, limit=limit)

@app.get("/invoices/pending", response_model=List[schemas.Invoice], tags=["Invoices"])
def read_pending_invoices(skip: int = 0, limit: int = 100, db: Session = DbDep):
    return crud.get_pending_invoices(db, skip=skip, limit=limit)

@app.get("/invoices/{invoice_id}", response_model=schemas.Invoice, tags=["Invoices"])
def read_invoice(invoice_id: int, db: Session = DbDep):
    db_invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@app.post("/invoices/{invoice_id}/pay", response_model=schemas.Invoice, tags=["Invoices"])
def pay_invoice(invoice_id: int, db: Session = DbDep):
    db_invoice = crud.get_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if db_invoice.payment_status == 'paid':
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    return crud.mark_invoice_as_paid(db=db, db_invoice=db_invoice)


# === Endpoints Reports (M5) ===
@app.get("/reports/revenue", response_model=schemas.RevenueReport, tags=["Reports"])
def report_revenue(start_date: date, end_date: date, db: Session = DbDep):
    total = crud.get_revenue_report(db, start_date=start_date, end_date=end_date)
    return schemas.RevenueReport(start_date=start_date, end_date=end_date, total_revenue=total)

@app.get("/reports/popular-veterinarians", response_model=List[schemas.Veterinarian], tags=["Reports"])
def report_popular_veterinarians(db: Session = DbDep):
    # Simplemente devuelve los Vets ordenados por 'total_appointments'
    return crud.get_popular_veterinarians(db)

@app.get("/reports/vaccination-alerts", response_model=List[schemas.VaccinationRecord], tags=["Reports"])
def report_vaccination_alerts(db: Session = DbDep):
    # Por defecto, busca vacunas para los próximos 30 días
    return crud.get_vaccination_alerts(db)