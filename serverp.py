import socket

# Configuración de red
host = '172.16.0.64'  # Dirección IPv4 del servidor
port = 12345  # Puerto arbitrario

# Crear un socket TCP/IP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Enlace del socket a la dirección y puerto
sock.bind((host, port))

# Escuchar conexiones entrantes
sock.listen(1)

print(f"Servidor escuchando en {host}:{port}")

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
