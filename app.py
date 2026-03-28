import streamlit as st
import re # Librería para buscar patrones de texto (regex)

# Configuración de la página (título e ícono en la pestaña del navegador)
st.set_page_config(page_title="Prototipo CalcBot IO", page_icon="🤖")

st.title("🤖 Asistente de Cálculo - Prototipo")
st.markdown("Este es un bot dummy. Intenta escribir frases como: *'Suma 5 y 3'* o *'resta 10 a 20'*.")

# ---------------------------------------------------------
# LÓGICA DEL BOT (El "cerebro" simplificado)
# ---------------------------------------------------------
def procesar_respuesta(entrada_usuario):
    """
    Analiza el texto del usuario buscando números y palabras clave (suma/resta).
    Devuelve la respuesta del bot.
    """
    entrada = entrada_usuario.lower()
    
    # Buscamos todos los números en el texto
    numeros = re.findall(r'\d+', entrada)
    
    # Si no hay al menos dos números, no podemos operar
    if len(numeros) < 2:
        return "Para probar este prototipo, por favor ingresa al menos dos números. Ej: 'Suma 10 y 5'."

    # Convertimos los textos encontrados a enteros
    num1 = int(numeros[0])
    num2 = int(numeros[1])

    # Lógica de detección de operación
    if "suma" in entrada or "+" in entrada or "mas" in entrada:
        resultado = num1 + num2
        return f"¡Claro! La suma de {num1} y {num2} es **{resultado}**."
    
    elif "resta" in entrada or "-" in entrada or "menos" in entrada:
        # Una lógica simple de resta (el primero menos el segundo)
        resultado = num1 - num2
        return f"Entendido. La resta de {num1} menos {num2} es **{resultado}**."
    
    else:
        return f"Detecté los números {num1} y {num2}, pero no entendí si quieres sumarlos o restarlos. Intenta decir 'Suma' o 'Resta'."

# ---------------------------------------------------------
# INTERFAZ DE CHAT (Estilo Gemini/ChatGPT)
# ---------------------------------------------------------

# 1. Inicializar el historial de chat en la sesión si no existe
# Esto es vital en Streamlit para que los mensajes no desaparezcan al recargar
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hola 👋, soy un prototipo. ¿Qué números quieres sumar o restar hoy?"}
    ]

# 2. Mostrar los mensajes anteriores del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Capturar la entrada del usuario (Cuadro de texto FIJO ABAJO)
# El operador := asigna la entrada a la variable 'prompt' si no está vacía
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    
    # A. Guardar y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Generar la respuesta del bot usando la lógica definida arriba
    respuesta_bot = procesar_respuesta(prompt)

    # C. Guardar y mostrar la respuesta del bot
    with st.chat_message("assistant"):
        st.markdown(respuesta_bot)
    st.session_state.messages.append({"role": "assistant", "content": respuesta_bot})