import streamlit as st
from core.conocimientos import conocimientos
from core.estado import reset_state
from core.nlp import parsear_numeros, normalizar


def generar_menu_metodos():
    from solvers import SOLVERS

    lineas = ["¿Qué método querés usar para resolver?\n"]
    for i, (_, solver) in enumerate(SOLVERS.items(), 1):
        sufijo = "" if solver.DISPONIBLE else " *(guía de pasos)*"
        lineas.append(f"**{i}.** {solver.NOMBRE}{sufijo}")
    lineas.append("\nEscribí el número o el nombre del método.")
    return "\n".join(lineas)


def procesar_elegir_metodo(entrada):
    from solvers import SOLVERS

    solvers_list = list(SOLVERS.items())
    nums = parsear_numeros(entrada)
    if nums:
        idx = int(nums[0]) - 1
        if 0 <= idx < len(solvers_list):
            metodo_id, _ = solvers_list[idx]
            return iniciar_resolver(metodo_id)

    entrada_norm = normalizar(entrada)
    for metodo_id, solver in SOLVERS.items():
        if normalizar(solver.NOMBRE) in entrada_norm or metodo_id.replace("_", " ") in entrada_norm:
            return iniciar_resolver(metodo_id)

    return f"No reconocí ese método.\n\n{generar_menu_metodos()}"


def iniciar_resolver(metodo):
    from solvers import SOLVERS

    st.session_state.pending_after_classification = None

    if metodo is None:
        st.session_state.current_flow = "elegir_metodo_resolver"
        return generar_menu_metodos()

    if metodo in SOLVERS and SOLVERS[metodo].DISPONIBLE:
        st.session_state.current_flow = metodo
        st.session_state.solver_step = 0
        st.session_state.solver_data = {}
        return SOLVERS[metodo].iniciar()

    # Fallback: guía de pasos desde conocimientos.json
    guias = conocimientos.get("guia_resolucion", {})
    guia_metodo = guias.get(metodo, guias.get("default", []))
    st.session_state.guia_actual = guia_metodo
    st.session_state.current_flow = "resolver"
    st.session_state.steps["resolver"] = 0
    return "Te guiaré paso a paso en el proceso de resolución:\n\n" + _avanzar_guia()


def procesar_resolver(_entrada):
    return _avanzar_guia()


def _avanzar_guia():
    guia = st.session_state.get("guia_actual", [])
    step = st.session_state.steps["resolver"]

    if not guia:
        reset_state()
        return "No encontré una guía de resolución cargada."

    if step < len(guia):
        item = guia[step]
        st.session_state.steps["resolver"] += 1
        numero_paso = step + 1
        mensaje = f"**Paso {numero_paso}: {item.get('paso', 'Sin título')}**\n\n{item.get('descripcion', 'Sin descripción.')}"

        if st.session_state.steps["resolver"] < len(guia):
            return mensaje + "\n\n¿Continuamos con el siguiente paso?"

        reset_state()
        return mensaje + "\n\n¡Eso completa la guía de resolución!"

    reset_state()
    return "Guía finalizada."
