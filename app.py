import streamlit as st

st.set_page_config(
    page_title="Login - Lewin Boutique",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos globales para integrar la vista limpia en Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0rem;
        max-width: 100%;
    }
    .stApp {
        background-color: #080b11;
    }
    iframe {
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login - Lewin Boutique</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #080b11;
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(255, 159, 0, 0.08) 0%, transparent 50%),
        linear-gradient(180deg, rgba(8, 11, 17, 0.82) 0%, rgba(13, 17, 26, 0.92) 100%),
        url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200&auto=format&fit=crop');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    /* LOGO SUPERIOR CORREGIDO */
    .brand-logo-wrapper {
      margin-bottom: 20px;
      display: flex;
      justify-content: center;
      filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.7));
      transition: transform 0.3s ease;
    }
    .brand-logo-wrapper:hover {
      transform: scale(1.03);
    }

    /* TARJETA GLASSMORPHIC ESTILO UI PINTEREST */
    .auth-card {
      width: 100%;
      max-width: 410px;
      background: rgba(22, 28, 40, 0.75);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 28px;
      padding: 42px 32px;
      box-shadow: 
        0 30px 60px rgba(0, 0, 0, 0.6),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
      text-align: center;
    }

    /* CABECERA */
    h1 {
      color: #ffffff;
      font-size: 30px;
      font-weight: 700;
      margin-bottom: 8px;
      letter-spacing: -0.5px;
    }
    h1 span {
      background: linear-gradient(135deg, #ffb300 0%, #ff8c00 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .system-subtitle {
      color: #ff9f00;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.8px;
      margin-bottom: 34px;
      opacity: 0.9;
    }

    /* INPUTS */
    .input-group {
      text-align: left;
      margin-bottom: 20px;
    }
    label {
      display: block;
      color: #8a99ad;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      margin-bottom: 8px;
      padding-left: 2px;
    }
    .input-container {
      position: relative;
    }
    .input-field-icon {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 14px;
      opacity: 0.7;
    }
    input {
      width: 100%;
      background: rgba(12, 16, 24, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 14px;
      padding: 14px 16px 14px 44px;
      color: #ffffff;
      font-size: 14px;
      outline: none;
      transition: all 0.25s ease;
    }
    input::placeholder {
      color: #434f63;
    }
    input:focus {
      border-color: rgba(255, 159, 0, 0.4);
      background: rgba(12, 16, 24, 0.9);
      box-shadow: 0 0 0 4px rgba(255, 159, 0, 0.08);
    }
    
    .password-toggle-btn {
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #ff9f00;
      cursor: pointer;
      font-size: 14px;
      padding: 4px;
      display: flex;
      align-items: center;
      transition: opacity 0.2s;
    }
    .password-toggle-btn:hover {
      opacity: 0.8;
    }

    .recovery-link {
      display: block;
      text-align: right;
      color: #ff9f00;
      font-size: 11px;
      text-decoration: none;
      margin-top: 8px;
      font-weight: 600;
      transition: color 0.2s;
    }
    .recovery-link:hover {
      color: #ffb300;
      text-decoration: underline;
    }

    /* BOTÓN PRINCIPAL */
    .submit-button {
      width: 100%;
      background: linear-gradient(135deg, #3d3129 0%, #28201b 100%);
      border: 1px solid rgba(255, 180, 100, 0.15);
      border-radius: 14px;
      padding: 15px;
      color: #ffffff;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 28px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
      transition: all 0.25s ease;
    }
    .submit-button:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.5);
      border-color: rgba(255, 159, 0, 0.3);
      filter: brightness(1.15);
    }

    /* SEPARADOR */
    .row-separator {
      position: relative;
      margin: 28px 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .separator-line {
      width: 100%;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .separator-text {
      position: absolute;
      background: #151a26;
      padding: 2px 12px;
      border-radius: 10px;
      font-size: 9px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.4px;
      color: #58667e;
    }

    /* REDES SOCIALES */
    .social-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }
    .social-button {
      background: rgba(12, 16, 24, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
    }
    .social-button:hover {
      background: rgba(20, 26, 38, 0.85);
      border-color: rgba(255, 255, 255, 0.12);
      transform: translateY(-2px);
    }

    /* FOOTER */
    .signup-footer {
      margin-top: 30px;
      font-size: 12px;
      color: #58667e;
    }
    .signup-footer a {
      color: #ff9f00;
      text-decoration: none;
      font-weight: 700;
    }
    .signup-footer a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>

  <!-- LOGO METALIZADO L&W FIX NAMESPACE SVG -->
  <div class="brand-logo-wrapper">
    <svg width="105" height="105" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 15 L40 15 L40 68 L58 68 L58 85 L15 85 Z" fill="url(#metal-premium)" stroke="#333" stroke-width="0.5"/>
      <path d="M60 15 L74 15 L79 65 L84 15 L98 15 L90 85 L76 85 L70 45 L64 85 L50 85 Z" fill="url(#metal-premium)" stroke="#333" stroke-width="0.5"/>
      <defs>
        <linearGradient id="metal-premium" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#e2e8f0" />
          <stop offset="30%" stop-color="#ffffff" />
          <stop offset="50%" stop-color="#475569" />
          <stop offset="75%" stop-color="#94a3b8" />
          <stop offset="100%" stop-color="#0f172a" />
        </linearGradient>
      </defs>
    </svg>
  </div>

  <!-- TARJETA PRINCIPAL -->
  <div class="auth-card">
    
    <h1>Welcome <span>Lewin</span></h1>
    <p class="system-subtitle">Sistema privado de LEWIN BOUTIQUE</p>

    <form onsubmit="event.preventDefault();">
      <div class="input-group">
        <label>Usuario</label>
        <div class="input-container">
          <span class="input-field-icon">👤</span>
          <input type="text" placeholder="Entrar usuario">
        </div>
      </div>

      <div class="input-group">
        <label>Contraseña</label>
        <div class="input-container">
          <span class="input-field-icon">🔒</span>
          <input type="password" placeholder="Entrar contraseña">
          <button type="button" class="password-toggle-btn">👁️</button>
        </div>
        <a href="#" class="recovery-link">Forgot Password?</a>
      </div>

      <button type="submit" class="submit-button">
        Sign In ➔
      </button>
    </form>

    <div class="row-separator">
      <div class="separator-line"></div>
      <span class="separator-text">In continue with</span>
    </div>

    <div class="social-grid">
      <button class="social-button"><span style="color: #00a2ff; font-size: 16px;">🌐</span></button>
      <button class="social-button"><span style="color: #ffffff; font-size: 16px;">💻</span></button>
      <button class="social-button"><span style="color: #c48b59; font-size: 16px;">💼</span></button>
    </div>

    <p class="signup-footer">Don't have an account? <a href="#">Sign Up</a></p>

  </div>

</body>
</html>
"""

st.components.v1.html(login_html, height=820, scrolling=False)
