# SD-T1-Cliente-Servidor (GUI Edition) 🚀

> Hecho por **Kevin Esguerra Cardona**, **David Julian Torres Osorio** y **Estaban Guapacha Jiminez** apoyado por **Gemini 2.5 Flash** usando **Antigravity**.

Sistema de mensajería asíncrono y distribuido basado en el modelo **Cliente-Servidor**, con soporte de chat en tiempo real y transferencia de archivos binarios mediante un protocolo **TLV (Type-Length-Value)** personalizado sobre **TCP/IP**.

---

## 🏗️ Arquitectura del Sistema

El proyecto está estructurado de forma modular siguiendo principios de **Orientación a Objetos (OOP)**, **Separación de Responsabilidades (SoC)** y **Patrón Observer**, que desacopla completamente la lógica de negocio del sistema de salida.

---

### 🌐 El Servidor (`server/`)

El servidor actúa como orquestador central. Hereda de `Observable` y emite eventos semánticos tipados que cualquier observer puede consumir sin modificar la lógica de red.

| Archivo | Rol |
|---|---|
| `core.py` | **ChatServer** — gestión de conexiones, estado y enrutamiento. Hereda de `Observable`. |
| `events.py` | Catálogo de **dataclasses de eventos** (`ServerStarted`, `ClientJoined`, `FileTransferRouted`, …). Datos puros, sin dependencias de presentación. |
| `observable.py` | Mixin **Observable** thread-safe con `emit()`, `subscribe()` y `unsubscribe()`. |
| `logger.py` | **ServerObserver** — observer concreto que traduce eventos a consola Rich y `server.log`. |
| `handlers.py` | Despacho del protocolo de comandos según tipo TLV. |
| `buffer.py` | Cola FIFO serializada para procesar peticiones en orden. |
| `session.py` | Abstracción del socket TCP para tramas TLV. |
| `facade.py` | **Único punto de cableado** — conecta `ChatServer` ↔ `ServerObserver`. |

> Para añadir una GUI al servidor o exponerlo como API, basta con implementar un nuevo observer y suscribirlo en `facade.py` sin tocar nada más.

---

### 💻 El Cliente (`client/`)

Combina lógica de red robusta con una interfaz visual moderna renderizada con pywebview.

| Archivo | Rol |
|---|---|
| `gui_app.py` | **Bridge** — puente entre JS del frontend y Python; gestiona la ventana pywebview. |
| `core.py` | **ChatClient** — lógica de alto nivel: conexión, comandos, envío de archivos. |
| `receiver.py` | Hilo daemon que escucha el socket y desempaqueta tramas TLV entrantes. |
| `state.py` | Estado centralizado de la sesión (nombre, chats, archivos, solicitudes). |
| `buffer.py` | Cola asíncrona de eventos hacia la GUI. Resiliente: errores del callback no matan el hilo. |
| `gui/` | `index.html` + `style.css` + `script.js` — interfaz completamente desacoplada del Python. |

---

### 📁 Archivos raíz

| Archivo | Rol |
|---|---|
| `servidor.py` | Punto de entrada del servidor. Instancia `ServerFacade(port=5000)`. |
| `cliente.py` | Punto de entrada del cliente. Lanza la GUI como proceso desvinculado (`pythonw.exe`). Errores capturados en `client_stderr.log`. |
| `test_logger.py` | Script de prueba de conexión TCP básica (handshake TLV). |
| `test_client_logic.py` | Script de prueba completa del ciclo connect → set_name → NAME_OK sin GUI. |

---

## 🛰️ Protocolo TLV

Protocolo personalizado sobre TCP: `[Type (1B)] [Length (4B BE)] [Value (NB)]`

| Tipo | Uso |
|---|---|
| `0` | Mensaje de texto entre usuarios |
| `1` | Comando de control (SET_NAME, REQ_CHAT, ACCEPT_CHAT, etc.) |
| `2` | Binario genérico (archivos con metadatos de origen y nombre embebidos) |

---

## 🚀 Ejecución

**Requisitos:** Python 3.10+

```powershell
# Terminal 1 — Servidor
python servidor.py

# Terminal 2 — Cliente (se abre en ventana separada)
python cliente.py
```

---

## 🧪 Cómo probar el sistema

1. **Lanzar el servidor**: `python servidor.py` — muestra el banner con la IP de red.
2. **Lanzar dos clientes**: `python cliente.py` dos veces (dos ventanas GUI).
3. **Conectar**: En cada ventana, ingresar host (`127.0.0.1` o la IP del banner), puerto `5000` y un nickname distinto.
4. **Descubrir usuarios**: Escribir `list` en la entrada de comandos.
5. **Iniciar chat**: Cliente A escribe `chat:NombreDeB`. Cliente B responde `accept`.
6. **Mensajear**: Cualquier texto en la entrada se envía al chat activo.
7. **Enviar archivo**: Escribir `file` → selector nativo → receptor escribe `accept` → elige carpeta.
8. **Salir**: Escribir `exit`.

Para probar sin GUI:
```powershell
python test_client_logic.py 127.0.0.1 5000 MiNick
```

---

## 🔍 Diagnóstico

| Log | Contenido |
|---|---|
| `server.log` | Registro persistente de todos los eventos del servidor en texto plano. |
| `client_stderr.log` | Errores internos del proceso GUI silencioso (`pythonw.exe`). |

---

*Desarrollado para la asignatura de Sistemas Distribuidos.*
