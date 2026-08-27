import json
from github import Github
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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

# --- CARGAR INVENTARIO (SUPABASE) Y CONFIGURACIÓN (GITHUB) CON CACHÉ ---
@st.cache_data(ttl=30)
def cargar_datos_completos():
    cats_default = ["Vestidos", "Blusas", "Pantalones", "Jeans", "Chaquetas", "Calzado", "Accesorios"]
    tallas_default = ["XS", "S", "M", "L", "XL", "Única"]
    colores_default = ["Negro", "Blanco", "Beige", "Rojo", "Azul", "Rosa", "Verde"]
    
    df = pd.DataFrame(columns=["ID", "Producto", "Categoria", "talla", "color", "cantidad", "alerta"])
    cats, tallas, colores = cats_default, tallas_default, colores_default

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
        config_data = {"categorias": cats, "tallas": tallas, "colores": colores}
        contenido = json.dumps(config_data, indent=4, ensure_ascii=False)
        try:
            file = repo.get_contents("config.json", ref="main")
            repo.update_file(file.path, "Actualización automática", contenido, file.sha, branch="main")
        except Exception:
            repo.create_file("config.json", "Creación inicial", contenido, branch="main")
        cargar_config_github.clear()
        cargar_datos_completos.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar en GitHub: {e}")
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
        if "inventario_local" not in st.session_state:
            st.session_state.inventario_local = pd.DataFrame(columns=["ID", "Producto", "Categoria", "talla", "color", "cantidad", "alerta"])
        st.session_state.inventario_local = pd.concat([st.session_state.inventario_local, nuevo_df], ignore_index=True)
        cargar_datos_completos.clear()
        return True

# --- COMPONENTE DE COPIAR AL PORTAPAPELES ---
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
            setTimeout(function() {{
                feedback.style.opacity = '0';
            }}, 1500);
        }}).catch(function(err) {{
            console.error('Error al copiar: ', err);
        }});
    }}
    </script>
    """
    components.html(component_code, height=65)

# --- PORTADA PREMIUM INTERACTIVA (HTML / CSS) ---
def render_portada_premium():
    html_portada = """
    <div style="
        background: radial-gradient(circle at 75% 50%, #1e1b24 0%, #0c0a12 60%, #030206 100%);
        color: #ffffff;
        font-family: 'Montserrat', sans-serif;
        padding: 40px 6%;
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.8);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 520px;
        box-sizing: border-box;
    ">
        <!-- Encabezado Portada -->
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
            <div style="font-weight: 700; letter-spacing: 2px; font-size: 1.1rem; font-family: 'Cinzel', serif;">LEWIN <span style="font-weight:300; color:#a0a0ab;">/ BOUTIQUE</span></div>
            <div style="display: flex; gap: 25px; font-size: 0.75rem; letter-spacing: 1.5px; text-transform: uppercase;">
                <span style="cursor:pointer; color:#f472b6;">Inicio</span>
                <span style="cursor:pointer; color:#a0a0ab;">Colecciones</span>
                <span style="cursor:pointer; color:#a0a0ab;">Editorial</span>
            </div>
        </div>

        <!-- Bloque Central -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 30px; gap: 20px;">
            <!-- Textos -->
            <div style="max-width: 45%; z-index: 2;">
                <h1 style="font-size: 3.2rem; font-weight: 700; line-height: 1.1; margin-bottom: 15px; font-family: 'Cinzel', serif; letter-spacing: -1px;">
                    Minimal<br>Garments
                </h1>
                <p style="color: #a0a0ab; font-size: 0.9rem; line-height: 1.6; margin-bottom: 25px;">
                    Texturas seleccionadas y cortes contemporáneos urbanos. Eleva el valor visual de tu marca gestionando colecciones exclusivas desde tu ecosistema premium.
                </p>
                <a href="#inventario-seccion" style="
                    display: inline-block;
                    background-color: #db2777;
                    color: #ffffff;
                    text-decoration: none;
                    padding: 12px 30px;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    font-weight: 600;
                    border-radius: 4px;
                    box-shadow: 0 4px 15px rgba(219, 39, 119, 0.4);
                ">Ver Inventario</a>
            </div>
            
            <!-- Imagen Flotante de Ropa con Reflejo -->
            <div style="width: 50%; display: flex; justify-content: center; align-items: center; position: relative;">
                <img src="https://unsplash.com" 
                     alt="Prenda Principal" 
                     style="
                        max-width: 75%; 
                        height: auto; 
                        filter: drop-shadow(0px 15px 30px rgba(0,0,0,0.9));
                        -webkit-box-reflect: below -15px linear-gradient(transparent 65%, rgba(255,255,255,0.15));
                     ">
            </div>
        </div>

        <!-- Indicador de Destacados Inferiores -->
        <div style="margin-top: 40px; display: flex; flex-direction: column; gap: 8px;">
            <span style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; color: #666;">Modelos Destacados</span>
            <div style="display: flex; gap: 40px;">
                <div style="font-size: 0.8rem;"><b style="color: #db2777;">$85.00</b> <span style="color: #a0a0ab; margin-left: 5px;">Gris Oxford</span></div>
                <div style="font-size: 0.8rem;"><b style="color: #db2777;">$95.00</b> <span style="color: #a0a0ab; margin-left: 5px;">Negro Mate</span></div>
            </div>
        </div>
    </div>
    """
    components.html(html_portada, height=560, scrolling=False)

# --- RENDERIZADO DE LA INTERFAZ EN STREAMLIT ---

# 1. Portada Desplegable al inicio de la Web
