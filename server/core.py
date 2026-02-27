#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import threading
from typing import Dict, Optional, Set, Tuple
from .session import ClientSession
from .buffer import RequestBuffer
from .handlers import ProtocolHandlers
from .observable import Observable
from .events import (
    ServerStarted, ServerStopped, FatalError,
    ClientHandshakeStarted, ClientJoined, ClientDisconnected,
    ActiveConnectionsChanged, ChatEstablished, ChatEnded,
    FileTransferRequested, FileTransferAccepted, FileTransferDenied,
    FileTransferRouted, FileTransferCompleted,
    BufferError, ClientError,
)

def get_local_ip() -> str:
    """Obtiene la dirección IP local"""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        ip: str = probe.getsockname()[0]
    finally:
        probe.close()
    return ip

class ChatServer(Observable):
    """Clase principal del servidor que maneja la lógica del chat"""

    def __init__(self, host: Optional[str] = None, port: int = 0) -> None:
        super().__init__()
        self.bind_host: str = host or "0.0.0.0"
        self.network_ip: str = get_local_ip()
        self.port: int = port
        self._clients: Dict[str, ClientSession] = {}
        self._active_sessions: Set[Tuple[str, str]] = set()
        self._pending_receive: Set[str] = set()
        self._lock = threading.Lock()
        self._buffer = RequestBuffer(self._dispatch_internal, self.emit)

    def start(self) -> None:
        """Inicia el servidor"""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_sock.bind((self.bind_host, self.port))
            server_sock.listen()

            real_host, real_port = server_sock.getsockname()
            self.port = real_port
            self.emit(ServerStarted(real_host, real_port, self.network_ip))

            self._accept_loop(server_sock)
        except KeyboardInterrupt:
            pass  # Cierre normal por Ctrl+C, sin emitir error
        except Exception as e:
            import traceback
            self.emit(FatalError(f"{e}\n{traceback.format_exc()}"))
        finally:
            server_sock.close()
            self.emit(ServerStopped(self.network_ip, self.port))
            self._buffer.stop()

    def _accept_loop(self, server_sock: socket.socket) -> None:
        """Loop de aceptación de clientes"""
        while True:
            conn, addr = server_sock.accept()
            temp_id = f"Temp_{random.randint(1000, 9999)}"
            session = ClientSession(conn, addr, temp_id)
            threading.Thread(target=self._handle_client, args=(session,), daemon=True).start()

    def _handle_client(self, session: ClientSession) -> None:
        """Maneja la sesión de un cliente"""
        self.emit(ClientHandshakeStarted(session.address, session.name))
        try:
            while True:
                tlv = session.recv_tlv()
                if not tlv: break
                msg_type, payload = tlv
                self._buffer.add_request(session, msg_type, payload)
        except Exception as exc:
            self.emit(ClientError(session.name, str(exc)))
        finally:
            self._disconnect(session)

    def _dispatch_internal(self, session: ClientSession, msg_type: int, payload: bytes):
        """Distribuye la solicitud al manejador interno."""
        ProtocolHandlers.dispatch(self, session, msg_type, payload)

    def handle_file_transfer(self, session: ClientSession, payload: bytes):
        """Reenvía un archivo binario (Tipo 2) al destinatario."""
        try:
            dst_len = payload[0]
            target_name = payload[1:1+dst_len].decode("utf-8")

            with self._lock:
                if (session.name, target_name) not in self._active_sessions:
                    session.send(1, f"ERROR:No tienes un chat activo con {target_name} para enviar archivos.".encode("utf-8"))
                    return
                if target_name not in self._clients:
                    session.send(1, f"ERROR:Usuario {target_name} desconectado".encode("utf-8"))
                    return

                sender_name = session.name.encode("utf-8")
                client_payload = bytes([len(sender_name)]) + sender_name + payload[1+dst_len:]
                self._clients[target_name].send(2, client_payload)
                self.emit(FileTransferRouted(session.name, target_name))
        except Exception as e:
            self.emit(ClientError(session.name, f"Fallo al procesar envío de archivo: {e}"))
            session.send(1, f"ERROR:Fallo al procesar envío de archivo: {e}".encode("utf-8"))

    def handle_set_name(self, session: ClientSession, new_name: str):
        """Establece el nombre del usuario"""
        with self._lock:
            if session.closed:
                return
            if new_name in self._clients or "Temp_" in new_name:
                session.send(1, b"NAME_TAKEN")
                return
            session.name = new_name
            self._clients[new_name] = session
            session.send(1, b"NAME_OK")
            count = len(self._clients)
        self.emit(ClientJoined(new_name, session.address))
        self.emit(ActiveConnectionsChanged(count))

    def send_user_list(self, session: ClientSession):
        """Envía la lista de usuarios al cliente"""
        with self._lock:
            user_list = ",".join(self._clients.keys())
        session.send(1, f"LIST_USERS:{user_list}".encode("utf-8"))

    def handle_req_chat(self, session: ClientSession, target_name: str):
        """Maneja la solicitud de chat"""
        with self._lock:
            if target_name not in self._clients:
                session.send(1, f"ERROR:Usuario {target_name} no encontrado".encode("utf-8"))
            else:
                self._clients[target_name].send(1, f"REQ_CHAT_FROM:{session.name}".encode("utf-8"))

    def handle_accept_chat(self, session: ClientSession, requester_name: str):
        """Maneja la aceptación de chat"""
        with self._lock:
            self._pending_receive.discard(session.name)
            if requester_name not in self._clients:
                session.send(1, f"ERROR:Usuario {requester_name} ya no está conectado".encode("utf-8"))
                return
            self._active_sessions.add((session.name, requester_name))
            self._active_sessions.add((requester_name, session.name))
            self._clients[requester_name].send(1, f"CHAT_ACCEPTED:{session.name}".encode("utf-8"))
            session.send(1, f"CHAT_ACCEPTED:{requester_name}".encode("utf-8"))
        self.emit(ChatEstablished(session.name, requester_name))

    def handle_deny_chat(self, session: ClientSession, requester_name: str):
        """Maneja la denegación de chat"""
        with self._lock:
            self._pending_receive.discard(session.name)
            if requester_name in self._clients:
                self._clients[requester_name].send(1, f"CHAT_DENIED:{session.name}".encode("utf-8"))

    def handle_stop_chat(self, session: ClientSession, target_name: str):
        """Maneja la finalización de chat"""
        with self._lock:
            self._active_sessions.discard((session.name, target_name))
            self._active_sessions.discard((target_name, session.name))
            if target_name in self._clients:
                self._clients[target_name].send(1, f"CHAT_STOPPED:{session.name}".encode("utf-8"))
        self.emit(ChatEnded(session.name, target_name))

    def handle_req_send_files(self, session: ClientSession, payload: str):
        """Maneja la solicitud de envío de archivos"""
        try:
            target_name, count = payload.split(":")
            with self._lock:
                if target_name in self._clients:
                    self._clients[target_name].send(1, f"REQ_SEND_FILES_FROM:{session.name}:{count}".encode("utf-8"))
                else:
                    session.send(1, f"ERROR:Usuario {target_name} no encontrado".encode("utf-8"))
                    return
            self.emit(FileTransferRequested(session.name, target_name, count))
        except ValueError:
            session.send(1, "ERROR:Formato REQ_SEND_FILES inválido".encode("utf-8"))

    def handle_accept_send_files(self, session: ClientSession, sender_name: str):
        """Maneja la aceptación de envío de archivos"""
        with self._lock:
            if sender_name in self._clients:
                self._clients[sender_name].send(1, f"ACCEPT_SEND_FILES_FROM:{session.name}".encode("utf-8"))
            else:
                session.send(1, f"ERROR:Usuario {sender_name} desconectado".encode("utf-8"))
                return
        self.emit(FileTransferAccepted(session.name, sender_name))

    def handle_deny_send_files(self, session: ClientSession, sender_name: str):
        """Maneja la denegación de envío de archivos"""
        with self._lock:
            if sender_name in self._clients:
                self._clients[sender_name].send(1, f"DENY_SEND_FILES_FROM:{session.name}".encode("utf-8"))
            else:
                return
        self.emit(FileTransferDenied(session.name, sender_name))

    def handle_files_received(self, session: ClientSession, sender_name: str):
        """Maneja la recepción de archivos"""
        with self._lock:
            if sender_name in self._clients:
                self._clients[sender_name].send(1, f"FILES_RECEIVED_FROM:{session.name}".encode("utf-8"))
            else:
                return
        self.emit(FileTransferCompleted(session.name, sender_name))

    def handle_chat_message(self, session: ClientSession, raw: str):
        """Maneja el envío de mensajes"""
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
        """Maneja la desconexión de un cliente"""
        session.closed = True
        with self._lock:
            if session.name in self._clients and self._clients[session.name] is session:
                self._clients.pop(session.name)
            self._pending_receive.discard(session.name)
            stale = [s for s in self._active_sessions if session.name in s]
            for s in stale:
                self._active_sessions.discard(s)
        self.emit(ClientDisconnected(session.name, session.address))
        session.close()
