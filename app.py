# --- 1. FLUJO DE LOGIN NÍTIDO Y UNIFICADO (2 Columnas Reales) ---
if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.1, 3.8, 0.1])
    with col2:
        # Estructura contenedora principal
        st.markdown(
            """
            <div style="
                background: #12151c;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 25px 50px rgba(0,0,0,0.9);
                overflow: hidden;
                width: 100%;
                max-width: 950px;
                margin: 0 auto;
                display: flex;
                flex-wrap: wrap;
            ">
                <!-- Lado Izquierdo: Banner Gráfico -->
                <div style="
                    flex: 1;
                    min-width: 300px;
                    background: linear-gradient(135deg, rgba(15, 18, 25, 0.85) 0%, rgba(20, 15, 30, 0.95) 100%), 
                                url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop');
                    background-size: cover;
                    background-position: center;
                    padding: 70px 40px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    border-right: 1px solid rgba(255, 255, 255, 0.06);
                ">
                    <h1 style="font-family: 'Cinzel', serif; color: #ffffff; font-size: 38px; font-weight: 700; margin-bottom: 12px; line-height: 1.1;">HELLO<br>WELCOME<span style="color: #ff3b3b;">!</span></h1>
                    <p style="color: #94a3b8; font-family: 'Montserrat', sans-serif; font-size: 13px; letter-spacing: 0.8px; line-height: 1.5; margin-top: 10px;">Sistema exclusivo de control de inventario boutique Lewin.</p>
                </div>
                
                <!-- Lado Derecho: Espacio reservado para el formulario -->
                <div style="
                    flex: 1;
                    min-width: 300px;
                    padding: 50px 40px;
                    background: #12151c;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                " id="login-form-container">
                </div>
            </div>
            
            <style>
            /* Hacemos que el formulario de Streamlit ocupe exactamente el espacio derecho sin desfasarse */
            div[data-testid="stForm"] {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                margin-top: -445px !important;
                margin-left: 52% !important;
                width: 44% !important;
            }
            @media(max-width: 768px) {
                div[data-testid="stForm"] {
                    margin-top: 0 !important;
                    margin-left: 0 !important;
                    width: 100% !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_login_nitido"):
            st.markdown(
                """
                <div style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 19px; color: #ffffff; margin-bottom: 2px;">Lewin Boutique</div>
                <div style="display: flex; gap: 15px; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px;">
                    <span style="color: #ff3b3b; font-size: 12px; font-weight: 600; border-bottom: 2px solid #ff3b3b; padding-bottom: 6px; margin-bottom: -7px;">Log in</span>
                    <span style="color: #64748b; font-size: 12px; font-weight: 500;">Sign Up</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<p style='color: #94a3b8; font-size: 11px; font-weight: 500; margin-bottom: 2px;'>Email Address</p>",
                unsafe_allow_html=True,
            )
            usuario_input = st.text_input(
                "Usuario",
                placeholder="Enter your email address",
                label_visibility="collapsed",
            )

            st.markdown(
                "<p style='color: #94a3b8; font-size: 11px; font-weight: 500; margin-bottom: 2px; margin-top: 10px;'>Password</p>",
                unsafe_allow_html=True,
            )
            clave_input = st.text_input(
                "Contraseña",
                type="password",
                placeholder="Enter your password",
                label_visibility="collapsed",
            )

            st.markdown(
                "<div style='display: flex; justify-content: space-between; align-items: center; margin-top: 8px; margin-bottom: 15px;'>"
                "<span style='color: #94a3b8; font-size: 11px;'>⬜ Remember me</span>"
                "<a style='color: #ff3b3b; font-size: 11px; text-decoration: none;' href='#'>Forgot password?</a>"
                "</div>",
                unsafe_allow_html=True,
            )

            boton_enviar = st.form_submit_button("Log in", use_container_width=True)

            st.markdown(
                """
                <div style="text-align: center; color: #64748b; font-size: 11px; margin: 10px 0;">or</div>
                <div style="display: flex; gap: 8px; justify-content: center;">
                    <div style="background: #1a1e29; border: 1px solid rgba(255,255,255,0.08); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #ffffff; text-align: center; flex: 1;">🌐 Google</div>
                    <div style="background: #1a1e29; border: 1px solid rgba(255,255,255,0.08); padding: 8px 12px; border-radius: 8px; font-size: 11px; color: #ffffff; text-align: center; flex: 1;">🍎 Apple</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if boton_enviar:
                if (
                    usuario_input in USUARIOS
                    and USUARIOS[usuario_input] == clave_input
                ):
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario_input
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos.")

    st.stop()
