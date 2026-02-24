#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import struct
import pathlib
from typing import Optional, Callable, List
from .state import ChatState
from .buffer import EventBuffer
from .receiver import MessageReceiver

class ChatClient:
    def __init__(self, event_callback: Optional[Callable] = None) -> None:
        self._sock: Optional[socket.socket] = None
        self._state = ChatState()
        self._buffer = EventBuffer(event_callback)
        self._receiver: Optional[MessageReceiver] = None

    def connect(self, host: str, port: int) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        self._receiver = MessageReceiver(self._sock, self._state, self._buffer)
        self._receiver.start()

    def disconnect(self) -> None:
        if self._sock:
            self._sock.close()
        self._buffer.stop()

    def set_name(self, name: str) -> bool:
        """Envía el comando para establecer el nickname."""
        if not name: return False
        self._state.name = name
        self._state.name_confirmed.clear()
        self._state.name_error = None
        self._send(1, f"SET_NAME:{name}".encode("utf-8"))
        return True

    def process_command(self, line: str) -> None:
        """Procesa un comando o mensaje de texto."""
        line = line.strip()
        if not line: return

        if self._state.pending_requests:
            requester = self._state.pending_requests[0]
            if line == "accept": self._cmd_accept()
            elif line == "deny": self._cmd_deny()
            else: self._buffer.add_event(f"[!] BLOQUEO: Debes 'accept' o 'deny' la solicitud de chat de {requester}.")
            return

        if self._state.pending_file_request:
            if line == "accept": self._cmd_accept()
            elif line == "deny": self._cmd_deny()
            else: self._buffer.add_event(f"[!] BLOQUEO: Debes 'accept' o 'deny' la transferencia de archivos.")
            return

        if line == "list": self._cmd_list()
        elif line == "sessions": self._cmd_sessions()
        elif line == "file":
            # Este comando ahora se activará desde la GUI para abrir el diálogo
            self._buffer.add_event("FILE_DIALOG_REQUEST")
        elif line.startswith("file:"):
            # Mantenemos soporte legado por si acaso, pero encolamos
            self.send_files([line.split(":", 1)[1]])
        elif line.startswith("stop"):
            target = line.split(":", 1)[1] if ":" in line else self._state.current_target
            self._cmd_stop(target)
        elif line.startswith("chat:"): self._cmd_chat(line.split(":", 1)[1])
        else: self._cmd_send(line)

    def _cmd_list(self) -> None: self._send(1, b"GET_USERS")

    def _cmd_sessions(self) -> None:
        sessions_str = ", ".join(self._state.open_sessions) if self._state.open_sessions else "Ninguno"
        self._buffer.add_event(f"[CHATS ACTIVOS] {sessions_str}")
        if self._state.current_target: 
            self._buffer.add_event(f"[ACTUAL] Chateando con: {self._state.current_target}")

    def _cmd_accept(self) -> None:
        if self._state.pending_requests:
            requester = self._state.pending_requests.pop(0)
            self._send(1, f"ACCEPT_CHAT:{requester}".encode("utf-8"))
            self._buffer.add_event(f"[INFO] Chat con {requester} aceptado.")
        elif self._state.pending_file_request:
            # Notificamos a la GUI que debe abrir el diálogo de carpeta
            self._buffer.add_event("FOLDER_DIALOG_REQUEST")
        else:
            self._buffer.add_event("[!] No hay nada que aceptar.")

    def _cmd_deny(self) -> None:
        if self._state.pending_requests:
            requester = self._state.pending_requests.pop(0)
            self._send(1, f"DENY_CHAT:{requester}".encode("utf-8"))
            self._buffer.add_event(f"[INFO] Solicitud de {requester} rechazada.")
        elif self._state.pending_file_request:
            req = self._state.pending_file_request
            self._send(1, f"DENY_SEND_FILES:{req['sender']}".encode("utf-8"))
            self._buffer.add_event(f"[INFO] Transferencia de {req['sender']} rechazada.")
            self._state.pending_file_request = None
        else:
            self._buffer.add_event("[!] No hay nada que rechazar.")

    def _cmd_stop(self, target: Optional[str]) -> None:
        if target and target in self._state.open_sessions:
            self._send(1, f"STOP_CHAT:{target}".encode("utf-8"))
            self._state.open_sessions.discard(target)
            if self._state.current_target == target: self._state.current_target = None
            self._buffer.add_event(f"[INFO] Chat con {target} finalizado.")
        else:
            self._buffer.add_event(f"[!] No tienes un chat activo con {target}")

    def _cmd_chat(self, target: str) -> None:
        if target == self._state.name:
            self._buffer.add_event("[!] No puedes chatear contigo mismo.")
            return
        if target in self._state.open_sessions:
            self._state.current_target = target
            self._buffer.add_event(f"[INFO] Cambiado a chat con {target}.")
        else:
            self._send(1, f"REQ_CHAT:{target}".encode("utf-8"))
            self._buffer.add_event(f"[SISTEMA] Solicitud enviada a {target}. Esperando...")
            self._state.current_target = target

    def send_files(self, paths: List[str]) -> None:
        """Inicia el proceso de envío para una lista de archivos."""
        if not self._state.current_target:
            self._buffer.add_event("[!] Selecciona un chat primero.")
            return

        valid_paths = []
        for p in paths:
            path = pathlib.Path(p)
            if path.exists():
                valid_paths.append(p)
            else:
                self._buffer.add_event(f"[!] Archivo no encontrado: {p}")

        if not valid_paths: return

        self._state.file_queue = valid_paths
        target = self._state.current_target
        # REQ_SEND_FILES:<Target>:<Count>
        self._send(1, f"REQ_SEND_FILES:{target}:{len(valid_paths)}".encode("utf-8"))
        self._buffer.add_event(f"[SISTEMA] Solicitando enviar {len(valid_paths)} archivo(s) a {target}...")

    def set_save_path_and_accept(self, path: str) -> None:
        """Se llama desde la GUI tras elegir carpeta de destino."""
        if self._state.pending_file_request:
            self._state.save_path = path
            sender = self._state.pending_file_request['sender']
            self._send(1, f"ACCEPT_SEND_FILES:{sender}".encode("utf-8"))
            self._buffer.add_event(f"[INFO] Carpeta de destino establecida. Esperando archivos de {sender}...")

    def _send_next_file(self) -> None:
        """Envía el siguiente archivo en la cola."""
        if not self._state.file_queue or not self._state.current_target:
            self._buffer.add_event("[INFO] Envío de archivos completado.")
            return

        path_str = self._state.file_queue.pop(0)
        path = pathlib.Path(path_str)
        
        try:
            file_data = path.read_bytes()
            filename = path.name.encode("utf-8")
            dst = self._state.current_target.encode("utf-8")
            # Mensaje tipo 2: DST_LEN (1) + DST + FILENAME_LEN (1) + FILENAME + DATA
            full_payload = bytes([len(dst)]) + dst + bytes([len(filename)]) + filename + file_data
            self._send(2, full_payload)
            self._buffer.add_event(f"[YO] Enviando {path.name}...")
        except Exception as e:
            self._buffer.add_event(f"[ERROR] Error al enviar {path.name}: {e}")
            self._send_next_file()

    def _cmd_send(self, text: str) -> None:
        if self._state.current_target: 
            self._send(0, f"CHAT:{self._state.current_target}:{text}".encode("utf-8"))
            self._buffer.add_event(f"[YO] {text}")
        else: 
            self._buffer.add_event("[!] Selecciona un chat primero.")

    def _send(self, msg_type: int, data: bytes) -> None:
        if self._sock:
            try:
                header = struct.pack("!BI", msg_type, len(data))
                self._sock.sendall(header + data)
            except Exception as e:
                self._buffer.add_event(f"[ERROR RED] Error al enviar: {e}")
