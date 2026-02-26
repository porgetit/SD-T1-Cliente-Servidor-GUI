#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dep_checker.py
--------------
Módulo de verificación e instalación de dependencias.
Se ejecuta antes de arrancar el sistema (cliente o servidor).

Flujo:
  1. Detecta el sistema operativo.
  2. Verifica dependencias del sistema (solo Linux).
  3. Verifica/crea un entorno virtual (.venv).
  4. Verifica dependencias Python (pywebview, rich) dentro del venv.
  5. Si hay faltantes, las instala automáticamente.
  6. Re-lanza el script original dentro del venv para asegurar el entorno correcto.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

# Dependencias Python requeridas (se cargarán de requisitos.txt si existe)
PYTHON_DEPS = ["pywebview", "rich"] 

# Directorio raíz del proyecto (donde viven client_app.py y server_app.py)
PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_ROOT / "venv"

# Archivo de requerimientos
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

def _load_requirements():
    """Carga las dependencias desde requirements.txt para actualizar PYTHON_DEPS."""
    global PYTHON_DEPS
    if not REQUIREMENTS_FILE.exists():
        warn(f"No se encontró {REQUIREMENTS_FILE.name}. Usando valores predeterminados.")
        return

    try:
        with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if lines:
                PYTHON_DEPS = lines
                ok(f"Dependencias cargadas desde {REQUIREMENTS_FILE.name}: {', '.join(PYTHON_DEPS)}")
    except Exception as e:
        error(f"Error al leer {REQUIREMENTS_FILE.name}: {e}")

# Dependencias del sistema para Linux (apt)
# Basado en la documentación oficial de pywebview para Debian/Ubuntu/Mint
SYSTEM_DEPS_LINUX = [
    "python3-gi",
    "python3-gi-cairo",
    "gir1.2-gtk-3.0",
    "gir1.2-webkit2-4.1", # Versión moderna (Mint 21/22, Ubuntu 22/24)
]

# Flag que se añade al re-lanzar dentro del venv para evitar bucles
_VENV_FLAG = "--running-in-venv"

# ---------------------------------------------------------------------------
# Utilidades de color para la terminal
# ---------------------------------------------------------------------------

def _c(text: str, code: str) -> str:
    """Aplica color ANSI si la terminal lo soporta."""
    if sys.stdout.isatty() and os.name != 'nt' or _supports_ansi_windows():
        return f"\033[{code}m{text}\033[0m"
    return text

def _supports_ansi_windows() -> bool:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        return True
    except Exception:
        return False

def info(msg):    print(_c(f"[INFO]    {msg}", "36"))
def ok(msg):      print(_c(f"[OK]      {msg}", "32"))
def warn(msg):    print(_c(f"[AVISO]   {msg}", "33"))
def error(msg):   print(_c(f"[ERROR]   {msg}", "31"))
def header(msg):  print(_c(f"\n{'='*55}\n  {msg}\n{'='*55}", "1;34"))

# ---------------------------------------------------------------------------
# Detección de OS
# ---------------------------------------------------------------------------

def get_os() -> str:
    """Retorna 'windows', 'linux' o 'other'."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    return "other"

# ---------------------------------------------------------------------------
# Dependencias del sistema (Linux)
# ---------------------------------------------------------------------------

def _is_system_pkg_installed(pkg: str) -> bool:
    """Verifica si un paquete apt está instalado."""
    result = subprocess.run(
        ["dpkg", "-s", pkg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

def check_system_deps_linux() -> list[str]:
    """Retorna lista de paquetes del sistema que faltan."""
    missing = []
    
    # Paquetes fijos requeridos
    required_fixed = [
        "python3-gi",
        "python3-gi-cairo",
        "gir1.2-gtk-3.0",
    ]
    
    for pkg in required_fixed:
        if not _is_system_pkg_installed(pkg):
            missing.append(pkg)
            
    # Lógica de WebKit2: Buscamos 4.1 o 4.0. Si no está ninguno, pedimos el 4.1
    if not _is_system_pkg_installed("gir1.2-webkit2-4.1") and \
       not _is_system_pkg_installed("gir1.2-webkit2-4.0"):
        # Verificamos cuál existe en el repo antes de pedirlo
        # Por defecto pedimos 4.1 ya que es el estándar moderno
        missing.append("gir1.2-webkit2-4.1")
        
    return missing

def install_system_deps_linux(missing: list[str]) -> bool:
    """Instala paquetes del sistema con apt. Retorna True si tuvo éxito."""
    warn(f"Faltan dependencias del sistema: {', '.join(missing)}")
    info("Se instalarán con apt (puede requerir contraseña sudo)...")
    try:
        subprocess.run(["sudo", "apt", "update", "-qq"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "--quiet"] + missing, check=True)
        ok("Dependencias del sistema instaladas correctamente.")
        return True
    except subprocess.CalledProcessError as e:
        error(f"No se pudieron instalar las dependencias del sistema: {e}")
        error("Instálalas manualmente con:")
        error(f"  sudo apt install {' '.join(missing)}")
        return False

# ---------------------------------------------------------------------------
# Entorno virtual
# ---------------------------------------------------------------------------

def venv_python() -> Path:
    """Retorna la ruta al ejecutable Python dentro del venv."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def venv_pip() -> Path:
    """Retorna la ruta al pip dentro del venv."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def ensure_venv() -> bool:
    """Crea el venv si no existe. Retorna True si ya existía o se creó bien."""
    if VENV_DIR.exists() and venv_python().exists():
        return True
    info(f"Creando entorno virtual en {VENV_DIR} ...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        ok("Entorno virtual creado.")
        return True
    except subprocess.CalledProcessError as e:
        error(f"No se pudo crear el entorno virtual: {e}")
        return False

# ---------------------------------------------------------------------------
# Dependencias Python dentro del venv
# ---------------------------------------------------------------------------

def _is_python_pkg_installed(pkg: str) -> bool:
    """Verifica si un paquete Python está instalado en el venv."""
    result = subprocess.run(
        [str(venv_python()), "-c", f"import importlib; importlib.import_module('{_import_name(pkg)}')"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0

def _import_name(pkg: str) -> str:
    """Convierte nombre de paquete pip a nombre de import (heurística simple)."""
    mapping = {
        "pywebview": "webview",
    }
    return mapping.get(pkg, pkg.replace("-", "_"))

def check_python_deps() -> list[str]:
    """Retorna lista de paquetes Python que faltan en el venv."""
    missing = []
    for pkg in PYTHON_DEPS:
        # Especial para Linux: pywebview requiere extras [gtk]
        check_name = pkg
        if pkg == "pywebview" and get_os() == "linux":
            check_name = "pywebview[gtk]"
        
        if not _is_python_pkg_installed(pkg):
            missing.append(check_name)
    return missing

def install_python_deps(missing: list[str]) -> bool:
    """Instala paquetes Python faltantes en el venv. Retorna True si tuvo éxito."""
    warn(f"Faltan paquetes Python: {', '.join(missing)}")
    info("Instalando en el entorno virtual...")
    try:
        subprocess.run(
            [str(venv_pip()), "install", "--quiet"] + missing,
            check=True
        )
        ok(f"Paquetes instalados: {', '.join(missing)}")
        return True
    except subprocess.CalledProcessError as e:
        error(f"No se pudieron instalar los paquetes: {e}")
        return False

# ---------------------------------------------------------------------------
# Re-lanzamiento dentro del venv
# ---------------------------------------------------------------------------

def relaunch_in_venv(extra_args: list[str] = None) -> None:
    """
    Re-lanza el script original (sys.argv[0]) usando el Python del venv.
    Añade _VENV_FLAG para evitar un bucle infinito.
    Esta función NO retorna: reemplaza el proceso actual.
    """
    script = os.path.abspath(sys.argv[0])
    args = sys.argv[1:]
    if extra_args:
        args += extra_args

    cmd = [str(venv_python()), script] + args + [_VENV_FLAG]
    info(f"Re-lanzando dentro del entorno virtual...")

    if os.name == "nt":
        # En Windows no hay os.execv limpio; usamos subprocess y salimos
        subprocess.run(cmd)
        sys.exit(0)
    else:
        os.execv(str(venv_python()), cmd)

# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------

def bootstrap(app_label: str = "sistema") -> None:
    """
    Función principal. Llámala al inicio de client_app.py y server_app.py.

    Si ya estamos dentro del venv (flag presente), no hace nada.
    Si no, verifica dependencias, instala lo faltante y re-lanza si es necesario.

    Args:
        app_label: Nombre descriptivo del componente ("cliente" o "servidor"),
                   usado solo para los mensajes en consola.
    """
    # Si ya estamos corriendo dentro del venv, no hacer nada
    if _VENV_FLAG in sys.argv:
        sys.argv.remove(_VENV_FLAG)
        return

    header(f"Verificando dependencias — {app_label}")

    # -- Cargar requerimientos externos --
    _load_requirements()

    os_name = get_os()
    info(f"Sistema operativo detectado: {platform.system()} {platform.release()}")

    needs_relaunch = False

    # -- Dependencias del sistema (solo Linux/Mint/Ubuntu) --
    if os_name == "linux":
        info("Verificando dependencias del sistema (GTK + WebKit2)...")
        missing_sys = check_system_deps_linux()
        if missing_sys:
            success = install_system_deps_linux(missing_sys)
            if not success:
                sys.exit(1)
        else:
            ok("Dependencias del sistema: OK")

    elif os_name == "windows":
        info("Windows detectado — dependencias del sistema no requeridas.")

    else:
        warn(f"Sistema operativo '{platform.system()}' no probado oficialmente.")
        warn("Se intentará continuar, pero pueden fallar dependencias del sistema.")

    # -- Entorno virtual --
    info("Verificando entorno virtual...")
    venv_is_new = not VENV_DIR.exists()
    if venv_is_new:
        info("No se encontró entorno virtual. Se creará uno nuevo.")

    if not ensure_venv():
        sys.exit(1)
    ok(f"Entorno virtual: {VENV_DIR}")

    # -- Dependencias Python --
    info("Verificando dependencias Python en el entorno virtual...")
    missing_py = check_python_deps()
    if missing_py:
        needs_relaunch = True
        success = install_python_deps(missing_py)
        if not success:
            sys.exit(1)
    else:
        ok("Dependencias Python: OK")

    # -- Re-lanzar si:
    #    a) Se instaló algo nuevo en esta ejecución, o
    #    b) El venv era nuevo (primera vez), o
    #    c) El proceso actual NO está corriendo desde el venv
    
    # Verificamos si el ejecutable actual está dentro de la carpeta del venv
    current_exe = Path(sys.executable).resolve()
    target_venv_exe = venv_python().resolve()
    running_from_venv = target_venv_exe.parent in current_exe.parents

    if needs_relaunch or venv_is_new or not running_from_venv:
        relaunch_in_venv()
    else:
        info(f"Todo en orden. Iniciando {app_label}...\n")
