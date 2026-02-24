import webview
import os
import json
import pathlib
from .core import ChatClient

class Bridge:
    def __init__(self):
        self._window = None
        self._client = ChatClient(event_callback=self._handle_server_event)

    def set_window(self, window):
        self._window = window

    def _handle_server_event(self, message: str):
        """Intercepta eventos especiales o los envía al frontend JS."""
        if message == "FILE_DIALOG_REQUEST":
            files = self.select_files()
            if files:
                self._client.send_files(files)
            return

        if message == "FOLDER_DIALOG_REQUEST":
            folder = self.select_folder()
            if folder:
                self._client.set_save_path_and_accept(folder)
            return

        if message == "START_FILE_TRANSFER":
            # Iniciar el envío secuencial de la cola
            while self._client._state.file_queue:
                self._client._send_next_file()
            return

        if self._window:
            # Usamos json.dumps para un escape robusto de comillas y backslashes
            # Esto es vital para rutas de Windows (C:\Users\...)
            json_msg = json.dumps(message)
            self._window.evaluate_js(f"addEvent({json_msg})")

    def connect(self, host: str, port: int):
        try:
            self._client.connect(host, port)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_name(self, name: str):
        if self._client.set_name(name):
            if self._client._state.name_confirmed.wait(timeout=5.0):
                if self._client._state.name_error:
                    return {"status": "error", "message": self._client._state.name_error}
                return {"status": "success", "username": name}
            return {"status": "error", "message": "Tiempo de espera agotado"}
        return {"status": "error", "message": "Nombre inválido"}

    def send_command(self, command: str):
        self._client.process_command(command)
        return {"status": "sent"}

    def get_my_name(self):
        return self._client._state.name

    def get_connected_users(self):
        return self._client._state.connected_users

    def close_window(self):
        if self._window:
            self._window.destroy()

    def select_files(self):
        if self._window:
            files = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
            return files if files else []
        return []

    def select_folder(self):
        if self._window:
            folder = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            # Webview returns a tuple/list for folder too in some versions, or a single string.
            if isinstance(folder, (list, tuple)) and folder:
                return folder[0]
            return folder if folder else ""
        return ""

def start_gui(host="127.0.0.1", port=5000):
    bridge = Bridge()
    html_path = pathlib.Path(__file__).parent / "gui" / "index.html"
    
    window = webview.create_window(
        'SD Chat GUI', 
        str(html_path), 
        js_api=bridge,
        width=1000,
        height=700
    )
    bridge.set_window(window)
    webview.start(debug=True)
