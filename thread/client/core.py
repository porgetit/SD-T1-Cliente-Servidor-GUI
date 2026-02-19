#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import struct
import pathlib
from typing import Optional
from .state import ChatState
from .buffer import EventBuffer
from .receiver import MessageReceiver

class ChatClient:
    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None
        self._state = ChatState()
        self._buffer = EventBuffer()

    def connect(self, host: str, port: int) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        MessageReceiver(self._sock, self._state, self._buffer).start()

    def run(self) -> None:
        self._handshake()
        self._print_menu()
        try:
            while True:
                line = input("> ").strip()
                if not line: continue
                if line == "exit": break
                self._process_input(line)
        except KeyboardInterrupt:
            pass
        finally:
            if self._sock: self._sock.close()
            self._buffer.stop()

    def _handshake(self) -> None:
        """Bucle de bloqueo para registrar el nickname."""
        while True:
            name = input("Ingrese su nickname: ").strip()
            if not name: continue
            
            self._state.name = name
            self._state.name_confirmed.clear()
            self._state.name_error = None
            
            self._send(1, f"SET_NAME:{name}".encode("utf-8"))
            
            # Esperamos la respuesta del servidor (máximo 5 segs)
            if not self._state.name_confirmed.wait(timeout=5.0):
                print("[!] Tiempo de espera agotado. Reintentando...")
                continue
                
            if self._state.name_error:
                print(f"[!] {self._state.name_error}")
            else:
                print(f"[SISTEMA] Nickname '{name}' confirmado.")
                break

    def _process_input(self, line: str) -> None:
        if self._state.pending_requests:
            requester = self._state.pending_requests[0]
            if line == "accept": self._cmd_accept()
            elif line == "deny": self._cmd_deny()
            else: print(f"[!] BLOQUEO: Debes 'accept' o 'deny' la solicitud de {requester}.")
            return

        if line == "list": self._cmd_list()
        elif line == "sessions": self._cmd_sessions()
        elif line.startswith("file:"):
            self._cmd_send_file(line.split(":", 1)[1])
        elif line.startswith("stop"):
            target = line.split(":", 1)[1] if ":" in line else self._state.current_target
            self._cmd_stop(target)
        elif line.startswith("chat:"): self._cmd_chat(line.split(":", 1)[1])
        else: self._cmd_send(line)

    def _cmd_list(self) -> None: self._send(1, b"GET_USERS")

    def _cmd_sessions(self) -> None:
        sessions_str = ", ".join(self._state.open_sessions) if self._state.open_sessions else "Ninguno"
        print(f"[CHATS ACTIVOS] {sessions_str}")
        if self._state.current_target: print(f"[ACTUAL] Chateando con: {self._state.current_target}")

    def _cmd_accept(self) -> None:
        if self._state.pending_requests:
            requester = self._state.pending_requests.pop(0)
            self._send(1, f"ACCEPT_CHAT:{requester}".encode("utf-8"))
            print(f"[INFO] Chat con {requester} aceptado.")

    def _cmd_deny(self) -> None:
        if self._state.pending_requests:
            requester = self._state.pending_requests.pop(0)
            self._send(1, f"DENY_CHAT:{requester}".encode("utf-8"))
            print(f"[INFO] Solicitud de {requester} rechazada.")

    def _cmd_stop(self, target: Optional[str]) -> None:
        if target and target in self._state.open_sessions:
            self._send(1, f"STOP_CHAT:{target}".encode("utf-8"))
            self._state.open_sessions.discard(target)
            if self._state.current_target == target: self._state.current_target = None
        else:
            print(f"[!] No tienes un chat activo con {target}")

    def _cmd_chat(self, target: str) -> None:
        if target == self._state.name:
            print("[!] No puedes chatear contigo mismo.")
            return
        if target in self._state.open_sessions:
            self._state.current_target = target
            print(f"[INFO] Cambiado a chat con {target}.")
        else:
            self._send(1, f"REQ_CHAT:{target}".encode("utf-8"))
            print(f"[SISTEMA] Solicitud enviada a {target}. Esperando...")
            self._state.current_target = target

    def _cmd_send_file(self, path_str: str) -> None:
        """Envía un archivo al destinatario actual."""
        if not self._state.current_target:
            print("[!] Selecciona un chat primero.")
            return

        path = pathlib.Path(path_str)
        if not path.exists():
            print(f"[!] Archivo no encontrado: {path_str}")
            return

        # Cualquier archivo se envía como Tipo 2 (Binario Genérico)
        msg_type = 2

        try:
            file_data = path.read_bytes()
            filename = path.name.encode("utf-8")
            # Payload para el servidor: dst_len(1)|dst|filename_len(1)|filename|data
            dst = self._state.current_target.encode("utf-8")
            full_payload = bytes([len(dst)]) + dst + bytes([len(filename)]) + filename + file_data
            self._send(msg_type, full_payload)
            print(f"[INFO] Enviando {path.name} a {self._state.current_target}...")
        except Exception as e:
            print(f"[ERROR] No se pudo leer el archivo: {e}")

    def _cmd_send(self, text: str) -> None:
        if self._state.current_target: self._send(0, f"CHAT:{self._state.current_target}:{text}".encode("utf-8"))
        else: print("[!] Selecciona un chat primero.")

    def _send(self, msg_type: int, data: bytes) -> None:
        if self._sock:
            header = struct.pack("!BI", msg_type, len(data))
            self._sock.sendall(header + data)

    @staticmethod
    def _print_menu() -> None:
        print("\n--- MENÚ DE MULTI-CHAT MODULAR (TLV) ---")
        print("Comandos: list, sessions, chat:<user>, file:<path>, accept, deny, stop, exit")
        print("=" * 45)
