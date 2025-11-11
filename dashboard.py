import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Configuración de la Página ---
st.set_page_config(
    page_title=" Clínica Veterinaria",
    page_icon="🐾",
    layout="wide"
)

# URL base de tu API de FastAPI (asegúrate de que esté corriendo)
API_URL = "http://127.0.0.1:8000"

# --- Funciones para Llamar a la API ---
    
@st.cache_data(ttl=15) # Cachear los datos por 15 segundos
def get_data(endpoint):
    """Función genérica para obtener datos de la API."""
    try:
        response = requests.get(f"{API_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Mostrar un error más amigable en la app
        st.error(f"Error al conectar con la API ({endpoint}): {e}")
        return None

def post_data(endpoint, data):
    """Función genérica para enviar datos a la API."""
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al enviar datos ({endpoint}): {response.json().get('detail', e)}")
        return None

# --- Título de la App ---
st.title("🐾 Clínica Veterinaria")
st.markdown("Esta app deberia funcionar con la API de la clínica (vM4 y vM5).")

# --- Sección de Reportes (Métricas M5) ---
st.header("📈 Reportes Rápidos")
st.info("Estos reportes solo funcionarán si la API está en la versión M5 o superior.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Ver Veterinarios Populares"):
        vet_info = []
        
        # 1. Intenta llamar al endpoint de M5
        # get_data() devolverá los datos si tiene éxito (M5), o None si falla (M4)
        report_data_m5 = get_data("/reports/popular-veterinarians")

        # 2. Comprueba si la llamada a M5 fue exitosa (report_data_m5 NO es None)
        if report_data_m5 is not None:
            st.subheader("Veterinarios Más Populares (M5)")
            
            # El endpoint M5 devuelve una lista de objetos Veterinarian
            # que ya incluyen 'total_appointments'
            for vet in report_data_m5:
                vet_info.append({
                    "ID": vet["veterinarian_id"], 
                    "Nombre": f"{vet['first_name']} {vet['last_name']}",
                    "Especialización": vet.get('specialization', 'N/A'),
                    "Total Citas (M5)": vet.get('total_appointments', 0) # Campo de M5
                })
        else:
            # 3. --- FALLBACK M4 ---
            # Si M5 falla (devuelve None), mostramos la advertencia 
            # e intentamos llamar al endpoint v1.0 (que sí funciona en M4)
            st.warning("No se pudo cargar el reporte M5 (API en M4?). Mostrando lista simple de veterinarios.")
            report_data_m4 = get_data("/veterinarians/") # Endpoint que existe en M4
            
            if report_data_m4:
                st.subheader("Lista de Veterinarios (M4)")
                for vet in report_data_m4:
                    vet_info.append({
                        "ID": vet["veterinarian_id"], 
                        "Nombre": f"{vet['first_name']} {vet['last_name']}",
                        "Especialización": vet.get('specialization', 'N/A'),
                        "Total Citas (M5)": "N/A" # El campo no existe en M4
                    })

        # 4. Mostrar los datos que se hayan podido obtener
        if vet_info:
            st.dataframe(pd.DataFrame(vet_info).set_index("ID"), use_container_width=True)
        else:
            # Esto solo se mostrará si fallan AMBAS llamadas
            st.error("No se pudieron cargar los datos de veterinarios.")
with col2:
    if st.button("Ver Alertas de Vacunación (M2+)"):
        alerts = get_data("/reports/vaccination-alerts")
        if alerts:
            st.subheader("Alertas de Vacunación Próximas")
            alert_info = [
                {
                    "Mascota": alert['pet']['name'],
                    "Vacuna": alert['vaccine']['name'],
                    "Próxima Dosis": alert['next_dose_date']
                }
                for alert in alerts
            ]
            st.dataframe(pd.DataFrame(alert_info), use_container_width=True)

with col3:
    st.subheader("Reporte de Ingresos (M4+)")
    start_date = st.date_input("Fecha Inicio", datetime(2025, 1, 1))
    end_date = st.date_input("Fecha Fin", datetime.now())
    if st.button("Generar Reporte de Ingresos"):
        report = get_data(f"/reports/revenue?start_date={start_date}&end_date={end_date}")
        if report:
            st.metric(label="Ingresos Totales (Facturas Pagadas)", value=f"${report.get('total_revenue', 0.00)}")

st.divider()

# --- Gestión de Recursos (Campos Comunes M4/M5) ---
st.header("Gestión de Recursos")

tab_owners, tab_pets, tab_appointments, tab_invoices = st.tabs(["Dueños", "Mascotas", "Citas", "Facturas (M4)"])

# --- Pestaña de Dueños ---
with tab_owners:
    st.subheader("Buscar y Ver Dueños")
    owners = get_data("/owners/")
    if owners:
        # --- LÓGICA DE COMPROBACIÓN (IF) ---
        # Verificamos si el primer dueño tiene los campos de M3 (que existen en M4 y M5)
        if owners and 'emergency_contact' in owners[0]:
            st.markdown("Mostrando campos de M3/M4/M5.")
            owner_df = pd.DataFrame(owners)[["owner_id", "first_name", "last_name", "email", "phone", "emergency_contact", "preferred_payment_method"]]
        else:
            # Si no, mostramos solo los campos básicos (v1.0)
            st.markdown("Mostrando campos básicos (pre-M3).")
            owner_df = pd.DataFrame(owners)[["owner_id", "first_name", "last_name", "email", "phone"]]
        
        st.dataframe(owner_df.set_index("owner_id"), use_container_width=True)
    
    st.subheader("Registrar Nuevo Dueño")
    with st.form("new_owner_form"):
        # Campos comunes
        new_first_name = st.text_input("Nombre")
        new_last_name = st.text_input("Apellido")
        new_email = st.text_input("Email")
        new_phone = st.text_input("Teléfono")
        new_address = st.text_area("Dirección")
        
        # Campos de M3 (que existen en M4 y M5)
        new_emergency_contact = st.text_input("Contacto de Emergencia (M3)")
        new_payment_method = st.selectbox("Método de Pago (M3)", [None, 'cash', 'credit', 'debit', 'insurance'])
        
        submitted_owner = st.form_submit_button("Registrar Dueño")
        if submitted_owner:
            owner_data = {
                "first_name": new_first_name,
                "last_name": new_last_name,
                "email": new_email,
                "phone": new_phone,
                "address": new_address,
                "emergency_contact": new_emergency_contact,
                "preferred_payment_method": new_payment_method
            }
            result = post_data("/owners/", owner_data)
            if result:
                st.success(f"¡Dueño '{result['first_name']}' registrado con ID: {result['owner_id']}!")
                st.rerun()

# --- Pestaña de Mascotas ---
with tab_pets:
    st.subheader("Ver Todas las Mascotas")
    pets = get_data("/pets/")
    if pets:
        pet_info = []
        
        # --- LÓGICA DE COMPROBACIÓN (IF) ---
        # Verificamos si el primer registro tiene campos de M5
        if pets and 'visit_count' in pets[0]:
            st.markdown("Mostrando métricas de M5.")
            for pet in pets:
                pet_info.append({
                    "ID": pet['pet_id'],
                    "Nombre": pet['name'],
                    "Especie": pet['species'],
                    "Dueño (Email)": pet['owner']['email'],
                    "Microchip (M3)": pet.get('microchip_number', 'N/A'),
                    "Visitas (M5)": pet.get('visit_count', 0),
                    "Última Visita (M5)": pet.get('last_visit_date', 'N/A')
                })
        # Si no, verificamos si tiene campos de M3 (pero no M5)
        elif pets and 'microchip_number' in pets[0]:
            st.markdown("Mostrando campos de M3/M4 (sin métricas M5).")
            for pet in pets:
                pet_info.append({
                    "ID": pet['pet_id'],
                    "Nombre": pet['name'],
                    "Especie": pet['species'],
                    "Dueño (Email)": pet['owner']['email'],
                    "Microchip (M3)": pet.get('microchip_number', 'N/A'),
                    "Esterilizado (M3)": "Sí" if pet.get('is_neutered') else "No"
                })
        elif pets:
            # Si no, es v1.0 o v2.0
            st.markdown("Mostrando campos básicos (pre-M3).")
            for pet in pets:
                pet_info.append({
                    "ID": pet['pet_id'],
                    "Nombre": pet['name'],
                    "Especie": pet['species'],
                    "Dueño (Email)": pet['owner']['email'],
                })
        
        st.dataframe(pd.DataFrame(pet_info).set_index("ID"), use_container_width=True)

# --- Pestaña de Citas ---
with tab_appointments:
    st.subheader("Ver Citas Programadas")
    appointments = get_data("/appointments/pending") # Endpoint de M4
    if appointments:
        appt_info = [
            {
                "ID Cita": appt['appointment_id'],
                "Fecha": datetime.fromisoformat(appt['appointment_date']).strftime('%Y-%m-%d %I:%M %p'),
                "Mascota": appt['pet']['name'],
                "Veterinario": f"{appt['veterinarian']['first_name']} {appt['veterinarian']['last_name']}",
                "Razón": appt.get('reason', 'N/A')
            }
            for appt in appointments
        ]
        st.dataframe(pd.DataFrame(appt_info).set_index("ID Cita"), use_container_width=True)

# --- Pestaña de Facturas (M4) ---
with tab_invoices:
    st.subheader("Facturas Pendientes de Pago (M4)")
    invoices = get_data("/invoices/pending")
    if invoices:
        invoice_info = [
            {
                "ID Factura": inv['invoice_id'],
                "Número": inv['invoice_number'],
                "Fecha Emisión": inv['issue_date'],
                "ID Cita": inv.get('appointment_id', 'N/A'),
                "Total": f"${inv['total_amount']}",
                "Estado": inv['payment_status']
            }
            for inv in invoices
        ]
        st.dataframe(pd.DataFrame(invoice_info).set_index("ID Factura"), use_container_width=True)