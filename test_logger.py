import socket
import time
import struct

def test_connection():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Conectando a localhost:5000...")
        s.connect(("127.0.0.1", 5000))
        print("Enviando handshake...")
        # TLV: Tipo 1 (Command), Length 14, Value "SET_NAME:Kevin"
        payload = b"SET_NAME:Kevin"
        msg = struct.pack("!BI", 1, len(payload)) + payload
        s.send(msg)
        time.sleep(2)
        print("Cerrando...")
        s.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
