#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import sys

def receive_messages(sock):
    """Hilo para recibir mensajes del servidor de forma asíncrona."""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            
            mensaje = data.decode('utf-8')
            
            if mensaje.startswith("ASSIGN_NAME:"):
                # El servidor nos asignó un nombre
                mi_nombre = mensaje.split(":")[1]
                print(f"\n[SISTEMA] Tu nombre es: {mi_nombre}")
            
            elif mensaje.startswith("LIST_USERS:"):
                # Lista de usuarios conectados
                usuarios = mensaje.split(":")[1]
                print(f"\n[USUARIOS CONECTADOS] {usuarios}")
            
            elif mensaje.startswith("FROM:"):
                # Mensaje de otro usuario
                _, remitente, contenido = mensaje.split(":", 2)
                print(f"\n[{remitente}] dice: {contenido}")
            
            elif mensaje.startswith("ERROR:"):
                print(f"\n[ERROR] {mensaje.split(':', 1)[1]}")
                
        except Exception:
            break
    print("\n[DESCONECTADO] Conexión perdida con el servidor.")

def main():
    print("="*45)
    host = input("  Ingrese la IP del servidor  : ").strip()
    port = int(input("  Ingrese el puerto del servidor: ").strip())
    print("="*45)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Error al conectar: {e}")
        return

    # Iniciar hilo de recepción
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    print("\n--- MENÚ DE CHAT ---")
    print("Comandos:")
    print("  'list'         - Ver usuarios conectados")
    print("  'chat:<user>'  - Iniciar chat con un usuario")
    print("  'stop'         - Terminar chat actual")
    print("  'exit'         - Salir")
    print("="*45)

    destino = None

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            
            if line == 'exit':
                break
            elif line == 'list':
                sock.sendall("GET_USERS".encode('utf-8'))
            elif line == 'stop':
                if destino:
                    print(f"[INFO] Chat con {destino} finalizado.")
                    destino = None
                else:
                    print("[!] No hay ningún chat activo.")
            elif line.startswith("chat:"):
                destino = line.split(":", 1)[1]
                print(f"[INFO] Ahora chateando con {destino}. Escribe tus mensajes a continuación.")
            else:
                if destino:
                    # Enviar mensaje al destino seleccionado
                    sock.sendall(f"CHAT:{destino}:{line}".encode('utf-8'))
                else:
                    print("[!] Debes seleccionar un destinatario primero con 'chat:<nombre>'")
        except KeyboardInterrupt:
            break

    sock.close()

if __name__ == "__main__":
    main()
