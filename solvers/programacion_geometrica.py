import numpy as np
import cvxpy as cp
import streamlit as st

from core.nlp import parsear_numeros
from core.estado import reset_state

ID = "programacion_geometrica"
NOMBRE = "Programación Geométrica"
DISPONIBLE = True

# Formulación GP en forma estándar:
#
#   min  f_0(x) = Σ c_k · x1^a_k1 · x2^a_k2 · ... (posinomio)
#   s.t. f_i(x) ≤ b_i  para cada i  (posinomio ≤ constante positiva)
#        x_j > 0
#
# Cada monomio se ingresa como: "coef, exp_1, exp_2, ..., exp_n"
# Ej: "3, 2, -1" → 3 · x1^2 · x2^(-1)


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "Voy a ayudarte a resolver el problema de **Programación Geométrica**.\n\n"
        "La función objetivo es un **posinomio** (suma de monomios con coeficientes positivos).\n\n"
        "Formato de monomio: `coef, exp_1, exp_2, ...`\n"
        "Ej: `3, 2, -1` → 3·x₁²·x₂⁻¹\n\n"
        "**Todas las variables deben ser estrictamente positivas (x > 0).**\n\n"
        "¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
    )


def procesar(entrada):
    return _procesar(entrada)


def _parsear_monomio(texto, n):
    nums = parsear_numeros(texto)
    if not nums or len(nums) < 1:
        return None
    coef = nums[0]
    if coef <= 0:
        return None  # GP requiere coeficientes positivos en posinomios
    exps = (list(nums[1:]) + [0] * n)[:n]
    return coef, exps


def _construir_expresion(x, terminos):
    """Construye un posinomio cvxpy a partir de lista de (coef, exponents)."""
    expr = 0
    for coef, exps in terminos:
        mono = coef
        for j, a in enumerate(exps):
            if a != 0:
                mono = mono * x[j] ** a
        expr = expr + mono
    return expr


def _intentar_resolver(sd):
    try:
        n = sd["n_vars"]
        x = cp.Variable(n, pos=True)

        obj_expr = _construir_expresion(x, sd["terminos_obj"])
        obj = cp.Minimize(obj_expr)

        constraints = []
        for terminos, b in sd.get("restricciones", []):
            lhs = _construir_expresion(x, terminos)
            constraints.append(lhs <= b)

        prob = cp.Problem(obj, constraints)
        prob.solve(gp=True)

        if prob.status in ("optimal", "optimal_inaccurate"):
            x_opt = x.value
            vars_str = "\n".join(f"  x{i+1} = {x_opt[i]:.6f}" for i in range(n))

            # Grado de dificultad = términos totales - variables - 1
            n_terminos = len(sd["terminos_obj"]) + sum(len(t) for t, _ in sd.get("restricciones", []))
            grado = n_terminos - n - 1

            reset_state()
            return (
                f"✅ **¡Problema resuelto!**\n\n"
                f"**Variables óptimas:**\n{vars_str}\n\n"
                f"**Valor óptimo f(x*):** {float(prob.value):.6f}\n\n"
                f"**Grado de dificultad:** {grado} "
                f"({'solución directa (sistema lineal)' if grado == 0 else 'requirió optimización del dual'})\n\n"
                f"*Nota: cvxpy resuelve GP vía transformación log-convexa, garantizando el óptimo global.*\n\n"
                f"¿Querés resolver otro problema o necesitás algo más?"
            )
        else:
            reset_state()
            return (
                f"❌ Sin solución. Estado: `{prob.status}`\n\n"
                f"Verificá que todos los coeficientes sean positivos y que el problema sea factible."
            )
    except Exception as e:
        reset_state()
        return f"❌ Error al resolver: {str(e)}"


def _procesar(entrada):
    sd = st.session_state.solver_data
    step = st.session_state.solver_step

    if step == 0:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
        sd["n_vars"] = int(nums[0])
        st.session_state.solver_step = 1
        return f"¿Cuántos **monomios** tiene la función objetivo? (ej: `2`)"

    if step == 1:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántos monomios tiene el objetivo? (ej: `2`)"
        sd["n_terminos_obj"] = int(nums[0])
        sd["terminos_obj"] = []
        st.session_state.solver_step = 2
        n = sd["n_vars"]
        return (
            f"Ingresá el **monomio 1** del objetivo.\n\n"
            f"Formato: `coef, exp_1, exp_2, ..., exp_{n}` (coef debe ser positivo)\n\n"
            f"Ej: `3, 2, -1` → 3·x₁²·x₂⁻¹"
        )

    if 2 <= step < 2 + sd.get("n_terminos_obj", 0):
        n = sd["n_vars"]
        parsed = _parsear_monomio(entrada, n)
        if parsed is None:
            m = step - 1
            return (
                f"No pude leer el monomio. El coeficiente debe ser positivo.\n\n"
                f"Formato: `coef, exp_1, ..., exp_{n}` → Ingresá el **monomio {m}** nuevamente."
            )
        sd["terminos_obj"].append(parsed)
        st.session_state.solver_step += 1
        if len(sd["terminos_obj"]) < sd["n_terminos_obj"]:
            m = len(sd["terminos_obj"]) + 1
            return f"Monomio {len(sd['terminos_obj'])} registrado ✓\n\nIngresá el **monomio {m}** del objetivo:"
        sd["restricciones"] = []
        st.session_state.solver_step = 2 + sd["n_terminos_obj"]
        return "Función objetivo registrada ✓\n\n¿Cuántas **restricciones** tiene el problema? (`0` si no hay)"

    nrest_step = 2 + sd.get("n_terminos_obj", 0)
    if step == nrest_step:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones? (ej: `1` o `0`)"
        sd["n_restricciones"] = int(nums[0])
        sd["rest_actual"] = {"terminos": [], "n_terminos": 0}
        st.session_state.solver_step = nrest_step + 1
        if sd["n_restricciones"] == 0:
            return _intentar_resolver(sd)
        return (
            f"¿Cuántos **monomios** tiene la restricción 1? (ej: `2`)\n\n"
            f"Recordá que la restricción debe ser de la forma: posinomio ≤ constante"
        )

    if step > nrest_step:
        n = sd["n_vars"]
        rest = sd["rest_actual"]

        if rest["n_terminos"] == 0:
            nums = parsear_numeros(entrada)
            if not nums or int(nums[0]) < 1:
                return "¿Cuántos monomios tiene esta restricción? (ej: `2`)"
            rest["n_terminos"] = int(nums[0])
            rest["terminos"] = []
            st.session_state.solver_step += 1
            m_idx = len(sd["restricciones"]) + 1
            return f"Ingresá el **monomio 1** de la restricción {m_idx}.\n\nFormato: `coef, exp_1, ..., exp_{n}`"

        if len(rest["terminos"]) < rest["n_terminos"]:
            parsed = _parsear_monomio(entrada, n)
            if parsed is None:
                return f"Coeficiente debe ser positivo. Formato: `coef, exp_1, ..., exp_{n}`"
            rest["terminos"].append(parsed)
            st.session_state.solver_step += 1
            if len(rest["terminos"]) < rest["n_terminos"]:
                m = len(rest["terminos"]) + 1
                return f"Monomio {len(rest['terminos'])} registrado ✓\n\nIngresá el **monomio {m}**:"
            r_idx = len(sd["restricciones"]) + 1
            return f"Monomios de restricción {r_idx} completos ✓\n\n¿Cuál es la **cota** (b) de esta restricción? (ej: `4`)"

        # Leer la cota b
        nums = parsear_numeros(entrada)
        if not nums or nums[0] <= 0:
            return "La cota b debe ser un número positivo. Ej: `4`"
        b = nums[0]
        sd["restricciones"].append((list(rest["terminos"]), b))
        sd["rest_actual"] = {"terminos": [], "n_terminos": 0}
        st.session_state.solver_step += 1

        if len(sd["restricciones"]) < sd["n_restricciones"]:
            r_next = len(sd["restricciones"]) + 1
            return (
                f"Restricción {len(sd['restricciones'])} registrada ✓\n\n"
                f"¿Cuántos **monomios** tiene la restricción {r_next}?"
            )
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
