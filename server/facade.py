#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
facade.py
---------
Punto de cableado entre el servidor y sus observers.
Es el ÚNICO lugar donde se decide qué observer escucha al servidor.
"""

from .core import ChatServer
from .logger import ServerObserver


class ServerFacade:
    """Fachada que conecta el ChatServer con su observer de salida."""

    def __init__(self, host: str = None, port: int = 0, log_filename: str = "server.log"):
        self._server   = ChatServer(host, port)
        self._observer = ServerObserver(log_filename)
        self._server.subscribe(self._observer)

    def run(self):
        """Inicia el servidor. Bloquea hasta que se detenga."""
        try:
            self._server.start()
        finally:
            self._observer.stop()
