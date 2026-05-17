import numpy as np
import sympy as sp
from scipy.optimize import linprog, minimize_scalar
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "frank_wolfe"
NOMBRE = "Método de Frank-Wolfe"
DISPONIBLE = True

# Algoritmo Frank-Wolfe (Conditional Gradient Method):
#
#   Resuelve: min f(x) s.t. x ∈ P  (P poliedro convexo definido por Ax ≤ b, x ≥ 0)
#
#   Iteración k:
#     1. Computar ∇f(xᵏ)
#     2. Resolver subproblema LP: dᵏ = argmin ∇f(xᵏ)ᵀ d  s.t. d ∈ P
#     3. Búsqueda de línea: αᵏ = argmin f(xᵏ + α(dᵏ - xᵏ))  para α ∈ [0,1]
#     4. xᵏ⁺¹ = xᵏ + αᵏ(dᵏ - xᵏ)
#     5. Gap de dualidad: g = ∇f(xᵏ)ᵀ(xᵏ - dᵏ) ≥ 0  → convergió si g < ε


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "Voy a resolver el problema con el **Método de Frank-Wolfe** (Gradiente Condicional).\n\n"
        "El método resuelve min f(x) s.t. x ∈ P, donde f es diferenciable y P es un poliedro "
        "(restricciones lineales). Mostraré **cada iteración** del algoritmo.\n\n"
        "Las variables se llaman **x1, x2, ..., xn**.\n\n"
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


def _correr_frank_wolfe(sd):
    n = sd["n_vars"]
    f_call = sd["f_callable"]
    expr = sd["expr"]
    variables = sd["variables"]
    x0 = np.array(sd["x0"], dtype=float)
    tol = sd.get("tol", 1e-4)
    max_iter = sd.get("max_iter", 20)

    grad_exprs = [sp.diff(expr, xi) for xi in variables]
    grad_lam = sp.lambdify(variables, grad_exprs, "numpy")

    def grad(x):
        raw = grad_lam(*x)
        return np.array([float(r) if np.isscalar(r) else float(np.asarray(r).flat[0]) for r in raw])

    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for coefs, signo, rhs in sd.get("restricciones", []):
        row = (list(coefs) + [0] * n)[:n]
        if signo == "<=":
            A_ub.append(row); b_ub.append(rhs)
        elif signo == ">=":
            A_ub.append([-v for v in row]); b_ub.append(-rhs)
        else:
            A_eq.append(row); b_eq.append(rhs)

    x = x0.copy()
    iteraciones = []

    for k in range(max_iter):
        g = grad(x)
        f_val = float(f_call(*x))

        lp = linprog(
            g,
            A_ub=A_ub or None, b_ub=b_ub or None,
            A_eq=A_eq or None, b_eq=b_eq or None,
            bounds=[(0, None)] * n,
            method="highs",
        )
        if not lp.success:
            break

        d = lp.x
        gap = float(g @ (x - d))  # dualidad: ≥ 0, = 0 en óptimo

        direction = d - x
        ls = minimize_scalar(
            lambda alpha: float(f_call(*(x + alpha * direction))),
            bounds=(0, 1),
            method="bounded",
        )
        alpha = float(ls.x)
        x_new = x + alpha * direction

        iteraciones.append({
            "k": k + 1,
            "x": x.copy(),
            "f": f_val,
            "grad": g.copy(),
            "d": d.copy(),
            "alpha": alpha,
            "gap": gap,
        })

        x = x_new

        if gap < tol:
            break

    return x, iteraciones


def _intentar_resolver(sd):
    try:
        x_opt, iteraciones = _correr_frank_wolfe(sd)
        n = sd["n_vars"]

        # Resumen de iteraciones
        tabla = ["| Iter | f(xᵏ) | Gap |", "|------|--------|-----|"]
        for it in iteraciones:
            tabla.append(f"| {it['k']} | {it['f']:.4f} | {it['gap']:.6f} |")

        # Detalle de las últimas iteraciones (máx 5)
        detalle = []
        for it in iteraciones[-min(5, len(iteraciones)):]:
            x_str = ", ".join(f"x{i+1}={v:.4f}" for i, v in enumerate(it["x"]))
            g_str = ", ".join(f"{v:.4f}" for v in it["grad"])
            d_str = ", ".join(f"{v:.4f}" for v in it["d"])
            detalle.append(
                f"**It {it['k']}:** {x_str} → ∇f=[{g_str}], d*=[{d_str}], α={it['alpha']:.4f}, gap={it['gap']:.6f}"
            )

        vars_str = "\n".join(f"  x{i+1} = {x_opt[i]:.4f}" for i in range(n))
        f_opt = float(sd["f_callable"](*x_opt))
        n_iter = len(iteraciones)
        gap_final = iteraciones[-1]["gap"] if iteraciones else 0

        reset_state()
        return (
            f"✅ **¡Frank-Wolfe completado!** ({n_iter} iteraciones)\n\n"
            f"**Variables finales:**\n{vars_str}\n\n"
            f"**f(x*):** {f_opt:.4f} | **Gap final:** {gap_final:.6f}\n\n"
            f"**Historial (todas las iteraciones):**\n" + "\n".join(tabla)
            + "\n\n**Últimas iteraciones con detalle:**\n" + "\n".join(detalle)
            + "\n\n¿Querés resolver otro problema o necesitás algo más?"
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
        n = sd["n_vars"]
        st.session_state.solver_step = 1
        return (
            f"Ingresá la **función objetivo** usando x1...x{n}.\n\n"
            f"Debe ser diferenciable. Usá `**` para potencias.\n\n"
            f"Ejemplo: `x1**2 + x2**2 - 4*x1 - 6*x2`"
        )

    if step == 1:
        n = sd["n_vars"]
        f_call, expr, variables = _parsear_expresion(entrada, n)
        if f_call is None:
            return f"No pude interpretar la expresión. Usá x1...x{n} y operadores Python."
        sd["f_callable"] = f_call
        sd["expr"] = expr
        sd["variables"] = variables
        st.session_state.solver_step = 2
        return (
            f"Función registrada: **f(x) = {expr}** ✓\n\n"
            f"Ingresá el **punto inicial** x⁰ ({n} valores, debe ser factible).\n\n"
            f"Ej: `{', '.join(['0'] * n)}`"
        )

    if step == 2:
        n = sd["n_vars"]
        nums = parsear_numeros(entrada)
        if not nums:
            return f"Ingresá {n} valores para el punto inicial. Ej: `0, 0`"
        sd["x0"] = (list(nums) + [0] * n)[:n]
        st.session_state.solver_step = 3
        return (
            f"Punto inicial x⁰ = [{', '.join(f'{v:.2f}' for v in sd['x0'])}] registrado ✓\n\n"
            f"¿Cuál es la **tolerancia** de convergencia ε? (recomendado: `0.0001`)"
        )

    if step == 3:
        nums = parsear_numeros(entrada)
        sd["tol"] = float(nums[0]) if nums else 1e-4
        st.session_state.solver_step = 4
        return "¿Cuántas **restricciones lineales** tiene el problema? (`0` si no hay)"

    if step == 4:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones? (ej: `2` o `0`)"
        sd["n_restricciones"] = int(nums[0])
        sd["restricciones"] = []
        st.session_state.solver_step = 5
        if sd["n_restricciones"] == 0:
            return _intentar_resolver(sd)
        return "Ingresá la **restricción 1** en formato `coefs <= b`.\n\nEj: `1, 1 <= 4`"

    if step >= 5:
        parsed = parsear_restriccion(entrada)
        if not parsed:
            n_r = len(sd.get("restricciones", [])) + 1
            return f"No pude leer la restricción. Usá `1, 1 <= 4`\n\nIngresá la **restricción {n_r}** nuevamente."
        sd.setdefault("restricciones", []).append(parsed)
        st.session_state.solver_step += 1
        if len(sd["restricciones"]) < sd["n_restricciones"]:
            n_r = len(sd["restricciones"]) + 1
            return f"Restricción {len(sd['restricciones'])} registrada ✓\n\nIngresá la **restricción {n_r}**:"
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
