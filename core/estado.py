import streamlit as st


def reset_state():
    st.session_state.current_flow = "idle"
    st.session_state.steps = {"clasificar": 0, "resolver": 0, "explicar": 0}
    st.session_state.pending_after_classification = None
    st.session_state.guia_actual = []


def init_session_state():
    if "current_flow" not in st.session_state:
        reset_state()
    if "steps" not in st.session_state:
        st.session_state.steps = {"clasificar": 0, "resolver": 0, "explicar": 0}
    if "pending_after_classification" not in st.session_state:
        st.session_state.pending_after_classification = None
    if "guia_actual" not in st.session_state:
        st.session_state.guia_actual = []
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Soy tu asistente de IO. Enviame tu problema de IO y te ayudaré a resolverlo."}
        ]
    if "solver_data" not in st.session_state:
        st.session_state.solver_data = {}
    if "solver_step" not in st.session_state:
        st.session_state.solver_step = 0
