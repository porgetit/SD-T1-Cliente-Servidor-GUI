#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket

# Solicitar al usuario la dirección del servidor
print("="*45)
host = input("  Ingrese la IP del servidor  : ").strip()
port = int(input("  Ingrese el puerto del servidor: ").strip())
print("="*45)

# Crear un socket TCP/IP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conectar el socket al servidor remoto
sock.connect((host, port))
print(f"Conectado al servidor {host}:{port}")

while True:
    # Enviar datos al servidor
    message = input("Ingrese un mensaje para el servidor: ")
    if message.lower() == 'exit!':
        break

    sock.sendall(message.encode('utf-8'))

    # Recibir respuesta del servidor
    data = sock.recv(1024)
    print(f"Respuesta del servidor: {data.decode('utf-8')}")

# Cerrar la conexión
sock.close()
