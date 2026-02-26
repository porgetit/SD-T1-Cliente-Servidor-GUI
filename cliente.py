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

# 1. Verificación de dependencias (Antes de importar módulos del proyecto)
from dep_checker import bootstrap
bootstrap("cliente")

# 2. Importación de la lógica del cliente
from client.gui_app import start_gui

def main():
    # Si se pasa un flag interno, ejecutamos la GUI normalmente (dentro del venv)
    if "--run-internal" in sys.argv:
        start_gui()
    else:
        # Lanzamos un proceso hijo desvinculado
        # Usamos pythonw.exe en Windows para evitar que se abra una consola extra
        python_exe = sys.executable
        if python_exe.lower().endswith("python.exe"):
            pythonw = python_exe[:-10] + "pythonw.exe"
            if os.path.exists(pythonw):
                python_exe = pythonw
            
        print(f"[LLAMADA] Lanzando instancia de cliente GUI...")
        
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            
        subprocess.Popen(
            [python_exe, __file__, "--run-internal"], 
            creationflags=creationflags,
            close_fds=True
        )
        print("[SISTEMA] Cliente lanzado. Terminal liberada.")

if __name__ == "__main__":
    main()
