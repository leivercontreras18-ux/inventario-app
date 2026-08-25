import streamlit as st
from google.oauth2.service_account import Credentials

# Convertimos los secretos de la conexión de gsheets a un diccionario limpio
service_account_info = dict(st.secrets["connections.gsheets"])

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
