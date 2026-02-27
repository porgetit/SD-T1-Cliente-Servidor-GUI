# Componente Servidor - Chat Modular

Este directorio contiene el núcleo del sistema de mensajería, diseñado bajo una arquitectura modular, multihilo y agnóstica a la infraestructura. El servidor expone sus eventos internos a través de un sistema de observadores intercambiables, separando completamente la lógica de negocio del sistema de salida.

## 🏗️ Arquitectura de Software

El servidor implementa el **patrón Observer** para desacoplar la lógica de red de cualquier sistema de presentación (consola, GUI, API REST).

### Capa de Negocio:
- **`core.py` (ChatServer)**: Gestiona el ciclo de vida de conexiones, el estado global de usuarios y el enrutamiento de mensajes. Hereda de `Observable` y emite **eventos semánticos tipados** ante cada acción interna — sin ningún conocimiento del sistema de salida.
- **`handlers.py` (ProtocolHandlers)**: Centraliza la interpretación del protocolo de comandos y el enrutamiento de datos binarios.
- **`buffer.py` (RequestBuffer)**: Cola FIFO serializada para procesar peticiones de red en orden. Notifica al sistema de eventos en caso de error.
- **`session.py` (ClientSession)**: Abstracción sobre el socket TCP. Maneja el envío y recepción de tramas TLV.

### Capa de Eventos (nueva):
- **`events.py`**: Catálogo de dataclasses inmutables que representan cada evento del servidor (`ServerStarted`, `ClientJoined`, `FileTransferRouted`, `BufferError`, etc.). Son datos puros, sin dependencias de presentación.
- **`observable.py`**: Mixin `Observable` thread-safe que dota a cualquier clase de la capacidad de emitir eventos (`emit`) y registrar observers (`subscribe`/`unsubscribe`).

### Capa de Presentación:
- **`logger.py` (ServerObserver)**: Observer concreto que traduce los eventos semánticos del servidor a dos salidas paralelas: consola Rich formateada y archivo de log de texto plano (`server.log`). Internamente usa dos workers asíncronos en colas separadas para no bloquear el servidor. Para cambiar la presentación (GUI, API, etc.), basta con implementar un nuevo observer y suscribirlo.

### Punto de Cableado:
- **`facade.py` (ServerFacade)**: Único lugar donde se instancia el servidor y sus observers y se conectan entre sí. Expone una interfaz mínima (`run()`) para el punto de entrada.

---

## 🛰️ Protocolo de Comunicación (TLV)

El servidor utiliza un protocolo de red personalizado basado en **TLV (Type-Length-Value)** sobre TCP.

### Estructura del Paquete:
- **Type (1 byte)**: Identifica el tipo de mensaje (`0`: Texto, `1`: Comando, `2`: Binario/Archivo).
- **Length (4 bytes)**: Entero sin signo (Big-Endian) que indica el tamaño del payload.
- **Value (N bytes)**: El contenido del mensaje.

---

## 🔌 Cómo añadir un nuevo observer

Para integrar una GUI, API REST u otro sistema de salida sin tocar el servidor:

```python
# En facade.py (única modificación necesaria)
from .mi_gui_observer import MiGuiObserver

self._server.subscribe(MiGuiObserver())
self._server.subscribe(self._observer)   # el logger original sigue funcionando
```

Cada observer recibe todos los eventos e implementa `__call__(self, event)`.

---

## 🏢 Agnóstico a la Infraestructura

1. **Detección dinámica de IP**: Probe de socket para identificar la interfaz activa sin configuración manual.
2. **Estado en memoria**: Sin dependencias de bases de datos externas.
3. **Concurrencia nativa**: `threading` para escalado vertical eficiente.

---

## 🚀 Flujo de Operación

1. **Arranque**: `servidor.py` instancia `ServerFacade` que conecta `ChatServer` ↔ `ServerObserver`.
2. **Inicio**: El servidor emite `ServerStarted` → el observer registra el banner.
3. **Aceptación**: Cada cliente genera una `ClientSession` y un hilo dedicado; el servidor emite `ClientHandshakeStarted`.
4. **Buffering**: Los mensajes entrantes van al `RequestBuffer` serializado.
5. **Procesamiento**: `ProtocolHandlers.dispatch` resuelve el comando y el servidor emite el evento de resultado (`ClientJoined`, `ChatEstablished`, `FileTransferRouted`, etc.).
6. **Salida**: El `ServerObserver` recibe el evento y lo distribuye a sus workers de consola y archivo.

---

## 🛠️ Requisitos
- **Python 3.10+**
- **Librerías**: `rich` (logging visual). Gestionadas mediante `requirements.txt`.
