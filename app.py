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

    # Asegurar que existan las columnas nuevas aunque la tabla aún no las tenga
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
        st.warning("No hay conexión a la base de datos para registrar el movimiento.")
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
            repo.update_file(file.path, "Actualización automática de configuración de inventario",
                              contenido, file.sha, branch="main")
        except Exception:
            repo.create_file("config.json", "Creación inicial de configuración de inventario",
                              contenido, branch="main")
        cargar_config_github.clear()
        cargar_datos_completos.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración en GitHub: {e}")
        return False


def subir_imagen(archivo, prenda_id):
    """Sube una foto al bucket de Supabase Storage y devuelve la URL pública."""
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
        st.warning(f"No se pudo subir la imagen (revisa que exista el bucket '{BUCKET_FOTOS}'): {e}")
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
    component_code = f"""
    <div style="display: inline-block; width: 100%;">
        <button id="copy-btn" onclick="copyText()" style="
            background: rgba(219, 39, 119, 0.12);
            color: #f472b6;
            border: 1px solid rgba(219, 39, 119, 0.35);
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            width: 100%;
            transition: all 0.2s ease;
        ">
            📋 {label}
        </button>
        <div id="feedback" style="text-align: center; font-size: 11px; color: #f472b6; opacity: 0; transition: opacity 0.3s; margin-top: 4px;">¡Copiado con éxito!</div>
    </div>
    <script>
    function copyText() {{
        navigator.clipboard.writeText(`{text_to_copy}`).then(function() {{
            var feedback = document.getElementById('feedback');
            feedback.style.opacity = '1';
            setTimeout(function() {{ feedback.style.opacity = '0'; }}, 1500);
        }}).catch(function(err) {{ console.error('Error al copiar: ', err); }});
    }}
    </script>
    """
    components.html(component_code, height=65)


# =====================================================================================
# ESTILOS (con soporte de tema claro / oscuro mediante variables CSS)
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

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

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
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px rgba(219, 39, 119, 0.3) !important;
}}
div[data-baseweb="input"] input {{ color: var(--text-color) !important; font-size: 13px !important; }}

div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
    background: var(--input-bg) !important;
    color: var(--text-color) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
    display: flex; justify-content: center; align-items: center;
    width: 100% !important;
}}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
    background: linear-gradient(135deg, #db2777 0%, #f472b6 100%) !important;
    border-color: #f472b6 !important;
    color: #ffffff !important;
    box-shadow: 0 8px 25px rgba(219, 39, 119, 0.4) !important;
    transform: translateY(-2px);
}}

div[data-testid="stForm"] {{
    background: var(--card-bg) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 20px !important;
    padding: 25px !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25) !important;
}}

.page-header {{ margin-bottom: 25px; padding-bottom: 10px; }}
.page-title {{ font-size: 32px; font-weight: 700; color: var(--text-color) !important; letter-spacing: 0.5px; }}
.page-subtitle {{ font-size: 14px; color: var(--text-secondary) !important; margin-top: 4px; }}

.section-title {{ font-size: 18px; font-weight: 600; color: var(--text-color); margin-bottom: 4px; }}
.section-subtitle {{ font-size: 12px; color: var(--text-secondary); margin-bottom: 15px; }}

.metric-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    padding: 20px; border-radius: 18px; text-align: left;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
    height: 100%; animation: fadeInUp 0.4s ease;
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
    font-weight: 800; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 15px; box-shadow: 0 0 15px rgba(219, 39, 119, 0.5);
}}
.user-info-title {{ font-size: 9px; color: var(--accent); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }}
.user-info-name {{ font-size: 14px; font-weight: 600; color: var(--text-color); }}
.user-info-rol {{ font-size: 10px; color: var(--text-secondary); text-transform: capitalize; }}

.product-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    padding: 0; border-radius: 16px; margin-bottom: 8px; overflow: hidden;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    animation: fadeInUp 0.35s ease;
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
# USUARIOS Y ROLES
# =====================================================================================

USUARIOS = {
    "leiver": {"clave": "natsudraghonil", "rol": "administrador"},
    "winderly": {"clave": "coromoto", "rol": "vendedor"},
}

# =====================================================================================
# ESTADO DE SESIÓN
# =====================================================================================

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
# 1. PANTALLA DE BIENVENIDA
# =====================================================================================

if not st.session_state.autenticado and st.session_state.etapa == "bienvenida":
    st.markdown(
        """
        <style>
        .block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
        .full-hero-wrapper {
            background: var(--card-bg); backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
            border: 1px solid var(--border-color); border-radius: 32px; padding: 50px 70px; min-height: 85vh;
            display: flex; flex-direction: column; justify-content: space-between; position: relative;
            overflow: hidden; box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.08);
            margin: 0 auto; max-width: 1450px;
        }
        .hero-inner { position: relative; z-index: 1; }
        .hero-topbar {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px;
            border-bottom: 1px solid var(--border-color); padding-bottom: 20px;
        }
        .hero-brand {
            font-family: 'Cinzel', serif; font-size: 15px; font-weight: 700; color: var(--text-color);
            letter-spacing: 2px; display: flex; align-items: center; gap: 10px;
        }
        .hero-nav-links {
            display: flex; gap: 25px; font-size: 12px; text-transform: uppercase;
            letter-spacing: 1.5px; color: var(--text-secondary); font-weight: 600;
        }
        .hero-title {
            font-family: 'Cinzel', serif; font-size: 52px; font-weight: 800; color: var(--text-color);
            letter-spacing: 2px; line-height: 1.1; margin-bottom: 16px;
        }
        .hero-subtitle-tag {
            font-size: 12px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px;
            font-weight: 700; margin-bottom: 20px;
        }
        .hero-desc { color: var(--text-secondary); font-size: 15px; line-height: 1.6; max-width: 650px; margin-bottom: 35px; }
        .feature-pills-container { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 40px; }
        .feature-pill {
            background: rgba(219, 39, 119, 0.1); border: 1px solid var(--border-color); color: var(--accent);
            padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;
        }
        </style>
        <div class="full-hero-wrapper">
            <div class="hero-inner">
                <div class="hero-topbar">
                    <div class="hero-brand">
                        <span style="width: 10px; height: 10px; background: #f472b6; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #f472b6;"></span>
                        PLAYING / MARKET
                    </div>
                    <div class="hero-nav-links"><span>Tienda</span><span>Categorías</span><span>Blog</span><span>Contacto</span></div>
                </div>
                <div class="hero-subtitle-tag">Boutique de Moda</div>
                <h1 class="hero-title">Lewin Boutique<br>Control Center</h1>
                <p class="hero-desc">
                    Gestión completa de inventario, ventas, reportes y catálogo visual en una sola plataforma,
                    con una interfaz de lujo en pantalla negra y oro rosa.
                </p>
                <div class="feature-pills-container">
                    <span class="feature-pill">📷 Fotos de productos</span>
                    <span class="feature-pill">💳 Ventas y compras</span>
                    <span class="feature-pill">📈 Reportes de rentabilidad</span>
                    <span class="feature-pill">👥 Roles de usuario</span>
                </div>
            </div>
            <div class="hero-inner" style="max-width: 380px;">
        """,
        unsafe_allow_html=True,
    )

    if st.button("INICIO", use_container_width=True):
        st.session_state.etapa = "login"
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================================
# 2. LOGIN
# =====================================================================================

elif not st.session_state.autenticado and st.session_state.etapa == "login":
    if st.button("← Volver a la portada"):
        st.session_state.etapa = "bienvenida"
        st.rerun()

    _, col_centro, _ = st.columns([1, 1.4, 1])
    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h3>✦ Lewin Boutique Access</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: var(--text-secondary); font-size: 12px;'>Ingrese sus credenciales en el sistema.</p>", unsafe_allow_html=True)

            usuario_input = st.text_input("Email Address / Usuario", placeholder="Ingrese su usuario")
            clave_input = st.text_input("Password / Contraseña", type="password", placeholder="Ingrese su contraseña")
            remember_checked = st.checkbox("Remember me")

            if st.button("Log in 🚪🚶", use_container_width=True):
                user_clean = usuario_input.strip().lower()
                pass_clean = clave_input.strip()

                if user_clean in USUARIOS and USUARIOS[user_clean]["clave"] == pass_clean:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = user_clean
                    st.session_state.rol_actual = USUARIOS[user_clean]["rol"]

                    if remember_checked:
                        st.query_params["recuerdame_user"] = user_clean
                    elif "recuerdame_user" in st.query_params:
                        del st.query_params["recuerdame_user"]

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

    st.sidebar.markdown(
        "<p style='font-size:10px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:1.5px; font-weight:700; margin: 12px 0 6px 4px;'>Menú Principal</p>",
        unsafe_allow_html=True,
    )

    opciones_menu = [("existencias", "📊 Existencias")]
    opciones_menu.append(("vender", "💳 Vender"))
    opciones_menu.append(("comprar", "📦 Registrar Compra"))
    if ES_ADMIN:
        opciones_menu.append(("registrar", "➕ Registrar Prenda"))
        opciones_menu.append(("modificar", "✏️ Editar / Borrar"))
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
    # Si un vendedor quedó apuntando a una página de admin (por sesión previa), lo regresamos
    if menu in ("registrar", "modificar", "configuracion") and not ES_ADMIN:
        menu = "existencias"
        st.session_state.menu_activo = "existencias"

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

        valor_inventario = 0.0
        if not df.empty and "cantidad" in df.columns and "precio_venta" in df.columns:
            valor_inventario = float((df["cantidad"] * df["precio_venta"]).sum())

        st.markdown("<div class='section-title'>Visión General del Inventario</div><div class='section-subtitle'>Resumen general de métricas y existencias.</div>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        for col, label, value in [
            (col1, "Total de Prendas / Modelos", total_prendas),
            (col2, "Stock Total Acumulado", stock_total),
            (col3, "Alertas de Stock Bajo", total_alertas),
            (col4, "Valor de Inventario (venta)", moneda(valor_inventario)),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>""", unsafe_allow_html=True)

        if total_alertas > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            nombres_alerta = ", ".join(prendas_alerta["Producto"].astype(str).tolist()[:8])
            st.markdown(
                f"""<div class="alert-banner">⚠️ <b>{total_alertas} prenda(s)</b> están en o por debajo del mínimo de stock: {nombres_alerta}{"..." if total_alertas > 8 else ""}</div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            st.markdown("<div class='section-title'>⚡ Ajuste Rápido de Stock</div><div class='section-subtitle'>Modifica existencias de manera inmediata seleccionando la prenda.</div>", unsafe_allow_html=True)
            col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
            with col_q1:
                ids_rapidos = df["ID"].astype(str).tolist()
                id_rapido = st.selectbox("Seleccionar Prenda", ids_rapidos, key="select_ajuste_rapido")
            with col_q2:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➖ Quitar 1 (-1)", use_container_width=True, key="btn_minus_1"):
                    fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = max(0, int(fila_actual["cantidad"]) - 1)
                    datos_act = fila_actual.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.success(f"Stock actualizado a {nueva_cant}")
                        st.rerun()
            with col_q3:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Añadir 1 (+1)", use_container_width=True, key="btn_plus_1"):
                    fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = int(fila_actual["cantidad"]) + 1
                    datos_act = fila_actual.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.success(f"Stock actualizado a {nueva_cant}")
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>📋 Búsqueda y Filtros Avanzados</div><div class='section-subtitle'>Combina filtros para encontrar exactamente lo que buscas.</div>", unsafe_allow_html=True)

            col_f1, col_f2, col_f3 = st.columns([1.5, 1, 1])
            with col_f1:
                busqueda = st.text_input("🔍 Buscar por nombre o ID", placeholder="Escribe el nombre de la prenda o su ID...")
            with col_f2:
                categorias_disponibles = ["Todas"] + sorted(list(df["Categoria"].dropna().unique()))
                filtro_categoria = st.selectbox("📂 Categoría", categorias_disponibles)
            with col_f3:
                tallas_disponibles = ["Todas"] + sorted(list(df["talla"].dropna().unique()))
                filtro_talla = st.selectbox("📏 Talla", tallas_disponibles)

            col_f4, col_f5, col_f6 = st.columns([1, 1, 1])
            with col_f4:
                colores_disponibles = ["Todos"] + sorted(list(df["color"].dropna().unique()))
                filtro_color = st.selectbox("🎨 Color", colores_disponibles)
            with col_f5:
                orden = st.selectbox("↕️ Ordenar por", ["Nombre (A-Z)", "Stock (mayor a menor)", "Stock (menor a mayor)", "Más vendidos"])
            with col_f6:
                solo_favoritos = st.checkbox("⭐ Solo favoritos", value=False)

            df_filtrado = df.copy()
            if busqueda.strip():
                query = busqueda.strip().lower()
                df_filtrado = df_filtrado[
                    df_filtrado["ID"].astype(str).str.lower().str.contains(query)
                    | df_filtrado["Producto"].astype(str).str.lower().str.contains(query)
                ]
            if filtro_categoria != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Categoria"] == filtro_categoria]
            if filtro_talla != "Todas":
                df_filtrado = df_filtrado[df_filtrado["talla"] == filtro_talla]
            if filtro_color != "Todos":
                df_filtrado = df_filtrado[df_filtrado["color"] == filtro_color]
            if solo_favoritos:
                df_filtrado = df_filtrado[df_filtrado["favorito"] == True]  # noqa: E712

            if orden == "Nombre (A-Z)":
                df_filtrado = df_filtrado.sort_values("Producto")
            elif orden == "Stock (mayor a menor)":
                df_filtrado = df_filtrado.sort_values("cantidad", ascending=False)
            elif orden == "Stock (menor a mayor)":
                df_filtrado = df_filtrado.sort_values("cantidad", ascending=True)
            elif orden == "Más vendidos":
                movs = cargar_movimientos()
                if not movs.empty:
                    ventas = movs[movs["tipo"] == "venta"].groupby("prenda_id")["cantidad"].sum()
                    df_filtrado["_vendidos"] = df_filtrado["ID"].astype(str).map(ventas).fillna(0)
                    df_filtrado = df_filtrado.sort_values("_vendidos", ascending=False)

            st.markdown("<br>", unsafe_allow_html=True)
            total_registros = len(df_filtrado)
            if total_registros > 0:
                items_por_pagina = 9
                total_paginas = max(1, (total_registros - 1) // items_por_pagina + 1)

                col_p1, col_p2 = st.columns([2, 2])
                with col_p1:
                    pagina_sel = st.selectbox("📄 Página", range(1, total_paginas + 1), key="paginacion_tabla") if total_paginas > 1 else 1

                inicio = (pagina_sel - 1) * items_por_pagina
                fin = min(inicio + items_por_pagina, total_registros)
                df_paginado = df_filtrado.iloc[inicio:fin]

                csv_data = df_filtrado.to_csv(index=False, sep=';').encode('utf-8-sig')
                with col_p2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    st.download_button("📥 Exportar Inventario a CSV", data=csv_data,
                                        file_name="inventario_lewin.csv", mime="text/csv",
                                        use_container_width=True)

                st.markdown(f"<div class='section-title'>Resultados (Mostrando {inicio+1} - {fin} de {total_registros})</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                cols_tarjetas = st.columns(3)
                for idx, (_, row) in enumerate(df_paginado.iterrows()):
                    col_actual = cols_tarjetas[idx % 3]
                    is_alerta = int(row["cantidad"]) <= int(row["alerta"])
                    borde_color = "var(--accent)" if is_alerta else "var(--border-color)"
                    badge_stock = (
                        f"<span style='color: #f472b6; font-weight: 700;'>Stock Bajo ({row['cantidad']})</span>"
                        if is_alerta else
                        f"<span style='color: #34d399; font-weight: 700;'>Stock: {row['cantidad']}</span>"
                    )
                    estrella = "⭐" if bool(row.get("favorito", False)) else "☆"
                    foto_html = (
                        f'<img class="product-photo" src="{row["foto_url"]}" />'
                        if row.get("foto_url") else
                        '<div class="product-photo-placeholder">👕</div>'
                    )
                    precio_html = ""
                    if float(row.get("precio_venta", 0) or 0) > 0:
                        precio_html = f"<div style='margin-top:6px; font-size:14px; font-weight:700; color: var(--accent);'>{moneda(row.get('precio_venta', 0))}</div>"

                    with col_actual:
                        st.markdown(
                            f"""<div class="product-card" style="border-color: {borde_color};">
{foto_html}
<div class="product-card-body">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
<span style="background: rgba(219, 39, 119, 0.15); color: var(--accent); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">ID: {row['ID']}</span>
<span style="font-size: 12px; color: var(--text-secondary);">{row['Categoria']}</span>
</div>
<div style="font-size: 16px; font-weight: 700; color: var(--text-color); margin-bottom: 8px;">{estrella} {row['Producto']}</div>
<div style="font-size: 13px; color: var(--text-secondary); display: flex; gap: 12px; margin-bottom: 8px;">
<span>📏 Talla: <b>{row['talla']}</b></span>
<span>🎨 Color: <b>{row['color']}</b></span>
</div>
{precio_html}
<div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 10px; font-size: 13px;">
{badge_stock}
<span style="font-size: 11px; color: var(--text-secondary);">Alerta mín: {row['alerta']}</span>
</div>
</div>
</div>""",
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
                                    qr_bytes = generar_qr_bytes(f"ID:{row['ID']} | {row['Producto']}")
                                    st.image(qr_bytes, width=140)
                                else:
                                    st.caption("Instala 'qrcode' en requirements.txt para activar esta función.")

                        detalles_texto = f"ID: {row['ID']} - {row['Producto']} ({row['Categoria']}) - Talla: {row['talla']} - Color: {row['color']} - Stock: {row['cantidad']}"
                        render_copy_button(detalles_texto, label="Copiar Detalles")
                        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
            else:
                st.info("No se encontraron registros con los filtros seleccionados.")
        else:
            st.info("No hay prendas registradas todavía en el sistema.")

    # -----------------------------------------------------------------------------
    # VENDER
    # -----------------------------------------------------------------------------
    elif menu == "vender":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">💳 Registrar Venta</div>
    <div class="page-subtitle">Descuenta stock automáticamente y guarda el movimiento en el historial.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas para vender.")
        else:
            with st.form("form_vender"):
                ids_venta = df["ID"].astype(str).tolist()
                id_venta = st.selectbox(
                    "Prenda", ids_venta,
                    format_func=lambda x: f"{x} — {df[df['ID'].astype(str) == x]['Producto'].values[0]}",
                )
                fila = df[df["ID"].astype(str) == str(id_venta)].iloc[0]

                st.markdown(f"**Stock disponible:** {int(fila['cantidad'])} unidades")

                col1, col2 = st.columns(2)
                with col1:
                    cantidad_vender = st.number_input("Cantidad a vender", min_value=1, max_value=max(1, int(fila["cantidad"])), value=1, step=1)
                with col2:
                    precio_unit = st.number_input("Precio de venta (por unidad)", min_value=0.0, value=float(fila.get("precio_venta", 0) or 0), step=1.0)

                total_venta = cantidad_vender * precio_unit
                st.markdown(f"**Total de la venta:** {moneda(total_venta)}")

                if st.form_submit_button("💰 Confirmar Venta", use_container_width=True):
                    if int(fila["cantidad"]) < cantidad_vender:
                        st.error("No hay stock suficiente para esta venta.")
                    else:
                        datos_act = fila.to_dict()
                        datos_act["cantidad"] = int(fila["cantidad"]) - int(cantidad_vender)
                        if actualizar_prenda(id_venta, datos_act):
                            registrar_movimiento(
                                prenda_id=id_venta, producto=fila["Producto"], tipo="venta",
                                cantidad=cantidad_vender, precio_unitario=precio_unit,
                                costo_unitario=fila.get("costo", 0),
                            )
                            st.success(f"¡Venta registrada! Total: {moneda(total_venta)}")
                            st.rerun()

    # -----------------------------------------------------------------------------
    # COMPRAR / REPONER STOCK
    # -----------------------------------------------------------------------------
    elif menu == "comprar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">📦 Registrar Compra de Mercancía</div>
    <div class="page-subtitle">Suma unidades al stock existente y registra el costo pagado al proveedor.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas. Primero registra una prenda desde el menú correspondiente.")
        else:
            with st.form("form_comprar"):
                ids_compra = df["ID"].astype(str).tolist()
                id_compra = st.selectbox(
                    "Prenda", ids_compra,
                    format_func=lambda x: f"{x} — {df[df['ID'].astype(str) == x]['Producto'].values[0]}",
                )
                fila = df[df["ID"].astype(str) == str(id_compra)].iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    cantidad_comprar = st.number_input("Cantidad a añadir", min_value=1, value=1, step=1)
                with col2:
                    costo_unit = st.number_input("Costo por unidad", min_value=0.0, value=float(fila.get("costo", 0) or 0), step=1.0)

                actualizar_costo = st.checkbox("Actualizar el costo registrado de esta prenda con este valor", value=True)

                if st.form_submit_button("📦 Confirmar Compra", use_container_width=True):
                    datos_act = fila.to_dict()
                    datos_act["cantidad"] = int(fila["cantidad"]) + int(cantidad_comprar)
                    if actualizar_costo:
                        datos_act["costo"] = costo_unit
                    if actualizar_prenda(id_compra, datos_act):
                        registrar_movimiento(
                            prenda_id=id_compra, producto=fila["Producto"], tipo="compra",
                            cantidad=cantidad_comprar, costo_unitario=costo_unit,
                        )
                        st.success("¡Compra registrada y stock actualizado!")
                        st.rerun()

    # -----------------------------------------------------------------------------
    # REGISTRAR PRENDA (solo admin)
    # -----------------------------------------------------------------------------
    elif menu == "registrar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">✨ Registro de Nuevas Prendas</div>
    <div class="page-subtitle">Añade nuevos artículos al catálogo, con foto, costo y precio de venta.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form(f"form_ropa_{st.session_state.form_version}", clear_on_submit=True):
            st.subheader("📦 Información Básica")
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("ID", placeholder="Ej: A1")
            with col2:
                nombre = st.text_input("Producto", placeholder="Ej: Short")

            st.subheader("🏷️ Clasificación y Atributos")
            col3, col4, col5 = st.columns(3)
            with col3:
                categoria = st.selectbox("Categoría", st.session_state.categorias_maestras)
            with col4:
                talla = st.selectbox("Talla", st.session_state.tallas_maestras)
            with col5:
                color = st.selectbox("Color", st.session_state.colores_maestros)

            st.subheader("📊 Control de Stock, Precios y Alertas")
            col6, col7 = st.columns(2)
            with col6:
                cantidad = st.number_input("Cantidad", min_value=0, value=0, step=1)
            with col7:
                alerta = st.number_input("Alerta de stock", min_value=0, value=0, step=1)

            col8, col9 = st.columns(2)
            with col8:
                costo = st.number_input("Costo por unidad", min_value=0.0, value=0.0, step=1.0)
            with col9:
                precio_venta = st.number_input("Precio de venta", min_value=0.0, value=0.0, step=1.0)

            st.subheader("📷 Foto del producto (opcional)")
            foto_subida = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg", "webp"])

            st.markdown("---")
            if st.form_submit_button("💾 Guardar Prenda en el Sistema", use_container_width=True):
                if sku.strip() == "":
                    st.error("El campo ID es obligatorio.")
                else:
                    foto_url = subir_imagen(foto_subida, sku.strip()) if foto_subida else ""
                    nueva_prenda = {
                        "ID": sku.strip(), "Producto": nombre.strip(), "Categoria": categoria,
                        "talla": talla, "color": color, "cantidad": cantidad, "alerta": alerta,
                        "costo": costo, "precio_venta": precio_venta, "foto_url": foto_url or "",
                        "favorito": False,
                    }
                    if guardar_prenda(nueva_prenda):
                        st.success("¡Prenda guardada con éxito!")
                        st.session_state.form_version += 1
                        st.rerun()

    # -----------------------------------------------------------------------------
    # MODIFICAR / ELIMINAR (solo admin)
    # -----------------------------------------------------------------------------
    elif menu == "modificar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">Modificar o Eliminar Prenda</div>
    <div class="page-subtitle">Busca o selecciona una prenda existente para actualizar sus datos o borrarla.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if not df.empty:
            modo_seleccion = st.radio("¿Cómo deseas encontrar la prenda?", ["Seleccionar de la lista", "Buscar por ID / Nombre"], horizontal=True)
            id_seleccionado = None

            if modo_seleccion == "Seleccionar de la lista":
                lista_ids = df["ID"].astype(str).tolist()
                id_seleccionado = st.selectbox("Seleccione el ID de la prenda", lista_ids)
            else:
                texto_busqueda = st.text_input("Escribe el ID o nombre del producto a buscar:", placeholder="Ej: A1 o Short...")
                if texto_busqueda.strip():
                    q = texto_busqueda.strip().lower()
                    df_coincidencias = df[
                        df["ID"].astype(str).str.lower().str.contains(q) | df["Producto"].astype(str).str.lower().str.contains(q)
                    ]
                    if not df_coincidencias.empty:
                        opciones_encontradas = df_coincidencias["ID"].astype(str).tolist()
                        id_seleccionado = st.selectbox(
                            f"Coincidencias encontradas ({len(opciones_encontradas)}):", opciones_encontradas,
                            format_func=lambda x: f"ID: {x} - {df_coincidencias[df_coincidencias['ID'].astype(str) == x]['Producto'].values[0]}",
                        )
                    else:
                        st.warning("No se encontraron prendas con ese criterio.")

            if id_seleccionado:
                fila_data = df[df["ID"].astype(str) == str(id_seleccionado)].iloc[0]

                if fila_data.get("foto_url"):
                    st.image(fila_data["foto_url"], width=180)

                st.markdown("<br>", unsafe_allow_html=True)
                with st.form("form_editar"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nuevo_id = st.text_input("ID", value=str(fila_data["ID"]))
                    with col2:
                        nuevo_nombre = st.text_input("Producto", value=str(fila_data["Producto"]))

                    st.markdown("---")
                    col3, col4, col5 = st.columns(3)
                    cat_actual = str(fila_data["Categoria"])
                    idx_cat = st.session_state.categorias_maestras.index(cat_actual) if cat_actual in st.session_state.categorias_maestras else 0
                    with col3:
                        nueva_categoria = st.selectbox("Categoria", st.session_state.categorias_maestras, index=idx_cat)

                    talla_actual = str(fila_data["talla"])
                    idx_talla = st.session_state.tallas_maestras.index(talla_actual) if talla_actual in st.session_state.tallas_maestras else 0
                    with col4:
                        nueva_talla = st.selectbox("talla", st.session_state.tallas_maestras, index=idx_talla)

                    color_actual = str(fila_data["color"])
                    idx_color = st.session_state.colores_maestros.index(color_actual) if color_actual in st.session_state.colores_maestros else 0
                    with col5:
                        nuevo_color = st.selectbox("color", st.session_state.colores_maestros, index=idx_color)

                    st.markdown("---")
                    col6, col7 = st.columns(2)
                    with col6:
                        nueva_cantidad = st.number_input("cantidad", min_value=0, value=int(fila_data["cantidad"]), step=1)
                    with col7:
                        nueva_alerta = st.number_input("alerta de stock", min_value=0, value=int(fila_data["alerta"]), step=1)

                    col8, col9 = st.columns(2)
                    with col8:
                        nuevo_costo = st.number_input("costo por unidad", min_value=0.0, value=float(fila_data.get("costo", 0) or 0), step=1.0)
                    with col9:
                        nuevo_precio = st.number_input("precio de venta", min_value=0.0, value=float(fila_data.get("precio_venta", 0) or 0), step=1.0)

                    nueva_foto = st.file_uploader("Reemplazar foto (opcional)", type=["png", "jpg", "jpeg", "webp"])

                    st.markdown("<br>", unsafe_allow_html=True)
                    col_btn1, col_btn2 = st.columns(2)
                    actualizar = col_btn1.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    eliminar = col_btn2.form_submit_button("🗑️ Eliminar Prenda", use_container_width=True)

                    if actualizar:
                        foto_final = fila_data.get("foto_url", "")
                        if nueva_foto:
                            subida = subir_imagen(nueva_foto, nuevo_id)
                            if subida:
                                foto_final = subida
                        datos_mod = {
                            "ID": nuevo_id, "Producto": nuevo_nombre, "Categoria": nueva_categoria,
                            "talla": nueva_talla, "color": nuevo_color, "cantidad": nueva_cantidad,
                            "alerta": nueva_alerta, "costo": nuevo_costo, "precio_venta": nuevo_precio,
                            "foto_url": foto_final, "favorito": bool(fila_data.get("favorito", False)),
                        }
                        if actualizar_prenda(id_seleccionado, datos_mod):
                            st.success("¡Prenda actualizada correctamente!")
                            st.rerun()

                    if eliminar:
                        if eliminar_prenda(id_seleccionado):
                            st.success("¡Prenda eliminada del sistema!")
                            st.rerun()
        else:
            st.info("No hay registros disponibles para modificar.")

    # -----------------------------------------------------------------------------
    # MOVIMIENTOS (historial / kardex)
    # -----------------------------------------------------------------------------
    elif menu == "movimientos":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">📜 Historial de Movimientos</div>
    <div class="page-subtitle">Todas las ventas, compras y ajustes registrados en el sistema.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs = cargar_movimientos()
        if movs.empty:
            st.info("Todavía no hay movimientos registrados. Se irán guardando cuando registres ventas o compras.")
        else:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                tipos_disponibles = ["Todos"] + sorted(movs["tipo"].dropna().unique().tolist())
                filtro_tipo = st.selectbox("Tipo de movimiento", tipos_disponibles)
            with col_m2:
                usuarios_disponibles = ["Todos"] + sorted(movs["usuario"].dropna().unique().tolist())
                filtro_usuario = st.selectbox("Usuario", usuarios_disponibles)

            movs_filtrado = movs.copy()
            if filtro_tipo != "Todos":
                movs_filtrado = movs_filtrado[movs_filtrado["tipo"] == filtro_tipo]
            if filtro_usuario != "Todos":
                movs_filtrado = movs_filtrado[movs_filtrado["usuario"] == filtro_usuario]

            st.dataframe(movs_filtrado, use_container_width=True, hide_index=True)

            csv_movs = movs_filtrado.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button("📥 Exportar Movimientos a CSV", data=csv_movs,
                                file_name="movimientos_lewin.csv", mime="text/csv")

    # -----------------------------------------------------------------------------
    # REPORTES
    # -----------------------------------------------------------------------------
    elif menu == "reportes":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">📈 Reportes y Rentabilidad</div>
    <div class="page-subtitle">Ventas, productos más vendidos y valorización del inventario.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs = cargar_movimientos()
        ventas = movs[movs["tipo"] == "venta"].copy() if not movs.empty else pd.DataFrame()

        total_ventas = 0.0
        total_costo_vendido = 0.0
        if not ventas.empty:
            ventas["monto"] = ventas["cantidad"] * ventas["precio_unitario"]
            ventas["costo_total"] = ventas["cantidad"] * ventas["costo_unitario"]
            total_ventas = float(ventas["monto"].sum())
            total_costo_vendido = float(ventas["costo_total"].sum())
        ganancia = total_ventas - total_costo_vendido

        valor_costo_inv = float((df["cantidad"] * df["costo"]).sum()) if not df.empty else 0.0
        valor_venta_inv = float((df["cantidad"] * df["precio_venta"]).sum()) if not df.empty else 0.0

        col1, col2, col3, col4 = st.columns(4)
        for col, label, value in [
            (col1, "Total Vendido (histórico)", moneda(total_ventas)),
            (col2, "Ganancia Estimada", moneda(ganancia)),
            (col3, "Valor Inventario (costo)", moneda(valor_costo_inv)),
            (col4, "Valor Inventario (venta)", moneda(valor_venta_inv)),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not ventas.empty:
            ventas["fecha_dt"] = pd.to_datetime(ventas["fecha"], errors="coerce")
            ventas["mes"] = ventas["fecha_dt"].dt.to_period("M").astype(str)

            st.markdown("<div class='section-title'>Ventas por mes</div>", unsafe_allow_html=True)
            ventas_mes = ventas.groupby("mes")["monto"].sum()
            st.bar_chart(ventas_mes)

            st.markdown("<div class='section-title'>Top 5 productos más vendidos (unidades)</div>", unsafe_allow_html=True)
            top_productos = ventas.groupby("producto")["cantidad"].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_productos)
        else:
            st.info("Aún no hay ventas registradas para generar gráficas. Usa el menú 'Vender' para empezar a registrar.")

    # -----------------------------------------------------------------------------
    # CONFIGURACIÓN (solo admin)
    # -----------------------------------------------------------------------------
    elif menu == "configuracion":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">⚙️ Configuración del Sistema</div>
    <div class="page-subtitle">Gestiona y personaliza las opciones maestras de categorías, tallas y colores.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)

        with col_cfg1:
            with st.container(border=True):
                st.markdown("<div class='section-title'>📂 Categorías</div>", unsafe_allow_html=True)
                for cat in list(st.session_state.edit_cats):
                    c_col1, c_col2 = st.columns([3, 1])
                    c_col1.markdown(f"- {cat}")
                    if c_col2.button("❌", key=f"del_cat_{cat}"):
                        if len(st.session_state.edit_cats) > 1:
                            st.session_state.edit_cats.remove(cat)
                            st.rerun()
                        else:
                            st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_cat_input = st.text_input("Nueva Categoría", placeholder="Ej: Faldas", key="input_nueva_cat")
                if st.button("➕ Agregar Categoría", key="btn_add_cat"):
                    clean_cat = nueva_cat_input.strip().capitalize()
                    if clean_cat and clean_cat not in st.session_state.edit_cats:
                        st.session_state.edit_cats.append(clean_cat)
                        st.rerun()
                    else:
                        st.warning("Nombre inválido o ya existente.")

        with col_cfg2:
            with st.container(border=True):
                st.markdown("<div class='section-title'>📏 Tallas</div>", unsafe_allow_html=True)
                for t in list(st.session_state.edit_tallas):
                    t_col1, t_col2 = st.columns([3, 1])
                    t_col1.markdown(f"- {t}")
                    if t_col2.button("❌", key=f"del_talla_{t}"):
                        if len(st.session_state.edit_tallas) > 1:
                            st.session_state.edit_tallas.remove(t)
                            st.rerun()
                        else:
                            st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_talla_input = st.text_input("Nueva Talla", placeholder="Ej: 30, XXL", key="input_nueva_talla")
                if st.button("➕ Agregar Talla", key="btn_add_talla"):
                    clean_talla = nueva_talla_input.strip().upper()
                    if clean_talla and clean_talla not in st.session_state.edit_tallas:
                        st.session_state.edit_tallas.append(clean_talla)
                        st.rerun()
                    else:
                        st.warning("Talla inválida o ya existente.")

        with col_cfg3:
            with st.container(border=True):
                st.markdown("<div class='section-title'>🎨 Colores</div>", unsafe_allow_html=True)
                for col_item in list(st.session_state.edit_colores):
                    col_c1, col_c2 = st.columns([3, 1])
                    col_c1.markdown(f"- {col_item}")
                    if col_c2.button("❌", key=f"del_color_{col_item}"):
                        if len(st.session_state.edit_colores) > 1:
                            st.session_state.edit_colores.remove(col_item)
                            st.rerun()
                        else:
                            st.error("Debe existir al menos uno.")
                st.markdown("<br>", unsafe_allow_html=True)
                nuevo_color_input = st.text_input("Nuevo Color", placeholder="Ej: Dorado", key="input_nuevo_color")
                if st.button("➕ Agregar Color", key="btn_add_color"):
                    clean_color = nuevo_color_input.strip().capitalize()
                    if clean_color and clean_color not in st.session_state.edit_colores:
                        st.session_state.edit_colores.append(clean_color)
                        st.rerun()
                    else:
                        st.warning("Color inválido o ya existente.")

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_save_master, _ = st.columns([1, 2, 1])
        with col_save_master:
            if st.button("💾 Guardar configuración en GitHub", use_container_width=True):
                exito = guardar_configuracion_completa(
                    st.session_state.edit_cats, st.session_state.edit_tallas, st.session_state.edit_colores
                )
                if exito:
                    st.session_state.categorias_maestras = list(st.session_state.edit_cats)
                    st.session_state.tallas_maestras = list(st.session_state.edit_tallas)
                    st.session_state.colores_maestros = list(st.session_state.edit_colores)
                    st.success("¡Configuración guardada en GitHub exitosamente!")
                    st.rerun()
