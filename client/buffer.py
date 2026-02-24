import queue
import threading
import sys
from typing import Optional, Callable

class EventBuffer:
    """Buffer de eventos para manejar actualizaciones de GUI."""

    def __init__(self, callback: Optional[Callable] = None):
        self._queue = queue.Queue()
        self._callback = callback
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()

    def add_event(self, message: str):
        self._queue.put(message)

    def _process_loop(self):
        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=1.0)
                if self._callback:
                    self._callback(message)
                self._queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)
