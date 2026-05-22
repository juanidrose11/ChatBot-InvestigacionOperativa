import numpy as np
from scipy.optimize import linprog
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "combinaciones_lineales"
NOMBRE = "Método de Combinaciones Lineales"
DISPONIBLE = True


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
            vars_str = "\n".join([f"  x{i+1} = {result.x[i]:.4f}" for i in range(n)])

            obj_lines = []
            for i, (obj, tipo) in enumerate(zip(sd["objetivos"], sd["tipos"])):
                coefs = np.array(obj[:n])
                if len(coefs) < n:
                    coefs = np.pad(coefs, (0, n - len(coefs)))
                val = float(np.dot(coefs, result.x))
                obj_lines.append(f"  f{i+1}(x) = {val:.4f}  ({tipo}imizar, w={sd['pesos'][i]:.2f})")

            obj_str = "\n".join(obj_lines)
            peso_str = "  " + ",  ".join([f"w{i+1}={sd['pesos'][i]:.2f}" for i in range(sd["n_obj"])])

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
        nums = parsear_numeros(entrada)
        if not nums:
            return "No pude leer los coeficientes. Ej: `3, 5 minimizar`"
        tipo = "max" if contiene_frase(normalizar(entrada), ["max", "maximizar"]) else "min"
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
