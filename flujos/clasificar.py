import streamlit as st
from core.nlp import contiene_frase, detectar_si_no, normalizar
from core.conocimientos import formatear_metodo, formatear_metodo_estocastico
from core.estado import reset_state


def procesar_clasificar(entrada):
    step = st.session_state.steps["clasificar"]
    entrada_normalizada = normalizar(entrada)

    if step == 0:
        st.session_state.steps["clasificar"] = 1
        return "¿Tus parámetros son aleatorios o son fijos/conocidos de antemano?"

    respuesta = detectar_si_no(entrada)

    if step == 1:
        if contiene_frase(entrada, ["aleatorio", "aleatorios", "incierto", "inciertos", "incertidumbre"]):
            st.session_state.steps["clasificar"] = 7
            return "¿Conocés o podés estimar las **probabilidades o distribuciones** de los datos inciertos (demanda, costos, tiempos)?"
        if contiene_frase(entrada, ["fijo", "fijos", "deterministico", "deterministicos", "conocidos"]):
            st.session_state.steps["clasificar"] = 2
            return "¿Tu problema tiene varios objetivos o criterios que quieras combinar con pesos?"
        return "Por favor, indicá si tus datos son aleatorios o fijos/conocidos."

    if step == 2:
        if respuesta == "si" or contiene_frase(
            entrada,
            ["varios objetivos", "multiobjetivo", "multicriterio", "pesos", "ponderaciones", "combinacion lineal"],
        ):
            reset_state()
            return formatear_metodo("combinaciones_lineales")
        if respuesta == "no":
            st.session_state.steps["clasificar"] = 3
            return "¿Tus restricciones son lineales?"
        return "Por favor, indica si tienes varios objetivos/criterios para combinar o no."

    if step == 3:
        if respuesta == "si":
            st.session_state.steps["clasificar"] = 4
            return "¿Qué tipo de función objetivo tienes? ¿Cuadrática o no lineal compleja?"
        if respuesta == "no":
            st.session_state.steps["clasificar"] = 5
            return "¿Tu función es polinómica o está formada por posinomios?"
        return "Por favor, indica si tus restricciones son lineales o no."

    if step == 4:
        reset_state()
        if "cuadratica" in entrada_normalizada:
            return formatear_metodo("prog_cuadratica_wolfe")
        return formatear_metodo("frank_wolfe")

    if step == 5:
        if respuesta == "si" or contiene_frase(entrada, ["polinomica", "posinomio", "posinomios"]):
            reset_state()
            return formatear_metodo("programacion_geometrica")
        if respuesta == "no":
            st.session_state.steps["clasificar"] = 6
            return "¿Tu función y tus restricciones son convexas?"
        return "Responde si la función es polinómica/posinomial o no para continuar."

    if step == 6:
        reset_state()
        if respuesta == "si":
            return formatear_metodo("programacion_convexa")
        if respuesta == "no":
            return formatear_metodo("pnl_general")
        return "Por favor, responde si tu función y restricciones son convexas o no."

    if step == 7:
        if respuesta == "si":
            st.session_state.steps["clasificar"] = 8
            return "¿Las decisiones principales deben tomarse **antes** de conocer el resultado aleatorio, y luego hay acciones correctivas posibles?"
        if respuesta == "no":
            st.session_state.steps["clasificar"] = 8
            return (
                "⚠️ Si no conocés las probabilidades, necesitarás estimarlas antes de modelar.\n\n"
                "¿Las decisiones principales se toman **antes** de conocer el resultado aleatorio?"
            )
        return "Respondé **sí** o **no**: ¿podés estimar probabilidades o distribuciones?"

    if step == 8:
        if respuesta == "si":
            st.session_state.steps["clasificar"] = 9
            return (
                "¿Cuál es tu **criterio de decisión** principal?\n\n"
                "**1.** Minimizar el **costo esperado**\n"
                "**2.** Minimizar el **riesgo** (varianza o pérdida máxima)\n"
                "**3.** Una **combinación** de costo esperado y riesgo"
            )
        if respuesta == "no":
            reset_state()
            return (
                "Si las decisiones se toman *después* de conocer todos los datos, "
                "tu problema es **determinístico**.\n\n"
                "Escribí **clasificar** para reiniciar el diagnóstico con parámetros fijos."
            )
        return "Respondé **sí** o **no**: ¿las decisiones se toman antes de conocer el resultado?"

    if step == 9:
        if contiene_frase(entrada, ["1", "costo esperado", "costo", "esperado"]):
            criterio = "Minimizar el **costo esperado** sobre todos los escenarios"
        elif contiene_frase(entrada, ["2", "riesgo", "varianza", "perdida"]):
            criterio = "Minimizar el **riesgo** (varianza o pérdida máxima)"
        elif contiene_frase(entrada, ["3", "combinacion", "ambos"]):
            criterio = "**Combinación ponderada** de costo esperado y riesgo"
        else:
            return "Elegí una opción: **1** (costo esperado), **2** (riesgo) o **3** (combinación)."

        reset_state()
        return formatear_metodo_estocastico(criterio)

    reset_state()
    return "Reinicié el diagnóstico. Prueba diciendo: 'clasificar un modelo'."
