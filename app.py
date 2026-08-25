import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Control de Inventario", page_icon="📦", layout="wide")

# --- DICCIONARIO DE USUARIOS AUTORIZADOS ---
USUARIOS = {
    "leiver": "ClaveSegura123!",
    "amigo1": "ClaveAmigo123!"
}

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""

if not st.session_state.autenticado:
    st.title("🔒 Acceso Privado - Inventario")
    usuario_input = st.text_input("Usuario")
    clave_input = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión"):
        if usuario_input in USUARIOS and USUARIOS[usuario_input] == clave_input:
            st.session_state.autenticado = True
            st.session_state.usuario_actual = usuario_input
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
            
    st.stop()

else:
    st.sidebar.write(f"👤 Conectado como: {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.rerun()

st.title("📦 Control de Inventario")

# --- CONEXIÓN DIRECTA A GOOGLE SHEETS (VÍA GSPREAD) ---
@st.cache_data(ttl=0)
def cargar_datos():
    sec = st.secrets["connections"]["gsheets"]
    
    # RECONSTRUCCIÓN ROBUSTA DE LA LLAVE PRIVADA
    pk = sec["private_key"]
    
    # Limpiamos espacios y aseguramos formato de saltos
    pk = pk.strip()
    
    # Si la clave viene comprimida en una sola línea o con escapes dañados, la reestructuramos
    if "-----BEGIN PRIVATE KEY-----" in pk and "-----END PRIVATE KEY-----" in pk:
        # Extraer el contenido entre los headers
        body = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
        # Quitar cualquier espacio, salto o barra invertida basura que haya dejado Streamlit
        body = "".join(body.split())
        
        # Volver a formatear en líneas de exactamente 64 caracteres (estándar PEM)
        chunks = [body[i:i+64] for i in range(0, len(body), 64)]
        pk = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(chunks) + "\n-----END PRIVATE KEY-----"

    service_account_info = {
        "type": sec["type"],
        "project_id": sec["project_id"],
        "private_key_id": sec["private_key_id"],
        "private_key": pk,
        "client_email": sec["client_email"],
        "client_id": sec["client_id"],
        "auth_uri": sec["auth_uri"],
        "token_uri": sec["token_uri"],
        "auth_provider_x509_cert_url": sec["auth_provider_x509_cert_url"],
        "client_x509_cert_url": sec["client_x509_cert_url"],
        "universe_domain": sec.get("universe_domain", "googleapis.com")
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    url = sec["spreadsheet"]
    sheet = client.open_by_url(url).sheet1
    
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Cargar y mostrar datos
try:
    df = cargar_datos()
    st.subheader("Estado Actual del Inventario")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error detallado de conexión: {e}")
