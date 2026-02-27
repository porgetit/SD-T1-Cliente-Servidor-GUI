#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_client_logic.py
--------------------
Diagnóstico de la lógica de conexión del cliente sin GUI (sin webview).
Simula exactamente lo que hace Bridge.connect() + Bridge.set_name().

Uso: python test_client_logic.py [host] [port] [nickname]
"""

import sys
import time
import traceback

HOST     = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT     = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
NICKNAME = sys.argv[3] if len(sys.argv) > 3 else "TestUser"

print(f"[TEST] Host={HOST}  Puerto={PORT}  Nickname={NICKNAME}")
print("-" * 50)

# ── Paso 1: Inicializar el cliente ──────────────────────────────────────────
print("[1] Inicializando ChatClient...")
try:
    from client.core import ChatClient
    events_received = []

    def on_event(msg: str):
        events_received.append(msg)
        print(f"    [EVENTO] {msg!r}")

    client = ChatClient(event_callback=on_event)
    print("    OK")
except Exception as e:
    print(f"    FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Paso 2: Conectar TCP ────────────────────────────────────────────────────
print(f"\n[2] Conectando a {HOST}:{PORT}...")
try:
    client.connect(HOST, PORT)
    print("    OK - Socket conectado, MessageReceiver iniciado")
except Exception as e:
    print(f"    FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Paso 3: Enviar SET_NAME y esperar NAME_OK ─────────────────────────────
print(f"\n[3] Enviando SET_NAME:{NICKNAME} (timeout 5s)...")
try:
    sent = client.set_name(NICKNAME)
    print(f"    set_name() retornó: {sent}")

    # Esperar la confirmación del servidor (igual que Bridge.set_name)
    confirmed = client._state.name_confirmed.wait(timeout=5.0)
    if confirmed:
        if client._state.name_error:
            print(f"    RESULTADO: NOMBRE RECHAZADO → {client._state.name_error}")
        else:
            print(f"    RESULTADO: NAME_OK ✓  nombre confirmado: {client._state.name}")
    else:
        print("    RESULTADO: TIMEOUT — el servidor no respondió en 5 segundos")
except Exception as e:
    print(f"    FAIL: {e}")
    traceback.print_exc()

# ── Paso 4: Esperar eventos adicionales ────────────────────────────────────
print("\n[4] Esperando 2 segundos para capturar eventos adicionales...")
time.sleep(2)

# ── Paso 5: Desconectar ────────────────────────────────────────────────────
print("\n[5] Desconectando...")
try:
    client.disconnect()
    print("    OK")
except Exception as e:
    print(f"    FAIL: {e}")

print("\n" + "=" * 50)
print(f"TOTAL EVENTOS RECIBIDOS: {len(events_received)}")
for ev in events_received:
    print(f"  - {ev!r}")
