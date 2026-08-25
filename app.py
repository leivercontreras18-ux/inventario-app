import json
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Essence // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- DISEÑO UI: BOUTIQUE MINIMALISTA Y LUJO OSCURO ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #09090b;
        color: #fafafa !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #121216 !important;
        border-right: 1px solid #27272a;
    }
    section[data-testid="stSidebar"] * {
        color: #f4f4f5 !important;
    }
    .hero-banner {
        background: linear-gradient(145deg, #18181b 0%, #09090b 100%);
        border: 1px solid #27272a;
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 150px;
        height: 100%;
        background: radial-gradient(circle, rgba(212,175,55,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 34px;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 15px;
        color: #a1a1aa !important;
    }
    .metric-card {
        background: rgba(24, 24, 27, 0.7);
        border: 1px solid #27272a;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 800;
        color: #d4af37 !important;
        margin-top: 8px;
    }
    .metric-label {
        font-size: 11px;
        color: #71717a !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
    }
    .user-badge {
        background: #18181b;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid #27272a;
        margin-bottom: 20px;
    }
    .user-status-title {
        font-size: 9px;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .user-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 12px #10b981;
        flex-shrink: 0;
    }
    .user-name {
        font-size: 18px;
        font-weight: 600;
        color: #fafafa;
    }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #121216 !important;
        color: #ffffff !important;
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        padding: 10px 14px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #27272a 0%, #18181b 100%) !important;
        color: #f4f4f5 !important;
        font-weight: 600;
        border-radius: 10px;
        border: 1px solid #3f3f46 !important;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        border-color: #d4af37 !important;
        color: #d4af37 !important;
    }
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

  # --- CONEXIÓN A GOOGLE SHEETS ---
  def cargar_datos():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    url = "https://docs.google.com/spreadsheets/d/1vMUgfp5eP7yOAoXMBCjp4XjpLvkoUz71vDp5RSDhOOI/edit?gid=0#gid=0"
    sheet = client.open_by_url(url).sheet1
    data = sheet.get_all_records()
    return sheet, pd.DataFrame(data)

  try:
    sheet, df = cargar_datos()

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
                  <div class="hero-subtitle">Control general de stock y monitoreo de inventario en tiempo real.</div>
              </div>
          """,
          unsafe_allow_html=True,
      )

      if not df.empty:
        total_prendas = len(df)
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
                  <div class="hero-subtitle">Añade artículos al catálogo sincronizado.</div>
              </div>
          """,
          unsafe_allow_html=True,
      )

      with st.form("form_ropa"):
        sku = st.text_input("ID / SKU (Ej: A1)")
        nombre = st.text_input("Producto / Descripción (Ej: Short)")
        categoria = st.selectbox(
            "Categoría",
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
        talla = st.selectbox("Talla", ["XS", "S", "M", "L", "XL", "Única"])
        color = st.text_input("Color Principal")
        cantidad = st.number_input("Cantidad Disponible", min_value=0, step=1)

        if st.form_submit_button("Guardar Prenda en el Sistema"):
          sheet.append_row([sku, nombre, categoria, talla, color, cantidad])
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
        # Detectamos automáticamente el nombre de la primera columna para usarla como ID
        col_id = df.columns[0]
        lista_ids = df[col_id].astype(str).tolist()
        id_seleccionado = st.selectbox(
            "Seleccione el identificador de la prenda", lista_ids
        )

        fila_idx = df[df[col_id].astype(str) == id_seleccionado].index[0]
        row_number = fila_idx + 2  # Fila en Sheets (salta cabecera)
        prenda_actual = df.loc[fila_idx]

        with st.form("form_editar"):
          # Campos dinámicos basados en tus columnas actuales
          nuevos_valores = []
          for col in df.columns:
            val_actual = prenda_actual[col]
            nuevo_val = st.text_input(
                f"Modificar [{col}]", value=str(val_actual)
            )
            nuevos_valores.append(nuevo_val)

          col_btn1, col_btn2 = st.columns(2)
          actualizar = col_btn1.form_submit_button(
              "💾 Guardar Cambios", use_container_width=True
          )
          eliminar = col_btn2.form_submit_button(
              "🗑️ Eliminar Prenda", use_container_width=True
          )

          if actualizar:
            letra_final = chr(65 + len(df.columns) - 1)
            sheet.update(f"A{row_number}:{letra_final}{row_number}", [nuevos_valores])
            st.success("¡Prenda actualizada correctamente!")
            st.rerun()

          if eliminar:
            sheet.delete_rows(row_number)
            st.success("¡Prenda eliminada del sistema!")
            st.rerun()
      else:
        st.info("No hay registros disponibles para modificar.")

  except Exception as e:
    st.error(f"Error al sincronizar con Google Sheets: {e}")
