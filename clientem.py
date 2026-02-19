#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import sys

# Variables globales para rastrear el estado del chat
solicitud_pendiente_de = None
mi_nombre = None
# Conjunto de usuarios con los que tenemos un chat aceptado
sesiones_abiertas = set()
# Destinatario al que enviamos mensajes actualmente
destino_actual = None

def receive_messages(sock):
    """Hilo para recibir mensajes del servidor de forma asíncrona."""
    global solicitud_pendiente_de, mi_nombre, destino_actual
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            
            mensaje = data.decode('utf-8')
            
            if mensaje.startswith("ASSIGN_NAME:"):
                mi_nombre = mensaje.split(":")[1]
                print(f"\n[SISTEMA] Tu nombre es: {mi_nombre}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("LIST_USERS:"):
                usuarios = mensaje.split(":")[1]
                print(f"\n[USUARIOS CONECTADOS] {usuarios}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("REQ_CHAT_FROM:"):
                solicitud_pendiente_de = mensaje.split(":")[1]
                print(f"\n[SOLICITUD] {solicitud_pendiente_de} quiere chatear contigo. Escribe 'accept' o 'deny'.")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_ACCEPTED:"):
                usuario = mensaje.split(":")[1]
                sesiones_abiertas.add(usuario)
                print(f"\n[SISTEMA] Chat con {usuario} ESTABLECIDO.")
                if not destino_actual:
                    destino_actual = usuario
                    print(f"[INFO] Ahora chateando con {usuario}.")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_DENIED:"):
                usuario = mensaje.split(":")[1]
                print(f"\n[SISTEMA] {usuario} ha rechazado tu solicitud de chat.")
                if destino_actual == usuario:
                    destino_actual = None
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_STOPPED:"):
                usuario = mensaje.split(":")[1]
                print(f"\n[SISTEMA] {usuario} ha finalizado el chat.")
                sesiones_abiertas.discard(usuario)
                if destino_actual == usuario:
                    destino_actual = None
                    print("[INFO] Has vuelto al menú principal. Selecciona otro chat con 'chat:<user>'.")
                print("> ", end="", flush=True)

            elif mensaje.startswith("FROM:"):
                _, remitente, contenido = mensaje.split(":", 2)
                print(f"\n[{remitente}] dice: {contenido}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("ERROR:"):
                print(f"\n[ERROR] {mensaje.split(':', 1)[1]}")
                print("> ", end="", flush=True)
                
        except Exception:
            break
    print("\n[DESCONECTADO] Conexión perdida con el servidor.")

def main():
    global solicitud_pendiente_de, destino_actual
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

    print("\n--- MENÚ DE MULTI-CHAT ---")
    print("Comandos:")
    print("  'list'          - Ver todos los usuarios en el servidor")
    print("  'sessions'      - Ver tus chats activos")
    print("  'chat:<user>'   - Cambiar a o solicitar chat con un usuario")
    print("  'accept'        - Aceptar solicitud entrante")
    print("  'deny'          - Rechazar solicitud entrante")
    print("  'stop'          - Terminar chat actual")
    print("  'stop:<user>'   - Terminar un chat específico")
    print("  'exit'          - Salir")
    print("="*45)

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            
            if line == 'exit':
                break

            # BLOQUEO: Si hay una solicitud pendiente, solo permitir accept/deny
            if solicitud_pendiente_de:
                if line == 'accept':
                    sock.sendall(f"ACCEPT_CHAT:{solicitud_pendiente_de}".encode('utf-8'))
                    solicitud_pendiente_de = None
                elif line == 'deny':
                    sock.sendall(f"DENY_CHAT:{solicitud_pendiente_de}".encode('utf-8'))
                    print(f"[INFO] Solicitud de {solicitud_pendiente_de} rechazada.")
                    solicitud_pendiente_de = None
                else:
                    print(f"[!] BLOQUEO: Debes 'accept' o 'deny' la solicitud de {solicitud_pendiente_de} antes de continuar.")
                continue

            if line == 'list':
                sock.sendall("GET_USERS".encode('utf-8'))
            elif line == 'sessions':
                print(f"[CHATS ACTIVOS] {', '.join(sesiones_abiertas) if sesiones_abiertas else 'Ninguno'}")
                if destino_actual:
                    print(f"[ACTUAL] Chateando con: {destino_actual}")
            elif line.startswith("stop"):
                target_to_stop = None
                if ":" in line:
                    target_to_stop = line.split(":", 1)[1]
                else:
                    target_to_stop = destino_actual
                
                if target_to_stop and target_to_stop in sesiones_abiertas:
                    sock.sendall(f"STOP_CHAT:{target_to_stop}".encode('utf-8'))
                    print(f"[INFO] Chat con {target_to_stop} finalizado.")
                    sesiones_abiertas.discard(target_to_stop)
                    if destino_actual == target_to_stop:
                        destino_actual = None
                elif target_to_stop:
                    print(f"[!] No tienes un chat activo con {target_to_stop}.")
                else:
                    print("[!] No hay ningún chat seleccionado para detener.")
                    
            elif line.startswith("chat:"):
                target = line.split(":", 1)[1]
                if target == mi_nombre:
                    print("[!] No puedes chatear contigo mismo.")
                    continue
                
                if target in sesiones_abiertas:
                    destino_actual = target
                    print(f"[INFO] Cambiado a chat con {target}.")
                else:
                    sock.sendall(f"REQ_CHAT:{target}".encode('utf-8'))
                    print(f"[SISTEMA] Solicitud de chat enviada a {target}. Esperando confirmación...")
                    destino_actual = target # Lo ponemos como actual; los mensajes fallarán hasta que acepte
            else:
                if destino_actual:
                    sock.sendall(f"CHAT:{destino_actual}:{line}".encode('utf-8'))
                else:
                    print("[!] Selecciona un chat con 'chat:<nombre>' o mira tus sesiones con 'sessions'")
        except KeyboardInterrupt:
            break

    sock.close()

if __name__ == "__main__":
    main()
