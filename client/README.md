# Componente Cliente - Chat Modular con GUI

Este directorio contiene la implementación del cliente de chat, que integra una interfaz gráfica moderna (HTML/CSS/JS) con una lógica de red robusta basada en Python.

## 🏗️ Arquitectura del Cliente

El cliente está diseñado bajo un modelo de **separación de responsabilidades** (SoC), permitiendo que la lógica de red y la interfaz de usuario operen de forma independiente pero coordinada.

### Componentes Clave:
- **`gui_app.py` (Bridge & GUI)**: Utiliza `pywebview` para renderizar la interfaz. La clase `Bridge` actúa como intermediario entre el JavaScript del navegador y el Python del sistema, exponiendo métodos de red a la UI.
- **`core.py` (Controlador Principal)**: Orquestra las operaciones de alto nivel: conexión, desconexión y procesamiento de comandos o mensajes emitidos por el usuario.
- **`receiver.py` (Receptor Asíncrono)**: Un hilo secundario dedicado exclusivamente a escuchar el socket. Desempaqueta los datos TLV y actualiza el estado o el buffer de eventos según el tipo de mensaje recibido.
- **`state.py` (Modelo de Estado)**: Almacena de forma centralizada la información de la sesión activa, usuarios conectados, solicitudes pendientes y colas de archivos.
- **`buffer.py` (Buffer de Eventos/UI)**: Gestiona la comunicación asíncrona hacia la GUI, proporcionando una cola de mensajes que el Bridge consume para actualizar la vista de forma segura.

---

## 🎨 Interfaz Gráfica (Modular)

La interfaz se encuentra en `/client/gui` y está totalmente desacoplada del código Python:
- **`index.html`**: Solo estructura y marcado.
- **`style.css`**: Diseño visual, temas y animaciones (CSS puro).
- **`script.js`**: Lógica de interacción del lado del cliente, incluyendo autocompletado de comandos y gestión del DOM.

---

## 🌍 Compatibilidad y Sistema Operativo

El cliente es **mayoritariamente agnóstico al SO**, pero incluye optimizaciones específicas para garantizar una experiencia "nativa":

### Agnosticismo:
- **Lógica de Red**: Utiliza sockets estándar de Python y flujos de hilos (`threading`), compatibles con Windows, Linux y macOS.
- **Renderizado**: `pywebview` utiliza el motor de renderizado nativo del SO (Edge/WebView2 en Windows, WebKit en macOS/Linux), asegurando que la UI se vea bien en todas partes sin empaquetar un navegador pesado.

### Optimizaciones de Infraestructura (Windows):
- **Aislamiento de Consola**: En Windows, `client_app.py` intenta usar `pythonw.exe` y banderas de creación de proceso (`DETACHED_PROCESS`) para lanzar el cliente sin abrir una ventana de terminal adicional, comportándose como una aplicación de escritorio real.
- **Rutas de Archivo**: La gestión de transferencias de archivos utiliza `pathlib` para asegurar la compatibilidad con los separadores de ruta (`\` vs `/`).

---

## 🛠️ Requisitos e Infraestructura
- **Python 3.10+**
- **Dependencias**:
  - `pywebview`: Para la ventana gráfica.
  - `python-clr` (opcional en Windows): Para una mejor integración con .NET/WebView2.
- **Red**: El cliente espera una conexión TCP abierta hacia el puerto del servidor (por defecto 5000), sin restricciones de firewall local para el tráfico saliente.

## 🚀 Flujo de Trabajo
1.  **Lanzamiento**: `client_app.py` inicia la GUI desvinculada.
2.  **Handshake**: El usuario ingresa host, puerto y nick; el Bridge inicia la conexión vía `core.py`.
3.  **Escucha**: Se activa `receiver.py` para procesar el flujo TLV entrante.
4.  **Interacción**: Los comandos escritos en la UI son enviados por el Bridge al Core, y los eventos recibidos se inyectan en el log de la GUI mediante el buffer.
