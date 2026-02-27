#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
events.py
---------
Dataclasses que representan cada evento semántico que el servidor puede emitir.
Son datos puros sin ninguna dependencia de presentación o formato.
"""

from dataclasses import dataclass, field
from typing import Tuple


# ---------------------------------------------------------------------------
# Eventos del ciclo de vida del servidor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServerStarted:
    """El servidor ha iniciado y está escuchando."""
    bind_ip: str
    port: int
    network_ip: str


@dataclass(frozen=True)
class ServerStopped:
    """El servidor se ha detenido de forma controlada."""
    network_ip: str
    port: int


@dataclass(frozen=True)
class FatalError:
    """Error irrecuperable en el servidor."""
    error_msg: str


# ---------------------------------------------------------------------------
# Eventos de conexión de clientes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClientHandshakeStarted:
    """Un cliente nuevo ha conectado y se está identificando."""
    addr: Tuple[str, int]
    temp_name: str


@dataclass(frozen=True)
class ClientJoined:
    """Un cliente completó el handshake y está registrado con nombre."""
    name: str
    addr: Tuple[str, int]


@dataclass(frozen=True)
class ClientDisconnected:
    """Un cliente se ha desconectado (normal o por error)."""
    name: str
    addr: Tuple[str, int]


@dataclass(frozen=True)
class ActiveConnectionsChanged:
    """El número de conexiones activas ha cambiado."""
    count: int


# ---------------------------------------------------------------------------
# Eventos de sesiones de chat
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChatEstablished:
    """Una sesión de chat fue aceptada entre dos usuarios."""
    name_a: str
    name_b: str


@dataclass(frozen=True)
class ChatEnded:
    """Un usuario cortó una sesión de chat activa."""
    who: str
    with_whom: str


# ---------------------------------------------------------------------------
# Eventos de transferencia de archivos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileTransferRequested:
    """Un usuario ha solicitado enviar archivos a otro."""
    sender: str
    receiver: str
    count: str


@dataclass(frozen=True)
class FileTransferAccepted:
    """El receptor aceptó la transferencia de archivos."""
    receiver: str
    sender: str


@dataclass(frozen=True)
class FileTransferDenied:
    """El receptor rechazó la transferencia de archivos."""
    receiver: str
    sender: str


@dataclass(frozen=True)
class FileTransferRouted:
    """Un paquete de archivo fue enrutado exitosamente al receptor."""
    sender: str
    receiver: str


@dataclass(frozen=True)
class FileTransferCompleted:
    """El receptor confirmó haber recibido el lote de archivos."""
    receiver: str
    sender: str


# ---------------------------------------------------------------------------
# Eventos de errores internos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BufferError:
    """Error al procesar una solicitud del buffer interno."""
    session_name: str
    error_msg: str


@dataclass(frozen=True)
class ClientError:
    """Error en la sesión de un cliente conectado."""
    session_name: str
    error_msg: str
