import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os

# Configuración de la página web (Forzamos diseño ancho para las 3 columnas)
st.set_page_config(page_title="Draft a la carta", layout="wide")

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =====================================================================
PASSWORD_STREAM = "bricks2026"
PASSWORD_MAESTRA = "bricks2026admin"
ARCHIVO_BD = "datos_draft.json"

# --- FUNCIONES DE PERSISTENCIA ---
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

# --- INICIALIZACIÓN DE ESTADO ---
datos_guardados = cargar_datos_globales()
if "jugadores" not in st.session_state: st.session_state.jugadores = datos_guardados["jugadores"]
if "historial_partidos" not in st.session_state: st.session_state.historial_partidos = datos_guardados["historial_partidos"]
if "draft_manual" not in st.session_state: st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}

# =====================================================================
# BARRA LATERAL Y LOGIN
# =====================================================================
st.sidebar.title("🍔 Bricks a la carta")
st.sidebar.subheader("🔒 Acceso de Seguridad")
password_ingresada = st.sidebar.text_input("Contraseña:", type="password")

es_admin_stream = (password_ingresada == PASSWORD_STREAM or password_ingresada == PASSWORD_MAESTRA)
es_super_admin = (password_ingresada == PASSWORD_MAESTRA)

ver_puntos = False
if es_super_admin: 
    st.sidebar.success("👑 SUPER-ADMIN Activo")
    ver_puntos = st.sidebar.toggle("🔧 Mostrar puntos de jugadores", value=False)
elif es_admin_stream: 
    st.sidebar.success("🔓 Streamer Activo")
    ver_puntos = st.sidebar.toggle("🔧 Mostrar puntos de jugadores", value=False)
else: 
    st.sidebar.info("👁️ Modo Espectador")

st.sidebar.write("---")
if st.sidebar.button("🔄 Sincronizar Datos", use_container_width=True):
    st.cache_data.clear()
    datos_actualizados = cargar_datos_globales()
    st.session_state.jugadores = datos_actualizados["jugadores"]
    st.session_state.historial_partidos = datos_actualizados["historial_partidos"]
    st.rerun()

# Menú de navegación
opciones_menu = ["🏀 Mesa de Draft"]
if es_super_admin: opciones_menu.append("📋 Administración Total")
seccion_actual = st.sidebar.radio("Navegación:", opciones_menu)

# =====================================================================
# VENTANA: ADMINISTRACIÓN TOTAL (SUPER-ADMIN)
# =====================================================================
if seccion_actual == "📋 Administración Total":
    st.title("⚙️ Panel de Control — Super Admin")
    tab_roster, tab_historial = st.tabs(["👤 Gestión Roster", "🚨 Gestión Historial"])
    
    with tab_roster:
        st.header("👤 Agregar / Borrar Jugadores")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Jugador:").upper().strip()
            pg = st.number_input("PG (Base)", 0, 99, 0)
            sg = st.number_input("SG (Escolta)", 0, 99, 0)
            sf = st.number_input("SF (Alero)", 0, 99, 0)
            pf = st.number_input("PF (Ala-Pívot)", 0, 99, 0)
            c = st.number_input("C (Pívot)", 0, 99, 0)
            if st.button("💾 Guardar Jugador permanentemente", use_container_width=True):
                if nombre:
                    st.session_state.jugadores[nombre] = {"PG":pg,"SG":sg,"SF":sf,"PF":pf,"C":c}
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.success(f"¡{nombre} guardado!")
                    st.rerun()
        with col2:
            st.write("Jugadores actuales en el Roster:")
            for j in sorted(list(st.session_state.jugadores.keys())):
                if st.button(f"🗑️ Eliminar {j}", key=f"del_{j}", use_container_width=True):
                    del st.session_state.jugadores[j]
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.rerun()

    with tab_historial:
        st.header("🚨 Gestión de Partidos (Filtro Anti-Troll)")
        if st.session_state.historial_partidos:
            opciones = [f"#{i+1}: {p['Equipos']} | {p['Resultado']}" for i, p in enumerate(st.session_state.historial_partidos)]
            idx_elegido = st.selectbox("Seleccionar partido para auditar o borrar:", range(len(opciones)), format_func=lambda x: opciones[x])
            
            c_del, c_edit = st.columns(2)
            if c_del.button("💥 BORRAR ESTE PARTIDO POR COMPLETO", type="primary", use_container_width=True):
                st.session_state.historial_partidos.pop(idx_elegido)
                guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                st.warning("Partido removido del historial.")
                st.rerun()
                
            with c_edit.expander("✏️ Editar Marcador de este Partido"):
                n_res1 = st.number_input("Nuevo Score Eq 1", value=0, key="adm_score_1")
                n_res2 = st.number_input("Nuevo Score Eq 2", value=0, key="adm_score_2")
                if st.button("Aplicar Corrección Forzada", use_container_width=True):
                    st.session_state.historial_partidos[idx_elegido]["Resultado"] = f"{n_res1} - {n_res2}"
                    guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                    st.success("¡Marcador actualizado!")
                    st.rerun()
        else:
            st.info("No hay partidos registrados en la base de datos.")

# =====================================================================
# VENTANA: MESA DE DRAFT (DISEÑO TRIPLE COLUMNA EN PARALELO)
# =====================================================================
else:
    st.title("🏀 Mesa de Draft a la Carta")
    
    # Declaramos las 3 columnas principales
    col_izquierda, col_centro, col_derecha = st.columns([1.1, 1.3, 1.4])
    
    # -----------------------------------------------------------------
    # COLUMNA 1: CONVOCATORIA Y ROLES (IZQUIERDA)
    # -----------------------------------------------------------------
    with col_izquierda:
        st.header("🎲 Convocatoria")
        presentes = []
        if not st.session_state.jugadores:
            st.warning("No hay jugadores cargados.")
        else:
            with st.container(height=350, border=True):
                for j in sorted(st.session_state.jugadores.keys()):
                    if es_admin_stream:
                        if st.checkbox(f"✔️ {j}", key=f"p_{j}"): presentes.append(j)
                    else:
                        if st.checkbox(f"✔️ {j}", key=f"p_{j}", disabled=True): presentes.append(j)
            st.write(f"**Conectados:** {len(presentes)} jugadores.")
        
        jugadores_fecha_perfiles = {}
        if presentes:
            st.write("---")
            st.subheader("🛠️ Ajuste de Roles hoy")
            with st.container(height=320, border=True):
                for jug in sorted(presentes):
                    st.markdown(f"**⛹️‍♂️ {jug}**")
                    pos_originales = list(st.session_state.jugadores[jug].keys())
                    roles_activos_hoy = []
                    
                    sub_cols = st.columns(len(pos_originales))
                    for idx_pos, pos in enumerate(pos_originales):
                        with sub_cols[idx_pos]:
                            if es_admin_stream:
                                if st.checkbox(pos, value=True, key=f"rol_{jug}_{pos}"): roles_activos_hoy.append(pos)
                            else:
                                if st.checkbox(pos, value=True, key=f"rol_{jug}_{pos}", disabled=True): roles_activos_hoy.append(pos)
                    
                    if roles_activos_hoy:
                        jugadores_fecha_perfiles[jug] = {p: st.session_state.jugadores[jug][p] for p in roles_activos_hoy}
                    else:
                        jugadores_fecha_perfiles[jug] = st.session_state.jugadores[jug]

    roles_totales = ["PG", "SG", "SF", "PF", "C"]
    ya_drafteados = [j[0] for j in st.session_state.draft_manual["Equipo 1"]] + [j[0] for j in st.session_state.draft_manual["Equipo 2"]]
    libres_hoy = [j for j in presentes if j not in ya_drafteados]
    pos_cubiertas_eq1 = [j[1] for j in st.session_state.draft_manual["Equipo 1"]]
    pos_cubiertas_eq2 = [j[1] for j in st.session_state.draft_manual["Equipo 2"]]

    # -----------------------------------------------------------------
    # COLUMNA 2: RUCOLO Y HERRAMIENTAS DE SORTEO (CENTRO)
    # -----------------------------------------------------------------
    with col_centro:
        st.header("🎡 Herramientas")
        if es_admin_stream:
            pestana1, pestana2 = st.tabs(["🎯 Sorteo Auto Balanced", "🎡 Ruleta Interactiva"])
            
            with pestana1:
                if st.button("🚀 Ejecutar Algoritmo de Sorteo", type="primary", use_container_width=True):
                    if len(presentes) < 10:
                        st.warning("Se necesitan mínimo 10 jugadores.")
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
                                elegido = next((j for j in disponibles if r in jugadores_fecha_perfiles.get(j, {})), None)
                                if elegido:
                                    eq1.append((elegido, r))
                                    s1 += jugadores_fecha_perfiles[elegido][r]
                                    disponibles.remove(elegido)
                                else:
                                    error_posicion = True
                                    break
                            
                            if error_posicion: continue
                            
                            for i, r in enumerate(roles_totales):
                                elegido = disponibles[i]
                                if r in jugadores_fecha_perfiles.get(elegido, {}):
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
                            st.success("¡Equipos armados y balanceados!")
                            st.rerun()
                        else:
                            st.error("Roster trabado. Habilita más posiciones dinámicas.")

            with pestana2:
                posicion_a_sortear = st.selectbox("Posición a sortear:", roles_totales)
                
                def es_seguro_elegir(jugador_test, pos_test):
                    libres_simulados = [j for j in libres_hoy if j != jugador_test]
                    faltantes_eq1 = [r for r in roles_totales if r not in pos_cubiertas_eq1]
                    faltantes_eq2 = [r for r in roles_totales if r not in pos_cubiertas_eq2]
                    if len(st.session_state.draft_manual["Equipo 1"]) <= len(st.session_state.draft_manual["Equipo 2"]):
                        if pos_test in faltantes_eq1: faltantes_eq1.remove(pos_test)
                    else:
                        if pos_test in faltantes_eq2: faltantes_eq2.remove(pos_test)
                    roles_que_faltan_llenar = faltantes_eq1 + faltantes_eq2
                    if not roles_que_faltan_llenar: return True
                    for _ in range(300):
                        random.shuffle(libres_simulados)
                        temp_libres = libres_simulados.copy()
                        exito = True
                        for r_faltante in roles_que_faltan_llenar:
                            apto = next((j for j in temp_libres if r_faltante in jugadores_fecha_perfiles.get(j, {})), None)
                            if apto: temp_libres.remove(apto)
                            else: {exito := False}; break
                        if exito: return True
                    return False

                candidatos = [j for j in libres_hoy if posicion_a_sortear in jugadores_fecha_perfiles.get(j, {}) and es_seguro_elegir(j, posicion_a_sortear)]

                if candidatos:
                    if "ganador_ruleta" not in st.session_state: st.session_state.ganador_ruleta = None
                    colores_gajos = ["#FF4B4B", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
                    lista_colores = [colores_gajos[i % len(colores_gajos)] for i in range(len(candidatos))]
                    
                    if st.button("🔮 Sincronizar Ruleta", use_container_width=True):
                        st.session_state.ganador_ruleta = random.choice(candidatos)
                    
                    ganador = st.session_state.ganador_ruleta if st.session_state.ganador_ruleta in candidatos else candidatos[0]
                    idx_ganador = candidatos.index(ganador)

                    # Corregido: pasamos los datos serializados limpiamente sin romper strings triples
                    js_candidatos = json.dumps(candidatos)
                    js_colores = json.dumps(lista_colores)

                    html_ruleta = f"""
                    <div style="text-align: center; background-color: #0e1117; padding: 5px; border-radius: 10px;">
                        <div style="position: relative; display: inline-block;">
                            <div style="position: absolute; top: -5px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 18px solid #FF4B4B; z-index: 10;"></div>
                            <canvas id="canvasRuleta" width="260" height="260" style="border: 3px solid #31333F; border-radius: 50%;"></canvas>
                        </div>
                        <br>
                        <button id="btnGirar" style="background-color: #FF4B4B; color: white; border: none; padding: 8px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; margin-top:5px;">🎡 GIRAR EN STREAM 🎡</button>
                        <h4 id="txtResultado" style="margin-top: 5px; color: #0e1117; min-height: 20px;">.</h4>
                    </div>
                    <script>
                        const candidatos = {js_candidatos};
                        const colores = {js_colores};
                        const idxGanador = {idx_ganador};
                        const canvas = document.getElementById("canvasRuleta");
                        const ctx = canvas.getContext("2d");
                        const numGajos = candidatos.length;
                        const angularGajo = (2 * Math.PI) / numGajos;
                        let anguloActual = 0;
                        function dibujar() {{
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            const centro = canvas.width / 2;
                            for (let i = 0; i < numGajos; i++) {{
                                const ang_i = anguloActual + (i * angularGajo);
                                const ang_f = ang_i + angularGajo;
                                ctx.beginPath(); ctx.moveTo(centro, centro); ctx.arc(centro, centro, centro - 3, ang_i, ang_f);
                                ctx.fillStyle = colores[i]; ctx.fill(); ctx.stroke();
                                ctx.save(); ctx.translate(centro, centro); ctx.rotate(ang_i + angularGajo / 2);
                                ctx.textAlign = "right"; ctx.fillStyle = "white"; ctx.font = "bold 11px sans-serif";
                                ctx.fillText(candidatos[i], centro - 15, 4); ctx.restore();
                            }}
                        }}
                        dibujar();
                        document.getElementById("btnGirar").addEventListener("click", () => {{
                            document.getElementById("btnGirar").disabled = true;
                            const totalAng = (6 * 2 * Math.PI) + (1.5 * Math.PI - (idxGanador * angularGajo) - (angularGajo / 2));
                            let start = null;
                            function animar(now) {{
                                if (!start) start = now; const prog = (now - start) / 3500;
                                if (prog < 1) {{ anguloActual = (1 - Math.pow(1 - prog, 3)) * totalAng; dibujar(); requestAnimationFrame(animar); }}
                                else {{ anguloActual = totalAng; dibujar(); const r = document.getElementById("txtResultado"); r.innerText = "🎯 ¡" + candidatos[idxGanador] + "!"; r.style.color = "#2ecc71"; }}
                            }}
                            requestAnimationFrame(animar);
                        }});
                    </script>
                    """
                    components.html(html_ruleta, height=360)

                    if st.button("📥 Mandar Ganador a la Mesa", use_container_width=True, type="primary"):
                        pts = jugadores_fecha_perfiles[ganador][posicion_a_sortear]
                        if len(st.session_state.draft_manual["Equipo 1"]) <= len(st.session_state.draft_manual["Equipo 2"]):
                            st.session_state.draft_manual["Equipo 1"].append((ganador, posicion_a_sortear))
                            st.session_state.draft_manual["Suma 1"] += pts
                        else:
                            st.session_state.draft_manual["Equipo 2"].append((ganador, posicion_a_sortear))
                            st.session_state.draft_manual["Suma 2"] += pts
                        st.session_state.ganador_ruleta = None
                        st.rerun()
                else:
                    st.markdown("🔒 *No hay candidatos válidos libres.*")

            st.write("---")
            st.write("**Agregar a Mano:**")
            if libres_hoy:
                c_m1, c_m2, c_m3 = st.columns(3)
                j_m = c_m1.selectbox("Jugador", libres_hoy, key="m_j")
                r_v = list(jugadores_fecha_perfiles.get(j_m, {}).keys())
                r_m = c_m2.selectbox("Rol", r_v, key="m_r")
                e_d = c_m3.selectbox("Hacia", ["Eq 1", "Eq 2"], key="m_e")
                if st.button("➕ Forzar Fichaje", use_container_width=True):
                    pts = jugadores_fecha_perfiles[j_m][r_m]
                    if e_d == "Eq 1":
                        st.session_state.draft_manual["Equipo 1"].append((j_m, r_m))
                        st.session_state.draft_manual["Suma 1"] += pts
                    else:
                        st.session_state.draft_manual["Equipo 2"].append((j_m, r_m))
                        st.session_state.draft_manual["Suma 2"] += pts
                    st.rerun()
            
            if st.button("❌ Reiniciar Mesa Completa", type="secondary", use_container_width=True):
                st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
                st.rerun()
        else:
            st.warning("Herramientas bloqueadas para Espectadores.")

    # -----------------------------------------------------------------
    # COLUMNA 3: CONTROL DE LA CANCHA Y DISCORD (DERECHA)
    # -----------------------------------------------------------------
    with col_derecha:
        st.header("🔥 Control de la Cancha")
        
        with st.container(height=340, border=True):
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                # Corregido: Limpiamos las comillas complejas de la f-string de Streamlit
                txt_e1 = f"### 🔵 Eq 1 ({st.session_state.draft_manual['Suma 1']})" if ver_puntos else "### 🔵 Eq 1"
                st.markdown(txt_e1)
                for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 1"]):
                    pts = st.session_state.jugadores[jug].get(rol, 0)
                    c_txt, c_x = st.columns([4, 1])
                    c_txt.write(f"• **{jug}** ({rol})")
                    if es_admin_stream and c_x.button("❌", key=f"k1_{idx}"):
                        st.session_state.draft_manual["Suma 1"] -= pts
                        st.session_state.draft_manual["Equipo 1"].pop(idx)
                        st.rerun()
                        
            with sub_col2:
                # Corregido: Igual acá, evitamos escapar comillas anidadas en Markdown
                txt_e2 = f"### 🔴 Eq 2 ({st.session_state.draft_manual['Suma 2']})" if ver_puntos else "### 🔴 Eq 2"
                st.markdown(txt_e2)
                for idx, (jug, rol) in enumerate(st.session_state.draft_manual["Equipo 2"]):
                    pts = st.session_state.jugadores[jug].get(rol, 0)
                    c_txt, c_x = st.columns([4, 1])
                    c_txt.write(f"• **{jug}** ({rol})")
                    if es_admin_stream and c_x.button("❌", key=f"k2_{idx}"):
                        st.session_state.draft_manual["Suma 2"] -= pts
                        st.session_state.draft_manual["Equipo 2"].pop(idx)
                        st.rerun()

        # Copiar a Discord compacto
        dict_e1 = {r: j for j, r in st.session_state.draft_manual["Equipo 1"]}
        dict_e2 = {r: j for j, r in st.session_state.draft_manual["Equipo 2"]}
        
        # Corregido: Armamos el bloque de texto plano de forma segura sin f-string triple rota
        texto_plano = "POS | EQUIPO 1       | EQUIPO 2\n"
        for pos in roles_totales:
            p1 = dict_e1.get(pos, '---').ljust(14)
            p2 = dict_e2.get(pos, '---')
            texto_plano += f"{pos.ljust(3)} : {p1} vs {p2}\n"
        st.code(texto_plano, language="text")

        # Registro del Marcador Final en vivo
        if es_admin_stream:
            st.markdown("**📝 Registrar Resultado Final:**")
            mc1, mc2, mc3 = st.columns([1.5, 1.5, 2])
            res_eq1 = mc1.number_input("🔵 Eq 1:", min_value=0, value=0, key="scr_1")
            res_eq2 = mc2.number_input("🔴 Eq 2:", min_value=0, value=0, key="scr_2")
            if mc3.button("💾 archivar", use_container_width=True):
                nombres_e1 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 1"]])
                nombres_e2 = ", ".join([j[0] for j in st.session_state.draft_manual["Equipo 2"]])
                st.session_state.historial_partidos.append({
                    "Equipos": f"🔵 ({nombres_e1}) VS 🔴 ({nombres_e2})",
                    "Resultado": f"{res_eq1} - {res_eq2}"
                })
                guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                st.success("¡Guardado!")
                st.rerun()

            if st.session_state.historial_partidos:
                with st.expander("🩹 Corregir último score cargado"):
                    ec1, ec2, ec3 = st.columns(3)
                    er1 = ec1.number_input("Eq 1:", min_value=0, value=0, key="err_1")
                    er2 = ec2.number_input("Eq 2:", min_value=0, value=0, key="err_2")
                    if ec3.button("Sobreescribir", use_container_width=True):
                        st.session_state.historial_partidos[-1]["Resultado"] = f"{er1} - {er2}"
                        guardar_datos_globales(st.session_state.jugadores, st.session_state.historial_partidos)
                        st.rerun()

    # =====================================================================
    # SECCIÓN INFERIOR: HISTORIAL DE RESULTADOS CONSTANTE Y GLOBAL
    # =====================================================================
    st.write("---")
    st.header("📜 Historial General de Resultados")
    if st.session_state.historial_partidos:
        columnas_historial = st.columns(2)
        for idx, part in enumerate(reversed(st.session_state.historial_partidos)):
            col_lado = columnas_historial[idx % 2]
            num_partido = len(st.session_state.historial_partidos) - idx
            col_lado.info(f"**Partido #{num_partido}:** {part['Equipos']} ➔ **Marcador: {part['Resultado']}**")
    else:
        st.write("*Todavía no hay partidos archivados en esta sesión.*")
