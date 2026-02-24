#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from client import ClientFacade

def main():
    print("=" * 45)
    host = input("  Ingrese la IP del servidor  : ").strip()
    port = int(input("  Ingrese el puerto del servidor: ").strip())
    print("=" * 45)

    ClientFacade().start(host, port)

if __name__ == "__main__":
    main()
