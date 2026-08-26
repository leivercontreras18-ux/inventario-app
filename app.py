import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- CARGA DE TAILWIND CSS & ESTILOS BASE ---
st.markdown(
    """
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
    /* Ocultar elementos nativos innecesarios de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilos personalizados para Inputs de Streamlit compatibles con el diseño Dark */
    div[data-baseweb="input"] {
        background-color: rgba(32, 37, 48, 0.6) !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: #e2e8f0 !important;
    }
    div[data-baseweb="input"] input {
        color: #e2e8f0 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* Estilo para Botones primarios en Streamlit */
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
        background: linear-gradient(to right, #2c2724, #4a3b32, #2c2724) !important;
        color: #ffffff !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        font-weight: 700 !important;
        padding: 0.85rem 1rem !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        filter: brightness(1.15) !important;
        transform: translateY(-1px) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
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


# --- ESTADOS DE SESIÓN ---
USUARIOS = {"leiver": "natsudraghonil", "winderly": "coromoto"}

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
  st.session_state.usuario_actual = ""
if "pantalla" not in st.session_state:
  st.session_state.pantalla = "login"
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

# --- 1. INTERFAZ DE LOGIN (TAILWIND HTML INTEGRADO) ---
if not st.session_state.autenticado:
  col_left, col_center, col_right = st.columns([1, 2.2, 1])

  with col_center:
    # Encabezado del Card, Logotipo LW en relieve y Fondos
    st.markdown(
        """
        <div class="relative flex flex-col items-center justify-center font-sans antialiased text-center pt-6">
          <!-- LOGOTIPO GEOMÉTRICO LW -->
          <div class="mb-6 drop-shadow-[0_10px_15px_rgba(255,255,255,0.07)] hover:scale-105 transition duration-300">
            <svg width="100" height="110" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 20 L42 20 L42 70 L55 70 L55 85 L20 85 Z" fill="url(#metal-gradient)" stroke="#555" stroke-width="0.5"/>
              <path d="M60 20 L75 20 L80 65 L85 20 L98 20 L90 85 L75 85 L70 45 L65 85 L52 85 Z" fill="url(#metal-gradient)" stroke="#555" stroke-width="0.5"/>
              <path d="M42 20 L42 70 L20 85" stroke="#fff" stroke-width="0.5" opacity="0.3"/>
              <path d="M70 45 L65 85 L52 85" stroke="#000" stroke-width="0.4" opacity="0.4"/>
              <defs>
                <linearGradient id="metal-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#94a3b8" />
                  <stop offset="35%" stop-color="#cbd5e1" />
                  <stop offset="50%" stop-color="#475569" />
                  <stop offset="65%" stop-color="#e2e8f0" />
                  <stop offset="100%" stop-color="#1e293b" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <!-- TARJETA GLASSMORPHISM HEADER -->
          <div class="w-full rounded-t-3xl border border-white/[0.08] bg-[#161a22]/80 p-6 pb-2 text-center backdrop-blur-xl">
            <h1 class="text-3xl font-medium tracking-wide text-white">
              Welcome <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600 font-semibold">Lewin</span>
            </h1>
            <p class="mt-2 text-xs font-semibold tracking-wider text-amber-500/80 uppercase">
              Sistema privado de LEWIN BOUTIQUE
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Formulario de credenciales conectado a Streamlit Python
    with st.form("form_login_tailwind"):
      st.markdown(
          "<p class='text-xs font-bold text-slate-400 tracking-wide uppercase"
          " pl-1 mb-1'>Usuario</p>",
          unsafe_allow_html=True,
      )
      usuario_input = st.text_input(
          "Usuario", placeholder="✉️ Entrar usuario", label_visibility="collapsed"
      )

      st.markdown(
          "<p class='text-xs font-bold text-slate-400 tracking-wide uppercase"
          " pl-1 mt-3 mb-1'>Contraseña</p>",
          unsafe_allow_html=True,
      )
      clave_input = st.text_input(
          "Contraseña",
          type="password",
          placeholder="🔒 Entrar contraseña",
          label_visibility="collapsed",
      )

      st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)
      boton_enviar = st.form_submit_button(
          "Sign In  ➔", use_container_width=True
      )

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

    # Pie de página y Redes Sociales del Card
    st.markdown(
        """
        <div class="w-full rounded-b-3xl border-x border-b border-white/[0.08] bg-[#161a22]/80 p-6 pt-0 text-center backdrop-blur-xl">
          <div class="relative my-4 flex items-center justify-center">
            <div class="w-full border-t border-white/[0.06]"></div>
            <span class="absolute bg-[#161a22] px-3 text-[11px] font-bold uppercase tracking-widest text-slate-500">In continue with</span>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <button type="button" class="flex items-center justify-center rounded-xl border border-white/[0.05] bg-[#202530]/40 py-2.5 hover:bg-[#202530]/80 transition">
              <span class="text-lg">🌐</span>
            </button>
            <button type="button" class="flex items-center justify-center rounded-xl border border-white/[0.05] bg-[#202530]/40 py-2.5 hover:bg-[#202530]/80 transition">
              <span class="text-lg">🐱</span>
            </button>
            <button type="button" class="flex items-center justify-center rounded-xl border border-white/[0.05] bg-[#202530]/40 py-2.5 hover:bg-[#202530]/80 transition">
              <span class="text-lg">💼</span>
            </button>
          </div>

          <p class="mt-6 text-xs text-slate-500">
            Don't have an account? <a href="#" class="font-semibold text-amber-500/80 hover:text-amber-400 transition">Sign Up</a>
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.stop()

# --- 2. PANEL PRINCIPAL DEL SISTEMA ---
else:
  usuario_formateado = st.session_state.usuario_actual.capitalize()
  inicial_usuario = usuario_formateado[0]

  st.sidebar.markdown(
      f"""
        <div class="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-amber-500/20 mb-4">
            <div class="w-9 h-9 rounded-full bg-amber-500 text-slate-900 font-extrabold flex items-center justify-center text-sm shadow-lg">
                {inicial_usuario}
            </div>
            <div>
                <div class="text-[9px] text-amber-400 font-bold uppercase tracking-wider">● Sesión Activa</div>
                <div class="text-sm font-semibold text-white">{usuario_formateado}</div>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.sidebar.markdown(
      "<p class='text-[10px] text-slate-500 uppercase tracking-widest"
      " font-bold mb-2 ml-1'>Menú Principal</p>",
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
      "<hr class='my-4 border-white/[0.06]'>", unsafe_allow_html=True
  )

  if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.rerun()

  df = cargar_inventario()
  menu = st.session_state.menu_activo

  if menu == "existencias":
    st.markdown(
        """
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-white">Panel Principal // Lewin Boutique</h1>
                <p class="text-sm text-slate-400">Control general de stock y monitoreo en tiempo real.</p>
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

    col1, col2 = st.columns(2)
    with col1:
      st.markdown(
          f"""
                <div class="p-5 rounded-2xl bg-[#161a22]/70 border border-white/[0.08] backdrop-blur-md">
                    <div class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total de Prendas / Modelos</div>
                    <div class="text-3xl font-extrabold text-amber-400 mt-2">{total_prendas}</div>
                </div>
            """,
          unsafe_allow_html=True,
      )
    with col2:
      st.markdown(
          f"""
                <div class="p-5 rounded-2xl bg-[#161a22]/70 border border-white/[0.08] backdrop-blur-md">
                    <div class="text-xs font-bold text-slate-400 uppercase tracking-wider">Stock Total Acumulado</div>
                    <div class="text-3xl font-extrabold text-amber-400 mt-2">{stock_total}</div>
                </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown("<br>", unsafe_allow_html=True)

    if not df.empty:
      st.dataframe(df, use_container_width=True)
    else:
      st.info("No hay prendas registradas todavía en el sistema.")

  elif menu == "registrar":
    st.markdown(
        """
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-white">Registro de Nuevas Prendas</h1>
                <p class="text-sm text-slate-400">Añade artículos al catálogo de la boutique.</p>
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
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-white">Modificar o Eliminar Prenda</h1>
                <p class="text-sm text-slate-400">Selecciona una prenda existente para actualizar sus datos o borrarla.</p>
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
