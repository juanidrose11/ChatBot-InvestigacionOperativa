import numpy as np
import sympy as sp
from scipy.optimize import minimize
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "pnl_general"
NOMBRE = "PNL General"
DISPONIBLE = True


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "Voy a ayudarte a resolver el problema de **Programación No Lineal General**.\n\n"
        "Podés ingresar cualquier función diferenciable. Las variables se llaman **x1, x2, ..., xn**.\n\n"
        "¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
    )


def procesar(entrada):
    return _procesar(entrada)


def _parsear_expresion(texto, n):
    variables = [sp.Symbol(f"x{i+1}") for i in range(n)]
    try:
        expr = sp.sympify(texto.replace("^", "**"))
        validas = {sp.Symbol(f"x{i+1}") for i in range(n)}
        if not expr.free_symbols.issubset(validas):
            return None, None, None
        return sp.lambdify(variables, expr, "numpy"), expr, variables
    except Exception:
        return None, None, None


def _intentar_resolver(sd):
    try:
        n = sd["n_vars"]
        tipo = sd["tipo"]
        f_call = sd["f_callable"]
        expr = sd["expr"]
        variables = sd["variables"]

        grad_exprs = [sp.diff(expr, xi) for xi in variables]
        grad_lam = sp.lambdify(variables, grad_exprs, "numpy")

        def obj(x):
            v = float(f_call(*x))
            return -v if tipo == "max" else v

        def jac(x):
            raw = grad_lam(*x)
            g = np.array([float(r) if np.isscalar(r) else float(np.asarray(r).flat[0]) for r in raw])
            return -g if tipo == "max" else g

        scipy_constraints = []
        for coefs, signo, rhs in sd.get("restricciones", []):
            row = np.array((list(coefs) + [0] * n)[:n])
            if signo == "<=":
                scipy_constraints.append({"type": "ineq", "fun": lambda x, r=row, b=rhs: b - r @ x})
            elif signo == ">=":
                scipy_constraints.append({"type": "ineq", "fun": lambda x, r=row, b=rhs: r @ x - b})
            else:
                scipy_constraints.append({"type": "eq", "fun": lambda x, r=row, b=rhs: r @ x - b})

        bounds = [(0, None)] * n
        n_starts = sd.get("n_starts", 3)

        np.random.seed(42)
        starts = [np.zeros(n)] + [np.random.uniform(0, 5, n) for _ in range(n_starts - 1)]

        best_result = None
        best_val = float("inf") if tipo == "min" else float("-inf")

        for x0 in starts:
            try:
                res = minimize(obj, x0, jac=jac, method="SLSQP",
                               bounds=bounds, constraints=scipy_constraints,
                               options={"maxiter": 1000, "ftol": 1e-9})
                if res.success:
                    val = float(f_call(*res.x))
                    if (tipo == "min" and val < best_val) or (tipo == "max" and val > best_val):
                        best_val = val
                        best_result = res
            except Exception:
                continue

        if best_result is not None:
            vars_str = "\n".join(f"  x{i+1} = {best_result.x[i]:.4f}" for i in range(n))
            reset_state()
            return (
                f"✅ **¡Problema resuelto!**\n\n"
                f"**Variables óptimas:**\n{vars_str}\n\n"
                f"**Valor óptimo f(x):** {best_val:.4f}\n\n"
                f"⚠️ *PNL General puede tener múltiples óptimos locales. "
                f"Se exploraron {n_starts} puntos de inicio distintos.*\n\n"
                f"¿Querés resolver otro problema o necesitás algo más?"
            )
        else:
            reset_state()
            return "❌ No se encontró solución factible. Verificá la expresión y las restricciones."
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
        return "¿Querés **minimizar** o **maximizar** la función objetivo?"

    if step == 1:
        sd["tipo"] = "max" if contiene_frase(normalizar(entrada), ["max", "maximizar"]) else "min"
        n = sd["n_vars"]
        st.session_state.solver_step = 2
        return (
            f"Ingresá la **función objetivo** usando x1...x{n}.\n\n"
            f"Operadores: `+`, `-`, `*`, `/`, `**` (potencia), `sqrt()`, `log()`, `exp()`.\n\n"
            f"Ejemplo: `x1**2 + 3*x1*x2 - 2*x2`"
        )

    if step == 2:
        n = sd["n_vars"]
        f_call, expr, variables = _parsear_expresion(entrada, n)
        if f_call is None:
            return (
                f"No pude interpretar la expresión. Usá x1...x{n} con operadores Python.\n\n"
                f"Ejemplo: `x1**2 + 3*x1*x2 - 2*x2`"
            )
        sd["f_callable"] = f_call
        sd["expr"] = expr
        sd["variables"] = variables
        st.session_state.solver_step = 3
        return (
            f"Función registrada: **f(x) = {expr}** ✓\n\n"
            f"¿Cuántos **puntos de inicio** querés explorar? (recomendado: `3`, más = más robusto)\n\n"
            f"Ej: `3`"
        )

    if step == 3:
        nums = parsear_numeros(entrada)
        sd["n_starts"] = max(1, int(nums[0])) if nums else 3
        sd["restricciones"] = []
        st.session_state.solver_step = 4
        return "¿Cuántas **restricciones lineales** tiene el problema? (`0` si no hay)"

    if step == 4:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones tiene? (ej: `2` o `0`)"
        sd["n_restricciones"] = int(nums[0])
        st.session_state.solver_step = 5
        if sd["n_restricciones"] == 0:
            return _intentar_resolver(sd)
        return "Ingresá la **restricción 1** en formato `coefs <= b`.\n\nEj: `1, 2 <= 10`"

    if step >= 5:
        parsed = parsear_restriccion(entrada)
        if not parsed:
            n_r = len(sd.get("restricciones", [])) + 1
            return f"No pude leer la restricción. Usá `1, 2 <= 10`\n\nIngresá la **restricción {n_r}** nuevamente."
        sd.setdefault("restricciones", []).append(parsed)
        st.session_state.solver_step += 1
        if len(sd["restricciones"]) < sd["n_restricciones"]:
            n_r = len(sd["restricciones"]) + 1
            return f"Restricción {len(sd['restricciones'])} registrada ✓\n\nIngresá la **restricción {n_r}**:"
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
