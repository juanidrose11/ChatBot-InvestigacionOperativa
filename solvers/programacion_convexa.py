import numpy as np
import cvxpy as cp
import streamlit as st

from core.nlp import parsear_numeros, parsear_restriccion, contiene_frase, normalizar
from core.estado import reset_state

ID = "programacion_convexa"
NOMBRE = "Programación Convexa"
DISPONIBLE = True


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "Voy a ayudarte a resolver el problema de **Programación Convexa**.\n\n"
        "Modelaremos la función objetivo como: **f(x) = ½xᵀQx + cᵀx**\n\n"
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
        convexa = np.all(eigenvalues >= -1e-8)

        if sd["tipo"] == "min" and not convexa:
            return (
                "⚠️ La matriz Q no es semidefinida positiva (autovalores negativos), "
                "por lo que **f(x) no es convexa**.\n\n"
                "Para programación convexa con minimización, Q debe tener autovalores ≥ 0.\n\n"
                "Revisá los coeficientes e intentá de nuevo escribiendo **cancelar**."
            )

        x = cp.Variable(n)
        expr = 0.5 * cp.quad_form(x, Q) + c @ x
        obj = cp.Minimize(expr) if sd["tipo"] == "min" else cp.Maximize(-expr)

        constraints = [x >= 0]
        for coefs, signo, rhs in sd.get("restricciones", []):
            row = np.array((list(coefs) + [0] * n)[:n])
            if signo == "<=":
                constraints.append(row @ x <= rhs)
            elif signo == ">=":
                constraints.append(row @ x >= rhs)
            else:
                constraints.append(row @ x == rhs)

        prob = cp.Problem(obj, constraints)
        prob.solve()

        if prob.status in ("optimal", "optimal_inaccurate"):
            vars_str = "\n".join(f"  x{i+1} = {x.value[i]:.4f}" for i in range(n))
            eig_str = ", ".join(f"{e:.4f}" for e in eigenvalues)
            val = float(prob.value) if sd["tipo"] == "min" else -float(prob.value)

            reset_state()
            return (
                f"✅ **¡Problema resuelto!**\n\n"
                f"**Variables óptimas:**\n{vars_str}\n\n"
                f"**Valor óptimo f(x):** {val:.4f}\n\n"
                f"**Autovalores de Q:** [{eig_str}]\n"
                f"→ Función {'convexa ✓ — óptimo global garantizado' if convexa else 'no convexa ⚠️'}\n\n"
                f"¿Querés resolver otro problema o necesitás algo más?"
            )
        else:
            reset_state()
            return f"❌ Sin solución. Estado del solver: `{prob.status}`\n\nVerificá que el problema sea factible."
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
        return "¿Querés **minimizar** o **maximizar** la función objetivo?"

    if step == 1:
        sd["tipo"] = "max" if contiene_frase(normalizar(entrada), ["max", "maximizar"]) else "min"
        n = sd["n_vars"]
        st.session_state.solver_step = 2
        return (
            f"Ingresá la **fila 1** de la matriz Q ({n}×{n}), separada por comas.\n\n"
            f"Q define la parte cuadrática: f(x) = ½xᵀQx + cᵀx\n\n"
            f"Ej ({n} valores): `{', '.join(['2'] + ['0'] * (n - 1))}`"
        )

    n = sd["n_vars"]
    if 2 <= step < 2 + n:
        nums = parsear_numeros(entrada)
        if not nums:
            fila = step - 1
            return f"No pude leer los valores. Ingresá la **fila {fila}** con {n} números."
        sd["Q"].append((nums + [0] * n)[:n])
        st.session_state.solver_step += 1
        if len(sd["Q"]) < n:
            fila = len(sd["Q"]) + 1
            return f"Fila {len(sd['Q'])} de Q registrada ✓\n\nIngresá la **fila {fila}** de Q:"
        st.session_state.solver_step = 2 + n
        return (
            f"Matriz Q completa ✓\n\n"
            f"Ahora ingresá el vector **c** ({n} valores, parte lineal cᵀx).\n\n"
            f"Ej: `{', '.join(['-4'] + ['-6'] * (n - 1))}`"
        )

    c_step = 2 + n
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
