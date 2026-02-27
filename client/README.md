# Componente Cliente - Chat Modular con GUI

Este directorio contiene la implementación del cliente de chat, que integra una interfaz gráfica moderna (HTML/CSS/JS) con una lógica de red robusta en Python, siguiendo un modelo de **separación de responsabilidades (SoC)**.

## 🏗️ Arquitectura del Cliente

### Capa de Red:
- **`core.py` (ChatClient)**: Orquesta las operaciones de alto nivel — conexión, desconexión y procesamiento de comandos del usuario — sin conocimiento de la UI.
- **`receiver.py` (MessageReceiver)**: Hilo daemon dedicado a escuchar el socket. Desempaqueta tramas TLV y actualiza el estado o el buffer de eventos según el tipo de mensaje.
- **`state.py` (ChatState)**: Almacena de forma centralizada el estado de la sesión activa: nombre, conversaciones abiertas, usuarios conectados, solicitudes pendientes y colas de transferencia de archivos.
- **`buffer.py` (EventBuffer)**: Cola de eventos asíncrona que desacopla el hilo de red de la GUI. Garantiza que errores en el callback (e.g., `evaluate_js`) no maten el hilo — los fallos se registran en `client_stderr.log`.

### Capa de Presentación:
- **`gui_app.py` (Bridge + GUI)**: Usa `pywebview` para renderizar la interfaz. La clase `Bridge` expone métodos Python al JavaScript del frontend (`connect`, `set_name`, `send_command`, `select_files`, etc.). Todos los errores del proceso silencioso `pythonw` se capturan en `client_stderr.log`.

### Interfaz Gráfica (`gui/`):
Totalmente desacoplada del código Python:
- **`index.html`**: Estructura semántica de la UI.
- **`style.css`**: Diseño visual, temas y animaciones (CSS puro).
- **`script.js`**: Lógica de interacción: autocompletado de comandos, gestión del DOM y actualización de la lista de usuarios.

---

## 🛠️ Diagnóstico y Logging

El cliente captura silenciosamente los errores del proceso GUI en **`client_stderr.log`** (en la raíz del proyecto). Este archivo contiene:
- Trazas de excepciones no capturadas en el proceso `pythonw`.
- Errores del callback `EventBuffer` al intentar inyectar eventos en la GUI.

Para habilitar las DevTools de Edge en la ventana del cliente (útil para depurar JavaScript), cambiar temporalmente en `gui_app.py`:
```python
webview.start(debug=True)
```

---

## 🌍 Compatibilidad

- **Lógica de red**: Sockets estándar Python + `threading`. Compatible con Windows, Linux y macOS.
- **Renderizado**: `pywebview` usa el motor nativo del SO (Edge/WebView2 en Windows, WebKit en macOS/Linux).
- **Aislamiento de consola (Windows)**: `cliente.py` usa `pythonw.exe` con `DETACHED_PROCESS` para comportarse como una app de escritorio sin terminal visible.
- **Rutas de archivo**: `pathlib` asegura compatibilidad con separadores `\\` vs `/`.

---

## 🚀 Flujo de Trabajo

1. **Lanzamiento**: `cliente.py` usa `pythonw.exe` para iniciar la GUI desvinculada de la terminal.
2. **Handshake**: El usuario ingresa host, puerto y nickname; `Bridge.connect()` establece el socket y lanza `MessageReceiver`.
3. **Registro**: `Bridge.set_name()` envía `SET_NAME:<nick>` y espera confirmación `NAME_OK` del servidor (timeout 5s).
4. **Escucha**: `MessageReceiver` procesa el flujo TLV y deposita eventos en `EventBuffer`.
5. **Interacción**: El buffer llama al callback de `Bridge`, que inyecta los mensajes en la UI vía `evaluate_js()`.
6. **Archivos**: El usuario escribe `file`, selecciona archivos con el diálogo nativo y el receptor acepta y elige la carpeta de destino.

---

## 🛠️ Requisitos
- **Python 3.10+**
- **Dependencias**: `pywebview` (ventana gráfica). Gestionadas mediante `requirements.txt`.
- **Red**: Conexión TCP abierta hacia el puerto del servidor (por defecto `5000`).
