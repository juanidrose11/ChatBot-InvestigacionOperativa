import streamlit as st
from core.nlp import detectar_si_no
from core.conocimientos import conocimientos
from core.estado import reset_state


def procesar_explicar(entrada):
    step = st.session_state.steps["explicar"]
    conceptos = conocimientos.get("explicacion_conceptos", {})

    simple = conceptos.get(
        "simple",
        "La optimización no lineal busca el mejor valor cuando las relaciones del modelo no son lineales.",
    )
    caso_practico = conceptos.get("caso_practico", "No hay caso práctico cargado.")
    ejemplo_estandar = conceptos.get("ejemplo_estandar", "No hay ejemplo cargado.")
    implicancia = conceptos.get("implicancia", "No hay implicancia cargada.")
    matematica_formal = conceptos.get("matematica_formal", "No hay formulación matemática cargada.")
    resumen_simple = conceptos.get("resumen_simple", "No hay resumen cargado.")

    if step == 0:
        st.session_state.steps["explicar"] = 1
        return simple + "\n\n¿Te gustaría ver un **caso práctico**?"

    respuesta = detectar_si_no(entrada)

    if step == 1:
        if respuesta == "si":
            st.session_state.steps["explicar"] = 2
            txt = caso_practico + "\n\n" + ejemplo_estandar
            return txt + "\n\n" + implicancia + "\n\n¿Necesitas un **nivel técnico** más alto (matemática formal)?"
        reset_state()
        return "¡Entendido! Hablame si necesitas algo más."

    if step == 2:
        if respuesta == "si":
            st.session_state.steps["explicar"] = 3
            return matematica_formal + "\n\n¿Ha quedado clara la explicación?"
        reset_state()
        return "¡Entendido! Hablame si necesitas algo más."

    if step == 3:
        if respuesta == "si":
            reset_state()
            return "¡Entendido! Hablame si necesitas algo más."
        st.session_state.steps["explicar"] = 3
        txt = matematica_formal + "\n\n" + resumen_simple
        return txt + "\n\n¿Ha quedado clara la explicación?"

    reset_state()
    return "Reinicié la explicación. Prueba diciendo: 'explicar un concepto'."
