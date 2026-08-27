import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Lewin // Inventario Boutique",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (Azul Acero y Celeste - Sin amarillo ni rojo)
st.markdown("""
<style>
    /* Fondo general de la interfaz */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
    /* Botones principales en Azul Acero */
    div.stButton > button {
        background-color: #1e3a8a;
        color: #ffffff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background-color: #2563eb;
        border-color: #60a5fa;
        color: #ffffff;
    }
    
    /* Títulos y acentos en Celeste */
    h1, h2, h3, h4, h5, h6 {
        color: #38bdf8 !important;
    }
    
    /* Campos de entrada de texto */
    .stTextInput input {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 6px;
    }
    
    .stTextInput input:focus {
        border-color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar / Menú Principal
with st.sidebar:
    st.markdown("### 👤 SESIÓN ACTIVA")
    st.info("Leiver")
    st.markdown("---")
    st.markdown("### MENÚ PRINCIPAL")
    
    menu = st.radio(
        "Navegación",
        ["Existencias", "Registrar Prenda", "Editar / Borrar", "Configuración"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.warning("Sesión cerrada.")

# Contenido principal según la opción seleccionada
if menu == "Configuración":
    st.title("⚙️ Configuración del Sistema")
    st.markdown("Gestiona y personaliza las opciones maestras de categorías, tallas y colores. Haz clic en guardar al terminar.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📁 Categorías")
        st.markdown("- Falda")
        st.text_input("Nueva Categoría", placeholder="Ej: Faldas", key="nueva_cat", label_visibility="collapsed")
        if st.button("➕ Agregar Categoría"):
            st.success("Categoría agregada")
            
    with col2:
        st.markdown("### 📏 Tallas")
        st.markdown("- M")
        st.text_input("Nueva Talla", placeholder="Ej: 30, XXL", key="nueva_talla", label_visibility="collapsed")
        if st.button("➕ Agregar Talla"):
            st.success("Talla agregada")
            
    with col3:
        st.markdown("### 🎨 Colores")
        st.markdown("- Celeste")
        st.text_input("Nuevo Color", placeholder="Ej: Azul Acero", key="new_color", label_visibility="collapsed")
        if st.button("➕ Agregar Color"):
            st.success("Color agregado")
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar configuración en GitHub", use_container_width=True):
        st.success("¡Configuración guardada correctamente en GitHub!")

elif menu == "Existencias":
    st.title("📦 Existencias de Inventario")
    st.write("Consulta y filtra el inventario actual de la boutique.")

elif menu == "Registrar Prenda":
    st.title("➕ Registrar Prenda")
    st.write("Añade nuevas prendas al catálogo de la boutique.")

elif menu == "Editar / Borrar":
    st.title("✏️ Editar / Borrar Prendas")
    st.write("Modifica o elimina registros existentes.")
