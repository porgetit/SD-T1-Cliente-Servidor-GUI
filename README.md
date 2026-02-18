# SD-T1: Sistema Cliente-Servidor con Sockets TCP/IP

## Descripción General

Este proyecto implementa un sistema de comunicación **cliente-servidor** usando la biblioteca estándar `socket` de Python. Sigue el modelo clásico de arquitectura distribuida **Cliente-Servidor**, donde un proceso actúa como proveedor de servicios (servidor) y otro como consumidor (cliente), comunicándose a través de la red mediante el protocolo **TCP/IP**.

---

## Modelo Arquitectónico: Cliente-Servidor

```
┌─────────────────────────────────────────────────────────┐
│                    RED TCP/IP                           │
│                                                         │
│   ┌──────────────┐   Mensajes    ┌──────────────────┐   │
│   │  clientep.py │ ────────────► │   serverp.py     │   │
│   │  (Cliente)   │ ◄──────────── │   (Servidor)     │   │
│   └──────────────┘   Respuestas  └──────────────────┘   │
│   172.16.0.64:XXXX               172.16.0.64:12345      │
└─────────────────────────────────────────────────────────┘
```

- **Protocolo de transporte:** TCP (`SOCK_STREAM`) — orientado a conexión, confiable y ordenado.
- **Familia de direcciones:** IPv4 (`AF_INET`).
- **Dirección del servidor:** `172.16.0.64`, puerto `12345`.
- **Flujo de comunicación:** El cliente inicia la conexión; el servidor acepta y responde. El intercambio es **interactivo y bidireccional** (half-duplex por turnos).

---

## `serverp.py` — El Servidor

### Función

`serverp.py` es el **proceso servidor**. Su responsabilidad es:
1. Ponerse a la escucha en una dirección y puerto conocidos.
2. Aceptar la conexión entrante de un cliente.
3. Recibir mensajes del cliente en un bucle continuo.
4. Pedir al operador humano que escriba una respuesta y enviarla de vuelta al cliente.
5. Cerrar la conexión cuando el cliente deja de enviar datos.

### Análisis línea a línea

```python
import socket
```
> **Línea 1.** Importa el módulo `socket` de la biblioteca estándar de Python. Este módulo expone la API de sockets del sistema operativo, permitiendo crear conexiones de red.

---

```python
host = '172.16.0.64'  # Dirección IPv4 del servidor
port = 12345          # Puerto arbitrario
```
> **Líneas 4-5.** Define las constantes de red:
> - `host`: la dirección IP de la interfaz de red en la que el servidor escuchará. Al usar una IP específica (en lugar de `''` o `'0.0.0.0'`), el servidor solo acepta conexiones que lleguen por esa interfaz.
> - `port`: número de puerto lógico (1024–65535 son de uso libre). El cliente debe conocer este valor para conectarse.

---

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
> **Línea 8.** Crea el objeto socket con dos parámetros:
> - `socket.AF_INET`: familia de direcciones IPv4.
> - `socket.SOCK_STREAM`: tipo de socket orientado a conexión (protocolo TCP). Garantiza entrega ordenada y sin duplicados.

---

```python
sock.bind((host, port))
```
> **Línea 11.** **`bind()`** asocia el socket a la dirección `(host, port)`. A partir de este momento el sistema operativo reserva ese puerto para este proceso. Recibe una tupla, no dos argumentos separados.

---

```python
sock.listen(1)
```
> **Línea 14.** **`listen(backlog)`** pone el socket en modo pasivo (escucha). El argumento `1` es el tamaño de la cola de conexiones pendientes: solo se encola 1 cliente a la vez antes de ser aceptado. Para servidores concurrentes este valor suele ser mayor.

---

```python
print(f"Servidor escuchando en {host}:{port}")
```
> **Línea 16.** Mensaje informativo en consola que confirma que el servidor está listo y esperando.

---

```python
conn, addr = sock.accept()
```
> **Línea 19.** **`accept()`** bloquea la ejecución hasta que un cliente se conecta. Devuelve:
> - `conn`: un **nuevo socket** dedicado exclusivamente a esta conexión (el socket original `sock` sigue disponible para aceptar más clientes si fuera necesario).
> - `addr`: tupla `(ip_cliente, puerto_cliente)` que identifica al cliente remoto.

---

```python
print(f"Conexión establecida desde: {addr}")
```
> **Línea 20.** Imprime la dirección del cliente conectado, útil para depuración y auditoría.

---

```python
while True:
```
> **Línea 22.** Bucle infinito que mantiene la sesión activa. El servidor seguirá recibiendo y respondiendo mensajes hasta que el cliente cierre la conexión.

---

```python
    data = conn.recv(1024)
```
> **Línea 24.** **`recv(bufsize)`** lee hasta `1024` bytes del socket de conexión. Es una operación **bloqueante**: el hilo espera hasta que lleguen datos. Devuelve `bytes`.

---

```python
    if not data:
        break
```
> **Líneas 25-26.** Cuando el cliente cierra su extremo de la conexión, `recv()` devuelve `b''` (bytes vacíos). La condición `not data` detecta este caso y rompe el bucle, terminando el servidor de forma limpia.

---

```python
    print(f"Mensaje recibido del cliente: {data.decode('utf-8')}")
```
> **Línea 27.** **`decode('utf-8')`** convierte los bytes recibidos a cadena de texto Python usando la codificación UTF-8. Luego imprime el mensaje en consola.

---

```python
    response = input("Ingrese la respuesta para el cliente: ")
```
> **Línea 30.** Solicita al operador del servidor que escriba una respuesta de forma interactiva. Esto convierte al servidor en un sistema de **chat manual** en lugar de uno automatizado.

---

```python
    conn.sendall(response.encode('utf-8'))
```
> **Línea 31.** **`sendall()`** envía todos los bytes de la respuesta al cliente.
> - **`encode('utf-8')`**: convierte la cadena de texto a bytes antes de enviarla (los sockets solo transmiten bytes).
> - **`sendall()`** (vs `send()`): garantiza que todos los datos sean enviados, reintentando internamente si el buffer del sistema operativo no los acepta de una sola vez.

---

```python
conn.close()
```
> **Línea 34.** **`close()`** libera el descriptor de fichero del socket de conexión y notifica al cliente que la sesión ha terminado (envía un segmento TCP FIN). Es buena práctica cerrarlo explícitamente aunque el programa termine.

---

### Métodos de `socket` utilizados en `serverp.py`

| Método | Descripción |
|---|---|
| `socket.socket(AF_INET, SOCK_STREAM)` | Crea un socket TCP/IPv4 |
| `sock.bind((host, port))` | Asocia el socket a una dirección y puerto locales |
| `sock.listen(backlog)` | Pone el socket en modo escucha pasiva |
| `sock.accept()` | Bloquea hasta aceptar una conexión; devuelve `(conn, addr)` |
| `conn.recv(bufsize)` | Lee hasta `bufsize` bytes del cliente (bloqueante) |
| `conn.sendall(data)` | Envía todos los bytes de `data` al cliente |
| `conn.close()` | Cierra el socket de conexión |

---

## `clientep.py` — El Cliente

### Función

`clientep.py` es el **proceso cliente**. Su responsabilidad es:
1. Conectarse al servidor en la dirección y puerto conocidos.
2. Pedir al usuario que escriba un mensaje y enviarlo al servidor.
3. Esperar y mostrar la respuesta del servidor.
4. Preguntar si se desea continuar o terminar la sesión.
5. Cerrar la conexión al salir.

### Encaje en la arquitectura

El cliente es el **iniciador activo** de la comunicación. A diferencia del servidor, no necesita `bind()` ni `listen()`: el sistema operativo le asigna automáticamente un puerto efímero al momento de conectarse. El cliente conoce de antemano la dirección del servidor (`172.16.0.64:12345`) y establece el canal TCP mediante el *three-way handshake* que gestiona el propio sistema operativo.

```
Cliente                          Servidor
   │──── SYN ──────────────────────►│
   │◄─── SYN-ACK ───────────────────│
   │──── ACK ──────────────────────►│  ← Conexión establecida
   │──── Mensaje (bytes) ──────────►│
   │◄─── Respuesta (bytes) ─────────│
   │──── FIN ──────────────────────►│  ← sock.close()
```

### Análisis línea a línea

```python
import socket
```
> **Línea 1.** Importa el módulo `socket`, igual que en el servidor.

---

```python
host = '172.16.0.64'
port = 12345
```
> **Líneas 4-5.** Mismas constantes que en el servidor. El cliente **debe** conocer la IP y el puerto del servidor para poder conectarse. Estos valores deben coincidir exactamente con los del servidor.

---

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
> **Línea 8.** Crea un socket TCP/IPv4, idéntico al del servidor. Ambos extremos deben usar el mismo tipo de socket para que la comunicación sea posible.

---

```python
sock.connect((host, port))
```
> **Línea 11.** **`connect()`** inicia el *three-way handshake* TCP hacia el servidor en `(host, port)`. Esta llamada es **bloqueante** hasta que la conexión se establece o falla (lanzando una excepción como `ConnectionRefusedError` si el servidor no está disponible). Es el equivalente activo de `accept()` en el servidor.

---

```python
while True:
```
> **Línea 13.** Bucle que permite enviar múltiples mensajes en la misma sesión, sin necesidad de reconectarse.

---

```python
    message = input("Ingrese un mensaje para el servidor: ")
```
> **Línea 15.** Solicita al usuario que escriba el mensaje a enviar. La ejecución se bloquea aquí hasta que el usuario presiona Enter.

---

```python
    sock.sendall(message.encode('utf-8'))
```
> **Línea 16.** **`sendall()`** envía el mensaje codificado en UTF-8 al servidor. Al igual que en el servidor, `encode()` convierte la cadena a bytes y `sendall()` garantiza el envío completo.

---

```python
    data = sock.recv(1024)
```
> **Línea 19.** **`recv(1024)`** espera y recibe la respuesta del servidor (hasta 1024 bytes). La ejecución se bloquea aquí hasta que el servidor envíe datos. Devuelve `bytes`.

---

```python
    print(f"Respuesta del servidor: {data.decode('utf-8')}")
```
> **Línea 20.** Decodifica la respuesta de bytes a texto UTF-8 y la muestra en consola.

---

```python
    continuar = input("¿Desea enviar otro mensaje? (s/n): ")
    if continuar.lower() != 's':
        break
```
> **Líneas 23-25.** Mecanismo de control de flujo del lado del cliente:
> - Pregunta al usuario si desea continuar.
> - **`lower()`** normaliza la entrada a minúsculas para aceptar tanto `'S'` como `'s'`.
> - Si la respuesta no es `'s'`, se rompe el bucle y la sesión termina.

---

```python
sock.close()
```
> **Línea 28.** **`close()`** cierra el socket del cliente. Esto envía un segmento TCP FIN al servidor, lo que hace que `conn.recv()` en el servidor devuelva `b''` y el servidor también termine su bucle limpiamente.

---

### Métodos de `socket` utilizados en `clientep.py`

| Método | Descripción |
|---|---|
| `socket.socket(AF_INET, SOCK_STREAM)` | Crea un socket TCP/IPv4 |
| `sock.connect((host, port))` | Inicia la conexión TCP hacia el servidor |
| `sock.sendall(data)` | Envía todos los bytes de `data` al servidor |
| `sock.recv(bufsize)` | Lee hasta `bufsize` bytes de la respuesta del servidor |
| `sock.close()` | Cierra el socket y notifica al servidor el fin de sesión |

---

## Flujo de Ejecución Completo

```
SERVIDOR (serverp.py)              CLIENTE (clientep.py)
─────────────────────              ─────────────────────
socket()                           socket()
bind()
listen()
accept() ──── espera ────────────► connect()
                                   input() → sendall()
recv() ◄─────────────────────────── (mensaje)
print(mensaje)
input() → sendall()
(respuesta) ──────────────────────► recv()
                                    print(respuesta)
                                    input("¿continuar?")
                                    [si 'n'] → close()
recv() → b'' → break ◄──────────── (FIN TCP)
close()
```

---

## Cómo Ejecutar

> **Requisito:** Python 3.x instalado. Ambos equipos deben poder alcanzarse en la red (o ejecutarse en la misma máquina).

**1. Iniciar el servidor primero:**
```bash
python serverp.py
```

**2. Iniciar el cliente (en otra terminal o equipo):**
```bash
python clientep.py
```

**3. Interactuar:** El cliente escribe mensajes, el servidor responde manualmente, hasta que el cliente decide terminar.

---

## Limitaciones del Diseño Actual

- **Un solo cliente:** `sock.listen(1)` y la ausencia de hilos o `select()` limitan el servidor a atender un único cliente por ejecución.
- **Sin manejo de errores:** No hay bloques `try/except` para gestionar desconexiones abruptas o errores de red.
- **Respuesta manual:** El servidor requiere un operador humano para responder; no es un servidor automatizado.
- **Sin cifrado:** La comunicación viaja en texto plano por la red.
