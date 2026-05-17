# Contrato que cada módulo solver debe cumplir:
#
#   ID: str          — clave del método (debe coincidir con la clave en conocimientos.json)
#   NOMBRE: str      — nombre legible para mostrar en el menú
#   DISPONIBLE: bool — True si tiene solver numérico real, False si sólo usa la guía de pasos
#
#   iniciar() -> str
#       Inicializa solver_data y solver_step en session_state.
#       Devuelve el primer mensaje/pregunta al usuario.
#
#   procesar(entrada: str) -> str
#       Recibe la entrada del usuario, avanza un paso y devuelve el siguiente mensaje.
#       Cuando termina, llama a reset_state() y devuelve el resultado final.
