#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
logger.py
---------
ServerObserver: observer concreto que traduce los eventos semánticos del servidor
a salidas formateadas (consola Rich y archivo de texto plano).

Para conectarlo al servidor, usa ServerFacade o subscribe() directamente:
    observer = ServerObserver()
    server.subscribe(observer)
    server.start()
"""

import re
import queue
import threading
from datetime import datetime
from typing import Optional, Any, Dict
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markup import escape

from .events import (
    ServerStarted, ServerStopped, FatalError,
    ClientHandshakeStarted, ClientJoined, ClientDisconnected,
    ActiveConnectionsChanged, ChatEstablished, ChatEnded,
    FileTransferRequested, FileTransferAccepted, FileTransferDenied,
    FileTransferRouted, FileTransferCompleted,
    BufferError, ClientError,
)


# ---------------------------------------------------------------------------
# Estructuras internas de los workers
# ---------------------------------------------------------------------------

@dataclass
class LogEntry:
    """Unidad de trabajo interna de los workers de salida."""
    level: str
    message: str
    timestamp: str
    extra: Optional[Dict[str, Any]] = None


class BaseLogWorker(threading.Thread):
    """Hilo base para los workers de salida."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__(daemon=False)
        self.log_queue = log_queue
        self.running = True

    def run(self):
        while self.running:
            try:
                entry = self.log_queue.get(timeout=1.0)
                if entry is None:
                    break
                self.process(entry)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def process(self, entry: LogEntry):
        raise NotImplementedError


class ConsoleWorker(BaseLogWorker):
    """Worker de salida a consola usando Rich."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__(log_queue)
        self.console = Console()

    def process(self, entry: LogEntry):
        ts = entry.timestamp
        lvl = entry.level
        msg = entry.message

        styles = {
            "INFO":   "bold blue",
            "OK":     "bold green",
            "ERROR":  "bold red",
            "SYSTEM": "bold cyan",
            "FILE":   "bold magenta",
        }
        style = styles.get(lvl, "white")

        try:
            if lvl == "BANNER":
                banner_text = Text()
                banner_text.append("Servidor de Chat Modular (TLV)\n", style="bold cyan")
                if entry.extra:
                    banner_text.append(f"IP: {entry.extra.get('network_ip')}\n", style="bold yellow")
                    banner_text.append(f"Puerto: {entry.extra.get('port')}", style="green")
                self.console.print(Panel(banner_text, expand=False, border_style="blue"))

            elif lvl == "CONNECTION":
                addr = entry.extra.get("addr", "???") if entry.extra else "???"
                status_style = "green" if "unido" in msg.lower() or "handshake" in msg.lower() else "red"
                self.console.print(
                    f"[dim]{ts}[/] [bold blue]INFO[/] "
                    f"Conexión de [bold yellow]{escape(addr)}[/]: "
                    f"[{status_style}]{escape(msg)}[/]"
                )

            elif lvl == "FILE":
                sender   = entry.extra.get("sender",   "???") if entry.extra else "???"
                receiver = entry.extra.get("receiver", "???") if entry.extra else "???"
                self.console.print(
                    f"[dim]{ts}[/] [bold magenta]ARCHIVO[/] "
                    f"[cyan]{escape(sender)}[/] -> [cyan]{escape(receiver)}[/]: {escape(msg)}"
                )

            else:
                self.console.print(f"[dim]{ts}[/] [{style}]{lvl}[/] {escape(msg)}")

        except Exception:
            print(f"[{ts}] [{lvl}] {msg}", flush=True)


class FileWorker(BaseLogWorker):
    """Worker de persistencia en archivo de texto plano."""

    def __init__(self, log_queue: queue.Queue, log_filename: str = "server.log"):
        super().__init__(log_queue)
        self.log_filename = log_filename

    @staticmethod
    def _strip_rich(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\[[^\]]+\]", "", str(text))

    def process(self, entry: LogEntry):
        ts  = entry.timestamp
        lvl = entry.level
        msg = self._strip_rich(entry.message)

        if lvl == "BANNER" and entry.extra:
            msg = f"Servidor iniciado. IP: {entry.extra.get('network_ip')}, Puerto: {entry.extra.get('port')}"
            lvl = "SYSTEM"
        elif lvl == "CONNECTION" and entry.extra:
            addr = entry.extra.get("addr", "")
            msg  = f"Conexión de {addr}: {msg}"
            lvl  = "INFO"
        elif lvl == "FILE" and entry.extra:
            sender   = entry.extra.get("sender",   "")
            receiver = entry.extra.get("receiver", "")
            msg = f"Archivo: {sender} -> {receiver}: {msg}"

        log_line = f"[{ts}] [{lvl}] {msg}\n"
        try:
            with open(self.log_filename, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ServerObserver: traduce eventos del servidor a LogEntries
# ---------------------------------------------------------------------------

class ServerObserver:
    """
    Observer concreto que traduce eventos semánticos del servidor a salidas formateadas.

    Mantiene dos workers independientes (consola y archivo). Para conectarlo:
        server.subscribe(ServerObserver())

    Para detenerlo limpiamente (vaciando las colas):
        observer.stop()
    """

    def __init__(self, log_filename: str = "server.log"):
        self._console_queue = queue.Queue()
        self._file_queue    = queue.Queue()

        self._console_worker = ConsoleWorker(self._console_queue)
        self._file_worker    = FileWorker(self._file_queue, log_filename)

        self._console_worker.start()
        self._file_worker.start()

    # ------------------------------------------------------------------
    # Punto de entrada del observer
    # ------------------------------------------------------------------

    def __call__(self, event: Any) -> None:
        """Recibe un evento y lo despacha al método correspondiente."""
        dispatch = {
            ServerStarted:            self._on_server_started,
            ServerStopped:            self._on_server_stopped,
            FatalError:               self._on_fatal_error,
            ClientHandshakeStarted:   self._on_handshake_started,
            ClientJoined:             self._on_client_joined,
            ClientDisconnected:       self._on_client_disconnected,
            ActiveConnectionsChanged: self._on_connections_changed,
            ChatEstablished:          self._on_chat_established,
            ChatEnded:                self._on_chat_ended,
            FileTransferRequested:    self._on_file_requested,
            FileTransferAccepted:     self._on_file_accepted,
            FileTransferDenied:       self._on_file_denied,
            FileTransferRouted:       self._on_file_routed,
            FileTransferCompleted:    self._on_file_completed,
            BufferError:              self._on_buffer_error,
            ClientError:              self._on_client_error,
        }
        handler = dispatch.get(type(event))
        if handler:
            handler(event)

    # ------------------------------------------------------------------
    # Handlers por tipo de evento
    # ------------------------------------------------------------------

    def _on_server_started(self, e: ServerStarted):
        self._broadcast("BANNER", "", {"network_ip": e.network_ip, "port": e.port})

    def _on_server_stopped(self, e: ServerStopped):
        self._broadcast("INFO",   f"Servidor finalizado en {e.network_ip}:{e.port}")
        self._broadcast("SYSTEM", f"Servidor detenido. IP: {e.network_ip}, Puerto: {e.port}")

    def _on_fatal_error(self, e: FatalError):
        self._broadcast("ERROR", f"Error fatal en el servidor: {e.error_msg}")

    def _on_handshake_started(self, e: ClientHandshakeStarted):
        self._broadcast("CONNECTION", "Handshake iniciado", {"addr": str(e.addr)})

    def _on_client_joined(self, e: ClientJoined):
        self._broadcast("OK", f"Usuario {e.name} ({e.addr}) se ha unido.")

    def _on_client_disconnected(self, e: ClientDisconnected):
        self._broadcast("CONNECTION", f"{e.name} se ha desconectado.", {"addr": str(e.addr)})

    def _on_connections_changed(self, e: ActiveConnectionsChanged):
        self._broadcast("INFO", f"Conexiones activas: {e.count}")

    def _on_chat_established(self, e: ChatEstablished):
        self._broadcast("INFO", f"Chat establecido: {e.name_a} <-> {e.name_b}")

    def _on_chat_ended(self, e: ChatEnded):
        self._broadcast("INFO", f"Chat finalizado: {e.who} ha cortado con {e.with_whom}")

    def _on_file_requested(self, e: FileTransferRequested):
        self._broadcast("FILE", f"Solicitud para enviar {e.count} archivos",
                        {"sender": e.sender, "receiver": e.receiver})

    def _on_file_accepted(self, e: FileTransferAccepted):
        self._broadcast("FILE", "Transferencia ACEPTADA",
                        {"sender": e.sender, "receiver": e.receiver})

    def _on_file_denied(self, e: FileTransferDenied):
        self._broadcast("FILE", "Transferencia RECHAZADA",
                        {"sender": e.sender, "receiver": e.receiver})

    def _on_file_routed(self, e: FileTransferRouted):
        self._broadcast("FILE", "Enrutado con éxito",
                        {"sender": e.sender, "receiver": e.receiver})

    def _on_file_completed(self, e: FileTransferCompleted):
        self._broadcast("FILE", "Lote RECIBIDO y confirmado",
                        {"sender": e.sender, "receiver": e.receiver})

    def _on_buffer_error(self, e: BufferError):
        self._broadcast("ERROR", f"Error procesando solicitud de {e.session_name}: {e.error_msg}")

    def _on_client_error(self, e: ClientError):
        self._broadcast("ERROR", f"{e.session_name}: {e.error_msg}")

    # ------------------------------------------------------------------
    # Infraestructura interna
    # ------------------------------------------------------------------

    def _broadcast(self, level: str, message: str, extra: Dict[str, Any] = None):
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = LogEntry(level, message, ts, extra)
        self._console_queue.put(entry)
        self._file_queue.put(entry)

    def stop(self):
        """Detiene los workers ordenadamente, vaciando las colas."""
        self._console_queue.put(None)
        self._file_queue.put(None)
        self._console_worker.join(timeout=2.0)
        self._file_worker.join(timeout=2.0)
        self._console_worker.running = False
        self._file_worker.running    = False
