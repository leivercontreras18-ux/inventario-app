import streamlit as st

st.title("Control de Inventario")

# Conexión automática usando los secretos en formato [connections.gsheets]
conn = st.connection("gsheets", type="gsheets")

# Leemos los datos de la hoja de cálculo
df = conn.read()

# Mostramos los datos en la aplicación
st.dataframe(df)
