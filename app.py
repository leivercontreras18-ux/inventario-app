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

def cargar_inventario():
    if supabase:
        try:
            res = supabase.table("inventario").select("*").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                df = df.rename(
                    columns={
                        "id": "ID",
                        "producto": "Producto",
                        "categoria": "Categoria",
                    }
                )
            return df
        except Exception:
            pass
    return st.session_state.get(
        "inventario_local",
        pd.DataFrame(
            columns=[
                "ID",
                "Producto",
                "Categoria",
                "talla",
                "color",
                "cantidad",
                "alerta",
            ]
        ),
    )

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
            return True
        except Exception as e:
            st.error(f"Error al guardar en la nube: {e}")
            return False
    else:
        nuevo_df = pd.DataFrame([nueva_prenda])
        st.session_state.inventario_local = pd.concat(
            [st.session_state.inventario_local, nuevo_df], ignore_index=True
        )
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
            supabase.table("inventario").eq("id", id_prenda).update(datos_db).execute()
            return True
        except Exception as e:
            st.error(f"Error al actualizar: {e}")
            return False
    else:
        df = st.session_state.inventario_local
        idx = df[df["ID"].astype(str) == str(id_prenda)].index[0]
        for col, val in datos_actualizados.items():
            df.loc[idx, col] = val
        return True

def eliminar_prenda(id_prenda):
    if supabase:
        try:
            supabase.table("inventario").delete().eq("id", id_prenda).execute()
            return True
        except Exception as e:
            st.error(f"Error al eliminar: {e}")
            return False
    else:
        df = st.session_state.inventario_local
        st.session_state.inventario_local = df[
            df["ID"].astype(str) != str(id_prenda)
        ].reset_index(drop=True)
        return True

# --- DISEÑO UI ADAPTADO Y TIPOGRAFÍAS DE LUJO ---
st.markdown(
    """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500&display=swap');

<style>
.stApp { 
    background: linear-gradient(rgba(10, 12, 16, 0.78), rgba(10, 12, 16, 0.88)), 
                url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1920&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    color: #f8fafc !important; 
}

header[data-testid="stHeader"] { background: transparent !important; }

section[data-testid="stSidebar"] { 
    width: 240px !important;
    background: rgba(16, 18, 23, 0.94) !important; 
    border-right: 1px solid rgba(255, 255, 255, 0.08); 
    backdrop-filter: blur(25px); 
}
section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

div[data-baseweb="input"] {
    background-color: #1a1d24 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #c99846 !important;
}
div[data-baseweb="input"] input {
    color: #ffffff !important;
    font-size: 13px !important;
}

div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #2b2e36 0%, #4a3e2c 50%, #8c6d3b 100%) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid rgba(201, 152, 70, 0.3) !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #353945 0%, #5c4d37 50%, #a68247 100%) !important;
    transform: translateY(-1px) !important;
}

.page-header { margin-bottom: 25px; padding-bottom: 10px; }
.page-title { font-size: 32px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
.page-subtitle { font-size: 14px; color: #94a3b8 !important; margin-top: 4px; }

.section-title { font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
.section-subtitle { font-size: 12px; color: #94a3b8; margin-bottom: 15px; }

.metric-card {
    background: rgba(20, 23, 30, 0.75); 
    backdrop-filter: blur(20px); 
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 20px; border-radius: 16px; text-align: left;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5);
    height: 100%;
}
.metric-value { font-size: 32px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
.metric-label { font-size: 11px; color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }

.user-profile { 
    background: rgba(255, 255, 255, 0.03); 
    padding: 14px 16px; border-radius: 14px; 
    border: 1px solid rgba(212, 175, 55, 0.25); margin-bottom: 20px;
    display: flex; align-items: center; gap: 12px;
}
.user-avatar {
    width: 36px; height: 36px; background: #d4af37; color: #0d121e;
    font-weight: 800; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 15px; box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
}
.user-info-title { font-size: 9px; color: #d4af37; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }
.user-info-name { font-size: 14px; font-weight: 600; color: #ffffff; }

.card-container {
    background: rgba(20, 22, 28, 0.88);
    backdrop-filter: blur(25px);
    padding: 35px 30px 25px 30px;
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
    box-shadow: 0 30px 60px rgba(0,0,0,0.8);
}
.social-btn-container {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 18px;
}
.social-btn {
    width: 48px;
    height: 48px;
    background: #181a20;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}
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
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "portada"
if "menu_activo" not in st.session_state:
    st.session_state.menu_activo = "existencias"
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

# Logotipo estilizado con tipografía refinada (Cinzel + Montserrat)
LOGO_HTML = """
<div style="text-align: center; margin-bottom: 12px;">
    <svg width="68" height="68" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 6px 10px rgba(0,0,0,0.6)); margin-bottom: 4px;">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#00c6ff" />
          <stop offset="50%" stop-color="#7b2cbf" />
          <stop offset="100%" stop-color="#0077b6" />
        </linearGradient>
        <linearGradient id="grad2" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#7209b7" />
          <stop offset="100%" stop-color="#4cc9f0" />
        </linearGradient>
      </defs>
      <circle cx="50" cy="22" r="10" fill="url(#grad1)" />
      <path d="M35 32 C 42 35, 48 42, 50 55 C 52 42, 58 35, 65 32 C 72 29, 78 36, 72 44 C 65 52, 58 60, 50 72 C 42 60, 35 52, 28 44 C 22 36, 28 29, 35 32 Z" fill="url(#grad1)" />
      <path d="M48 68 C 55 75, 68 82, 75 75 C 82 68, 75 55, 65 50 C 60 48, 55 52, 53 58 Z" fill="url(#grad2)" />
    </svg>
    <div style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 26px; letter-spacing: 4px; color: #ffffff; line-height: 1.1;">LEWIN</div>
    <div style="font-family: 'Montserrat', sans-serif; font-weight: 300; font-size: 10px; letter-spacing: 6px; color: #94a3b8; text-transform: uppercase; margin-top: 2px;">boutique</div>
</div>
"""

# --- 1. FLUJO DE LOGIN / PORTADA ---
if not st.session_state.autenticado:
    if st.session_state.pantalla == "portada":
        col1, col2, col3 = st.columns([1, 1.25, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(LOGO_HTML, unsafe_allow_html=True)

            st.markdown(
                """
<div class="card-container" style="padding-top: 15px !important;">
    <div style="font-family: 'Montserrat', sans-serif; font-size: 16px; font-weight: 500; color: #ffffff; margin-bottom: 2px;">
        Control de Inventario
    </div>
    <div style="font-family: 'Montserrat', sans-serif; color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin-bottom: 10px;">
        Sistema Privado
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In  →", use_container_width=True):
                st.session_state.pantalla = "login"
                st.rerun()

            st.markdown(
                """
<div style="margin-top: 25px; color: #5a6270; font-size: 11px; display: flex; align-items: center; justify-content: center; gap: 10px;">
    <div style="flex:1; height:1px; background: rgba(255,255,255,0.08);"></div>
    or continue with
    <div style="flex:1; height:1px; background: rgba(255,255,255,0.08);"></div>
</div>

<div class="social-btn-container">
    <div class="social-btn">
        <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"/><path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"/><path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 10.8 0 12.5s.7 2.8 1.9 5.2l3.7-2.9z"/><path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16C3.7 19.7 7.5 22.3 12 22.3z"/></svg>
    </div>
    <div class="social-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
    </div>
    <div class="social-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#0077b5"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

    elif st.session_state.pantalla == "login":
        col1, col2, col3 = st.columns([1, 1.25, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(LOGO_HTML, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            with st.form("form_login_tailwind"):
                st.markdown(
                    "<p style='color: #94a3b8; font-size: 11px; font-weight: 500;"
                    " margin-bottom: 4px; text-align: left;'>✉️ Email Address</p>",
                    unsafe_allow_html=True,
                )
                usuario_input = st.text_input(
                    "Usuario",
                    placeholder="Enter your email",
                    label_visibility="collapsed",
                )

                st.markdown(
                    "<p style='color: #94a3b8; font-size: 11px; font-weight: 500;"
                    " margin-bottom: 4px; margin-top: 10px; text-align: left;'>🔒 Password</p>",
                    unsafe_allow_html=True,
                )
                clave_input = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Enter your password",
                    label_visibility="collapsed",
                )

                st.markdown(
                    "<div style='text-align: right; margin-top: -5px; margin-bottom:"
                    " 15px;'><a style='color: #e0a346; font-size: 11px;"
                    " text-decoration: none;' href='#'>Forgot Password?</a></div>",
                    unsafe_allow_html=True,
                )

                col_f1, col_f2 = st.columns(2)
                boton_enviar = col_f1.form_submit_button(
                    "Sign In →", use_container_width=True
                )
                boton_volver = col_f2.form_submit_button(
                    "Volver", use_container_width=True
                )

                if boton_volver:
                    st.session_state.pantalla = "portada"
                    st.rerun()

                if boton_enviar:
                    if (
                        usuario_input in USUARIOS
                        and USUARIOS[usuario_input] == clave_input
                    ):
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = usuario_input
                        st.rerun()
                    else:
                        st.error("⚠️ Usuario o contraseña incorrectos.")

    st.stop()

# --- 2. PANEL PRINCIPAL ---
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
        "<p style='font-size:10px; color:#64748b; text-transform:uppercase;"
        " letter-spacing:1.5px; font-weight:700; margin: 12px 0 6px 4px;'>Menú"
        " Principal</p>",
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

    st.sidebar.markdown(
        "<hr style='margin: 25px 0 15px 0; border-color:"
        " rgba(255,255,255,0.06);'>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.pantalla = "portada"
        st.rerun()

    df = cargar_inventario()
    menu = st.session_state.menu_activo

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

        st.markdown(
            """
<div class="section-title">Visión General del Inventario</div>
<div class="section-subtitle">Resumen general de métricas y existencias.</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
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

        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            st.markdown(
                """
<div class="section-title">📋 Registro Actual de Inventario</div>
""",
                unsafe_allow_html=True,
            )
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay prendas registradas todavía en el sistema.")

    elif menu == "registrar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">Registro de Nuevas Prendas</div>
    <div class="page-subtitle">Añade artículos al catálogo de la boutique.</div>
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
                    nueva_prenda = {
                        "ID": sku.strip(),
                        "Producto": nombre.strip(),
                        "Categoria": categoria,
                        "talla": talla,
                        "color": color.strip(),
                        "cantidad": cantidad,
                        "alerta": alerta,
                    }
                    if guardar_prenda(nueva_prenda):
                        st.success("¡Prenda guardada con éxito!")
                        st.rerun()

    elif menu == "modificar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">Modificar o Eliminar Prenda</div>
    <div class="page-subtitle">Selecciona una prenda existente para actualizar sus datos o borrarla.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if not df.empty:
            lista_ids = df["ID"].astype(str).tolist()
            id_seleccionado = st.selectbox("Seleccione el ID de la prenda", lista_ids)

            fila_data = df[df["ID"].astype(str) == id_seleccionado].iloc[0]

            with st.form("form_editar"):
                nuevo_id = st.text_input("ID", value=str(fila_data["ID"]))
                nuevo_nombre = st.text_input("Producto", value=str(fila_data["Producto"]))
                nueva_categoria = st.text_input(
                    "Categoria", value=str(fila_data["Categoria"])
                )
                nueva_talla = st.text_input("talla", value=str(fila_data["talla"]))
                nuevo_color = st.text_input("color", value=str(fila_data["color"]))
                nueva_cantidad = st.number_input(
                    "cantidad", min_value=0, value=int(fila_data["cantidad"]), step=1
                )
                nueva_alerta = st.number_input(
                    "alerta de stock",
                    min_value=0,
                    value=int(fila_data["alerta"]),
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
