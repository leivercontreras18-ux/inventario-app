import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Essence // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- DISEÑO UI ---
st.markdown(
    """
    <style>
    .stApp { background-color: #09090b; color: #fafafa !important; }
    section[data-testid="stSidebar"] { background-color: #121216 !important; border-right: 1px solid #27272a; }
    section[data-testid="stSidebar"] * { color: #f4f4f5 !important; }
    .hero-banner {
        background: linear-gradient(145deg, #18181b 0%, #09090b 100%);
        border: 1px solid #27272a; padding: 35px; border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); margin-bottom: 30px;
    }
    .hero-title { font-size: 34px; font-weight: 700; color: #ffffff !important; margin-bottom: 8px; }
    .hero-subtitle { font-size: 15px; color: #a1a1aa !important; }
    .metric-card {
        background: rgba(24, 24, 27, 0.7); border: 1px solid #27272a;
        padding: 24px; border-radius: 16px; text-align: center;
    }
    .metric-value { font-size: 36px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
    .metric-label { font-size: 11px; color: #71717a !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }
    .user-badge { background: #18181b; padding: 16px; border-radius: 16px; border: 1px solid #27272a; margin-bottom: 20px; }
    .user-status-title { font-size: 9px; color: #71717a; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 8px; }
    .user-content { display: flex; align-items: center; gap: 12px; }
    .status-dot { width: 10px; height: 10px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 12px #10b981; }
    .user-name { font-size: 18px; font-weight: 600; color: #fafafa; }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #121216 !important; color: #ffffff !important; border: 1px solid #27272a !important; border-radius: 10px !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #27272a 0%, #18181b 100%) !important; color: #f4f4f5 !important;
        font-weight: 600; border-radius: 10px; border: 1px solid #3f3f46 !important; padding: 10px 24px;
    }
    .stButton>button:hover { border-color: #d4af37 !important; color: #d4af37 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CONTROL DE ACCESO ---
USUARIOS = {"leiver": "natsudraghonil", "winderly": "coromoto"}

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if "usuario_actual" not in st.session_state:
  st.session_state.usuario_actual = ""

# Inicializar inventario local si no existe
if "inventario" not in st.session_state:
  st.session_state.inventario = pd.DataFrame(
      columns=[
          "ID",
          "Producto",
          "Categoria",
          "talla",
          "color",
          "cantidad",
          "alerta",
      ]
  )

if not st.session_state.autenticado:
  col1, col2, col3 = st.columns([1, 1.2, 1])
  with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
            <div style="background: #18181b; padding: 40px; border-radius: 20px; border: 1px solid #27272a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">👕</div>
                <h2 style="color: #ffffff; margin-bottom: 5px;">ESSENCE</h2>
                <p style="color: #a1a1aa; font-size: 12px; text-transform: uppercase; letter-spacing: 3px;">// PANEL DE ACCESO</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    usuario_input = st.text_input("Usuario")
    clave_input = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión", use_container_width=True):
      if (
          usuario_input in USUARIOS
          and USUARIOS[usuario_input] == clave_input
      ):
        st.session_state.autenticado = True
        st.session_state.usuario_actual = usuario_input
        st.rerun()
      else:
        st.error("Credenciales inválidas")
  st.stop()

else:
  usuario_formateado = st.session_state.usuario_actual.capitalize()
  st.sidebar.markdown(
      f"""
        <div class="user-badge">
            <div class="user-status-title">Estado en línea</div>
            <div class="user-content">
                <span class="status-dot"></span>
                <div class="user-name">{usuario_formateado}</div>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.rerun()

  df = st.session_state.inventario

  menu = st.sidebar.selectbox(
      "Navegación del Sistema",
      [
          "📊 Estado de Existencias",
          "➕ Registrar Prenda",
          "✏️ Modificar / Eliminar Prenda",
      ],
  )

  if menu == "📊 Estado de Existencias":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">👕 Panel Principal // Essence</div>
                <div class="hero-subtitle">Control general de stock y monitoreo en tiempo real.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if not df.empty:
      total_prendas = len(df)
      stock_total = (
          df["cantidad"].sum() if "cantidad" in df.columns else 0
      )

      col1, col2 = st.columns(2)
      with col1:
        st.markdown(
            f"""
                    <div class="metric-card">
                        <div class="metric-label">Modelos Registrados</div>
                        <div class="metric-value">{total_prendas}</div>
                    </div>
                """,
            unsafe_allow_html=True,
        )
      with col2:
        st.markdown(
            f"""
                    <div class="metric-card">
                        <div class="metric-label">Total en Stock</div>
                        <div class="metric-value">{stock_total}</div>
                    </div>
                """,
            unsafe_allow_html=True,
        )

      st.markdown("<br>", unsafe_allow_html=True)
      st.subheader("📋 Registro Actual de Inventario")
      st.dataframe(df, use_container_width=True)
    else:
      st.info("No hay prendas registradas todavía.")

  elif menu == "➕ Registrar Prenda":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">➕ Registro de Nuevas Prendas</div>
                <div class="hero-subtitle">Añade artículos al catálogo local.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_ropa"):
      sku = st.text_input("ID (Ej: A1)")
      nombre = st.text_input("Producto (Ej: Short)")
      categoria = st.selectbox(
          "Categoria",
          [
              "Vestidos",
              "Blusas",
              "Pantalones",
              "Jeans",
              "Chaquetas",
              "Calzado",
              "Accesorios",
          ],
      )
      talla = st.selectbox("talla", ["XS", "S", "M", "L", "XL", "Única"])
      color = st.text_input("color")
      cantidad = st.number_input("cantidad", min_value=0, step=1)
      alerta = st.number_input("alerta de stock", min_value=0, step=1)

      if st.form_submit_button("Guardar Prenda en el Sistema"):
        if sku.strip() == "":
          st.error("El campo ID es obligatorio.")
        else:
          nuevo_registro = pd.DataFrame([{
              "ID": sku,
              "Producto": nombre,
              "Categoria": categoria,
              "talla": talla,
              "color": color,
              "cantidad": cantidad,
              "alerta": alerta,
          }])
          st.session_state.inventario = pd.concat(
              [st.session_state.inventario, nuevo_registro], ignore_index=True
          )
          st.success("¡Prenda guardada con éxito!")
          st.rerun()

  elif menu == "✏️ Modificar / Eliminar Prenda":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">✏️ Modificar o Eliminar Prenda</div>
                <div class="hero-subtitle">Selecciona una prenda existente para actualizar sus datos o borrarla.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if not df.empty:
      lista_ids = df["ID"].astype(str).tolist()
      id_seleccionado = st.selectbox("Seleccione el ID de la prenda", lista_ids)

      fila_idx = df[df["ID"].astype(str) == id_seleccionado].index[0]
      prenda_actual = df.loc[fila_idx]

      with st.form("form_editar"):
        nuevo_id = st.text_input("ID", value=str(prenda_actual["ID"]))
        nuevo_nombre = st.text_input(
            "Producto", value=str(prenda_actual["Producto"])
        )
        nueva_categoria = st.text_input(
            "Categoria", value=str(prenda_actual["Categoria"])
        )
        nueva_talla = st.text_input("talla", value=str(prenda_actual["talla"]))
        nuevo_color = st.text_input("color", value=str(prenda_actual["color"]))
        nueva_cantidad = st.number_input(
            "cantidad", min_value=0, value=int(prenda_actual["cantidad"]), step=1
        )
        nueva_alerta = st.number_input(
            "alerta de stock",
            min_value=0,
            value=int(prenda_actual["alerta"]),
            step=1,
        )

        col_btn1, col_btn2 = st.columns(2)
        actualizar = col_btn1.form_submit_button(
            "💾 Guardar Cambios", use_container_width=True
        )
        eliminar = col_btn2.form_submit_button(
            "🗑️ Eliminar Prenda", use_container_width=True
        )

        if actualizar:
          st.session_state.inventario.loc[fila_idx, :] = [
              nuevo_id,
              nuevo_nombre,
              nueva_categoria,
              nueva_talla,
              nuevo_color,
              int(nueva_cantidad),
              int(nueva_alerta),
          ]
          st.success("¡Prenda actualizada correctamente!")
          st.rerun()

        if eliminar:
          st.session_state.inventario = (
              st.session_state.inventario.drop(fila_idx)
              .reset_index(drop=True)
          )
          st.success("¡Prenda eliminada del sistema!")
          st.rerun()
    else:
      st.info("No hay registros disponibles para modificar.")
