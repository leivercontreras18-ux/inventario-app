import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- DISEÑO UI (ESTILO MODERN BOUTIQUE & MINIMALISTA) ---
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
    
    /* BARRA LATERAL ELEGANTE */
    section[data-testid="stSidebar"] { 
        width: 240px !important;
        background: rgba(13, 18, 30, 0.85) !important; 
        border-right: 1px solid rgba(212, 175, 55, 0.15); 
        backdrop-filter: blur(20px); 
    }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    
    /* ENCABEZADO LIMPIO SIN BLOQUE GRANDE */
    .page-header {
        margin-bottom: 25px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 15px;
    }
    .page-title { font-size: 28px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
    .page-subtitle { font-size: 14px; color: #94a3b8 !important; margin-top: 4px; }
    
    /* TARJETAS DE MÉTRICAS SUTILES */
    .metric-card {
        background: rgba(18, 24, 38, 0.4); 
        backdrop-filter: blur(12px); 
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 20px; border-radius: 14px; text-align: center;
    }
    .metric-value { font-size: 32px; font-weight: 800; color: #d4af37 !important; margin-top: 6px; }
    .metric-label { font-size: 10px; color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }
    
    /* TARJETA DE USUARIO MINIMALISTA */
    .user-profile { 
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(255, 255, 255, 0.02)); 
        padding: 14px 16px; 
        border-radius: 14px; 
        border: 1px solid rgba(212, 175, 55, 0.3); 
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .user-avatar {
        width: 36px; height: 36px;
        background: #d4af37;
        color: #0d121e;
        font-weight: 800;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    }
    .user-info-title { font-size: 9px; color: #d4af37; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }
    .user-info-name { font-size: 14px; font-weight: 600; color: #ffffff; }

    /* BOTONES LATERALES ESTILO PASTILLA */
    .stSidebar .stButton>button {
        background: transparent !important; 
        color: #cbd5e1 !important;
        font-weight: 500; 
        font-size: 13px;
        border-radius: 12px; 
        border: 1px solid transparent !important; 
        padding: 10px 14px;
        text-align: left;
        margin-bottom: 6px;
        width: 100%;
        transition: all 0.25s ease;
    }
    .stSidebar .stButton>button:hover { 
        background: rgba(255, 255, 255, 0.06) !important; 
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px);
    }

    /* MENSAJE DE ESTADO LIMPIO */
    div.stAlert {
        background: rgba(18, 24, 38, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: #cbd5e1 !important;
        border-radius: 12px !important;
    }
    div.stAlert * { color: #cbd5e1 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ESTADOS DE LA APLICACIÓN ---
USUARIOS = {"leiver": "natsudraghonil", "winderly": "coromoto"}

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
  st.session_state.usuario_actual = ""
if "pantalla" not in st.session_state:
  st.session_state.pantalla = "portada"
if "menu_activo" not in st.session_state:
  st.session_state.menu_activo = "existencias"
if "inventario" not in st.session_state:
  st.session_state.inventario = pd.DataFrame(
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

# --- 1. FLUJO DE NO AUTENTICADO ---
if not st.session_state.autenticado:

  if st.session_state.pantalla == "portada":
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      st.markdown("<br><br>", unsafe_allow_html=True)
      st.markdown(
          """
            <div style="
                background: rgba(18, 24, 38, 0.6); 
                backdrop-filter: blur(16px);
                padding: 45px 30px; 
                border-radius: 20px; 
                border: 1px solid rgba(212, 175, 55, 0.2); 
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            ">
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
                    <div style="
                        width: 70px; height: 70px; 
                        background: rgba(212, 175, 55, 0.1); 
                        border: 1px solid rgba(212, 175, 55, 0.4);
                        border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: 900; color: #d4af37;
                    ">
                        L
                    </div>
                </div>
                <div style="color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: 5px; margin-bottom: 4px;">
                    LEWIN
                </div>
                <div style="color: #d4af37; font-size: 14px; text-transform: uppercase; letter-spacing: 4px; font-weight: 600; margin-bottom: 10px;">
                    Boutique
                </div>
                <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 2px;">
                    Sistema Privado
                </div>
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
                background: rgba(18, 24, 38, 0.6); 
                backdrop-filter: blur(16px);
                padding: 30px 25px 10px 25px; 
                border-radius: 20px 20px 0px 0px; 
                border: 1px solid rgba(212, 175, 55, 0.2); 
                border-bottom: none;
                text-align: center;
            ">
                <div style="font-size: 22px; font-weight: 600; color: #ffffff; margin-bottom: 4px;">
                    Acceso al Sistema
                </div>
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">
                    Introduce tus credenciales para continuar
                </div>
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

# --- 2. FLUJO PRINCIPAL CUANDO YA ESTÁ AUTENTICADO ---
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
      "<hr style='margin: 25px 0 15px 0; border-color: rgba(255,255,255,0.06);'>"
      "",
      unsafe_allow_html=True,
  )

  if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.session_state.pantalla = "portada"
    st.rerun()

  df = st.session_state.inventario
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

    if not df.empty:
      total_prendas = len(df)
      stock_total = (
          df["cantidad"].sum() if "cantidad" in df.columns else 0
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

      st.markdown("<br>", unsafe_allow_html=True)
      st.subheader("📋 Registro Actual de Inventario")
      st.dataframe(df, use_container_width=True)
    else:
      st.info("No hay prendas registradas todavía.")

  elif menu == "registrar":
    st.markdown(
        """
            <div class="page-header">
                <div class="page-title">Registro de Nuevas Prendas</div>
                <div class="page-subtitle">Añade artículos al catálogo local.</div>
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
          nuevo_registro = pd.DataFrame([{
              "ID": sku,
              "Producto": nombre,
              "Categoria": categoria,
              "talla": talla,
              "color": color,
              "cantidad": cantidad,
              "alerta": alerta,
          }])
          st.session_state.inventario = pd.concat(
              [st.session_state.inventario, nuevo_registro], ignore_index=True
          )
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

      fila_idx = df[df["ID"].astype(str) == id_seleccionado].index[0]
      prenda_actual = df.loc[fila_idx]

      with st.form("form_editar"):
        nuevo_id = st.text_input("ID", value=str(prenda_actual["ID"]))
        nuevo_nombre = st.text_input(
            "Producto", value=str(prenda_actual["Producto"])
        )
        nueva_categoria = st.text_input(
            "Categoria", value=str(prenda_actual["Categoria"])
        )
        nueva_talla = st.text_input("talla", value=str(prenda_actual["talla"]))
        nuevo_color = st.text_input("color", value=str(prenda_actual["color"]))
        nueva_cantidad = st.number_input(
            "cantidad", min_value=0, value=int(prenda_actual["cantidad"]), step=1
        )
        nueva_alerta = st.number_input(
            "alerta de stock",
            min_value=0,
            value=int(prenda_actual["alerta"]),
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
          st.session_state.inventario.loc[fila_idx, :] = [
              nuevo_id,
              nuevo_nombre,
              nueva_categoria,
              nueva_talla,
              nuevo_color,
              int(nueva_cantidad),
              int(nueva_alerta),
          ]
          st.success("¡Prenda actualizada correctamente!")
          st.rerun()

        if eliminar:
          st.session_state.inventario = (
              st.session_state.inventario.drop(fila_idx)
              .reset_index(drop=True)
          )
          st.success("¡Prenda eliminada del sistema!")
          st.rerun()
    else:
      st.info("No hay registros disponibles para modificar.")
