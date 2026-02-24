import sys
import subprocess
import os
from client.gui_app import start_gui

def main():
    # Si se pasa un flag interno, ejecutamos la GUI normalmente
    if "--run-internal" in sys.argv:
        start_gui()
    else:
        # De lo contrario, lanzamos un proceso hijo desvinculado
        # Usamos pythonw.exe para evitar que se abra una consola extra en Windows
        python_exe = sys.executable
        if python_exe.lower().endswith("python.exe"):
            python_exe = python_exe[:-10] + "pythonw.exe"
            
        if not os.path.exists(python_exe):
            python_exe = sys.executable
            
        print(f"[LLAMADA] Lanzando instancia de cliente GUI...")
        subprocess.Popen([python_exe, __file__, "--run-internal"], 
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS 
                         if os.name == 'nt' else 0,
                         close_fds=True)
        print("[SISTEMA] Cliente lanzado. Terminal liberada.")

if __name__ == "__main__":
    main()
