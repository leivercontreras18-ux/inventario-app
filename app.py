import streamlit as st

st.set_page_config(
    page_title="Login - Lewin Boutique",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ocultar interfaz por defecto de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .stApp {
        background-color: #0b0f17;
    }
    </style>
""", unsafe_allow_html=True)

# Código HTML/CSS de la interfaz ajustado
login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #0b0f17;
      background-image: linear-gradient(180deg, rgba(11, 15, 23, 0.88) 0%, rgba(15, 20, 31, 0.82) 100%), 
                        url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200&auto=format&fit=crop');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      box-sizing: border-box;
    }

    .brand-logo-wrapper {
      margin-bottom: 28px;
      display: flex;
      justify-content: center;
      filter: drop-shadow(0 12px 20px rgba(0, 0, 0, 0.6));
    }

    .auth-card {
      width: 100%;
      max-width: 415px;
      background-color: #171d29; 
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 24px;
      padding: 48px 36px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75);
      text-align: center;
      box-sizing: border-box;
    }

    h1 {
      color: #ffffff;
      font-size: 32px;
      font-weight: 700;
      margin: 0 0 12px 0;
      letter-spacing: -0.5px;
    }
    h1 span {
      color: #ff9f00;
    }
    .system-subtitle {
      color: #ff9f00;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.6px;
      margin: 0 0 38px 0;
    }

    .input-group {
      text-align: left;
      margin-bottom: 24px;
    }
    label {
      display: block;
      color: #7a869a;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
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
      color: #505d76;
      font-size: 14px;
      display: flex;
      align-items: center;
    }
    input {
      width: 100%;
      background-color: #11151e; 
      border: 1px solid rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      padding: 16px 16px 16px 46px;
      color: #ffffff;
      font-size: 14px;
      outline: none;
      box-sizing: border-box;
      transition: all 0.2s ease-in-out;
    }
    input::placeholder {
      color: #404b5e;
    }
    input:focus {
      border-color: rgba(255, 159, 0, 0.3);
      background-color: #0c0f16;
    }
    
    .password-toggle-btn {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #ff9f00;
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
    }

    .recovery-link {
      display: block;
      text-align: right;
      color: #ff9f00;
      font-size: 12px;
      text-decoration: none;
      margin-top: 10px;
      font-weight: 600;
    }
    .recovery-link:hover {
      text-decoration: underline;
    }

    .submit-button {
      width: 100%;
      background: linear-gradient(180deg, #3a312c 0%, #2b2421 100%);
      border: 1px solid rgba(255, 255, 255, 0.03);
      border-radius: 14px;
      padding: 16px;
      color: #ffffff;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin-top: 32px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      transition: all 0.2s ease;
    }
    .submit-button:hover {
      filter: brightness(1.1);
    }

    .row-separator {
      position: relative;
      margin: 32px 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .separator-line {
      width: 100%;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    .separator-text {
      position: absolute;
      background-color: #171d29;
      padding: 0 14px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.4px;
      color: #505d76;
    }

    .social-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .social-button {
      background-color: #11151e;
      border: 1px solid rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      padding: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.2s;
    }
    .social-button:hover {
      background-color: #0c0f16;
    }
    .icon-blue { color: #00a2ff; }
    .icon-gray { color: #ffffff; }
    .icon-brown { color: #c48b59; }

    .signup-footer {
      margin-top: 36px;
      font-size: 12px;
      color: #505d76;
    }
    .signup-footer a {
      color: #ff9f00;
      text-decoration: none;
      font-weight: 700;
    }
  </style>
</head>
<body>

  <div class="brand-logo-wrapper">
    <svg width="115" height="115" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 15 L40 15 L40 68 L58 68 L58 85 L15 85 Z" fill="url(#metal-premium)" stroke="#333" stroke-width="0.5"/>
      <path d="M60 15 L74 15 L79 65 L84 15 L98 15 L90 85 L76 85 L70 45 L64 85 L50 85 Z" fill="url(#metal-premium)" stroke="#333" stroke-width="0.5"/>
      <defs>
        <linearGradient id="metal-premium" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#cbd5e1" />
          <stop offset="30%" stop-color="#ffffff" />
          <stop offset="50%" stop-color="#475569" />
          <stop offset="75%" stop-color="#94a3b8" />
          <stop offset="100%" stop-color="#11151e" />
        </linearGradient>
      </defs>
    </svg>
  </div>

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
      <button class="social-button"><span class="icon-blue" style="font-size: 16px;">🌐</span></button>
      <button class="social-button"><span class="icon-gray" style="font-size: 16px;">💻</span></button>
      <button class="social-button"><span class="icon-brown" style="font-size: 16px;">💼</span></button>
    </div>

    <p class="signup-footer">Don't have an account? <a href="#">Sign Up</a></p>

  </div>

</body>
</html>
"""

st.components.v1.html(login_html, height=880, scrolling=True)
