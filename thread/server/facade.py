#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .core import ChatServer

class ServerFacade:
    """Fachada para simplificar el acceso y control del servidor."""

    def __init__(self, host: str = None, port: int = 0):
        self._server = ChatServer(host, port)

    def run(self):
        """Inicia el servidor."""
        self._server.start()
