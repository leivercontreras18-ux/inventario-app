import streamlit as st

st.set_page_config(
    page_title="Login - Lewin Boutique",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ocultar la barra superior y pie de página predeterminados de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background-color: #0c0f12;
    }
    </style>
""", unsafe_allow_html=True)

# Inyección del código HTML y CSS completo
login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #0c0f12;
      background-image: linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(12, 15, 18, 0.6) 100%), 
                        url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200&auto=format&fit=crop');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      box-sizing: border-box;
    }

    .login-container {
      width: 100%;
      max-width: 400px;
      padding: 20px;
      text-align: center;
      margin: auto;
    }

    .logo-box {
      margin-bottom: 25px;
      filter: drop-shadow(0 8px 12px rgba(255, 255, 255, 0.05));
    }

    .login-card {
      background: rgba(22, 26, 34, 0.75);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 24px;
      padding: 40px 30px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    }

    h1 {
      color: #ffffff;
      font-size: 28px;
      font-weight: 500;
      margin: 0 0 8px 0;
      letter-spacing: 0.5px;
    }
    h1 span {
      background: linear-gradient(to right, #fbbf24, #d97706);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 700;
    }
    .subtitle {
      color: #f59e0b;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin: 0 0 35px 0;
      opacity: 0.9;
    }

    .form-group {
      text-align: left;
      margin-bottom: 20px;
    }
    label {
      display: block;
      color: #94a3b8;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      padding-left: 4px;
    }
    .input-wrapper {
      position: relative;
    }
    .input-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: #64748b;
      font-size: 14px;
    }
    input {
      width: 100%;
      background: rgba(32, 37, 48, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 12px;
      padding: 14px 16px 14px 42px;
      color: #e2e8f0;
      font-size: 14px;
      outline: none;
      box-sizing: border-box;
      transition: all 0.2s ease;
    }
    input::placeholder {
      color: #475569;
    }
    input:focus {
      border-color: rgba(99, 102, 241, 0.4);
      background: rgba(32, 37, 48, 0.8);
      box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    }
    
    .eye-icon {
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
    }

    .forgot-link {
      display: block;
      text-align: right;
      color: rgba(245, 158, 11, 0.8);
      font-size: 12px;
      text-decoration: none;
      margin-top: 6px;
    }

    .btn-submit {
      width: 100%;
      background: linear-gradient(to right, #2c2724, #4a3b32, #2c2724);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 15px;
      color: #ffffff;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 25px;
      transition: all 0.2s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .btn-submit:hover {
      filter: brightness(1.15);
    }

    .divider {
      position: relative;
      margin: 25px 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .divider-line {
      width: 100%;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .divider-text {
      position: absolute;
      background: #161a22;
      padding: 0 12px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #475569;
    }

    .oauth-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }
    .oauth-btn {
      background: rgba(32, 37, 48, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .footer-text {
      margin-top: 30px;
      font-size: 12px;
      color: #475569;
    }
    .footer-text a {
      color: rgba(245, 158, 11, 0.8);
      text-decoration: none;
      font-weight: 600;
    }
  </style>
</head>
<body>

  <div class="login-container">
    
    <!-- LOGOTIPO LW -->
    <div class="logo-box">
      <svg width="90" height="100" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 20 L42 20 L42 70 L55 70 L55 85 L20 85 Z" fill="url(#metal)" stroke="#555" stroke-width="0.5"/>
        <path d="M60 20 L75 20 L80 65 L85 20 L98 20 L90 85 L75 85 L70 45 L65 85 L52 85 Z" fill="url(#metal)" stroke="#555" stroke-width="0.5"/>
        <defs>
          <linearGradient id="metal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#94a3b8" />
            <stop offset="35%" stop-color="#cbd5e1" />
            <stop offset="50%" stop-color="#475569" />
            <stop offset="65%" stop-color="#e2e8f0" />
            <stop offset="100%" stop-color="#1e293b" />
          </linearGradient>
        </defs>
      </svg>
    </div>

    <!-- TARJETA DE ACCESO -->
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
          Sign In <span>➔</span>
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
  </div>

</body>
</html>
"""

st.components.v1.html(login_html, height=800, scrolling=True)
