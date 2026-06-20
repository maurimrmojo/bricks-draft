import streamlit as st
import streamlit.components.v1 as components
import random
import time
import json
import os

# Configuración de la página web
st.set_page_config(page_title="Draft a la carta", layout="wide")

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD (DOBLE CLAVE)
# =====================================================================
PASSWORD_STREAM = "bricks2026"        # Clave para operar el stream y la mesa
PASSWORD_MAESTRA = "bricks2026admin"   # Clave máxima para Roster y Borrados
ARCHIVO_BD = "datos_draft.json"

# --- FUNCIONES PARA LEER Y GUARDAR EN EL ALMACENAMIENTO PERSISTENTE ---
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

# --- CARGA INICIAL DE DATOS ---
datos_guardados = cargar_datos_globales()

if "jugadores" not in st.session_state:
    st.session_state.jugadores = datos_guardados["jugadores"]

if "historial_partidos" not in st.session_state:
    st.session_state.historial_partidos = datos_guardados["historial_partidos"]

if "draft_manual" not in st.session_state:
    st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}

# --- BARRA LATERAL: LOGIN Y NAVEGACIÓN ---
st.sidebar.title("🍔 Bricks a la carta")
st.sidebar.subheader("🔒 Acceso de Seguridad")

password_ingresada = st.sidebar.text_input("Contraseña:", type="password")

# Validation de jerarquías
es_admin_stream = (password_ingresada == PASSWORD_STREAM or password_ingresada == PASSWORD_MAESTRA)
es_super_admin = (password_ingresada == PASSWORD_MAESTRA)

ver_puntos = False
if es_super_admin:
    st.sidebar.success("👑 Permisos de SUPER-ADMIN Activos")
    ver_puntos = st.sidebar.toggle("🔧 Optimizar renderizado de streaming (H.264)", value=False)
elif es_admin_stream:
    st.sidebar.success("🔓 Permisos de Streamer Activos")
    ver_puntos = st.sidebar.toggle("🔧 Optimizar renderizado de streaming (H.264)", value=False)
else:
    if password_ingresada:
        st.sidebar.error("❌ Contraseña Incorrecta")
    st.sidebar.info("👁️ Modo Espectador (Solo Lectura)")

st.sidebar.write("---")

if st.sidebar.button("🔄 Sincronizar Datos (F5 Manual)", use_container_width=True):
    st.cache_data.clear()
    datos_actualizados = cargar_datos_globales()
    st.session_state.jugadores = datos_actualizados["jugadores"]
    st.session_state.historial_partidos = datos_actualizados["historial_partidos"]
    st.rerun()

# Menú dinámico según el nivel de seguridad
opciones_menu = ["🏀 Mesa de Draft"]
if es_super_admin:
    opciones_menu.append("📋 Roster y Gestión de Fichas (Privado)")

seccion = st.sidebar.radio("Ir a la ventana:", opciones_menu)

# =====================================================================
# VENTANA: ROSTER Y GESTIÓN DE FICHAS (SÓLO SUPER-ADMIN)
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
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.success(f"¡{nombre} guardado permanentemente!")
                    st.rerun()
                else:
                    st.error("Ponle al menos una posición válida.")
            else:
                st.error("Escribe un nombre válido.")
                
        # --- SECCIÓN ULTRA PROTEGIDA DE CONTROL DE HISTORIAL ---
        st.write("---")
        st.header("⚠️ Control de Historial")
        if st.session_state.historial_partidos:
            st.write(f"Partidos registrados: {len(st.session_state.historial_partidos)}")
            if st.button("🚨 Eliminar Último Partido Cargado", type="secondary", use_container_width=True):
                partido_borrado = st.session_state.historial_partidos.pop()
                guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                st.warning("Se eliminó el último registro correctamente.")
                st.rerun()
        else:
            st.info("No hay partidos en el historial para borrar.")
                
    with col_lista:
        st.header("🪪 Carnets Registrados")
        if not st.session_state.jugadores:
            st.info("No hay jugadores cargados en el roster todavía.")
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
                            guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                            st.rerun()

# =====================================================================
# VENTANA: PANEL DE CONTROL, CONVOCATORIA Y RULETA VISUAL
# =====================================================================
else:
    st.title("🏀 Draft a la carta")
    st.subheader("Convocatoria diaria, sorteos y streaming oficial")

    st.header("🎲 Convocatoria del Día")
    
    if not st.session_state.jugadores:
        st.warning("⚠️ Primero debes iniciar sesión con la clave Maestra e ir a '📋 Roster' para cargar jugadores.")
        presentes = []
    else:
        presentes = []
        columnas_check = st.columns(4)
        for i, jug in enumerate(sorted(st.session_state.jugadores.keys())):
            with columnas_check[i % 4]:
                if es_admin_stream:
                    if st.checkbox(f"✔️ {jug}", key=f"p_{jug}"):
                        presentes.append(jug)
                else:
                    esta_tildado = st.checkbox(f"✔️ {jug}", key=f"p_{jug}", disabled=True)
                    if esta_tildado:
                        presentes.append(jug)
                    
        st.write(f"**Conectados hoy:** {len(presentes)} jugadores.")
    st.write("---")
    
    jugadores_fecha_perfiles = {}
    if presentes:
        st.subheader("🛠️ Ajuste de Roles para la Fecha (Exclusiones de hoy)")
        col_roles_dinamicos = st.columns(3)
        for idx, jug in enumerate(sorted(presentes)):
            col_jug = col_roles_dinamicos[idx % 3]
            with col_jug:
                with st.container(border=True):
                    st.markdown(f"**⛹️‍♂️ {jug}**")
                    pos_originales = list(st.session_state.jugadores[jug].keys())
                    
                    roles_activos_hoy = []
                    for pos in pos_originales:
                        if es_admin_stream:
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

    if es_admin_stream:
        pestana1, pestana2 = st.tabs(["🎯 Sorteo Automático Completo", "🎡 Ruleta Interactiva y Manual"])
        
        with pestana1:
            if st.button("🚀 Lanzar Sorteo Automático Balanced", type="primary", use_container_width=True):
                if len(presentes) < 10:
                    st.warning("Faltan convocados. Se necesitan mínimo 10 jugadores.")
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

        with pestana2:
            st.write("### 1. Sorteo por Ruleta Gráfica 🎡")
            posicion_a_sortear = st.selectbox("Elegí qué posición vas a sortear hoy:", roles_totales)
            
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
                st.markdown(f"**Disponibles en el bombo:** {', '.join(candidatos)}")
                
                if "ganador_ruleta" not in st.session_state:
                    st.session_state.ganador_ruleta = None

                colores_gajos = ["#FF4B4B", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#e377c2", "#bcbd22"]
                lista_colores = [colores_gajos[i % len(colores_gajos)] for i in range(len(candidatos))]
                
                json_candidatos = json.dumps(candidatos)
                json_colores = json.dumps(lista_colores)
                
                if st.button("🔮 Preparar y Sincronizar Ruleta", use_container_width=True):
                    st.session_state.ganador_ruleta = random.choice(candidatos)
                
                ganador = st.session_state.ganador_ruleta if st.session_state.ganador_ruleta in candidatos else candidatos[0]
                idx_ganador = candidatos.index(ganador)

                html_ruleta = f"""
                <div style="text-align: center; font-family: sans-serif; background-color: #0e1117; color: white; padding: 15px; border-radius: 10px;">
                    <div style="position: relative; display: inline-block;">
                        <div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent; border-top: 25px solid #FF4B4B; z-index: 10;"></div>
                        <canvas id="canvasRuleta" width="380" height="380" style="border: 4px solid #31333F; border-radius: 50%; box-shadow: 0 0 15px rgba(0,0,0,0.5);"></canvas>
                    </div>
                    <br><br>
                    <button id="btnGirar" style="background-color: #FF4B4B; color: white; border: none; padding: 12px 35px; font-size: 18px; font-weight: bold; border-radius: 5px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">🎡 ¡GIRAR EN STREAM! 🎡</button>
                    <h2 id="txtResultado" style="margin-top: 15px; color: #0e1117; min-height: 35px; transition: color 0.5s;">.</h2>
                </div>

                <script>
                    const candidatos = {json_candidatos};
                    const colores = {json_colores};
                    const idxGanador = {idx_ganador};
                    
                    const canvas = document.getElementById("canvasRuleta");
                    const ctx = canvas.getContext("2d");
                    const numGajos = candidatos.length;
                    const angularGajo = (2 * Math.PI) / numGajos;
                    let anguloActual = 0;
                    
                    function dibujarRuleta() {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        const centro = canvas.width / 2;
                        
                        for (let i = 0; i < numGajos; i++) {{
                            const anguloInicio = anguloActual + (i * angularGajo);
                            const anguloFin = anguloInicio + angularGajo;
                            
                            ctx.beginPath();
                            ctx.moveTo(centro, centro);
                            ctx.arc(centro, centro, centro - 5, anguloInicio, anguloFin);
                            ctx.fillStyle = colores[i];
                            ctx.fill();
                            ctx.lineWidth = 2;
                            ctx.strokeStyle = "#0e1117";
                            ctx.stroke();
                            
                            ctx.save();
                            ctx.translate(centro, centro);
                            ctx.rotate(anguloInicio + angularGajo / 2);
                            ctx.textAlign = "right";
                            ctx.fillStyle = "white";
                            ctx.font = "bold 14px sans-serif";
                            ctx.fillText(candidatos[i], centro - 20, 5);
                            ctx.restore();
                        }}
                        
                        ctx.beginPath();
                        ctx.arc(centro, centro, 25, 0, 2 * Math.PI);
                        ctx.fillStyle = "#31333F";
                        ctx.fill();
                        ctx.strokeStyle = "white";
                        ctx.lineWidth = 3;
                        ctx.stroke();
                    }}

                    dibujarRuleta();

                    document.getElementById("btnGirar").addEventListener("click", () => {{
                        document.getElementById("btnGirar").disabled = true;
                        document.getElementById("btnGirar").style.opacity = "0.5";
                        document.getElementById("txtResultado").style.color = "#0e1117";
                        
                        const vueltasCompletas = 5 + Math.floor(Math.random() * 3);
                        const anguloObjetivoGajo = 1.5 * Math.PI - (idxGanador * angularGajo) - (angularGajo / 2);
                        const anguloFinal = (vueltasCompletas * 2 * Math.PI) + anguloObjetivoGajo;
                        
                        let inicioTiempo = null;
                        const duracionGiro = 4500;
                        
                        function animarGiro(tiempoActual) {{
                            if (!inicioTiempo) inicioTiempo = tiempoActual;
                            const progreso = (tiempoActual - inicioTiempo) / duracionGiro;
                            
                            if (progreso < 1) {{
                                const factorDesaceleracion = 1 - Math.pow(1 - progreso, 3);
                                anguloActual = factorDesaceleracion * anguloFinal;
                                dibujarRuleta();
                                requestAnimationFrame(animarGiro);
                            }} else {{
                                anguloActual = anguloFinal;
                                dibujarRuleta();
                                const res = document.getElementById("txtResultado");
                                res.innerText = "🎯 ¡SELECCIONADO: " + candidatos[idxGanador] + "!";
                                res.style.color = "#2ecc71";
                            }}
                        }}
                        requestAnimationFrame(animarGiro);
                    }});
                </script>
                """
                components.html(html_ruleta, height=520)

                st.write("👉 **Confirmación Oficial:** Una vez que la ruleta se detenga en el stream, presiona el botón de abajo para enviar al seleccionado a su respectivo equipo:")
                if st.button("📥 Confirmar y agregar seleccionado", use_container_width=True, type="primary"):
                    pts_jugador = jugadores_fecha_perfiles[ganador][posicion_a_sortear]
                    if len(st.session_state.draft_manual["Equipo 1"]) <= len(st.session_state.draft_manual["Equipo 2"]):
                        st.session_state.draft_manual["Equipo 1"].append((ganador, posicion_a_sortear))
                        st.session_state.draft_manual["Suma 1"] += pts_jugador
                    else:
                        st.session_state.draft_manual["Equipo 2"].append((ganador, posicion_a_sortear))
                        st.session_state.draft_manual["Suma 2"] += pts_jugador
                    st.session_state.ganador_ruleta = None
                    st.rerun()
            else:
                st.markdown(f"⚠️ *No quedan jugadores viables habilitados para ocupar el rol de {posicion_a_sortear}.*")
            
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
                if es_admin_stream:
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
                if es_admin_stream:
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
        
        if es_admin_stream:
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
                guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                st.success("¡Partido archivado en la nube!")
                st.rerun()
        else:
            st.info("🏃‍♂️ El partido está en juego. Los resultados solo pueden ser cargados por el organizador.")
            
        if st.session_state.historial_partidos:
            st.write("### 📜 Historial de Resultados")
            for idx, part in enumerate(st.session_state.historial_partidos):
                st.info(f"**Partido #{idx+1}:** {part['Equipos']} ➔ **Marcador Final: {part['Resultado']}**")
