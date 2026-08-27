import streamlit as st

st.markdown("### ✨ Registro de Nuevas Prendas")
st.markdown("Añade nuevos artículos al catálogo de la boutique de forma rápida y ordenada.")

with st.form("registro_prenda_form", clear_on_submit=True):
    # Bloque 1: Identificación principal
    col1, col2 = st.columns(2)
    with col1:
        id_prenda = st.text_input("ID", placeholder="Ej: A1")
    with col2:
        producto = st.text_input("Producto", placeholder="Ej: Short")

    st.markdown("---")
    
    # Bloque 2: Características de la prenda
    col3, col4, col5 = st.columns(3)
    with col3:
        categoria = st.selectbox("Categoria", ["Falda", "Vestido", "Pantalón", "Blusa", "Short"])
    with col4:
        talla = st.selectbox("Talla", ["XS", "S", "M", "L", "XL"])
    with col5:
        color = st.selectbox("Color", ["Verde", "Negro", "Blanco", "Rojo", "Azul"])

    st.markdown("---")

    # Bloque 3: Stock y Alertas
    col6, col7 = st.columns(2)
    with col6:
        cantidad = st.number_input("Cantidad", min_value=0, step=1)
    with col7:
        alerta_stock = st.number_input("Alerta de stock", min_value=0, step=1)

    st.markdown("")
    
    # Botón de guardado destacado
    submitted = st.form_submit_button("💾 Guardar Prenda", use_container_width=True)
    
    if submitted:
        if id_prenda and producto:
            st.success(f"¡Prenda {producto} registrada con éxito!")
        else:
            st.warning("Por favor completa al menos el ID y el nombre del producto.")
