import numpy as np
from scipy.optimize import linprog
import streamlit as st

from core.nlp import parsear_numeros
from core.estado import reset_state

ID = "programacion_estocastica"
NOMBRE = "Programación Estocástica"
DISPONIBLE = True

# Formulación two-stage SP (forma extensiva):
#
#   min  cᵀx  +  Σ_s p_s · qᵀy_s
#   s.t. Ax ≤ b                   (primera etapa)
#        x + y_s ≤ h_s  para cada s  (segunda etapa: acción x + recourse y_s cubre demanda h_s)
#        x, y_s ≥ 0
#
# Variables en el LP extensivo: [x (n_x), y_1 (n_y), ..., y_k (n_y)]


def iniciar():
    st.session_state.solver_data = {}
    st.session_state.solver_step = 0
    return (
        "Voy a ayudarte a resolver el problema de **Programación Estocástica** (2 etapas).\n\n"
        "**Estructura:**\n"
        "- Primera etapa: decidís **x** antes de conocer el escenario (ej: cuánto producir/comprar).\n"
        "- Segunda etapa: actuás con **y_s** como recourse según el escenario s que se realice.\n\n"
        "¿Cuántas **variables de primera etapa** tiene el problema? (ej: `2`)"
    )


def procesar(entrada):
    return _procesar(entrada)


def _intentar_resolver(sd):
    try:
        n_x = sd["n_x"]
        n_y = sd["n_y"]
        c = np.array(sd["c"], dtype=float)    # costos primera etapa
        q = np.array(sd["q"], dtype=float)    # costos segunda etapa (por escenario)
        probs = np.array(sd["probs"], dtype=float)
        escenarios = sd["escenarios"]          # lista de arrays h_s (demanda/recurso por escenario)
        n_esc = len(escenarios)

        # Vector de costos extendido: [c, p1*q, p2*q, ..., pk*q]
        c_ext = np.concatenate([c] + [probs[s] * q for s in range(n_esc)])

        A_ub_rows = []
        b_ub_rows = []

        # Restricciones de primera etapa: A_x · x ≤ b_x (sin variables y)
        for row_coefs, _, rhs in sd.get("rest_primera", []):
            row = np.array((list(row_coefs) + [0] * n_x)[:n_x])
            full_row = np.concatenate([row, np.zeros(n_esc * n_y)])
            A_ub_rows.append(full_row)
            b_ub_rows.append(rhs)

        # Restricciones de segunda etapa por escenario: x + y_s ≤ h_s
        # En variables extendidas: [I | 0...I...0] · [x, y1,...,yk] ≤ h_s
        # donde I está en la posición del escenario s
        for s, h_s in enumerate(escenarios):
            for j in range(min(n_y, len(h_s))):
                row = np.zeros(n_x + n_esc * n_y)
                # coef de x_j en la restricción j del escenario s
                if j < n_x:
                    row[j] = 1.0
                # coef de y_s_j
                row[n_x + s * n_y + j] = 1.0
                A_ub_rows.append(row)
                b_ub_rows.append(float(h_s[j]))

        A_ub = np.array(A_ub_rows) if A_ub_rows else None
        b_ub = np.array(b_ub_rows) if b_ub_rows else None
        bounds = [(0, None)] * (n_x + n_esc * n_y)

        result = linprog(c_ext, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        if result.success:
            x_opt = result.x[:n_x]
            x_str = "\n".join(f"  x{i+1} = {x_opt[i]:.4f}" for i in range(n_x))

            esc_lines = []
            for s in range(n_esc):
                y_s = result.x[n_x + s * n_y: n_x + (s + 1) * n_y]
                y_str = ", ".join(f"y{j+1}={v:.4f}" for j, v in enumerate(y_s))
                costo_s = float(q @ y_s)
                esc_lines.append(f"  Escenario {s+1} (p={probs[s]:.2f}): {y_str} → costo recourse = {costo_s:.4f}")

            costo_fijo = float(c @ x_opt)
            costo_esp = sum(probs[s] * float(q @ result.x[n_x + s * n_y: n_x + (s + 1) * n_y]) for s in range(n_esc))

            reset_state()
            return (
                f"✅ **¡Problema resuelto!**\n\n"
                f"**Variables de primera etapa (x*):**\n{x_str}\n\n"
                f"**Costo fijo de primera etapa:** {costo_fijo:.4f}\n\n"
                f"**Costo esperado de recourse:** {costo_esp:.4f}\n\n"
                f"**Costo total esperado:** {result.fun:.4f}\n\n"
                f"**Recourse por escenario:**\n" + "\n".join(esc_lines)
                + "\n\n¿Querés resolver otro problema o necesitás algo más?"
            )
        else:
            reset_state()
            return f"❌ Sin solución. Estado: `{result.message}`\n\nVerificá que el problema sea factible."
    except Exception as e:
        reset_state()
        return f"❌ Error al resolver: {str(e)}"


def _procesar(entrada):
    sd = st.session_state.solver_data
    step = st.session_state.solver_step

    if step == 0:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántas **variables de primera etapa** tiene el problema? (ej: `2`)"
        sd["n_x"] = int(nums[0])
        st.session_state.solver_step = 1
        return f"¿Cuántas **variables de segunda etapa** (recourse) hay por escenario? (ej: `2`)"

    if step == 1:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántas variables de segunda etapa por escenario? (ej: `1`)"
        sd["n_y"] = int(nums[0])
        st.session_state.solver_step = 2
        return (
            f"Ingresá los **costos de primera etapa** c ({sd['n_x']} valores), separados por comas.\n\n"
            f"Ej: `2, 3`"
        )

    if step == 2:
        nums = parsear_numeros(entrada)
        if not nums:
            return f"Ingresá {sd['n_x']} costos de primera etapa. Ej: `2, 3`"
        sd["c"] = (nums + [0] * sd["n_x"])[: sd["n_x"]]
        st.session_state.solver_step = 3
        return (
            f"Ingresá los **costos de segunda etapa** q ({sd['n_y']} valores, iguales para todos los escenarios).\n\n"
            f"Ej: `1, 4`"
        )

    if step == 3:
        nums = parsear_numeros(entrada)
        if not nums:
            return f"Ingresá {sd['n_y']} costos de segunda etapa. Ej: `1, 4`"
        sd["q"] = (nums + [0] * sd["n_y"])[: sd["n_y"]]
        sd["rest_primera"] = []
        st.session_state.solver_step = 4
        return "¿Cuántas **restricciones de primera etapa** tiene el problema? (`0` si no hay)"

    if step == 4:
        nums = parsear_numeros(entrada)
        if not nums:
            return "¿Cuántas restricciones de primera etapa? (ej: `1` o `0`)"
        sd["n_rest_primera"] = int(nums[0])
        st.session_state.solver_step = 5
        if sd["n_rest_primera"] == 0:
            return f"¿Cuántos **escenarios** tiene el problema? (ej: `3`)"
        return "Ingresá la **restricción 1** de primera etapa en formato `coefs <= b`.\n\nEj: `1, 1 <= 10`"

    if step == 5:
        from core.nlp import parsear_restriccion
        if sd.get("n_rest_primera", 0) > 0 and len(sd["rest_primera"]) < sd["n_rest_primera"]:
            parsed = parsear_restriccion(entrada)
            if not parsed:
                n_r = len(sd["rest_primera"]) + 1
                return f"No pude leer la restricción. Usá `1, 1 <= 10`\n\nIngresá la **restricción {n_r}** nuevamente."
            sd["rest_primera"].append(parsed)
            if len(sd["rest_primera"]) < sd["n_rest_primera"]:
                n_r = len(sd["rest_primera"]) + 1
                return f"Restricción {len(sd['rest_primera'])} registrada ✓\n\nIngresá la **restricción {n_r}**:"
        st.session_state.solver_step = 6
        return f"¿Cuántos **escenarios** tiene el problema? (ej: `3`)"

    if step == 6:
        nums = parsear_numeros(entrada)
        if not nums or int(nums[0]) < 1:
            return "¿Cuántos escenarios? (ej: `3`)"
        sd["n_esc"] = int(nums[0])
        sd["probs"] = []
        sd["escenarios"] = []
        st.session_state.solver_step = 7
        return (
            f"Ingresá las **probabilidades** de los {sd['n_esc']} escenarios separadas por comas (deben sumar 1).\n\n"
            f"Ej: `0.3, 0.5, 0.2`"
        )

    if step == 7:
        nums = parsear_numeros(entrada)
        if not nums or len(nums) < sd["n_esc"]:
            return f"Necesito {sd['n_esc']} probabilidades. Ej: `0.3, 0.5, 0.2`"
        probs = nums[: sd["n_esc"]]
        total = sum(probs)
        if abs(total - 1.0) > 0.01:
            probs = [p / total for p in probs]
            aviso = f"⚠️ Las probabilidades sumaban {total:.2f}, las normalicé.\n\n"
        else:
            aviso = ""
        sd["probs"] = probs
        st.session_state.solver_step = 8
        return aviso + (
            f"Ingresá los **recursos/demanda** del escenario 1 "
            f"({sd['n_y']} valores, uno por variable de recourse).\n\n"
            f"Ej: `5, 8`"
        )

    if step >= 8:
        esc_idx = step - 8
        nums = parsear_numeros(entrada)
        if not nums:
            return f"Ingresá {sd['n_y']} valores para el escenario {esc_idx + 1}. Ej: `5, 8`"
        h_s = (nums + [0] * sd["n_y"])[: sd["n_y"]]
        sd["escenarios"].append(h_s)
        st.session_state.solver_step += 1

        if len(sd["escenarios"]) < sd["n_esc"]:
            next_esc = len(sd["escenarios"]) + 1
            return (
                f"Escenario {len(sd['escenarios'])} registrado ✓\n\n"
                f"Ingresá los **recursos/demanda** del escenario {next_esc}:"
            )
        return _intentar_resolver(sd)

    return "Algo salió mal. Escribí **cancelar** para reiniciar."
