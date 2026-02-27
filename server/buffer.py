#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import queue
import threading
import traceback
from typing import Callable, Any
from .events import BufferError


class RequestBuffer:
    """Buffer de peticiones para procesar mensajes en orden de llegada."""

    def __init__(self, processor: Callable[[Any, str], None], emit: Callable[[Any], None]):
        """
        Args:
            processor: Función que procesa cada solicitud (session, msg_type, payload).
            emit:      Callable del servidor para emitir eventos de error sin acoplarse al logger.
        """
        self._queue = queue.Queue()
        self._processor = processor
        self._emit = emit
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()

    def add_request(self, session: Any, msg_type: int, payload: bytes):
        """Agrega una solicitud al buffer."""
        self._queue.put((session, msg_type, payload))

    def _process_loop(self):
        """Bucle de procesamiento de solicitudes con control de errores."""
        while not self._stop_event.is_set():
            try:
                session, msg_type, payload = self._queue.get(timeout=1.0)
                try:
                    self._processor(session, msg_type, payload)
                except Exception as e:
                    self._emit(BufferError(session.name, f"{e}\n{traceback.format_exc()}"))
                finally:
                    self._queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def stop(self):
        """Detiene el buffer."""
        self._stop_event.set()
        self._worker.join()
