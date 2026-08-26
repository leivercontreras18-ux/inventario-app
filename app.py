import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="👕", layout="wide"
)

# --- DISEÑO UI (ESTILO GLASSMORPHISM & SIDEBAR COMPACTA) ---
st.markdown(
    """
    <style>
    .stApp { 
        background: linear-gradient(rgba(15, 23, 42, 0.4), rgba(15, 23, 42, 0.7)), 
                    url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: #fafafa !important; 
    }
    
    /* ANCHO Y ESTILO DE LA BARRA LATERAL REDUCIDO */
    section[data-testid="stSidebar"] { 
        width: 240px !important;
        background-color: rgba(18, 18, 22, 0.92) !important; 
        border-right: 1px solid #27272a; 
        backdrop-filter: blur(10px); 
    }
    section[data-testid="stSidebar"] * { color: #f4f4f5 !important; }
    
    .hero-banner {
        background: rgba(24, 24, 27, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); 
        padding: 35px; border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); margin-bottom: 30px;
    }
    .hero-title { font-size: 34px; font-weight: 700; color: #ffffff !important; margin-bottom: 8px; }
    .hero-subtitle { font-size: 15px; color: #a1a1aa !important; }
    .metric-card {
        background: rgba(24, 24, 27, 0.75); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px; border-radius: 16px; text-align: center;
    }
    .metric-value { font-size: 36px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
    .metric-label { font-size: 11px; color: #71717a !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; }
    
    /* USUARIO COMPACTO */
    .user-badge { 
        background: rgba(24, 24, 27, 0.8); 
        padding: 12px 14px; 
        border-radius: 12px; 
        border: 1px solid #27272a; 
        margin-bottom: 15px; 
    }
    .user-status-title { font-size: 8px; color: #71717a; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 4px; }
    .user-content { display: flex; align-items: center; gap: 10px; }
    .status-dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
    .user-name { font-size: 15px; font-weight: 600; color: #fafafa; }

    /* ESTILOS DE ENTRADAS Y BOTONES */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.06) !important; 
        color: #ffffff !important; 
        border: 1px solid rgba(255, 255, 255, 0.15) !important; 
        border-radius: 12px !important; 
        backdrop-filter: blur(8px);
        padding: 12px !important;
    }
    .stTextInput input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; 
        color: #ffffff !important;
        font-weight: 600; 
        border-radius: 10px; 
        border: none !important; 
        padding: 8px 16px;
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important; 
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.5);
    }
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

  # PANTALLA 1: PORTADA PRINCIPAL
  if st.session_state.pantalla == "portada":
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      st.markdown("<br><br>", unsafe_allow_html=True)
      st.markdown(
          """
            <div style="
                background: rgba(18, 24, 38, 0.65); 
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                padding: 45px 30px; 
                border-radius: 24px; 
                border: 1px solid rgba(255, 255, 255, 0.12); 
                text-align: center;
                box-shadow: 0 25px 50px rgba(0,0,0,0.6);
            ">
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
                    <div style="
                        width: 70px; height: 70px; 
                        background: rgba(255, 255, 255, 0.1); 
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: 900; color: #38bdf8;
                        box-shadow: 0 0 25px rgba(56, 189, 248, 0.4);
                    ">
                        L
                    </div>
                </div>
                <div style="color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: 5px; margin-bottom: 4px;">
                    LEWIN
                </div>
                <div style="color: #38bdf8; font-size: 14px; text-transform: uppercase; letter-spacing: 4px; font-weight: 600; margin-bottom: 10px;">
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

  # PANTALLA 2: FORMULARIO DE LOGIN
  elif st.session_state.pantalla == "login":
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
      st.markdown("<br>", unsafe_allow_html=True)

      st.markdown(
          """
            <div style="
                background: rgba(18, 24, 38, 0.6); 
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                padding: 30px 25px 10px 25px; 
                border-radius: 24px 24px 0px 0px; 
                border: 1px solid rgba(255, 255, 255, 0.12); 
                border-bottom: none;
                text-align: center;
                box-shadow: 0 25px 50px rgba(0,0,0,0.5);
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
            st.error(
                "⚠️ Usuario o contraseña incorrectos. Por favor verifícalos."
            )
  st.stop()

# --- 2. FLUJO PRINCIPAL CUANDO YA ESTÁ AUTENTICADO ---
else:
  usuario_formateado = st.session_state.usuario_actual.capitalize()
  st.sidebar.markdown(
      f"""
        <div class="user-badge">
            <div class="user-status-title">En línea</div>
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
    st.session_state.pantalla = "portada"
    st.rerun()

  st.sidebar.markdown(
      "<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.1);'>"
      "<p style='font-size:11px; color:#a1a1aa; text-transform:uppercase;"
      " letter-spacing:1px; margin-bottom:5px;'>Navegación</p>",
      unsafe_allow_html=True,
  )

  df = st.session_state.inventario

  menu = st.sidebar.selectbox(
      "Navegación del Sistema",
      [
          "📊 Estado de Existencias",
          "➕ Registrar Prenda",
          "✏️ Modificar / Eliminar Prenda",
      ],
      label_visibility="collapsed",
  )

  if menu == "📊 Estado de Existencias":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">👕 Panel Principal // Lewin Boutique</div>
                <div class="hero-subtitle">Control general de stock y monitoreo en tiempo real.</div>
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

  elif menu == "➕ Registrar Prenda":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">➕ Registro de Nuevas Prendas</div>
                <div class="hero-subtitle">Añade artículos al catálogo local.</div>
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

  elif menu == "✏️ Modificar / Eliminar Prenda":
    st.markdown(
        """
            <div class="hero-banner">
                <div class="hero-title">✏️ Modificar o Eliminar Prenda</div>
                <div class="hero-subtitle">Selecciona una prenda existente para actualizar sus datos o borrarla.</div>
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
