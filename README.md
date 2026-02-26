# SD-T1-Cliente-Servidor (GUI Edition) 🚀

> Hecho por **Kevin Esguerra Cardona**, apoyado por **Gemini 3 Flash** usando **Antigravity**.

Sistema de mensajería asíncrono y distribuido basado en el modelo **Cliente-Servidor**, diseñado para la transferencia eficiente de mensajes de texto y archivos binarios mediante un protocolo **TLV (Type-Length-Value)** personalizado sobre **TCP/IP**.

---

## 🏗️ Arquitectura del Sistema

El proyecto está estructurado de forma modular siguiendo principios de **Programación Orientada a Objetos (OOP)** y **Separación de Responsabilidades (SoC)**.

### 🌐 El Servidor (`server/`)
Actúa como el orquestador central, gestionando la concurrencia y el enrutamiento de datos.

- **`servidor.py` [NUEVO]**: Punto de entrada principal. Verifica dependencias e inicia la fachada del servidor.
- **`core.py` (ChatServer)**: Gestiona el ciclo de vida de las conexiones y el estado global.
- **`handlers.py` (ProtocolHandlers)**: Despacha la lógica de negocio basada en el tipo de mensaje recibido.
- **`buffer.py` (RequestBuffer)**: Implementa una cola de procesamiento serializado.
- **`session.py` (ClientSession)**: Abstracción sobre los sockets para envío/recepción de frames TLV.

### 💻 El Cliente (`client/`)
Combina una lógica de red robusta con una interfaz visual moderna.

- **`cliente.py` [NUEVO]**: Punto de entrada principal. Gestiona dependencias y lanza la GUI desvinculada de la terminal.
- **`gui_app.py` (Bridge)**: Utiliza `pywebview` para renderizar un frontend HTML/JS.
- **`core.py` (ChatClient)**: Orquesta las solicitudes salientes y la gestión de estados locales.
- **`receiver.py` (MessageReceiver)**: Hilo dedicado que escucha el socket para procesar eventos entrantes.
- **`buffer.py` (EventBuffer)**: Sincroniza los eventos con la interfaz de usuario.

---

## 🛠️ Verificación de Dependencias (`dep_checker.py`)

El sistema incluye un script inteligente de pre-arranque (`dep_checker.py`) que:
1.  Detecta el SO (Linux/Windows).
2.  Carga los requisitos desde `requirements.txt`.
3.  Crea y gestiona un entorno virtual (`venv`) automáticamente.
4.  Instala dependencias faltantes sin intervención manual.

---

## 🚀 Ejecución y Pruebas

### Requisitos
- Python 3.10 o superior.

### Paso 1: Iniciar el Servidor
Abra una terminal en la raíz del proyecto y ejecute:
```powershell
python servidor.py
```
El servidor validará el entorno e iniciará en el puerto 5000.

### Paso 2: Iniciar el Cliente
En otra terminal, ejecute:
```powershell
python cliente.py
```
*Nota: En Windows, el cliente se lanza como un proceso desvinculado de la consola.*

---

## 🧪 ¿Cómo probar el sistema?

Para realizar una prueba completa de integración, sigue estos pasos:

1.  **Lanzar el Servidor**: Ejecute `python servidor.py`.
2.  **Lanzar dos Clientes**: Ejecute `python cliente.py` dos veces.
3.  **Conexión**:
    - En el Cliente A: Ingrese un nickname y presione "Entrar al Chat".
    - En el Cliente B: Ingrese un nickname y presione "Entrar al Chat".
4.  **Descubrimiento**: Escribe `list` en cualquier entrada de comando para ver al otro usuario.
5.  **Iniciar Chat**: En el Cliente A, escribe `chat:NombreDeBeta`. El Cliente B deberá `accept`.
6.  **Enviar Mensaje**: Una vez establecido el chat, escribe cualquier texto para chatear.
7.  **Enviar Archivo**: 
    - Escribe `file`. Se abrirá un selector de archivos nativo.
    - El receptor deberá `accept` y elegir una carpeta de destino.
8.  **Finalizar**: Escribe `exit` para cerrar la aplicación.

---
*Desarrollado para la asignatura de Sistemas Distribuidos.*
