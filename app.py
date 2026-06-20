import streamlit as st
import random
import time

# Configuración de la página web
st.set_page_config(page_title="Draft a la carta", layout="wide")

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD (Cambiá la contraseña acá si querés)
# =====================================================================
PASSWORD_ADMIN = "bricks2026"

# --- MEMORIA DEL PROGRAMA (PERSISTENTE) ---
# Arranca completamente vacío para cargar desde cero
if "jugadores" not in st.session_state:
    st.session_state.jugadores = {}

if "draft_manual" not in st.session_state:
    st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}

if "historial_partidos" not in st.session_state:
    st.session_state.historial_partidos = []

# --- BARRA LATERAL: LOGIN Y NAVEGACIÓN ---
st.sidebar.title("🍔 Bricks a la carta")
st.sidebar.subheader("🔒 Acceso Organizador")

# Campo de contraseña
password_ingresada = st.sidebar.text_input("Contraseña:", type="password")
es_admin = (password_ingresada == PASSWORD_ADMIN)

# Control de revelación de puntos (Camuflado para que no sospechen en stream)
ver_puntos = False
if es_admin:
    st.sidebar.success("🔓 Permisos de Admin Activos")
    ver_puntos = st.sidebar.toggle("🔧 Optimizar renderizado de streaming (H.264)", value=False)
else:
    if password_ingresada:
        st.sidebar.error("❌ Contraseña Incorrecta")
    st.sidebar.info("👁️ Modo Espectador (Solo Lectura)")

st.sidebar.write("---")

# Filtro de opciones de navegación según si es admin o no
opciones_menu = ["🏀 Mesa de Draft"]
if es_admin:
    opciones_menu.append("📋 Roster y Gestión de Fichas (Privado)")

seccion = st.sidebar.radio("Ir a la ventana:", opciones_menu)

# =====================================================================
# VENTANA: ROSTER Y GESTIÓN DE FICHAS (SOLO ACCESIBLE SI ES ADMIN)
# =====================================================================
if seccion == "📋 Roster y Gestión de Fichas (Privado)":
    st.title("📋 Roster Oficial — Draft a la carta")
    st.subheader("Administración de fichas técnicas de jugadores")
    
    col_carga, col_lista = st.columns([1, 2.5])
    
    with col_carga:
        st.header("👤 Añadir / Modificar")
        nombre = st.text_input("Nombre del Jugador:").strip().upper()
        
        st.write("Puntajes por posición:")
        pg = st.number_input("PG (Base)", 0, 99, 0)
        sg = st.number_input("SG (Escolta)", 0, 99, 0)
        sf = st.number_input("SF (Alero)", 0, 99, 0)
        pf = st.number_input("PF (Ala-Pívot)", 0, 99, 0)
        c = st.number_input("C (Pívot)", 0, 99, 0)
        
        if st.button("💾 Guardar en Base de Datos", use_container_width=True):
            if nombre:
                perfil = {pos: val for pos, val in [("PG", pg), ("SG", sg), ("SF", sf), ("PF", pf), ("C", c)] if val > 0}
                if perfil:
                    st.session_state.jugadores[nombre] = perfil
                    st.success(f"¡{nombre} actualizado exitosamente!")
                    st.rerun()
                else:
                    st.error("Ponle al menos una posición válida.")
            else:
                st.error("Escribe un nombre válido.")
                
    with col_lista:
        st.header("🪪 Carnets Registrados")
        if not st.session_state.jugadores:
            st.info("No hay jugadores cargados en el roster todavía. ¡Agrega el primero a la izquierda!")
        else:
            columnas_roster = st.columns(3)
            for idx, (jug, posiciones) in enumerate(sorted(st.session_state.jugadores.items())):
                col_actual = columnas_roster[idx % 3]
                with col_actual:
                    with st.container(border=True):
                        st.markdown(f"### ⛹️‍♂️ {jug}")
                        texto_pos = ""
                        for pos, pts in posiciones.items():
                            texto_pos += f"**{pos}:** {pts} pts  \n"
                        st.write(texto_pos)
                        
                        if st.button("🗑️ Eliminar", key=f"del_{jug}"):
                            del st.session_state.jugadores[jug]
                            st.rerun()

# =====================================================================
# VENTANA: PANEL DE CONTROL, CONVOCATORIA Y RULETA
# =====================================================================
else:
    st.title("🏀 Draft a la carta")
    st.subheader("Convocatoria diaria, sorteos y streaming oficial")

    # 1. Convocatoria del Día
    st.header("🎲 Convocatoria del Día")
    
    if not st.session_state.jugadores:
        st.warning("⚠️ Primero debes iniciar sesión como Admin e ir a la sección '📋 Roster' para cargar a tus jugadores.")
        presentes = []
    else:
        presentes = []
        columnas_check = st.columns(4)
        for i, jug in enumerate(sorted(st.session_state.jugadores.keys())):
            with columnas_check[i % 4]:
                if es_admin:
                    if st.checkbox(f"✔️ {jug}", key=f"p_{jug}"):
                        presentes.append(jug)
                else:
                    esta_tildado = st.checkbox(f"✔️ {jug}", key=f"p_{jug}", disabled=True)
                    if esta_tildado:
                        presentes.append(jug)
                    
        st.write(f"**Conectados hoy:** {len(presentes)} jugadores.")
    st.write("---")
    
    # --- AJUSTE DINÁMICO DE POSICIONES PARA LA FECHA ---
    jugadores_fecha_perfiles = {}
    
    if presentes:
        st.subheader("🛠️ Ajuste de Roles para la Fecha (Exclusiones de hoy)")
        st.write("Si alguien no quiere o no puede jugar en alguna posición hoy, destildala acá abajo:")
        
        col_roles_dinamicos = st.columns(3)
        for idx, jug in enumerate(sorted(presentes)):
            col_jug = col_roles_dinamicos[idx % 3]
            with col_jug:
                with st.container(border=True):
                    st.markdown(f"**⛹️‍♂️ {jug}**")
                    pos_originales = list(st.session_state.jugadores[jug].keys())
                    
                    roles_activos_hoy = []
                    for pos in pos_originales:
                        if es_admin:
                            if st.checkbox(f"Habilitar {pos}", value=True, key=f"rol_{jug}_{pos}"):
                                roles_activos_hoy.append(pos)
                        else:
                            val_espectador = st.checkbox(f"Habilitar {pos}", value=True, key=f"rol_{jug}_{pos}", disabled=True)
                            if val_espectador:
                                roles_activos_hoy.append(pos)
                    
                    if roles_activos_hoy:
                        jugadores_fecha_perfiles[jug] = {p: st.session_state.jugadores[jug][p] for p in roles_activos_hoy}
                    else:
                        jugadores_fecha_perfiles[jug] = st.session_state.jugadores[jug]
        st.write("---")
    
    roles_totales = ["PG", "SG", "SF", "PF", "C"]
    ya_drafteados = [j[0] for j in st.session_state.draft_manual["Equipo 1"]] + [j[0] for j in st.session_state.draft_manual["Equipo 2"]]
    libres_hoy = [j for j in presentes if j not in ya_drafteados]
    
    pos_cubiertas_eq1 = [j[1] for j in st.session_state.draft_manual["Equipo 1"]]
    pos_cubiertas_eq2 = [j[1] for j in st.session_state.draft_manual["Equipo 2"]]

    if es_admin:
        pestana1, pestana2 = st.tabs(["🎯 Sorteo Automático Completo", "🎡 Ruleta y Selección Manual"])
        
        # --- PESTAÑA 1: AUTOMÁTICO COMPLETO ---
        with pestana1:
            if st.button("🚀 Lanzar Sorteo Automático Balanced", type="primary", use_container_width=True):
                if len(presentes) < 10:
                    st.warning("Faltan convocados. Se necesitan mínimo 10 jugadores para balancear los equipos.")
                else:
                    pool = presentes.copy()
                    mejor_comb = None
                    menor_dif = 9999
                    
                    for _ in range(3000):
                        random.shuffle(pool)
                        eq1, eq2 = [], []
                        s1, s2 = 0, 0
                        disponibles = pool.copy()
                        error_posicion = False
                        
                        for r in roles_totales:
                            elegido = next((j for j in disponibles if r in jugadores_fecha_perfiles[j]), None)
                            if elegido:
                                eq1.append((elegido, r))
                                s1 += jugadores_fecha_perfiles[elegido][r]
                                disponibles.remove(elegido)
                            else:
                                error_posicion = True
                                break
                        
                        if error_posicion:
                            continue
                        
                        for i, r in enumerate(roles_totales):
                            elegido = disponibles[i]
                            if r in jugadores_fecha_perfiles[elegido]:
                                eq2.append((elegido, r))
                                s2 += jugadores_fecha_perfiles[elegido][r]
                            else:
                                error_posicion = True
                                break
                                
                        if not error_posicion and len(eq1) == 5 and len(eq2) == 5:
                            if abs(s1 - s2) < menor_dif:
                                menor_dif = abs(s1 - s2)
                                mejor_comb = (eq1, eq2, s1, s2)
                                
                    if mejor_comb:
                        st.session_state.draft_manual["Equipo 1"] = mejor_comb[0]
                        st.session_state.draft_manual["Equipo 2"] = mejor_comb[1]
                        st.session_state.draft_manual["Suma 1"] = mejor_comb[2]
                        st.session_state.draft_manual["Suma 2"] = mejor_comb[3]
                        st.success("¡Equipos automáticos generados!")
                    else:
                        st.error("No hay una combinación perfecta con las restricciones actuales.")

        # --- PESTAÑA 2: RULETA Y MANUAL ---
        with pestana2:
            st.write("### 1. Sorteo por Posición Específica")
            posicion_a_sortear = st.selectbox("Elegí qué posición vas a sortear en la ruleta:", roles_totales)
            
            def es_seguro_elegir(jugador_test, pos_test):
                libres_simulados = [j for j in libres_hoy if j != jugador_test]
                faltantes_eq1 = [r for r in roles_totales if r not in pos_cubiertas_eq1]
                faltantes_eq2 = [r for r in roles_totales if r not in pos_cubiertas_eq2]
                
                if len(st.session_state.draft_manual["Equipo 1"]) <= len(st.session_state.draft_manual["Equipo 2"]):
                    if pos_test in faltantes_eq1: faltantes_eq1.remove(pos_test)
                else:
                    if pos_test in faltantes_eq2: faltantes_eq2.remove(pos_test)
                
                roles_que_faltan_llenar = faltantes_eq1 + faltantes_eq2
                if not roles_que_faltan_llenar:
                    return True
                    
                for _ in range(500):
                    random.shuffle(libres_simulados)
                    temp_libres = libres_simulados.copy()
                    exito = True
                    for r_faltante in roles_que_faltan_llenar:
                        apto = next((j for j in temp_libres if r_faltante in jugadores_fecha_perfiles[j]), None)
                        if apto:
                            temp_libres.remove(apto)
                        else:
                            exito = False
                            break
                    if exito:
                        return True
                return False

            candidatos = []
            for j in libres_hoy:
                if posicion_a_sortear in jugadores_fecha_perfiles[j] and jugadores_fecha_perfiles[j][posicion_a_sortear] > 0:
                    if es_seguro_elegir(j, posicion_a_sortear):
                        candidatos.append(j)

            if candidatos:
                st.markdown(f"**Disponibles para {posicion_a_sortear} ahora:** {', '.join(candidatos)}")
            else:
                st.markdown(f"⚠️ *No quedan jugadores viables habilitados para ocupar el rol de {posicion_a_sortear}.*")
            
            if st.button("🎡 ¡Girar Ruleta para esta posición!", use_container_width=True):
                if not candidatos:
                    st.error("No hay candidatos viables.")
                else:
                    contenedor_ruleta = st.empty()
                    for _ in range(10):
                        nombre_ruleta = random.choice(candidatos)
                        contenedor_ruleta.markdown(f"<h2 style='text-align: center; color: #FF4B4B;'>🎡 {nombre_ruleta} 🎡</h2>", unsafe_allow_html=True)
                        time.sleep(0.12)
                    
                    elegido_final = random.choice(candidatos)
                    contenedor_ruleta.markdown(f"<h1 style='text-align: center; color: #2ecc71;'>🎯 {elegido_final} 🎯</h1>", unsafe_allow_html=True)
                    
                    pts_jugador = jugadores_fecha_perfiles[elegido_final][posicion_a_sortear]
                    if len(st.session_state.draft_manual["Equipo 1"]) <= len(st.session_state.draft_manual["Equipo 2"]):
                        st.session_state.draft_manual["Equipo 1"].append((elegido_final, posicion_a_sortear))
                        st.session_state.draft_manual["Suma 1"] += pts_jugador
                    else:
                        st.session_state.draft_manual["Equipo 2"].append((elegido_final, posicion_a_sortear))
                        st.session_state.draft_manual["Suma 2"] += pts_jugador
                    st.rerun()
                        
            st.write("---")
            st.write("### 2. Agregar Jugador a Mano")
            
            if libres_hoy:
                col_man1, col_man2, col_man3 = st.columns(3)
                with col_man1:
                    jugador_manual = st.selectbox("Elegir Jugador:", libres_hoy)
                with col_man2:
                    roles_validos = [pos for pos, val in jugadores_fecha_perfiles[jugador_manual].items() if val > 0]
                    rol_manual_raw = st.selectbox("Asignar como posición:", roles_validos)
                    rol_manual = rol_manual_raw.split(" ")[0] if rol_manual_raw else None
                with col_man3:
                    equipo_destino = st.selectbox("Asignar al:", ["Equipo 1", "Equipo 2"])
                    
                if st.button("➕ Meter al equipo a mano", use_container_width=True):
                    if jugador_manual and rol_manual:
                        pts_jugador = jugadores_fecha_perfiles[jugador_manual][rol_manual]
                        if equipo_destino == "Equipo 1":
                            st.session_state.draft_manual["Equipo 1"].append((jugador_manual, rol_manual))
                            st.session_state.draft_manual["Suma 1"] += pts_jugador
                        else:
                            st.session_state.draft_manual["Equipo 2"].append((jugador_manual, rol_manual))
                            st.session_state.draft_manual["Suma 2"] += pts_jugador
                        st.rerun()
            else:
                st.info("Todos los presentes están asignados.")

            if st.button("❌ Reiniciar Tablas de Equipos", type="secondary"):
                st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
                st.rerun()
    else:
        st.warning("🔒 Las herramientas de sorteo, ruleta y cambios manuales están bloqueadas en modo espectador.")

    # --- PANTALLA DE RESULTADOS DEL DRAFT ---
    if st.session_state.draft_manual["Equipo 1"] or st.session_state.draft_manual["Equipo 2"]:
        st.write("---")
        st.header("🔥 CONTROL DE LA CANCHA")
        
        col_eq1, col_eq2 = st.columns(2)
        
        with col_eq1:
            sub_e1 = f"🔵 EQUIPO 1 (Global: {st.session_state.draft_manual['Suma 1']})" if ver_puntos else "🔵 EQUIPO 1"
            st.subheader(sub_e1)
            
            for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 1"]):
                pts = st.session_state.jugadores[jug].get(rol, 0)
                if es_admin:
                    c_inf, c_btn = st.columns([4, 1])
                    txt_jugador = f"🏃‍♂️ **{jug}** - {rol} ({pts} pts)" if ver_puntos else f"🏃‍♂️ **{jug}** - {rol}"
                    c_inf.write(txt_jugador)
                    if c_btn.button("❌", key=f"kick_1_{jug}_{idx}"):
                        st.session_state.draft_manual["Suma 1"] -= pts
                        st.session_state.draft_manual["Equipo 1"].pop(idx)
                        st.rerun()
                else:
                    st.write(f"🏃‍♂️ **{jug}** - {rol}")
                
        with col_eq2:
            sub_e2 = f"🔴 EQUIPO 2 (Global: {st.session_state.draft_manual['Suma 2']})" if ver_puntos else "🔴 EQUIPO 2"
            st.subheader(sub_e2)
            
            for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 2"]):
                pts = st.session_state.jugadores[jug].get(rol, 0)
                if es_admin:
                    c_inf, c_btn = st.columns([4, 1])
                    txt_jugador = f"🏃‍♂️ **{jug}** - {rol} ({pts} pts)" if ver_puntos else f"🏃‍♂️ **{jug}** - {rol}"
                    c_inf.write(txt_jugador)
                    if c_btn.button("❌", key=f"kick_2_{jug}_{idx}"):
                        st.session_state.draft_manual["Suma 2"] -= pts
                        st.session_state.draft_manual["Equipo 2"].pop(idx)
                        st.rerun()
                else:
                    st.write(f"🏃‍♂️ **{jug}** - {rol}")
                
        # --- REGISTRO DEL MARCADOR ---
        st.write("---")
        st.subheader("📝 Registrar Resultado Final")
        
        if es_admin:
            marcador_col1, marcador_col2 = st.columns(2)
            with marcador_col1:
                res_eq1 = st.number_input("Puntos Equipo 1:", min_value=0, value=0, key="r_1")
            with marcador_col2:
                res_eq2 = st.number_input("Puntos Equipo 2:", min_value=0, value=0, key="r_2")
                
            if st.button("💾 Guardar Marcador", use_container_width=True):
                nombres_e1 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 1"]])
                nombres_e2 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 2"]])
                
                registro = {
                    "Equipos": f"🔵 ({nombres_e1}) VS 🔴 ({nombres_e2})",
                    "Resultado": f"{res_eq1} - {res_eq2}"
                }
                st.session_state.historial_partidos.append(registro)
                st.success("¡Partido archivado!")
        else:
            st.info("🏃‍♂️ El partido está en juego. Los resultados solo pueden ser cargados por el organizador.")
            
        if st.session_state.historial_partidos:
            st.write("### 📜 Historial de Resultados")
            for idx, part in enumerate(st.session_state.historial_partidos):
                st.info(f"**Partido #{idx+1}:** {part['Equipos']} ➔ **Marcador Final: {part['Resultado']}**")