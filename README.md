# 🚀 Chatbot de Investigación Operativa

Chatbot de Investigación Operativa es una aplicación web inteligente diseñada para ayudar a estudiantes y profesionales a resolver problemas de Investigación Operativa. Utilizando Modelos de Lenguaje de Gran Escala (LLMs), el sistema puede analizar problemas, generar modelos matemáticos (PL, IP, CPL, etc.) y resolverlos de manera interactiva.

## ✨ Características Principales

- **💬 Interfaz de Chat Intuitiva**: Conversa con el chatbot para describir tu problema en lenguaje natural.
- **🧠 Modelado Automático**: El sistema identifica automáticamente las variables, la función objetivo y las restricciones.
- ** solver Integration**: Resuelve modelos de Programación Lineal (PL) y Programación Entera (IP) utilizando solucionadores robustos.
- **🌐 Despliegue Global**:
  - **URL Principal**: [chatbot-investigacionoperativa-qhnbu6ecbkvh5fkygg6uh7.streamlit.app](https://chatbot-investigacionoperativa-qhnbu6ecbkvh5fkygg6uh7.streamlit.app/)
  - **URL Alternativa**: [chatbot-inv-operativa.streamlit.app](https://chatbot-inv-operativa.streamlit.app/)

## 🛠️ Instalación Local

Si deseas ejecutar el proyecto en tu máquina local, sigue estos pasos:

### Requisitos Previos

- Python 3.8+
- Pip

### Pasos de Instalación

1. **Clonar el repositorio** (o descargar los archivos):
   ```bash
   git clone <url-del-repositorio>
   cd ChatBot-InvestigaciónOperativa
   ```

2. **Instalar dependencias**:
   Crea un entorno virtual y activa el entorno (recomendado):
   ```bash
   python -m venv .venv
   .

.venv\Scripts\activate   # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
   Luego, instala las librerías necesarias:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación**:
   ```bash
   streamlit run app.py
   ```
   Esto iniciará la aplicación y deberías poder acceder a ella en tu navegador (usualmente en `http://localhost:3000`).

## 📁 Estructura del Proyecto

- `app.py`: Punto de entrada principal de la aplicación Streamlit.
- `pages/`: Contiene las diferentes páginas o módulos de la aplicación.
- `utils/`: Funciones de utilidad y lógica de negocio.
- `requirements.txt`: Lista de dependencias del proyecto.

---

**Desarrollado por "Equipo Casi Factible"**
