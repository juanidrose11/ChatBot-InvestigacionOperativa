import re

import numpy as np
from scipy.optimize import linprog
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "combinaciones_lineales"
NOMBRE = "Método de Combinaciones Lineales"
DISPONIBLE = True

PATRON_NUMERO = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"


def _parsear_objetivo(entrada, n):
    tipo = "max" if contiene_frase(entrada, ["max", "maximizar"]) else "min"
    texto = normalizar(entrada)
    texto = re.sub(r"\b(maximizar|max|minimizar|min)\b", "", texto)
    texto = texto.replace(",", " ")
    partes = texto.split()

    if len(partes) != n:
        return None, tipo

    coefs = []
    for parte in partes:
        if not re.fullmatch(PATRON_NUMERO, parte):
            return None, tipo
        coefs.append(float(parte))

    return coefs, tipo


def _formatear_numero(valor, max_decimales=4):
    valor = float(valor)
    if abs(valor) < 1e-10:
        valor = 0.0

    texto = f"{valor:.{max_decimales}f}".rstrip("0").rstrip(".")
    return texto if texto and texto != "-0" else "0"


def _restriccion_cumple(lhs, signo, rhs):
    tol = 1e-7
    if signo == "<=":
        return lhs <= rhs + tol
    if signo == ">=":
        return lhs >= rhs - tol
    return abs(lhs - rhs) <= tol


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "¡Perfecto! Voy a pedirte los datos para resolver el problema.\n\n"
        "¿Cuántas **variables de decisión** tiene tu problema? (ej: `2`)"
    )


def procesar(entrada):
    return _procesar(entrada)


def _resolver(sd):
    n = sd["n_vars"]
    c = np.zeros(n)
    for obj, tipo, peso in zip(sd["objetivos"], sd["tipos"], sd["pesos"]):
        coefs = np.array(obj[:n])
        if len(coefs) < n:
            coefs = np.pad(coefs, (0, n - len(coefs)))
        if tipo == "max":
            coefs = -coefs
        c += peso * coefs

    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for coefs, signo, rhs in sd.get("restricciones", []):
        row = list(coefs[:n]) + [0] * max(0, n - len(coefs))
        if signo == "<=":
            A_ub.append(row)
            b_ub.append(rhs)
        elif signo == ">=":
            A_ub.append([-x for x in row])
            b_ub.append(-rhs)
        else:
            A_eq.append(row)
            b_eq.append(rhs)

    return linprog(
        c,
        A_ub=A_ub or None,
        b_ub=b_ub or None,
        A_eq=A_eq or None,
        b_eq=b_eq or None,
        bounds=[(0, None)] * n,
        method="highs",
    )


def _intentar_resolver(sd):
    try:
        result = _resolver(sd)
        if result.success:
            n = sd["n_vars"]
            vars_str = "\n".join([f"  x{i+1} = {_formatear_numero(result.x[i])}" for i in range(n)])

            obj_lines = []
            objetivos_contexto = []
            for i, (obj, tipo) in enumerate(zip(sd["objetivos"], sd["tipos"])):
                coefs = np.array(obj[:n])
                if len(coefs) < n:
                    coefs = np.pad(coefs, (0, n - len(coefs)))
                val = float(np.dot(coefs, result.x))
                objetivos_contexto.append({
                    "valor": val,
                    "tipo": tipo,
                    "peso": float(sd["pesos"][i]),
                })
                obj_lines.append(
                    f"  f{i+1}(x) = {_formatear_numero(val)}  "
                    f"({tipo}imizar, w={_formatear_numero(sd['pesos'][i], 2)})"
                )

            obj_str = "\n".join(obj_lines)
            peso_str = "  " + ",  ".join(
                [f"w{i+1}={_formatear_numero(sd['pesos'][i], 2)}" for i in range(sd["n_obj"])]
            )
            restricciones_contexto = []
            for coefs, signo, rhs in sd.get("restricciones", []):
                row = np.array((list(coefs) + [0] * n)[:n], dtype=float)
                lhs = float(row @ result.x)
                restricciones_contexto.append({
                    "lhs": lhs,
                    "signo": signo,
                    "rhs": float(rhs),
                    "cumple": _restriccion_cumple(lhs, signo, float(rhs)),
                })

            st.session_state.last_solution_context = {
                "metodo": ID,
                "variables": [float(v) for v in result.x[:n]],
                "objetivos": objetivos_contexto,
                "restricciones": restricciones_contexto,
            }

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


def _procesar(entrada):
    sd = st.session_state.solver_data
    step = st.session_state.solver_step

    if step == 0:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "No entendí. ¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
        sd["n_vars"] = int(nums[0])
        st.session_state.solver_step = 1
        return f"Perfecto, {sd['n_vars']} variables. ¿Cuántos **objetivos** querés combinar? (ej: `2`)"

    if step == 1:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántos objetivos tiene el problema? (ej: `2`)"
        sd["n_obj"] = int(nums[0])
        sd["objetivos"] = []
        sd["tipos"] = []
        st.session_state.solver_step = 2
        return (
            f"Ingresá los coeficientes del **objetivo 1** separados por comas "
            f"e indicá si se **minimiza o maximiza**.\n\n"
            f"Ej: `3, 5 minimizar`"
        )

    if 2 <= step < 2 + sd.get("n_obj", 0):
        nums, tipo = _parsear_objetivo(entrada, sd["n_vars"])
        if nums is None:
            return (
                f"Los coeficientes deben ser solo números y tienen que ser exactamente "
                f"{sd['n_vars']} valores.\n\n"
                f"Ej: `3, 5 minimizar`"
            )
        sd["objetivos"].append(nums)
        sd["tipos"].append(tipo)
        st.session_state.solver_step += 1
        if len(sd["objetivos"]) < sd["n_obj"]:
            num = len(sd["objetivos"]) + 1
            return f"Objetivo {len(sd['objetivos'])} registrado ✓\n\nIngresá los coeficientes del **objetivo {num}** y si se minimiza o maximiza."
        return (
            f"Todos los objetivos registrados ✓\n\n"
            f"Ingresá los **pesos** para cada objetivo separados por comas (deben sumar 1).\n\n"
            f"Ej: `0.6, 0.4`"
        )

    peso_step = 2 + sd.get("n_obj", 0)
    if step == peso_step:
        nums = parsear_numeros(entrada)
        if not nums or len(nums) < sd["n_obj"]:
            return f"Necesito {sd['n_obj']} pesos. Ej: `0.6, 0.4`"
        total = sum(nums[: sd["n_obj"]])
        pesos = [p / total for p in nums[: sd["n_obj"]]]
        aviso = "" if abs(total - 1.0) < 0.01 else f"⚠️ Los pesos sumaban {total:.2f}, los normalicé automáticamente.\n\n"
        sd["pesos"] = pesos
        sd["restricciones"] = []
        st.session_state.solver_step += 1
        return aviso + "¿Cuántas **restricciones** tiene el problema? (escribí `0` si no hay)"

    nrest_step = peso_step + 1
    if step == nrest_step:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones tiene? (ej: `2` o `0`)"
        sd["n_restricciones"] = int(nums[0])
        st.session_state.solver_step += 1
        if sd["n_restricciones"] == 0:
            return _intentar_resolver(sd)
        return (
            f"Ingresá la **restricción 1** en este formato:\n"
            f"`coeficientes <= término_independiente`\n\n"
            f"Ej: `1, 2 <= 10`"
        )

    if step > nrest_step:
        parsed = parsear_restriccion(entrada)
        if not parsed:
            n = len(sd["restricciones"]) + 1
            return f"No pude leer la restricción. Usá el formato `1, 2 <= 10`\n\nIngresá la **restricción {n}** nuevamente."
        sd["restricciones"].append(parsed)
        st.session_state.solver_step += 1
        if len(sd["restricciones"]) < sd["n_restricciones"]:
            n = len(sd["restricciones"]) + 1
            return f"Restricción {len(sd['restricciones'])} registrada ✓\n\nIngresá la **restricción {n}**:"
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
