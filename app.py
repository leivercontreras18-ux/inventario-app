import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
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
    
    /* Barra lateral estilizada */
    section[data-testid="stSidebar"] {
        background-color: #121216 !important;
        border-right: 1px solid #27272a;
    }
    section[data-testid="stSidebar"] * {
        color: #f4f4f5 !important;
    }
    
    /* Banner principal elegante */
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
    
    /* Tarjetas de métricas tipo vidrio oscuro */
    .metric-card {
        background: rgba(24, 24, 27, 0.7);
        border: 1px solid #27272a;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #d4af37;
        transform: translateY(-2px);
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
    
    /* Insignia de usuario */
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
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 18px;
        font-weight: 600;
        color: #fafafa;
        letter-spacing: 0.5px;
    }
    
    /* Campos de formularios modernos */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: #121216 !important;
        color: #ffffff !important;
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        padding: 10px 14px;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 0 1px #d4af37 !important;
    }
    
    /* Botones sofisticados */
    .stButton>button {
        background: linear-gradient(135deg, #27272a 0%, #18181b 100%) !important;
        color: #f4f4f5 !important;
        font-weight: 600;
        border-radius: 10px;
        border: 1px solid #3f3f46 !important;
        padding: 10px 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
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
            <div style="background: #18181b; padding: 40px; border-radius: 20px; border: 1px solid #27272a; box-shadow: 0 20px 40px rgba(0,0,0,0.5); text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">👕</div>
                <h2 style="color: #ffffff; margin-bottom: 5px; letter-spacing: -0.5px;">ESSENCE</h2>
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
    # Lee directamente el diccionario general de los secretos configurados
    credentials_dict = dict(st.secrets)
    creds = Credentials.from_service_account_info(
        credentials_dict, scopes=scopes
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
        ["📊 Estado de Existencias", "➕ Registrar Prenda"],
    )

    if menu == "📊 Estado de Existencias":
        st.markdown(
            """
            <div class="hero-banner">
                <div class="hero-title">👕 Panel Principal // Essence</div>
                <div class="hero-subtitle">Control general de stock y monitoreo de inventario de prendas en tiempo real.</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if not df.empty:
            total_prendas = len(df)
            stock_total = (
                df["Cantidad"].sum() if "Cantidad" in df.columns else 0
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

            # Alertas de Stock Mínimo
            if "Cantidad" in df.columns and "Minimo" in df.columns:
                stock_bajo = df[df["Cantidad"] <= df["Minimo"]]
                if not stock_bajo.empty:
                    st.warning(
                        f"⚠️ Atención: Hay {len(stock_bajo)} modelo(s) con stock por debajo del mínimo recomendado."
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📋 Registro Actual de Inventario")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay prendas registradas todavía en la base de datos.")

    elif menu == "➕ Registrar Prenda":
        st.markdown(
            """
            <div class="hero-banner">
                <div class="hero-title">➕ Registro de Nuevas Prendas</div>
                <div class="hero-subtitle">Añade artículos al catálogo sincronizado de la tienda.</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("form_ropa"):
            sku = st.text_input("SKU / Código (Ej: CAM-001)")
            nombre = st.text_input(
                "Nombre / Descripción (Ej: Vestido Lino)"
            )
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
            talla = st.selectbox(
                "Talla", ["XS", "S", "M", "L", "XL", "Única"]
            )
            color = st.text_input("Color Principal")
            cantidad = st.number_input(
                "Cantidad Disponible", min_value=0, step=1
            )
            minimo = st.number_input(
                "Alerta de Stock Mínimo", min_value=0, step=1
            )

            if st.form_submit_button("Guardar Prenda en el Sistema"):
                sheet.append_row(
                    [sku, nombre, categoria, talla, color, cantidad, minimo]
                )
                st.success("¡Prenda guardada con éxito!")
                st.rerun()

except Exception as e:
    st.error(f"Error al sincronizar con Google Sheets: {e}")
