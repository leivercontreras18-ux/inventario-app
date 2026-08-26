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


# --- DISEÑO UI (TEXTURA DE TELA OSCURA & GLASSMORPHISM) ---
st.markdown(
    """
    <style>
    .stApp { 
        background: linear-gradient(rgba(12, 14, 18, 0.75), rgba(12, 14, 18, 0.88)), 
                    url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #f8fafc !important; 
    }
    
    section[data-testid="stSidebar"] { 
        width: 240px !important;
        background: rgba(18, 20, 26, 0.92) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.08); 
        backdrop-filter: blur(25px); 
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    
    /* Estilos de Cajas de Texto / Inputs */
    div[data-baseweb="input"] {
        background-color: #1a1d24 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"] input {
        color: #ffffff !important;
    }
    
    /* Botón estilo Degradado Dorado Metalizado */
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #2b251d 0%, #614929 50%, #aa8344 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #3d3428 0%, #7d5e35 50%, #cfa053 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.2);
    }

    .page-header { margin-bottom: 25px; padding-bottom: 10px; }
    .page-title { font-size: 32px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
    .page-subtitle { font-size: 14px; color: #94a3b8 !important; margin-top: 4px; }
    
    .section-title { font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
    .section-subtitle { font-size: 12px; color: #94a3b8; margin-bottom: 15px; }
    
    .metric-card {
        background: rgba(22, 25, 33, 0.70); 
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

    div.stAlert {
        background: rgba(22, 25, 33, 0.70) !important;
        backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #cbd5e1 !important; border-radius: 14px !important;
    }
    div.stAlert * { color: #cbd5e1 !important; }
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

# --- 1. FLUJO DE LOGIN / PORTADA ---
if not st.session_state.autenticado:
  if st.session_state.pantalla == "portada":
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
      st.markdown("<br>", unsafe_allow_html=True)
      # LOGO EXACTO (SVG 3D METALIZADO GENERADO)
      st.markdown(
          """
            <div style="text-align: center; margin-bottom: 25px;">
                <svg width="110" height="110" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="metal1" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#f1f5f9"/>
                            <stop offset="50%" stop-color="#94a3b8"/>
                            <stop offset="100%" stop-color="#334155"/>
                        </linearGradient>
                        <linearGradient id="metal2" x1="100%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#ffffff"/>
                            <stop offset="50%" stop-color="#cbd5e1"/>
                            <stop offset="100%" stop-color="#475569"/>
                        </linearGradient>
                        <linearGradient id="metal3" x1="0%" y1="100%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#1e293b"/>
                            <stop offset="50%" stop-color="#64748b"/>
                            <stop offset="100%" stop-color="#94a3b8"/>
                        </linearGradient>
                        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="12" stdDeviation="10" flood-color="#000000" flood-opacity="0.85"/>
                        </filter>
                    </defs>
                    <g filter="url(#shadow)">
                        <path d="M 90,25 L 35,55 L 35,145 L 90,175 L 90,148 L 58,130 L 58,110 L 85,110 L 85,90 L 58,90 L 58,70 L 90,52 Z" fill="url(#metal1)"/>
                        <path d="M 35,55 L 90,25 L 90,38 L 48,62 L 48,138 L 90,162 L 90,175 L 35,145 Z" fill="url(#metal2)"/>
                        <path d="M 110,25 L 165,55 L 165,145 L 110,175 L 110,148 L 142,130 L 142,70 L 110,52 Z" fill="url(#metal2)"/>
                        <path d="M 110,25 L 165,55 L 165,70 L 123,45 L 123,155 L 165,130 L 165,145 L 110,175 Z" fill="url(#metal3)"/>
                        <path d="M 123,70 L 142,82 L 142,118 L 123,130 Z" fill="#111318" opacity="0.9"/>
                    </g>
                </svg>
            </div>
            
            <div style="
                background: rgba(22, 25, 32, 0.75); backdrop-filter: blur(25px);
                padding: 35px 30px; border-radius: 24px; 
                border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
                box-shadow: 0 25px 50px rgba(0,0,0,0.7);
            ">
                <div style="color: #ffffff; font-size: 26px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px;">
                    Welcome <span style="color: #d4af37;">Back</span>
                </div>
                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 20px;">Inicia sesión para gestionar el inventario boutique</div>
            </div>
            """,
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("Ingresar al Sistema →", use_container_width=True):
        st.session_state.pantalla = "login"
        st.rerun()

  elif st.session_state.pantalla == "login":
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          """
            <div style="text-align: center; margin-bottom: 15px;">
                <svg width="90" height="90" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="metal1" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#f1f5f9"/>
                            <stop offset="50%" stop-color="#94a3b8"/>
                            <stop offset="100%" stop-color="#334155"/>
                        </linearGradient>
                        <linearGradient id="metal2" x1="100%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#ffffff"/>
                            <stop offset="50%" stop-color="#cbd5e1"/>
                            <stop offset="100%" stop-color="#475569"/>
                        </linearGradient>
                        <linearGradient id="metal3" x1="0%" y1="100%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#1e293b"/>
                            <stop offset="50%" stop-color="#64748b"/>
                            <stop offset="100%" stop-color="#94a3b8"/>
                        </linearGradient>
                        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="12" stdDeviation="10" flood-color="#000000" flood-opacity="0.85"/>
                        </filter>
                    </defs>
                    <g filter="url(#shadow)">
                        <path d="M 90,25 L 35,55 L 35,145 L 90,175 L 90,148 L 58,130 L 58,110 L 85,110 L 85,90 L 58,90 L 58,70 L 90,52 Z" fill="url(#metal1)"/>
                        <path d="M 35,55 L 90,25 L 90,38 L 48,62 L 48,138 L 90,162 L 90,175 L 35,145 Z" fill="url(#metal2)"/>
                        <path d="M 110,25 L 165,55 L 165,145 L 110,175 L 110,148 L 142,130 L 142,70 L 110,52 Z" fill="url(#metal2)"/>
                        <path d="M 110,25 L 165,55 L 165,70 L 123,45 L 123,155 L 165,130 L 165,145 L 110,175 Z" fill="url(#metal3)"/>
                        <path d="M 123,70 L 142,82 L 142,118 L 123,130 Z" fill="#111318" opacity="0.9"/>
                    </g>
                </svg>
            </div>
            <div style="
                background: rgba(22, 25, 32, 0.75); backdrop-filter: blur(25px);
                padding: 25px 25px 10px 25px; border-radius: 24px 24px 0px 0px; 
                border: 1px solid rgba(255, 255, 255, 0.1); border-bottom: none; text-align: center;
            ">
                <div style="font-size: 24px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">
                    Welcome <span style="color: #d4af37;">Back</span>
                </div>
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">Ingresa tus datos de acceso</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      with st.form("form_login"):
        st.markdown(
            "<p style='color: #cbd5e1; font-size: 12px; font-weight: 500;"
            " margin-bottom: 2px;'>Usuario</p>",
            unsafe_allow_html=True,
        )
        usuario_input = st.text_input(
            "Usuario",
            placeholder="Introduce tu usuario",
            label_visibility="collapsed",
        )

        st.markdown(
            "<p style='color: #cbd5e1; font-size: 12px; font-weight: 500;"
            " margin-bottom: 2px; margin-top: 8px;'>Contraseña</p>",
            unsafe_allow_html=True,
        )
        clave_input = st.text_input(
            "Contraseña",
            type="password",
            placeholder="••••••••••••",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        boton_enviar = col_f1.form_submit_button(
            "Entrar →", use_container_width=True
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
