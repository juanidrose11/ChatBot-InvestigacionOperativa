import streamlit as st

from core.estado import MENU_INICIAL, init_session_state, reset_state
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

FRASES_VOLVER_MENU = [
    "cancelar",
    "salir",
    "volver al menu",
    "volver al menu inicial",
    "volvamos al menu",
    "volvamos al menu inicial",
    "menu inicial",
    "ir al menu",
    "ir al menu inicial",
    "reiniciar",
]


def _formatear_numero(valor, max_decimales=4):
    valor = float(valor)
    if abs(valor) < 1e-10:
        valor = 0.0

    texto = f"{valor:.{max_decimales}f}".rstrip("0").rstrip(".")
    return texto if texto and texto != "-0" else "0"


def _quiere_interpretar_resultado(entrada):
    return contiene_frase(
        entrada,
        [
            "que significa",
            "significa",
            "interpretar",
            "interpretame",
            "explicar resultado",
            "explicame resultado",
            "resultado",
            "resultados",
            "solucion de compromiso",
            "compromiso",
            "solucion optima",
            "por que",
        ],
    )


def _explicar_ultimo_resultado():
    contexto = st.session_state.get("last_solution_context")
    if not contexto:
        return None

    if contexto.get("metodo") != "combinaciones_lineales":
        return None

    variables = contexto.get("variables", [])
    objetivos = contexto.get("objetivos", [])
    restricciones = contexto.get("restricciones", [])

    variables_txt = ", ".join(
        f"x{i+1}={_formatear_numero(valor)}" for i, valor in enumerate(variables)
    )
    objetivos_txt = "\n".join(
        f"- f{i+1}(x) = {_formatear_numero(obj['valor'])} "
        f"({'minimizar' if obj['tipo'] == 'min' else 'maximizar'}, "
        f"peso w{i+1}={_formatear_numero(obj['peso'], 2)})"
        for i, obj in enumerate(objetivos)
    )

    if restricciones:
        restricciones_txt = "\n".join(
            f"- R{i+1}: {_formatear_numero(rest['lhs'])} {rest['signo']} "
            f"{_formatear_numero(rest['rhs'])} "
            f"({'se cumple' if rest['cumple'] else 'no se cumple'})"
            for i, rest in enumerate(restricciones)
        )
    else:
        restricciones_txt = "- No se cargaron restricciones adicionales; se mantienen las cotas x >= 0."

    return (
        f"La solución **{variables_txt}** significa que esos son los valores óptimos "
        f"que debe tomar cada variable de decisión para el modelo que cargaste.\n\n"
        f"Están dentro de la **región factible** porque satisfacen las restricciones:\n"
        f"{restricciones_txt}\n\n"
        f"En este punto, los objetivos quedan así:\n{objetivos_txt}\n\n"
        f"Es una **solución de compromiso** porque el problema tiene más de un objetivo: "
        f"no se eligió optimizar un único criterio aislado, sino una combinación ponderada. "
        f"Los pesos reflejan la importancia relativa de cada objetivo; por ejemplo, un peso "
        f"más alto hace que ese objetivo tenga más influencia en la solución final."
    )


def procesar_respuesta(entrada):
    if contiene_frase(entrada, FRASES_VOLVER_MENU):
        reset_state()
        return "Volvimos al menú inicial.\n\n" + MENU_INICIAL

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

    if _quiere_interpretar_resultado(entrada):
        explicacion = _explicar_ultimo_resultado()
        if explicacion:
            return explicacion

    intencion = detectar_intencion(entrada)

    if intencion == "saludo":
        return MENU_INICIAL
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
