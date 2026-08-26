def cargar_configuracion_db():
    if supabase:
        try:
            res = supabase.table("configuracion").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                cats = df[df["tipo"] == "categoria"]["valor"].tolist()
                tallas = df[df["tipo"] == "talla"]["valor"].tolist()
                colores = df[df["tipo"] == "color"]["valor"].tolist()
                return cats, tallas, colores
        except Exception as e:
            pass
    return [], [], []

def agregar_configuracion_db(tipo, valor):
    if supabase:
        try:
            supabase.table("configuracion").insert({"tipo": tipo, "valor": valor}).execute()
            return True
        except Exception:
            return False
    return False

def eliminar_configuracion_db(tipo, valor):
    if supabase:
        try:
            supabase.table("configuracion").delete().eq("tipo", tipo).eq("valor", valor).execute()
            return True
        except Exception:
            return False
    return False
