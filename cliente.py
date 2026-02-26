#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cliente.py
----------
Punto de entrada principal para el cliente del chat.
Gestiona la verificación de dependencias y el inicio de la GUI.
"""

import sys
import subprocess
import os

# 2. Importación de la lógica del cliente (se carga después en el proceso hijo)
def start_gui_safe():
    from client.gui_app import start_gui
    start_gui()

def main():
    # El proceso hijo/interno NO debe volver a correr bootstrap() ni el relanzador del venv
    if "--run-internal" in sys.argv or "--debug" in sys.argv:
        try:
            with open("client_launch.log", "a", encoding="utf-8") as f:
                f.write(f"[{os.getpid()}] Iniciando GUI interna con args: {sys.argv}\n")
            start_gui_safe()
        except Exception as e:
            with open("client_launch.log", "a", encoding="utf-8") as f:
                f.write(f"[{os.getpid()}] CRASH EN GUI: {e}\n")
            raise e
    else:
        # 1. Verificación de dependencias (Instalador modular)
        from installer import bootstrap
        bootstrap("client")
        
        python_exe = sys.executable
        is_debug = "--debug" in sys.argv
        
        # En Windows, usamos pythonw para el hijo desvincualdo si no es debug
        if not is_debug and python_exe.lower().endswith("python.exe"):
            pythonw = python_exe[:-10] + "pythonw.exe"
            if os.path.exists(pythonw):
                python_exe = pythonw
            
        script_path = os.path.abspath(__file__)
        project_cwd = os.path.dirname(script_path)
        
        print(f"[LLAMADA] Lanzando instancia de cliente GUI (Python: {os.path.basename(python_exe)})...")
        
        creationflags = 0
        if os.name == 'nt' and not is_debug:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            
        subprocess.Popen(
            [python_exe, script_path, "--run-internal"], 
            creationflags=creationflags,
            close_fds=True,
            cwd=project_cwd
        )
        print(f"[SISTEMA] Cliente lanzado. (Logs en {os.path.join(project_cwd, 'client_launch.log')})")

if __name__ == "__main__":
    main()
