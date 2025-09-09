import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="INTEGRaL 360 - Programa de Lealtad", layout="wide")
st.title("☕ Bienvenido a Café Integral: Tu Programa de Lealtad")
st.markdown("Accede con tu ID o QR, actualiza tus datos y descubre promociones exclusivas. Gana puntos con cada visita.")

# Conexión segura sin cache
def get_db_connection():
    return sqlite3.connect('integral360.db', check_same_thread=False)

if 'cliente' not in st.session_state:
    st.session_state.cliente = None

# Acceso
st.header("Accede a tu Cuenta")
col1, col2 = st.columns([2, 1])
with col1:
    cliente_id = st.text_input("Ingresa tu ID de cliente (o escanea tu QR)", key="cliente_id")
with col2:
    if st.button("Acceder", key="btn_acceder"):
        try:
            if cliente_id.strip() == "":
                st.warning("Por favor ingresa tu ID antes de continuar.")
            else:
                with get_db_connection() as conn:
                    cliente = pd.read_sql(f"SELECT * FROM clientes WHERE id={int(cliente_id)}", conn)
                if not cliente.empty:
                    st.session_state.cliente = cliente.iloc[0]
                    st.success(f"¡Hola {cliente['nombre'].iloc[0]}! Tienes {cliente['puntos_lealtad'].iloc[0]} puntos.")
                else:
                    st.error("ID no encontrado. Contacta al negocio para registrarte.")
        except ValueError:
            st.error("Ingresa un ID válido (número entero).")
        except Exception as e:
            st.error(f"Error al acceder: {str(e)}")

# Actualización de datos
if st.session_state.cliente is not None:
    st.header("Actualiza tus Datos y Gana Puntos")
    with st.form("cuestionario"):
        nombre = st.text_input("Nombre", value=st.session_state.cliente['nombre'])
        email = st.text_input("Email", value=st.session_state.cliente['email'])
        telefono = st.text_input("Teléfono", value=st.session_state.cliente['telefono'])
        direccion = st.text_input("Dirección", value=st.session_state.cliente['direccion'])
        edad = st.number_input("Edad", min_value=18, max_value=100, value=int(st.session_state.cliente['edad']))

        # Traducción segura de sexo
        sexo_valor = st.session_state.cliente['sexo']
        sexo_opciones = ["Femenino", "Masculino", "Otro"]
        sexo_mapeo = {"F": "Femenino", "M": "Masculino", "Otro": "Otro"}
        sexo_traducido = sexo_mapeo.get(sexo_valor, "Otro")
        sexo_index = sexo_opciones.index(sexo_traducido)
        sexo = st.selectbox("Sexo", sexo_opciones, index=sexo_index)

        # Traducción segura de preferencias
        pref_valor = st.session_state.cliente['preferencias']
        pref_opciones = ["Dulce", "Amargo", "Equilibrado"]
        pref_index = pref_opciones.index(pref_valor) if pref_valor in pref_opciones else 0
        preferencias = st.selectbox("Preferencia de sabor", pref_opciones, index=pref_index)

        submitted = st.form_submit_button("Enviar y Ganar 10 Puntos")

        if submitted:
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("""
                        UPDATE clientes 
                        SET nombre=?, email=?, telefono=?, direccion=?, edad=?, sexo=?, preferencias=?,
                            puntos_lealtad=puntos_lealtad+10, ultima_visita=?
                        WHERE id=?
                    """, (nombre, email, telefono, direccion, edad, sexo, preferencias, 
                          datetime.now().strftime('%Y-%m-%d'), st.session_state.cliente['id']))
                    conn.commit()
                st.session_state.cliente['nombre'] = nombre
                st.session_state.cliente['email'] = email
                st.session_state.cliente['telefono'] = telefono
                st.session_state.cliente['direccion'] = direccion
                st.session_state.cliente['edad'] = edad
                st.session_state.cliente['sexo'] = sexo
                st.session_state.cliente['preferencias'] = preferencias
                st.session_state.cliente['puntos_lealtad'] += 10
                st.session_state.cliente['ultima_visita'] = datetime.now().strftime('%Y-%m-%d')
                st.success("¡Datos actualizados! Ganaste 10 puntos. Recibe promo: 10% off en tu próximo latte.")
            except Exception as e:
                st.error(f"Error al actualizar datos: {str(e)}")

# Panel personalizado
if st.session_state.cliente is not None:
    st.header("🎯 Tu Perfil y Recompensas")

    try:
        with get_db_connection() as conn:
            historial = pd.read_sql(f"SELECT fecha, total FROM ventas WHERE cliente_id={st.session_state.cliente['id']}", conn)
            cluster_info = pd.read_sql(f"SELECT cluster FROM clientes WHERE id={st.session_state.cliente['id']}", conn)

        visitas = len(historial)
        gasto_total = historial['total'].sum()
        ticket_prom = gasto_total / visitas if visitas > 0 else 0
        cluster = cluster_info['cluster'].iloc[0] if not cluster_info.empty else -1

        perfiles = {
            0: "🎓 Estudiante con consumo moderado",
            1: "💼 Profesional con alto poder adquisitivo",
            2: "🎨 Creativo con consumo variable",
            -1: "Perfil no clasificado aún"
        }

        st.markdown(f"**Tu perfil:** {perfiles.get(cluster)}")
        st.markdown(f"**Visitas registradas:** {visitas}")
        st.markdown(f"**Ticket promedio:** ${ticket_prom:.0f}")
        st.markdown(f"**Puntos actuales:** {st.session_state.cliente['puntos_lealtad']}")

        # Simulador de recompensas
        st.subheader("🔮 Simulador de Recompensas")
        visitas_futuras = st.slider("¿Cuántas veces planeas visitarnos este mes?", 0, 10, 3)
        puntos_proyectados = st.session_state.cliente['puntos_lealtad'] + (visitas_futuras * 10)
        st.markdown(f"Si cumples tu meta, tendrás **{puntos_proyectados} puntos**.")
        if puntos_proyectados >= 100:
            st.success("🎁 ¡Desbloqueas combo gratis de café + snack!")
        elif puntos_proyectados >= 50:
            st.info("☕ Obtienes 20% de descuento en tu bebida favorita.")

        # Promociones personalizadas
        st.subheader("🎁 Promociones para Ti")
        if cluster == 0:
            st.markdown("- 2x1 en café americano los lunes")
        elif cluster == 1:
            st.markdown("- 15% off en espresso doble entre semana")
        elif cluster == 2:
            st.markdown("- Combo creativo: café + pan artesanal por $55")

        # Historial de visitas
        st.subheader("📅 Historial de Visitas")
        if not historial.empty:
            st.dataframe(historial.sort_values('fecha', ascending=False))
        else:
            st.info("Aún no tienes visitas registradas.")

        # Sugerencias
        st.subheader("📢 ¿Qué te gustaría ver en el menú?")
        sugerencia = st.text_area("Escribe tu sugerencia aquí")
        enviar = st.button("Enviar sugerencia", key="enviar_sugerencia")

        if enviar and sugerencia.strip():
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO sugerencias (cliente_id, texto, fecha) VALUES (?, ?, ?)", 
                              (st.session_state.cliente['id'], sugerencia.strip(), datetime.now().strftime('%Y-%m-%d')))
                    conn.commit()
                st.success("✅ ¡Gracias por tu sugerencia! La tomaremos en cuenta.")
            except Exception as e:
                st.error(f"Error al guardar sugerencia: {str(e)}")
        elif enviar:
            st.warning("Por favor escribe una sugerencia antes de enviar.")
    except Exception as e:
        st.error(f"Error al cargar tu perfil: {str(e)}")

else:
    st.markdown("Accede con tu ID para ver tu perfil, promociones y recompensas personalizadas.")
