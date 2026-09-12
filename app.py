import base64
import json
import textwrap
import urllib.parse
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

try:
    import fitz  # PyMuPDF
    IMAGEN_FACTURA_DISPONIBLE = True
except ImportError:
    IMAGEN_FACTURA_DISPONIBLE = False

st.set_page_config(
    page_title="Lewin // Inventario Boutique", page_icon="\U0001F455", layout="wide"
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

LOGO_LEWIN_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAHgAAACRCAYAAAAIL3yYAABuxklEQVR42uz9d7ym91nfib+vb7nL006frjLqvViyZYMByRQHgwMJ0SS/JMBmlwDJZn/ZkF3SMxo2YQNZyDohJjiFxEAMI0IzGIOxZyxwkT2jZtWRpmj6zDlz2lPv8v1e+8f9jCxMNRG2HLhfr0flpdGZM+e6r/65Ph/hj/PZu9ewb188s6mLv/noE989HAy+yVr7hhgqSRIfU+/e387cE71u+xffeveNTwAcOHDAPfDAAzV/+rwmj/yxfFVV4aGHxHzfvviv/tujezY2B//PoD+8oq6UUNXk3tNKPduW5pjp5aTWTHrd9s95Cd//Ffdd/8yhQ+rvvVeqPzXP69HAqvLgww+b/Q8+qN//3g++98TF4V/ZGARM1ECNuKhmJmuzNDvHfK8Xup1EXIJZWJzBuWI1UO77+rfc+K/3Hjjg9v2pJ7/+DLx3716zb9+++H+995f//YmLxXdcXBnWIsaaoOIqpWta7N62i7nWDEni8bnBZ4Zo6jqf8a7dkZAm5Xd8zd3X/ef9qnaPSPhTM71ODLxX1ewTiT/6/g/f+dhz5x4/uaZ1COpMVUqilq6m7F64gkU/RyvNkTziWg5pWTQRQlrHrGt11/Z5O+wv/6N33rn7+1XVyp8a+Y/8mNfyiz378MOiqubEy8v/9MLaSMZFkMm4lFAGtFR62Qxt18HWCdQG1UDQSA2UBkpjzCBgTixvVL638M9/5enj/0BEwv79++2fmuqP9rjXLvWqiEg4NdSdFy9tfsPGxlBFgjUhEkLE+Yy51gw+GAQIWjd/FwUJKILgCGpkGKI7s7YRtnbz7/+NF05++KtvuOLTqmpEJP6pyb5IHvzQwYMW4IMf+ehXj8eVn4yqEGuVWAZipVgMzjhiAA1KDEKoIdRKqCMhKPX070FExnXQifE6qOofFhF96Ev4h6yqoqp2v6pVVbt/v9oDBw64/fvVfsl48LPvXlaA8froLRtrmyZUNlYxYBGsMTjxxBo0QhSBKBAsMQhEQ4ygCihEhUpxy8NRXMxbd//CkRO3fLPIs18qXrx/v9qlpYNy8ODBCDD9nr8odcRrZuCHH96jqirvft+H3rq+ukGUniAKKsQAoYayihShxrqIrS1aCqSWWIE6UK9ohBBArGejijo712uZfvWPgL/y0MGDBnjdG3jPnt9eFD62qUtmvHHPxsWLsRoMrBSTTitvfdXs/MzMeDx+7xvuuOVD0xSnr1sDT99U/bfv+/W+KhSTgsS2ETGoWKo6UhY1tUmpYmMmqQWtTROW64gGRWslBohREDVmZXOkWzDv+NCjzy587X23XPrj+kF8bkgF5HPTwvTf9XN///3ahNoHQQF+/vjZd6YuW2oV9cGqLv/++pnT31QN+oupMXTyLiHqbxH5lY1La//+vvvufvryz+5168HT9kifP75805NHTtwaQxlRZ1QDigFjqOpAUdUED1VQxCg2CDEqMSh1rWgdUR+INQRnwVjZHBf19rnWzLgcfQXwCwebXF//cRj14YcfNnv27AnTH/bv+IHv++0F5Sv//XKv/rRqcptI+avPL3/Ttt78Xzt57IlQlJWN4xGLMz2SLD3m6vjv3/zl9/yL3+33P3jwoL3//vvDa2ns18TA94PZB/XK5vm/sbDU7fVaSd1fLpygRBSnQgjKpK4JiUBUQhWITpCJEq1BrVDXEKuIGgtGwCiFKIVEiTZuATj4mufL/faZpSURkRoIqioPP/PMXOe667adX1+3ThJTaKl1jPXc4vZeWN24KCLHLr/YD4H+yjPnvtMo5jaRH3386ZU3XTp79qvPHD1STQZrbNu2xeYz86HX7bw3Ffm+q2+6+uVDhw75fr+vBw8ejPv27Yt7975SW9Sv6xDtNGieeL1q13bOXTyBEY+IBwRFGJclY1+TOECaFG2ioFHQoBAEaiGaCMaAgRijjIYF7bL+FuA9ty7fr6+Ftz40HfJc9r79R4/OVKn7yp86c+ENcsXV33luMH5pYtw9aZ63vZthNjP0V4fH19zmV3ynHvLbuUdvfRiVPRI/cGTtU93h4Js++pvPvGf1/Mt/fdRfj92Z3Fx51XVkSfILdVl9+KZbrvmRV30LFYDuV/vQ3oeM7JP4+IHHZydJ/b0uMetvfOM9P7h/v9rPzeVfNAMvP/ywArQS8zNrw/7fvvbqJfPcC+eoJzVp1kJEAMNoXNA3I3wrJ7UGG8BGA7USSiVaUAwqipEIYohlIHihLuJ/19u9d+9ec+tDD8kekd8Wgv/r8vK9lciDQ8N3lHXsltG/LNgd41jtMDiljEUxHD6htvtTblXvuqlc/Kd3npv9KjO6cORte7b92RPPr+2+cObcd128dP7bszzNohRce912Ey0vRgk/+1M/9V/+8b59++KBAwfc5fCrqvLQQw+JTA34xMEnvse1/A8MJuPTEszb9u7dax588LUpJl8TAy8tLQlArOv7296yZbalV+2Y46Xjm1jfxuAwFjDCuC4Z1gXGOepacWXAmKZ1UhSNsSnAIkiMOBNxZSTDZH/kMHx5pr2vyaIHLlzobPa2bFvZuPiuIs/eURnPeFxQxUirN3NdXdV4EjouFTsKJ/26/mp6dHOh6/xb2s7enIzHY4M5/qkPH/0HJ4+d+O6yHlwZwljzTkZvfnE9yc1vTerxv7jzprs/tn//fjsdt9YA+tlwrKc/dv6rz65f+DuD4eQbcqdPLs3Of9tNd9x0fNoO6uvGwMvLTQ9sRR4JITDbcnLrdVvZWD3BcNLHtxZxImgMVCFQ1iVVTPHiIJgmYElE1DTdooKoYqOSJgFXR1oZx/5IhoW4RyT86okT28et1g3tEA6dUPlUNRreULdnbH8wVKNVMGo09d4Vm/0LbZety0jrdHPc69C6PgnJQ7MG6ouXyE3YNEmZXlw/89aNjZU/k7TB5lrsvnl3KhKfmZ2ZffuVV155Bn7nblsPqJMHpH7uF57bYdvpvjPnz33HerHO9uu3Eaj/15vuuOmpQ4cOeZHXblX6mubgGM3YGkM3S9k21+LW67fy1HObEGrEOEQADYyLMQZL22dojNhoMWqaCUfUJv+KYohYgubiSDDvb6LFwT9wQbJX1ewD3SMSdP9++/MXL/75NWP/WeWSG05OiuNqkt1lqYSyCBZnbFTT6XRNq2U4v7r5Lb3l8s/M2Nb3xAv9mFWTaCYhOC2k7eKFshq0Tp9/OV0ZnknbM2lMe21m5mddksrp0aD621deeeWZQ4cO+fe///3hsnEVFRQRkfqJX3x+t1r34Y2Njd3n1k6V196529jc/NNyUjy+f//+5N577y1fz32wES847+l1Uq7a3mI8qTh6chWqGVp5h6iGGGom5RhUSIHEGJxErEYMFitgQ01LK3xYZyaZp9cy7c9nowWw/9yFv/8zeWfPOMrdG3VksFlEn2W7Q1GqM6k4gjFEXViaM8NL/Z8qL5kP3VK2vrXaKN7hRuN2OlFtx1rQyuBKVkcrO09deJHaj5nb3qU32zZpbuuFhVk77g//6T33vOnDn2uk/fv3Wx4kikh89peOfod32b7lwYUda8VKfc2duy05e2657cafU5B7f5fW7HVlYKg0qo3GGpLU0207du7ICSgXz21SjCN5toR1HUJdUeiYqJGoShIsPioeAxJJLTBZR/yGtNxMSI1eArj//t+9it67d6/hoYfYJxJ/4cSJW/rG/dio3XnrWlHTHxWhFC/GOBOLIhqDqeMk5NbZjm9JXJ38zO6y+2ObK8Mfzay71W6O0P4o9PKODWHzos/onrh4LD+39rK25xJm53vS6uRkeRZS5zXVTMq6Tpvi6MFXKt/9D+63e/bsCT/+4z+ePfVzz/6Mt/7PrvSXWa/WwsKOuRMxCd911+13fWTaV7++R5VN++F83srMph3EPEsp8xa9TsXWRUM7SVlfmzAankPCLHkyS9SAaEUMJTE4RC0WgzcF5XiNIl7S227dZSWMj4dCDlzOBL/DuJfRH/v28V+PHv8H/bz30BqSXFxZC0GsGOOt0PTf0ajRUMdWZ8bmlZnYcfjn+cl6iTR7pRLAYrQkAJ41VjUqMRq1BhEVNRo1mkn0pU6Tf2jT2Nq4tLY8/vKrn/1Tf3V27c69994bHzx4UP77cTdfX3d23x+f/s/f+s0Tf+f502c3gYqE2vTKiq0N2zuzds38vNt19Y45u31+Loml5yvj6qf0Z178X8xP/sNPPb38Qx/6tSOPv/T86T6G2hgl1qYyVkwlVNWY8biiv75KXxsqn1I2CWF9k6q/Tj90aRk40N7w59/x5m97+Jvf9jV37N+/P772591+Y577wP374wMPPvKjP/3k4V8eXFylbJqmP48qKsbUhG53vnvn3Xff/ZZ3vP0b37m13XpXGftXq6L450f7p4+/632fOH1q9TJrG1Pzttac6Rgbg1g1m70+a8tLrK5doG9K1scZg/U1Noc1I4iE9S3yPfe95U++50ffdf+BAwfq1/jU67f5/e8/sB9U8eHHjvzLnz9y9Cd7F1doxR6tQWpDE2J4Y6iLCYtrZ4jG0t25k82sYHVzSH9jkyqG47PdsO9X3vW2N/7+X/z2v/h1/2x18/6jR0/c/4kDR39p7ezyiVE1YmwcNR4xSmgqYkXEY8Zj1q5c4uT58/TX11mbjBmu9ZkUJVWosS0/vuHGG9/+4X/x/r+z7/f3mF63b/sP97z7fftiVeXBXzhy9CcOHzn63qPPLm9fH4wYFSVlVRNihTGmSUtSg7eaZrFjHXVVMx5NGA1HJqYpkyR55jZ7a2ff8Q3f+LGP/vP3/qG8vXfu3m02fv2j9505c/Fn/uPjT3389JlL65uDkfT7Y7a2tlidbFJWNXUIIQ197W29wXq750vXNrf40bX3v/k//t2//rW/+033fNNDe/a8+v29L9yV0uv17AcfPNBc1T94+Ld/+9Pvf/z4Kx9eubS5OewP6G9sMh6PKcsxRVmiNggu7dt+f9jMbm311ze26K9uML40oL/eZzwYUZQVY9N/srm04s1m8Wn33fP3/t09b77v98W6e9V1Xn1wvxq9evj91642q8r6f/zUk/8k1u4v/t6R55bOXdrg0vlLrK+tMh6OGQ1HDKfGLaqKiPq+rIeXNjeG/ZWV9X7/0iW2Njfo9zdY6/epygld11pud5c+8+Y3f/333vu2+/5/b7nptgNf4hXf1/6E6vd/7k/Uq0Xl/sPjR//hY8df+c7HL5xbGgyGrG/0GPR79NdWGQ1H1CGEsq59URaDfm/j4kZ/fWNjY2Njc3NzffVi/+KlVdY3N7i0scF4PCY/9aK7+tpr3vr5d7zrXfe95zve+bH9+/fvP7B/f7ycn7/q6b2uPfjhffvC/vf+Tvyv/+rX/q5pPvf5y5vDfq8/YGPQZ2Njk62tLXq9Hpv9DfphwGAwGLz44ouvvPDCCxfPX1rZeHFpud/r9fr9jfXBZDxj+Z97h9t11W23P/n2b/qGv/uWN9/1i9NT7b6HvvQ99vft/e3x90PzI8/8x2M//ujT79/qj6631vRssG02t7bY2NzkuZdfZnV9hfGkYnNzfXB588pLL5w7d+X4iRP9y5vrsrG27q21+n9567tP3v7mN375n/uGOx/9Q7yvL/1Z7wF76OGH7eH9f/h93/jHf3zX/b//o//0V0+evXBzv98f9Psbtm6s32tq30zK/sW+9K/8yve89Wf3798ff5ff83f982D/7/005eHDh/2+ffviA/v3xy9Fhfjv8c1/y1XwFz2/fUa5f789+NBDIq/1yYn79u2L+ff1T1/476/5d31F1f0q5w+sJ/3z93zD7+v5/H8wAP8H99oZfL8+v3sAAAAASUVORK5CYII="

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
    tallas_default = ["XS", "S", "M", "L", "XL", "\u00danica"]
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
        st.warning("No hay conexi\u00f3n a la base de datos para registrar el movimiento.")
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
        st.warning("No hay conexi\u00f3n a la base de datos.")
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
        st.warning("No hay conexi\u00f3n a la base de datos.")
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
    if not supabase:
        st.warning("No hay conexi\u00f3n a la base de datos.")
        return False
    try:
        deudores_actual = cargar_deudores()
        fila_deudor = deudores_actual[deudores_actual["id"].astype(str) == str(deudor_id)]
        if not fila_deudor.empty:
            saldo_actual = float(fila_deudor.iloc[0].get("saldo", 0) or 0)
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
            repo.update_file(file.path, "Actualizaci\u00f3n autom\u00e1tica de configuraci\u00f3n de inventario",
                              contenido, file.sha, branch="main")
        except Exception:
            repo.create_file("config.json", "Creaci\u00f3n inicial de configuraci\u00f3n de inventario",
                              contenido, branch="main")
        cargar_config_github.clear()
        cargar_datos_completos.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuraci\u00f3n en GitHub: {e}")
        return False

def subir_imagen(archivo, prenda_id):
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
    tasas_disponibles = obtener_tasas_cambio()
    opciones = list(tasas_disponibles.keys()) + ["Manual"]
    if not tasas_disponibles:
        st.caption("\u26a0\ufe0f No se pudo conectar con la API de tasas en este momento; usa 'Manual'.")

    fuente_sel = st.selectbox("Tasa de cambio", opciones, key=f"{key_prefix}_fuente_tasa")

    if fuente_sel == "Manual":
        tasa_valor = st.number_input("Escribe la tasa manualmente", min_value=0.0, step=0.01, value=valor_por_defecto, key=f"{key_prefix}_tasa_manual")
    else:
        info_tasa = tasas_disponibles[fuente_sel]
        tasa_valor = info_tasa["valor"]
        st.caption(f"\U0001f4b1 {fuente_sel}: {tasa_valor:,.2f} Bs \u2014 actualizado {formatear_fecha_corta(info_tasa['fecha'])}")

    return tasa_valor, fuente_sel

def logo_svg_markup(size=30):
    alto = round(size * 1.208)
    return f'<img src="data:image/png;base64,{LOGO_LEWIN_BASE64}" width="{size}" height="{alto}" style="display:block; object-fit:contain;" />'

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
    filas_html = ""
    for _, fila in df_deudas.iterrows():
        tipo = str(fila.get("tipo", ""))
        if tipo == "cargo":
            badge = "<span style='background: rgba(244,114,182,0.15); color:#f472b6; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Cargo (le fi\u00e9)</span>"
        elif tipo == "abono":
            badge = "<span style='background: rgba(52,211,153,0.15); color:#34d399; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Abono (pag\u00f3)</span>"
        else:
            badge = f"<span style='background: rgba(219,39,119,0.15); color:var(--accent); padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>{tipo.capitalize()}</span>"

        descripcion_txt = fila.get("descripcion", "") or "\u2014"
        medio_pago_txt = fila.get("medio_pago", "") or "\u2014"
        tasa_val = float(fila.get("tasa_cambio", 0) or 0)
        tasa_txt = f"{tasa_val:,.2f}" if tasa_val > 0 else "\u2014"
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
<th>Fecha</th><th>Persona</th><th>Tipo</th><th>Descripci\u00f3n</th><th>Monto</th><th>Medio de Pago</th><th>Tasa</th><th>Usuario</th>
</tr></thead>
<tbody>{filas_html}</tbody>
</table>
</div>"""
    st.markdown(tabla_html, unsafe_allow_html=True)

def render_tabla_movimientos(df_mov):
    filas_html = ""
    for _, fila in df_mov.iterrows():
        tipo = str(fila.get("tipo", ""))
        if tipo == "venta":
            badge = "<span style='background: rgba(52,211,153,0.15); color:#34d399; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Venta</span>"
        elif tipo == "compra":
            badge = "<span style='background: rgba(212,175,120,0.15); color:#a78bfa; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>Compra</span>"
        else:
            badge = f"<span style='background: rgba(219,39,119,0.15); color:var(--accent); padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;'>{tipo.capitalize()}</span>"

        proveedor_txt = fila.get("proveedor", "") or "\u2014"
        cliente_txt = fila.get("cliente", "") or "\u2014"
        filas_html += f"""<tr>
<td>{formatear_fecha_corta(fila.get('fecha', ''))}</td>
<td>{fila.get('producto', '')}</td>
<td>{badge}</td>
<td style="text-align:center;">{int(fila.get('cantidad', 0) or 0)}</td>
<td style="text-align:right;">{moneda(fila.get('precio_unitario', 0))}</td>
<td style="text-align:right;">{moneda(fila.get('costo_unitario', 0))}</td>
<td>{cliente_txt}</td>
<td>{proveedor_txt}</td>
<td>{fila.get('usuario', '')}</td>
</tr>"""

    tabla_html = f"""<div class="tabla-movimientos-wrapper">
<table class="tabla-movimientos">
<thead><tr>
<th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cant.</th><th>Precio Unit.</th><th>Costo Unit.</th><th>Cliente</th><th>Proveedor</th><th>Usuario</th>
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
    c = colores_grafico()
    etiquetas = [formato_valor(v) if formato_valor else str(v) for v in serie.values]
    x_valores = [str(v) for v in serie.index]
    fig = go.Figure(data=[go.Bar(
        x=x_valores, y=serie.values,
        marker=dict(
            color=serie.values,
            colorscale=[[0, "#db2777"], [0.5, "#ec4899"], [1, "#f472b6"]],
            line=dict(width=0),
        ),
        text=etiquetas, textposition="outside", textfont=dict(color=c["texto"], size=12),
        hovertemplate="%{x}<br>%{text}<extra></extra>",
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["texto"], family="Poppins, sans-serif"),
        xaxis=dict(type="category", showgrid=False, title=None, tickfont=dict(color=c["texto"])),
        yaxis=dict(showgrid=True, gridcolor=c["grid"], title=None, tickfont=dict(color=c["texto"]), zeroline=False),
        margin=dict(l=10, r=10, t=30, b=10), height=altura, showlegend=False,
        bargap=0.35,
    )
    return fig

def grafico_barras_horizontal(serie, altura=300):
    c = colores_grafico()
    fig = go.Figure(data=[go.Bar(
        x=serie.values, y=list(serie.index), orientation="h",
        marker=dict(
            color=serie.values,
            colorscale=[[0, "#db2777"], [0.5, "#ec4899"], [1, "#f472b6"]],
            line=dict(width=0),
        ),
        text=[str(int(v)) for v in serie.values], textposition="outside", textfont=dict(color=c["texto"], size=12),
        hovertemplate="%{y}<br>%{x} unidades<extra></extra>",
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["texto"], family="Poppins, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor=c["grid"], title=None, tickfont=dict(color=c["texto"]), zeroline=False),
        yaxis=dict(type="category", showgrid=False, title=None, autorange="reversed", tickfont=dict(color=c["texto"])),
        margin=dict(l=10, r=10, t=30, b=10), height=altura, showlegend=False,
        bargap=0.35,
    )
    return fig

def grafico_dona(serie, texto_centro_arriba="", texto_centro_abajo="", altura=340):
    c = colores_grafico()
    paleta = ["#db2777", "#ec4899", "#f472b6", "#fbcfe8", "#f43f5e", "#be185d", "#fb7185", "#fda4af"]
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
        font=dict(color=c["texto"], family="Poppins, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10), height=altura, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color=c["texto"], size=11)),
        annotations=[dict(
            text=f"<b style='font-size:26px'>{texto_centro_arriba}</b><br><span style='font-size:11px'>{texto_centro_abajo}</span>",
            x=0.5, y=0.5, font=dict(color=c["texto"]), showarrow=False,
        )],
    )
    return fig

def generar_factura_imagen(pdf_bytes, cantidad_items):
    if not IMAGEN_FACTURA_DISPONIBLE or not pdf_bytes:
        return None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pagina = doc[0]
        alto_mm = 42 + 20 + 9 + (cantidad_items * 9) + 45
        alto_pt = min(alto_mm * 2.83465, pagina.rect.height)
        recorte = fitz.Rect(0, 0, pagina.rect.width, alto_pt)
        pix = pagina.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=recorte)
        return pix.tobytes("png")
    except Exception as e:
        st.warning(f"No se pudo generar la imagen: {e}")
        return None

def generar_texto_whatsapp_factura(venta_id, cliente, fecha_texto, items_factura, total_factura, pagado):
    lineas = [
        "\U0001f9fe *LEWIN BOUTIQUE*",
        f"Factura N\u00b0 {str(venta_id)[:8].upper()}",
        f"\U0001f4c5 {fecha_texto}",
        f"\U0001f464 Cliente: {cliente or 'Consumidor final'}",
        "",
        "*Productos:*",
    ]
    for item in items_factura:
        cantidad_i = int(item["cantidad"])
        subtotal_i = cantidad_i * float(item["precio_unitario"])
        lineas.append(f"\u2022 {cantidad_i}x {item['producto']} \u2014 {moneda(item['precio_unitario'])} c/u = {moneda(subtotal_i)}")
    lineas.append("")
    lineas.append(f"\U0001f4b0 *TOTAL: {moneda(total_factura)}*")
    lineas.append("\u2705 Pagada" if pagado else "\U0001f552 Pendiente de pago")
    lineas.append("")
    lineas.append("\u00a1Gracias por tu compra! \U0001f49c")
    return "\n".join(lineas)

def generar_factura_pdf(venta_id, cliente, fecha_texto, items_factura, total_factura):
    if not PDF_DISPONIBLE:
        return None
    pdf = FPDF(format="A4")
    pdf.add_page()
    ancho_pagina = pdf.w - 2 * pdf.l_margin

    pdf.set_fill_color(219, 39, 119)
    pdf.rect(0, 0, pdf.w, 32, style="F")
    try:
        logo_bytes = base64.b64decode(LOGO_LEWIN_BASE64)
        pdf.image(BytesIO(logo_bytes), x=12, y=6, w=14, type="PNG")
    except Exception:
        pass
    pdf.set_xy(30, 9)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "LEWIN BOUTIQUE", ln=True)
    pdf.set_xy(30, 18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(253, 242, 248)
    pdf.cell(0, 6, "Factura de venta", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(pdf.w - 90, 9)
    pdf.cell(78, 6, f"N. {str(venta_id)[:8].upper()}", align="R", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(pdf.w - 90, 16)
    pdf.cell(78, 6, fecha_texto, align="R", ln=True)

    pdf.set_y(42)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(157, 23, 77)
    pdf.cell(0, 6, "FACTURAR A", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, cliente or "Consumidor final", ln=True)
    pdf.ln(6)

    anchos = [ancho_pagina * 0.44, ancho_pagina * 0.16, ancho_pagina * 0.20, ancho_pagina * 0.20]
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(219, 39, 119)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(anchos[0], 9, "  Producto", fill=True)
    pdf.cell(anchos[1], 9, "Cantidad", fill=True, align="C")
    pdf.cell(anchos[2], 9, "Precio Unit.", fill=True, align="R")
    pdf.cell(anchos[3], 9, "Subtotal  ", fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    for idx, item in enumerate(items_factura):
        subtotal_item = float(item["cantidad"]) * float(item["precio_unitario"])
        if idx % 2 == 0:
            pdf.set_fill_color(253, 242, 248)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(40, 35, 60)
        pdf.cell(anchos[0], 9, "  " + str(item["producto"])[:40], fill=True)
        pdf.cell(anchos[1], 9, str(int(item["cantidad"])), fill=True, align="C")
        pdf.cell(anchos[2], 9, moneda(item["precio_unitario"]), fill=True, align="R")
        pdf.cell(anchos[3], 9, moneda(subtotal_item) + "  ", fill=True, align="R", ln=True)

    pdf.ln(8)

    ancho_total = 80
    pdf.set_x(pdf.w - pdf.r_margin - ancho_total)
    pdf.set_fill_color(219, 39, 119)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(ancho_total * 0.45, 11, "  TOTAL", fill=True, align="L")
    pdf.cell(ancho_total * 0.55, 11, moneda(total_factura) + "  ", fill=True, align="R", ln=True)

    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(0, 6, "Gracias por tu compra", ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, "Lewin Boutique", ln=True, align="C")

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

# =====================================================================================
# ESTILOS CON TEMA ES6 LUXURY DARK / LIGHT & SIDEBAR SUAVE
# =====================================================================================

def get_css(tema: str, compacto: bool = False) -> str:
    ancho_sidebar = "84px" if compacto else "270px"
    if tema == "claro":
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.06) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 40%),
                           linear-gradient(160deg, #fdf2f8 0%, #fff5f9 50%, #fdf4f9 100%);
            --text-color: #2b1f26;
            --text-secondary: #8a6b78;
            --accent: #db2777;
            --accent-light: #ec4899;
            --accent-neon: #10b981;
            --card-bg: rgba(255, 255, 255, 0.94);
            --border-color: rgba(219, 39, 119, 0.18);
            --sidebar-bg: rgba(255, 255, 255, 0.98);
            --input-bg: rgba(253, 242, 248, 0.85);
        """
    else:
        variables = """
            --bg-gradient: radial-gradient(circle at 20% 20%, rgba(219, 39, 119, 0.12) 0%, transparent 40%),
                           radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.08) 0%, transparent 40%),
                           linear-gradient(135deg, #0c0b0e 0%, #151119 50%, #100f14 100%);
            --text-color: #fdf2f8;
            --text-secondary: #a8949e;
            --accent: #ec4899;
            --accent-light: #f472b6;
            --accent-neon: #34d399;
            --card-bg: rgba(18, 15, 22, 0.85);
            --border-color: rgba(219, 39, 119, 0.22);
            --sidebar-bg: rgba(14, 12, 17, 0.97);
            --input-bg: rgba(24, 20, 28, 0.85);
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

:root {{ {variables} }}

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes menuSlideDown {{
    from {{ opacity: 0; transform: translateY(-8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.stApp {{
    background: var(--bg-gradient);
    background-attachment: fixed;
    color: var(--text-color) !important;
    font-family: 'Poppins', sans-serif !important;
}}

header[data-testid="stHeader"] {{ background: transparent !important; }}

.block-container {{ max-width: 100% !important; padding: 3.5rem 2rem 2rem 2rem !important; }}

section[data-testid="stSidebar"] {{
    width: {ancho_sidebar} !important;
    min-width: {ancho_sidebar} !important;
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
    backdrop-filter: blur(30px);
    transition: width 0.25s ease;
}}
section[data-testid="stSidebar"] * {{ color: var(--text-color) !important; }}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    gap: 4px !important;
}}

/* BOTONES SIDEBAR ALINEADOS A LA IZQUIERDA Y ESTILIZADOS */
section[data-testid="stSidebar"] div.stButton > button {{
    justify-content: flex-start !important;
    text-align: left !important;
    display: flex !important;
    align-items: center !important;
    border-radius: 12px !important;
    padding: 9px 14px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    width: 100% !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--text-color) !important;
    box-shadow: none !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

section[data-testid="stSidebar"] div.stButton > button p,
section[data-testid="stSidebar"] div.stButton > button span,
section[data-testid="stSidebar"] div.stButton > button div {{
    text-align: left !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    font-size: 13px !important;
}}

section[data-testid="stSidebar"] div.stButton > button:hover {{
    background: rgba(236, 72, 153, 0.08) !important;
    color: var(--accent-light) !important;
    border-color: rgba(236, 72, 153, 0.2) !important;
    transform: none !important;
}}

/* BOTON PRINCIPAL ACTIVO (Ej: INICIO) */
section[data-testid="stSidebar"] div.stButton > button[kind="primary"]:not([aria-label*="•"]) {{
    background: rgba(236, 72, 153, 0.16) !important;
    color: #ffffff !important;
    border: 1px solid rgba(236, 72, 153, 0.35) !important;
    border-radius: 12px !important;
    box-shadow: 0 0 16px rgba(236, 72, 153, 0.25) !important;
    font-weight: 700 !important;
}}

/* SUB-ITEMS CON GUIA LATERAL PURPURA/ROSA */
section[data-testid="stSidebar"] button[aria-label*="•"] {{
    margin-left: 14px !important;
    width: calc(100% - 14px) !important;
    padding: 7px 12px 7px 12px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: none !important;
    border-left: 2px solid rgba(236, 72, 153, 0.35) !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    box-shadow: none !important;
    animation: menuSlideDown 0.25s ease !important;
    transition: all 0.2s ease !important;
}}

section[data-testid="stSidebar"] button[aria-label*="•"] p {{
    color: var(--text-secondary) !important;
    font-size: 12px !important;
}}

section[data-testid="stSidebar"] button[aria-label*="•"]:hover {{
    background: rgba(236, 72, 153, 0.08) !important;
    color: #f472b6 !important;
    border-left: 2px solid #ec4899 !important;
}}
section[data-testid="stSidebar"] button[aria-label*="•"]:hover p {{
    color: #f472b6 !important;
}}

/* SUB-ITEM ACTIVO (RESALTADO CON BRILLO ROSA COMO EN LA IMAGEN 2) */
section[data-testid="stSidebar"] button[kind="primary"][aria-label*="•"] {{
    background: rgba(236, 72, 153, 0.18) !important;
    color: #f9a8d4 !important;
    border: 1px solid rgba(236, 72, 153, 0.3) !important;
    border-left: 2.5px solid #ec4899 !important;
    border-radius: 8px !important;
    box-shadow: 0 0 14px rgba(236, 72, 153, 0.22) !important;
    font-weight: 700 !important;
    animation: none !important;
}}

section[data-testid="stSidebar"] button[kind="primary"][aria-label*="•"] p,
section[data-testid="stSidebar"] button[kind="primary"][aria-label*="•"] * {{
    color: #f9a8d4 !important;
    font-weight: 700 !important;
}}

div[data-baseweb="input"], div[data-baseweb="select"] > div {{
    background-color: var(--input-bg) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-color) !important;
}}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px rgba(219, 39, 119, 0.3) !important;
}}
div[data-baseweb="input"] input {{ color: var(--text-color) !important; font-size: 13px !important; }}

/* BOTONES DEL CONTENIDO PRINCIPAL */
.main div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
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
.main div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
    background: linear-gradient(135deg, #db2777 0%, #ec4899 100%) !important;
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
    background: linear-gradient(135deg, #db2777 0%, #ec4899 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; box-shadow: 0 0 10px rgba(219, 39, 119, 0.45);
}}
.form-section-title {{
    font-size: 13px; font-weight: 700; color: var(--text-color);
    text-transform: uppercase; letter-spacing: 1px;
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

.config-chip {{
    background: rgba(219, 39, 119, 0.07); border: 1px solid var(--border-color);
    border-radius: 10px; padding: 8px 14px; margin-bottom: 6px;
    font-size: 13px; color: var(--text-color); display: flex; align-items: center; height: 38px;
}}

.kpi-card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border-color); border-radius: 16px;
    padding: 18px 20px; margin-bottom: 12px; animation: fadeInUp 0.35s ease;
    box-shadow: 0 8px 24px rgba(219, 39, 119, 0.08);
}}
.kpi-icon-box {{
    width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 16px; margin-bottom: 10px;
}}
.kpi-label {{ font-size: 12.5px; color: var(--text-secondary); font-weight: 600; }}
.kpi-value {{ font-size: 22px; font-weight: 800; color: var(--text-color); margin-top: 2px; }}

.logo-brand-row {{
    display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
    padding-bottom: 14px; border-bottom: 1px solid var(--border-color);
}}
.logo-brand-name {{ font-size: 15px; font-weight: 800; color: var(--text-color); letter-spacing: 1px; line-height: 1.1; }}
.logo-brand-sub {{ font-size: 9px; font-weight: 600; color: var(--text-secondary); letter-spacing: 2px; }}

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
    background: rgba(219, 39, 119, 0.08); padding: 10px 12px; border-radius: 14px;
    border: 1px solid var(--border-color); margin-bottom: 10px;
    display: flex; align-items: center; gap: 10px;
}}
.user-avatar {{
    width: 34px; height: 34px; background: linear-gradient(135deg, #db2777 0%, #ec4899 100%); color: #ffffff;
    font-weight: 800; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 13px; box-shadow: 0 0 15px rgba(219, 39, 119, 0.5); flex-shrink: 0;
}}
.user-info-name {{ font-size: 13px; font-weight: 700; color: var(--text-color); line-height: 1.2; }}

.menu-divider {{ height: 1px; background: var(--border-color); margin: 12px 0 10px 0; }}

.menu-group-title {{
    font-size: 9px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1.5px;
    font-weight: 700; margin: 14px 0 6px 4px; opacity: 0.75;
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

if query_params.get("ir") == "login" and st.session_state.etapa == "bienvenida":
    st.session_state.etapa = "login"
    del st.query_params["ir"]

ES_ADMIN = True

# =====================================================================================
# 1. PANTALLA DE BIENVENIDA
# =====================================================================================

if not st.session_state.autenticado and st.session_state.etapa == "bienvenida":
    total_prendas_hero = len(df) if not df.empty else 0
    porcentaje_ok_hero = round(int((df["cantidad"] > df["alerta"]).sum()) / total_prendas_hero * 100) if total_prendas_hero > 0 else 0

    hero_html = """
        <style>
        .block-container { padding: 3.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }
        .full-hero-wrapper {
            background: var(--card-bg); backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
            border: 1px solid var(--border-color); border-radius: 32px; padding: 50px 70px 55px 70px;
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
            50% { box-shadow: 0 8px 40px rgba(236, 72, 153, 0.65); }
        }
        .bg-photo-hero {
            position: absolute; top: -10%; right: -15%; width: 55%; height: 130%;
            background: radial-gradient(circle at 30% 30%, rgba(219, 39, 119, 0.30), transparent 60%);
            border-radius: 50%; filter: blur(10px); z-index: 0;
        }
        .hero-inner { position: relative; z-index: 1; }
        .hero-topbar {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px;
            border-bottom: 1px solid var(--border-color); padding-bottom: 20px;
        }
        .hero-brand { display: flex; align-items: center; gap: 12px; }
        .brand-icon-hero {
            display: flex; align-items: center; justify-content: center;
        }
        .hero-brand-name {
            font-family: 'Poppins', sans-serif !important; font-size: 15px; font-weight: 700; color: var(--text-color); letter-spacing: 2px;
        }
        h1.hero-title, .hero-title {
            font-family: 'Poppins', sans-serif !important; font-size: 52px; font-weight: 800 !important; color: var(--text-color);
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
        .stat-value-hero { font-family: 'Poppins', sans-serif !important; font-size: 26px; font-weight: 800; color: var(--text-color); }
        .stat-label-hero {
            font-size: 10px; color: var(--text-secondary); text-transform: uppercase;
            letter-spacing: 1.5px; font-weight: 700; margin-top: 2px;
        }
        .hero-inicio-link {
            background: linear-gradient(135deg, #db2777 0%, #ec4899 100%);
            color: #ffffff !important; text-decoration: none !important;
            padding: 10px 26px; border-radius: 10px; font-weight: 700; font-size: 13px;
            letter-spacing: 0.5px; animation: pulseGlowHero 2.6s ease-in-out infinite;
            display: inline-block;
        }
        </style>
        <div class="full-hero-wrapper">
            <div class="bg-photo-hero"></div>
            <div class="hero-inner">
                <div class="hero-topbar">
                    <div class="hero-brand">
                        <div class="brand-icon-hero">LOGO_SVG_PLACEHOLDER</div>
                        <div class="hero-brand-name">LEWIN BOUTIQUE</div>
                    </div>
                    <a class="hero-inicio-link" href="?ir=login">INICIO</a>
                </div>
                <div class="hero-subtitle-tag">Inventario Boutique</div>
                <h1 class="hero-title">Lewin Boutique<br>Control Center</h1>
                <p class="hero-desc">
                    Gesti\u00f3n completa de inventario, ventas, reportes y cat\u00e1logo visual en una sola plataforma.
                </p>
                <div class="feature-pills-container">
                    <span class="feature-pill">\U0001F4F7 Fotos de productos</span>
                    <span class="feature-pill">\U0001F4B3 Ventas y compras</span>
                    <span class="feature-pill">\U0001F4C8 Reportes de rentabilidad</span>
                    <span class="feature-pill">\U0001F465 Roles de usuario</span>
                </div>
                <div class="stats-row-hero">
                    <div><div class="stat-value-hero">PLACEHOLDER_TOTAL</div><div class="stat-label-hero">Prendas en cat\u00e1logo</div></div>
                    <div><div class="stat-value-hero">PLACEHOLDER_PORC%</div><div class="stat-label-hero">Stock por encima del m\u00ednimo</div></div>
                    <div><div class="stat-value-hero">24/7</div><div class="stat-label-hero">Acceso en la nube</div></div>
                </div>
            </div>
        </div>
        """
    hero_html = hero_html.replace("PLACEHOLDER_TOTAL", str(total_prendas_hero)).replace("PLACEHOLDER_PORC", str(porcentaje_ok_hero)).replace("LOGO_SVG_PLACEHOLDER", logo_svg_markup(38))
    hero_html = textwrap.dedent(hero_html)

    st.markdown(hero_html, unsafe_allow_html=True)
    st.stop()

# =====================================================================================
# 2. LOGIN
# =====================================================================================

elif not st.session_state.autenticado and st.session_state.etapa == "login":
    login_style_html = textwrap.dedent(
        """
        <style>
        .login-welcome-tag {
            font-size: 11px; color: var(--accent); text-transform: uppercase; letter-spacing: 3px;
            font-weight: 700; text-align: center; margin-bottom: 6px;
        }
        .login-brand-icon {
            margin: 0 auto 12px auto;
            display: flex; align-items: center; justify-content: center;
        }
        .login-title-text {
            font-family: 'Poppins', sans-serif !important; font-size: 22px; font-weight: 700 !important;
            color: var(--text-color); letter-spacing: 1px; text-align: center;
        }
        .login-subtitle-text {
            font-size: 12px; color: var(--text-secondary); text-align: center; margin-top: 4px; margin-bottom: 14px;
        }
        </style>
        """
    )
    st.markdown(login_style_html, unsafe_allow_html=True)

    if st.button("\u2190 Volver a la portada"):
        st.session_state.etapa = "bienvenida"
        st.rerun()

    _, col_centro, _ = st.columns([1, 1.4, 1])
    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='login-welcome-tag'>Bienvenida de vuelta</div>", unsafe_allow_html=True)
        with st.form("form_login"):
            st.markdown(f"<div class='login-brand-icon'>{logo_svg_markup(40)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-title-text'>Lewin Boutique Access</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-subtitle-text'>Ingresa tus credenciales para continuar</div>", unsafe_allow_html=True)

            usuario_input = st.text_input("\U0001f464 Usuario", placeholder="Ingresa tu usuario")
            clave_input = st.text_input("\U0001f512 Contrase\u00f1a", type="password", placeholder="Ingresa tu contrase\u00f1a")
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
                    st.error("\u26a0\ufe0f Usuario o contrase\u00f1a incorrectos.")
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

    LOGO_SVG = logo_svg_markup(34)

    if compacto:
        st.sidebar.markdown(f"<div style='display:flex; justify-content:center; margin-bottom:6px;'>{LOGO_SVG}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(
            f"""<div class="logo-brand-row">
{LOGO_SVG}
<div><div class="logo-brand-name">LEWIN</div><div class="logo-brand-sub">BOUTIQUE</div></div>
</div>""",
            unsafe_allow_html=True,
        )

    col_collapse1, col_collapse2 = st.sidebar.columns([3, 1])
    with col_collapse2:
        if st.button("\u2630", key="btn_toggle_compacto", help="Colapsar / expandir men\u00fa"):
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
        tema_claro = st.sidebar.toggle("\u2600\ufe0f Modo claro", value=(st.session_state.tema == "claro"))
        nuevo_tema = "claro" if tema_claro else "oscuro"
        if nuevo_tema != st.session_state.tema:
            st.session_state.tema = nuevo_tema
            st.rerun()

    st.sidebar.markdown("<div class='menu-divider'></div>", unsafe_allow_html=True)

    GRUPOS_CLAVES_MENU = {
        "acc_inventario": ["existencias", "etiquetas", "registrar", "modificar"],
        "acc_ventas": ["vender", "ventas_pagadas", "deudores"],
        "acc_compras": ["comprar", "movimientos", "facturas"],
    }
    if "grupo_menu_abierto" not in st.session_state:
        st.session_state.grupo_menu_abierto = next(
            (k for k, claves in GRUPOS_CLAVES_MENU.items() if menu_actual in claves), "acc_inventario"
        )
    if "grupo_menu_apertura_n" not in st.session_state:
        st.session_state.grupo_menu_apertura_n = 0

    def render_grupo_acordeon(icono_grupo, titulo_grupo, items, session_key):
        """Botón principal con flechita (▾/▸) y sub-ítems jerárquicos alineados."""
        claves_grupo = [c for c, _ in items]
        expandido = (st.session_state.grupo_menu_abierto == session_key)

        if compacto:
            if st.sidebar.button(icono_grupo, use_container_width=True, key=f"grupo_{session_key}", type=("primary" if menu_actual in claves_grupo else "secondary"), help=titulo_grupo):
                st.session_state.menu_activo = claves_grupo[0]
                st.rerun()
            return

        chevron = "\u25be" if expandido else "\u25b8"
        tipo_grupo = "primary" if (menu_actual in claves_grupo and not expandido) else "secondary"
        if st.sidebar.button(f"{icono_grupo}  {titulo_grupo}  {chevron}", use_container_width=True, key=f"grupo_{session_key}", type=tipo_grupo):
            if not expandido:
                st.session_state.grupo_menu_apertura_n += 1
            st.session_state.grupo_menu_abierto = None if expandido else session_key
            st.rerun()

        if expandido:
            n = st.session_state.grupo_menu_apertura_n
            for clave, etiqueta in items:
                if clave in ("registrar", "modificar", "configuracion") and not ES_ADMIN:
                    continue
                es_activo = (menu_actual == clave)
                tipo_item = "primary" if es_activo else "secondary"
                if st.sidebar.button(f"\u2022  {etiqueta}", use_container_width=True, key=f"sub_{clave}_{n}", type=tipo_item):
                    st.session_state.menu_activo = clave
                    st.session_state.grupo_menu_abierto = session_key
                    st.rerun()

    # --- Inicio (ítem plano, sin acordeón) ---
    etiqueta_inicio = "\U0001f3e0" if compacto else "\U0001f3e0  Inicio"
    if st.sidebar.button(etiqueta_inicio, use_container_width=True, key="menu_inicio", type=("primary" if menu_actual == "inicio" else "secondary"), help="Inicio" if compacto else None):
        st.session_state.menu_activo = "inicio"
        st.rerun()

    st.sidebar.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    render_grupo_acordeon("\U0001f4ca", "Prendas", [
        ("existencias", "Prendas en Stock"), ("etiquetas", "Etiquetas de Precios"), ("registrar", "Registrar Prenda"), ("modificar", "Eliminar Prenda"),
    ], "acc_inventario")

    render_grupo_acordeon("\U0001f6cd\ufe0f", "Ventas", [
        ("vender", "Nueva Venta"), ("ventas_pagadas", "Ventas Pagadas"), ("deudores", "Ventas por Pagar"),
    ], "acc_ventas")

    render_grupo_acordeon("\U0001f4e6", "Compras", [
        ("comprar", "Registrar Compra"), ("movimientos", "Movimientos"), ("facturas", "Facturas"),
    ], "acc_compras")

    if not compacto:
        st.sidebar.markdown("<p class='menu-group-title'>Negocio</p>", unsafe_allow_html=True)
    for clave, icono, etiqueta in [("reportes", "\U0001f4c8", "Reportes"), ("configuracion", "\u2699\ufe0f", "Configuraci\u00f3n")]:
        if clave == "configuracion" and not ES_ADMIN:
            continue
        tipo_boton = "primary" if menu_actual == clave else "secondary"
        label_boton = icono if compacto else f"{icono}  {etiqueta}"
        if st.sidebar.button(label_boton, use_container_width=True, key=f"menu_{clave}", type=tipo_boton, help=etiqueta if compacto else None):
            st.session_state.menu_activo = clave
            st.rerun()

    st.sidebar.markdown("<hr style='margin: 16px 0 12px 0; border-color: var(--border-color);'>", unsafe_allow_html=True)

    etiqueta_salir = "\U0001f6aa" if compacto else "\U0001f6aa  Cerrar Sesi\u00f3n"
    if st.sidebar.button(etiqueta_salir, use_container_width=True, help="Cerrar Sesi\u00f3n" if compacto else None):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.session_state.etapa = "bienvenida"
        if "recuerdame_user" in st.query_params:
            del st.query_params["recuerdame_user"]
        st.rerun()

    menu = st.session_state.get("menu_activo", "inicio")
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
    <div class="page-title">\U0001f3e0 Inicio</div>
    <div class="page-subtitle">Resumen general de Lewin Boutique, {st.session_state.usuario_actual.capitalize()}.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs_inicio = cargar_movimientos()
        deudores_inicio = cargar_deudores()

        total_prendas_inicio = len(df) if not df.empty else 0
        alertas_inicio = int((df["cantidad"] <= df["alerta"]).sum()) if not df.empty else 0
        valor_inventario_inicio = float((df["cantidad"] * df["precio_venta"]).sum()) if not df.empty else 0.0

        ventas_df_inicio = movs_inicio[movs_inicio["tipo"] == "venta"].copy() if not movs_inicio.empty else pd.DataFrame()
        if not ventas_df_inicio.empty:
            ventas_df_inicio["monto"] = ventas_df_inicio["cantidad"] * ventas_df_inicio["precio_unitario"]
        total_ventas_monto = float(ventas_df_inicio["monto"].sum()) if not ventas_df_inicio.empty else 0.0

        tarjetas_kpi = [
            ("\U0001f4e6", "db2777", total_prendas_inicio, "prendas", "Total Prendas", "existencias", "Ver inventario"),
            ("$", "ec4899", moneda(valor_inventario_inicio), "", "Valor del Inventario", "reportes", "Ver detalle"),
            ("\u26a0\ufe0f", "ef4444", alertas_inicio, "prendas", "Stock Bajo", "existencias", "Ver productos"),
        ]
        cols_kpi = st.columns(3)
        for idx, (icono_k, color_k, valor_k, sufijo_k, label_k, destino_k, texto_link_k) in enumerate(tarjetas_kpi):
            with cols_kpi[idx]:
                st.markdown(
                    f"""<div class="kpi-card">
<div class="kpi-icon-box" style="background: #{color_k}22; color: #{color_k};">{icono_k}</div>
<div class="kpi-label">{label_k}</div>
<div class="kpi-value">{valor_k} <span style="font-size:13px; font-weight:500; color:var(--text-secondary);">{sufijo_k}</span></div>
</div>""",
                    unsafe_allow_html=True,
                )
                if st.button(f"{texto_link_k} \u2192", key=f"kpi_link_{idx}", use_container_width=True):
                    st.session_state.menu_activo = destino_k
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                f"""<div class="kpi-label">Total Ventas (hist\u00f3rico)</div>
<div class="kpi-value" style="font-size: 26px;">{moneda(total_ventas_monto)}</div>""",
                unsafe_allow_html=True,
            )
            if not ventas_df_inicio.empty:
                ventas_df_inicio["fecha_dt"] = pd.to_datetime(ventas_df_inicio["fecha"], errors="coerce")
                ventas_df_inicio["mes"] = ventas_df_inicio["fecha_dt"].dt.to_period("M").astype(str)
                tendencia_mensual = ventas_df_inicio.groupby("mes")["monto"].sum().sort_index()
                if len(tendencia_mensual) >= 2:
                    cambio_pct = ((tendencia_mensual.iloc[-1] - tendencia_mensual.iloc[-2]) / tendencia_mensual.iloc[-2] * 100) if tendencia_mensual.iloc[-2] > 0 else 0
                    flecha = "\u2191" if cambio_pct >= 0 else "\u2193"
                    color_cambio = "#22c55e" if cambio_pct >= 0 else "#ef4444"
                    st.markdown(f"<div style='color:{color_cambio}; font-size:12px; font-weight:700;'>{flecha} {abs(cambio_pct):.1f}% vs mes anterior</div>", unsafe_allow_html=True)
                fig_tendencia = go.Figure(data=[go.Scatter(
                    x=list(tendencia_mensual.index), y=tendencia_mensual.values,
                    mode="lines", line=dict(color="#ec4899", width=3, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(236, 72, 153, 0.12)",
                )])
                fig_tendencia.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0), height=140, showlegend=False,
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                )
                st.plotly_chart(fig_tendencia, use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("Todav\u00eda no hay ventas para mostrar la tendencia.")

        st.markdown("<br>", unsafe_allow_html=True)

        col_izq_inicio, col_der_inicio = st.columns([1, 1.2])
        with col_izq_inicio:
            with st.container(border=True):
                st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Ventas por categor\u00eda</div>", unsafe_allow_html=True)
                if not ventas_df_inicio.empty and not df.empty:
                    ventas_cat_inicio = ventas_df_inicio.copy()
                    ventas_cat_inicio["prenda_id"] = ventas_cat_inicio["prenda_id"].astype(str)
                    mapa_cat_inicio = df.set_index(df["ID"].astype(str))["Categoria"]
                    ventas_cat_inicio["Categoria"] = ventas_cat_inicio["prenda_id"].map(mapa_cat_inicio)
                    agrupado_cat_inicio = ventas_cat_inicio.dropna(subset=["Categoria"]).groupby("Categoria")["cantidad"].sum()
                    agrupado_cat_inicio = agrupado_cat_inicio[agrupado_cat_inicio > 0]
                    if not agrupado_cat_inicio.empty:
                        st.plotly_chart(grafico_dona(agrupado_cat_inicio, altura=240), use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.caption("Sin datos suficientes todav\u00eda.")
                else:
                    st.caption("Sin ventas registradas todav\u00eda.")

        with col_der_inicio:
            with st.container(border=True):
                st.markdown("<div class='kpi-label' style='margin-bottom: 10px;'>Movimientos recientes</div>", unsafe_allow_html=True)
                if not movs_inicio.empty:
                    recientes = movs_inicio.sort_values("fecha", ascending=False).head(5)
                    for _, mov_r in recientes.iterrows():
                        es_venta_r = mov_r["tipo"] == "venta"
                        color_r = "#22c55e" if es_venta_r else "#ef4444"
                        signo_r = "\u2191" if es_venta_r else "\u2193"
                        monto_r = float(mov_r["cantidad"]) * float(mov_r["precio_unitario"] if es_venta_r else mov_r["costo_unitario"])
                        st.markdown(
                            f"""<div class="mov-reciente-item">
<div>
<div style="font-size:9.5px; font-weight:700; color:{color_r}; letter-spacing:0.5px;">{mov_r['tipo'].upper()}</div>
<div style="font-size:13px; font-weight:600; color:var(--text-color);">{mov_r['producto']}</div>
</div>
<div style="text-align:right;">
<div style="font-size:13px; font-weight:700; color:{color_r};">{signo_r} {moneda(monto_r)}</div>
<div style="font-size:10.5px; color:var(--text-secondary);">{formatear_fecha_corta(mov_r['fecha'])}</div>
</div>
</div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("Todav\u00eda no hay movimientos registrados.")

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

        st.markdown("<div class='section-title'>Visi\u00f3n General del Inventario</div><div class='section-subtitle'>Resumen general de m\u00e9tricas y existencias.</div>", unsafe_allow_html=True)

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
                f"""<div class="alert-banner">\u26a0\ufe0f <b>{total_alertas} prenda(s)</b> est\u00e1n en o por debajo del m\u00ednimo de stock: {nombres_alerta}{"..." if total_alertas > 8 else ""}</div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if not df.empty:
            st.markdown("<div class='section-title'>\u26a1 Ajuste R\u00e1pido de Stock</div><div class='section-subtitle'>Modifica existencias de manera inmediata seleccionando la prenda.</div>", unsafe_allow_html=True)
            col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
            with col_q1:
                ids_rapidos = df["ID"].astype(str).tolist()
                id_rapido = st.selectbox("Seleccionar Prenda", ids_rapidos, key="select_ajuste_rapido")
            with col_q2:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("\u2796 Quitar 1 (-1)", use_container_width=True, key="btn_minus_1"):
                    fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = max(0, int(fila_actual["cantidad"]) - 1)
                    datos_act = fila_actual.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.success(f"Stock actualizado a {nueva_cant}")
                        st.rerun()
            with col_q3:
                st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
                if st.button("\u2795 A\u00f1adir 1 (+1)", use_container_width=True, key="btn_plus_1"):
                    fila_actual = df[df["ID"].astype(str) == str(id_rapido)].iloc[0]
                    nueva_cant = int(fila_actual["cantidad"]) + 1
                    datos_act = fila_actual.to_dict()
                    datos_act["cantidad"] = nueva_cant
                    if actualizar_prenda(id_rapido, datos_act):
                        st.success(f"Stock actualizado a {nueva_cant}")
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>\U0001f4cb B\u00fasqueda y Filtros Avanzados</div><div class='section-subtitle'>Combina filtros para encontrar exactamente lo que buscas.</div>", unsafe_allow_html=True)

            col_f1, col_f2, col_f3 = st.columns([1.5, 1, 1])
            with col_f1:
                busqueda = st.text_input("\U0001f50d Buscar por nombre o ID", placeholder="Escribe el nombre de la prenda o su ID...")
            with col_f2:
                categorias_disponibles = ["Todas"] + sorted(list(df["Categoria"].dropna().unique()))
                filtro_categoria = st.selectbox("\U0001f4c2 Categor\u00eda", categorias_disponibles)
            with col_f3:
                tallas_disponibles = ["Todas"] + sorted(list(df["talla"].dropna().unique()))
                filtro_talla = st.selectbox("\U0001f4cf Talla", tallas_disponibles)

            col_f4, col_f5, col_f6 = st.columns([1, 1, 1])
            with col_f4:
                colores_disponibles = ["Todos"] + sorted(list(df["color"].dropna().unique()))
                filtro_color = st.selectbox("\U0001f3a8 Color", colores_disponibles)
            with col_f5:
                orden = st.selectbox("\u2195\ufe0f Ordenar por", ["Nombre (A-Z)", "Stock (mayor a menor)", "Stock (menor a mayor)", "M\u00e1s vendidos"])
            with col_f6:
                solo_favoritos = st.checkbox("\u2b50 Solo favoritos", value=False)

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
                df_filtrado = df_filtrado[df_filtrado["favorito"] == True]

            if orden == "Nombre (A-Z)":
                df_filtrado = df_filtrado.sort_values("Producto")
            elif orden == "Stock (mayor a menor)":
                df_filtrado = df_filtrado.sort_values("cantidad", ascending=False)
            elif orden == "Stock (menor a mayor)":
                df_filtrado = df_filtrado.sort_values("cantidad", ascending=True)
            elif orden == "M\u00e1s vendidos":
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
                    pagina_sel = st.selectbox("\U0001f4c4 P\u00e1gina", range(1, total_paginas + 1), key="paginacion_tabla") if total_paginas > 1 else 1

                inicio = (pagina_sel - 1) * items_por_pagina
                fin = min(inicio + items_por_pagina, total_registros)
                df_paginado = df_filtrado.iloc[inicio:fin]

                csv_data = df_filtrado.to_csv(index=False, sep=';').encode('utf-8-sig')
                with col_p2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    st.download_button("\U0001f4e5 Exportar Inventario a CSV", data=csv_data,
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
                    estrella = "\u2b50" if bool(row.get("favorito", False)) else "\u2606"
                    foto_html = (
                        f'<img class="product-photo" src="{row["foto_url"]}" />'
                        if row.get("foto_url") else
                        '<div class="product-photo-placeholder">\U0001F455</div>'
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
<span>\U0001f4cf Talla: <b>{row['talla']}</b></span>
<span>\U0001f3a8 Color: <b>{row['color']}</b></span>
</div>
{precio_html}
<div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 10px; font-size: 13px;">
{badge_stock}
<span style="font-size: 11px; color: var(--text-secondary);">Alerta m\u00edn: {row['alerta']}</span>
</div>
</div>
</div>"""

                    with col_actual:
                        st.markdown(tarjeta_html, unsafe_allow_html=True)

                        c_fav, c_qr = st.columns(2)
                        with c_fav:
                            if st.button("\u2b50 Favorito" if not row.get("favorito", False) else "\u2606 Quitar", key=f"fav_{row['ID']}", use_container_width=True):
                                datos_act = row.to_dict()
                                datos_act["favorito"] = not bool(row.get("favorito", False))
                                if actualizar_prenda(row["ID"], datos_act):
                                    st.rerun()
                        with c_qr:
                            with st.popover("\U0001f517 QR", use_container_width=True) if hasattr(st, "popover") else st.expander("\U0001f517 QR"):
                                if QR_DISPONIBLE:
                                    qr_bytes = generar_qr_bytes(f"ID:{row['ID']} | {row['Producto']}")
                                    st.image(qr_bytes, width=140)
                                else:
                                    st.caption("Instala 'qrcode' en requirements.txt para activar esta funci\u00f3n.")
                        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
            else:
                st.info("No se encontraron registros con los filtros seleccionados.")
        else:
            st.info("No hay prendas registradas todav\u00eda en el sistema.")

    # -----------------------------------------------------------------------------
    # ETIQUETAS DE PRECIOS
    # -----------------------------------------------------------------------------
    elif menu == "etiquetas":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\U0001F3F7\ufe0f Generador de Etiquetas de Precios</div>
    <div class="page-subtitle">Crea e imprime etiquetas para colocar en las prendas f\u00edsicas con logo, talla, color y precio.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas para generar etiquetas.")
        else:
            tasa_etiqueta, _ = selector_tasa_cambio("etiquetas_tasa")
            cats_etiquetas = ["Todas"] + list(st.session_state.categorias_maestras)
            cat_sel_et = st.selectbox("Filtrar por Categor\u00eda", cats_etiquetas, key="cat_sel_etiquetas")

            df_et = df.copy()
            if cat_sel_et != "Todas":
                df_et = df_et[df_et["Categoria"] == cat_sel_et]

            opciones_prendas_et = df_et["ID"].astype(str).tolist()
            prendas_sel_et = st.multiselect(
                "Seleccionar prendas a imprimir",
                opciones_prendas_et,
                default=opciones_prendas_et[:6],
                format_func=lambda x: f"ID: {x} - {df_et[df_et['ID'].astype(str) == x]['Producto'].values[0]}"
            )

            if prendas_sel_et:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>\U0001f4cb Vista Previa de Etiquetas Imprimibles</div>", unsafe_allow_html=True)

                cols_et = st.columns(3)
                for idx, pid in enumerate(prendas_sel_et):
                    fila_p = df[df["ID"].astype(str) == str(pid)].iloc[0]
                    precio_usd = float(fila_p.get("precio_venta", 0) or 0)
                    precio_bs = precio_usd * tasa_etiqueta if tasa_etiqueta > 0 else 0.0
                    bs_txt = f"<br><span style='font-size:11px; color:#666;'>{precio_bs:,.2f} Bs</span>" if precio_bs > 0 else ""

                    card_html = f"""<div style="background: #ffffff; color: #1a1a1a; padding: 16px; border-radius: 12px; border: 2px dashed #db2777; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
<div style="text-align: center; border-bottom: 1px solid #eee; padding-bottom: 6px; margin-bottom: 8px;">
<div style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 11px; letter-spacing: 2px; color: #db2777;">LEWIN BOUTIQUE</div>
<div style="font-weight: 700; font-size: 13px; color: #111;">{fila_p['Producto']}</div>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<div style="font-size: 11px; color: #444;">
<div>ID: <b>{fila_p['ID']}</b></div>
<div>Talla: <b>{fila_p['talla']}</b></div>
<div>Color: <b>{fila_p['color']}</b></div>
</div>
</div>
<div style="border-top: 1px solid #eee; padding-top: 6px; display: flex; justify-content: space-between; align-items: center;">
<span style="font-size: 18px; font-weight: 800; color: #db2777;">{moneda(precio_usd)}</span>
{bs_txt}
</div>
</div>"""
                    with cols_et[idx % 3]:
                        st.markdown(card_html, unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # VENDER
    # -----------------------------------------------------------------------------
    elif menu == "vender":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\U0001f6cd\ufe0f Nueva Venta</div>
    <div class="page-subtitle">Arma el pedido y dinos si ya te pagaron o queda pendiente.</div>
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
                    format_func=lambda x: f"{x} \u2014 {df[df['ID'].astype(str) == x]['Producto'].values[0]} (stock: {int(df[df['ID'].astype(str) == x]['cantidad'].values[0])})",
                    key="select_producto_venta_nueva",
                )
            with col_p2:
                cantidad_venta_sel = st.number_input("Cantidad", min_value=1, value=1, step=1, key="cantidad_venta_nueva")
            with col_p3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("\u2795 Agregar", use_container_width=True, key="btn_agregar_venta_nueva"):
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
                            f"<div class='config-chip'>{item['cantidad']} \u00d7 {item['producto']} \u2014 {moneda(item['cantidad'] * item['precio_unitario'])}</div>",
                            unsafe_allow_html=True,
                        )
                    with c_item2:
                        if st.button("\u2715", key=f"quitar_venta_nueva_{idx}", use_container_width=True):
                            st.session_state.carrito_venta_nueva.pop(idx)
                            st.rerun()

                st.markdown(f"**Total del pedido: {moneda(total_venta_nueva)}**")
                st.markdown("<br>", unsafe_allow_html=True)

                estado_pago = st.radio(
                    "\u00bfEsta venta fue pagada?",
                    ["\u2705 S\u00ed, pagada", "\U0001f9fe No, queda pendiente (fiado)"],
                    horizontal=True, key="estado_pago_venta_nueva",
                )
                fue_pagada = estado_pago.startswith("\u2705")

                nombre_valido = True
                if fue_pagada:
                    medio_pago_venta = st.selectbox(
                        "Medio de pago", ["Efectivo", "Pago M\u00f3vil", "Transferencia", "Zelle", "Otro"],
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
                    NUEVA_PERSONA_NV = "\u2795 Persona nueva"
                    opciones_persona_nv = [NUEVA_PERSONA_NV] + deudores_df_nv["id"].astype(str).tolist()
                    persona_sel_nv = st.selectbox(
                        "\u00bfA qui\u00e9n se le f\u00eda?", opciones_persona_nv,
                        format_func=lambda x: x if x == NUEVA_PERSONA_NV else deudores_df_nv[deudores_df_nv["id"].astype(str) == x]["nombre"].values[0],
                        key="select_persona_venta_nueva",
                    )
                    nombre_nuevo_nv, telefono_nuevo_nv = "", ""
                    if persona_sel_nv == NUEVA_PERSONA_NV:
                        col_np1, col_np2 = st.columns(2)
                        with col_np1:
                            nombre_nuevo_nv = st.text_input("Nombre", placeholder="Ej: Mar\u00eda P\u00e9rez", key="nombre_nueva_persona_nv")
                        with col_np2:
                            telefono_nuevo_nv = st.text_input("Tel\u00e9fono (opcional)", placeholder="Ej: 0414-1234567", key="telefono_nueva_persona_nv")
                        nombre_valido = nombre_nuevo_nv.strip() != ""
                    tasa_venta_nv, fuente_tasa_venta_nv = selector_tasa_cambio("venta_nueva", st.session_state.get("ultima_tasa", 0.0))
                    if tasa_venta_nv > 0:
                        st.caption(f"\U0001f4b1 Equivalente: {total_venta_nueva * tasa_venta_nv:,.2f} Bs")
                    medio_pago_venta = ""

                if st.button("\u2705 Confirmar Venta", use_container_width=True, key="btn_confirmar_venta_nueva", disabled=not nombre_valido):
                    venta_id_nv = str(uuid.uuid4())
                    id_persona_final_nv = None
                    if fue_pagada:
                        cliente_final_nv = cliente_pagada_nv.strip() or "Consumidor final"
                    else:
                        if persona_sel_nv == "\u2795 Persona nueva":
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
                        st.success(f"\u00a1Venta registrada como pagada! Total: {moneda(total_venta_nueva)}")
                        st.rerun()
                    else:
                        nombre_persona_final_nv = cliente_final_nv
                        if id_persona_final_nv:
                            descripcion_pedido_nv = ", ".join(f"{i['cantidad']}\u00d7 {i['producto']}" for i in st.session_state.carrito_venta_nueva)
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
                            st.success(f"\u00a1Venta registrada como pendiente! Nuevo saldo de {nombre_persona_final_nv}: {moneda(nuevo_saldo_nv)}")
                            st.rerun()

                if not nombre_valido:
                    st.caption("\u26a0\ufe0f Escribe el nombre de la persona nueva para poder confirmar.")

    # -----------------------------------------------------------------------------
    # VENTAS PAGADAS
    # -----------------------------------------------------------------------------
    elif menu == "ventas_pagadas":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\u2705 Ventas Pagadas</div>
    <div class="page-subtitle">Historial de ventas que se cobraron completas al momento (sin fiar).</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs_todos = cargar_movimientos()
        ventas_pagadas_df = movs_todos[(movs_todos["tipo"] == "venta") & (movs_todos["pagado"] == True)] if not movs_todos.empty else pd.DataFrame()

        total_pagado_hist = float((ventas_pagadas_df["cantidad"] * ventas_pagadas_df["precio_unitario"]).sum()) if not ventas_pagadas_df.empty else 0.0
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Vendido (pagado)</div><div class="metric-value">{moneda(total_pagado_hist)}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Cantidad de Ventas</div><div class="metric-value">{len(ventas_pagadas_df)}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if ventas_pagadas_df.empty:
            st.info("Todav\u00eda no hay ventas pagadas registradas. Usa 'Nueva Venta' para empezar.")
        else:
            render_tabla_movimientos(ventas_pagadas_df)

    # -----------------------------------------------------------------------------
    # COMPRAR / REPONER STOCK
    # -----------------------------------------------------------------------------
    elif menu == "comprar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\U0001f4e6 Registrar Compra a Proveedores</div>
    <div class="page-subtitle">Suma unidades al stock existente y registra a qui\u00e9n le compraste y cu\u00e1nto pagaste.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay prendas registradas. Primero registra una prenda desde el men\u00fa correspondiente.")
        else:
            proveedor_nombre = st.text_input("Proveedor", placeholder="Ej: Textiles Andina, Mar\u00eda la mayorista, etc.")

            ids_compra = df["ID"].astype(str).tolist()
            id_compra = st.selectbox(
                "Prenda", ids_compra,
                format_func=lambda x: f"{x} \u2014 {df[df['ID'].astype(str) == x]['Producto'].values[0]}",
            )
            fila = df[df["ID"].astype(str) == str(id_compra)].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                cantidad_comprar = st.number_input("Cantidad a a\u00f1adir", min_value=1, value=1, step=1)
            with col2:
                costo_unit = st.number_input("Costo por unidad", min_value=0.0, value=float(fila.get("costo", 0) or 0), step=1.0)

            monto_total_compra = cantidad_comprar * costo_unit
            st.markdown(f"**Monto total de la compra: {moneda(monto_total_compra)}**")

            actualizar_costo = st.checkbox("Actualizar el costo registrado de esta prenda con este valor", value=True)

            proveedor_valido = proveedor_nombre.strip() != ""

            if st.button("\U0001f4e6 Confirmar Compra", use_container_width=True, disabled=not proveedor_valido):
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
                    st.success(f"\u00a1Compra registrada a {proveedor_nombre}! Total: {moneda(monto_total_compra)}")
                    st.rerun()

            if not proveedor_valido:
                st.caption("\u26a0\ufe0f Escribe el nombre del proveedor para poder confirmar.")

    # -----------------------------------------------------------------------------
    # REGISTRAR PRENDA (solo admin)
    # -----------------------------------------------------------------------------
    elif menu == "registrar":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\u2728 Registro de Nuevas Prendas</div>
    <div class="page-subtitle">A\u00f1ade nuevos art\u00edculos al cat\u00e1logo, con foto, costo y precio de venta.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form(f"form_ropa_{st.session_state.form_version}", clear_on_submit=True):
            encabezado_seccion_form("\U0001f4e6", "Informaci\u00f3n B\u00e1sica")
            col1, col2 = st.columns(2)
            with col1:
                sku = st.text_input("ID", placeholder="Ej: A1")
            with col2:
                nombre = st.text_input("Producto", placeholder="Ej: Short")

            encabezado_seccion_form("\U0001f3f7\ufe0f", "Clasificaci\u00f3n y Atributos")
            col3, col4, col5 = st.columns(3)
            with col3:
                categoria = st.selectbox("Categor\u00eda", st.session_state.categorias_maestras)
            with col4:
                talla = st.selectbox("Talla", st.session_state.tallas_maestras)
            with col5:
                color = st.selectbox("Color", st.session_state.colores_maestros)

            encabezado_seccion_form("\U0001f4ca", "Control de Stock, Precios y Alertas")
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

            encabezado_seccion_form("\U0001f4f7", "Foto del producto (opcional)")
            foto_subida = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg", "webp"])

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("\U0001f4be Guardar Prenda en el Sistema", use_container_width=True):
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
                        st.success("\u00a1Prenda guardada con \u00e9xito!")
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
            modo_seleccion = st.radio("\u00bfC\u00f3mo deseas encontrar la prenda?", ["Seleccionar de la lista", "Buscar por ID / Nombre"], horizontal=True)
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
                    actualizar = col_btn1.form_submit_button("\U0001f4be Guardar Cambios", use_container_width=True)
                    eliminar = col_btn2.form_submit_button("\U0001f5d1\ufe0f Eliminar Prenda", use_container_width=True)

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
                            st.success("\u00a1Prenda actualizada correctamente!")
                            st.rerun()

                    if eliminar:
                        if eliminar_prenda(id_seleccionado):
                            st.success("\u00a1Prenda eliminada del sistema!")
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
    <div class="page-title">\U0001f4dc Historial de Movimientos</div>
    <div class="page-subtitle">Todas las ventas, compras y ajustes registrados en el sistema.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        movs = cargar_movimientos()
        if movs.empty:
            st.info("Todav\u00eda no hay movimientos registrados. Se ir\u00e1n guardando cuando registres ventas o compras.")
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
            st.download_button("\U0001f4e5 Exportar Movimientos a CSV", data=csv_movs,
                                file_name="movimientos_lewin.csv", mime="text/csv")

    # -----------------------------------------------------------------------------
    # FACTURAS
    # -----------------------------------------------------------------------------
    elif menu == "facturas":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\U0001f9fe Facturas</div>
    <div class="page-subtitle">Elige una venta y descarga su factura en PDF.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if not PDF_DISPONIBLE:
            st.warning("Falta instalar la librer\u00eda para generar PDF. Agrega `fpdf2` a tu requirements.txt para activar esta funci\u00f3n.")

        movs_fact = cargar_movimientos()
        ventas_con_id = movs_fact[(movs_fact["tipo"] == "venta") & (movs_fact["venta_id"] != "")] if not movs_fact.empty else pd.DataFrame()

        if ventas_con_id.empty:
            st.info("Todav\u00eda no hay ventas con factura disponible. A partir de ahora, cada venta que registres desde 'Nueva Venta' generar\u00e1 su propia factura autom\u00e1ticamente.")
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
                    f"{formatear_fecha_corta(resumen_facturas[resumen_facturas['venta_id'] == x]['fecha'].values[0])} \u2014 "
                    f"{resumen_facturas[resumen_facturas['venta_id'] == x]['cliente'].values[0]} \u2014 "
                    f"{moneda(resumen_facturas[resumen_facturas['venta_id'] == x]['total'].values[0])}"
                    + ("" if resumen_facturas[resumen_facturas['venta_id'] == x]['pagado'].values[0] else " (pendiente)")
                ),
            )

            items_venta_sel = ventas_con_id[ventas_con_id["venta_id"] == venta_sel]
            fila_resumen = resumen_facturas[resumen_facturas["venta_id"] == venta_sel].iloc[0]

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Vista previa</div>", unsafe_allow_html=True)

            filas_preview = ""
            for idx, (_, r) in enumerate(items_venta_sel.iterrows()):
                bg_fila = "#fdf2f8" if idx % 2 == 0 else "#ffffff"
                filas_preview += f"""<tr style="background:{bg_fila};">
<td style="padding:10px 14px;">{r['producto']}</td>
<td style="padding:10px 14px; text-align:center;">{int(r['cantidad'])}</td>
<td style="padding:10px 14px; text-align:right;">{moneda(r['precio_unitario'])}</td>
<td style="padding:10px 14px; text-align:right;">{moneda(r['cantidad'] * r['precio_unitario'])}</td>
</tr>"""

            estado_badge = (
                "<span style='background:#dcfce7; color:#16a34a; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700;'>PAGADA</span>"
                if fila_resumen["pagado"] else
                "<span style='background:#fef3c7; color:#b45309; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700;'>PENDIENTE</span>"
            )

            factura_preview_html = f"""<div style="background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 15px 40px rgba(0,0,0,0.18); max-width:640px; margin:0 auto; font-family:'Poppins',sans-serif;">
<div style="background:linear-gradient(135deg,#db2777,#ec4899); padding:22px 26px; display:flex; justify-content:space-between; align-items:center;">
<div style="display:flex; align-items:center; gap:12px;">
{logo_svg_markup(32)}
<div>
<div style="color:#fff; font-weight:800; font-size:17px; letter-spacing:0.5px;">LEWIN BOUTIQUE</div>
<div style="color:#fce7f3; font-size:11px;">Factura de venta</div>
</div>
</div>
<div style="text-align:right;">
<div style="color:#fff; font-weight:700; font-size:13px;">N. {str(venta_sel)[:8].upper()}</div>
<div style="color:#fce7f3; font-size:11px;">{formatear_fecha_corta(fila_resumen['fecha'])}</div>
</div>
</div>
<div style="padding:20px 26px 6px 26px; display:flex; justify-content:space-between; align-items:flex-start;">
<div>
<div style="color:#9d174d; font-size:10px; font-weight:700; letter-spacing:1px;">FACTURAR A</div>
<div style="color:#211c3d; font-size:16px; font-weight:700; margin-top:2px;">{fila_resumen['cliente']}</div>
</div>
<div>{estado_badge}</div>
</div>
<table style="width:100%; border-collapse:collapse; margin-top:14px; font-size:13px;">
<thead><tr style="background:#db2777;">
<th style="padding:10px 14px; text-align:left; color:#fff; font-size:11px;">PRODUCTO</th>
<th style="padding:10px 14px; text-align:center; color:#fff; font-size:11px;">CANT.</th>
<th style="padding:10px 14px; text-align:right; color:#fff; font-size:11px;">PRECIO UNIT.</th>
<th style="padding:10px 14px; text-align:right; color:#fff; font-size:11px;">SUBTOTAL</th>
</tr></thead>
<tbody style="color:#3a3355;">{filas_preview}</tbody>
</table>
<div style="display:flex; justify-content:flex-end; padding:16px 26px;">
<div style="background:#db2777; color:#fff; padding:10px 24px; border-radius:10px; font-weight:800; font-size:15px; display:flex; gap:18px;">
<span>TOTAL</span><span>{moneda(fila_resumen['total'])}</span>
</div>
</div>
<div style="text-align:center; padding:8px 20px 22px 20px; color:#9d174d; font-size:11px; font-style:italic;">Gracias por tu compra</div>
</div>"""
            st.markdown(factura_preview_html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            items_para_pdf = items_venta_sel[["producto", "cantidad", "precio_unitario"]].to_dict("records")

            pdf_bytes = None
            if PDF_DISPONIBLE:
                pdf_bytes = generar_factura_pdf(
                    venta_sel, fila_resumen["cliente"], formatear_fecha_corta(fila_resumen["fecha"]),
                    items_para_pdf, fila_resumen["total"],
                )

            col_img, col_pdf, col_wa = st.columns(3)
            with col_img:
                if IMAGEN_FACTURA_DISPONIBLE and pdf_bytes:
                    imagen_bytes = generar_factura_imagen(pdf_bytes, len(items_para_pdf))
                    if imagen_bytes:
                        st.download_button(
                            "\U0001f5bc\ufe0f Descargar como Imagen", data=imagen_bytes,
                            file_name=f"factura_{str(venta_sel)[:8]}.png", mime="image/png",
                            use_container_width=True,
                        )
                        st.caption("Ideal para enviar como foto por WhatsApp.")
                else:
                    st.caption("\u26a0\ufe0f Falta instalar `pymupdf` en tu requirements.txt para esta opci\u00f3n.")
            with col_pdf:
                if PDF_DISPONIBLE:
                    st.download_button(
                        "\U0001f4c4 Descargar en PDF", data=pdf_bytes,
                        file_name=f"factura_{str(venta_sel)[:8]}.pdf", mime="application/pdf",
                        use_container_width=True,
                    )
            with col_wa:
                texto_wa = generar_texto_whatsapp_factura(
                    venta_sel, fila_resumen["cliente"], formatear_fecha_corta(fila_resumen["fecha"]),
                    items_para_pdf, fila_resumen["total"], bool(fila_resumen["pagado"]),
                )
                link_wa = "https://wa.me/?text=" + urllib.parse.quote(texto_wa)
                st.link_button("\U0001f4ac Enviar Texto por WhatsApp", url=link_wa, use_container_width=True)

            st.caption("Para enviar la imagen por WhatsApp: desc\u00e1rgala con el primer bot\u00f3n y adj\u00fantala como foto en el chat.")

    # -----------------------------------------------------------------------------
    # DEUDORES (cuentas por cobrar)
    # -----------------------------------------------------------------------------
    elif menu == "deudores":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\U0001f9fe Ventas por Pagar</div>
    <div class="page-subtitle">Lleva el control de qui\u00e9n te debe, cu\u00e1nto le fiaste y cu\u00e1nto te ha pagado.</div>
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

        with st.expander("\U0001f465 Ver todas las personas registradas"):
            if deudores_df.empty:
                st.info("Todav\u00eda no has agregado a nadie.")
            else:
                deudores_ordenado = deudores_df.sort_values("saldo", ascending=False)
                for _, fila in deudores_ordenado.iterrows():
                    saldo_val = float(fila.get("saldo", 0) or 0)
                    color_saldo = "#f472b6" if saldo_val > 0 else "#34d399"
                    telefono_txt = fila.get("telefono") or "\u2014"
                    st.markdown(
                        f"<div class='config-chip' style='justify-content: space-between;'>"
                        f"<span>{fila['nombre']} <span style='color: var(--text-secondary); font-size: 11px;'>({telefono_txt})</span></span>"
                        f"<span style='color: {color_saldo}; font-weight: 700;'>{moneda(saldo_val)}</span></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<br><hr style='border-color: var(--border-color);'><br>", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>\U0001f50d Buscar Persona y Cobrar</div><div class='section-subtitle'>Encuentra a alguien para ver su saldo, su historial, o registrarle un pago.</div>", unsafe_allow_html=True)

        if deudores_df.empty:
            st.info("Todav\u00eda no hay personas registradas. Usa la secci\u00f3n de arriba para agregar la primera.")
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
            telefono_buscado = fila_buscada.get("telefono") or "\u2014"

            st.markdown(
                f"""<div class="product-card" style="border-color: var(--border-color);">
<div class="product-card-body">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<div style="font-size: 18px; font-weight: 700; color: var(--text-color);">{fila_buscada['nombre']}</div>
<div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">\U0001f4de {telefono_buscado}</div>
</div>
<div style="font-size: 24px; font-weight: 800; color: {color_saldo_buscado};">{moneda(saldo_buscado)}</div>
</div>
</div>
</div>""",
                unsafe_allow_html=True,
            )

            col_pago1, col_pago2 = st.columns(2)
            with col_pago1:
                moneda_pago_sel = st.radio("\u00bfEn qu\u00e9 moneda pag\u00f3?", ["D\u00f3lares ($)", "Bol\u00edvares (Bs)"], horizontal=True, key="moneda_pago_sel")
            with col_pago2:
                medio_pago_sel = st.selectbox(
                    "Medio de pago",
                    ["Efectivo", "Pago M\u00f3vil", "Transferencia", "Zelle", "Otro"],
                    key="medio_pago_buscar",
                )

            if moneda_pago_sel == "Bol\u00edvares (Bs)":
                tasa_cobro, fuente_tasa_cobro = selector_tasa_cambio("cobro")
                monto_bs_ingresado = st.number_input("Monto recibido en Bs", min_value=0.0, step=1.0, key="monto_bs_cobro")
                monto_pago_usd = (monto_bs_ingresado / tasa_cobro) if tasa_cobro > 0 else 0.0
                if tasa_cobro > 0:
                    st.caption(f"\U0001f4b1 Equivalente: {moneda(monto_pago_usd)}")
                else:
                    st.caption("\u26a0\ufe0f Elige una tasa para poder calcular el equivalente en d\u00f3lares.")
            else:
                tasa_cobro = 0.0
                monto_pago_usd = st.number_input("Monto recibido en $", min_value=0.0, step=1.0, key="monto_usd_cobro")

            nota_pago = st.text_input("Nota (opcional)", placeholder="Ej: abono parcial", key="nota_pago_buscar")

            if st.button("\U0001f4b5 Registrar Este Pago", use_container_width=True, key="btn_registrar_pago_buscar"):
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
                    st.success(f"\u00a1Pago registrado! Nuevo saldo de {fila_buscada['nombre']}: {moneda(nuevo_saldo_buscado)}")
                    st.rerun()

            with st.expander(f"\U0001f4dc Historial de {fila_buscada['nombre']}"):
                deudas_mov_todas = cargar_deudas_movimientos()
                historial_persona = deudas_mov_todas[deudas_mov_todas["deudor_id"].astype(str) == str(id_buscado)] if not deudas_mov_todas.empty else pd.DataFrame()
                if historial_persona.empty:
                    st.info("Todav\u00eda no hay movimientos con esta persona.")
                else:
                    render_tabla_deudas(historial_persona)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"\U0001f5d1\ufe0f Eliminar a {fila_buscada['nombre']} del sistema", key="btn_eliminar_persona_buscada"):
                if eliminar_deudor(id_buscado):
                    st.success(f"{fila_buscada['nombre']} fue eliminada/o.")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>\U0001f4dc Historial General</div><div class='section-subtitle'>Todos los cargos y abonos registrados, de todas las personas.</div>", unsafe_allow_html=True)
        deudas_mov = cargar_deudas_movimientos()
        if deudas_mov.empty:
            st.info("A\u00fan no hay movimientos de deudores registrados.")
        else:
            render_tabla_deudas(deudas_mov)

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("\U0001f5d1\ufe0f Eliminar un movimiento del historial"):
                opciones_mov = deudas_mov["id"].astype(str).tolist()
                mov_a_borrar = st.selectbox(
                    "Elige el movimiento a eliminar",
                    opciones_mov,
                    format_func=lambda x: (
                        f"{formatear_fecha_corta(deudas_mov[deudas_mov['id'].astype(str) == x]['fecha'].values[0])} \u2014 "
                        f"{deudas_mov[deudas_mov['id'].astype(str) == x]['deudor_nombre'].values[0]} \u2014 "
                        f"{deudas_mov[deudas_mov['id'].astype(str) == x]['tipo'].values[0]} \u2014 "
                        f"{moneda(deudas_mov[deudas_mov['id'].astype(str) == x]['monto'].values[0])}"
                    ),
                    key="select_borrar_deuda_mov",
                )
                st.caption("Al eliminarlo, el saldo de esa persona se ajusta autom\u00e1ticamente.")
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
    <div class="page-title">\U0001f4c8 Reportes y Rentabilidad</div>
    <div class="page-subtitle">Ventas, productos m\u00e1s vendidos y valorizaci\u00f3n del inventario.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_reset1, col_reset2 = st.columns([3, 1])
        with col_reset2:
            if st.button("\U0001f504 Restablecer Reportes", use_container_width=True):
                st.session_state.confirmar_reset_reportes = True

        if st.session_state.get("confirmar_reset_reportes"):
            st.markdown(
                "<div class='alert-banner'>\u26a0\ufe0f <b>\u00bfSeguro que quieres restablecer el apartado de Reportes?</b><br>"
                "Esto borrar\u00e1 TODO el historial de ventas y compras registrado hasta ahora.</div>",
                unsafe_allow_html=True,
            )
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("\u2705 S\u00ed, restablecer todo", use_container_width=True):
                    if eliminar_todos_los_movimientos():
                        st.session_state.confirmar_reset_reportes = False
                        st.success("\u00a1Listo! Los reportes y el historial de movimientos quedaron en cero.")
                        st.rerun()
            with col_c2:
                if st.button("\u2715 Cancelar", use_container_width=True):
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
            (col1, "Total Vendido (hist\u00f3rico)", moneda(total_ventas)),
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
            st.plotly_chart(grafico_barras_vertical(ventas_mes, formato_valor=moneda), use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='section-title'>Top 5 productos m\u00e1s vendidos (unidades)</div>", unsafe_allow_html=True)
            top_productos = ventas.groupby("producto")["cantidad"].sum().sort_values(ascending=False).head(5)
            st.plotly_chart(grafico_barras_horizontal(top_productos), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("A\u00fan no hay ventas registradas para generar gr\u00e1ficas.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_dona1, col_dona2 = st.columns(2)

        with col_dona1:
            st.markdown("<div class='section-title'>Inventario por categor\u00eda</div>", unsafe_allow_html=True)
            if not df.empty:
                inv_por_cat = df.groupby("Categoria")["cantidad"].sum()
                inv_por_cat = inv_por_cat[inv_por_cat > 0]
                if not inv_por_cat.empty:
                    st.plotly_chart(
                        grafico_dona(inv_por_cat, texto_centro_arriba=str(int(inv_por_cat.sum())), texto_centro_abajo="unidades"),
                        use_container_width=True, config={"displayModeBar": False},
                    )
                else:
                    st.info("No hay stock registrado todav\u00eda.")
            else:
                st.info("No hay prendas registradas todav\u00eda.")

        with col_dona2:
            st.markdown("<div class='section-title'>Ventas por categor\u00eda</div>", unsafe_allow_html=True)
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
                    st.info("A\u00fan no hay suficientes ventas para mostrar por categor\u00eda.")
            else:
                st.info("A\u00fan no hay ventas registradas.")

    # -----------------------------------------------------------------------------
    # CONFIGURACIÓN (solo admin)
    # -----------------------------------------------------------------------------
    elif menu == "configuracion":
        st.markdown(
            """
<div class="page-header">
    <div class="page-title">\u2699\ufe0f Configuraci\u00f3n del Sistema</div>
    <div class="page-subtitle">Gestiona y personaliza las opciones maestras de categor\u00edas, tallas y colores.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)

        with col_cfg1:
            with st.container(border=True):
                encabezado_seccion_form("\U0001f4c2", "Categor\u00edas")
                for cat in list(st.session_state.edit_cats):
                    c_col1, c_col2 = st.columns([4, 1])
                    with c_col1:
                        st.markdown(f"<div class='config-chip'>{cat}</div>", unsafe_allow_html=True)
                    with c_col2:
                        if st.button("\u2715", key=f"del_cat_{cat}", use_container_width=True):
                            if len(st.session_state.edit_cats) > 1:
                                st.session_state.edit_cats.remove(cat)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_cat_input = st.text_input("Nueva Categor\u00eda", placeholder="Ej: Faldas", key="input_nueva_cat")
                if st.button("\u2795 Agregar Categor\u00eda", key="btn_add_cat", use_container_width=True):
                    clean_cat = nueva_cat_input.strip().capitalize()
                    if clean_cat and clean_cat not in st.session_state.edit_cats:
                        st.session_state.edit_cats.append(clean_cat)
                        st.rerun()
                    else:
                        st.warning("Nombre inv\u00e1lido o ya existente.")

        with col_cfg2:
            with st.container(border=True):
                encabezado_seccion_form("\U0001f4cf", "Tallas")
                for t in list(st.session_state.edit_tallas):
                    t_col1, t_col2 = st.columns([4, 1])
                    with t_col1:
                        st.markdown(f"<div class='config-chip'>{t}</div>", unsafe_allow_html=True)
                    with t_col2:
                        if st.button("\u2715", key=f"del_talla_{t}", use_container_width=True):
                            if len(st.session_state.edit_tallas) > 1:
                                st.session_state.edit_tallas.remove(t)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos una.")
                st.markdown("<br>", unsafe_allow_html=True)
                nueva_talla_input = st.text_input("Nueva Talla", placeholder="Ej: 30, XXL", key="input_nueva_talla")
                if st.button("\u2795 Agregar Talla", key="btn_add_talla", use_container_width=True):
                    clean_talla = nueva_talla_input.strip().upper()
                    if clean_talla and clean_talla not in st.session_state.edit_tallas:
                        st.session_state.edit_tallas.append(clean_talla)
                        st.rerun()
                    else:
                        st.warning("Talla inv\u00e1lida o ya existente.")

        with col_cfg3:
            with st.container(border=True):
                encabezado_seccion_form("\U0001f3a8", "Colores")
                for col_item in list(st.session_state.edit_colores):
                    col_c1, col_c2 = st.columns([4, 1])
                    with col_c1:
                        st.markdown(f"<div class='config-chip'>{col_item}</div>", unsafe_allow_html=True)
                    with col_c2:
                        if st.button("\u2715", key=f"del_color_{col_item}", use_container_width=True):
                            if len(st.session_state.edit_colores) > 1:
                                st.session_state.edit_colores.remove(col_item)
                                st.rerun()
                            else:
                                st.error("Debe existir al menos uno.")
                st.markdown("<br>", unsafe_allow_html=True)
                nuevo_color_input = st.text_input("Nuevo Color", placeholder="Ej: Dorado", key="input_nuevo_color")
                if st.button("\u2795 Agregar Color", key="btn_add_color", use_container_width=True):
                    clean_color = nuevo_color_input.strip().capitalize()
                    if clean_color and clean_color not in st.session_state.edit_colores:
                        st.session_state.edit_colores.append(clean_color)
                        st.rerun()
                    else:
                        st.warning("Color inv\u00e1lido o ya existente.")

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_save_master, _ = st.columns([1, 2, 1])
        with col_save_master:
            if st.button("\U0001f4be Guardar configuraci\u00f3n en GitHub", use_container_width=True):
                exito = guardar_configuracion_completa(
                    st.session_state.edit_cats, st.session_state.edit_tallas, st.session_state.edit_colores
                )
                if exito:
                    st.session_state.categorias_maestras = list(st.session_state.edit_cats)
                    st.session_state.tallas_maestras = list(st.session_state.edit_tallas)
                    st.session_state.colores_maestros = list(st.session_state.edit_colores)
                    st.success("\u00a1Configuraci\u00f3n guardada en GitHub exitosamente!")
                    st.rerun()
