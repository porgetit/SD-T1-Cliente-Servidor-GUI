# SD-T1-Cliente-Servidor (GUI Edition) 🚀

> Hecho por **Kevin Esguerra Cardona**, apoyado por **Gemini 3 Flash** usando **Antigravity**.

Sistema de mensajería asíncrono y distribuido basado en el modelo **Cliente-Servidor**, diseñado para la transferencia eficiente de mensajes de texto y archivos binarios mediante un protocolo **TLV (Type-Length-Value)** personalizado sobre **TCP/IP**.

---

## 🏗️ Arquitectura del Sistema

El proyecto está estructurado de forma modular siguiendo principios de **Programación Orientada a Objetos (OOP)** y **Separación de Responsabilidades (SoC)**.

### 🌐 El Servidor (`server/`)
Actúa como el orquestador central, gestionando la concurrencia y el enrutamiento de datos.

- **`core.py` (ChatServer)**: Gestiona el ciclo de vida de las conexiones y el estado global.
- **`handlers.py` (ProtocolHandlers)**: Despacha la lógica de negocio basada en el tipo de mensaje recibido.
- **`buffer.py` (RequestBuffer)**: Implementa una cola de procesamiento serializado para evitar condiciones de carrera en el estado del servidor.
- **`session.py` (ClientSession)**: Abstracción de bajo nivel sobre los sockets para envío/recepción atómica de frames TLV.

### 💻 El Cliente (`client/`)
Combina una lógica de red robusta con una interfaz visual moderna.

- **`gui_app.py` (Bridge)**: Utiliza `pywebview` para renderizar un frontend HTML/JS y conectarlo con la lógica Python.
- **`core.py` (ChatClient)**: Orquesta las solicitudes salientes y la gestión de estados locales (sesiones activas, colas de archivos).
- **`receiver.py` (MessageReceiver)**: Hilo dedicado que escucha constantemente el socket para procesar eventos entrantes de forma no bloqueante.
- **`buffer.py` (EventBuffer)**: Sincroniza los eventos provenientes del hilo receptor con la interfaz de usuario.

---

## 📡 Protocolo de Comunicación (TLV)

Para garantizar que los datos se entreguen íntegros y sin problemas de fragmentación (típicos de TCP), implementamos un sistema de **Framing Binario**.

### Estructura del Frame
Cada mensaje en la red viaja con el siguiente encabezado de 5 bytes:

| Tamaño | Campo | Formato (`struct`) | Descripción |
| :--- | :--- | :--- | :--- |
| **1 Byte** | `Type` | `B` (unsigned char) | Clasifica el propósito del mensaje. |
| **4 Bytes** | `Length` | `I` (unsigned int) | Tamaño del `Payload` en bytes. |

### Tipos de Mensajes
1.  **Tipo 0 (Texto)**: Mensajes de chat convencionales (UTF-8).
2.  **Tipo 1 (Comando)**: Señalización del sistema (handshakes, listas, solicitudes de chat).
3.  **Tipo 2 (Binario Genérico)**: Envoltura para archivos con metadatos internos.

---

## 📂 Transferencia de Archivos (Doble TLV)

El sistema soporta el envío de **múltiples archivos** de cualquier extensión. La seguridad se garantiza mediante un **Handshake de tres vías**:

1.  **Solicitud**: El Emisor envía un comando `REQ_SEND_FILES` con el conteo de archivos.
2.  **Autorización**: El Receptor recibe una notificación y elige una carpeta de destino; si acepta, envía `ACCEPT_SEND_FILES`.
3.  **Transmisión**: El Emisor comienza a enviar frames de **Tipo 2** secuencialmente.

### Anatomía del Payload Tipo 2
Para que el servidor sepa a quién enrutar y el receptor sepa cómo guardar el archivo, el payload interno sigue esta estructura:
`[DST_LEN][DST_NAME][FILENAME_LEN][FILENAME][DATA]`

> [!NOTE]
> El sistema incluye lógica automática de **evasión de colisiones**: si un archivo ya existe en la carpeta de destino, se renombra automáticamente (ej: `foto_1.png`).

---

## ✨ Características de la GUI

La interfaz ha sido diseñada para ser funcional y estéticamente agradable:
- **Tema Oscuro**: Estética "Modern Dark" con acentos en azul cian.
- **Autocompletado**: Soporte para `TAB` en comandos (`chat:`, `stop:`, `file:`) y nombres de usuarios conectados.
- **Ayuda Integrada**: Modal interactivo accesible desde la interfaz.
- **Handshake de Nickname**: Registro ordenado con validación de nombres duplicados.

---

## 🛠️ Ejecución y Pruebas

### Requisitos
- Python 3.10 o superior.
- Librería `pywebview` (`pip install pywebview`).

### Paso 1: Iniciar el Servidor
```powershell
python server_app.py
```
El servidor detectará automáticamente tu IP local y escuchará en el puerto 5000.

### Paso 2: Iniciar el Cliente
```powershell
python client_app.py
```
*Nota: El cliente se lanza en un proceso independiente desvinculado de la terminal.*

---

## 🧪 ¿Cómo probar el sistema?

Para realizar una prueba completa de integración, sigue estos pasos:

1.  **Lanzar el Servidor**: Abre una terminal y ejecuta `python server_app.py`.
2.  **Lanzar dos Clientes**: Abre una segunda y tercera terminal para ejecutar `python client_app.py` dos veces.
3.  **Conexión**:
    - En el Cliente A: Ingresa el nombre `Alfa` y presiona "Entrar al Chat".
    - En el Cliente B: Ingresa el nombre `Beta` y presiona "Entrar al Chat".
4.  **Descubrimiento**: Escribe `list` en cualquier entrada de comando para ver al otro usuario.
5.  **Iniciar Chat**: En el Cliente A, escribe `chat:Beta`. El Cliente B recibirá una solicitud que deberá `accept`.
6.  **Enviar Mensaje**: Una vez establecido el chat, escribe cualquier texto para chatear.
7.  **Enviar Archivo**: 
    - Escribe `file`. Se abrirá un selector de archivos nativo.
    - Selecciona uno o varios archivos.
    - El Cliente B recibirá una solicitud. Al escribir `accept`, se le pedirá elegir una carpeta donde guardar los archivos.
    - Observa cómo se trasfieren los bytes y se guardan con el nombre original en el destino.
8.  **Finalizar**: Escribe `exit` para cerrar la aplicación.

---
*Desarrollado para la asignatura de Sistemas Distribuidos.*
