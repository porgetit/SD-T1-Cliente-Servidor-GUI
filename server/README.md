# Componente Servidor - Chat Modular

Este directorio contiene el núcleo del sistema de mensajería, diseñado bajo una arquitectura modular, multihilo y agnóstica a la infraestructura.

## 🏗️ Arquitectura de Software

El servidor se ha estructurado siguiendo principios de separación de responsabilidades para facilitar su escalabilidad y mantenimiento:

### Componentes Clave:
- **`facade.py` (Fachada)**: Proporciona una interfaz simplificada (`ServerFacade`) para iniciar y controlar el servidor, ocultando la complejidad interna del sistema.
- **`core.py` (Núcleo)**: Contiene la clase `ChatServer`, que gestiona el ciclo de vida de las conexiones, el estado global de los usuarios y el despacho de mensajes.
- **`session.py` (Gestión de Sesiones)**: La clase `ClientSession` encapsula la comunicación directa con un socket, manejando el envío y recepción de datos en formato TLV.
- **`buffer.py` (Buffer de Peticiones)**: Implementa una cola de prioridad FIFO que asegura que todas las peticiones entrantes sean procesadas de forma secuencial y ordenada por un hilo trabajador dedicado, evitando condiciones de carrera en el estado global.
- **`handlers.py` (Manejadores de Protocolo)**: Centraliza la lógica de interpretación de comandos (JSON/Texto) y el enrutamiento de datos binarios.
- **`logger.py` (Logging Enriquecido)**: Utiliza la librería `rich` para proporcionar una consola administrativa visual y detallada de eventos en tiempo real.

---

## 🛰️ Protocolo de Comunicación (TLV)

El servidor utiliza un protocolo de red personalizado basado en **TLV (Type-Length-Value)** sobre TCP. Este diseño garantiza que el servidor pueda manejar datos heterogéneos (texto, comandos, binarios) de forma eficiente.

### Estructura del Paquete:
- **Type (1 byte)**: Identifica el tipo de mensaje (0: Texto, 1: Comando, 2: Binario/Archivo).
- **Length (4 bytes)**: Entero sin signo (Big-Endian) que indica el tamaño del payload.
- **Value (N bytes)**: El contenido real del mensaje.

---

## 🏢 Agnóstico a la Infraestructura

Una característica fundamental de este servidor es que es **totalmente agnóstico a la infraestructura** donde se despliega. Esto se logra mediante:

1.  **Detección Dinámica de IP**: Utiliza un "probe" de socket para identificar la interfaz de red local activa, permitiendo que el servidor se autoconfigure en diferentes entornos (LAN, VPN, localhost) sin intervención manual.
2.  **Abstracción de Sockets**: La lógica de negocio no depende de configuraciones específicas del SO, sino que interactúa con la capa de abstracción de Python `socket`.
3.  **Independencia de Persistencia**: Actualmente, el servidor mantiene el estado en memoria RAM, lo que elimina dependencias de bases de datos externas y facilita despliegues rápidos en contenedores o máquinas virtuales ligeras.
4.  **Concurrencia Nativa**: El uso de `threading` permite un escalado vertical eficiente sin requerir orquestadores complejos de procesos externos para una carga de usuarios moderada.

---

## 🚀 Flujo de Operación

1.  **Arranque**: `servidor.py` verifica dependencias, instancia `ServerFacade`, vincula el socket a un puerto (por defecto 5000) y comienza el loop de aceptación.
2.  **Aceptación**: Cada cliente nuevo genera una `ClientSession` y un hilo dedicado para la recepción (`_handle_client`).
3.  **Buffering**: Las ráfagas de mensajes entrantes se depositan en el `RequestBuffer`.
4.  **Procesamiento**: El hilo `worker` del buffer extrae las peticiones y llama a `ProtocolHandlers.dispatch`.
5.  **Enrutamiento**: Si el mensaje es una transferencia de archivos (Tipo 2), el servidor busca la sesión del destinatario y reenvía el payload binario con metadatos de origen inyectados.

## 🛠️ Requisitos
- **Python 3.10+**
- **Librerías**: Gestionadas automáticamente mediante `requirements.txt` (usa `rich` para el logging visual).
