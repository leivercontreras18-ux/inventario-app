import json
from github import Github
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- CONEXIÓN A BASE DE DATOS SUPABASE ---
@st.cache_resource
def obtener_conexion_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = obtener_conexion_supabase()

# --- CARGAR CONFIGURACIÓN DESDE GITHUB CON CACHÉ ---
@st.cache_data(ttl=60)
def cargar_config_github():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo("leivercontreras18-ux/inventario-app")
        file_content = repo.get_contents("config.json", ref="main")
        return json.loads(file_content.decoded_content.decode("utf-8"))
    except Exception:
        return None

# --- CARGAR INVENTARIO (SUPABASE) Y CONFIGURACIÓN (GITHUB) CON CACHÉ OPTIMIZADO ---
@st.cache_data(ttl=30)
def cargar_datos_completos():
    cats_default = ["Vestidos", "Blusas", "Pantalones", "Jeans", "Chaquetas", "Calzado", "Accesorios"]
    tallas_default = ["XS", "S", "M", "L", "XL", "Única"]
    colores_default = ["Negro", "Blanco", "Beige", "Rojo", "Azul", "Rosa", "Verde"]
    
    df = pd.DataFrame(columns=["ID", "Producto", "Categoria", "talla", "color", "cantidad", "alerta"])
    cats, tallas, colores = cats_default, tallas_default, colores_default

    # 1. Cargar Inventario desde Supabase
    if supabase:
        try:
            res_inv = supabase.table("inventario").select("*").execute()
            if res_inv.data:
                df = pd.DataFrame(res_inv.data)
                df = df.rename(
                    columns={
                        "id": "ID",
                        "producto": "Producto",
                        "categoria": "Categoria",
                    }
                )
        except Exception as e:
            st.warning(f"Aviso al cargar inventario de la nube: {e}")

    # 2. Cargar Configuración desde GitHub
    config_data = cargar_config_github()
    if config_data:
        cats = config_data.get("categorias", cats_default)
        tallas = config_data.get("tallas", tallas_default)
        colores = config_data.get("colores", colores_default)

    return df, cats, tallas, colores

def guardar_configuracion_completa(cats, tallas, colores):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo("leivercontreras18-ux/inventario-app")
        
        config_data = {
            "categorias": cats,
            "tallas": tallas,
            "colores": colores
        }
        contenido = json.dumps(config_data, indent=4, ensure_ascii=False)
        
        try:
            file = repo.get_contents("config.json", ref="main")
            repo.update_file(
                file.path, 
                "Actualización automática de configuración de inventario", 
                contenido, 
                file.sha, 
                branch="main"
            )
        except Exception:
            repo.create_file(
                "config.json", 
                "Creación inicial de configuración de inventario", 
                contenido, 
                branch="main"
            )
        cargar_config_github.clear()
        cargar_datos_completos.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración en GitHub: {e}")
        return False

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
        st.session_state.inventario_local = df[
            df["ID"].astype(str) != str(id_prenda)
        ].reset_index(drop=True)
        cargar_datos_completos.clear()
        return True

# --- ESTILOS NÍTIDOS UI CON FONDO MEJORADO Y GLASSMORPHISM ---
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500;600&display=swap');

/* Fondo General con Gradiente Elegante y Luces de Neón Tenues */
.stApp { 
    background: radial-gradient(circle at 20% 20%, rgba(212, 175, 55, 0.06) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(255, 59, 59, 0.05) 0%, transparent 40%),
                linear-gradient(135deg, #0f141d 0%, #141a24 50%, #1a2230 100%);
    background-attachment: fixed;
    color: #f8fafc !important; 
}

header[data-testid="stHeader"] { background: transparent !important; }

.block-container {
    max-width: 100% !important;
    padding: 2rem !important;
}

section[data-testid="stSidebar"] { 
    width: 240px !important;
    background: rgba(15, 20, 29, 0.85) !important; 
    border-right: 1px solid rgba(255, 255, 255, 0.1); 
    backdrop-filter: blur(25px); 
}
section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

/* Inputs estándar de Streamlit */
div[data-baseweb="input"], div[data-baseweb="select"] > div {
    background-color: rgba(25, 33, 47, 0.8) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #ffffff !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: #ff3b3b !important;
}
div[data-baseweb="input"] input {
    color: #ffffff !important;
    font-size: 13px !important;
}

/* Efecto 3D Puerta para TODOS los botones */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: #18202c !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
    transition: all 0.4s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1;
    width: 100% !important;
}

div.stButton > button::before, div[data-testid="stFormSubmitButton"] > button::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: #ff3b3b;
    transform-origin: left center;
    transform: rotateY(0deg);
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease;
    z-index: -1;
    border-radius: 7px;
}

div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: #ff3b3b !important;
    box-shadow: inset 20px 0 30px rgba(255, 59, 59, 0.1), 0 0 20px rgba(255, 59, 59, 0.4) !important;
    color: #ffffff !important;
}

div.stButton > button:hover::before, div[data-testid="stFormSubmitButton"] > button:hover::before {
    transform: rotateY(72deg);
    opacity: 0.95; 
}

div.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateZ(-30px) scale(0.95) !important;
    box-shadow: 0 0 5px rgba(255, 59, 59, 0.6) !important;
}

/* Tarjeta de Bienvenida Glassmorphism */
.hero-card {
    background: rgba(26, 34, 48, 0.65) !important;
    backdrop-filter: blur(30px) !important;
    -webkit-backdrop-filter: blur(30px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 24px;
    padding: 60px 30px 40px 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 30px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    margin-bottom: 25px;
}

/* Formularios Glassmorphism */
div[data-testid="stForm"] {
    background: rgba(26, 34, 48, 0.65) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    padding: 25px !important;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
}

.page-header { margin-bottom: 25px; padding-bottom: 10px; }
.page-title { font-size: 32px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
.page-subtitle { font-size: 14px; color: #a0aec0 !important; margin-top: 4px; }

.section-title { font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
.section-subtitle { font-size: 12px; color: #a0aec0; margin-bottom: 15px; }

.metric-card {
    background: rgba(26, 34, 48, 0.65); 
    backdrop-filter: blur(20px); 
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 20px; border-radius: 16px; text-align: left;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    height: 100%;
}
.metric-value { font-size: 32px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
.metric-label { font-size: 11px; color: #a0aec0 !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }

.user-profile { 
    background: rgba(255, 255, 255, 0.05); 
    padding: 14px 16px; border-radius: 14px; 
    border: 1px solid rgba(212, 175, 55, 0.3); margin-bottom: 20px;
    display: flex; align-items: center; gap: 12px;
}
.user-avatar {
    width: 36px; height: 36px; background: #d4af37; color: #0d121e;
    font-weight: 800; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 15px; box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
}
.user-info-title { font-size: 9px; color: #d4af37; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }
.user-info-name { font-size: 14px; font-weight: 600; color: #ffffff; }
</style>
""",
    unsafe_allow_html=True,
)

# --- ESTADOS DE SESIÓN ---
USUARIOS = {"leiver": "natsudraghonil", "winderly": "coromoto"}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""
if "etapa" not in st.session_state:
    st.session_state.etapa = "bienvenida"
if "inventario_local" not in st.session_state:
    st.session_state.inventario_local = pd.DataFrame(
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
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# Cargar datos e inicializar listas maestras
df, cats_init, tallas_init, colores_init = cargar_datos_completos()

if "categorias_maestras" not in st.session_state:
    st.session_state.categorias_maestras = cats_init
if "tallas_maestras" not in st.session_state:
    st.session_state.tallas_maestras = tallas_init
if "colores_maestros" not in st.session_state:
    st.session_state.colores_maestros = colores_init

# Sincronizar estados de edición de configuración
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

# --- 1. PANTALLA DE BIENVENIDA ---
if not st.session_state.autenticado and st.session_state.etapa == "bienvenida":
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1.8, 1])
    with col_centro:
        st.markdown(
            """
            <style>
            @keyframes levitar {
                0% { transform: translateY(0px); filter: drop-shadow(0 10px 15px rgba(212,175,55,0.4)); }
                50% { transform: translateY(-12px); filter: drop-shadow(0 20px 25px rgba(212,175,55,0.7)); }
                100% { transform: translateY(0px); filter: drop-shadow(0 10px 15px rgba(212,175,55,0.4)); }
            }
            .hero-card::before {
                content: '';
                position: absolute;
                top: -50%; left: -50%;
                width: 200%; height: 200%;
                background: radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.08) 0%, transparent 55%);
                pointer-events: none;
                z-index: 0;
            }
            .hero-content {
                position: relative;
                z-index: 1;
            }
            .hero-icon {
                font-size: 72px;
                display: inline-block;
                margin-bottom: 20px;
                animation: levitar 4s ease-in-out infinite;
            }
            .hero-title {
                font-family: 'Cinzel', serif;
                font-size: 44px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: 5px;
                margin-bottom: 12px;
                text-shadow: 0 0 40px rgba(255,255,255,0.2);
            }
            .hero-subtitle {
                font-size: 13px;
                color: #d4af37;
                text-transform: uppercase;
                letter-spacing: 5px;
                font-weight: 700;
                margin-bottom: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }
            .hero-subtitle::before, .hero-subtitle::after {
                content: '';
                height: 1px;
                width: 50px;
                background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.6), transparent);
            }
            .hero-desc {
                color: #a0aec0;
                font-size: 15px;
                line-height: 1.7;
                max-width: 480px;
                margin: 0 auto;
                font-weight: 400;
            }
            </style>
            
            <div class="hero-card">
                <div class="hero-content">
                    <div class="hero-icon">👕</div>
                    <h1 class="hero-title">LEWIN BOUTIQUE</h1>
                    <p class="hero-subtitle">Boutique & Inventory Control</p>
                    <p class="hero-desc">
                        Sistema exclusivo de Lewin Boutique
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        _, col_boton_centro, _ = st.columns([1, 1.4, 1])
        with col_boton_centro:
            if st.button("Acceder al Sistema 🚪🚶", use_container_width=True):
                st.session_state.etapa = "login"
                st.rerun()

    st.stop()

# --- 2. FLUJO DE LOGIN ---
elif not st.session_state.autenticado and st.session_state.etapa == "login":
    if st.button("← Volver a la portada"):
        st.session_state.etapa = "bienvenida"
        st.rerun()

    _, col_centro, _ = st.columns([1, 1.4, 1])
    
    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h3>✦ Lewin Boutique</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #a0aec0; font-size: 12px;'>Ingrese sus credenciales de acceso.</p>", unsafe_allow_html=True)
            
            usuario_input = st.text_input("Email Address / Usuario", placeholder="Ingrese su usuario")
            clave_input = st.text_input("Password / Contraseña", type="password", placeholder="Ingrese su contraseña")
            remember_checked = st.checkbox("Remember me")
            
            if st.button("Log in 🚪🚶", use_container_width=True):
                user_clean = usuario_input.strip().lower()
                pass_clean = clave_input.strip()
                
                if user_clean in USUARIOS and USUARIOS[user_clean] == pass_clean:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = user_clean
                    
                    if remember_checked:
                        st.query_params["recuerdame_user"] = user_clean
                    else:
                        if "recuerdame_user" in st.query_params:
                            del st.query_params["recuerdame_user"]
                            
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos.")
                    
    st.stop()

# --- 3. PANEL PRINCIPAL ---
else:
    usuario_formateado = st.session_state.usuario_actual.capitalize()
    inicial_usuario = usuario_formateado[0]

    st.sidebar.markdown(
        f"""
<div class="user-profile">
    <div class="user-avatar">{inicial_usuario}</div>
    <div>
        <div class="user-info-title">● Sesión Activa</div>
        <div class="user-info-name">{usuario_formateado}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        "<p style='font-size:10px; color:#a0aec0; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; margin: 12px 0 6px 4px;'>Menú Principal</p>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("📊 Existencias", use_container_width=True):
        st.session_state.menu_activo = "existencias"
        st.rerun()

    if st.sidebar.button("➕ Registrar Prenda", use_container_width=True):
        st.session_state.menu_activo = "registrar"
        st.rerun()

    if st.sidebar.button("✏️ Editar / Borrar", use_container_width=True):
        st.session_state.menu_activo = "modificar"
        st.rerun()

    if st.sidebar.button("⚙️ Configuración", use_container_width=True):
        st.session_state.menu_activo = "configuracion"
        st.rerun()

    st.sidebar.markdown(
        "<hr style='margin: 25px 0 15px 0; border-color: rgba(255,255,255,0.08);'>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.etapa = "bienvenida"
        if "recuerdame_user" in st.query_params:
            del st.query_params["recuerdame_user"]
        st.rerun()

    menu = st.session_state.get("menu_activo", "existencias")

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
        stock_total = (
            int(df["cantidad"].sum())
            if not df.empty and "cantidad" in df.columns
            else 0
        )
        
        total_alertas = 0
        if not df.empty and "cantidad" in df.columns and "alerta" in df.columns:
            total_alertas = int(df[df["cantidad"] <= df["alerta"]].shape[0])

        st.markdown(
            """
<div class="section-title">Visión General del Inventario</div>
<div class="section-subtitle">Resumen general de métricas y existencias.</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
<div class="metric-card">
    <div class="metric-label">Total de Prendas / Modelos</div>
    <div class="metric-value">{total_prendas}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
<div class="metric-card">
    <div class="metric-label">Stock Total Acumulado</div>
    <div class="metric-value">{stock_total}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
<div class="metric-card">
    <div class="metric-label">Alertas de Stock Bajo</div>
    <div class="metric-value" style="color: {'#ff3b3b' if total_alertas > 0 else '#d4af37'} !important;">{total_alertas}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            # --- AJUSTE RÁPIDO DE STOCK (+1 / -1) ---
            st.markdown(
                """
<div class="section-title">⚡ Ajuste Rápido de Stock</div>
<div class="section-subtitle">Modifica existencias de manera inmediata seleccionando la prenda.</div>
""",
                unsafe_allow_html=True,
            )
            col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
            with col_q1:
                ids_rapidos = df["ID"].astype(str).tolist()
                id_rapido = st.selectbox("Seleccionar Prenda", ids_rapidos, key="select_ajuste_rapido")
            with col_q2:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➖ Quitar 1 (-1)", use_container_width=True, key="btn_minus_1"):
                    if id_rapido:
                        fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                        nueva_cant = max(0, int(fila_actual["cantidad"]) - 1)
                        datos_act = {
                            "ID": str(fila_actual["ID"]),
                            "Producto": str(fila_actual["Producto"]),
                            "Categoria": str(fila_actual["Categoria"]),
                            "talla": str(fila_actual["talla"]),
                            "color": str(fila_actual["color"]),
                            "cantidad": nueva_cant,
                            "alerta": int(fila_actual["alerta"])
                        }
                        if actualizar_prenda(id_rapido, datos_act):
                            st.success(f"Stock actualizado a {nueva_cant}")
                            st.rerun()
            with col_q3:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Añadir 1 (+1)", use_container_width=True, key="btn_plus_1"):
                    if id_rapido:
                        fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                        nueva_cant = int(fila_actual["cantidad"]) + 1
                        datos_act = {
                            "ID": str(fila_actual["ID"]),
                            "Producto": str(fila_actual["Producto"]),
                            "Categoria": str(fila_actual["Categoria"]),
                            "talla": str(fila_actual["talla"]),
                            "color": str(fila_actual["color"]),
                            "cantidad": nueva_cant,
                            "alerta": int(fila_actual["alerta"])
                        }
                        if actualizar_prenda(id_rapido, datos_act):
                            st.success(f"Stock actualizado a {nueva_cant}")
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """
<div class="section-title">📋 Filtros, Búsqueda y Paginación</div>
<div class="section-subtitle">Filtra por categoría o busca un producto en específico.</div>
""",
                unsafe_allow_html=True,
            )

            col_f1, col_f2 = st.columns([1.5, 1])
            with col_f1:
                busqueda = st.text_input("🔍 Buscar por nombre o ID", placeholder="Escribe el nombre de la prenda o su ID...")
            with col_f2:
                categorias_disponibles = ["Todas"] + list(df["Categoria"].dropna().unique())
                filtro_categoria = st.selectbox("📂 Filtrar por Categoría", categorias_disponibles)

            df_filtrado = df.copy()
            if busqueda.strip():
                query = busqueda.strip().lower()
                df_filtrado = df_filtrado[
                    df_filtrado["ID"].astype(str).str.lower().str.contains(query) | 
                    df_filtrado["Producto"].astype(str).str.lower().str.contains(query)
                ]
            
            if filtro_categoria != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Categoria"] == filtro_categoria]

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- PAGINACIÓN Y EXPORTACIÓN CSV ---
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
                    st.download_button(
                        label="📥 Exportar Inventario a CSV",
                        data=csv_data,
                        file_name="inventario_lewin.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                st.markdown(f"<div class='section-title'>Resultados (Mostrando {inicio+1} - {fin} de {total_registros} registros)</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # --- DISEÑO DE TARJETAS GRID (3 COLUMNAS) ---
                cols_tarjetas = st.columns(3)
                for idx, (_, row) in enumerate(df_paginado.iterrows()):
                    col_actual = cols_tarjetas[idx % 3]
                    
                    is_alerta = int(row["cantidad"]) <= int(row["alerta"])
                    borde_color = "#ff3b3b" if is_alerta else "rgba(255, 255, 255, 0.12)"
                    badge_stock = f"<span style='color: #ff3b3b; font-weight: 700;'>Stock Bajo ({row['cantidad']})</span>" if is_alerta else f"<span style='color: #22c55e; font-weight: 700;'>Stock: {row['cantidad']}</span>"

                    with col_actual:
                        st.markdown(
                            f"""
                            <div style="
                                background: rgba(26, 34, 48, 0.65);
                                backdrop-filter: blur(20px);
                                border: 1px solid {borde_color};
                                padding: 18px;
                                border-radius: 14px;
                                margin-bottom: 16px;
                                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <span style="background: rgba(212, 175, 55, 0.15); color: #d4af37; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">ID: {row['ID']}</span>
                                    <span style="font-size: 12px; color: #a0aec0;">{row['Categoria']}</span>
                                </div>
                                <div style="font-size: 16px; font-weight: 700; color: #ffffff; margin-bottom: 8px;">{row['Producto']}</div>
                                <div style="font-size: 13px; color: #cbd5e1; display: flex; gap: 12px; margin-bottom: 12px;">
                                    <span>📏 Talla: <b>{row['talla']}</b></span>
                                    <span>🎨 Color: <b>{row['color']}</b></span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px; font-size: 13px;">
                                    {badge_stock}
                                    <span style="font-size: 11px; color: #a0aec0;">Alerta mín: {row['alerta']}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.info("No se encontraron registros con los filtros seleccionados.")
        else:
            st.info("No hay prendas registradas todavía en el sistema.")

    elif menu == "registrar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">✨ Registro de Nuevas Prendas</div>
    <div class="page-subtitle">Añade nuevos artículos al catálogo de la boutique de forma rápida y ordenada.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form(f"form_ropa_{st.session_state.form_version}", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("ID", placeholder="Ej: A1")
            with col2:
                nombre = st.text_input("Producto", placeholder="Ej: Short")

            st.markdown("---")
            
            col3, col4, col5 = st.columns(3)
            with col3:
                categoria = st.selectbox("Categoria", st.session_state.categorias_maestras)
            with col4:
                talla = st.selectbox("talla", st.session_state.tallas_maestras)
            with col5:
                color = st.selectbox("color", st.session_state.colores_maestros)

            st.markdown("---")

            col6, col7 = st.columns(2)
            with col6:
                cantidad = st.number_input("cantidad", min_value=0, step=1)
            with col7:
                alerta = st.number_input("alerta de stock", min_value=0, step=1)

            st.markdown("")

            if st.form_submit_button("💾 Guardar Prenda en el Sistema", use_container_width=True):
                if sku.strip() == "":
                    st.error("El campo ID es obligatorio.")
                else:
                    nueva_prenda = {
                        "ID": sku.strip(),
                        "Producto": nombre.strip(),
                        "Categoria": categoria,
                        "talla": talla,
                        "color": color,
                        "cantidad": cantidad,
                        "alerta": alerta,
                    }
                    if guardar_prenda(nueva_prenda):
                        st.success("¡Prenda guardada con éxito!")
                        st.session_state.form_version += 1
                        st.rerun()

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
            modo_seleccion = st.radio(
                "¿Cómo deseas encontrar la prenda?", 
                ["Seleccionar de la lista", "Buscar por ID / Nombre"], 
                horizontal=True
            )

            id_seleccionado = None

            if modo_seleccion == "Seleccionar de la lista":
                lista_ids = df["ID"].astype(str).tolist()
                id_seleccionado = st.selectbox("Seleccione el ID de la prenda", lista_ids)
            else:
                texto_busqueda = st.text_input("Escribe el ID o nombre del producto a buscar:", placeholder="Ej: A1 o Short...")
                if texto_busqueda.strip():
                    q = texto_busqueda.strip().lower()
                    df_coincidencias = df[
                        df["ID"].astype(str).str.lower().str.contains(q) | 
                        df["Producto"].astype(str).str.lower().str.contains(q)
                    ]
                    if not df_coincidencias.empty:
                        opciones_encontradas = df_coincidencias["ID"].astype(str).tolist()
                        id_seleccionado = st.selectbox(
                            f"Coincidencias encontradas ({len(opciones_encontradas)}):", 
                            opciones_encontradas,
                            format_func=lambda x: f"ID: {x} - {df_coincidencias[df_coincidencias['ID'].astype(str) == x]['Producto'].values[0]}"
                        )
                    else:
                        st.warning("No se encontraron prendas con ese criterio.")

            if id_seleccionado:
                fila_data = df[df["ID"].astype(str) == str(id_seleccionado)].iloc[0]

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

                    st.markdown("<br>", unsafe_allow_html=True)
                    col_btn1, col_btn2 = st.columns(2)
                    actualizar = col_btn1.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    eliminar = col_btn2.form_submit_button("🗑️ Eliminar Prenda", use_container_width=True)

                    if actualizar:
                        datos_mod = {
                            "ID": nuevo_id,
                            "Producto": nuevo_nombre,
                            "Categoria": nueva_categoria,
                            "talla": nueva_talla,
                            "color": nuevo_color,
                            "cantidad": nueva_cantidad,
                            "alerta": nueva_alerta,
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

    elif menu == "configuracion":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">⚙️ Configuración del Sistema</div>
    <div class="page-subtitle">Gestiona y personaliza las opciones maestras de categorías, tallas y colores. Haz clic en guardar al terminar.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)

        # CATEGORÍAS
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

        # TALLAS
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

        # COLORES
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
                    st.session_state.edit_cats, 
                    st.session_state.edit_tallas, 
                    st.session_state.edit_colores
                )
                if exito:
                    st.session_state.categorias_maestras = list(st.session_state.edit_cats)
                    st.session_state.tallas_maestras = list(st.session_state.edit_tallas)
                    st.session_state.colores_maestros = list(st.session_state.edit_colores)
                    st.success("¡Configuración guardada en GitHub exitosamente!")
                    st.rerun()
