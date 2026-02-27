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
        """Agrega un evento al buffer."""
        self._queue.put(message)

    def _process_loop(self):
        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=1.0)
                if self._callback:
                    try:
                        self._callback(message)
                    except Exception as e:
                        import sys
                        print(f"[EventBuffer ERROR] callback falló: {e}", file=sys.stderr, flush=True)
                self._queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        """Detiene el buffer."""
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)
