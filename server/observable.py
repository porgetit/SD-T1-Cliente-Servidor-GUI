#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
observable.py
-------------
Mixin Observable: permite a cualquier clase emitir eventos tipados
y registrar observers que los consumen.

Uso:
    class MiClase(Observable):
        def hacer_algo(self):
            self.emit(AlgunEvento(dato="valor"))

    instancia = MiClase()
    instancia.subscribe(mi_observer)   # mi_observer(event) será llamado
"""

import threading
from typing import Callable, Any


class Observable:
    """
    Mixin que dota a una clase de capacidad de emisión de eventos.

    Cualquier clase puede heredar de Observable para publicar eventos
    a sus observers registrados. La emisión es thread-safe.
    """

    def __init__(self):
        self._observers: list[Callable[[Any], None]] = []
        self._obs_lock = threading.Lock()

    def subscribe(self, observer: Callable[[Any], None]) -> None:
        """
        Registra un observer para recibir todos los eventos emitidos.

        Args:
            observer: Callable que acepta un único argumento (el evento).
        """
        with self._obs_lock:
            self._observers.append(observer)

    def unsubscribe(self, observer: Callable[[Any], None]) -> None:
        """
        Elimina un observer previamente registrado.

        Args:
            observer: El mismo callable que fue registrado.
        """
        with self._obs_lock:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

    def emit(self, event: Any) -> None:
        """
        Emite un evento a todos los observers registrados.

        La entrega es síncrona y en el mismo hilo que llama a emit().
        Si un observer lanza una excepción, se ignora para no bloquear
        al servidor (mismo principio de robustez que el logger).

        Args:
            event: El objeto de evento (dataclass de events.py).
        """
        with self._obs_lock:
            observers = list(self._observers)
        for observer in observers:
            try:
                observer(event)
            except Exception:
                pass
