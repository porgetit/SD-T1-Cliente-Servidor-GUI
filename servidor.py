#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
servidor.py
-----------
Punto de entrada principal para el servidor del chat.
Gestiona la verificación de dependencias e inicia el socket server.
"""

# 1. Verificación de dependencias (Antes de importar módulos del proyecto)
from dep_checker import bootstrap
bootstrap("servidor")

# 2. Importación de la lógica del servidor
from server.facade import ServerFacade

def main():
    # Iniciamos el servidor en el puerto 5000 por defecto
    ServerFacade(port=5000).run()

if __name__ == "__main__":
    main()
