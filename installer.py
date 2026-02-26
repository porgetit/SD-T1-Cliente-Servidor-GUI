#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
installer.py
------------
Módulo dedicado a la gestión de instalación y desvío de responsabilidades.
Centraliza la creación del venv, instalación de dependencias y re-lanzamiento.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# --- Configuración ---
PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_ROOT / "venv"
VENV_FLAG = "--running-in-venv"

def info(msg):  print(f"[INSTALADOR] [INFO]  {msg}")
def ok(msg):    print(f"[INSTALADOR] [OK]    {msg}")
def warn(msg):  print(f"[INSTALADOR] [AVISO] {msg}")
def error(msg): print(f"[INSTALADOR] [ERROR] {msg}")

def _get_os() -> str:
    return platform.system().lower()

def _get_venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def _ensure_venv() -> bool:
    """Crea el entorno virtual si no existe."""
    v_python = _get_venv_python()
    if VENV_DIR.exists() and v_python.exists():
        return True
    
    info(f"Creando entorno virtual en {VENV_DIR}...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        ok("Entorno virtual creado exitosamente.")
        return True
    except Exception as e:
        error(f"Error al crear el venv: {e}")
        return False

def _install_deps(app_type: str, os_type: str):
    """Instala las dependencias según el rol y el sistema operativo."""
    v_python = str(_get_venv_python())
    
    # 1. Dependencia común: Rich
    deps = ["rich"]
    
    # 2. Dependencias según el rol
    if app_type == "client":
        if os_type == "linux":
            info("Configurando dependencias de cliente para LINUX (usando extras GTK)...")
            deps.append("pywebview[gtk]")
        else:
            info("Configurando dependencias de cliente para WINDOWS...")
            deps.append("pywebview")
    else:
        info("Configurando dependencias para SERVIDOR...")

    info(f"Instalando/verificando paquetes: {', '.join(deps)}")
    try:
        # Usamos -m pip para asegurar que instalamos en el venv correcto
        subprocess.run([v_python, "-m", "pip", "install", "--quiet"] + deps, check=True)
        ok("Dependencias instaladas correctamente.")
        return True
    except Exception as e:
        error(f"Error al instalar dependencias: {e}")
        return False

def _relaunch_in_venv():
    """Vuelve a lanzar el script original usando el Python del venv."""
    v_python = str(_get_venv_python())
    script = os.path.abspath(sys.argv[0])
    args = sys.argv[1:] + [VENV_FLAG]
    
    info("Re-lanzando proceso dentro del entorno virtual...")
    if os.name == "nt":
        # En Windows usamos subprocess y salimos
        subprocess.run([v_python, script] + args)
        sys.exit(0)
    else:
        # En Unix usamos execv para reemplazar el proceso
        os.execv(v_python, [v_python, script] + args)

def bootstrap(app_type: str):
    """
    Punto de entrada para cliente o servidor.
    Determina si ya estamos en el venv, de lo contrario lo prepara.
    """
    # 1. Si ya tenemos el flag de venv, simplemente lo removemos y procedemos a instalar/ejecutar
    if VENV_FLAG in sys.argv:
        sys.argv.remove(VENV_FLAG)
        os_type = _get_os()
        info(f"Ejecutando dentro del VENV para [{app_type.upper()}]")
        
        # Instalamos las dependencias AQUÍ, ya dentro del venv
        if not _install_deps(app_type, os_type):
            sys.exit(1)
        return

    os_type = _get_os()
    info(f"Iniciando flujo de preparación para [{app_type.upper()}] en [{os_type.upper()}]")
    
    # 2. Asegurar que el VENV existe
    if not _ensure_venv():
        sys.exit(1)
        
    # 3. Verificar si el proceso actual es el del venv
    current_exe = Path(sys.executable).resolve()
    v_python = _get_venv_python().resolve()
    
    # Si el proceso no es el del venv, relanzamos de inmediato
    if v_python.parent not in current_exe.parents:
        info("No se detectó ejecución en VENV. Relanzando...")
        _relaunch_in_venv()
    else:
        # En caso de que se ejecute manualmente desde el venv sin el flag
        info("Ejecución detectada en VENV (manual). Verificando dependencias...")
        if not _install_deps(app_type, os_type):
            sys.exit(1)
