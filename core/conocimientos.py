import json
import streamlit as st


def cargar_conocimientos():
    try:
        with open("conocimientos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar la base de conocimientos: {e}")
        return {}


conocimientos = cargar_conocimientos()


def formatear_metodo(clave_metodo):
    data = conocimientos.get("metodos", {}).get(clave_metodo)
    if not data:
        return "No tengo información detallada sobre ese método."

    nombre = data.get("nombre", "Método no especificado")
    porque = data.get("porque", "No hay una justificación cargada.")
    alcance = data.get("alcance", "No hay alcance cargado.")
    supuesto = data.get("supuesto", "No hay supuesto cargado.")
    criterios_modelado = data.get("criterios_modelado")
    salida_esperada = data.get("salida_esperada", "No hay salida esperada cargada.")

    detalle_criterios = ""
    if criterios_modelado:
        detalle_criterios = f"\n\n**Criterios básicos de modelado**: {criterios_modelado}"

    # Bonus 2.2: pending con el método ya incorporado
    st.session_state.pending_after_classification = {"action": "resolver", "metodo": clave_metodo}

    return (
        f"¡Clasificación lista! Te recomiendo usar: **{nombre}**.\n\n"
        f"**¿Por qué?**: {porque}\n\n"
        f"**Alcance**: {alcance}\n\n"
        f"**Supuesto**: {supuesto}\n\n"
        f"**Salida esperada**: {salida_esperada}{detalle_criterios}\n\n"
        f"¿Te gustaría que te ayude a **resolver** este problema?"
    )


def formatear_metodo_estocastico(criterio):
    data = conocimientos.get("metodos", {}).get("programacion_estocastica", {})

    st.session_state.pending_after_classification = {"action": "resolver", "metodo": "programacion_estocastica"}

    return (
        f"¡Clasificación lista! Te recomiendo usar: **{data.get('nombre')}**.\n\n"
        f"**¿Por qué?**: {data.get('porque')}\n\n"
        f"**Criterio de decisión identificado**: {criterio}\n\n"
        f"**Alcance**: {data.get('alcance')}\n\n"
        f"**Supuesto**: {data.get('supuesto')}\n\n"
        f"**Criterios básicos de modelado**: {data.get('criterios_modelado')}\n\n"
        f"**Salida esperada**: {data.get('salida_esperada')}\n\n"
        f"¿Te gustaría que te ayude a **resolver** este problema?"
    )
