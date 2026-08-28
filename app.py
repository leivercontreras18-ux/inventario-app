import json
import uuid
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from github import Github
from supabase import create_client

try:
    import qrcode
    QR_DISPONIBLE = True
except ImportError:
    QR_DISPONIBLE = False

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="👕", layout="wide"
)

# =====================================================================================
# CONEXIONES
# =====================================================================================

@st.cache_resource
def obtener_conexion_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = obtener_conexion_supabase()

BUCKET_FOTOS = "productos-fotos"


@st.cache_data(ttl=60)
def cargar_config_github():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo("leivercontreras18-ux/inventario-app")
        file_content = repo.get_contents("config.json", ref="main")
        return json.loads(file_content.decoded_content.decode("utf-8"))
    except Exception:
        return None


# =====================================================================================
# CARGA DE DATOS
# =====================================================================================

COLUMNAS_INVENTARIO = [
    "ID", "Producto", "Categoria", "talla", "color", "cantidad", "alerta",
    "foto_url", "costo", "precio_venta", "favorito",
]

COLUMNAS_MOVIMIENTOS = [
    "id", "prenda_id", "producto", "tipo", "cantidad",
    "precio_unitario", "costo_unitario", "fecha", "usuario",
]


@st.cache_data(ttl=30)
def cargar_datos_completos():
    cats_default = ["Vestidos", "Blusas", "Pantalones", "Jeans", "Chaquetas", "Calzado", "Accesorios"]
    tallas_default = ["XS", "S", "M", "L", "XL", "Única"]
    colores_default = ["Negro", "Blanco", "Beige", "Rojo", "Azul", "Rosa", "Verde"]

    df = pd.DataFrame(columns=COLUMNAS_INVENTARIO)
    cats, tallas, colores = cats_default, tallas_default, colores_default

    if supabase:
        try:
            res_inv = supabase.table("inventario").select("*").execute()
            if res_inv.data:
                df = pd.DataFrame(res_inv.data)
                df = df.rename(columns={"id": "ID", "producto": "Producto", "categoria": "Categoria"})
        except Exception as e:
            st.warning(f"Aviso al cargar inventario de la nube: {e}")

    defaults_nuevos = {"foto_url": "", "costo": 0.0, "precio_venta": 0.0, "favorito": False}
    for col, default in defaults_nuevos.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    config_data = cargar_config_github()
    if config_data:
        cats = config_data.get("categorias", cats_default)
        tallas = config_data.get("tallas", tallas_default)
        colores = config_data.get("colores", colores_default)

    return df, cats, tallas, colores


@st.cache_data(ttl=20)
def cargar_movimientos():
    if not supabase:
        return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)
    try:
        res = supabase.table("movimientos").select("*").order("fecha", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.warning(f"No se pudieron cargar los movimientos: {e}")
    return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)


def registrar_movimiento(prenda_id, producto, tipo, cantidad, precio_unitario=0, costo_unitario=0):
    if not supabase:
        return False
    try:
        datos = {
            "id": str(uuid.uuid4()),
            "prenda_id": str(prenda_id),
            "producto": str(producto),
            "tipo": tipo,
            "cantidad": int(cantidad),
            "precio_unitario": float(precio_unitario or 0),
            "costo_unitario": float(costo_unitario or 0),
            "fecha": datetime.now().isoformat(),
            "usuario": st.session_state.get("usuario_actual", ""),
        }
        supabase.table("movimientos").insert(datos).execute()
        cargar_movimientos.clear()
        return True
    except Exception as e:
        st.error(f"Error al registrar el movimiento: {e}")
        return False


def guardar_configuracion_completa(cats, tallas, colores):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo("leivercontreras18-ux/inventario-app")
        config_data = {"categorias": cats, "tallas": tallas, "colores": colores}
        contenido = json.dumps(config_data, indent=4, ensure_ascii=False)
        try:
            file = repo.get_contents("config.json", ref="main")
            repo.update_file(file.path, "Actualización automática de configuración", contenido, file.sha, branch="main")
        except Exception:
            repo.create_file("config.json", "Creación inicial de configuración", contenido, branch="main")
        cargar_config_github.clear()
        cargar_datos_completos.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración en GitHub: {e}")
        return False


def subir_imagen(archivo, prenda_id):
    if not supabase or archivo is None:
        return None
    try:
        ext = archivo.name.split(".")[-1].lower()
        nombre_archivo = f"{prenda_id}_{uuid.uuid4().hex[:8]}.{ext}"
        contenido = archivo.read()
        supabase.storage.from_(BUCKET_FOTOS).upload(
            nombre_archivo, contenido, {"content-type": archivo.type}
        )
        return supabase.storage.from_(BUCKET_FOTOS).get_public_url(nombre_archivo)
    except Exception as e:
        st.warning(f"No se pudo subir la imagen: {e}")
        return None


def guardar_prenda(nueva_prenda):
    if supabase:
        try:
            datos_db = {
                "id": str(nueva_prenda["ID"]),
                "producto": str(nueva_prenda["Producto"]),
                "categoria": str(nueva_prenda["Categoria"]),
                "talla": str(nueva_prenda["talla"]),
                "color": str(nueva_prenda["color"]),
                "cantidad": int(nueva_prenda["cantidad"]),
                "alerta": int(nueva_prenda["alerta"]),
                "foto_url": str(nueva_prenda.get("foto_url", "") or ""),
                "costo": float(nueva_prenda.get("costo", 0) or 0),
                "precio_venta": float(nueva_prenda.get("precio_venta", 0) or 0),
                "favorito": bool(nueva_prenda.get("favorito", False)),
            }
            supabase.table("inventario").insert(datos_db).execute()
            cargar_datos_completos.clear()
            return True
        except Exception as e:
            st.error(f"Error al guardar en la nube: {e}")
            return False
    else:
        nuevo_df = pd.DataFrame([nueva_prenda])
        st.session_state.inventario_local = pd.concat(
            [st.session_state.inventario_local, nuevo_df], ignore_index=True
        )
        cargar_datos_completos.clear()
        return True


def actualizar_prenda(id_prenda, datos_actualizados):
    if supabase:
        try:
            datos_db = {
                "id": str(datos_actualizados["ID"]),
                "producto": str(datos_actualizados["Producto"]),
                "categoria": str(datos_actualizados["Categoria"]),
                "talla": str(datos_actualizados["talla"]),
                "color": str(datos_actualizados["color"]),
                "cantidad": int(datos_actualizados["cantidad"]),
                "alerta": int(datos_actualizados["alerta"]),
                "foto_url": str(datos_actualizados.get("foto_url", "") or ""),
                "costo": float(datos_actualizados.get("costo", 0) or 0),
                "precio_venta": float(datos_actualizados.get("precio_venta", 0) or 0),
                "favorito": bool(datos_actualizados.get("favorito", False)),
            }
            supabase.table("inventario").update(datos_db).match({"id": id_prenda}).execute()
            cargar_datos_completos.clear()
            return True
        except Exception as e:
            st.error(f"Error al actualizar: {e}")
            return False
    else:
        df = st.session_state.inventario_local
        idx = df[df["ID"].astype(str) == str(id_prenda)].index[0]
        for col, val in datos_actualizados.items():
            df.loc[idx, col] = val
        cargar_datos_completos.clear()
        return True


def eliminar_prenda(id_prenda):
    if supabase:
        try:
            supabase.table("inventario").delete().match({"id": id_prenda}).execute()
            cargar_datos_completos.clear()
            return True
        except Exception as e:
            st.error(f"Error al eliminar: {e}")
            return False
    else:
        df = st.session_state.inventario_local
        st.session_state.inventario_local = df[df["ID"].astype(str) != str(id_prenda)].reset_index(drop=True)
        cargar_datos_completos.clear()
        return True


# =====================================================================================
# UTILIDADES
# =====================================================================================

def moneda(valor):
    try:
        return f"${float(valor):,.2f}"
    except Exception:
        return "$0.00"


def generar_qr_bytes(texto):
    if not QR_DISPONIBLE:
        return None
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_copy_button(text_to_copy: str, label: str = "Copiar Código"):
    safe_text = text_to_copy.replace('"', '\\"').replace("'", "\\'")
    component_code = f"""
    <div style="background: transparent; font-family: sans-serif; padding: 0; margin: 0;">
        <button onclick="navigator.clipboard.writeText('{safe_text}'); this.innerText='¡Copiado!'; setTimeout(() => this.innerText='📋 {label}', 1500);" style="
            background: rgba(219, 39, 119, 0.12);
            color: #f472b6;
            border: 1px solid rgba(219, 39, 119, 0.35);
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.2s ease;
        ">📋 {label}</button>
    </div>
    """
    components.html(component_code, height=40)


# =====================================================================================
# ESTILOS
# =====================================================================================

def get_css(tema: str) -> str:
    if tema == "claro":
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.08) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.06) 0%, transparent 40%),
                           linear-gradient(135deg, #fdf2f8 0%, #ffffff 50%, #fdf4f9 100%);
            --text-color: #2b1f26;
            --text-secondary: #8a6b78;
            --accent: #db2777;
            --accent-light: #ec4899;
            --card-bg: rgba(255, 255, 255, 0.85);
            --border-color: rgba(219, 39, 119, 0.25);
            --sidebar-bg: rgba(255, 255, 255, 0.95);
            --input-bg: rgba(255, 255, 255, 0.9);
        """
    else:
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.12) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.08) 0%, transparent 40%),
                           linear-gradient(135deg, #0c0b0e 0%, #141117 50%, #100f13 100%);
            --text-color: #f9f6f8;
            --text-secondary: #b899a6;
            --accent: #f472b6;
            --accent-light: #f472b6;
            --card-bg: rgba(18, 16, 22, 0.9);
            --border-color: rgba(219, 39, 119, 0.25);
            --sidebar-bg: rgba(16, 15, 19, 0.95);
            --input-bg: rgba(24, 22, 28, 0.9);
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500;600;700&display=swap');

:root {{ {variables} }}

.stApp {{
    background: var(--bg-gradient);
    background-attachment: fixed;
    color: var(--text-color) !important;
    font-family: 'Montserrat', sans-serif !important;
}}

header[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ max-width: 100% !important; padding: 2rem !important; }}

section[data-testid="stSidebar"] {{
    width: 250px !important;
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
    backdrop-filter: blur(25px);
}}
section[data-testid="stSidebar"] * {{ color: var(--text-color) !important; }}

div[data-baseweb="input"], div[data-baseweb="select"] > div {{
    background-color: var(--input-bg) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-color) !important;
}}

div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
    background: var(--input-bg) !important;
    color: var(--text-color) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
    background: linear-gradient(135deg, #db2777 0%, #f472b6 100%) !important;
    border-color: #f472b6 !important;
    color: #ffffff !important;
    transform: translateY(-2px);
}}

div[data-testid="stForm"] {{
    background: var(--card-bg) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 20px !important;
    padding: 25px !important;
}}

.page-header {{ margin-bottom: 25px; padding-bottom: 10px; }}
.page-title {{ font-size: 32px; font-weight: 700; color: var(--text-color) !important; }}
.page-subtitle {{ font-size: 14px; color: var(--text-secondary) !important; margin-top: 4px; }}
.section-title {{ font-size: 18px; font-weight: 600; color: var(--text-color); margin-bottom: 4px; }}
.section-subtitle {{ font-size: 12px; color: var(--text-secondary); margin-bottom: 15px; }}

.metric-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    padding: 20px; border-radius: 18px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    height: 100%;
}}
.metric-value {{ font-size: 32px; font-weight: 800; color: var(--accent) !important; margin-top: 8px; }}
.metric-label {{ font-size: 11px; color: var(--text-secondary) !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }}

.user-profile {{
    background: rgba(219, 39, 119, 0.1); padding: 14px 16px; border-radius: 14px;
    border: 1px solid var(--border-color); margin-bottom: 20px;
    display: flex; align-items: center; gap: 12px;
}}
.user-avatar {{
    width: 36px; height: 36px; background: linear-gradient(135deg, #db2777 0%, #f472b6 100%); color: #ffffff;
    font-weight: 800; border-radius: 50%; display: flex; align-items: center; justify-content: center;
}}
.user-info-title {{ font-size: 9px; color: var(--accent); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }}
.user-info-name {{ font-size: 14px; font-weight: 600; color: var(--text-color); }}
.user-info-rol {{ font-size: 10px; color: var(--text-secondary); text-transform: capitalize; }}

.product-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    border-radius: 16px; margin-bottom: 8px; overflow: hidden;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}}
.product-card-body {{ padding: 16px; }}
.product-photo {{ width: 100%; height: 160px; object-fit: cover; display: block; }}
.product-photo-placeholder {{
    width: 100%; height: 160px; display: flex; align-items: center; justify-content: center;
    background: rgba(219, 39, 119, 0.08); font-size: 34px; color: var(--accent);
}}
.alert-banner {{
    background: rgba(244, 114, 182, 0.12); border: 1px solid var(--accent);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 20px; color: var(--text-color);
}}
</style>
"""


# =====================================================================================
# USUARIOS Y ESTADO
# =====================================================================================

USUARIOS = {
    "leiver": {"clave": "natsudraghonil", "rol": "administrador"},
    "winderly": {"clave": "coromoto", "rol": "vendedor"},
}

defaults_sesion = {
    "autenticado": False,
    "usuario_actual": "",
    "rol_actual": "",
    "etapa": "bienvenida",
    "tema": "oscuro",
    "form_version": 0,
    "menu_activo": "existencias",
}
for k, v in defaults_sesion.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "inventario_local" not in st.session_state:
    st.session_state.inventario_local = pd.DataFrame(columns=COLUMNAS_INVENTARIO)

st.markdown(get_css(st.session_state.tema), unsafe_allow_html=True)

df, cats_init, tallas_init, colores_init = cargar_datos_completos()

if "categorias_maestras" not in st.session_state:
    st.session_state.categorias_maestras = cats_init
if "tallas_maestras" not in st.session_state:
    st.session_state.tallas_maestras = tallas_init
if "colores_maestros" not in st.session_state:
    st.session_state.colores_maestros = colores_init
if "edit_cats" not in st.session_state:
    st.session_state.edit_cats = list(st.session_state.categorias_maestras)
if "edit_tallas" not in st.session_state:
    st.session_state.edit_tallas = list(st.session_state.tallas_maestras)
if "edit_colores" not in st.session_state:
    st.session_state.edit_colores = list(st.session_state.colores_maestros)

query_params = st.query_params
if not st.session_state.autenticado and "recuerdame_user" in query_params:
    saved_user = query_params["recuerdame_user"]
    if saved_user in USUARIOS:
        st.session_state.autenticado = True
        st.session_state.usuario_actual = saved_user
        st.session_state.rol_actual = USUARIOS[saved_user]["rol"]

ES_ADMIN = st.session_state.rol_actual == "administrador"

# =====================================================================================
# 1. BIENVENIDA
# =====================================================================================

if not st.session_state.autenticado and st.session_state.etapa == "bienvenida":
    st.markdown(
        """
        <style>
        .block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
        .full-hero-wrapper {
            background: var(--card-bg); backdrop-filter: blur(40px);
            border: 1px solid var(--border-color); border-radius: 32px; padding: 50px 70px; min-height: 85vh;
            display: flex; flex-direction: column; justify-content: space-between;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5); margin: 0 auto; max-width: 1450px;
        }
        .hero-title { font-family: 'Cinzel', serif; font-size: 52px; font-weight: 800; color: var(--text-color); margin-bottom: 16px; }
        </style>
        <div class="full-hero-wrapper">
            <div>
                <div style="font-family: 'Cinzel', serif; font-size: 15px; font-weight: 700; color: var(--text-color); letter-spacing: 2px; margin-bottom: 35px;">
                    ✦ LEWIN BOUTIQUE
                </div>
                <div style="font-size: 12px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px; font-weight: 700; margin-bottom: 20px;">Control Center</div>
                <h1 class="hero-title">Lewin Boutique<br>Inventario y Ventas</h1>
                <p style="color: var(--text-secondary); font-size: 15px; line-height: 1.6; max-width: 650px; margin-bottom: 35px;">
                    Plataforma de gestión de stock, ventas y reportes con una interfaz de lujo.
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("INICIO", use_container_width=True):
        st.session_state.etapa = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================================
# 2. LOGIN
# =====================================================================================

elif not st.session_state.autenticado and st.session_state.etapa == "login":
    if st.button("← Volver"):
        st.session_state.etapa = "bienvenida"
        st.rerun()

    _, col_centro, _ = st.columns([1, 1.4, 1])
    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h3>✦ Lewin Boutique Access</h3>", unsafe_allow_html=True)
            usuario_input = st.text_input("Usuario", placeholder="Ingrese su usuario")
            clave_input = st.text_input("Contraseña", type="password", placeholder="Contraseña")
            remember_checked = st.checkbox("Recordarme")

            if st.button("Log in 🚪", use_container_width=True):
                user_clean = usuario_input.strip().lower()
                pass_clean = clave_input.strip()

                if user_clean in USUARIOS and USUARIOS[user_clean]["clave"] == pass_clean:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = user_clean
                    st.session_state.rol_actual = USUARIOS[user_clean]["rol"]
                    if remember_checked:
                        st.query_params["recuerdame_user"] = user_clean
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos.")
    st.stop()

# =====================================================================================
# 3. PANEL PRINCIPAL
# =====================================================================================

else:
    usuario_formateado = st.session_state.usuario_actual.capitalize()
    inicial_usuario = usuario_formateado[0]
    rol_formateado = st.session_state.rol_actual.capitalize()

    st.sidebar.markdown(
        f"""
<div class="user-profile">
    <div class="user-avatar">{inicial_usuario}</div>
    <div>
        <div class="user-info-title">● Sesión Activa</div>
        <div class="user-info-name">{usuario_formateado}</div>
        <div class="user-info-rol">{rol_formateado}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    tema_claro = st.sidebar.toggle("☀️ Modo claro", value=(st.session_state.tema == "claro"))
    nuevo_tema = "claro" if tema_claro else "oscuro"
    if nuevo_tema != st.session_state.tema:
        st.session_state.tema = nuevo_tema
        st.rerun()

    st.sidebar.markdown("<p style='font-size:10px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:1.5px; font-weight:700; margin: 12px 0 6px 4px;'>Menú Principal</p>", unsafe_allow_html=True)

    opciones_menu = [("existencias", "📊 Existencias"), ("vender", "💳 Vender"), ("comprar", "📦 Registrar Compra")]
    if ES_ADMIN:
        opciones_menu.extend([("registrar", "➕ Registrar Prenda"), ("modificar", "✏️ Editar / Borrar")])
    opciones_menu.append(("movimientos", "📜 Movimientos"))
    opciones_menu.append(("reportes", "📈 Reportes"))
    if ES_ADMIN:
        opciones_menu.append(("configuracion", "⚙️ Configuración"))

    for clave, etiqueta in opciones_menu:
        if st.sidebar.button(etiqueta, use_container_width=True, key=f"menu_{clave}"):
            st.session_state.menu_activo = clave
            st.rerun()

    st.sidebar.markdown("<hr style='margin: 25px 0 15px 0; border-color: var(--border-color);'>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.session_state.etapa = "bienvenida"
        if "recuerdame_user" in st.query_params:
            del st.query_params["recuerdame_user"]
        st.rerun()

    menu = st.session_state.get("menu_activo", "existencias")
    if menu in ("registrar", "modificar", "configuracion") and not ES_ADMIN:
        menu = "existencias"

    # -----------------------------------------------------------------------------
    # EXISTENCIAS
    # -----------------------------------------------------------------------------
    if menu == "existencias":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">Panel Principal // Lewin Boutique</div>
    <div class="page-subtitle">Control general de stock y monitoreo en tiempo real.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        total_prendas = len(df) if not df.empty else 0
        stock_total = int(df["cantidad"].sum()) if not df.empty and "cantidad" in df.columns else 0
        total_alertas = 0
        prendas_alerta = pd.DataFrame()
        if not df.empty and "cantidad" in df.columns and "alerta" in df.columns:
            prendas_alerta = df[df["cantidad"] <= df["alerta"]]
            total_alertas = int(prendas_alerta.shape[0])

        valor_inventario = float((df["cantidad"] * df["precio_venta"]).sum()) if not df.empty else 0.0

        col1, col2, col3, col4 = st.columns(4)
        for col, label, value in [
            (col1, "Total Modelos", total_prendas),
            (col2, "Stock Total", stock_total),
            (col3, "Alertas Stock", total_alertas),
            (col4, "Valor (Venta)", moneda(valor_inventario)),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            st.markdown("<div class='section-title'>⚡ Ajuste Rápido de Stock</div>", unsafe_allow_html=True)
            col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
            with col_q1:
                id_rapido = st.selectbox("Seleccionar Prenda", df["ID"].astype(str).tolist(), key="select_ajuste_rapido")
            with col_q2:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➖ Quitar 1 (-1)", use_container_width=True, key="btn_minus_1"):
                    fila = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = max(0, int(fila["cantidad"]) - 1)
                    datos_act = fila.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.rerun()
            with col_q3:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Añadir 1 (+1)", use_container_width=True, key="btn_plus_1"):
                    fila = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = int(fila["cantidad"]) + 1
                    datos_act = fila.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>📋 Catálogo y Filtros</div>", unsafe_allow_html=True)

            col_f1, col_f2, col_f3 = st.columns([1.5, 1, 1])
            with col_f1:
                busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o ID...")
            with col_f2:
                filtro_categoria = st.selectbox("📂 Categoría", ["Todas"] + sorted(list(df["Categoria"].dropna().unique())))
            with col_f3:
                filtro_talla = st.selectbox("📏 Talla", ["Todas"] + sorted(list(df["talla"].dropna().unique())))

            df_filtrado = df.copy()
            if busqueda.strip():
                q = busqueda.strip().lower()
                df_filtrado = df_filtrado[df_filtrado["ID"].astype(str).str.lower().str.contains(q) | df_filtrado["Producto"].astype(str).str.lower().str.contains(q)]
            if filtro_categoria != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Categoria"] == filtro_categoria]
            if filtro_talla != "Todas":
                df_filtrado = df_filtrado[df_filtrado["talla"] == filtro_talla]

            total_registros = len(df_filtrado)
            if total_registros > 0:
                cols_tarjetas = st.columns(3)
                for idx, (_, row) in enumerate(df_filtrado.iterrows()):
                    col_actual = cols_tarjetas[idx % 3]
                    is_alerta = int(row["cantidad"]) <= int(row["alerta"])
                    borde_color = "var(--accent)" if is_alerta else "var(--border-color)"
                    badge_stock = f"<span style='color: {'#f472b6' if is_alerta else '#34d399'}; font-weight: 700;'>Stock: {row['cantidad']}</span>"
                    estrella = "⭐" if bool(row.get("favorito", False)) else "☆"
                    
                    foto_html = f'<img class="product-photo" src="{row["foto_url"]}" />' if row.get("foto_url") else '<div class="product-photo-placeholder">👕</div>'
                    precio_html = f"<div style='margin-top:6px; font-size:14px; font-weight:700; color: var(--accent);'>{moneda(row.get('precio_venta', 0))}</div>" if float(row.get("precio_venta", 0) or 0) > 0 else ""

                    with col_actual:
                        st.markdown(
                            f"""
                            <div class="product-card" style="border-color: {borde_color};">
                                {foto_html}
                                <div class="product-card-body">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <span style="background: rgba(219, 39, 119, 0.15); color: var(--accent); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">ID: {row['ID']}</span>
                                        <span style="font-size: 12px; color: var(--text-secondary);">{row['Categoria']}</span>
                                    </div>
                                    <div style="font-size: 16px; font-weight: 700; color: var(--text-color); margin-bottom: 8px;">{estrella} {row['Producto']}</div>
                                    <div style="font-size: 13px; color: var(--text-secondary); display: flex; gap: 12px; margin-bottom: 8px;">
                                        <span>📏 <b>{row['talla']}</b></span>
                                        <span>🎨 <b>{row['color']}</b></span>
                                    </div>
                                    {precio_html}
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 10px; font-size: 13px;">
                                        {badge_stock}
                                        <span style="font-size: 11px; color: var(--text-secondary);">Mín: {row['alerta']}</span>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        c_fav, c_qr = st.columns(2)
                        with c_fav:
                            if st.button("⭐ Favorito" if not row.get("favorito", False) else "☆ Quitar", key=f"fav_{row['ID']}", use_container_width=True):
                                datos_act = row.to_dict()
                                datos_act["favorito"] = not bool(row.get("favorito", False))
                                if actualizar_prenda(row["ID"], datos_act):
                                    st.rerun()
                        with c_qr:
                            with st.popover("🔗 QR", use_container_width=True) if hasattr(st, "popover") else st.expander("🔗 QR"):
                                if QR_DISPONIBLE:
                                    st.image(generar_qr_bytes(f"ID:{row['ID']} | {row['Producto']}"), width=140)

                        render_copy_button(f"ID: {row['ID']} - {row['Producto']} ({row['Categoria']}) Talla: {row['talla']} Stock: {row['cantidad']}", label="Copiar")
                        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
            else:
                st.info("No se encontraron registros.")
        else:
            st.info("No hay prendas registradas.")

    # -----------------------------------------------------------------------------
    # VENDER
    # -----------------------------------------------------------------------------
    elif menu == "vender":
        st.markdown("<div class='page-header'><div class='page-title'>💳 Registrar Venta</div></div>", unsafe_allow_html=True)
        if df.empty:
            st.info("No hay prendas.")
        else:
            with st.form("form_vender"):
                id_venta = st.selectbox("Prenda", df["ID"].astype(str).tolist(), format_func=lambda x: f"{x} — {df[df['ID'].astype(str) == x]['Producto'].values[0]}")
                fila = df[df["ID"].astype(str) == str(id_venta)].iloc[0]
                st.markdown(f"**Stock disponible:** {int(fila['cantidad'])}")

                c1, c2 = st.columns(2)
                with c1:
                    cant = st.number_input("Cantidad", min_value=1, max_value=max(1, int(fila["cantidad"])), value=1)
                with c2:
                    precio = st.number_input("Precio unitario", min_value=0.0, value=float(fila.get("precio_venta", 0) or 0))

                if st.form_submit_button("💰 Confirmar Venta", use_container_width=True):
                    if int(fila["cantidad"]) < cant:
                        st.error("Stock insuficiente.")
                    else:
                        datos_act = fila.to_dict()
                        datos_act["cantidad"] = int(fila["cantidad"]) - int(cant)
                        if actualizar_prenda(id_venta, datos_act):
                            registrar_movimiento(id_venta, fila["Producto"], "venta", cant, precio, fila.get("costo", 0))
                            st.success("¡Venta registrada!")
                            st.rerun()

    # -----------------------------------------------------------------------------
    # COMPRAR
    # -----------------------------------------------------------------------------
    elif menu == "comprar":
        st.markdown("<div class='page-header'><div class='page-title'>📦 Registrar Compra</div></div>", unsafe_allow_html=True)
        if df.empty:
            st.info("No hay prendas.")
        else:
            with st.form("form_comprar"):
                id_compra = st.selectbox("Prenda", df["ID"].astype(str).tolist(), format_func=lambda x: f"{x} — {df[df['ID'].astype(str) == x]['Producto'].values[0]}")
                fila = df[df["ID"].astype(str) == str(id_compra)].iloc[0]

                c1, c2 = st.columns(2)
                with c1:
                    cant = st.number_input("Cantidad", min_value=1, value=1)
                with c2:
                    costo = st.number_input("Costo unitario", min_value=0.0, value=float(fila.get("costo", 0) or 0))

                if st.form_submit_button("📦 Confirmar Compra", use_container_width=True):
                    datos_act = fila.to_dict()
                    datos_act["cantidad"] = int(fila["cantidad"]) + int(cant)
                    datos_act["costo"] = costo
                    if actualizar_prenda(id_compra, datos_act):
                        registrar_movimiento(id_compra, fila["Producto"], "compra", cant, 0, costo)
                        st.success("¡Compra registrada!")
                        st.rerun()

    # -----------------------------------------------------------------------------
    # REGISTRAR
    # -----------------------------------------------------------------------------
    elif menu == "registrar":
        st.markdown("<div class='page-header'><div class='page-title'>➕ Registrar Prenda</div></div>", unsafe_allow_html=True)
        with st.form(f"form_reg_{st.session_state.form_version}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: sku = st.text_input("ID")
            with c2: nombre = st.text_input("Producto")

            c3, c4, c5 = st.columns(3)
            with c3: cat = st.selectbox("Categoría", st.session_state.categorias_maestras)
            with c4: talla = st.selectbox("Talla", st.session_state.tallas_maestras)
            with c5: color = st.selectbox("Color", st.session_state.colores_maestros)

            c6, c7 = st.columns(2)
            with c6: cant = st.number_input("Cantidad", min_value=0, value=0)
            with c7: alerta = st.number_input("Alerta stock", min_value=0, value=0)

            c8, c9 = st.columns(2)
            with c8: costo = st.number_input("Costo", min_value=0.0, value=0.0)
            with c9: precio = st.number_input("Precio venta", min_value=0.0, value=0.0)

            foto = st.file_uploader("Foto", type=["png", "jpg", "jpeg", "webp"])

            if st.form_submit_button("💾 Guardar Prenda", use_container_width=True):
                if not sku.strip():
                    st.error("El ID es obligatorio.")
                else:
                    foto_url = subir_imagen(foto, sku.strip()) if foto else ""
                    nueva = {
                        "ID": sku.strip(), "Producto": nombre.strip(), "Categoria": cat,
                        "talla": talla, "color": color, "cantidad": cant, "alerta": alerta,
                        "costo": costo, "precio_venta": precio, "foto_url": foto_url or "", "favorito": False
                    }
                    if guardar_prenda(nueva):
                        st.success("¡Guardado!")
                        st.session_state.form_version += 1
                        st.rerun()

    # -----------------------------------------------------------------------------
    # MODIFICAR
    # -----------------------------------------------------------------------------
    elif menu == "modificar":
        st.markdown("<div class='page-header'><div class='page-title'>✏️ Modificar o Eliminar</div></div>", unsafe_allow_html=True)
        if not df.empty:
            id_sel = st.selectbox("Seleccione ID", df["ID"].astype(str).tolist())
            fila = df[df["ID"].astype(str) == str(id_sel)].iloc[0]

            if fila.get("foto_url"):
                st.image(fila["foto_url"], width=150)

            with st.form("form_edit"):
                n_id = st.text_input("ID", value=str(fila["ID"]))
                n_nom = st.text_input("Producto", value=str(fila["Producto"]))
                n_cat = st.selectbox("Categoría", st.session_state.categorias_maestras, index=st.session_state.categorias_maestras.index(fila["Categoria"]) if fila["Categoria"] in st.session_state.categorias_maestras else 0)
                n_talla = st.selectbox("Talla", st.session_state.tallas_maestras, index=st.session_state.tallas_maestras.index(fila["talla"]) if fila["talla"] in st.session_state.tallas_maestras else 0)
                n_color = st.selectbox("Color", st.session_state.colores_maestros, index=st.session_state.colores_maestros.index(fila["color"]) if fila["color"] in st.session_state.colores_maestros else 0)
                n_cant = st.number_input("Cantidad", min_value=0, value=int(fila["cantidad"]))
                n_alerta = st.number_input("Alerta", min_value=0, value=int(fila["alerta"]))
                n_costo = st.number_input("Costo", min_value=0.0, value=float(fila.get("costo", 0) or 0))
                n_precio = st.number_input("Precio venta", min_value=0.0, value=float(fila.get("precio_venta", 0) or 0))
                nueva_foto = st.file_uploader("Nueva foto", type=["png", "jpg", "jpeg", "webp"])

                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Guardar", use_container_width=True):
                    f_url = fila.get("foto_url", "")
                    if nueva_foto:
                        subida = subir_imagen(nueva_foto, n_id)
                        if subida: f_url = subida
                    datos_mod = {
                        "ID": n_id, "Producto": n_nom, "Categoria": n_cat, "talla": n_talla,
                        "color": n_color, "cantidad": n_cant, "alerta": n_alerta, "costo": n_costo,
                        "precio_venta": n_precio, "foto_url": f_url, "favorito": bool(fila.get("favorito", False))
                    }
                    if actualizar_prenda(id_sel, datos_mod):
                        st.success("¡Actualizado!")
                        st.rerun()
                if c2.form_submit_button("🗑️ Eliminar", use_container_width=True):
                    if eliminar_prenda(id_sel):
                        st.success("¡Eliminado!")
                        st.rerun()

    # -----------------------------------------------------------------------------
    # MOVIMIENTOS
    # -----------------------------------------------------------------------------
    elif menu == "movimientos":
        st.markdown("<div class='page-header'><div class='page-title'>📜 Movimientos</div></div>", unsafe_allow_html=True)
        movs = cargar_movimientos()
        if movs.empty:
            st.info("Sin movimientos.")
        else:
            st.dataframe(movs, use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------------
    # REPORTES
    # -----------------------------------------------------------------------------
    elif menu == "reportes":
        st.markdown("<div class='page-header'><div class='page-title'>📈 Reportes</div></div>", unsafe_allow_html=True)
        movs = cargar_movimientos()
        ventas = movs[movs["tipo"] == "venta"].copy() if not movs.empty else pd.DataFrame()
        total_v = float((ventas["cantidad"] * ventas["precio_unitario"]).sum()) if not ventas.empty else 0.0
        total_c = float((ventas["cantidad"] * ventas["costo_unitario"]).sum()) if not ventas.empty else 0.0
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">Ventas</div><div class="metric-value">{moneda(total_v)}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="metric-card"><div class="metric-label">Ganancia</div><div class="metric-value">{moneda(total_v - total_c)}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">Inventario (Venta)</div><div class="metric-value">{moneda(float((df['cantidad'] * df['precio_venta']).sum())) if not df.empty else '$0'}</div></div>""", unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # CONFIGURACIÓN
    # -----------------------------------------------------------------------------
    elif menu == "configuracion":
        st.markdown("<div class='page-header'><div class='page-title'>⚙️ Configuración</div></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown("**Categorías**")
                for cat in list(st.session_state.edit_cats):
                    sc1, sc2 = st.columns([3, 1])
                    sc1.markdown(cat)
                    if sc2.button("❌", key=f"dc_{cat}") and len(st.session_state.edit_cats) > 1:
                        st.session_state.edit_cats.remove(cat)
                        st.rerun()
                nueva_c = st.text_input("Nueva Categoría", key="nc")
                if st.button("Agregar Cat"):
                    if nueva_c.strip() and nueva_c.strip().capitalize() not in st.session_state.edit_cats:
                        st.session_state.edit_cats.append(nueva_c.strip().capitalize())
                        st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("**Tallas**")
                for t in list(st.session_state.edit_tallas):
                    st1, st2 = st.columns([3, 1])
                    st1.markdown(t)
                    if st2.button("❌", key=f"dt_{t}") and len(st.session_state.edit_tallas) > 1:
                        st.session_state.edit_tallas.remove(t)
                        st.rerun()
                nueva_t = st.text_input("Nueva Talla", key="nt")
                if st.button("Agregar Talla"):
                    if nueva_t.strip() and nueva_t.strip().upper() not in st.session_state.edit_tallas:
                        st.session_state.edit_tallas.append(nueva_t.strip().upper())
                        st.rerun()
        with c3:
            with st.container(border=True):
                st.markdown("**Colores**")
                for col in list(st.session_state.edit_colores):
                    cc1, cc2 = st.columns([3, 1])
                    cc1.markdown(col)
                    if cc2.button("❌", key=f"dcol_{col}") and len(st.session_state.edit_colores) > 1:
                        st.session_state.edit_colores.remove(col)
                        st.rerun()
                nuevo_col = st.text_input("Nuevo Color", key="nco")
                if st.button("Agregar Color"):
                    if nuevo_col.strip() and nuevo_col.strip().capitalize() not in st.session_state.edit_colores:
                        st.session_state.edit_colores.append(nuevo_col.strip().capitalize())
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Guardar configuración en GitHub", use_container_width=True):
            if guardar_configuracion_completa(st.session_state.edit_cats, st.session_state.edit_tallas, st.session_state.edit_colores):
                st.success("¡Guardado en GitHub!")
                st.rerun()
