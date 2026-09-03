import json
import textwrap
import uuid
from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from github import Github
from supabase import create_client

try:
    import qrcode
    QR_DISPONIBLE = True
except ImportError:
    QR_DISPONIBLE = False

try:
    from fpdf import FPDF
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

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


@st.cache_resource
def obtener_conexion_github():
    try:
        return Github(st.secrets["GITHUB_TOKEN"])
    except Exception:
        return None


@st.cache_data(ttl=60)
def cargar_config_github():
    try:
        g = obtener_conexion_github()
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
    "precio_unitario", "costo_unitario", "pagado", "medio_pago", "proveedor",
    "venta_id", "cliente", "fecha", "usuario",
]

COLUMNAS_DEUDORES = ["id", "nombre", "telefono", "saldo", "notas"]

COLUMNAS_DEUDAS_MOVIMIENTOS = [
    "id", "deudor_id", "deudor_nombre", "tipo", "descripcion", "monto",
    "medio_pago", "tasa_cambio", "fecha", "usuario",
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
            df_mov = pd.DataFrame(res.data)
            if "pagado" not in df_mov.columns:
                df_mov["pagado"] = True
            else:
                df_mov["pagado"] = df_mov["pagado"].fillna(True)
            if "medio_pago" not in df_mov.columns:
                df_mov["medio_pago"] = ""
            else:
                df_mov["medio_pago"] = df_mov["medio_pago"].fillna("")
            if "proveedor" not in df_mov.columns:
                df_mov["proveedor"] = ""
            else:
                df_mov["proveedor"] = df_mov["proveedor"].fillna("")
            if "venta_id" not in df_mov.columns:
                df_mov["venta_id"] = ""
            else:
                df_mov["venta_id"] = df_mov["venta_id"].fillna("")
            if "cliente" not in df_mov.columns:
                df_mov["cliente"] = ""
            else:
                df_mov["cliente"] = df_mov["cliente"].fillna("")
            return df_mov
    except Exception as e:
        st.warning(f"No se pudieron cargar los movimientos: {e}")
    return pd.DataFrame(columns=COLUMNAS_MOVIMIENTOS)


def registrar_movimiento(prenda_id, producto, tipo, cantidad, precio_unitario=0, costo_unitario=0, pagado=True, medio_pago="", proveedor="", venta_id="", cliente=""):
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
            "pagado": bool(pagado),
            "medio_pago": str(medio_pago or ""),
            "proveedor": str(proveedor or ""),
            "venta_id": str(venta_id or ""),
            "cliente": str(cliente or ""),
            "fecha": datetime.now().isoformat(),
            "usuario": st.session_state.get("usuario_actual", ""),
        }
        supabase.table("movimientos").insert(datos).execute()
        cargar_movimientos.clear()
        return True
    except Exception as e:
        st.error(f"Error al registrar el movimiento: {e}")
        return False


def eliminar_todos_los_movimientos():
    """Borra todo el historial de ventas/compras (usado por el botón 'Restablecer' de Reportes)."""
    if not supabase:
        return False
    try:
        supabase.table("movimientos").delete().neq("id", "___nunca___").execute()
        cargar_movimientos.clear()
        return True
    except Exception as e:
        st.error(f"Error al restablecer los movimientos: {e}")
        return False


@st.cache_data(ttl=20)
def cargar_deudores():
    if not supabase:
        return pd.DataFrame(columns=COLUMNAS_DEUDORES)
    try:
        res = supabase.table("deudores").select("*").order("nombre").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.warning(f"No se pudieron cargar los deudores: {e}")
    return pd.DataFrame(columns=COLUMNAS_DEUDORES)


@st.cache_data(ttl=20)
def cargar_deudas_movimientos():
    if not supabase:
        return pd.DataFrame(columns=COLUMNAS_DEUDAS_MOVIMIENTOS)
    try:
        res = supabase.table("deudas_movimientos").select("*").order("fecha", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.warning(f"No se pudieron cargar los movimientos de deudores: {e}")
    return pd.DataFrame(columns=COLUMNAS_DEUDAS_MOVIMIENTOS)


def guardar_deudor(nombre, telefono="", notas=""):
    if not supabase:
        st.warning("No hay conexión a la base de datos.")
        return None
    try:
        nuevo_id = str(uuid.uuid4())
        datos = {
            "id": nuevo_id,
            "nombre": str(nombre).strip(),
            "telefono": str(telefono or "").strip(),
            "saldo": 0.0,
            "notas": str(notas or "").strip(),
        }
        supabase.table("deudores").insert(datos).execute()
        cargar_deudores.clear()
        return nuevo_id
    except Exception as e:
        st.error(f"Error al guardar la persona: {e}")
        return None


def actualizar_saldo_deudor(deudor_id, nuevo_saldo):
    if not supabase:
        return False
    try:
        supabase.table("deudores").update({"saldo": float(nuevo_saldo)}).match({"id": deudor_id}).execute()
        cargar_deudores.clear()
        return True
    except Exception as e:
        st.error(f"Error al actualizar el saldo: {e}")
        return False


def eliminar_deudor(deudor_id):
    if not supabase:
        return False
    try:
        supabase.table("deudores").delete().match({"id": deudor_id}).execute()
        cargar_deudores.clear()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False


def registrar_movimiento_deuda(deudor_id, deudor_nombre, tipo, descripcion, monto, medio_pago="", tasa_cambio=0):
    if not supabase:
        st.warning("No hay conexión a la base de datos.")
        return False
    try:
        datos = {
            "id": str(uuid.uuid4()),
            "deudor_id": str(deudor_id),
            "deudor_nombre": str(deudor_nombre),
            "tipo": tipo,
            "descripcion": str(descripcion or ""),
            "monto": float(monto or 0),
            "medio_pago": str(medio_pago or ""),
            "tasa_cambio": float(tasa_cambio or 0),
            "fecha": datetime.now().isoformat(),
            "usuario": st.session_state.get("usuario_actual", ""),
        }
        supabase.table("deudas_movimientos").insert(datos).execute()
        cargar_deudas_movimientos.clear()
        return True
    except Exception as e:
        st.error(f"Error al registrar el movimiento: {e}")
        return False


def eliminar_movimiento_deuda(movimiento_id, deudor_id, tipo, monto):
    """Borra un cargo/abono del historial y corrige el saldo del deudor para que cuadre."""
    if not supabase:
        st.warning("No hay conexión a la base de datos.")
        return False
    try:
        deudores_actual = cargar_deudores()
        fila_deudor = deudores_actual[deudores_actual["id"].astype(str) == str(deudor_id)]
        if not fila_deudor.empty:
            saldo_actual = float(fila_deudor.iloc[0].get("saldo", 0) or 0)
            # Si se borra un cargo, se resta lo que había sumado; si se borra un abono, se vuelve a sumar.
            nuevo_saldo = saldo_actual - float(monto) if tipo == "cargo" else saldo_actual + float(monto)
            actualizar_saldo_deudor(deudor_id, nuevo_saldo)
        supabase.table("deudas_movimientos").delete().match({"id": movimiento_id}).execute()
        cargar_deudas_movimientos.clear()
        return True
    except Exception as e:
        st.error(f"Error al eliminar el movimiento: {e}")
        return False


def guardar_configuracion_completa(cats, tallas, colores):
    try:
        g = obtener_conexion_github()
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

@st.cache_data(ttl=900)
def obtener_tasas_cambio():
    """Consulta tasas de cambio de Venezuela (BCV, Paralelo/Binance, Euro) desde una API pública gratuita."""
    fuentes = {
        "BCV": "https://ve.dolarapi.com/v1/dolares/oficial",
        "Paralelo / Binance": "https://ve.dolarapi.com/v1/dolares/paralelo",
        "Euro BCV": "https://ve.dolarapi.com/v1/euros/oficial",
        "Euro Paralelo": "https://ve.dolarapi.com/v1/euros/paralelo",
    }
    tasas = {}
    for etiqueta, url in fuentes.items():
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                valor = data.get("promedio") or data.get("venta") or data.get("compra")
                if valor:
                    tasas[etiqueta] = {"valor": float(valor), "fecha": data.get("fechaActualizacion", "")}
        except Exception:
            pass
    return tasas


def selector_tasa_cambio(key_prefix, valor_por_defecto=0.0):
    """Selector de tasa de cambio: BCV / Paralelo-Binance / Euro (en vivo) o Manual. Devuelve (valor, etiqueta_fuente)."""
    tasas_disponibles = obtener_tasas_cambio()
    opciones = list(tasas_disponibles.keys()) + ["Manual"]
    if not tasas_disponibles:
        st.caption("⚠️ No se pudo conectar con la API de tasas en este momento; usa 'Manual'.")

    fuente_sel = st.selectbox("Tasa de cambio", opciones, key=f"{key_prefix}_fuente_tasa")

    if fuente_sel == "Manual":
        tasa_valor = st.number_input("Escribe la tasa manualmente", min_value=0.0, step=0.01, value=valor_por_defecto, key=f"{key_prefix}_tasa_manual")
    else:
        info_tasa = tasas_disponibles[fuente_sel]
        tasa_valor = info_tasa["valor"]
        st.caption(f"💱 {fuente_sel}: {tasa_valor:,.2f} Bs — actualizado {formatear_fecha_corta(info_tasa['fecha'])}")

    return tasa_valor, fuente_sel


def moneda(valor):
    try:
        return f"${float(valor):,.2f}"
    except Exception:
        return "$0.00"


def encabezado_seccion_form(icono, titulo):
    st.markdown(
        f"""<div class="form-section-header"><span class="form-section-icon">{icono}</span><span class="form-section-title">{titulo}</span></div>""",
        unsafe_allow_html=True,
    )


def formatear_fecha_corta(valor_fecha):
    try:
        dt = pd.to_datetime(valor_fecha)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(valor_fecha)


def render_tabla_deudas(df_deudas):
    """Tabla HTML con estilo de marca para el historial de cargos/abonos de deudores."""
    filas_html = ""
    for _, fila in df_deudas.iterrows():
        tipo = str(fila.get("tipo", ""))
        if tipo == "cargo":
            badge = "<span style='background: rgba(244,114,182,0.15); color:#f472b6; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Cargo (le fié)</span>"
        elif tipo == "abono":
            badge = "<span style='background: rgba(52,211,153,0.15); color:#34d399; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Abono (pagó)</span>"
        else:
            badge = f"<span style='background: rgba(219,39,119,0.15); color:var(--accent); padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>{tipo.capitalize()}</span>"

        descripcion_txt = fila.get("descripcion", "") or "—"
        medio_pago_txt = fila.get("medio_pago", "") or "—"
        tasa_val = float(fila.get("tasa_cambio", 0) or 0)
        tasa_txt = f"{tasa_val:,.2f}" if tasa_val > 0 else "—"
        filas_html += f"""<tr>
<td>{formatear_fecha_corta(fila.get('fecha', ''))}</td>
<td>{fila.get('deudor_nombre', '')}</td>
<td>{badge}</td>
<td>{descripcion_txt}</td>
<td style="text-align:right;">{moneda(fila.get('monto', 0))}</td>
<td>{medio_pago_txt}</td>
<td style="text-align:right;">{tasa_txt}</td>
<td>{fila.get('usuario', '')}</td>
</tr>"""

    tabla_html = f"""<div class="tabla-movimientos-wrapper">
<table class="tabla-movimientos">
<thead><tr>
<th>Fecha</th><th>Persona</th><th>Tipo</th><th>Descripción</th><th>Monto</th><th>Medio de Pago</th><th>Tasa</th><th>Usuario</th>
</tr></thead>
<tbody>{filas_html}</tbody>
</table>
</div>"""
    st.markdown(tabla_html, unsafe_allow_html=True)


def render_tabla_movimientos(df_mov):
    """Tabla HTML con estilo de marca para el historial de movimientos (ventas/compras)."""
    filas_html = ""
    for _, fila in df_mov.iterrows():
        tipo = str(fila.get("tipo", ""))
        if tipo == "venta":
            badge = "<span style='background: rgba(52,211,153,0.15); color:#34d399; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Venta</span>"
        elif tipo == "compra":
            badge = "<span style='background: rgba(212,175,120,0.15); color:#d4af78; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Compra</span>"
        else:
            badge = f"<span style='background: rgba(219,39,119,0.15); color:var(--accent); padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>{tipo.capitalize()}</span>"

        proveedor_txt = fila.get("proveedor", "") or "—"
        filas_html += f"""<tr>
<td>{formatear_fecha_corta(fila.get('fecha', ''))}</td>
<td>{fila.get('producto', '')}</td>
<td>{badge}</td>
<td style="text-align:center;">{int(fila.get('cantidad', 0) or 0)}</td>
<td style="text-align:right;">{moneda(fila.get('precio_unitario', 0))}</td>
<td style="text-align:right;">{moneda(fila.get('costo_unitario', 0))}</td>
<td>{proveedor_txt}</td>
<td>{fila.get('usuario', '')}</td>
</tr>"""

    tabla_html = f"""<div class="tabla-movimientos-wrapper">
<table class="tabla-movimientos">
<thead><tr>
<th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cant.</th><th>Precio Unit.</th><th>Costo Unit.</th><th>Proveedor</th><th>Usuario</th>
</tr></thead>
<tbody>{filas_html}</tbody>
</table>
</div>"""
    st.markdown(tabla_html, unsafe_allow_html=True)


def colores_grafico():
    if st.session_state.get("tema") == "claro":
        return {"texto": "#2b1f26", "grid": "rgba(219, 39, 119, 0.15)"}
    return {"texto": "#f9f6f8", "grid": "rgba(219, 39, 119, 0.15)"}


def grafico_barras_vertical(serie, formato_valor=None, altura=300):
    """Gráfica de barras vertical con degradado rosa/oro, para series tipo 'ventas por mes'."""
    c = colores_grafico()
    etiquetas = [formato_valor(v) if formato_valor else str(v) for v in serie.values]
    x_valores = [str(v) for v in serie.index]
    fig = go.Figure(data=[go.Bar(
        x=x_valores, y=serie.values,
        marker=dict(
            color=serie.values,
            colorscale=[[0, "#7a1f4a"], [0.5, "#db2777"], [1, "#f472b6"]],
            line=dict(width=0),
        ),
        text=etiquetas, textposition="outside", textfont=dict(color=c["texto"], size=12),
        hovertemplate="%{x}<br>%{text}<extra></extra>",
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["texto"], family="Montserrat, sans-serif"),
        xaxis=dict(type="category", showgrid=False, title=None, tickfont=dict(color=c["texto"])),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], title=None, tickfont=dict(color=c["texto"]), zeroline=False),
        margin=dict(l=10, r=10, t=30, b=10), height=altura, showlegend=False,
        bargap=0.35,
    )
    return fig


def grafico_barras_horizontal(serie, altura=300):
    """Gráfica de barras horizontal con degradado rosa/oro, para rankings tipo 'top productos'."""
    c = colores_grafico()
    fig = go.Figure(data=[go.Bar(
        x=serie.values, y=list(serie.index), orientation="h",
        marker=dict(
            color=serie.values,
            colorscale=[[0, "#7a1f4a"], [0.5, "#db2777"], [1, "#f472b6"]],
            line=dict(width=0),
        ),
        text=[str(int(v)) for v in serie.values], textposition="outside", textfont=dict(color=c["texto"], size=12),
        hovertemplate="%{y}<br>%{x} unidades<extra></extra>",
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["texto"], family="Montserrat, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor=c["grid"], title=None, tickfont=dict(color=c["texto"]), zeroline=False),
        yaxis=dict(type="category", showgrid=False, title=None, autorange="reversed", tickfont=dict(color=c["texto"])),
        margin=dict(l=10, r=10, t=30, b=10), height=altura, showlegend=False,
        bargap=0.35,
    )
    return fig


def grafico_dona(serie, texto_centro_arriba="", texto_centro_abajo="", altura=340):
    """Gráfica de dona (pastel) con la paleta rosa/oro, con un total destacado en el centro."""
    c = colores_grafico()
    paleta = ["#7a1f4a", "#db2777", "#f472b6", "#f9a8d4", "#d4af78", "#a52465", "#ec4899", "#be185d"]
    colores_segmentos = [paleta[i % len(paleta)] for i in range(len(serie))]
    fig = go.Figure(data=[go.Pie(
        labels=list(serie.index), values=list(serie.values), hole=0.62,
        marker=dict(colors=colores_segmentos, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="percent", textfont=dict(color="#ffffff", size=12),
        hovertemplate="%{label}<br>%{value} (%{percent})<extra></extra>",
        sort=False,
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["texto"], family="Montserrat, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10), height=altura, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color=c["texto"], size=11)),
        annotations=[dict(
            text=f"<b style='font-size:26px'>{texto_centro_arriba}</b><br><span style='font-size:11px'>{texto_centro_abajo}</span>",
            x=0.5, y=0.5, font=dict(color=c["texto"]), showarrow=False,
        )],
    )
    return fig


def generar_factura_pdf(venta_id, cliente, fecha_texto, items_factura, total_factura):
    """Arma un PDF de factura simple con los productos de una venta. Devuelve bytes o None si fpdf2 no está instalado."""
    if not PDF_DISPONIBLE:
        return None
    pdf = FPDF(format="A4")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(219, 39, 119)
    pdf.cell(0, 12, "LEWIN BOUTIQUE", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, "Factura de venta", ln=True)
    pdf.ln(4)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"N. de factura: {str(venta_id)[:8].upper()}", ln=True)
    pdf.cell(0, 6, f"Fecha: {fecha_texto}", ln=True)
    pdf.cell(0, 6, f"Cliente: {cliente or 'Consumidor final'}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(244, 114, 182)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 8, "Producto", border=1, fill=True)
    pdf.cell(30, 8, "Cantidad", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Precio Unit.", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Subtotal", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(20, 20, 20)
    for item in items_factura:
        subtotal_item = float(item["cantidad"]) * float(item["precio_unitario"])
        pdf.cell(80, 8, str(item["producto"])[:42], border=1)
        pdf.cell(30, 8, str(int(item["cantidad"])), border=1, align="C")
        pdf.cell(35, 8, moneda(item["precio_unitario"]), border=1, align="R")
        pdf.cell(35, 8, moneda(subtotal_item), border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(145, 9, "TOTAL", align="R")
    pdf.cell(35, 9, moneda(total_factura), align="R", ln=True)

    pdf.ln(16)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, "Gracias por tu compra", ln=True, align="C")

    return bytes(pdf.output())


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

def get_css(tema: str, compacto: bool = False) -> str:
    ancho_sidebar = "84px" if compacto else "260px"
    if tema == "claro":
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.05) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.04) 0%, transparent 40%),
                           linear-gradient(135deg, #fdf5f8 0%, #ffffff 50%, #fdf6f9 100%);
            --text-color: #2b1f26;
            --text-secondary: #8a6b78;
            --accent: #db2777;
            --accent-light: #ec4899;
            --accent-neon: #34d399;
            --card-bg: rgba(255, 255, 255, 0.88);
            --border-color: rgba(219, 39, 119, 0.16);
            --sidebar-bg: rgba(255, 255, 255, 0.96);
            --input-bg: rgba(255, 255, 255, 0.92);
        """
    else:
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.07) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 40%),
                           linear-gradient(135deg, #100e12 0%, #17141a 50%, #130f14 100%);
            --text-color: #f5f1f3;
            --text-secondary: #a8909d;
            --accent: #ec6aa8;
            --accent-light: #ec6aa8;
            --accent-neon: #34d399;
            --card-bg: rgba(22, 19, 24, 0.85);
            --border-color: rgba(219, 39, 119, 0.14);
            --sidebar-bg: rgba(18, 16, 20, 0.96);
            --input-bg: rgba(28, 25, 31, 0.85);
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500;600;700&display=swap');

:root {{ {variables} }}

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes glowActivo {{
    0%, 100% {{ box-shadow: 0 0 8px rgba(236, 106, 168, 0.35), inset 3px 0 0 var(--accent); }}
    50% {{ box-shadow: 0 0 16px rgba(236, 106, 168, 0.55), inset 3px 0 0 var(--accent); }}
}}

.stApp {{
    background: var(--bg-gradient);
    background-attachment: fixed;
    color: var(--text-color) !important;
    font-family: 'Montserrat', sans-serif !important;
}}

header[data-testid="stHeader"] {{ background: transparent !important; }}

.block-container {{ max-width: 100% !important; padding: 3.5rem 2rem 2rem 2rem !important; }}

section[data-testid="stSidebar"] {{
    width: {ancho_sidebar} !important;
    min-width: {ancho_sidebar} !important;
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
    backdrop-filter: blur(25px);
    transition: width 0.25s ease;
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

.form-section-header {{
    display: flex; align-items: center; gap: 10px;
    margin: 22px 0 14px 0; padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
}}
.form-section-header:first-of-type {{ margin-top: 2px; }}
.form-section-icon {{
    width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #db2777 0%, #f472b6 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; box-shadow: 0 0 10px rgba(219, 39, 119, 0.45);
}}
.form-section-title {{
    font-size: 13px; font-weight: 700; color: var(--text-color);
    text-transform: uppercase; letter-spacing: 1px;
}}

section[data-testid="stFileUploaderDropzone"] {{
    background: var(--input-bg) !important;
    border: 1.5px dashed var(--border-color) !important;
    border-radius: 14px !important;
}}
section[data-testid="stFileUploaderDropzone"] button {{
    background: rgba(219, 39, 119, 0.15) !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color) !important;
}}

.tabla-movimientos-wrapper {{
    max-height: 480px; overflow-y: auto; border: 1px solid var(--border-color);
    border-radius: 14px; background: var(--card-bg); backdrop-filter: blur(20px);
}}
.tabla-movimientos {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.tabla-movimientos thead th {{
    position: sticky; top: 0; background: rgba(219, 39, 119, 0.15); color: var(--text-color);
    text-align: left; padding: 12px 14px; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); z-index: 1;
}}
.tabla-movimientos tbody td {{
    padding: 10px 14px; color: var(--text-color); border-bottom: 1px solid var(--border-color);
}}
.tabla-movimientos tbody tr:hover {{ background: rgba(219, 39, 119, 0.06); }}
.tabla-movimientos tbody tr:last-child td {{ border-bottom: none; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(20px);
}}
.config-chip {{
    background: rgba(219, 39, 119, 0.07); border: 1px solid var(--border-color);
    border-radius: 10px; padding: 8px 14px; margin-bottom: 6px;
    font-size: 13px; color: var(--text-color); display: flex; align-items: center; height: 38px;
}}

.dashboard-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color); border-radius: 16px;
    padding: 20px; display: flex; justify-content: space-between; align-items: flex-start;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2); margin-bottom: 16px; animation: fadeInUp 0.35s ease;
}}
.dashboard-card-value {{ font-size: 28px; font-weight: 800; color: var(--text-color); }}
.dashboard-card-label {{ font-size: 12px; color: var(--text-secondary); margin-top: 4px; }}
.dashboard-card-icon {{ font-size: 26px; opacity: 0.85; }}
.dashboard-total-banner {{
    background: linear-gradient(135deg, #db2777 0%, #f472b6 100%); border-radius: 18px;
    padding: 26px 32px; display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 15px 35px rgba(219, 39, 119, 0.35); margin-top: 8px;
}}
.dashboard-total-value {{ font-size: 32px; font-weight: 800; color: #ffffff; }}
.dashboard-total-label {{ font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 4px; }}
.dashboard-total-icon {{ font-size: 34px; color: #ffffff; opacity: 0.9; }}

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

.user-profile-compact {{
    background: rgba(219, 39, 119, 0.08); padding: 10px 12px; border-radius: 12px;
    border: 1px solid var(--border-color); margin-bottom: 10px;
    display: flex; align-items: center; gap: 10px;
}}
.user-avatar {{
    width: 32px; height: 32px; background: linear-gradient(135deg, #db2777 0%, #f472b6 100%); color: #ffffff;
    font-weight: 800; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 13px; box-shadow: 0 0 15px rgba(219, 39, 119, 0.5); flex-shrink: 0;
}}
.user-info-name {{ font-size: 13px; font-weight: 700; color: var(--text-color); line-height: 1.2; }}
.user-info-rol {{ font-size: 9px; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }}

.menu-divider {{ height: 1px; background: var(--border-color); margin: 12px 0 10px 0; }}

.menu-group-title {{
    font-size: 9px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1.5px;
    font-weight: 700; margin: 14px 0 6px 4px; opacity: 0.75;
}}

section[data-testid="stSidebar"] button[kind="secondary"] {{
    background: transparent !important; border: 1px solid transparent !important;
    text-align: left !important; justify-content: flex-start !important;
    box-shadow: none !important; padding: 9px 12px !important; font-weight: 500 !important;
    transition: background 0.15s ease !important;
}}
section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
    background: rgba(236, 106, 168, 0.08) !important; border-color: var(--border-color) !important;
    transform: none !important;
}}
section[data-testid="stSidebar"] button[kind="primary"] {{
    background: rgba(236, 106, 168, 0.13) !important; color: var(--text-color) !important;
    border: none !important; border-radius: 10px !important;
    text-align: left !important; justify-content: flex-start !important;
    font-weight: 700 !important; padding: 9px 12px !important;
    animation: glowActivo 2.4s ease-in-out infinite !important;
}}
section[data-testid="stSidebar"] button[kind="primary"]:hover {{
    transform: none !important;
}}

.user-badge-neon {{
    display: inline-flex; align-items: center; gap: 5px; font-size: 9px; font-weight: 800;
    letter-spacing: 1px; color: var(--accent-neon); text-transform: uppercase;
}}
.user-badge-neon .dot-neon {{
    width: 6px; height: 6px; border-radius: 50%; background: var(--accent-neon);
    box-shadow: 0 0 6px var(--accent-neon); flex-shrink: 0;
}}

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
div[data-testid="stCode"] {{
    width: 100% !important;
    overflow-x: hidden !important;
}}

div[data-testid="stCode"] pre,
div[data-testid="stCode"] code,
div[data-testid="stCode"] * {{
    white-space: pre-wrap !important;
    word-break: break-word !important;
    overflow-x: hidden !important;
}}

div[data-testid="stTextArea"] textarea {{
    background-color: var(--input-bg) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    resize: none !important;
}}

.alert-banner {{
    background: rgba(244, 114, 182, 0.12); border: 1px solid var(--accent);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 20px; color: var(--text-color);
}}

/* --- Sub-opciones del menú (van al final para garantizar que ganen) --- */
section[data-testid="stSidebar"] button[aria-label^="•"] {{
    font-size: 12.5px !important; color: var(--text-secondary) !important;
    border-left: 1.5px solid var(--border-color) !important; border-radius: 0 !important;
    margin-left: 16px !important; padding: 7px 10px 7px 14px !important; font-weight: 500 !important;
    box-shadow: none !important; background: transparent !important; animation: none !important;
}}
section[data-testid="stSidebar"] button[aria-label^="•"]:hover {{
    background: rgba(236, 106, 168, 0.06) !important; color: var(--text-color) !important;
}}
section[data-testid="stSidebar"] button[kind="primary"][aria-label^="•"] {{
    color: var(--accent) !important; border-left: 2px solid var(--accent) !important;
    background: transparent !important; box-shadow: none !important; font-weight: 700 !important;
    animation: none !important;
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
    "menu_activo": "inicio",
    "sidebar_compacto": False,
}
for k, v in defaults_sesion.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "inventario_local" not in st.session_state:
    st.session_state.inventario_local = pd.DataFrame(columns=COLUMNAS_INVENTARIO)

st.markdown(get_css(st.session_state.tema, st.session_state.sidebar_compacto), unsafe_allow_html=True)

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

ES_ADMIN = True  # Todos los usuarios (leiver y winderly) tienen acceso completo por igual

# =====================================================================================
# 1. PANTALLA DE BIENVENIDA
# =====================================================================================

if not st.session_state.autenticado and st.session_state.etapa == "bienvenida":
    total_prendas_hero = len(df) if not df.empty else 0
    if total_prendas_hero > 0:
        porcentaje_ok_hero = round(int((df["cantidad"] > df["alerta"]).sum()) / total_prendas_hero * 100)
    else:
        porcentaje_ok_hero = 0

    hero_html = """
        <style>
        .block-container { padding: 3.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }
        .full-hero-wrapper {
            background: var(--card-bg); backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
            border: 1px solid var(--border-color); border-radius: 32px 32px 0 0; padding: 50px 70px 35px 70px;
            display: flex; flex-direction: column; position: relative;
            overflow: hidden; box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.08);
            margin: 0 auto; max-width: 1450px;
        }
        @keyframes floatParticle {
            0%   { transform: translateY(0px) translateX(0px); opacity: 0.25; }
            50%  { transform: translateY(-18px) translateX(8px); opacity: 0.6; }
            100% { transform: translateY(0px) translateX(0px); opacity: 0.25; }
        }
        @keyframes pulseGlowHero {
            0%, 100% { box-shadow: 0 8px 25px rgba(219, 39, 119, 0.35); }
            50% { box-shadow: 0 8px 40px rgba(244, 114, 182, 0.65); }
        }
        @keyframes kenBurnsHero {
            0% { transform: scale(1) translate(0,0); }
            100% { transform: scale(1.08) translate(-1%, -1%); }
        }
        .bg-photo-hero {
            position: absolute; top: -10%; right: -15%; width: 55%; height: 130%;
            background: radial-gradient(circle at 30% 30%, rgba(219, 39, 119, 0.30), transparent 60%);
            border-radius: 50%; filter: blur(10px);
            animation: kenBurnsHero 14s ease-in-out infinite alternate; z-index: 0;
        }
        .particle-hero {
            position: absolute; border-radius: 50%; background: #f472b6; filter: blur(1px); z-index: 0;
        }
        .stitch-line-hero { position: absolute; border-top: 1.5px dashed rgba(212, 175, 120, 0.4); z-index: 0; }
        .hero-inner { position: relative; z-index: 1; }
        .hero-topbar {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px;
            border-bottom: 1px solid var(--border-color); padding-bottom: 20px;
        }
        .hero-brand { display: flex; align-items: center; gap: 12px; }
        .brand-icon-hero {
            width: 30px; height: 30px; border-radius: 50%;
            background: linear-gradient(135deg, #db2777 0%, #f472b6 60%, #d4af78 100%);
            display: flex; align-items: center; justify-content: center;
            font-family: 'Cinzel', serif !important; font-weight: 800; font-size: 14px; color: #0c0b0e;
            box-shadow: 0 0 14px rgba(244, 114, 182, 0.6);
        }
        .hero-brand-name {
            font-family: 'Cinzel', serif !important; font-size: 15px; font-weight: 700; color: var(--text-color); letter-spacing: 2px;
        }
        h1.hero-title, .hero-title {
            font-family: 'Cinzel', serif !important; font-size: 52px; font-weight: 800 !important; color: var(--text-color);
            letter-spacing: 2px; line-height: 1.1; margin-bottom: 16px;
        }
        .hero-subtitle-tag {
            font-size: 12px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px;
            font-weight: 700; margin-bottom: 20px;
        }
        .hero-desc { color: var(--text-secondary); font-size: 15px; line-height: 1.6; max-width: 650px; margin-bottom: 35px; }
        .feature-pills-container { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 32px; }
        .feature-pill {
            background: rgba(219, 39, 119, 0.1); border: 1px solid var(--border-color); color: var(--accent);
            padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;
        }
        .stats-row-hero { display: flex; gap: 40px; }
        .stat-value-hero { font-family: 'Cinzel', serif !important; font-size: 26px; font-weight: 800; color: var(--text-color); }
        .stat-label-hero {
            font-size: 10px; color: var(--text-secondary); text-transform: uppercase;
            letter-spacing: 1.5px; font-weight: 700; margin-top: 2px;
        }
        .hero-cta-box {
            max-width: 1450px; margin: 0 auto; background: var(--card-bg); backdrop-filter: blur(40px);
            border: 1px solid var(--border-color); border-top: none; border-radius: 0 0 32px 32px;
            padding: 25px 70px 30px 70px;
        }
        div[data-testid="stButton"] { max-width: 340px; margin: 0 auto; }
        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #db2777 0%, #f472b6 100%) !important;
            color: #ffffff !important; border: none !important;
            animation: pulseGlowHero 2.6s ease-in-out infinite !important;
        }
        .footer-signature-hero { margin-top: 10px; text-align: center; font-size: 10px; color: var(--text-secondary); }
        </style>
        <div class="full-hero-wrapper">
            <div class="bg-photo-hero"></div>
            <div class="particle-hero" style="width:5px; height:5px; top:15%; left:60%; animation: floatParticle 6s ease-in-out infinite;"></div>
            <div class="particle-hero" style="width:3px; height:3px; top:35%; left:75%; animation: floatParticle 8s ease-in-out infinite 1s;"></div>
            <div class="particle-hero" style="width:4px; height:4px; top:55%; left:68%; animation: floatParticle 7s ease-in-out infinite 2s;"></div>
            <div class="particle-hero" style="width:3px; height:3px; top:25%; left:85%; animation: floatParticle 9s ease-in-out infinite 0.5s;"></div>
            <div class="stitch-line-hero" style="top:12%; left:5%; width:120px;"></div>
            <div class="stitch-line-hero" style="bottom:18%; left:5%; width:80px;"></div>
            <div class="hero-inner">
                <div class="hero-topbar">
                    <div class="hero-brand">
                        <div class="brand-icon-hero">L</div>
                        <div class="hero-brand-name">LEWIN BOUTIQUE</div>
                    </div>
                </div>
                <div class="hero-subtitle-tag">Inventario Boutique</div>
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
                <div class="stats-row-hero">
                    <div><div class="stat-value-hero">PLACEHOLDER_TOTAL</div><div class="stat-label-hero">Prendas en catálogo</div></div>
                    <div><div class="stat-value-hero">PLACEHOLDER_PORC%</div><div class="stat-label-hero">Stock por encima del mínimo</div></div>
                    <div><div class="stat-value-hero">24/7</div><div class="stat-label-hero">Acceso en la nube</div></div>
                </div>
            </div>
        </div>
        <div class="hero-cta-box">
        """
    hero_html = hero_html.replace("PLACEHOLDER_TOTAL", str(total_prendas_hero)).replace("PLACEHOLDER_PORC", str(porcentaje_ok_hero))

    st.markdown(hero_html, unsafe_allow_html=True)

    if st.button("INICIO", use_container_width=True):
        st.session_state.etapa = "login"
        st.rerun()

    st.markdown("<div class='footer-signature-hero'>Diseñado con ♥ para Lewin Boutique</div></div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================================
# 2. LOGIN
# =====================================================================================

elif not st.session_state.autenticado and st.session_state.etapa == "login":
    st.markdown(
        """
        <style>
        @keyframes floatParticleLogin {
            0%   { transform: translateY(0px) translateX(0px); opacity: 0.2; }
            50%  { transform: translateY(-20px) translateX(10px); opacity: 0.55; }
            100% { transform: translateY(0px) translateX(0px); opacity: 0.2; }
        }
        @keyframes pulseGlowLogin {
            0%, 100% { box-shadow: 0 8px 25px rgba(219, 39, 119, 0.35); }
            50% { box-shadow: 0 8px 40px rgba(244, 114, 182, 0.65); }
        }
        .particle-login {
            position: fixed; border-radius: 50%; background: #f472b6; filter: blur(1px);
            z-index: 0; pointer-events: none;
        }
        .login-welcome-tag {
            font-size: 11px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px;
            font-weight: 700; text-align: center; margin-bottom: 6px;
        }
        .login-brand-icon {
            width: 42px; height: 42px; border-radius: 50%; margin: 0 auto 12px auto;
            background: linear-gradient(135deg, #db2777 0%, #f472b6 60%, #d4af78 100%);
            display: flex; align-items: center; justify-content: center;
            font-family: 'Cinzel', serif !important; font-weight: 800; font-size: 18px; color: #0c0b0e;
            box-shadow: 0 0 18px rgba(244, 114, 182, 0.6);
        }
        .login-title-text {
            font-family: 'Cinzel', serif !important; font-size: 22px; font-weight: 700 !important;
            color: var(--text-color); letter-spacing: 1px; text-align: center;
        }
        .login-subtitle-text {
            font-size: 12px; color: var(--text-secondary); text-align: center; margin-top: 4px; margin-bottom: 14px;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #db2777 0%, #f472b6 100%) !important;
            color: #ffffff !important; border: none !important;
            animation: pulseGlowLogin 2.6s ease-in-out infinite !important;
        }
        </style>
        <div class="particle-login" style="width:5px; height:5px; top:15%; left:10%; animation: floatParticleLogin 7s ease-in-out infinite;"></div>
        <div class="particle-login" style="width:3px; height:3px; top:75%; left:15%; animation: floatParticleLogin 9s ease-in-out infinite 1s;"></div>
        <div class="particle-login" style="width:4px; height:4px; top:20%; left:88%; animation: floatParticleLogin 8s ease-in-out infinite 0.5s;"></div>
        <div class="particle-login" style="width:3px; height:3px; top:80%; left:85%; animation: floatParticleLogin 10s ease-in-out infinite 2s;"></div>
        <div class="particle-login" style="width:6px; height:6px; top:50%; left:6%; animation: floatParticleLogin 11s ease-in-out infinite 1.5s;"></div>
        <div class="particle-login" style="width:4px; height:4px; top:45%; left:94%; animation: floatParticleLogin 9.5s ease-in-out infinite 0.8s;"></div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("← Volver a la portada"):
        st.session_state.etapa = "bienvenida"
        st.rerun()

    _, col_centro, _ = st.columns([1, 1.4, 1])
    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='login-welcome-tag'>Bienvenida de vuelta</div>", unsafe_allow_html=True)
        with st.form("form_login"):
            st.markdown("<div class='login-brand-icon'>L</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-title-text'>Lewin Boutique Access</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-subtitle-text'>Ingresa tus credenciales para continuar</div>", unsafe_allow_html=True)

            usuario_input = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            clave_input = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            remember_checked = st.checkbox("Recordarme")

            if st.form_submit_button("INGRESAR", use_container_width=True):
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
    menu_actual = st.session_state.get("menu_activo", "inicio")
    compacto = st.session_state.sidebar_compacto

    col_collapse1, col_collapse2 = st.sidebar.columns([3, 1])
    with col_collapse2:
        if st.button("☰", key="btn_toggle_compacto", help="Colapsar / expandir menú"):
            st.session_state.sidebar_compacto = not st.session_state.sidebar_compacto
            st.rerun()

    if compacto:
        st.sidebar.markdown(
            f"""<div class="user-profile-compact" style="justify-content: center;"><div class="user-avatar">{inicial_usuario}</div></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            f"""
<div class="user-profile-compact">
    <div class="user-avatar">{inicial_usuario}</div>
    <div>
        <div class="user-info-name">{usuario_formateado}</div>
        <div class="user-badge-neon"><span class="dot-neon"></span>{rol_formateado}</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    if not compacto:
        tema_claro = st.sidebar.toggle("☀️ Modo claro", value=(st.session_state.tema == "claro"))
        nuevo_tema = "claro" if tema_claro else "oscuro"
        if nuevo_tema != st.session_state.tema:
            st.session_state.tema = nuevo_tema
            st.rerun()

    st.sidebar.markdown("<div class='menu-divider'></div>", unsafe_allow_html=True)

    GRUPOS_CLAVES_MENU = {
        "acc_inventario": ["existencias", "registrar", "modificar"],
        "acc_ventas": ["vender", "ventas_pagadas", "deudores"],
        "acc_compras": ["comprar", "movimientos", "facturas"],
    }
    if "grupo_menu_abierto" not in st.session_state:
        st.session_state.grupo_menu_abierto = next(
            (k for k, claves in GRUPOS_CLAVES_MENU.items() if menu_actual in claves), None
        )

    def render_grupo_acordeon(icono_grupo, titulo_grupo, items, session_key):
        """Botón principal con flechita (▼/▶). Solo un grupo puede estar abierto a la vez."""
        claves_grupo = [c for c, _ in items]
        activo_grupo = menu_actual in claves_grupo
        tipo_grupo = "primary" if activo_grupo else "secondary"

        if compacto:
            if st.sidebar.button(icono_grupo, use_container_width=True, key=f"grupo_{session_key}", type=tipo_grupo, help=titulo_grupo):
                st.session_state.menu_activo = claves_grupo[0]
                st.rerun()
            return

        expandido = st.session_state.grupo_menu_abierto == session_key
        chevron = "▼" if expandido else "▶"
        if st.sidebar.button(f"{icono_grupo}  {titulo_grupo}  {chevron}", use_container_width=True, key=f"grupo_{session_key}", type=tipo_grupo):
            st.session_state.grupo_menu_abierto = None if expandido else session_key
            st.rerun()
        if expandido:
            for clave, etiqueta in items:
                if clave in ("registrar", "modificar", "configuracion") and not ES_ADMIN:
                    continue
                tipo_item = "primary" if menu_actual == clave else "secondary"
                if st.sidebar.button(f"•  {etiqueta}", use_container_width=True, key=f"item_{clave}", type=tipo_item):
                    st.session_state.menu_activo = clave
                    st.session_state.grupo_menu_abierto = session_key
                    st.rerun()

    # --- Inicio (ítem plano, sin acordeón) ---
    etiqueta_inicio = "🏠" if compacto else "🏠  Inicio"
    if st.sidebar.button(etiqueta_inicio, use_container_width=True, key="menu_inicio", type=("primary" if menu_actual == "inicio" else "secondary"), help="Inicio" if compacto else None):
        st.session_state.menu_activo = "inicio"
        st.rerun()

    st.sidebar.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    render_grupo_acordeon("📊", "Prendas", [
        ("existencias", "Prendas"), ("registrar", "Registrar Prenda"), ("modificar", "Eliminar Prenda"),
    ], "acc_inventario")

    render_grupo_acordeon("🛍️", "Ventas", [
        ("vender", "Nueva Venta"), ("ventas_pagadas", "Ventas Pagadas"), ("deudores", "Ventas por Pagar"),
        ("facturas", "Facturas"),
    ], "acc_ventas")

    render_grupo_acordeon("📦", "Compras", [
        ("comprar", "Registrar Compra"), ("movimientos", "Movimientos"),
    ], "acc_compras")

    if not compacto:
        st.sidebar.markdown("<p class='menu-group-title'>Negocio</p>", unsafe_allow_html=True)
    for clave, icono, etiqueta in [("reportes", "📈", "Reportes"), ("configuracion", "⚙️", "Configuración")]:
        if clave == "configuracion" and not ES_ADMIN:
            continue
        tipo_boton = "primary" if menu_actual == clave else "secondary"
        label_boton = icono if compacto else f"{icono}  {etiqueta}"
        if st.sidebar.button(label_boton, use_container_width=True, key=f"menu_{clave}", type=tipo_boton, help=etiqueta if compacto else None):
            st.session_state.menu_activo = clave
            st.rerun()

    st.sidebar.markdown("<hr style='margin: 20px 0 15px 0; border-color: var(--border-color);'>", unsafe_allow_html=True)

    etiqueta_salir = "🚪" if compacto else "🚪 Cerrar Sesión"
    if st.sidebar.button(etiqueta_salir, use_container_width=True, help="Cerrar Sesión" if compacto else None):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.session_state.etapa = "bienvenida"
        if "recuerdame_user" in st.query_params:
            del st.query_params["recuerdame_user"]
        st.rerun()

    menu = st.session_state.get("menu_activo", "inicio")
    # Si un vendedor quedó apuntando a una página de admin (por sesión previa), lo regresamos
    if menu in ("registrar", "modificar", "configuracion") and not ES_ADMIN:
        menu = "existencias"
        st.session_state.menu_activo = "existencias"

    # -----------------------------------------------------------------------------
    # INICIO (dashboard resumen)
    # -----------------------------------------------------------------------------
    if menu == "inicio":
        st.markdown(
            f"""
<div class="page-header">
    <div class="page-title">🏠 Inicio</div>
    <div class="page-subtitle">Resumen general de Lewin Boutique, {st.session_state.usuario_actual.capitalize()}.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs_inicio = cargar_movimientos()
        deudores_inicio = cargar_deudores()

        total_prendas_inicio = len(df) if not df.empty else 0
        alertas_inicio = int((df["cantidad"] <= df["alerta"]).sum()) if not df.empty else 0
        compras_inicio = int((movs_inicio["tipo"] == "compra").sum()) if not movs_inicio.empty else 0
        ventas_inicio = int((movs_inicio["tipo"] == "venta").sum()) if not movs_inicio.empty else 0
        deudores_count_inicio = int((deudores_inicio["saldo"] > 0).sum()) if not deudores_inicio.empty else 0
        total_usuarios_inicio = len(USUARIOS)

        ventas_df_inicio = movs_inicio[movs_inicio["tipo"] == "venta"] if not movs_inicio.empty else pd.DataFrame()
        total_ventas_monto = float((ventas_df_inicio["cantidad"] * ventas_df_inicio["precio_unitario"]).sum()) if not ventas_df_inicio.empty else 0.0

        tarjetas_inicio = [
            ("👕", total_prendas_inicio, "Prendas"),
            ("📦", compras_inicio, "Compras"),
            ("🛍️", ventas_inicio, "Ventas"),
            ("⚠️", alertas_inicio, "Reposición"),
            ("🧾", deudores_count_inicio, "Clientes por Cobrar"),
            ("👤", total_usuarios_inicio, "Usuarios"),
        ]

        cols_inicio = st.columns(3)
        for idx, (icono_t, valor_t, etiqueta_t) in enumerate(tarjetas_inicio):
            with cols_inicio[idx % 3]:
                st.markdown(
                    f"""<div class="dashboard-card">
<div><div class="dashboard-card-value">{valor_t}</div><div class="dashboard-card-label">{etiqueta_t}</div></div>
<div class="dashboard-card-icon">{icono_t}</div>
</div>""",
                    unsafe_allow_html=True,
                )

        st.markdown(
            f"""<div class="dashboard-total-banner">
<div><div class="dashboard-total-value">{moneda(total_ventas_monto)}</div><div class="dashboard-total-label">Total Ventas</div></div>
<div class="dashboard-total-icon">$</div>
</div>""",
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------------
    # EXISTENCIAS
    # -----------------------------------------------------------------------------
    elif menu == "existencias":
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

                    tarjeta_html = f"""<div class="product-card" style="border-color: {borde_color};">
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
</div>"""

                    with col_actual:
                        st.markdown(tarjeta_html, unsafe_allow_html=True)

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
                        st.text_area(
                            "Detalles", value=detalles_texto, height=70, disabled=True,
                            label_visibility="collapsed", key=f"detalle_{row['ID']}",
                        )
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
    <div class="page-title">🆕 Nueva Venta</div>
    <div class="page-subtitle">Arma el pedido y dinos si ya te pagaron o queda pendiente — la app la manda sola a "Ventas Pagadas" o "Ventas por Pagar".</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas para vender.")
        else:
            if "carrito_venta_nueva" not in st.session_state:
                st.session_state.carrito_venta_nueva = []

            col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
            with col_p1:
                ids_venta_nueva = df["ID"].astype(str).tolist()
                producto_venta_sel = st.selectbox(
                    "Producto", ids_venta_nueva,
                    format_func=lambda x: f"{x} — {df[df['ID'].astype(str) == x]['Producto'].values[0]} (stock: {int(df[df['ID'].astype(str) == x]['cantidad'].values[0])})",
                    key="select_producto_venta_nueva",
                )
            with col_p2:
                cantidad_venta_sel = st.number_input("Cantidad", min_value=1, value=1, step=1, key="cantidad_venta_nueva")
            with col_p3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Agregar", use_container_width=True, key="btn_agregar_venta_nueva"):
                    fila_prod = df[df["ID"].astype(str) == str(producto_venta_sel)].iloc[0]
                    if cantidad_venta_sel > int(fila_prod["cantidad"]):
                        st.error(f"Solo hay {int(fila_prod['cantidad'])} en stock.")
                    else:
                        st.session_state.carrito_venta_nueva.append({
                            "id": fila_prod["ID"], "producto": fila_prod["Producto"],
                            "cantidad": int(cantidad_venta_sel), "precio_unitario": float(fila_prod.get("precio_venta", 0) or 0),
                            "costo_unitario": float(fila_prod.get("costo", 0) or 0),
                        })
                        st.rerun()

            if st.session_state.carrito_venta_nueva:
                total_venta_nueva = sum(item["cantidad"] * item["precio_unitario"] for item in st.session_state.carrito_venta_nueva)
                for idx, item in enumerate(st.session_state.carrito_venta_nueva):
                    c_item1, c_item2 = st.columns([4, 1])
                    with c_item1:
                        st.markdown(
                            f"<div class='config-chip'>{item['cantidad']} × {item['producto']} — {moneda(item['cantidad'] * item['precio_unitario'])}</div>",
                            unsafe_allow_html=True,
                        )
                    with c_item2:
                        if st.button("✕", key=f"quitar_venta_nueva_{idx}", use_container_width=True):
                            st.session_state.carrito_venta_nueva.pop(idx)
                            st.rerun()

                st.markdown(f"**Total del pedido: {moneda(total_venta_nueva)}**")
                st.markdown("<br>", unsafe_allow_html=True)

                estado_pago = st.radio(
                    "¿Esta venta fue pagada?",
                    ["✅ Sí, pagada", "🧾 No, queda pendiente (fiado)"],
                    horizontal=True, key="estado_pago_venta_nueva",
                )
                fue_pagada = estado_pago.startswith("✅")

                nombre_valido = True
                if fue_pagada:
                    medio_pago_venta = st.selectbox(
                        "Medio de pago", ["Efectivo", "Pago Móvil", "Transferencia", "Zelle", "Otro"],
                        key="medio_pago_venta_nueva",
                    )
                    cliente_pagada_nv = st.text_input(
                        "Nombre del cliente (opcional, para la factura)", placeholder="Ej: Consumidor final",
                        key="cliente_pagada_nv",
                    )
                    deudores_df_nv = pd.DataFrame()
                    persona_sel_nv = None
                else:
                    deudores_df_nv = cargar_deudores()
                    NUEVA_PERSONA_NV = "➕ Persona nueva"
                    opciones_persona_nv = [NUEVA_PERSONA_NV] + deudores_df_nv["id"].astype(str).tolist()
                    persona_sel_nv = st.selectbox(
                        "¿A quién se le fía?", opciones_persona_nv,
                        format_func=lambda x: x if x == NUEVA_PERSONA_NV else deudores_df_nv[deudores_df_nv["id"].astype(str) == x]["nombre"].values[0],
                        key="select_persona_venta_nueva",
                    )
                    nombre_nuevo_nv, telefono_nuevo_nv = "", ""
                    if persona_sel_nv == NUEVA_PERSONA_NV:
                        col_np1, col_np2 = st.columns(2)
                        with col_np1:
                            nombre_nuevo_nv = st.text_input("Nombre", placeholder="Ej: María Pérez", key="nombre_nueva_persona_nv")
                        with col_np2:
                            telefono_nuevo_nv = st.text_input("Teléfono (opcional)", placeholder="Ej: 0414-1234567", key="telefono_nueva_persona_nv")
                        nombre_valido = nombre_nuevo_nv.strip() != ""
                    tasa_venta_nv, fuente_tasa_venta_nv = selector_tasa_cambio("venta_nueva", st.session_state.get("ultima_tasa", 0.0))
                    if tasa_venta_nv > 0:
                        st.caption(f"💱 Equivalente: {total_venta_nueva * tasa_venta_nv:,.2f} Bs")
                    medio_pago_venta = ""

                if st.button("✅ Confirmar Venta", use_container_width=True, key="btn_confirmar_venta_nueva", disabled=not nombre_valido):
                    venta_id_nv = str(uuid.uuid4())
                    id_persona_final_nv = None
                    if fue_pagada:
                        cliente_final_nv = cliente_pagada_nv.strip() or "Consumidor final"
                    else:
                        if persona_sel_nv == "➕ Persona nueva":
                            id_persona_final_nv = guardar_deudor(nombre_nuevo_nv, telefono_nuevo_nv)
                            cliente_final_nv = nombre_nuevo_nv
                        else:
                            id_persona_final_nv = persona_sel_nv
                            cliente_final_nv = deudores_df_nv[deudores_df_nv["id"].astype(str) == str(persona_sel_nv)]["nombre"].values[0]

                    for item in st.session_state.carrito_venta_nueva:
                        fila_prod_actual = df[df["ID"].astype(str) == str(item["id"])].iloc[0]
                        datos_act = fila_prod_actual.to_dict()
                        datos_act["cantidad"] = int(fila_prod_actual["cantidad"]) - item["cantidad"]
                        actualizar_prenda(item["id"], datos_act)
                        registrar_movimiento(
                            prenda_id=item["id"], producto=item["producto"], tipo="venta",
                            cantidad=item["cantidad"], precio_unitario=item["precio_unitario"],
                            costo_unitario=item["costo_unitario"], pagado=fue_pagada,
                            medio_pago=medio_pago_venta, venta_id=venta_id_nv, cliente=cliente_final_nv,
                        )

                    if fue_pagada:
                        st.session_state.carrito_venta_nueva = []
                        st.success(f"¡Venta registrada como pagada! Total: {moneda(total_venta_nueva)}")
                        st.rerun()
                    else:
                        nombre_persona_final_nv = cliente_final_nv
                        if id_persona_final_nv:
                            descripcion_pedido_nv = ", ".join(f"{i['cantidad']}× {i['producto']}" for i in st.session_state.carrito_venta_nueva)
                            deudores_actualizado_nv = cargar_deudores()
                            fila_persona_nv = deudores_actualizado_nv[deudores_actualizado_nv["id"].astype(str) == str(id_persona_final_nv)].iloc[0]
                            saldo_actual_nv = float(fila_persona_nv.get("saldo", 0) or 0)
                            nuevo_saldo_nv = saldo_actual_nv + total_venta_nueva
                            actualizar_saldo_deudor(id_persona_final_nv, nuevo_saldo_nv)
                            registrar_movimiento_deuda(
                                deudor_id=id_persona_final_nv, deudor_nombre=nombre_persona_final_nv,
                                tipo="cargo", descripcion=descripcion_pedido_nv, monto=total_venta_nueva,
                                tasa_cambio=tasa_venta_nv,
                            )
                            if tasa_venta_nv > 0:
                                st.session_state.ultima_tasa = tasa_venta_nv
                            st.session_state.carrito_venta_nueva = []
                            st.success(f"¡Venta registrada como pendiente! Nuevo saldo de {nombre_persona_final_nv}: {moneda(nuevo_saldo_nv)}")
                            st.rerun()

                if not nombre_valido:
                    st.caption("⚠️ Escribe el nombre de la persona nueva para poder confirmar.")

    # -----------------------------------------------------------------------------
    # VENTAS PAGADAS (historial de ventas cobradas de una vez)
    # -----------------------------------------------------------------------------
    elif menu == "ventas_pagadas":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">✅ Ventas Pagadas</div>
    <div class="page-subtitle">Historial de ventas que se cobraron completas al momento (sin fiar).</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs_todos = cargar_movimientos()
        ventas_pagadas_df = movs_todos[(movs_todos["tipo"] == "venta") & (movs_todos["pagado"] == True)] if not movs_todos.empty else pd.DataFrame()  # noqa: E712

        total_pagado_hist = float((ventas_pagadas_df["cantidad"] * ventas_pagadas_df["precio_unitario"]).sum()) if not ventas_pagadas_df.empty else 0.0
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Vendido (pagado)</div><div class="metric-value">{moneda(total_pagado_hist)}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Cantidad de Ventas</div><div class="metric-value">{len(ventas_pagadas_df)}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if ventas_pagadas_df.empty:
            st.info("Todavía no hay ventas pagadas registradas. Usa 'Nueva Venta' para empezar.")
        else:
            render_tabla_movimientos(ventas_pagadas_df)

    # -----------------------------------------------------------------------------
    # COMPRAR / REPONER STOCK
    # -----------------------------------------------------------------------------
    elif menu == "comprar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">📦 Registrar Compra a Proveedores</div>
    <div class="page-subtitle">Suma unidades al stock existente y registra a quién le compraste y cuánto pagaste.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas. Primero registra una prenda desde el menú correspondiente.")
        else:
            proveedor_nombre = st.text_input("Proveedor", placeholder="Ej: Textiles Andina, María la mayorista, etc.")

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

            monto_total_compra = cantidad_comprar * costo_unit
            st.markdown(f"**Monto total de la compra: {moneda(monto_total_compra)}**")

            actualizar_costo = st.checkbox("Actualizar el costo registrado de esta prenda con este valor", value=True)

            proveedor_valido = proveedor_nombre.strip() != ""

            if st.button("📦 Confirmar Compra", use_container_width=True, disabled=not proveedor_valido):
                datos_act = fila.to_dict()
                datos_act["cantidad"] = int(fila["cantidad"]) + int(cantidad_comprar)
                if actualizar_costo:
                    datos_act["costo"] = costo_unit
                if actualizar_prenda(id_compra, datos_act):
                    registrar_movimiento(
                        prenda_id=id_compra, producto=fila["Producto"], tipo="compra",
                        cantidad=cantidad_comprar, costo_unitario=costo_unit,
                        proveedor=proveedor_nombre,
                    )
                    st.success(f"¡Compra registrada a {proveedor_nombre}! Total: {moneda(monto_total_compra)}")
                    st.rerun()

            if not proveedor_valido:
                st.caption("⚠️ Escribe el nombre del proveedor para poder confirmar.")

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
            encabezado_seccion_form("📦", "Información Básica")
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("ID", placeholder="Ej: A1")
            with col2:
                nombre = st.text_input("Producto", placeholder="Ej: Short")

            encabezado_seccion_form("🏷️", "Clasificación y Atributos")
            col3, col4, col5 = st.columns(3)
            with col3:
                categoria = st.selectbox("Categoría", st.session_state.categorias_maestras)
            with col4:
                talla = st.selectbox("Talla", st.session_state.tallas_maestras)
            with col5:
                color = st.selectbox("Color", st.session_state.colores_maestros)

            encabezado_seccion_form("📊", "Control de Stock, Precios y Alertas")
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

            encabezado_seccion_form("📷", "Foto del producto (opcional)")
            foto_subida = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg", "webp"])

            st.markdown("<br>", unsafe_allow_html=True)
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

            st.markdown("<br>", unsafe_allow_html=True)
            render_tabla_movimientos(movs_filtrado)

            csv_movs = movs_filtrado.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button("📥 Exportar Movimientos a CSV", data=csv_movs,
                                file_name="movimientos_lewin.csv", mime="text/csv")

    # -----------------------------------------------------------------------------
    # FACTURAS
    # -----------------------------------------------------------------------------
    elif menu == "facturas":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">🧾 Facturas</div>
    <div class="page-subtitle">Elige una venta y descarga su factura en PDF.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if not PDF_DISPONIBLE:
            st.warning("Falta instalar la librería para generar PDF. Agrega `fpdf2` a tu requirements.txt para activar esta función.")

        movs_fact = cargar_movimientos()
        ventas_con_id = movs_fact[(movs_fact["tipo"] == "venta") & (movs_fact["venta_id"] != "")] if not movs_fact.empty else pd.DataFrame()

        if ventas_con_id.empty:
            st.info("Todavía no hay ventas con factura disponible. A partir de ahora, cada venta que registres desde 'Nueva Venta' generará su propia factura automáticamente.")
        else:
            ventas_con_id = ventas_con_id.copy()
            ventas_con_id["subtotal"] = ventas_con_id["cantidad"] * ventas_con_id["precio_unitario"]
            resumen_facturas = ventas_con_id.groupby("venta_id").agg(
                fecha=("fecha", "first"), cliente=("cliente", "first"),
                pagado=("pagado", "first"), total=("subtotal", "sum"),
            ).reset_index().sort_values("fecha", ascending=False)

            opciones_venta_id = resumen_facturas["venta_id"].tolist()
            venta_sel = st.selectbox(
                "Elige la venta",
                opciones_venta_id,
                format_func=lambda x: (
                    f"{formatear_fecha_corta(resumen_facturas[resumen_facturas['venta_id'] == x]['fecha'].values[0])} — "
                    f"{resumen_facturas[resumen_facturas['venta_id'] == x]['cliente'].values[0]} — "
                    f"{moneda(resumen_facturas[resumen_facturas['venta_id'] == x]['total'].values[0])}"
                    + ("" if resumen_facturas[resumen_facturas['venta_id'] == x]['pagado'].values[0] else " (pendiente)")
                ),
            )

            items_venta_sel = ventas_con_id[ventas_con_id["venta_id"] == venta_sel]
            fila_resumen = resumen_facturas[resumen_facturas["venta_id"] == venta_sel].iloc[0]

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Vista previa</div>", unsafe_allow_html=True)

            filas_preview = ""
            for _, r in items_venta_sel.iterrows():
                filas_preview += f"""<tr>
<td>{r['producto']}</td>
<td style="text-align:center;">{int(r['cantidad'])}</td>
<td style="text-align:right;">{moneda(r['precio_unitario'])}</td>
<td style="text-align:right;">{moneda(r['cantidad'] * r['precio_unitario'])}</td>
</tr>"""
            st.markdown(
                f"""<div class="tabla-movimientos-wrapper"><table class="tabla-movimientos">
<thead><tr><th>Producto</th><th>Cant.</th><th>Precio Unit.</th><th>Subtotal</th></tr></thead>
<tbody>{filas_preview}</tbody></table></div>""",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"**Cliente:** {fila_resumen['cliente']}  \n"
                f"**Fecha:** {formatear_fecha_corta(fila_resumen['fecha'])}  \n"
                f"**Total: {moneda(fila_resumen['total'])}**"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if PDF_DISPONIBLE:
                items_para_pdf = items_venta_sel[["producto", "cantidad", "precio_unitario"]].to_dict("records")
                pdf_bytes = generar_factura_pdf(
                    venta_sel, fila_resumen["cliente"], formatear_fecha_corta(fila_resumen["fecha"]),
                    items_para_pdf, fila_resumen["total"],
                )
                st.download_button(
                    "📄 Descargar Factura en PDF", data=pdf_bytes,
                    file_name=f"factura_{str(venta_sel)[:8]}.pdf", mime="application/pdf",
                    use_container_width=True,
                )

    # -----------------------------------------------------------------------------
    # DEUDORES (cuentas por cobrar)
    # -----------------------------------------------------------------------------
    elif menu == "deudores":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">🧾 Ventas por Pagar</div>
    <div class="page-subtitle">Lleva el control de quién te debe, cuánto le fiaste y cuánto te ha pagado.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        deudores_df = cargar_deudores()
        total_por_cobrar = float(deudores_df["saldo"].sum()) if not deudores_df.empty else 0.0
        cantidad_deudores = int((deudores_df["saldo"] > 0).sum()) if not deudores_df.empty else 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Total por Cobrar</div><div class="metric-value">{moneda(total_por_cobrar)}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Personas que Deben</div><div class="metric-value">{cantidad_deudores}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("👥 Ver todas las personas registradas"):
            if deudores_df.empty:
                st.info("Todavía no has agregado a nadie.")
            else:
                deudores_ordenado = deudores_df.sort_values("saldo", ascending=False)
                for _, fila in deudores_ordenado.iterrows():
                    saldo_val = float(fila.get("saldo", 0) or 0)
                    color_saldo = "#f472b6" if saldo_val > 0 else "#34d399"
                    telefono_txt = fila.get("telefono") or "—"
                    st.markdown(
                        f"<div class='config-chip' style='justify-content: space-between;'>"
                        f"<span>{fila['nombre']} <span style='color: var(--text-secondary); font-size: 11px;'>({telefono_txt})</span></span>"
                        f"<span style='color: {color_saldo}; font-weight: 700;'>{moneda(saldo_val)}</span></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<br><hr style='border-color: var(--border-color);'><br>", unsafe_allow_html=True)

        # =========================================================================
        # SECCIÓN 2: BUSCAR PERSONA Y COBRAR
        # =========================================================================
        st.markdown("<div class='section-title'>🔍 Buscar Persona y Cobrar</div><div class='section-subtitle'>Encuentra a alguien para ver su saldo, su historial, o registrarle un pago.</div>", unsafe_allow_html=True)

        if deudores_df.empty:
            st.info("Todavía no hay personas registradas. Usa la sección de arriba para agregar la primera.")
        else:
            ids_buscar = deudores_df["id"].astype(str).tolist()
            id_buscado = st.selectbox(
                "Escribe o selecciona el nombre",
                ids_buscar,
                format_func=lambda x: deudores_df[deudores_df["id"].astype(str) == x]["nombre"].values[0],
                key="select_buscar_persona",
            )
            fila_buscada = deudores_df[deudores_df["id"].astype(str) == str(id_buscado)].iloc[0]
            saldo_buscado = float(fila_buscada.get("saldo", 0) or 0)
            color_saldo_buscado = "#f472b6" if saldo_buscado > 0 else "#34d399"
            telefono_buscado = fila_buscada.get("telefono") or "—"

            st.markdown(
                f"""<div class="product-card" style="border-color: var(--border-color);">
<div class="product-card-body">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<div style="font-size: 18px; font-weight: 700; color: var(--text-color);">{fila_buscada['nombre']}</div>
<div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">📞 {telefono_buscado}</div>
</div>
<div style="font-size: 24px; font-weight: 800; color: {color_saldo_buscado};">{moneda(saldo_buscado)}</div>
</div>
</div>
</div>""",
                unsafe_allow_html=True,
            )

            col_pago1, col_pago2 = st.columns(2)
            with col_pago1:
                moneda_pago_sel = st.radio("¿En qué moneda pagó?", ["Dólares ($)", "Bolívares (Bs)"], horizontal=True, key="moneda_pago_sel")
            with col_pago2:
                medio_pago_sel = st.selectbox(
                    "Medio de pago",
                    ["Efectivo", "Pago Móvil", "Transferencia", "Zelle", "Otro"],
                    key="medio_pago_buscar",
                )

            if moneda_pago_sel == "Bolívares (Bs)":
                tasa_cobro, fuente_tasa_cobro = selector_tasa_cambio("cobro")
                monto_bs_ingresado = st.number_input("Monto recibido en Bs", min_value=0.0, step=1.0, key="monto_bs_cobro")
                monto_pago_usd = (monto_bs_ingresado / tasa_cobro) if tasa_cobro > 0 else 0.0
                if tasa_cobro > 0:
                    st.caption(f"💱 Equivalente: {moneda(monto_pago_usd)}")
                else:
                    st.caption("⚠️ Elige una tasa para poder calcular el equivalente en dólares.")
            else:
                tasa_cobro = 0.0
                monto_pago_usd = st.number_input("Monto recibido en $", min_value=0.0, step=1.0, key="monto_usd_cobro")

            nota_pago = st.text_input("Nota (opcional)", placeholder="Ej: abono parcial", key="nota_pago_buscar")

            if st.button("💵 Registrar Este Pago", use_container_width=True, key="btn_registrar_pago_buscar"):
                if monto_pago_usd <= 0:
                    st.error("El monto debe ser mayor a 0.")
                else:
                    nuevo_saldo_buscado = saldo_buscado - monto_pago_usd
                    actualizar_saldo_deudor(id_buscado, nuevo_saldo_buscado)
                    registrar_movimiento_deuda(
                        deudor_id=id_buscado, deudor_nombre=fila_buscada["nombre"],
                        tipo="abono", descripcion=nota_pago, monto=monto_pago_usd,
                        medio_pago=f"{medio_pago_sel} ({moneda_pago_sel})", tasa_cambio=tasa_cobro,
                    )
                    st.success(f"¡Pago registrado! Nuevo saldo de {fila_buscada['nombre']}: {moneda(nuevo_saldo_buscado)}")
                    st.rerun()

            with st.expander(f"📜 Historial de {fila_buscada['nombre']}"):
                deudas_mov_todas = cargar_deudas_movimientos()
                historial_persona = deudas_mov_todas[deudas_mov_todas["deudor_id"].astype(str) == str(id_buscado)] if not deudas_mov_todas.empty else pd.DataFrame()
                if historial_persona.empty:
                    st.info("Todavía no hay movimientos con esta persona.")
                else:
                    render_tabla_deudas(historial_persona)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🗑️ Eliminar a {fila_buscada['nombre']} del sistema", key="btn_eliminar_persona_buscada"):
                if eliminar_deudor(id_buscado):
                    st.success(f"{fila_buscada['nombre']} fue eliminada/o.")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📜 Historial General</div><div class='section-subtitle'>Todos los cargos y abonos registrados, de todas las personas.</div>", unsafe_allow_html=True)
        deudas_mov = cargar_deudas_movimientos()
        if deudas_mov.empty:
            st.info("Aún no hay movimientos de deudores registrados.")
        else:
            render_tabla_deudas(deudas_mov)

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🗑️ Eliminar un movimiento del historial"):
                opciones_mov = deudas_mov["id"].astype(str).tolist()
                mov_a_borrar = st.selectbox(
                    "Elige el movimiento a eliminar",
                    opciones_mov,
                    format_func=lambda x: (
                        f"{formatear_fecha_corta(deudas_mov[deudas_mov['id'].astype(str) == x]['fecha'].values[0])} — "
                        f"{deudas_mov[deudas_mov['id'].astype(str) == x]['deudor_nombre'].values[0]} — "
                        f"{deudas_mov[deudas_mov['id'].astype(str) == x]['tipo'].values[0]} — "
                        f"{moneda(deudas_mov[deudas_mov['id'].astype(str) == x]['monto'].values[0])}"
                    ),
                    key="select_borrar_deuda_mov",
                )
                st.caption("Al eliminarlo, el saldo de esa persona se ajusta automáticamente. Nota: si el movimiento borrado era un cargo de productos, el stock NO se devuelve solo — ajústalo manualmente en 'Editar / Borrar' si hace falta.")
                if st.button("Eliminar este movimiento", key="btn_borrar_deuda_mov"):
                    fila_a_borrar = deudas_mov[deudas_mov["id"].astype(str) == str(mov_a_borrar)].iloc[0]
                    if eliminar_movimiento_deuda(
                        movimiento_id=mov_a_borrar,
                        deudor_id=fila_a_borrar["deudor_id"],
                        tipo=fila_a_borrar["tipo"],
                        monto=fila_a_borrar["monto"],
                    ):
                        st.success("Movimiento eliminado y saldo actualizado.")
                        st.rerun()

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

        col_reset1, col_reset2 = st.columns([3, 1])
        with col_reset2:
            if st.button("🔄 Restablecer Reportes", use_container_width=True):
                st.session_state.confirmar_reset_reportes = True

        if st.session_state.get("confirmar_reset_reportes"):
            st.markdown(
                "<div class='alert-banner'>⚠️ <b>¿Seguro que quieres restablecer el apartado de Reportes?</b><br>"
                "Esto borrará TODO el historial de ventas y compras registrado hasta ahora (también desaparecerá de "
                "'Movimientos'), para que puedas empezar a usar la app desde cero. Esta acción no se puede deshacer, "
                "y no toca tus prendas ni el stock actual.</div>",
                unsafe_allow_html=True,
            )
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("✅ Sí, restablecer todo", use_container_width=True):
                    if eliminar_todos_los_movimientos():
                        st.session_state.confirmar_reset_reportes = False
                        st.success("¡Listo! Los reportes y el historial de movimientos quedaron en cero.")
                        st.rerun()
            with col_c2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_reset_reportes = False
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

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
            if len(ventas_mes) < 2:
                st.caption("Con solo un mes de datos el gráfico se ve muy simple — se vuelve más útil a medida que registres ventas en distintos meses.")
            st.plotly_chart(grafico_barras_vertical(ventas_mes, formato_valor=moneda), use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='section-title'>Top 5 productos más vendidos (unidades)</div>", unsafe_allow_html=True)
            top_productos = ventas.groupby("producto")["cantidad"].sum().sort_values(ascending=False).head(5)
            st.plotly_chart(grafico_barras_horizontal(top_productos), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Aún no hay ventas registradas para generar gráficas. Usa el menú 'Vender' para empezar a registrar.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_dona1, col_dona2 = st.columns(2)

        with col_dona1:
            st.markdown("<div class='section-title'>Inventario por categoría</div>", unsafe_allow_html=True)
            if not df.empty:
                inv_por_cat = df.groupby("Categoria")["cantidad"].sum()
                inv_por_cat = inv_por_cat[inv_por_cat > 0]
                if not inv_por_cat.empty:
                    st.plotly_chart(
                        grafico_dona(inv_por_cat, texto_centro_arriba=str(int(inv_por_cat.sum())), texto_centro_abajo="unidades"),
                        use_container_width=True, config={"displayModeBar": False},
                    )
                else:
                    st.info("No hay stock registrado todavía.")
            else:
                st.info("No hay prendas registradas todavía.")

        with col_dona2:
            st.markdown("<div class='section-title'>Ventas por categoría</div>", unsafe_allow_html=True)
            if not ventas.empty and not df.empty:
                ventas_cat = ventas.copy()
                ventas_cat["prenda_id"] = ventas_cat["prenda_id"].astype(str)
                mapa_categoria = df.set_index(df["ID"].astype(str))["Categoria"]
                ventas_cat["Categoria"] = ventas_cat["prenda_id"].map(mapa_categoria)
                ventas_por_cat = ventas_cat.dropna(subset=["Categoria"]).groupby("Categoria")["cantidad"].sum()
                ventas_por_cat = ventas_por_cat[ventas_por_cat > 0]
                if not ventas_por_cat.empty:
                    st.plotly_chart(
                        grafico_dona(ventas_por_cat, texto_centro_arriba=str(int(ventas_por_cat.sum())), texto_centro_abajo="vendidas"),
                        use_container_width=True, config={"displayModeBar": False},
                    )
                else:
                    st.info("Aún no hay suficientes ventas para mostrar por categoría.")
            else:
                st.info("Aún no hay ventas registradas.")

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
                encabezado_seccion_form("📂", "Categorías")
                for cat in list(st.session_state.edit_cats):
                    c_col1, c_col2 = st.columns([4, 1])
                    with c_col1:
                        st.markdown(f"<div class='config-chip'>{cat}</div>", unsafe_allow_html=True)
                    with c_col2:
                        if st.button("✕", key=f"del_cat_{cat}", use_container_width=True):
                            if len(st.session_state.edit_cats) > 1:
                                st.session_state.edit_cats.remove(cat)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_cat_input = st.text_input("Nueva Categoría", placeholder="Ej: Faldas", key="input_nueva_cat")
                if st.button("➕ Agregar Categoría", key="btn_add_cat", use_container_width=True):
                    clean_cat = nueva_cat_input.strip().capitalize()
                    if clean_cat and clean_cat not in st.session_state.edit_cats:
                        st.session_state.edit_cats.append(clean_cat)
                        st.rerun()
                    else:
                        st.warning("Nombre inválido o ya existente.")

        with col_cfg2:
            with st.container(border=True):
                encabezado_seccion_form("📏", "Tallas")
                for t in list(st.session_state.edit_tallas):
                    t_col1, t_col2 = st.columns([4, 1])
                    with t_col1:
                        st.markdown(f"<div class='config-chip'>{t}</div>", unsafe_allow_html=True)
                    with t_col2:
                        if st.button("✕", key=f"del_talla_{t}", use_container_width=True):
                            if len(st.session_state.edit_tallas) > 1:
                                st.session_state.edit_tallas.remove(t)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_talla_input = st.text_input("Nueva Talla", placeholder="Ej: 30, XXL", key="input_nueva_talla")
                if st.button("➕ Agregar Talla", key="btn_add_talla", use_container_width=True):
                    clean_talla = nueva_talla_input.strip().upper()
                    if clean_talla and clean_talla not in st.session_state.edit_tallas:
                        st.session_state.edit_tallas.append(clean_talla)
                        st.rerun()
                    else:
                        st.warning("Talla inválida o ya existente.")

        with col_cfg3:
            with st.container(border=True):
                encabezado_seccion_form("🎨", "Colores")
                for col_item in list(st.session_state.edit_colores):
                    col_c1, col_c2 = st.columns([4, 1])
                    with col_c1:
                        st.markdown(f"<div class='config-chip'>{col_item}</div>", unsafe_allow_html=True)
                    with col_c2:
                        if st.button("✕", key=f"del_color_{col_item}", use_container_width=True):
                            if len(st.session_state.edit_colores) > 1:
                                st.session_state.edit_colores.remove(col_item)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos uno.")
                st.markdown("<br>", unsafe_allow_html=True)
                nuevo_color_input = st.text_input("Nuevo Color", placeholder="Ej: Dorado", key="input_nuevo_color")
                if st.button("➕ Agregar Color", key="btn_add_color", use_container_width=True):
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
