import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

# Configuración de página
st.set_page_config(page_title="Draft a la Carta - Bricks", layout="wide", initial_sidebar_state="expanded")

# --- VARIABLES GLOBALES Y CONSTANTES ---
CODIGOS_MATCHMAKING = ["1q2w", "3e4r", "5t6y", "7u8i", "9o0p", "asdf", "ghjk", "lzxc", "vbnm", "qwer"]
roles_totales = ["PG", "SG", "SF", "PF", "C"]

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_datos_globales():
    # Intenta cargar desde archivo local, si no crea una estructura base
    if os.path.exists("datos_draft.json"):
        try:
            with open("datos_draft.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"jugadores": {}, "historial_partidos": []}

def guardar_datos_globales(jugadores, historial):
    data = {"jugadores": jugadores, "historial_partidos": historial}
    with open("datos_draft.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- INICIALIZACIÓN DE ESTADO ---
datos_guardados = cargar_datos_globales()
if "jugadores" not in st.session_state: st.session_state.jugadores = datos_guardados["jugadores"]
if "historial_partidos" not in st.session_state: st.session_state.historial_partidos = datos_guardados["historial_partidos"]
if "draft_manual" not in st.session_state: st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
if "lista_espera_forzada" not in st.session_state: st.session_state.lista_espera_forzada = []

# Contador independiente para los códigos del día
if "contador_codigo_dia" not in st.session_state: st.session_state.contador_codigo_dia = 0

cant_partidos = len(st.session_state.historial_partidos)
codigo_actual = CODIGOS_MATCHMAKING[st.session_state.contador_codigo_dia % len(CODIGOS_MATCHMAKING)]

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🏀 Bricks a la carta")

# Autenticación Básica Admin
clave_seguridad = st.sidebar.text_input("Clave de Seguridad:", type="password")
es_admin_stream = (clave_seguridad == "bricks2026admin")

if es_admin_stream:
    st.sidebar.success("👑 SUPER-ADMIN Activo")
else:
    st.sidebar.info("Modo visualizador de Stream")

st.sidebar.write("---")
ver_puntos = st.sidebar.checkbox("Mostrar puntos de jugadores", value=False)

st.sidebar.write("---")
if st.sidebar.button("🔄 Sincronizar Datos", use_container_width=True):
    st.cache_data.clear()
    datos_actualizados = cargar_datos_globales()
    st.session_state.jugadores = datos_actualizados["jugadores"]
    st.session_state.historial_partidos = datos_actualizados["historial_partidos"]
    st.rerun()

# Botón para reiniciar la secuencia de códigos diarios
if st.sidebar.button("♻️ Reiniciar Códigos (Nuevo Día)", type="primary", use_container_width=True):
    st.session_state.contador_codigo_dia = 0
    st.toast("¡Secuencia de códigos reseteada a 1q2w!", icon="✅")
    st.rerun()

# --- CONTROL DE PESTAÑAS DINÁMICAS ---
# Selección de herramienta en el sidebar
herramienta_seleccionada = st.sidebar.radio(
    "Sección / Herramienta:",
    ["Administración Total", "Sorteo Auto Balanced", "Ruleta Interactive", "Armado 100% a Mano"]
)

# --- PROCESAMIENTO DE CONVOCATORIA DEL DÍA ---
# Filtramos quiénes están checkeados hoy para el pool activo
jugadores_fecha_perfiles = {}
lista_espera = []

for j_name, j_perfil in st.session_state.jugadores.items():
    if j_perfil.get("fecha_activa", False):
        jugadores_fecha_perfiles[j_name] = j_perfil
        if j_perfil.get("en_espera", False):
            lista_espera.append(j_name)

# Mezclar lista de espera para prioridades justas si no hay forzado
if st.session_state.lista_espera_forzada:
    lista_espera = st.session_state.lista_espera_forzada

# --- DIVISION DE INTERFAZ CENTRAL: CONTENIDO IZQUIERDA VS CANCHA DERECHA ---
col_izquierda, col_derecha = st.columns([5.5, 4.5])

with col_izquierda:
    # -----------------------------------------------------------------
    # PESTAÑA 1: ADMINISTRACIÓN TOTAL
    # -----------------------------------------------------------------
    if herramienta_seleccionada == "Administración Total":
        st.title("📋 Gestión Global de Bricks")
        
        tab_convocatoria, tab_rostros, tab_historial = st.tabs(["📢 Convocatoria de Hoy", "👥 Modificar Roster", "🚨 Gestión Historial"])
        
        with tab_convocatoria:
            st.subheader("Selección de Jugadores Presentes para el Stream")
            if not st.session_state.jugadores:
                st.warning("El roster está vacío. Agregá jugadores en la otra pestaña.")
            else:
                st.write("Marcá a los que estén listos para jugar hoy:")
                cc1, cc2 = st.columns(2)
                nombres_ordenados = sorted(list(st.session_state.jugadores.keys()))
                mitad = len(nombres_ordenados) // 2
                
                for idx, name in enumerate(nombres_ordenados):
                    target_col = cc1 if idx < mitad else cc2
                    perfil = st.session_state.jugadores[name]
                    
                    # Layout en línea para presente + banco
                    sc1, sc2, sc3 = target_col.columns([2, 1.5, 1.5])
                    
                    is_act = sc1.checkbox(f"🏃 {name}", value=perfil.get("fecha_activa", False), key=f"act_{name}")
                    is_esp = sc2.checkbox("⏳ Banco", value=perfil.get("en_espera", False), key=f"esp_{name}", disabled=not is_act)
                    
                    if is_act != perfil.get("fecha_activa", False) or is_esp != perfil.get("en_espera", False):
                        st.session_state.jugadores[name]["fecha_activa"] = is_act
                        st.session_state.jugadores[name]["en_espera"] = is_esp if is_act else False
                        guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                        st.rerun()
                        
        with tab_rostros:
            st.subheader("Crear o Editar Perfiles")
            with st.form("form_add_player"):
                new_name = st.text_input("Nombre del Jugador (Único):").upper().strip()
                st.write("Asignar nivel de habilidad por Rol (0 a 100):")
                r_cols = st.columns(5)
                val_pg = r_cols[0].number_input("PG", 0, 100, 50)
                val_sg = r_cols[1].number_input("SG", 0, 100, 50)
                val_sf = r_cols[2].number_input("SF", 0, 100, 50)
                val_pf = r_cols[3].number_input("PF", 0, 100, 50)
                val_c = r_cols[4].number_input("C", 0, 100, 50)
                
                if st.form_submit_button("💾 Guardar / Registrar Jugador") and new_name:
                    st.session_state.jugadores[new_name] = {
                        "PG": val_pg, "SG": val_sg, "SF": val_sf, "PF": val_pf, "C": val_c,
                        "fecha_activa": False, "en_espera": False
                    }
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.success(f"¡{new_name} registrado correctamente!")
                    st.rerun()
                    
            st.write("---")
            st.write("**Roster Completo Registrado:**")
            for n in sorted(list(st.session_state.jugadores.keys())):
                p = st.session_state.jugadores[n]
                st.write(f"• **{n}** ➡️ PG: {p['PG']} | SG: {p['SG']} | SF: {p['SF']} | PF: {p['PF']} | C: {p['C']}")
                
        with tab_historial:
            st.subheader("Historial de Partidos Guardados")
            if not st.session_state.historial_partidos:
                st.info("No hay partidos archivados todavía.")
            else:
                for idx, part in enumerate(reversed(st.session_state.historial_partidos)):
                    real_idx = len(st.session_state.historial_partidos) - 1 - idx
                    hc1, hc2 = st.columns([4, 1.5])
                    hc1.write(f" Partido {real_idx+1} ({part['Codigo Usado']}): {part['Equipos']} ➡️ **{part['Resultado']}**")
                    if es_admin_stream and hc2.button("💥 BORRAR", key=f"del_h_{real_idx}"):
                        st.session_state.historial_partidos.pop(real_idx)
                        guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                        st.rerun()

    # -----------------------------------------------------------------
    # PESTAÑA 2: SORTEO AUTOMÁTICO BALANCEADO
    # -----------------------------------------------------------------
    elif herramienta_seleccionada == "Sorteo Auto Balanced":
        st.title("⚖️ Matchmaker Balanceado")
        st.write("El sistema analiza los mejores perfiles del día para armar el duelo más parejo posible.")
        
        if len(jugadores_fecha_perfiles) < 10:
            st.warning(f"Se necesitan mínimo 10 jugadores activos en Convocatoria (Hay {len(jugadores_fecha_perfiles)}).")
        else:
            if st.button("🎲 Calcular y Lanzar Match Balanceado", type="primary", use_container_width=True):
                pool_candidatos = list(jugadores_fecha_perfiles.keys())
                for esp in lista_espera:
                    if esp in pool_candidatos: pool_candidatos.remove(esp)
                    
                if len(pool_candidatos) < 10:
                    st.error("No hay suficientes jugadores fuera de la lista de espera para armar el quinteto.")
                else:
                    elegidos = random.sample(pool_candidatos, 10)
                    mejores_equipos = None
                    menor_dif = 999999
                    
                    # Algoritmo de fuerza bruta optimizado para balanceo por posición nativa
                    for _ in range(500):
                        random.shuffle(elegidos)
                        eq1_names = elegidos[:5]
                        eq2_names = elegidos[5:]
                        
                        roles_e1 = roles_totales.copy()
                        roles_e2 = roles_totales.copy()
                        random.shuffle(roles_e1)
                        random.shuffle(roles_e2)
                        
                        eq1_draft = list(zip(eq1_names, roles_e1))
                        eq2_draft = list(zip(eq2_names, roles_e2))
                        
                        s1 = sum([jugadores_fecha_perfiles[j][r] for j, r in eq1_draft])
                        s2 = sum([jugadores_fecha_perfiles[j][r] for j, r in eq2_draft])
                        dif = abs(s1 - s2)
                        
                        if dif < menor_dif:
                            menor_dif = dif
                            mejores_equipos = (eq1_draft, eq2_draft, s1, s2)
                            
                    st.session_state.draft_manual["Equipo 1"] = mejores_equipos[0]
                    st.session_state.draft_manual["Equipo 2"] = mejores_equipos[1]
                    st.session_state.draft_manual["Suma 1"] = mejores_equipos[2]
                    st.session_state.draft_manual["Suma 2"] = mejores_equipos[3]
                    st.success(f"¡Match balanceado con éxito! Diferencia de nivel estimada: {menor_dif} pts.")
                    st.rerun()

    # -----------------------------------------------------------------
    # PESTAÑA 3: RULETA INTERACTIVA
    # -----------------------------------------------------------------
    elif herramienta_seleccionada == "Ruleta Interactive":
        st.title("🎡 Ruleta de Roles por Jugador")
        st.write("Sorteá los roles al azar de los jugadores presentes que vos elijas.")
        
        pool_activos = sorted(list(jugadores_fecha_perfiles.keys()))
        if not pool_activos:
            st.warning("No hay jugadores activos hoy. Marcalos en la Convocatoria.")
        else:
            j_seleccionados = st.multiselect("Elegí exactamente 10 jugadores para el sorteo:", pool_activos)
            if len(j_seleccionados) == 10:
                if st.button("🔥 Girar Ruleta de Destino", type="primary", use_container_width=True):
                    random.shuffle(j_seleccionados)
                    e1 = j_seleccionados[:5]
                    e2 = j_seleccionados[5:]
                    
                    eq1_draft = list(zip(e1, roles_totales))
                    eq2_draft = list(zip(e2, roles_totales))
                    
                    st.session_state.draft_manual["Equipo 1"] = eq1_draft
                    st.session_state.draft_manual["Equipo 2"] = eq2_draft
                    st.session_state.draft_manual["Suma 1"] = sum([jugadores_fecha_perfiles[j][r] for j, r in eq1_draft])
                    st.session_state.draft_manual["Suma 2"] = sum([jugadores_fecha_perfiles[j][r] for j, r in eq2_draft])
                    st.success("¡Equipos dictados por la ruleta!")
                    st.rerun()

    # -----------------------------------------------------------------
    # PESTAÑA 4: ARMADO 100% A MANO (MESA DE DRAFT DIRECTA)
    # -----------------------------------------------------------------
    elif herramienta_seleccionada == "Armado 100% a Mano":
        st.title("✍️ Editor de Quintetos Manual")
        st.write("Armá las escuadras libremente seleccionando el roster global.")
        
        todos_los_jugadores = sorted(list(st.session_state.jugadores.keys()))
        
        m_col1, m_col2 = st.columns(2)
        
        with m_col1:
            st.markdown("### 🔵 Selección Equipo 1")
            j1_1 = st.selectbox("PG - Eq 1", ["--"] + todos_los_jugadores, key="s_1_1")
            j1_2 = st.selectbox("SG - Eq 1", ["--"] + todos_los_jugadores, key="s_1_2")
            j1_3 = st.selectbox("SF - Eq 1", ["--"] + todos_los_jugadores, key="s_1_3")
            j1_4 = st.selectbox("PF - Eq 1", ["--"] + todos_los_jugadores, key="s_1_4")
            j1_5 = st.selectbox("C - Eq 1", ["--"] + todos_los_jugadores, key="s_1_5")
            
        with m_col2:
            st.markdown("### 🔴 Selección Equipo 2")
            j2_1 = st.selectbox("PG - Eq 2", ["--"] + todos_los_jugadores, key="s_2_1")
            j2_2 = st.selectbox("SG - Eq 2", ["--"] + todos_los_jugadores, key="s_2_2")
            j2_3 = st.selectbox("SF - Eq 2", ["--"] + todos_los_jugadores, key="s_2_3")
            j2_4 = st.selectbox("PF - Eq 2", ["--"] + todos_los_jugadores, key="s_2_4")
            j2_5 = st.selectbox("C - Eq 2", ["--"] + todos_los_jugadores, key="s_2_5")
            
        st.write("")
        if st.button("💾 Aplicar Plantilla Manual a la Cancha", type="primary", use_container_width=True):
            e1_build = []
            if j1_1 != "--": e1_build.append((j1_1, "PG"))
            if j1_2 != "--": e1_build.append((j1_2, "SG"))
            if j1_3 != "--": e1_build.append((j1_3, "SF"))
            if j1_4 != "--": e1_build.append((j1_4, "PF"))
            if j1_5 != "--": e1_build.append((j1_5, "C"))
            
            e2_build = []
            if j2_1 != "--": e2_build.append((j2_1, "PG"))
            if j2_2 != "--": e2_build.append((j2_2, "SG"))
            if j2_3 != "--": e2_build.append((j2_3, "SF"))
            if j2_4 != "--": e2_build.append((j2_4, "PF"))
            if j2_5 != "--": e2_build.append((j2_5, "C"))
            
            st.session_state.draft_manual["Equipo 1"] = e1_build
            st.session_state.draft_manual["Equipo 2"] = e2_build
            
            # Sumas seguras basadas en roster total
            st.session_state.draft_manual["Suma 1"] = sum([st.session_state.jugadores[j][r] for j, r in e1_build])
            st.session_state.draft_manual["Suma 2"] = sum([st.session_state.jugadores[j][r] for j, r in e2_build])
            st.success("¡Pizarra actualizada en el panel de control!")
            st.rerun()

    st.write("")
    if st.button("❌ Reiniciar Mesa Completa", use_container_width=True):
        st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
        st.rerun()

# =====================================================================
# BLOQUE COMÚN REUTILIZABLE: RENDERIZADO DE CANCHA (COLUMNA DERECHA)
# =====================================================================
with col_derecha:
    st.header("🔥 Control")
    
    # Renderizado visual nativo en Streamlit
    with st.container(border=True):
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            if ver_puntos:
                st.markdown(f"### 🔵 Eq 1 ({st.session_state.draft_manual['Suma 1']})")
            else:
                st.markdown("### 🔵 Eq 1")
            for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 1"]):
                pts = st.session_state.jugadores[jug].get(rol, 0)
                c_txt, c_x = st.columns([3.5, 1.2])
                c_txt.write(f"• **{jug}** ({rol})")
                if es_admin_stream and c_x.button("❌", key=f"k1_{idx}"):
                    st.session_state.draft_manual["Suma 1"] -= pts
                    st.session_state.draft_manual["Equipo 1"].pop(idx)
                    st.rerun()
                    
        with sub_col2:
            if ver_puntos:
                st.markdown(f"### 🔴 Eq 2 ({st.session_state.draft_manual['Suma 2']})")
            else:
                st.markdown("### 🔴 Eq 2")
            for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 2"]):
                pts = st.session_state.jugadores[jug].get(rol, 0)
                c_txt, c_x = st.columns([3.5, 1.2])
                c_txt.write(f"• **{jug}** ({rol})")
                if es_admin_stream and c_x.button("❌", key=f"k2_{idx}"):
                    st.session_state.draft_manual["Suma 2"] -= pts
                    st.session_state.draft_manual["Equipo 2"].pop(idx)
                    st.rerun()

    st.markdown(f'🔑 **Matchmaking:** `{codigo_actual}`', unsafe_allow_html=True)
    st.write("")
    
    # -----------------------------------------------------------------
    # MOTOR DE GENERACIÓN DE IMAGEN NATIVA (PILLOW)
    # -----------------------------------------------------------------
    def generar_imagen_cancha():
        ancho, alto = 600, 400
        img = Image.new("RGB", (ancho, alto), "#0e1117")
        canvas = ImageDraw.Draw(img)
        
        try:
            fuente_titulo = ImageFont.truetype("arial.ttf", 24)
            fuente_sub = ImageFont.truetype("arial.ttf", 18)
            fuente_texto = ImageFont.truetype("arial.ttf", 16)
        except:
            fuente_titulo = fuente_sub = fuente_texto = ImageFont.load_default()
            
        canvas.rectangle([10, 10, ancho - 10, alto - 10], outline="#31333F", width=3)
        canvas.text((30, 25), "🏀 DRAFT A LA CARTA", fill="#ffffff", font=fuente_titulo)
        canvas.line([(30, 60), (ancho - 30, 60)], fill="#31333F", width=2)
        
        canvas.text((40, 80), "🔵 EQUIPO 1", fill="#1f77b4", font=fuente_sub)
        y_pos = 115
        for jug, rol in st.session_state.draft_manual["Equipo 1"]:
            canvas.text((50, y_pos), f"• {jug} ({rol})", fill="#e2e8f0", font=fuente_texto)
            y_pos += 30
        if not st.session_state.draft_manual["Equipo 1"]:
            canvas.text((50, 115), "(Sin jugadores)", fill="#64748b", font=fuente_texto)
            
        canvas.text((320, 80), "🔴 EQUIPO 2", fill="#ff4b4b", font=fuente_sub)
        y_pos = 115
        for jug, rol in st.session_state.draft_manual["Equipo 2"]:
            canvas.text((330, y_pos), f"• {jug} ({rol})", fill="#e2e8f0", font=fuente_texto)
            y_pos += 30
        if not st.session_state.draft_manual["Equipo 2"]:
            canvas.text((330, 115), "(Sin jugadores)", fill="#64748b", font=fuente_texto)
            
        canvas.line([(30, 330), (ancho - 30, 330)], fill="#31333F", width=2)
        canvas.text((30, 350), f"🔑 MATCHMAKING CODE:  {codigo_actual}", fill="#2ecc71", font=fuente_sub)
        
        ruta_temp = "cancha_temp.png"
        img.save(ruta_temp)
        return ruta_temp

    try:
        archivo_foto = generar_imagen_cancha()
        with open(archivo_foto, "rb") as file:
            btn_descarga = st.download_button(
                label="📸 CAPTURAR CANCHA (FOTO PNG)",
                data=file,
                file_name=f"Cancha_Match_{codigo_actual}.png",
                mime="image/png",
                use_container_width=True,
                type="primary"
            )
    except Exception as e:
        st.error(f"Error generando imagen: {e}")

    st.write("")

    if es_admin_stream:
        st.markdown("**📝 Marcador Final:**")
        mc1, mc2, mc3 = st.columns([1.5, 1.5, 2])
        res_eq1 = mc1.number_input("🔵 Eq 1:", min_value=0, value=0, key="scr_1")
        res_eq2 = mc2.number_input("🔴 Eq 2:", min_value=0, value=0, key="scr_2")
        
        if mc3.button("💾 archivar", use_container_width=True):
            nombres_e1 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 1"]])
            nombres_e2 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 2"]])
            
            st.session_state.historial_partidos.append({
                "Equipos": f"🔵 ({nombres_e1}) VS 🔴 ({nombres_e2})",
                "Resultado": f"{res_eq1} - {res_eq2}",
                "Codigo Usado": codigo_actual
            })
            guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
            
            # Avanza al siguiente código de la lista para el próximo partido
            st.session_state.contador_codigo_dia += 1
            
            if res_eq1 > res_eq2:
                equipo_a_reemplazar = "Equipo 2"
                equipo_fijo = "Equipo 1"
            elif res_eq2 > res_eq1:
                equipo_a_reemplazar = "Equipo 1"
                equipo_fijo = "Equipo 2"
            else:
                equipo_a_reemplazar = "Equipo 2"
                equipo_fijo = "Equipo 1"
            
            roles_perdedores = [j[1] for j in st.session_state.draft_manual[equipo_a_reemplazar]]
            if not roles_perdedores: roles_perdedores = roles_totales.copy()
            
            nuevo_equipo_reemplazo = []
            banco_simulado = lista_espera.copy()
            
            for r_liberado in roles_perdedores:
                # Busca primero en perfiles del día, si no está (manual) cae en el roster global seguro
                candidato_banco = next((j for j in banco_simulado if r_liberado in jugadores_fecha_perfiles.get(j, st.session_state.jugadores.get(j, {}))), None)
                if candidato_banco:
                    nuevo_equipo_reemplazo.append((candidato_banco, r_liberado))
                    banco_simulado.remove(candidato_banco)
                else:
                    if banco_simulado:
                        candidato_banco = banco_simulado[0]
                        nuevo_equipo_reemplazo.append((candidato_banco, r_liberado))
                        banco_simulado.remove(candidato_banco)
            
            # Cálculo de sumas protegido con .get() alternativo para evitar KeyErrors
            suma_fijo = sum([jugadores_fecha_perfiles.get(j[0], st.session_state.jugadores.get(j[0], {})).get(j[1], 0) for j in st.session_state.draft_manual[equipo_fijo]])
            suma_reemplazo = sum([jugadores_fecha_perfiles.get(j[0], st.session_state.jugadores.get(j[0], {})).get(j[1], 0) for j in nuevo_equipo_reemplazo])
            
            st.session_state.draft_manual[equipo_a_reemplazar] = nuevo_equipo_reemplazo
            if equipo_fijo == "Equipo 1":
                st.session_state.draft_manual["Suma 1"] = suma_fijo
                st.session_state.draft_manual["Suma 2"] = suma_reemplazo
            else:
                st.session_state.draft_manual["Suma 1"] = suma_reemplazo
                st.session_state.draft_manual["Suma 2"] = suma_fijo
            
            st.session_state.lista_espera_forzada = [] 
            st.success("¡Partido archivado y rotación lista!")
            st.rerun()

        if st.session_state.historial_partidos:
            with st.expander("🩹 Corregir score anterior"):
                ec1, ec2, ec3 = st.columns(3)
                er1 = ec1.number_input("Eq 1:", min_value=0, value=0, key="err_1")
                er2 = ec2.number_input("Eq 2:", min_value=0, value=0, key="err_2")
                if ec3.button("Modificar", use_container_width=True):
                    st.session_state.historial_partidos[-1]["Resultado"] = f"{er1} - {er2}"
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.rerun()
