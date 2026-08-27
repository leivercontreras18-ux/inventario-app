st.markdown(f"<div class='section-title'>Resultados ({inicio+1} - {fin} de {total_registros} registros)</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # Mostrar en formato de tarjetas grid (3 columnas)
                cols_tarjetas = st.columns(3)
                for idx, (_, row) in enumerate(df_paginado.iterrows()):
                    col_actual = cols_tarjetas[idx % 3]
                    
                    # Verificar si está en alerta de stock
                    is_alerta = int(row["cantidad"]) <= int(row["alerta"])
                    borde_color = "#ff3b3b" if is_alerta else "rgba(255, 255, 255, 0.08)"
                    badge_stock = f"<span style='color: #ff3b3b; font-weight: 700;'>Stock Bajo ({row['cantidad']})</span>" if is_alerta else f"<span style='color: #22c55e; font-weight: 700;'>Stock: {row['cantidad']}</span>"

                    with col_actual:
                        st.markdown(
                            f"""
                            <div style="
                                background: rgba(20, 23, 30, 0.75);
                                backdrop-filter: blur(20px);
                                border: 1px solid {borde_color};
                                padding: 18px;
                                border-radius: 14px;
                                margin-bottom: 16px;
                                box-shadow: 0 10px 25px rgba(0,0,0,0.4);
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <span style="background: rgba(212, 175, 55, 0.15); color: #d4af37; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">ID: {row['ID']}</span>
                                    <span style="font-size: 12px; color: #94a3b8;">{row['Categoria']}</span>
                                </div>
                                <div style="font-size: 16px; font-weight: 700; color: #ffffff; margin-bottom: 8px;">{row['Producto']}</div>
                                <div style="font-size: 13px; color: #cbd5e1; display: flex; gap: 12px; margin-bottom: 12px;">
                                    <span>📏 Talla: <b>{row['talla']}</b></span>
                                    <span>🎨 Color: <b>{row['color']}</b></span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; font-size: 13px;">
                                    {badge_stock}
                                    <span style="font-size: 11px; color: #64748b;">Alerta mín: {row['alerta']}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
