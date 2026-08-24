import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Inventario", page_icon="📦", layout="wide")

# --- DICCIONARIO DE USUARIOS AUTORIZADOS ---
USUARIOS = {
    "leiver": "ClaveSegura123!",
    "amigo1": "ClaveAmigo123!"
}

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Privado - Inventario")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if user in USUARIOS and USUARIOS[user] == password:
            st.session_state.autenticado = True
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- APP PRINCIPAL ---
st.sidebar.write(f"Bienvenido, *{st.session_state.usuario}* 👋")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📦 Sistema de Control de Inventario")

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

if not df.empty and "Cantidad" in df.columns and "Minimo" in df.columns:
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
    df["Minimo"] = pd.to_numeric(df["Minimo"], errors="coerce").fillna(0)

    bajos = df[df["Cantidad"] <= df["Minimo"]]
    if not bajos.empty:
        st.warning(f"⚠️ *Atención:* Hay {len(bajos)} productos con stock bajo o agotado.")

st.subheader("📋 Inventario Actual")
st.dataframe(df, use_container_width=True)

st.subheader("➕ Registrar / Agregar Producto")
with st.form("nuevo_producto"):
    prod = st.text_input("Nombre del Producto")
    cat = st.selectbox("Categoría", ["Electrónica", "Hogar", "Ropa", "Alimentos", "Otros"])
    cant = st.number_input("Cantidad", min_value=0, value=1)
    min_cant = st.number_input("Stock Mínimo Alerta", min_value=0, value=1)
    
    enviado = st.form_submit_button("Guardar en Google Sheets")
    
    if enviado:
        if prod.strip():
            nuevo_id = len(df) + 1
            nueva_fila = pd.DataFrame([{
                "ID": nuevo_id,
                "Producto": prod,
                "Categoria": cat,
                "Cantidad": cant,
                "Minimo": min_cant
            }])
            df_nuevo = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_nuevo)
            st.success(f"¡{prod} guardado con éxito!")
            st.rerun()
        else:
            st.error("Por favor ingresa un nombre de producto.")
