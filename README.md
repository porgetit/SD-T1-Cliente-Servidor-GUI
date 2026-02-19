# Sistema de Multi-Chat Modular (Protocolo TLV)

Este proyecto implementa un sistema de mensajería asíncrono y distribuido utilizando la arquitectura **Cliente-Servidor**, sobre protocolos **IPv4** y **TCP/IP**. El sistema ha sido diseñado bajo principios sólidos de ingeniería de software para garantizar la escalabilidad, mantenibilidad y robustez en la transferencia de datos binarios.

## 🚀 Características Principales

- **Gestión de Nicknames**: Registro único de usuarios mediante un handshake de confirmación.
- **Multiprocesamiento Ordenado**: Uso de colas de peticiones para garantizar que los mensajes se procesen en el orden exacto de llegada.
- **Doble Buffer de Sincronización**: Sistema que evita el solapamiento de mensajes entrantes con la entrada de texto del usuario en la consola.
- **Transferencia Universal**: Soporte para envío de cualquier tipo de archivo (binario o texto) sin restricciones de extensión.
- **Descargas Automáticas**: Organización dinámica de archivos recibidos en la carpeta `Downloads` del sistema.

## 🛠️ Arquitectura y Diseño

El sistema se encuentra dentro de la carpeta `thread/` y está dividido en dos grandes paquetes independientes:

### 1. Servidor (`thread/server/`)
- **`facade.py`**: Punto de entrada simplificado (Patrón Fachada).
- **`core.py`**: Orquestación principal, manejo de conexiones y enrutado de archivos genéricos.
- **`session.py`**: Abstracción de bajo nivel para la comunicación por socket.
- **`buffer.py`**: Implementa el `RequestBuffer` para la serialización de tareas concurrentes.
- **`handlers.py`**: Despacho de la lógica de negocio según el protocolo.

### 2. Cliente (`thread/client/`)
- **`facade.py`**: Fachada para el inicio del cliente.
- **`core.py`**: Manejo de entrada de usuario y preparación de payloads binarios.
- **`receiver.py`**: Hilo de fondo dedicado a la escucha, parseo de red y reconstrucción de archivos.
- **`buffer.py`**: `EventBuffer` que gestiona la salida limpia por consola.
- **`state.py`**: Repositorio central de información.

## 📡 Protocolo TLV Simplificado (3 Tipos)

Para la comunicación, utilizamos un patrón de **empaquetamiento binario framing** optimizado. Cada mensaje transmitido sigue este patrón:

| Campo | Tamaño | Formato (`struct`) | Descripción |
| :--- | :--- | :--- | :--- |
| **Tipo** | 1 Byte | `B` (Unsigned Char) | `0`: Texto, `1`: Comando, `2`: Binario Genérico |
| **Longitud** | 4 Bytes | `I` (Unsigned Int) | Tamaño exacto del payload total en bytes |

### Estructura del Payload Binario (Tipo 2)
Para permitir el envío de **cualquier archivo**, el payload de Tipo 2 utiliza un encapsulamiento interno (Doble TLV) que viaja de la siguiente forma:

1. `[LongitudNombre(1B)]`: Longitud del nombre del archivo.
2. `[NombreArchivo(NB)]`: Nombre original con extensión (ej: `foto.png`, `main.py`).
3. `[ContenidoBinario(MB)]`: El flujo de bytes puro del archivo.

> [!IMPORTANT]
> Se utiliza el prefijo `!` en `struct.pack("!BI", ...)` para forzar el **Network Byte Order (Big-Endian)**, garantizando que máquinas con diferentes arquitecturas (Windows/Linux) se entiendan perfectamente.

## 💡 Justificación Técnica

### ¿Por qué Modularidad y SRP?
Originalmente, el sistema era un archivo monolítico. Aplicamos el **Principio de Responsabilidad Única (SRP)** para separar la lógica de red de la lógica de interfaz (UI). Esto permite:
- **Testabilidad**: Probar el envío de archivos sin necesidad de lanzar la UI.
- **Mantenibilidad**: Corregir errores en el buffer sin afectar el protocolo.

### ¿Por qué TLV?
La red es un flujo continuo de bytes. Sin un patrón de empaquetamiento, es imposible distinguir dónde termina un mensaje y empieza otro (problema de concatenación de sockets). El patrón **TLV** permite al receptor saber exactamente cuántos bytes debe esperar antes de procesar un mensaje completo. 

Nuestra implementación de **Doble TLV para archivos** permite que cualquier formato (ej: código fuente, ejecutables, comprimidos) viaje con su propio "DNI" (nombre y extensión), logrando un sistema 100% agnóstico al tipo de dato.

## 📋 Requisitos y Ejecución

- **Python 3.10+** (Sin dependencias externas).

### Servidor
```powershell
python thread/server_app.py
```

### Cliente
```powershell
python thread/client_app.py
```

### Comandos del Cliente
- `list`: Muestra usuarios conectados.
- `chat:<nickname>`: Inicia un chat con un usuario.
- `file:<ruta_absoluta>`: Envía un archivo al chat actual.
- `stop`: Finaliza el chat activo.
- `exit`: Cierra la sesión.

## ⚠️ Limitaciones
- **Alcance**: Diseñado para redes locales o VPNs punto a punto.
- **Persistencia**: Los nicknames y chats se pierden al reiniciar el servidor (no usa base de datos).
- **Seguridad**: Los datos se transmiten sin cifrado (TCP plano).

---
*Desarrollado como solución robusta para el ejercicio de sistemas distribuidos.*
