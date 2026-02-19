#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import threading
import struct
from typing import Dict, Optional, Set, Tuple, Any
from .session import ClientSession
from .buffer import RequestBuffer
from .handlers import ProtocolHandlers

def get_local_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        ip: str = probe.getsockname()[0]
    finally:
        probe.close()
    return ip

class ChatServer:
    def __init__(self, host: Optional[str] = None, port: int = 0) -> None:
        self.host: str = host or get_local_ip()
        self.port: int = port
        self._clients: Dict[str, ClientSession] = {}
        self._active_sessions: Set[Tuple[str, str]] = set()
        self._pending_receive: Set[str] = set()
        self._lock = threading.Lock()
        self._buffer = RequestBuffer(self._dispatch_internal)

    def start(self) -> None:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen()

        real_host, real_port = server_sock.getsockname()
        self.port = real_port
        self._print_banner(real_host, real_port)
        self._accept_loop(server_sock)

    def _accept_loop(self, server_sock: socket.socket) -> None:
        while True:
            conn, addr = server_sock.accept()
            # Asignamos un ID temporal hasta que se confirme el nombre
            temp_id = f"Temp_{random.randint(1000, 9999)}"
            session = ClientSession(conn, addr, temp_id)
            # No lo agregamos a _clients todavía formalmente para evitar colisiones de 'list'
            threading.Thread(target=self._handle_client, args=(session,), daemon=True).start()

    def _handle_client(self, session: ClientSession) -> None:
        print(f"[NUEVA CONEXIÓN] Handshake iniciado con {session.address}")
        try:
            while True:
                tlv = session.recv_tlv()
                if not tlv: break
                msg_type, payload = tlv
                # Agregamos al buffer para procesamiento ordenado (incluye binarios)
                self._buffer.add_request(session, msg_type, payload)
        except Exception as exc:
            print(f"[ERROR] {session.name}: {exc}")
        finally:
            self._disconnect(session)

    def _dispatch_internal(self, session: ClientSession, msg_type: int, payload: bytes):
        # Este método es llamado por el worker del RequestBuffer
        ProtocolHandlers.dispatch(self, session, msg_type, payload)

    def handle_file_transfer(self, session: ClientSession, payload: bytes):
        """Reenvía un archivo binario (Tipo 2) al destinatario."""
        try:
            # Formato esperado: target_len(1)|target|filename_len(1)|filename|data
            dst_len = payload[0]
            target_name = payload[1:1+dst_len].decode("utf-8")
            
            with self._lock:
                if (session.name, target_name) not in self._active_sessions:
                    session.send(1, f"ERROR:No tienes un chat activo con {target_name} para enviar archivos.".encode("utf-8"))
                    return
                if target_name not in self._clients:
                    session.send(1, f"ERROR:Usuario {target_name} desconectado".encode("utf-8"))
                    return
                
                # Re-empaquetamos para el receptor: sender_len(1)|sender|filename_len(1)|filename|data
                sender_name = session.name.encode("utf-8")
                # El resto del payload (filename_len + filename + data) ya viene después del destino
                client_payload = bytes([len(sender_name)]) + sender_name + payload[1+dst_len:]
                
                self._clients[target_name].send(2, client_payload)
                print(f"[ARCHIVO] {session.name} -> {target_name} (Enrutado)")
        except Exception as e:
            session.send(1, f"ERROR:Fallo al procesar envío de archivo: {e}".encode("utf-8"))

    def handle_set_name(self, session: ClientSession, new_name: str):
        with self._lock:
            if new_name in self._clients or "Temp_" in new_name:
                session.send(1, b"NAME_TAKEN")
                return
            
            # Registrar el nuevo nombre
            old_name = session.name
            session.name = new_name
            self._clients[new_name] = session
            print(f"[REGISTRO] {new_name} ({session.address}) se ha unido.")
            session.send(1, b"NAME_OK")
            print(f"[CONEXIONES ACTIVAS] {len(self._clients)}")

    def send_user_list(self, session: ClientSession):
        with self._lock:
            user_list = ",".join(self._clients.keys())
        session.send(1, f"LIST_USERS:{user_list}".encode("utf-8"))

    def handle_req_chat(self, session: ClientSession, target_name: str):
        with self._lock:
            if target_name not in self._clients:
                session.send(1, f"ERROR:Usuario {target_name} no encontrado".encode("utf-8"))
            else:
                self._clients[target_name].send(1, f"REQ_CHAT_FROM:{session.name}".encode("utf-8"))

    def handle_accept_chat(self, session: ClientSession, requester_name: str):
        with self._lock:
            self._pending_receive.discard(session.name)
            if requester_name not in self._clients:
                session.send(1, f"ERROR:Usuario {requester_name} ya no está conectado".encode("utf-8"))
                return
            self._active_sessions.add((session.name, requester_name))
            self._active_sessions.add((requester_name, session.name))
            print(f"[CHAT ESTABLECIDO] {session.name} <-> {requester_name}")
            self._clients[requester_name].send(1, f"CHAT_ACCEPTED:{session.name}".encode("utf-8"))
            session.send(1, f"CHAT_ACCEPTED:{requester_name}".encode("utf-8"))

    def handle_deny_chat(self, session: ClientSession, requester_name: str):
        with self._lock:
            self._pending_receive.discard(session.name)
            if requester_name in self._clients:
                self._clients[requester_name].send(1, f"CHAT_DENIED:{session.name}".encode("utf-8"))

    def handle_stop_chat(self, session: ClientSession, target_name: str):
        print(f"[CHAT FINALIZADO] {session.name} ha terminado el chat con {target_name}")
        with self._lock:
            self._active_sessions.discard((session.name, target_name))
            self._active_sessions.discard((target_name, session.name))
            if target_name in self._clients:
                self._clients[target_name].send(1, f"CHAT_STOPPED:{session.name}".encode("utf-8"))

    def handle_chat_message(self, session: ClientSession, raw: str):
        try:
            _, target_name, text = raw.split(":", 2)
        except ValueError:
            session.send(1, "ERROR:Formato de mensaje inválido".encode("utf-8"))
            return
        with self._lock:
            if (session.name, target_name) not in self._active_sessions:
                session.send(1, f"ERROR:No tienes un chat activo con {target_name}.".encode("utf-8"))
                return
            if target_name not in self._clients:
                session.send(1, f"ERROR:Usuario {target_name} desconectado".encode("utf-8"))
                self._active_sessions.discard((session.name, target_name))
                self._active_sessions.discard((target_name, session.name))
                return
            self._clients[target_name].send(0, f"FROM:{session.name}:{text}".encode("utf-8"))

    def _disconnect(self, session: ClientSession):
        with self._lock:
            self._clients.pop(session.name, None)
            self._pending_receive.discard(session.name)
            stale = [s for s in self._active_sessions if session.name in s]
            for s in stale:
                self._active_sessions.discard(s)
        print(f"[DESCONEXIÓN] {session.name} desconectado.")
        session.close()

    def _print_banner(self, host: str, port: int):
        print("=" * 45)
        print("  Servidor de Chat Modular listo.")
        print(f"  IP    : {host}")
        print(f"  Puerto: {port}")
        print("=" * 45)
