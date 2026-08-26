import streamlit as st

st.set_page_config(
    page_title="Login - Lewin Boutique",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ocultar la interfaz por defecto de Streamlit
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
        background-color: #0c0f12;
    }
    </style>
""", unsafe_allow_html=True)

# Código HTML y CSS actualizado
login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background-color: #0c0f12;
      background-image: linear-gradient(135deg, rgba(12, 15, 18, 0.85) 0%, rgba(20, 24, 33, 0.7) 100%), 
                        url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200&auto=format&fit=crop');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-sizing: border-box;
      padding: 20px;
    }

    .logo-container {
      margin-bottom: 25px;
      display: flex;
      justify-content: center;
      filter: drop-shadow(0 15px 20px rgba(0, 0, 0, 0.7));
    }

    .login-card {
      width: 100%;
      max-width: 410px;
      background: linear-gradient(180deg, rgba(26, 32, 44, 0.75) 0%, rgba(18, 22, 28, 0.85) 100%);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 28px;
      padding: 45px 35px;
      box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8);
      text-align: center;
      box-sizing: border-box;
    }

    h1 {
      color: #ffffff;
      font-size: 32px;
      font-weight: 600;
      margin: 0 0 10px 0;
      letter-spacing: 0.5px;
    }
    h1 span {
      background: linear-gradient(to right, #ffb020, #f59e0b);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 700;
    }
    .subtitle {
      color: #f59e0b;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.8px;
      margin: 0 0 40px 0;
    }

    .form-group {
      text-align: left;
      margin-bottom: 22px;
    }
    label {
      display: block;
      color: #94a3b8;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 10px;
      padding-left: 2px;
    }
    .input-wrapper {
      position: relative;
    }
    .input-icon {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      color: #64748b;
      font-size: 15px;
    }
    input {
      width: 100%;
      background: rgba(23, 28, 38, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 14px;
      padding: 15px 16px 15px 46px;
      color: #f1f5f9;
      font-size: 14px;
      outline: none;
      box-sizing: border-box;
      transition: all 0.2s ease;
    }
    input::placeholder {
      color: #475569;
    }
    input:focus {
      border-color: rgba(245, 158, 11, 0.3);
      background: rgba(23, 28, 38, 0.8);
      box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.05);
    }
    
    .eye-icon {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
      font-size: 14px;
    }

    .forgot-link {
      display: block;
      text-align: right;
      color: rgba(245, 158, 11, 0.8);
      font-size: 12px;
      text-decoration: none;
      margin-top: 8px;
    }
    .forgot-link:hover {
      color: #f59e0b;
    }

    .btn-submit {
      width: 100%;
      background: linear-gradient(to right, #2d2522, #47372e, #2d2522);
      border: 1px solid rgba(255, 255, 255, 0.04);
      border-radius: 14px;
      padding: 16px;
      color: #ffffff;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 30px;
      transition: all 0.2s ease;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    .btn-submit:hover {
      filter: brightness(1.15);
    }

    .divider {
      position: relative;
      margin: 30px 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .divider-line {
      width: 100%;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    .divider-text {
      position: absolute;
      background: #141822;
      padding: 0 14px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: #475569;
    }

    .oauth-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .oauth-btn {
      background: rgba(23, 28, 38, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.04);
      border-radius: 14px;
      padding: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    .oauth-btn:hover {
      background: rgba(32, 39, 53, 0.8);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .footer-text {
      margin-top: 35px;
      font-size: 12px;
      color: #475569;
    }
    .footer-text a {
      color: #f59e0b;
      text-decoration: none;
      font-weight: 600;
    }
  </style>
</head>
<body>

  <div class="logo-container">
    <svg width="110" height="110" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 15 L40 15 L40 68 L58 68 L58 85 L15 85 Z" fill="url(#premium-metal)" stroke="#444" stroke-width="0.5"/>
      <path d="M60 15 L74 15 L79 65 L84 15 L98 15 L90 85 L76 85 L70 45 L64 85 L50 85 Z" fill="url(#premium-metal)" stroke="#444" stroke-width="0.5"/>
      <defs>
        <linearGradient id="premium-metal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#cbd5e1" />
          <stop offset="25%" stop-color="#f1f5f9" />
          <stop offset="50%" stop-color="#475569" />
          <stop offset="75%" stop-color="#94a3b8" />
          <stop offset="100%" stop-color="#1e293b" />
        </linearGradient>
      </defs>
    </svg>
  </div>

  <div class="login-card">
    
    <h1>Welcome <span>Lewin</span></h1>
    <p class="subtitle">Sistema privado de LEWIN BOUTIQUE</p>

    <form onsubmit="event.preventDefault();">
      <div class="form-group">
        <label>Usuario</label>
        <div class="input-wrapper">
          <span class="input-icon">👤</span>
          <input type="text" placeholder="Entrar usuario">
        </div>
      </div>

      <div class="form-group">
        <label>Contraseña</label>
        <div class="input-wrapper">
          <span class="input-icon">🔒</span>
          <input type="password" placeholder="Entrar contraseña">
          <button type="button" class="eye-icon">👁️</button>
        </div>
        <a href="#" class="forgot-link">Forgot Password?</a>
      </div>

      <button type="submit" class="btn-submit">
        Sign In ➔
      </button>
    </form>

    <div class="divider">
      <div class="divider-line"></div>
      <span class="divider-text">In continue with</span>
    </div>

    <div class="oauth-row">
      <button class="oauth-btn">🌐</button>
      <button class="oauth-btn">💻</button>
      <button class="oauth-btn">💼</button>
    </div>

    <p class="footer-text">Don't have an account? <a href="#">Sign Up</a></p>

  </div>

</body>
</html>
"""

st.components.v1.html(login_html, height=850, scrolling=True)
