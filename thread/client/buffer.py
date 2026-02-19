#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import queue
import threading
import sys

class EventBuffer:
    """Buffer de eventos para manejar impresiones en pantalla sin solapamiento."""

    def __init__(self):
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()

    def add_event(self, message: str):
        self._queue.put(message)

    def _process_loop(self):
        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=1.0)
                # Limpiamos la línea actual (donde está el prompt "> ") e imprimimos el mensaje
                sys.stdout.write("\r" + " " * 80 + "\r")
                print(message)
                sys.stdout.write("> ")
                sys.stdout.flush()
                self._queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        self._stop_event.set()
        self._worker.join()
