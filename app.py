import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

# Configuración de la página web (Forzamos diseño ancho)
st.set_page_config(page_title="Draft a la carta", layout="wide")

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD Y PERSISTENCIA
# =====================================================================
PASSWORD_STREAM = "bricks2026"
PASSWORD_MAESTRA = "bricks2026admin"
ARCHIVO_BD = "datos_draft.json"

CODIGOS_MATCHMAKING = ["1q2w", "2w3e", "3e4r", "4r5t", "5t6y", "6y7u", "7u8i", "8i9o", "9o0p"]

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
if "lista_espera_forzada" not in st.session_state: st.session_state.lista_espera_forzada = []

# NUEVO: Contador independiente para los códigos diarios
if "contador_codigo_dia" not in st.session_state: st.session_state.contador_codigo_dia = 0

cant_partidos = len(st.session_state.historial_partidos)
codigo_actual = CODIGOS_MATCHMAKING[st.session_state.contador_codigo_dia % len(CODIGOS_MATCHMAKING)]

# =====================================================================
# BARRA LATERAL Y LOGIN (GESTIÓN DE NAVEGACIÓN PRINCIPAL)
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

# NUEVO: Botón para reiniciar la secuencia de códigos diarios
if st.sidebar.button("♻️ Reiniciar Códigos (Nuevo Día)", type="primary", use_container_width=True):
    st.session_state.contador_codigo_dia = 0
    st.toast("¡Secuencia de códigos reseteada a 1q2w!", icon="✅")
    st.rerun()

# Estructura de navegación para poder ocultar la Convocatoria dinámicamente
opciones_menu = []
if es_super_admin:
    opciones_menu.append("📋 Administración Total")

# Ponemos las herramientas directamente en el control de navegación
if es_admin_stream:
    opciones_menu.extend(["🎯 Sorteo Auto Balanced", "🎡 Ruleta Interactive", "✍️ Armado 100% a Mano"])
else:
    opciones_menu.append("🏀 Ver Mesa de Draft (Espectador)")

seccion_actual = st.sidebar.radio("Seleccionar Sección / Herramienta:", opciones_menu)

# VARIABLES GLOBALES DE CONTROL DE CONVOCATORIA
roles_totales = ["PG", "SG", "SF", "PF", "C"]
presentes = []
jugadores_fecha_perfiles = {}

# Procesamiento previo de la convocatoria (siempre activo en segundo plano)
for jug in sorted(st.session_state.jugadores.keys()):
    roles_activos_hoy = []
    for pos in roles_totales:
        if st.session_state.get(f"rol_{jug}_{pos}", False):
            roles_activos_hoy.append(pos)
    if roles_activos_hoy:
        presentes.append(jug)
        jugadores_fecha_perfiles[jug] = {p: st.session_state.jugadores[jug][p] for p in roles_activos_hoy}

ya_drafteados = [j[0] for j in st.session_state.draft_manual["Equipo 1"]] + [j[0] for j in st.session_state.draft_manual["Equipo 2"]]
if st.session_state.lista_espera_forzada:
    lista_espera = st.session_state.lista_espera_forzada
else:
    lista_espera = [j for j in presentes if j not in ya_drafteados]

libres_hoy = [j for j in presentes if j not in ya_drafteados]
pos_cubiertas_eq1 = [j[1] for j in st.session_state.draft_manual["Equipo 1"]]
pos_cubiertas_eq2 = [j[1] for j in st.session_state.draft_manual["Equipo 2"]]
equipos_listos = (len(st.session_state.draft_manual["Equipo 1"]) == 5 and len(st.session_state.draft_manual["Equipo 2"]) == 5)

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
            st.write("📋 Jugadores actuales en el Roster:")
            for j in sorted(list(st.session_state.jugadores.keys())):
                puntos = st.session_state.jugadores[j]
                with st.container(border=True):
                    c_info, c_action = st.columns([3, 1])
                    with c_info:
                        st.markdown(f"### 🪪 {j}")
                        st.code(f"PG: {puntos.get('PG', 0)} | SG: {puntos.get('SG', 0)} | SF: {puntos.get('SF', 0)} | PF: {puntos.get('PF', 0)} | C: {puntos.get('C', 0)}", language="text")
                    with c_action:
                        st.write("") 
                        if st.button("🗑️ Eliminar", key=f"del_{j}", use_container_width=True, type="primary"):
                            del st.session_state.jugadores[j]
                            guardar_datos_globales(st.session_state.historial_partidos, st.session_state.historial_partidos)
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
# VENTANA: MESA DE DRAFT (CONFIGURACIÓN DINÁMICA DE COLUMNAS)
# =====================================================================
elif seccion_actual == "✍️ Armado 100% a Mano":
    # MODO CONFIGURACIÓN REQUERIDO: Oculta convocatoria, usa 2 columnas anchas
    st.title("🏀 Mesa de Draft (Armado Manual)")
    col_centro, col_derecha = st.columns([2.3, 1.3])
    
    with col_centro:
        st.header("✍️ Distribución de Plantilla Manual")
        sub_col_armado, sub_col_espera_fija = st.columns([2.0, 1.3])
        opciones_busqueda = ["---"] + sorted(list(st.session_state.jugadores.keys()))
        dict_actual_e1 = {r: j for j, r in st.session_state.draft_manual["Equipo 1"]}
        dict_actual_e2 = {r: j for j, r in st.session_state.draft_manual["Equipo 2"]}
        
        with sub_col_armado:
            c_man_e1, c_man_e2 = st.columns(2)
            with c_man_e1:
                st.markdown("🔵 **Equipo 1**")
                b_pg1 = st.selectbox("PG:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e1.get("PG", "---")) if dict_actual_e1.get("PG", "---") in opciones_busqueda else 0, key="bm_pg1")
                b_sg1 = st.selectbox("SG:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e1.get("SG", "---")) if dict_actual_e1.get("SG", "---") in opciones_busqueda else 0, key="bm_sg1")
                b_sf1 = st.selectbox("SF:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e1.get("SF", "---")) if dict_actual_e1.get("SF", "---") in opciones_busqueda else 0, key="bm_sf1")
                b_pf1 = st.selectbox("PF:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e1.get("PF", "---")) if dict_actual_e1.get("PF", "---") in opciones_busqueda else 0, key="bm_pf1")
                b_c1  = st.selectbox("C:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e1.get("C", "---")) if dict_actual_e1.get("C", "---") in opciones_busqueda else 0, key="bm_c1")
                
            with c_man_e2:
                st.markdown("🔴 **Equipo 2**")
                b_pg2 = st.selectbox("PG:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e2.get("PG", "---")) if dict_actual_e2.get("PG", "---") in opciones_busqueda else 0, key="bm_pg2")
                b_sg2 = st.selectbox("SG:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e2.get("SG", "---")) if dict_actual_e2.get("SG", "---") in opciones_busqueda else 0, key="bm_sg2")
                b_sf2 = st.selectbox("SF:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e2.get("SF", "---")) if dict_actual_e2.get("SF", "---") in opciones_busqueda else 0, key="bm_sf2")
                b_pf2 = st.selectbox("PF:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e2.get("PF", "---")) if dict_actual_e2.get("PF", "---") in opciones_busqueda else 0, key="bm_pf2")
                b_c2  = st.selectbox("C:", opciones_busqueda, index=opciones_busqueda.index(dict_actual_e2.get("C", "---")) if dict_actual_e2.get("C", "---") in opciones_busqueda else 0, key="bm_c2")
            
            st.write("")
            if st.button("💾 Aplicar Plantilla Manual a la Cancha", type="primary", use_container_width=True):
                nuevo_e1 = []
                s1 = 0
                for pos, val in [("PG", b_pg1), ("SG", b_sg1), ("SF", b_sf1), ("PF", b_pf1), ("C", b_c1)]:
                    if val != "---":
                        nuevo_e1.append((val, pos))
                        s1 += st.session_state.jugadores[val].get(pos, 0)
                        
                nuevo_e2 = []
                s2 = 0
                for pos, val in [("PG", b_pg2), ("SG", b_sg2), ("SF", b_sf2), ("PF", b_pf2), ("C", b_c2)]:
                    if val != "---":
                        nuevo_e2.append((val, pos))
                        s2 += st.session_state.jugadores[val].get(pos, 0)
                
                nuevo_banco = []
                for i in range(1, 10):
                    b_val = st.session_state.get(f"besp_{i}", "---")
                    if b_val != "---" and b_val not in nuevo_banco:
                        nuevo_banco.append(b_val)
                        
                st.session_state.draft_manual["Equipo 1"] = nuevo_e1
                st.session_state.draft_manual["Equipo 2"] = nuevo_e2
                st.session_state.draft_manual["Suma 1"] = s1
                st.session_state.draft_manual["Suma 2"] = s2
                st.session_state.lista_espera_forzada = nuevo_banco
                st.success("¡Cancha cargada con éxito!")
                st.rerun()

        with sub_col_espera_fija:
            st.markdown("📋 **Lista de Espera**")
            banco_actual = st.session_state.lista_espera_forzada.copy()
            while len(banco_actual) < 9:
                banco_actual.append("---")
                
            with st.container(height=340, border=True):
                for i in range(1, 10):
                    st.selectbox(f"⏳ Campo {i}:", opciones_busqueda, index=opciones_busqueda.index(banco_actual[i-1] if banco_actual[i-1] in opciones_busqueda else "---"), key=f"besp_{i}")

        st.write("---")
        if st.button("❌ Reiniciar Mesa Completa", type="secondary", use_container_width=True):
            st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
            st.session_state.lista_espera_forzada = []
            st.rerun()

else:
    # MODO JUEGO REGULAR: Muestra las 3 columnas tradicionales (Convocatoria activa)
    st.title("🏀 Mesa de Draft a la Carta")
    col_izquierda, col_centro, col_derecha = st.columns([1.1, 1.4, 1.1])
    
    with col_izquierda:
        st.header("🎲 Convocatoria")
        if not st.session_state.jugadores:
            st.warning("No hay jugadores en el roster.")
        else:
            with st.container(height=420, border=True):
                for jug in sorted(st.session_state.jugadores.keys()):
                    st.markdown(f"**⛹️‍♂️ {jug}**")
                    pos_originales = list(st.session_state.jugadores[jug].keys())
                    
                    sub_cols = st.columns(len(pos_originales))
                    for idx_pos, pos in enumerate(pos_originales):
                        with sub_cols[idx_pos]:
                            val_check = st.session_state.get(f"rol_{jug}_{pos}", False)
                            if es_admin_stream:
                                st.checkbox(pos, value=val_check, key=f"rol_{jug}_{pos}", on_change=None)
                            else:
                                st.checkbox(pos, value=val_check, key=f"rol_{jug}_{pos}", disabled=True)
            st.write(f"**Conectados:** {len(presentes)}")

        st.write("---")
        st.subheader("📋 Espera de Filtro")
        if lista_espera:
            with st.container(height=150, border=True):
                for esp in lista_espera:
                    st.write(f"⏳ **{esp}**")

    with col_centro:
        st.header("🎡 Herramientas")
        if not es_admin_stream:
            st.warning("Modo Espectador activo.")
        elif seccion_actual == "🎯 Sorteo Auto Balanced":
            if equipos_listos:
                st.info("🔒 **Equipos armados.** Sorteo bloqueado.")
            else:
                if st.button("🚀 Ejecutar Algoritmo de Sorteo", type="primary", use_container_width=True):
                    if len(presentes) < 10:
                        st.warning("Se necesitan mínimo 10 jugadores con roles asignados.")
                    else:
                        st.session_state.lista_espera_forzada = [] 
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
                            st.success("¡Equipos balanceados!")
                            st.rerun()
                        else:
                            st.error("Roster trabado. Habilitá más posiciones dinámicas.")

        elif seccion_actual == "🎡 Ruleta Interactive":
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
                    exito_simulacion = True
                    for r_faltante in roles_que_faltan_llenar:
                        apto = next((j for j in temp_libres if r_faltante in jugadores_fecha_perfiles.get(j, {})), None)
                        if apto: temp_libres.remove(apto)
                        else: 
                            exito_simulacion = False
                            break
                    if exito_simulacion: return True
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

                js_candidatos = json.dumps(candidatos)
                js_colores = json.dumps(lista_colores)

                html_ruleta = f"""
                <div style="text-align: center; background-color: #0e1117; padding: 5px; border-radius: 10px;">
                    <div style="position: relative; display: inline-block;">
                        <div style="position: absolute; top: -5px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 18px solid #FF4B4B; z-index: 10;"></div>
                        <canvas id="canvasRuleta" width="240" height="240" style="border: 3px solid #31333F; border-radius: 50%;"></canvas>
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
                components.html(html_ruleta, height=340)

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
        if st.button("❌ Reiniciar Mesa Completa", type="secondary", use_container_width=True):
            st.session_state.draft_manual = {"Equipo 1": [], "Equipo 2": [], "Suma 1": 0, "Suma 2": 0}
            st.session_state.lista_espera_forzada = []
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
        # Crear un lienzo oscuro (estilo Bricks / Streamlit dark)
        ancho, alto = 600, 400
        img = Image.new("RGB", (ancho, alto), "#0e1117")
        canvas = ImageDraw.Draw(img)
        
        # Intentar cargar fuentes del sistema (si no, usa la default)
        try:
            fuente_titulo = ImageFont.truetype("arial.ttf", 24)
            fuente_sub = ImageFont.truetype("arial.ttf", 18)
            fuente_texto = ImageFont.truetype("arial.ttf", 16)
        except:
            fuente_titulo = fuente_sub = fuente_texto = ImageFont.load_default()
            
        # Dibujar bordes decorativos estéticos
        canvas.rectangle([10, 10, ancho - 10, alto - 10], outline="#31333F", width=3)
        
        # Encabezado principal
        canvas.text((30, 25), "🏀 DRAFT A LA CARTA", fill="#ffffff", font=fuente_titulo)
        canvas.line([(30, 60), (ancho - 30, 60)], fill="#31333F", width=2)
        
        # --- EQUIPO 1 (COLUMNA IZQUIERDA) ---
        canvas.text((40, 80), "🔵 EQUIPO 1", fill="#1f77b4", font=fuente_sub)
        y_pos = 115
        for jug, rol in st.session_state.draft_manual["Equipo 1"]:
            canvas.text((50, y_pos), f"• {jug} ({rol})", fill="#e2e8f0", font=fuente_texto)
            y_pos += 30
        if not st.session_state.draft_manual["Equipo 1"]:
            canvas.text((50, 115), "(Sin jugadores)", fill="#64748b", font=fuente_texto)
            
        # --- EQUIPO 2 (COLUMNA DERECHA) ---
        canvas.text((320, 80), "🔴 EQUIPO 2", fill="#ff4b4b", font=fuente_sub)
        y_pos = 115
        for jug, rol in st.session_state.draft_manual["Equipo 2"]:
            canvas.text((330, y_pos), f"• {jug} ({rol})", fill="#e2e8f0", font=fuente_texto)
            y_pos += 30
        if not st.session_state.draft_manual["Equipo 2"]:
            canvas.text((330, 115), "(Sin jugadores)", fill="#64748b", font=fuente_texto)
            
        # --- PIE DE PÁGINA: MATCHMAKING ---
        canvas.line([(30, 330), (ancho - 30, 330)], fill="#31333F", width=2)
        canvas.text((30, 350), f"🔑 MATCHMAKING CODE:  {codigo_actual}", fill="#2ecc71", font=fuente_sub)
        
        # Guardar en caché temporal para el botón
        ruta_temp = "cancha_temp.png"
        img.save(ruta_temp)
        return ruta_temp

    # Generamos la foto en segundo plano y la dejamos lista para descargar
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
            
            # NUEVO: Avanza al siguiente código de la lista para el próximo partido
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
                candidato_banco = next((j for j in banco_simulado if r_liberado in jugadores_fecha_perfiles.get(j, {})), None)
                if candidato_banco:
                    nuevo_equipo_reemplazo.append((candidato_banco, r_liberado))
                    banco_simulado.remove(candidato_banco)
                else:
                    if banco_simulado:
                        candidato_banco = banco_simulado[0]
                        nuevo_equipo_reemplazo.append((candidato_banco, r_liberado))
                        banco_simulado.remove(candidato_banco)
            
            suma_fijo = sum([jugadores_fecha_perfiles.get(j[0], st.session_state.jugadores[j[0]]).get(j[1], 0) for j in st.session_state.draft_manual[equipo_fijo]])
            suma_reemplazo = sum([jugadores_fecha_perfiles.get(j[0], st.session_state.jugadores[j[0]]).get(j[1], 0) for j in nuevo_equipo_reemplazo])
            
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

# =====================================================================
# SECCIÓN INFERIOR: HISTORIAL DE RESULTADOS GLOBAL CONSTANTE
# =====================================================================
st.write("---")
st.header("📜 Historial General de Resultados")
if st.session_state.historial_partidos:
    columnas_historial = st.columns(2)
    for idx, part in enumerate(reversed(st.session_state.historial_partidos)):
        col_lado = columnas_historial[idx % 2]
        num_partido = len(st.session_state.historial_partidos) - idx
        cod_info = f" (Cod: {part.get('Codigo Usado', 'N/A')})"
        col_lado.info(f"**Partido #{num_partido}{cod_info}:** {part['Equipos']} ➔ **Marcador: {part['Resultado']}**")
else:
    st.write("*Todavía no hay partidos archivados en esta sesión.*")
