import streamlit as st
from google.oauth2.service_account import Credentials

# Cargamos los secretos directamente desde la raíz configurada en Streamlit
service_account_info = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
    "universe_domain": st.secrets["universe_domain"]
}

# Definimos los permisos necesarios
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Creamos las credenciales correctamente
creds = Credentials.from_service_account_info(
    service_account_info, 
    scopes=scopes
)

# A partir de aquí continúa el resto de la lógica de tu inventario...
st.success("¡Conexión configurada correctamente!")
