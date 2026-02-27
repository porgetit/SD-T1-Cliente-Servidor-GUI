#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cliente.py
----------
Punto de entrada principal para el cliente del chat.
Inicia la interfáz gráfica.
"""

import sys
import os
import subprocess
from client.gui_app import start_gui

def main():
    # Si ya se está ejecutando en el proceso hijo desvinculado
    if "--run-internal" in sys.argv:
        # Redirigir stderr a archivo para capturar errores del proceso silencioso
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_stderr.log")
        sys.stderr = open(log_path, "a", encoding="utf-8", buffering=1)
        import traceback
        try:
            start_gui()
        except Exception:
            traceback.print_exc()   # va al client_stderr.log
        return

    # Lógica para lanzar el proceso desvinculado (evita consola extra en Windows)
    python_exe = sys.executable
    if os.name == 'nt' and python_exe.lower().endswith("python.exe"):
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw
            
    script_path = os.path.abspath(__file__)
    
    print(f"[SISTEMA] Lanzando instancia de cliente GUI...")
    
    creationflags = 0
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        
    subprocess.Popen(
        [python_exe, script_path, "--run-internal"], 
        creationflags=creationflags,
        close_fds=True
    )
    print("[SISTEMA] Proceso cliente iniciado.")

if __name__ == "__main__":
    main()
