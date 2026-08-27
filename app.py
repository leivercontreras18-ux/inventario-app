st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Montserrat:wght@300;400;500;600&display=swap');

/* Fondo General con Gradiente Elegante y Luces Doradas Tenues */
.stApp { 
    background: radial-gradient(circle at 20% 20%, rgba(212, 175, 55, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(184, 134, 11, 0.05) 0%, transparent 40%),
                linear-gradient(135deg, #0f141d 0%, #141a24 50%, #1a2230 100%);
    background-attachment: fixed;
    color: #f8fafc !important; 
}

header[data-testid="stHeader"] { background: transparent !important; }

.block-container {
    max-width: 100% !important;
    padding: 2rem !important;
}

section[data-testid="stSidebar"] { 
    width: 240px !important;
    background: rgba(15, 20, 29, 0.85) !important; 
    border-right: 1px solid rgba(212, 175, 55, 0.2); 
    backdrop-filter: blur(25px); 
}
section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

/* Inputs estándar de Streamlit */
div[data-baseweb="input"], div[data-baseweb="select"] > div {
    background-color: rgba(25, 33, 47, 0.8) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    color: #ffffff !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: #d4af37 !important;
    box-shadow: 0 0 8px rgba(212, 175, 55, 0.3) !important;
}
div[data-baseweb="input"] input {
    color: #ffffff !important;
    font-size: 13px !important;
}

/* Efecto 3D Puerta para TODOS los botones (Ahora en Tono Dorado) */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: #18202c !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
    transition: all 0.4s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1;
    width: 100% !important;
}

div.stButton > button::before, div[data-testid="stFormSubmitButton"] > button::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%);
    transform-origin: left center;
    transform: rotateY(0deg);
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease;
    z-index: -1;
    border-radius: 7px;
}

div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: #d4af37 !important;
    box-shadow: inset 20px 0 30px rgba(212, 175, 55, 0.15), 0 0 20px rgba(212, 175, 55, 0.4) !important;
    color: #ffffff !important;
}

div.stButton > button:hover::before {
    transform: rotateY(72deg);
    opacity: 0.95; 
}

div.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateZ(-30px) scale(0.95) !important;
    box-shadow: 0 0 5px rgba(212, 175, 55, 0.6) !important;
}

/* Tarjeta de Bienvenida Glassmorphism */
.hero-card {
    background: rgba(26, 34, 48, 0.65) !important;
    backdrop-filter: blur(30px) !important;
    -webkit-backdrop-filter: blur(30px) !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 24px;
    padding: 60px 30px 40px 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 30px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    margin-bottom: 25px;
}

/* Formularios Glassmorphism */
div[data-testid="stForm"] {
    background: rgba(26, 34, 48, 0.65) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 16px !important;
    padding: 25px !important;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
}

.page-header { margin-bottom: 25px; padding-bottom: 10px; }
.page-title { font-size: 32px; font-weight: 700; color: #ffffff !important; letter-spacing: 0.5px; }
.page-subtitle { font-size: 14px; color: #a0aec0 !important; margin-top: 4px; }

.section-title { font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
.section-subtitle { font-size: 12px; color: #a0aec0; margin-bottom: 15px; }

.metric-card {
    background: rgba(26, 34, 48, 0.65); 
    backdrop-filter: blur(20px); 
    border: 1px solid rgba(212, 175, 55, 0.2);
    padding: 20px; border-radius: 16px; text-align: left;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    height: 100%;
}
.metric-value { font-size: 32px; font-weight: 800; color: #d4af37 !important; margin-top: 8px; }
.metric-label { font-size: 11px; color: #a0aec0 !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; }

.user-profile { 
    background: rgba(255, 255, 255, 0.05); 
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
</style>
""", unsafe_allow_html=True)
