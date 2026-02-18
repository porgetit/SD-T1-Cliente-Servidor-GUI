#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket

# Detectar automáticamente la IP local de esta máquina
def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))  # No envía datos; solo determina la interfaz de salida
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

host = obtener_ip_local()
port = 0  # 0 = el SO asigna un puerto libre automáticamente

# Crear un socket TCP/IP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Enlace del socket a la dirección y puerto
sock.bind((host, port))

# Escuchar conexiones entrantes
sock.listen(1)

# Obtener el puerto real asignado por el SO
host_real, port_real = sock.getsockname()
print("="*45)
print(f"  Servidor listo. Comparte estos datos con el cliente:")
print(f"  IP   : {host_real}")
print(f"  Puerto: {port_real}")
print("="*45)

# Esperar una conexión
conn, addr = sock.accept()
print(f"Conexión establecida desde: {addr}")

while True:
    # Recibir datos del cliente
    data = conn.recv(1024)
    if not data:
        break
    print(f"Mensaje recibido del cliente: {data.decode('utf-8')}")

    # Enviar respuesta al cliente
    response = input("Ingrese la respuesta para el cliente: ")
    conn.sendall(response.encode('utf-8'))

# Cerrar la conexión
conn.close()
