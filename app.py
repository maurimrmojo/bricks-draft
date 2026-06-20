import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os

# Configuración de la página web
st.set_page_config(page_title="Draft a la carta", layout="wide")

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =====================================================================
PASSWORD_STREAM = "bricks2026"
PASSWORD_MAESTRA = "bricks2026admin"
ARCHIVO_BD = "datos_draft.json"

def cargar_datos_globales():
    if os.path.exists(ARCHIVO_BD):
        try:
            with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"jugadores": {}, "historial_partidos": []}

def guardar_datos_globales(jugadores, historial):
    datos = {"jugadores": jugadores, "historial_partidos": historial}
    with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

datos_guardados = cargar_datos_globales()
if "jugadores" not in st.session_state: st.session_state.jugadores = datos_guardados["jugadores"]
if "historial_partidos" not in st.session_state: st.session_state.historial_partidos = datos_guardados["historial_partidos"]
if "draft_manual" not in st.session_state: st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}

# --- SIDEBAR ---
st.sidebar.title("🍔 Bricks a la carta")
password_ingresada = st.sidebar.text_input("Contraseña:", type="password")
es_admin_stream = (password_ingresada == PASSWORD_STREAM or password_ingresada == PASSWORD_MAESTRA)
es_super_admin = (password_ingresada == PASSWORD_MAESTRA)

if es_super_admin: st.sidebar.success("👑 SUPER-ADMIN Activo")
elif es_admin_stream: st.sidebar.success("🔓 Streamer Activo")
else: st.sidebar.info("👁️ Modo Espectador")

# =====================================================================
# VENTANA: ROSTER Y GESTIÓN (PRIVADO)
# =====================================================================
if es_super_admin and st.sidebar.radio("Navegación:", ["Mesa de Draft", "Administración"]) == "Administración":
    st.title("⚙️ Panel de Administración")
    
    # 1. Gestión de Partidos (Anti-Troll Total)
    st.header("🚨 Gestión de Partidos")
    if st.session_state.historial_partidos:
        opciones_partidos = [f"#{i+1}: {p['Equipos']} | {p['Resultado']}" for i, p in enumerate(st.session_state.historial_partidos)]
        idx_elegido = st.selectbox("Seleccionar partido para gestionar:", range(len(opciones_partidos)), format_func=lambda x: opciones_partidos[x])
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🗑️ ELIMINAR ESTE PARTIDO", type="primary"):
                st.session_state.historial_partidos.pop(idx_elegido)
                guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                st.rerun()
        with col_btn2:
            with st.expander("✏️ Corregir Resultado"):
                p_edit1 = st.number_input("Puntos Eq 1:", value=0, key="edit_1")
                p_edit2 = st.number_input("Puntos Eq 2:", value=0, key="edit_2")
                if st.button("Guardar Corrección"):
                    st.session_state.historial_partidos[idx_elegido]["Resultado"] = f"{p_edit1} - {p_edit2}"
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.rerun()
    else:
        st.info("No hay partidos registrados.")

# =====================================================================
# VENTANA PRINCIPAL (Mesa de Draft + Historial Permanente)
# =====================================================================
else:
    st.title("🏀 Mesa de Draft")
    # [Aquí iría toda la lógica de convocatoria y draft...]
    
    st.write("---")
    
    # HISTORIAL SIEMPRE VISIBLE (Mejora: Accesible a todos)
    st.header("📜 Historial de Resultados")
    if st.session_state.historial_partidos:
        for idx, part in enumerate(reversed(st.session_state.historial_partidos)):
            st.info(f"**Partido #{len(st.session_state.historial_partidos)-idx}:** {part['Equipos']} ➔ **{part['Resultado']}**")
    else:
        st.write("Todavía no hay partidos en la temporada.")
