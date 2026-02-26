#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import struct
import pathlib
from typing import Optional, Any
from .state import ChatState
from .buffer import EventBuffer

class MessageReceiver(threading.Thread):
    """Hilo daemon que escucha mensajes del servidor y los agrega al buffer de eventos."""

    def __init__(self, sock, state: ChatState, buffer: EventBuffer) -> None:
        super().__init__(daemon=True)
        self._sock = sock
        self._state = state
        self._buffer = buffer

    def recv_all(self, n: int) -> Optional[bytes]:
        """Recibe todos los bytes de un paquete."""
        data = b""
        while len(data) < n:
            packet = self._sock.recv(n - len(data))
            if not packet: return None
            data += packet
        return data

    def run(self) -> None:
        """Bucle principal del hilo."""
        while True:
            try:
                header = self.recv_all(5)
                if not header: break
                msg_type, length = struct.unpack("!BI", header)
                payload = self.recv_all(length)
                if payload is None: break
                
                self._dispatch(msg_type, payload)
            except Exception as e:
                self._buffer.add_event(f"[ERROR RECEPTOR] {e}")
                break
        self._buffer.add_event("[DESCONECTADO] Conexión perdida con el servidor.")

    def _dispatch(self, msg_type: int, payload: bytes) -> None:
        """Distribuye los mensajes al método correspondiente."""
        if msg_type in (0, 1):
            message = payload.decode("utf-8")
            if message == "NAME_OK": self._on_name_ok()
            elif message == "NAME_TAKEN": self._on_name_taken()
            elif message.startswith("LIST_USERS:"): self._on_list_users(message.split(":", 1)[1])
            elif message.startswith("REQ_CHAT_FROM:"): self._on_req_chat_from(message.split(":", 1)[1])
            elif message.startswith("CHAT_ACCEPTED:"): self._on_chat_accepted(message.split(":", 1)[1])
            elif message.startswith("CHAT_DENIED:"): self._on_chat_denied(message.split(":", 1)[1])
            elif message.startswith("CHAT_STOPPED:"): self._on_chat_stopped(message.split(":", 1)[1])
            elif message.startswith("FROM:"): self._on_message_received(message)
            elif message.startswith("ERROR:"): self._on_error(message.split(":", 1)[1])
            elif message.startswith("REQ_SEND_FILES_FROM:"): self._on_req_send_files_from(message.split(":", 1)[1])
            elif message.startswith("ACCEPT_SEND_FILES_FROM:"): self._on_accept_send_files_from(message.split(":", 1)[1])
            elif message.startswith("DENY_SEND_FILES_FROM:"): self._on_deny_send_files_from(message.split(":", 1)[1])
            elif message.startswith("FILES_RECEIVED_FROM:"): self._on_files_received_from(message.split(":", 1)[1])
        elif msg_type == 2:
            self._on_file_received(payload)

    def _on_name_ok(self) -> None:
        self._state.name_confirmed.set()

    def _on_name_taken(self) -> None:
        self._state.name_error = "El nombre ya está en uso."
        self._state.name_confirmed.set()

    def _on_list_users(self, users: str) -> None:
        user_list = [u for u in users.split(",") if u]
        self._state.connected_users = user_list
        # Notificamos al buffer
        self._buffer.add_event(f"USERS_UPDATE:{users}")
        self._buffer.add_event(f"[USUARIOS CONECTADOS] {users}")

    def _on_req_chat_from(self, requester: str) -> None:
        self._state.pending_requests.append(requester)
        self._buffer.add_event(f"[SOLICITUD] {requester} quiere chatear contigo. Escribe 'accept' o 'deny' ({len(self._state.pending_requests)} pendientes).")

    def _on_chat_accepted(self, partner: str) -> None:
        self._state.open_sessions.add(partner)
        self._buffer.add_event(f"[SISTEMA] Chat con {partner} ESTABLECIDO.")
        if not self._state.current_target:
            self._state.current_target = partner
            self._buffer.add_event(f"[INFO] Ahora chateando con {partner}.")

    def _on_chat_denied(self, partner: str) -> None:
        self._buffer.add_event(f"[SISTEMA] {partner} ha rechazado tu solicitud de chat.")
        if self._state.current_target == partner:
            self._state.current_target = None

    def _on_chat_stopped(self, partner: str) -> None:
        self._buffer.add_event(f"[SISTEMA] {partner} ha finalizado el chat.")
        self._state.open_sessions.discard(partner)
        if self._state.current_target == partner:
            self._state.current_target = None
            self._buffer.add_event("[INFO] Has vuelto al menú principal. Selecciona otro chat con 'chat:<user>'.")

    def _on_message_received(self, raw: str) -> None:
        _, sender, content = raw.split(":", 2)
        self._buffer.add_event(f"[{sender}] dice: {content}")

    def _on_error(self, description: str) -> None:
        self._buffer.add_event(f"[ERROR] {description}")

    def _on_req_send_files_from(self, payload: str) -> None:
        sender, count = payload.split(":")
        self._state.pending_file_request = {"sender": sender, "count": int(count)}
        self._buffer.add_event(f"[SOLICITUD] {sender} quiere enviarte {count} archivo(s). Escribe 'accept' o 'deny'.")

    def _on_accept_send_files_from(self, target: str) -> None:
        # El receptor aceptó, ahora el emisor (nosotros) debe empezar a mandar la cola
        self._buffer.add_event(f"[INFO] {target} ha aceptado la transferencia. Iniciando envío...")
        # Necesitamos una forma de que ChatClient empiece a mandar. 
        # Podemos usar un evento especial en el buffer que el ChatClient escuche? 
        # O mejor, llamar a una función del cliente si tenemos referencia.
        # MessageReceiver no tiene referencia al cliente, pero ChatClient puede observar el buffer.
        self._buffer.add_event("START_FILE_TRANSFER")

    def _on_deny_send_files_from(self, target: str) -> None:
        self._buffer.add_event(f"[!] {target} ha rechazado la transferencia de archivos.")
        self._state.file_queue = []

    def _on_files_received_from(self, target: str) -> None:
        self._buffer.add_event(f"[INFO] {target} ha recibido todos los archivos correctamente.")

    def _on_file_received(self, payload: bytes) -> None:
        """Maneja la recepción de archivos (Binario Genérico Tipo 2)."""
        try:
            # Formato esperado: sender_len(1)|sender|filename_len(1)|filename|data
            s_len = payload[0]
            sender = payload[1:1+s_len].decode("utf-8")
            f_len = payload[1+s_len]
            filename = payload[2+s_len:2+s_len+f_len].decode("utf-8")
            file_data = payload[2+s_len+f_len:]
            
            # Ruta de guardado: usar save_path si existe, sino descargas por defecto
            if self._state.save_path:
                down_path = pathlib.Path(self._state.save_path)
            else:
                down_path = pathlib.Path.home() / "Downloads" / self._state.name
            
            down_path.mkdir(parents=True, exist_ok=True)
            dest_file = down_path / filename
            
            # Evitar sobreescribir si ya existe (añadir número)
            count = 1
            original_stem = dest_file.stem
            while dest_file.exists():
                dest_file = dest_file.with_name(f"{original_stem}_{count}{dest_file.suffix}")
                count += 1

            with open(dest_file, "wb") as f:
                f.write(file_data)
            
            self._buffer.add_event(f"[ARCHIVO] Recibido de {sender}: {filename} (Guardado en {dest_file})")
            
            # Si era parte de una solicitud pendiente, descontamos
            if self._state.pending_file_request and self._state.pending_file_request['sender'] == sender:
                self._state.pending_file_request['count'] -= 1
                if self._state.pending_file_request['count'] <= 0:
                    self._state.pending_file_request = None
                    self._state.save_path = None
                    self._buffer.add_event(f"[INFO] Transferencia de {sender} completada.")
                    # Notificamos al servidor para que avise al emisor
                    self._sock.sendall(struct.pack("!BI", 1, len(f"FILES_RECEIVED:{sender}")) + f"FILES_RECEIVED:{sender}".encode("utf-8"))
        except Exception as e:
            self._buffer.add_event(f"[ERROR ARCHIVO] {e}")
