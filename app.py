import streamlit as st
import json
import re

# config de la pagina
st.set_page_config(
    page_title="Chatbot IO - DEMO",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def cargar_conocimientos():
    try:
        with open("conocimientos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar la base de conocimientos: {e}")
        return {}

conocimientos = cargar_conocimientos()

# --- FORMATEO ---
def formatear_metodo(clave_metodo):
    metodos = conocimientos.get("metodos", {})
    if clave_metodo not in metodos:
        return "No tengo información detallada sobre ese método."
    data = metodos[clave_metodo]
    return f"""¡Clasificación lista! Te recomiendo usar: **{data['nombre']}**.

**¿Por qué?**: {data['porque']}\n
**Alcance**: {data['alcance']}\n
**Supuesto**: {data['supuesto']}\n
¿Te gustaría que te ayude a **resolver** este problema?""" #ESTO ANDA SOLO SI PONES "resolver"

# --- DETECCIÓN ---
def detectar_intencion(texto):
    texto = texto.lower()
    if any(p in texto for p in ["hola", "buenas", "qué tal", "que tal", "saludos"]):
        return "saludo"
    if any(p in texto for p in ["1", "clasificar", "diagnóstico", "diagnostico", "qué método", "cual método", "recomendar", "identificar"]):
        return "clasificar"
    if any(p in texto for p in ["2","resolver", "ejercicio", "guía", "guia", "cómo se hace", "pasos", "resolución"]):
        return "resolver"
    if any(p in texto for p in ["3","explicar", "concepto", "qué es", "que es", "entender", "definición", "teoría"]):
        return "explicar"
    return "desconocido"

def detectar_si_no(texto):
    texto = texto.lower()
    if any(p in texto for p in ["sí", "si", "claro", "por supuesto", "dale", "ok", "fijos", "antemano", "polinómica"]):
        return "si"
    if any(p in texto for p in ["no", "negativo", "para nada", "incierta"]):
        return "no"
    return None

# --- FLUJO CLASIFICAR (DIAGNÓSTICO) ---
def procesar_clasificar(entrada):
    step = st.session_state.step
    
    if step == 0:
        st.session_state.step = 1
        return "¿Tus parámetros son aleatorios o tienen incertidumbre?"
        
    respuesta = detectar_si_no(entrada)
    
    if step == 1:
        if "aleatorios" in entrada.lower() or "aleatorio" in entrada.lower():
            reset_state()
            return formatear_metodo("programacion_estocastica")
        elif "incertidumbre" in entrada.lower():
            st.session_state.step = 2
            return "¿Tus restricciones son lineales?"
        else:
            return "Por favor, indica si tus datos son aleatorios o fijos."
            
    if step == 2:
        if respuesta == "si":
            st.session_state.step = 3
            return "¿Qué tipo de función objetivo tienes? (¿Cuadrática o No lineal compleja?)"
        elif respuesta == "no":
            st.session_state.step = 4
            return "¿Tu función es Polinómica (posinomios)?"
        else:
            return "Por favor, indica si tus restricciones son lineales o no (Sí/No)."
            
    if step == 3: # Rama Lineal
        reset_state()
        if "cuadrática" in entrada.lower() or "cuadratica" in entrada.lower():
            return formatear_metodo("prog_cuadratica_wolfe")
        else:
            return formatear_metodo("frank_wolfe")
            
    if step == 4: # Rama No Lineal
        if respuesta == "si":
            reset_state()
            return formatear_metodo("programacion_geometrica")
        elif respuesta == "no":
            st.session_state.step = 5
            return "¿Tu función y restricciones son Convexas?"
        else:
            return "Responde si es polinómica o no para continuar."
            
    if step == 5:
        reset_state()
        if respuesta == "si":
            return formatear_metodo("programacion_convexa")
        else:
            return formatear_metodo("pnl_general")

# --- FLUJO RESOLVER --- esto no se che
def procesar_resolver(entrada):
    guia = conocimientos.get("guia_resolucion", [])
    step = st.session_state.step
    
    if step < len(guia):
        item = guia[step]
        st.session_state.step += 1
        mensaje = f"**Paso {step}: {item['paso']}**\n\n{item['descripcion']}"
        if st.session_state.step < len(guia):
            mensaje += "\n\n¿Continuamos con el siguiente paso?"
            return mensaje
        else:
            reset_state()
            return mensaje + "\n\n¡Eso completa la guía de resolución!"
    return "Guía finalizada."

# --- FLUJO EXPLICAR ---
def procesar_explicar(entrada):
    conceptos = conocimientos.get("explicacion_conceptos", {})
    step = st.session_state.step
    
    if step == 0:
        st.session_state.step = 1
        return conceptos["simple"] + "\n\n¿Te gustaría ver un **caso práctico**?"
        
    respuesta = detectar_si_no(entrada)

    if step == 1:
        st.session_state.step = 2
        if respuesta == "si":
            txt = conceptos["caso_practico"] + "\n" + conceptos["ejemplo_estandar"] 
            return txt + "\n\n" + conceptos["implicancia"] + "\n\n¿Necesitas un **nivel técnico** más alto (matemática formal)?"
        else:
            reset_state()
            return "¡Entendido! Hablame si necesitas algo mas."

    if step == 2:
        st.session_state.step = 3
        if respuesta == "si":
            txt = conceptos["matematica_formal"]
            return txt + "\n\n¿Ha quedado clara la explicación?"
        else:
            reset_state()
            return "¡Entendido! Hablame si necesitas algo mas."
            
    if step == 3:
        if respuesta == "si":
            reset_state()
            return "¡Entendido! Hablame si necesitas algo mas."
        else:
            st.session_state.step = 3
            txt = conceptos["matematica_formal"] + "\n" + conceptos["resumen_simple"]
            return txt + "\n\n¿Ha quedado clara la explicación?"


def reset_state():
    st.session_state.current_flow = "idle"
    st.session_state.step = 0

# --- LÓGICA PRINCIPAL ---
def procesar_respuesta(entrada):
    if "cancelar" in entrada.lower() or "salir" in entrada.lower():
        reset_state()
        return "Flujo cancelado. ¿Qué prefieres: **Clasificar**, **Resolver** o **Explicar**?"

    flow = st.session_state.current_flow
    
    if flow == "clasificar":
        return procesar_clasificar(entrada)
    elif flow == "resolver":
        return procesar_resolver(entrada)
    elif flow == "explicar":
        return procesar_explicar(entrada)
    
    # Detección de inicio
    intencion = detectar_intencion(entrada)
    
    if intencion == "saludo":
        return "¡Hola! 👋 Soy tu asistente de IO. Puedo ayudarte a:\n1. **Clasificar** un modelo.\n2. **Resolver** un problema.\n3. **Explicar** conceptos.\n\n¿Por dónde empezamos?"
    elif intencion == "clasificar":
        st.session_state.current_flow = "clasificar"
        st.session_state.step = 0
        return procesar_clasificar("")
    elif intencion == "resolver":
        st.session_state.current_flow = "resolver"
        st.session_state.step = 0
        return "Te guiaré paso a paso en el proceso de resolución:\n\n" + procesar_resolver("")
    elif intencion == "explicar":
        st.session_state.current_flow = "explicar"
        st.session_state.step = 0
        return procesar_explicar("")
    else:
        return "No estoy seguro de qué necesitas. Prueba diciendo: 'ayúdame a clasificar un modelo', 'pasos para resolver un problema' o 'explícame la teoría'."

# UI
if "current_flow" not in st.session_state: reset_state()
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu asistente de IO. Enviame tu problema de IO y te ayudare a resolverlo."}]

st.title("🤖 Chatbot de IO DEMO")
st.markdown("Me encargo de clasificar, resolver y explicar problemas de Investigación Operativa")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribe aquí tu consulta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    resp = procesar_respuesta(prompt)
    with st.chat_message("assistant"): st.markdown(resp)
    st.session_state.messages.append({"role": "assistant", "content": resp})