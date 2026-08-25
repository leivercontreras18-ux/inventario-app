import streamlit as st
import pandas as pd
import gspread
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
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

# --- CONEXIÓN DIRECTA A GOOGLE SHEETS (DECODIFICACIÓN BASE64 BLINDADA) ---
@st.cache_data(ttl=0)
def cargar_datos():
    sec = st.secrets["connections"]["gsheets"]
    
    raw_key = sec["private_key"]
    
    # Limpiamos delimitadores y espacios en blanco de forma segura
    clean_body = raw_key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    clean_body = "".join(clean_body.split())
    
    # Como la longitud exacta es de 1629 caracteres de texto base64 plano, 
    # la decodificamos directamente a bytes binarios y la cargamos evitando el parsing PEM tradicional
    try:
        der_bytes = base64.b64decode(clean_body)
        private_key_obj = serialization.load_der_private_key(der_bytes, password=None, backend=default_backend())
    except Exception:
        # Plan de respaldo por si el formato entra como PEM estándar corregido
        chunks = [clean_body[i:i+64] for i in range(0, len(clean_body), 64)]
        pem_string = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(chunks) + "\n-----END PRIVATE KEY-----\n"
        private_key_obj = serialization.load_pem_private_key(pem_string.encode("utf-8"), password=None, backend=default_backend())

    service_account_info = {
        "type": sec["type"],
        "project_id": sec["project_id"],
        "private_key_id": sec["private_key_id"],
        "private_key": raw_key.replace("\\n", "\n"),
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
