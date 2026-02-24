#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
from typing import Tuple, Optional

class ClientSession:
    """Representa la conexión de un cliente individual al servidor."""

    def __init__(self, sock: socket.socket, address: Tuple[str, int], name: str) -> None:
        self._sock = sock
        self.address = address
        self.name = name

    def send(self, msg_type: int, data: bytes) -> None:
        """Envía un mensaje usando el formato TLV (!BI)."""
        header = struct.pack("!BI", msg_type, len(data))
        self._sock.sendall(header + data)

    def recv_all(self, n: int) -> Optional[bytes]:
        """Auxiliar para recibir exactamente n bytes."""
        data = b""
        while len(data) < n:
            packet = self._sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv_tlv(self) -> Optional[Tuple[int, bytes]]:
        """Recibe un mensaje TLV completo."""
        header = self.recv_all(5)
        if not header:
            return None
        msg_type, length = struct.unpack("!BI", header)
        payload = self.recv_all(length)
        if payload is None:
            return None
        return msg_type, payload

    def close(self) -> None:
        self._sock.close()
