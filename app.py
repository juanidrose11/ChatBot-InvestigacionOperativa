import streamlit as st

from core.estado import init_session_state, reset_state
from core.nlp import detectar_intencion, detectar_si_no, contiene_frase
from flujos.clasificar import procesar_clasificar
from flujos.explicar import procesar_explicar
from flujos.resolver import procesar_resolver, iniciar_resolver, procesar_elegir_metodo
from solvers import SOLVERS

st.set_page_config(
    page_title="Chatbot IO - DEMO",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_session_state()


def procesar_respuesta(entrada):
    if contiene_frase(entrada, ["cancelar", "salir"]):
        reset_state()
        return "Flujo cancelado. ¿Qué preferís: **Clasificar**, **Resolver** o **Explicar**?"

    # Bonus 2.2: pending tiene el método incorporado
    pending = st.session_state.get("pending_after_classification")
    if pending and pending.get("action") == "resolver":
        respuesta = detectar_si_no(entrada)
        if respuesta == "si":
            return iniciar_resolver(pending["metodo"])
        if respuesta == "no":
            st.session_state.pending_after_classification = None
            return "¡Entendido! Hablame si necesitas algo más."

    flow = st.session_state.current_flow

    if flow == "clasificar":
        return procesar_clasificar(entrada)
    if flow == "resolver":
        return procesar_resolver(entrada)
    if flow == "explicar":
        return procesar_explicar(entrada)
    if flow == "elegir_metodo_resolver":
        return procesar_elegir_metodo(entrada)
    if flow in SOLVERS:
        return SOLVERS[flow].procesar(entrada)

    intencion = detectar_intencion(entrada)

    if intencion == "saludo":
        return (
            "¡Hola! 👋 Soy tu asistente de IO. Puedo ayudarte a:\n"
            "1. **Clasificar** un modelo.\n"
            "2. **Resolver** un problema.\n"
            "3. **Explicar** conceptos.\n\n"
            "¿Por dónde empezamos?"
        )
    if intencion == "clasificar":
        st.session_state.current_flow = "clasificar"
        st.session_state.steps["clasificar"] = 0
        return procesar_clasificar("")
    if intencion == "resolver":
        return iniciar_resolver(None)
    if intencion == "explicar":
        st.session_state.current_flow = "explicar"
        st.session_state.steps["explicar"] = 0
        return procesar_explicar("")

    return (
        "No estoy seguro de qué necesitas. "
        "Probá diciendo: 'clasificar un modelo', 'resolver un problema' o 'explicar la teoría'."
    )


# --- UI ---
st.title("🤖 Chatbot de IO DEMO")
st.markdown("Me encargo de clasificar, resolver y explicar problemas de Investigación Operativa")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Escribe aquí tu consulta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    resp = procesar_respuesta(prompt)
    with st.chat_message("assistant"):
        st.markdown(resp)
    st.session_state.messages.append({"role": "assistant", "content": resp})
