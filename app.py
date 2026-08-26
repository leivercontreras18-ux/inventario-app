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


# Funciones CRUD para Supabase con respaldo local
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


# --- DISEÑO UI (GLASSMORPHISM & BOUTIQUE STYLE) ---
st.markdown(
    """
    <style>
    .stApp { 
        background: linear-gradient(rgba(10, 15, 30, 0.6), rgba(10, 15, 30, 0.9)), 
                    url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #f8fafc !important; 
    }
    
    section[data-testid="stSidebar"] { 
        width: 240px !important;
        background: rgba(13, 18, 30, 0.85) !important; 
        border-right: 1px solid rgba(212, 175, 55, 0.15); 
        backdrop-filter: blur(20px); 
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    
    .page-header { margin-bottom: 25px; padding-bottom: 10px; }
    .page-title { font-size: 32px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
    .page-subtitle { font-size: 14px; color: #94a3b8 !important; margin-top: 4px; }
    
    .section-title { font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
    .section-subtitle { font-size: 12px; color: #94a3b8; margin-bottom: 15px; }
    
    .metric-card {
        background: rgba(18, 24, 38, 0.5); 
        backdrop-filter: blur(12px); 
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px; border-radius: 16px; text-align: left;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        height: 100%;
    }
    .metric-value { font-size: 32px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
    .metric-label { font-size: 11px; color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }
    
    .user-profile { 
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(255, 255, 255, 0.02)); 
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

    .stSidebar .stButton>button {
        background: transparent !important; color: #cbd5e1 !important;
        font-weight: 500; font-size: 13px; border-radius: 12px; 
        border: 1px solid transparent !important; padding: 10px 14px;
        text-align: left; margin-bottom: 6px; width: 100%; transition: all 0.25s ease;
    }
    .stSidebar .stButton>button:hover { 
        background: rgba(255, 255, 255, 0.06) !important; color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.1) !important; transform: translateX(4px);
    }

    div.stAlert {
        background: rgba(18, 24, 38, 0.5) !important;
        backdrop-filter: blur(10px) !important;
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
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      st.markdown("<br><br>", unsafe_allow_html=True)
      st.markdown(
          """
            <div style="
                background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(16px);
                padding: 45px 30px; border-radius: 20px; 
                border: 1px solid rgba(212, 175, 55, 0.2); text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            ">
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
                    <div style="
                        width: 70px; height: 70px; background: rgba(212, 175, 55, 0.1); 
                        border: 1px solid rgba(212, 175, 55, 0.4); border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: 900; color: #d4af37;
                    ">L</div>
                </div>
                <div style="color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: 5px; margin-bottom: 4px;">LEWIN</div>
                <div style="color: #d4af37; font-size: 14px; text-transform: uppercase; letter-spacing: 4px; font-weight: 600; margin-bottom: 10px;">Boutique</div>
                <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 2px;">Sistema Privado</div>
            </div>
            """,
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("Iniciar Sesión", use_container_width=True):
        st.session_state.pantalla = "login"
        st.rerun()

  elif st.session_state.pantalla == "login":
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          """
            <div style="
                background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(16px);
                padding: 30px 25px 10px 25px; border-radius: 20px 20px 0px 0px; 
                border: 1px solid rgba(212, 175, 55, 0.2); border-bottom: none; text-align: center;
            ">
                <div style="font-size: 22px; font-weight: 600; color: #ffffff; margin-bottom: 4px;">Acceso al Sistema</div>
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">Introduce tus credenciales para continuar</div>
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
            placeholder="Ingresa tu usuario",
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
            "Ingresar", use_container_width=True
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
