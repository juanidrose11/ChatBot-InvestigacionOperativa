#para ejecutar hay que poner el comando streamlit run app.py en la terminal

import streamlit as st #esta es la libreria para crear la interfaz web del bot de chat
import re #libreria para buscar patrones de texto (regex)

#esto es para ocultar el header y el footer de streamlit q ya trae por defecto
ocultar_st = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(ocultar_st, unsafe_allow_html=True)

#config de la pagina
#este seria el titulo que aparece en la pestaña del navegador y el icono que se muestra al lado del titulo
st.set_page_config(page_title="Prototipo ChatBot IO", page_icon="🤖") #titulo e icono

#titulo y descripcion
st.title("🤖 Asistente de Cálculo - Prototipo")
st.markdown("Este es un bot dummy. Intenta escribir frases como: *'Suma 5 y 3'* o *'resta 10 a 20'*.")

#logica del bot
def procesar_respuesta(entrada_usuario):
    #aca analiza el texto del usuario y busca numeros y palabras clave para decidir si sumar o restar
    entrada = entrada_usuario.lower() #lo vuelve minuscula todo
    
    #buscar los numeros en el texto ingresado
    numeros = re.findall(r'\d+', entrada)
    
    #si no hay al menos dos numeros no se puede hacer la operacion
    if len(numeros) < 2:
        return "Para probar este prototipo, por favor ingresa al menos dos números. Ej: 'Suma 10 y 5'."

    #convertir los numeros encontrados en el texto a enteros para poder operar con ellos
    num1 = int(numeros[0])
    num2 = int(numeros[1])

    #decidir si sumar o restar dependiendo de las palabras clave que se ingresaron (tiene en cuenta la primera)
    if "suma" in entrada or "+" in entrada or "mas" in entrada: #si la palabra es suma o un signo de + o escribe la palabra mas
        resultado = num1 + num2 #sumar
        return f"La suma de {num1} y {num2} es **{resultado}**. :3"
    
    elif "resta" in entrada or "-" in entrada or "menos" in entrada:
        resultado = num1 - num2 #restar
        return f"La resta de {num1} menos {num2} es **{resultado}**. :3"
    
    else:
        return f"Detecté los números {num1} y {num2}, pero no entendí si quieres sumarlos o restarlos. Intenta decir 'Suma' o 'Resta'."

#INTERFAZ DE CHAT
#inicializar el historial de chat en la sesion si no existe
if "messages" not in st.session_state: #si no hay mensajes en la sesion actual
    st.session_state.messages = [#iniciar un chat nuevo, o sea mandar mensajes
        {"role": "assistant", "content": "Hola 👋, soy un prototipo. ¿Qué números quieres sumar o restar?"}
    ]

#mostrar mensajes anteriores del chat 
for message in st.session_state.messages: #si hay mensajes en la sesion, mostrarlos
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#cuadro de texto para ingresar mensajes del usuario
if prompt := st.chat_input("Escribi tu consulta aca..."):
    
    #guardar y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #respuesta del bot
    respuesta_bot = procesar_respuesta(prompt)

    #guardar y mostrar la respuesta del bot
    with st.chat_message("assistant"):
        st.markdown(respuesta_bot)
    st.session_state.messages.append({"role": "assistant", "content": respuesta_bot})