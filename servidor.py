#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
servidor.py
-----------
Punto de entrada principal para el servidor del chat.
Inicia el socket server.
"""

import os
from server.facade import ServerFacade

def main():
    # Buscamos el puerto en la variable de entorno, si no existe usamos 5000
    port = int(os.environ.get("PORT", 5000))
    ServerFacade(port=port).run()

if __name__ == "__main__":
    main()
