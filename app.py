import json
import re
import unicodedata

import streamlit as st
import numpy as np
from scipy.optimize import linprog


# Configuración de la página
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


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def contiene_frase(texto, frases):
    texto = normalizar(texto)
    return any(re.search(rf"\b{re.escape(normalizar(frase))}\b", texto) for frase in frases)



def parsear_numeros(texto):
    return [float(x) for x in re.findall(r'[-+]?\d*\.?\d+', texto)]


def parsear_restriccion(texto):
    texto_norm = texto.strip()
    if '<=' in texto_norm:
        signo = '<='
        partes = texto_norm.split('<=')
    elif '>=' in texto_norm:
        signo = '>='
        partes = texto_norm.split('>=')
    elif '=' in texto_norm:
        signo = '='
        partes = texto_norm.split('=')
    else:
        return None
    if len(partes) < 2:
        return None
    coefs = parsear_numeros(partes[0])
    rhs   = parsear_numeros(partes[1])
    if not coefs or not rhs:
        return None
    return (coefs, signo, rhs[0])


def resolver_combinaciones_lineales(sd):
    n = sd['n_vars']
    c = np.zeros(n)
    for obj, tipo, peso in zip(sd['objetivos'], sd['tipos'], sd['pesos']):
        coefs = np.array(obj[:n])
        if len(coefs) < n:
            coefs = np.pad(coefs, (0, n - len(coefs)))
        if tipo == 'max':
            coefs = -coefs      # convertimos max en min
        c += peso * coefs

    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for coefs, signo, rhs in sd.get('restricciones', []):
        row = list(coefs[:n]) + [0] * max(0, n - len(coefs))
        if signo == '<=':
            A_ub.append(row); b_ub.append(rhs)
        elif signo == '>=':
            A_ub.append([-x for x in row]); b_ub.append(-rhs)
        else:
            A_eq.append(row); b_eq.append(rhs)

    return linprog(
        c,
        A_ub=A_ub or None, b_ub=b_ub or None,
        A_eq=A_eq or None, b_eq=b_eq or None,
        bounds=[(0, None)] * n,
        method='highs'
    )


def intentar_resolver_combinaciones(sd):
    try:
        result = resolver_combinaciones_lineales(sd)
        if result.success:
            n = sd['n_vars']
            vars_str = "\n".join([f"  x{i+1} = {result.x[i]:.4f}" for i in range(n)])

            obj_lines = []
            for i, (obj, tipo) in enumerate(zip(sd['objetivos'], sd['tipos'])):
                coefs = np.array(obj[:n])
                if len(coefs) < n:
                    coefs = np.pad(coefs, (0, n - len(coefs)))
                val = float(np.dot(coefs, result.x))
                obj_lines.append(f"  f{i+1}(x) = {val:.4f}  ({tipo}imizar, w={sd['pesos'][i]:.2f})")

            obj_str  = "\n".join(obj_lines)
            peso_str = "  " + ",  ".join([f"w{i+1}={sd['pesos'][i]:.2f}" for i in range(sd['n_obj'])])

            reset_state()
            st.session_state.solver_data = {}
            st.session_state.solver_step = 0

            return (
                f"✅ **¡Problema resuelto!**\n\n"
                f"**Variables óptimas:**\n{vars_str}\n\n"
                f"**Valor de cada objetivo:**\n{obj_str}\n\n"
                f"**Pesos usados:**\n{peso_str}\n\n"
                f"¿Querés resolver otro problema o necesitás algo más?"
            )
        else:
            reset_state()
            return f"❌ El solver no encontró solución: `{result.message}`\n\nVerificá que el problema sea factible."
    except Exception as e:
        reset_state()
        return f"❌ Error al resolver: {str(e)}"


def procesar_solver_combinaciones(entrada):
    sd   = st.session_state.solver_data
    step = st.session_state.solver_step

    # Paso 0 — cantidad de variables
    if step == 0:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "No entendí. ¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
        sd['n_vars'] = int(nums[0])
        st.session_state.solver_step = 1
        return f"Perfecto, {sd['n_vars']} variables. ¿Cuántos **objetivos** querés combinar? (ej: `2`)"

    # Paso 1 — cantidad de objetivos
    if step == 1:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántos objetivos tiene el problema? (ej: `2`)"
        sd['n_obj']    = int(nums[0])
        sd['objetivos'] = []
        sd['tipos']     = []
        st.session_state.solver_step = 2
        return (
            f"Ingresá los coeficientes del **objetivo 1** separados por comas "
            f"e indicá si se **minimiza o maximiza**.\n\n"
            f"Ej: `3, 5 minimizar`"
        )

    # Pasos 2..2+n_obj-1 — coeficientes de cada objetivo
    if 2 <= step < 2 + sd.get('n_obj', 0):
        nums = parsear_numeros(entrada)
        if not nums:
            return "No pude leer los coeficientes. Ej: `3, 5 minimizar`"
        tipo = 'max' if contiene_frase(normalizar(entrada), ['max', 'maximizar']) else 'min'
        sd['objetivos'].append(nums)
        sd['tipos'].append(tipo)
        st.session_state.solver_step += 1

        if len(sd['objetivos']) < sd['n_obj']:
            num = len(sd['objetivos']) + 1
            return f"Objetivo {len(sd['objetivos'])} registrado ✓\n\nIngresá los coeficientes del **objetivo {num}** y si se minimiza o maximiza."
        return (
            f"Todos los objetivos registrados ✓\n\n"
            f"Ingresá los **pesos** para cada objetivo separados por comas (deben sumar 1).\n\n"
            f"Ej: `0.6, 0.4`"
        )

    # Paso pesos
    peso_step = 2 + sd.get('n_obj', 0)
    if step == peso_step:
        nums = parsear_numeros(entrada)
        if not nums or len(nums) < sd['n_obj']:
            return f"Necesito {sd['n_obj']} pesos. Ej: `0.6, 0.4`"
        total = sum(nums[:sd['n_obj']])
        pesos = [p / total for p in nums[:sd['n_obj']]]
        aviso = "" if abs(total - 1.0) < 0.01 else f"⚠️ Los pesos sumaban {total:.2f}, los normalicé automáticamente.\n\n"
        sd['pesos'] = pesos
        sd['restricciones'] = []
        st.session_state.solver_step += 1
        return aviso + "¿Cuántas **restricciones** tiene el problema? (escribí `0` si no hay)"

    # Paso cantidad de restricciones
    nrest_step = peso_step + 1
    if step == nrest_step:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones tiene? (ej: `2` o `0`)"
        sd['n_restricciones'] = int(nums[0])
        st.session_state.solver_step += 1
        if sd['n_restricciones'] == 0:
            return intentar_resolver_combinaciones(sd)
        return (
            f"Ingresá la **restricción 1** en este formato:\n"
            f"`coeficientes <= término_independiente`\n\n"
            f"Ej: `1, 2 <= 10`"
        )

    # Pasos recolección de restricciones
    if step > nrest_step:
        parsed = parsear_restriccion(entrada)
        if not parsed:
            n = len(sd['restricciones']) + 1
            return f"No pude leer la restricción. Usá el formato `1, 2 <= 10`\n\nIngresá la **restricción {n}** nuevamente."
        sd['restricciones'].append(parsed)
        st.session_state.solver_step += 1

        if len(sd['restricciones']) < sd['n_restricciones']:
            n = len(sd['restricciones']) + 1
            return f"Restricción {len(sd['restricciones'])} registrada ✓\n\nIngresá la **restricción {n}**:"
        return intentar_resolver_combinaciones(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."





# --- FORMATEO ---
def formatear_metodo(clave_metodo):
    metodos = conocimientos.get("metodos", {})
    data = metodos.get(clave_metodo)

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

    st.session_state.pending_after_classification = "resolver"
    st.session_state.ultimo_metodo = clave_metodo

    return f"""¡Clasificación lista! Te recomiendo usar: **{nombre}**.

**¿Por qué?**: {porque}

**Alcance**: {alcance}

**Supuesto**: {supuesto}

**Salida esperada**: {salida_esperada}{detalle_criterios}

¿Te gustaría que te ayude a **resolver** este problema?"""


# --- DETECCIÓN ---
def detectar_intencion(texto):
    if contiene_frase(texto, ["hola", "buenas", "que tal", "saludos"]):
        return "saludo"
    if contiene_frase(
        texto,
        [
            "clasificar",
            "diagnostico",
            "que metodo",
            "cual metodo",
            "recomendar",
            "identificar",
            "opcion 1",
        ]
    ):
        return "clasificar"
    if contiene_frase(
        texto,
        ["resolver", "ejercicio", "guia", "como se hace", "pasos", "resolucion", "opcion 2"],
    ):
        return "resolver"
    if contiene_frase(
        texto,
        ["explicar", "concepto", "que es", "entender", "definicion", "teoria", "opcion 3"],
    ):
        return "explicar"
    return "desconocido"


def detectar_si_no(texto):
    if contiene_frase(texto, ["si", "claro", "por supuesto", "dale", "ok", "correcto", "afirmativo"]):
        return "si"
    if contiene_frase(texto, ["no", "negativo", "para nada", "incorrecto"]):
        return "no"
    return None




def formatear_metodo_estocastico(criterio):
    data = conocimientos.get("metodos", {}).get("programacion_estocastica", {})

    st.session_state.ultimo_metodo = "programacion_estocastica"
    st.session_state.pending_after_classification = "resolver"

    return f"""¡Clasificación lista! Te recomiendo usar: **{data.get('nombre')}**.

**¿Por qué?**: {data.get('porque')}

**Criterio de decisión identificado**: {criterio}

**Alcance**: {data.get('alcance')}

**Supuesto**: {data.get('supuesto')}

**Criterios básicos de modelado**: {data.get('criterios_modelado')}

**Salida esperada**: {data.get('salida_esperada')}

¿Te gustaría que te ayude a **resolver** este problema?"""





# --- FLUJO CLASIFICAR (DIAGNÓSTICO) ---
def procesar_clasificar(entrada):
    step = st.session_state.step
    entrada_normalizada = normalizar(entrada)

    if step == 0:
        st.session_state.step = 1
        return "¿Tus parámetros son aleatorios o son fijos/conocidos de antemano?"

    respuesta = detectar_si_no(entrada)

    if step == 1:
        if contiene_frase(entrada, ["aleatorio", "aleatorios", "incierto", "inciertos", "incertidumbre"]):
            st.session_state.step = 7  # ← antes llamaba directo a formatear_metodo
            return "¿Conocés o podés estimar las **probabilidades o distribuciones** de los datos inciertos (demanda, costos, tiempos)?"
        if contiene_frase(entrada, ["fijo", "fijos", "deterministico", "deterministicos", "conocidos"]):
            st.session_state.step = 2
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
            st.session_state.step = 3
            return "¿Tus restricciones son lineales?"
        return "Por favor, indica si tienes varios objetivos/criterios para combinar o no."

    if step == 3:
        if respuesta == "si":
            st.session_state.step = 4
            return "¿Qué tipo de función objetivo tienes? ¿Cuadrática o no lineal compleja?"
        if respuesta == "no":
            st.session_state.step = 5
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
            st.session_state.step = 6
            return "¿Tu función y tus restricciones son convexas?"
        return "Responde si la función es polinómica/posinomial o no para continuar."

    if step == 6:
        reset_state()
        if respuesta == "si":
            return formatear_metodo("programacion_convexa")
        if respuesta == "no":
            return formatear_metodo("pnl_general")
        return "Por favor, responde si tu función y restricciones son convexas o no."

    #reset_state()
    #return "Reinicié el diagnóstico. Prueba diciendo: 'clasificar un modelo'."

    if step == 7:
        if respuesta == "si":
            st.session_state.step = 8
            return "¿Las decisiones principales deben tomarse **antes** de conocer el resultado aleatorio, y luego hay acciones correctivas posibles?"
        if respuesta == "no":
            st.session_state.step = 8
            return ("⚠️ Si no conocés las probabilidades, necesitarás estimarlas antes de modelar.\n\n"
                    "¿Las decisiones principales se toman **antes** de conocer el resultado aleatorio?")
        return "Respondé **sí** o **no**: ¿podés estimar probabilidades o distribuciones?"

    if step == 8:
        if respuesta == "si":
            st.session_state.step = 9
            return ("¿Cuál es tu **criterio de decisión** principal?\n\n"
                    "**1.** Minimizar el **costo esperado**\n"
                    "**2.** Minimizar el **riesgo** (varianza o pérdida máxima)\n"
                    "**3.** Una **combinación** de costo esperado y riesgo")
        if respuesta == "no":
            reset_state()
            return ("Si las decisiones se toman *después* de conocer todos los datos, "
                    "tu problema es **determinístico**.\n\n"
                    "Escribí **clasificar** para reiniciar el diagnóstico con parámetros fijos.")
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

# --- FLUJO RESOLVER ---
def procesar_resolver(_entrada):
    # Usá la guía cargada en sesión (específica del método)
    guia = st.session_state.get("guia_actual", [])
    
    # Si no hay guía en sesión (usuario entró directo sin clasificar),
    # usá la guía genérica como fallback
    if not guia:
        guias = conocimientos.get("guia_resolucion", {})
        guia = guias.get("default", [])

    step = st.session_state.step

    if not guia:
        reset_state()
        return "No encontré una guía de resolución cargada."

    if step < len(guia):
        item = guia[step]
        st.session_state.step += 1
        numero_paso = step + 1
        mensaje = f"**Paso {numero_paso}: {item.get('paso', 'Sin título')}**\n\n{item.get('descripcion', 'Sin descripción.')}"

        if st.session_state.step < len(guia):
            mensaje += "\n\n¿Continuamos con el siguiente paso?"
            return mensaje

        reset_state()
        return mensaje + "\n\n¡Eso completa la guía de resolución!"

    reset_state()
    return "Guía finalizada."


# --- FLUJO EXPLICAR ---
def procesar_explicar(entrada):
    conceptos = conocimientos.get("explicacion_conceptos", {})
    step = st.session_state.step

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
        st.session_state.step = 1
        return simple + "\n\n¿Te gustaría ver un **caso práctico**?"

    respuesta = detectar_si_no(entrada)

    if step == 1:
        if respuesta == "si":
            st.session_state.step = 2
            txt = caso_practico + "\n\n" + ejemplo_estandar
            return txt + "\n\n" + implicancia + "\n\n¿Necesitas un **nivel técnico** más alto (matemática formal)?"

        reset_state()
        return "¡Entendido! Hablame si necesitas algo más."

    if step == 2:
        if respuesta == "si":
            st.session_state.step = 3
            return matematica_formal + "\n\n¿Ha quedado clara la explicación?"

        reset_state()
        return "¡Entendido! Hablame si necesitas algo más."

    if step == 3:
        if respuesta == "si":
            reset_state()
            return "¡Entendido! Hablame si necesitas algo más."

        st.session_state.step = 3
        txt = matematica_formal + "\n\n" + resumen_simple
        return txt + "\n\n¿Ha quedado clara la explicación?"

    reset_state()
    return "Reinicié la explicación. Prueba diciendo: 'explicar un concepto'."


def reset_state():
    st.session_state.current_flow = "idle"
    st.session_state.step = 0


def iniciar_resolver():
    metodo = st.session_state.get("ultimo_metodo", "default")
    st.session_state.pending_after_classification = None

    if metodo == "combinaciones_lineales":
        st.session_state.current_flow = "solver_combinaciones"
        st.session_state.solver_step  = 0
        st.session_state.solver_data  = {}
        return (
            "¡Perfecto! Voy a pedirte los datos para resolver el problema.\n\n"
            "¿Cuántas **variables de decisión** tiene tu problema? (ej: `2`)"
        )

    guias       = conocimientos.get("guia_resolucion", {})
    guia_metodo = guias.get(metodo, guias.get("default", []))
    st.session_state.guia_actual   = guia_metodo
    st.session_state.current_flow  = "resolver"
    st.session_state.step          = 0
    return "Te guiaré paso a paso en el proceso de resolución:\n\n" + procesar_resolver("")


# --- LÓGICA PRINCIPAL ---
def procesar_respuesta(entrada):
    if contiene_frase(entrada, ["cancelar", "salir"]):
        reset_state()
        st.session_state.pending_after_classification = None
        return "Flujo cancelado. ¿Qué prefieres: **Clasificar**, **Resolver** o **Explicar**?"

    respuesta = detectar_si_no(entrada)
    if st.session_state.get("pending_after_classification") == "resolver":
        if respuesta == "si":
            return iniciar_resolver()
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
    if flow == "solver_combinaciones":
        return procesar_solver_combinaciones(entrada)


    intencion = detectar_intencion(entrada)

    if intencion == "saludo":
        return "¡Hola! 👋 Soy tu asistente de IO. Puedo ayudarte a:\n1. **Clasificar** un modelo.\n2. **Resolver** un problema.\n3. **Explicar** conceptos.\n\n¿Por dónde empezamos?"
    if intencion == "clasificar":
        st.session_state.current_flow = "clasificar"
        st.session_state.step = 0
        return procesar_clasificar("")
    if intencion == "resolver":
        return iniciar_resolver()
    if intencion == "explicar":
        st.session_state.current_flow = "explicar"
        st.session_state.step = 0
        return procesar_explicar("")

    return "No estoy seguro de qué necesitas. Prueba diciendo: 'ayúdame a clasificar un modelo', 'pasos para resolver un problema' o 'explícame la teoría'."


# UI
if "current_flow" not in st.session_state:
    reset_state()
if "pending_after_classification" not in st.session_state:
    st.session_state.pending_after_classification = None
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de IO. Enviame tu problema de IO y te ayudaré a resolverlo."}
    ]
if "solver_data" not in st.session_state:
    st.session_state.solver_data = {}
if "solver_step" not in st.session_state:
    st.session_state.solver_step = 0

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