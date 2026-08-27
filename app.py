import os
import json
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="Lewin // Inventario Boutique",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500;600&display=swap');

/* Fondo General con Gradiente Elegante y Luces Doradas Tenues */
.stApp { 
    background: radial-gradient(circle at 20% 20%, rgba(212, 175, 55, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(184, 134, 11, 0.05) 0%, transparent 40%),
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
    border-right: 1px solid rgba(212, 175, 55, 0.2); 
    backdrop-filter: blur(25px); 
}
section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

/* Inputs estándar de Streamlit */
div[data-baseweb="input"], div[data-baseweb="select"] > div {
    background-color: rgba(25, 33, 47, 0.8) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    color: #ffffff !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: #d4af37 !important;
    box-shadow: 0 0 8px rgba(212, 175, 55, 0.3) !important;
}
div[data-baseweb="input"] input {
    color: #ffffff !important;
    font-size: 13px !important;
}

/* Efecto 3D Puerta para TODOS los botones (Ahora en Tono Dorado) */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: #18202c !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
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
    background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%);
    transform-origin: left center;
    transform: rotateY(0deg);
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease;
    z-index: -1;
    border-radius: 7px;
}

div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: #d4af37 !important;
    box-shadow: inset 20px 0 30px rgba(212, 175, 55, 0.15), 0 0 20px rgba(212, 175, 55, 0.4) !important;
    color: #ffffff !important;
}

div.stButton > button:hover::before {
    transform: rotateY(72deg);
    opacity: 0.95; 
}

div.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateZ(-30px) scale(0.95) !important;
    box-shadow: 0 0 5px rgba(212, 175, 55, 0.6) !important;
}

/* Tarjeta de Bienvenida Glassmorphism */
.hero-card {
    background: rgba(26, 34, 48, 0.65) !important;
    backdrop-filter: blur(30px) !important;
    -webkit-backdrop-filter: blur(30px) !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
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
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
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
    border: 1px solid rgba(212, 175, 55, 0.2);
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
""", unsafe_allow_html=True)

# ==========================================
# 2. PERSISTENCIA EN GITHUB VIA API
# ==========================================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN"))
REPO_OWNER = "leivercontreras18-ux"
REPO_NAME = "inventario-app"
FILE_PATH = "data/inventory_db.json"

def get_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def load_data_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    try:
        res = requests.get(url, headers=get_headers())
        if res.status_code == 200:
            content_b64 = res.json()["content"]
            import base64
            content_str = base64.b64decode(content_b64).decode("utf-8")
            data = json.loads(content_str)
            return data.get("inventario", []), data.get("configuracion", {}), res.json()["sha"]
    except Exception as e:
        st.error(f"Error al conectar con GitHub: {e}")
    
    # Datos por defecto si falla la descarga
    default_config = {
        "categorias": ["Faldas", "Vestidos", "Tops", "Pantalones"],
        "tallas": ["XS", "S", "M", "L", "XL"],
        "colores": ["Negro", "Blanco", "Rojo", "Verde", "Beige", "Dorado"]
    }
    return [], default_config, None

def save_data_to_github(inventario, configuracion, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data_to_save = {
        "inventario": inventario,
        "configuracion": configuracion
    }
    
    import base64
    json_bytes = json.dumps(data_to_save, indent=2, ensure_ascii=False).encode("utf-8")
    content_b64 = base64.b64encode(json_bytes).decode("utf-8")
    
    payload = {
        "message": "Actualización de base de datos de inventario",
        "content": content_b64
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(url, json=payload, headers=get_headers())
    if res.status_code in [200, 201]:
        st.session_state["sha"] = res.json()["content"]["sha"]
        return True
    else:
        st.error(f"Error al guardar en GitHub: {res.json().get('message')}")
        return False

# Inicialización del Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "inventario" not in st.session_state:
    inv, cfg, sha = load_data_from_github()
    st.session_state["inventario"] = inv
    st.session_state["configuracion"] = cfg
    st.session_state["sha"] = sha

# ==========================================
# 3. CONTROL DE SESIÓN (LOGIN)
# ==========================================
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="hero-card">
            <h1 style="font-family: 'Cinzel', serif; font-size: 38px; color: #ffffff; letter-spacing: 2px; margin-bottom: 5px;">LEWIN</h1>
            <p style="color: #d4af37; font-size: 11px; text-transform: uppercase; letter-spacing: 3px; font-weight: 700; margin-bottom: 25px;">Boutique Inventory Control</p>
            <p style="color: #cbd5e1; font-size: 13px;">Acceso restringido para el personal de inventario y ventas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                # Validar usuario (Credencial por defecto Leiver / 1234)
                if user.strip().lower() == "leiver" and password == "1234":
                    st.session_state["logged_in"] = True
                    st.session_state["user_name"] = "Leiver"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"""
    <div class="user-profile">
        <div class="user-avatar">{st.session_state["user_name"][0]}</div>
        <div>
            <div class="user-info-title">• SESIÓN ACTIVA</div>
            <div class="user-info-name">{st.session_state["user_name"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size: 9px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 10px;">MENÚ PRINCIPAL</div>', unsafe_allow_html=True)
    
    opcion = st.radio(
        "Navegación",
        ["📦 Existencias", "➕ Registrar Prenda", "✏️ Editar / Borrar", "⚙️ Configuración"],
        label_visibility="collapsed"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.rerun()

# ==========================================
# 5. MÓDULOS DE LA APLICACIÓN
# ==========================================

# MÓDULO 1: EXISTENCIAS
if opcion == "📦 Existencias":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📦 Existencias de Inventario</div>
        <div class="page-subtitle">Consulta y filtra el catálogo activo de prendas en tiempo real.</div>
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state["inventario"])
    
    if df.empty:
        st.info("Aún no hay prendas registradas en el catálogo. Usa el menú lateral para agregar nuevas prendas.")
    else:
        # Métricas principales
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">TOTAL UNIDADES</div>
                <div class="metric-value">{df['cantidad'].sum() if 'cantidad' in df else 0}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">MODELOS ÚNICOS</div>
                <div class="metric-value">{len(df)}</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            valor_total = (df['cantidad'] * df['precio']).sum() if ('cantidad' in df and 'precio' in df) else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">VALOR ESTIMADO</div>
                <div class="metric-value">${valor_total:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            cat_filter = st.multiselect("Filtrar por Categoría", options=st.session_state["configuracion"]["categorias"])
        with col2:
            busqueda = st.text_input("🔍 Buscar por Nombre o Referencia")

        filtered_df = df.copy()
        if cat_filter:
            filtered_df = filtered_df[filtered_df['categoria'].isin(cat_filter)]
        if busqueda:
            filtered_df = filtered_df[filtered_df['nombre'].str.contains(busqueda, case=False, na=False)]

        st.dataframe(
            filtered_df,
            column_config={
                "id": "ID",
                "nombre": "Prenda / Modelo",
                "categoria": "Categoría",
                "talla": "Talla",
                "color": "Color",
                "cantidad": "Stock",
                "precio": st.column_config.NumberColumn("Precio", format="$%.2f"),
                "fecha": "Última Actualización"
            },
            use_container_width=True,
            hide_index=True
        )

# MÓDULO 2: REGISTRAR PRENDA
elif opcion == "➕ Registrar Prenda":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">➕ Registrar Nueva Prenda</div>
        <div class="page-subtitle">Añade nuevos artículos al catálogo y sincronízalos con GitHub.</div>
    </div>
    """, unsafe_allow_html=True)

    cfg = st.session_state["configuracion"]

    with st.form("form_registro"):
        nombre = st.text_input("Nombre de la Prenda / Referencia", placeholder="Ej. Vestido Seda Noche")
        col1, col2, col3 = st.columns(3)
        with col1:
            categoria = st.selectbox("Categoría", cfg.get("categorias", []))
        with col2:
            talla = st.selectbox("Talla", cfg.get("tallas", []))
        with col3:
            color = st.selectbox("Color", cfg.get("colores", []))

        col4, col5 = st.columns(2)
        with col4:
            cantidad = st.number_input("Cantidad inicial", min_value=1, value=1, step=1)
        with col5:
            precio = st.number_input("Precio ($)", min_value=0.0, value=25.0, step=0.50)

        submit = st.form_submit_button("Guardar Prenda en Catalogó")

        if submit:
            if not nombre.strip():
                st.error("El nombre de la prenda es obligatorio.")
            else:
                nueva_prenda = {
                    "id": len(st.session_state["inventario"]) + 1,
                    "nombre": nombre,
                    "categoria": categoria,
                    "talla": talla,
                    "color": color,
                    "cantidad": cantidad,
                    "precio": precio,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state["inventario"].append(nueva_prenda)
                
                # Persistencia en GitHub
                exito = save_data_to_github(
                    st.session_state["inventario"], 
                    st.session_state["configuracion"], 
                    st.session_state["sha"]
                )
                if exito:
                    st.success("¡Prenda guardada y sincronizada en GitHub correctamente!")
                    st.rerun()

# MÓDULO 3: EDITAR / BORRAR
elif opcion == "✏️ Editar / Borrar":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">✏️ Gestionar Inventario</div>
        <div class="page-subtitle">Modifica existencias o elimina artículos obsoletos.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state["inventario"]:
        st.info("No hay prendas registradas para gestionar.")
    else:
        df = pd.DataFrame(st.session_state["inventario"])
        item_sel = st.selectbox("Selecciona una prenda para editar:", options=df['nombre'].tolist())
        
        # Encontrar item
        index_target = next((i for i, item in enumerate(st.session_state["inventario"]) if item["nombre"] == item_sel), None)
        
        if index_target is not None:
            prenda = st.session_state["inventario"][index_target]
            cfg = st.session_state["configuracion"]

            with st.form("form_edit"):
                st.write(f"**Editando ID #{prenda['id']}:** {prenda['nombre']}")
                edit_nombre = st.text_input("Nombre", value=prenda['nombre'])
                c1, c2, c3 = st.columns(3)
                with c1:
                    edit_cat = st.selectbox("Categoría", cfg["categorias"], index=cfg["categorias"].index(prenda["categoria"]) if prenda["categoria"] in cfg["categorias"] else 0)
                with c2:
                    edit_talla = st.selectbox("Talla", cfg["tallas"], index=cfg["tallas"].index(prenda["talla"]) if prenda["talla"] in cfg["tallas"] else 0)
                with c3:
                    edit_color = st.selectbox("Color", cfg["colores"], index=cfg["colores"].index(prenda["color"]) if prenda["color"] in cfg["colores"] else 0)

                c4, c5 = st.columns(2)
                with c4:
                    edit_cant = st.number_input("Cantidad", min_value=0, value=int(prenda['cantidad']))
                with c5:
                    edit_precio = st.number_input("Precio ($)", min_value=0.0, value=float(prenda['precio']))

                btn_guardar = st.form_submit_button("Actualizar Prenda")

                if btn_guardar:
                    st.session_state["inventario"][index_target] = {
                        "id": prenda["id"],
                        "nombre": edit_nombre,
                        "categoria": edit_cat,
                        "talla": edit_talla,
                        "color": edit_color,
                        "cantidad": edit_cant,
                        "precio": edit_precio,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    save_data_to_github(st.session_state["inventario"], st.session_state["configuracion"], st.session_state["sha"])
                    st.success("Cambios actualizados y sincronizados.")
                    st.rerun()

            st.markdown("---")
            if st.button("🗑️ Eliminar esta prenda"):
                st.session_state["inventario"].pop(index_target)
                save_data_to_github(st.session_state["inventario"], st.session_state["configuracion"], st.session_state["sha"])
                st.warning("Prenda eliminada correctamente.")
                st.rerun()

# MÓDULO 4: CONFIGURACIÓN
elif opcion == "⚙️ Configuración":
    st.markdown("""
    <div class="page-header">
        <div class="page-title">⚙️ Configuración del Sistema</div>
        <div class="page-subtitle">Gestiona y personaliza las opciones maestras de categorías, tallas y colores. Haz clic en guardar al terminar.</div>
    </div>
    """, unsafe_allow_html=True)

    cfg = st.session_state["configuracion"]
    col_cat, col_tal, col_col = st.columns(3)

    # Categorías
    with col_cat:
        st.markdown('<div class="section-title">📂 Categorías</div>', unsafe_allow_html=True)
        for cat in cfg.get("categorias", []):
            c1, c2 = st.columns([3, 1])
            c1.write(f"• {cat}")
            if c2.button("❌", key=f"del_cat_{cat}"):
                cfg["categorias"].remove(cat)
                st.rerun()
        
        nueva_cat = st.text_input("Nueva Categoría", key="input_nueva_cat", placeholder="Ej: Faldas")
        if st.button("➕ Agregar Categoría"):
            if nueva_cat and nueva_cat not in cfg["categorias"]:
                cfg["categorias"].append(nueva_cat)
                st.rerun()

    # Tallas
    with col_tal:
        st.markdown('<div class="section-title">📐 Tallas</div>', unsafe_allow_html=True)
        for tal in cfg.get("tallas", []):
            c1, c2 = st.columns([3, 1])
            c1.write(f"• {tal}")
            if c2.button("❌", key=f"del_tal_{tal}"):
                cfg["tallas"].remove(tal)
                st.rerun()
        
        nueva_tal = st.text_input("Nueva Talla", key="input_nueva_tal", placeholder="Ej: 30, XXL")
        if st.button("➕ Agregar Talla"):
            if nueva_tal and nueva_tal not in cfg["tallas"]:
                cfg["tallas"].append(nueva_tal)
                st.rerun()

    # Colores
    with col_col:
        st.markdown('<div class="section-title">🎨 Colores</div>', unsafe_allow_html=True)
        for col in cfg.get("colores", []):
            c1, c2 = st.columns([3, 1])
            c1.write(f"• {col}")
            if c2.button("❌", key=f"del_col_{col}"):
                cfg["colores"].remove(col)
                st.rerun()
        
        nuevo_col = st.text_input("Nuevo Color", key="input_nuevo_col", placeholder="Ej: Dorado")
        if st.button("➕ Agregar Color"):
            if nuevo_col and nuevo_col not in cfg["colores"]:
                cfg["colores"].append(nuevo_col)
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("💾 Guardar configuración en GitHub"):
        exito = save_data_to_github(st.session_state["inventario"], cfg, st.session_state["sha"])
        if exito:
            st.success("¡Configuración guardada exitosamente!")
