import numpy as np
import cvxpy as cp
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "prog_cuadratica_wolfe"
NOMBRE = "Programación Cuadrática (Método de Wolfe)"
DISPONIBLE = True


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
        "Voy a ayudarte a resolver el problema de **Programación Cuadrática** con el Método de Wolfe.\n\n"
        "La función objetivo es: **f(x) = ½xᵀQx + cᵀx**, con restricciones lineales.\n\n"
        "Al resolver, mostraré las **condiciones KKT** verificadas.\n\n"
        "¿Cuántas **variables de decisión** tiene el problema? (ej: `2`)"
    )


def procesar(entrada):
    return _procesar(entrada)


def _intentar_resolver(sd):
    try:
        n = sd["n_vars"]
        Q = np.array(sd["Q"], dtype=float)
        c = np.array(sd["c"], dtype=float)

        eigenvalues = np.linalg.eigvalsh(Q)
        semidefinida_pos = np.all(eigenvalues >= -1e-8)

        x_var = cp.Variable(n)
        obj = cp.Minimize(0.5 * cp.quad_form(x_var, Q) + c @ x_var)

        constraint_objs = [x_var >= 0]
        A_rows, b_rows, signos = [], [], []
        for coefs, signo, rhs in sd.get("restricciones", []):
            row = np.array((list(coefs) + [0] * n)[:n])
            A_rows.append(row)
            b_rows.append(rhs)
            signos.append(signo)
            if signo == "<=":
                constraint_objs.append(row @ x_var <= rhs)
            elif signo == ">=":
                constraint_objs.append(row @ x_var >= rhs)
            else:
                constraint_objs.append(row @ x_var == rhs)

        prob = cp.Problem(obj, constraint_objs)
        prob.solve()

        if prob.status not in ("optimal", "optimal_inaccurate"):
            reset_state()
            return f"❌ Sin solución. Estado: `{prob.status}`\n\nVerificá que el problema sea factible."

        x_opt = x_var.value
        f_opt = float(prob.value)

        # Gradiente en x* = Qx* + c
        grad = Q @ x_opt + c

        # Verificación KKT: ∇f(x*) + Σ λᵢ aᵢ ≈ 0, λᵢ ≥ 0, λᵢ gᵢ(x*) = 0
        kkt_lines = ["**Condiciones KKT verificadas en x*:**\n"]
        kkt_lines.append(f"∇f(x*) = Qx* + c = [{', '.join(f'{g:.4f}' for g in grad)}]")

        dual_vals = []
        restricciones_contexto = []
        for i, con in enumerate(constraint_objs[1:]):  # skip x >= 0
            lam = con.dual_value
            dual_vals.append(lam)
            lhs = float(A_rows[i] @ x_opt)
            rhs = float(b_rows[i])
            g_val = lhs - rhs
            restricciones_contexto.append({
                "lhs": lhs,
                "signo": signos[i],
                "rhs": rhs,
                "cumple": _restriccion_cumple(lhs, signos[i], rhs),
                "activa": abs(lhs - rhs) < 1e-6,
                "lambda": float(np.asarray(lam).flat[0]) if lam is not None else None,
            })
            kkt_lines.append(
                f"λ{i+1} = {lam:.4f}, g{i+1}(x*) = {g_val:.4f}"
                + (" ← activa" if abs(g_val) < 1e-6 else "")
            )

        eig_str = ", ".join(f"{e:.4f}" for e in eigenvalues)
        vars_str = "\n".join(f"  x{i+1} = {x_opt[i]:.4f}" for i in range(n))

        reset_state()
        return (
            f"✅ **¡Problema resuelto!**\n\n"
            f"**Variables óptimas:**\n{vars_str}\n\n"
            f"**Valor óptimo f(x*):** {f_opt:.4f}\n\n"
            f"**Autovalores de Q:** [{eig_str}]\n"
            f"→ Q es {'semidefinida positiva ✓' if semidefinida_pos else 'no semidefinida positiva ⚠️'}\n\n"
            + "\n".join(kkt_lines)
            + f"\n\n*Solución {'global' if semidefinida_pos else 'local'} según convexidad de Q.*\n\n"
            + "¿Querés resolver otro problema o necesitás algo más?"
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
        sd["Q"] = []
        st.session_state.solver_step = 1
        n = sd["n_vars"]
        return (
            f"Ingresá la **fila 1** de la matriz Q ({n}×{n}), separada por comas.\n\n"
            f"Ej ({n} valores): `{', '.join(['2'] + ['0'] * (n - 1))}`"
        )

    n = sd["n_vars"]
    if 1 <= step < 1 + n:
        nums = parsear_numeros(entrada)
        if not nums:
            fila = step
            return f"No pude leer los valores. Ingresá la **fila {fila}** con {n} números."
        sd["Q"].append((nums + [0] * n)[:n])
        st.session_state.solver_step += 1
        if len(sd["Q"]) < n:
            fila = len(sd["Q"]) + 1
            return f"Fila {len(sd['Q'])} de Q registrada ✓\n\nIngresá la **fila {fila}** de Q:"
        st.session_state.solver_step = 1 + n
        return (
            f"Matriz Q completa ✓\n\n"
            f"Ingresá el vector **c** ({n} valores, parte lineal).\n\n"
            f"Ej: `{', '.join(['-4'] + ['-6'] * (n - 1))}`"
        )

    c_step = 1 + n
    if step == c_step:
        nums = parsear_numeros(entrada)
        if not nums:
            return f"Ingresá el vector c con {n} valores. Ej: `-4, -6`"
        sd["c"] = (nums + [0] * n)[:n]
        sd["restricciones"] = []
        st.session_state.solver_step = c_step + 1
        return "¿Cuántas **restricciones lineales** tiene el problema? (`0` si no hay)"

    nrest_step = c_step + 1
    if step == nrest_step:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones tiene? (ej: `2` o `0`)"
        sd["n_restricciones"] = int(nums[0])
        st.session_state.solver_step = nrest_step + 1
        if sd["n_restricciones"] == 0:
            return _intentar_resolver(sd)
        return "Ingresá la **restricción 1** en formato `coefs <= b`.\n\nEj: `1, 1 <= 4`"

    if step > nrest_step:
        parsed = parsear_restriccion(entrada)
        if not parsed:
            n_r = len(sd["restricciones"]) + 1
            return f"No pude leer la restricción. Usá `1, 1 <= 4`\n\nIngresá la **restricción {n_r}** nuevamente."
        sd["restricciones"].append(parsed)
        st.session_state.solver_step += 1
        if len(sd["restricciones"]) < sd["n_restricciones"]:
            n_r = len(sd["restricciones"]) + 1
            return f"Restricción {len(sd['restricciones'])} registrada ✓\n\nIngresá la **restricción {n_r}**:"
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
