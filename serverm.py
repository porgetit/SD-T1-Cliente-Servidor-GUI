#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import random

# Diccionario para rastrear clientes: {nombre: socket}
clientes = {}
# Conjunto para rastrear sesiones activas: {(usuario1, usuario2)}
sesiones_activas = set()
# Conjunto para rastrear quién tiene una solicitud pendiente de responder
pendientes_recibir = set()
# Bloqueo para acceso seguro a las estructuras de datos desde múltiples hilos
lock = threading.Lock()

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def enviar_lista_usuarios(conn):
    with lock:
        lista = ",".join(clientes.keys())
    conn.sendall(f"LIST_USERS:{lista}".encode('utf-8'))

def handle_client(conn, addr, nombre):
    print(f"[NUEVA CONEXIÓN] {nombre} ({addr}) conectado.")
    
    # Notificar al cliente su nombre asignado
    conn.sendall(f"ASSIGN_NAME:{nombre}".encode('utf-8'))
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            mensaje_raw = data.decode('utf-8')
            
            if mensaje_raw == "GET_USERS":
                enviar_lista_usuarios(conn)
            
            elif mensaje_raw.startswith("REQ_CHAT:"):
                destino = mensaje_raw.split(":", 1)[1]
                with lock:
                    if destino in clientes:
                        if destino in pendientes_recibir:
                            conn.sendall(f"ERROR:Usuario {destino} está ocupado con otra solicitud.".encode('utf-8'))
                        else:
                            pendientes_recibir.add(destino)
                            clientes[destino].sendall(f"REQ_CHAT_FROM:{nombre}".encode('utf-8'))
                    else:
                        conn.sendall(f"ERROR:Usuario {destino} no encontrado".encode('utf-8'))
            
            elif mensaje_raw.startswith("ACCEPT_CHAT:"):
                remitente_req = mensaje_raw.split(":", 1)[1]
                with lock:
                    pendientes_recibir.discard(nombre)
                    if remitente_req in clientes:
                        sesiones_activas.add((nombre, remitente_req))
                        sesiones_activas.add((remitente_req, nombre))
                        print(f"[CHAT ESTABLECIDO] {nombre} <-> {remitente_req}")
                        clientes[remitente_req].sendall(f"CHAT_ACCEPTED:{nombre}".encode('utf-8'))
                        conn.sendall(f"CHAT_ACCEPTED:{remitente_req}".encode('utf-8'))
                    else:
                        conn.sendall(f"ERROR:Usuario {remitente_req} ya no está conectado".encode('utf-8'))
            
            elif mensaje_raw.startswith("DENY_CHAT:"):
                remitente_req = mensaje_raw.split(":", 1)[1]
                with lock:
                    pendientes_recibir.discard(nombre)
                    if remitente_req in clientes:
                        clientes[remitente_req].sendall(f"CHAT_DENIED:{nombre}".encode('utf-8'))
            
            elif mensaje_raw.startswith("STOP_CHAT:"):
                destino_chat = mensaje_raw.split(":", 1)[1]
                print(f"[CHAT FINALIZADO] {nombre} ha terminado el chat con {destino_chat}")
                with lock:
                    sesiones_activas.discard((nombre, destino_chat))
                    sesiones_activas.discard((destino_chat, nombre))
                    if destino_chat in clientes:
                        clientes[destino_chat].sendall(f"CHAT_STOPPED:{nombre}".encode('utf-8'))
            
            elif mensaje_raw.startswith("CHAT:"):
                # Formato: CHAT:<destino>:<mensaje>
                try:
                    _, destino_msg, msg = mensaje_raw.split(":", 2)
                    with lock:
                        if (nombre, destino_msg) in sesiones_activas:
                            if destino_msg in clientes:
                                target_sock = clientes[destino_msg]
                                target_sock.sendall(f"FROM:{nombre}:{msg}".encode('utf-8'))
                            else:
                                conn.sendall(f"ERROR:Usuario {destino_msg} desconectado".encode('utf-8'))
                                sesiones_activas.discard((nombre, destino_msg))
                                sesiones_activas.discard((destino_msg, nombre))
                        else:
                            conn.sendall(f"ERROR:No tienes un chat activo con {destino_msg}. Debes pedir permiso primero.".encode('utf-8'))
                except ValueError:
                    conn.sendall("ERROR:Formato de mensaje inválido".encode('utf-8'))
            
    except Exception as e:
        print(f"[ERROR] {nombre}: {e}")
    finally:
        with lock:
            if nombre in clientes:
                del clientes[nombre]
            # Limpiar estado del usuario desconectado
            pendientes_recibir.discard(nombre)
            sesiones_ha_eliminar = [s for s in sesiones_activas if nombre in s]
            for s in sesiones_ha_eliminar:
                sesiones_activas.discard(s)
        print(f"[DESCONEXIÓN] {nombre} desconectado.")
        conn.close()

def main():
    host = obtener_ip_local()
    port = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen()

    host_real, port_real = sock.getsockname()
    print("="*45)
    print(f"  Servidor de Chat con Confirmación listo.")
    print(f"  IP   : {host_real}")
    print(f"  Puerto: {port_real}")
    print("="*45)

    while True:
        conn, addr = sock.accept()
        nombre = f"User_{random.randint(1000, 9999)}"
        
        with lock:
            clientes[nombre] = conn
            
        thread = threading.Thread(target=handle_client, args=(conn, addr, nombre))
        thread.start()
        print(f"[CONEXIONES ACTIVAS] {len(clientes)}")

if __name__ == "__main__":
    main()
