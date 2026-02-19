#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .core import ChatClient

class ClientFacade:
    """Fachada para simplificar el uso del cliente de chat."""

    def __init__(self):
        self._client = ChatClient()

    def start(self, host: str, port: int):
        """Conecta e inicia el cliente."""
        try:
            self._client.connect(host, port)
            self._client.run()
        except Exception as e:
            print(f"Error en el cliente: {e}")
