#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class ProtocolHandlers:
    """Manejadores de la lógica del protocolo de comunicación."""

    @staticmethod
    def dispatch(server, session, msg_type: int, payload: bytes):
        if msg_type in (0, 1):
            raw = payload.decode("utf-8")
            if raw.startswith("SET_NAME:"):
                server.handle_set_name(session, raw.split(":", 1)[1])
            elif raw.startswith("GET_USERS"):
                server.send_user_list(session)
            elif raw.startswith("REQ_CHAT:"):
                server.handle_req_chat(session, raw.split(":", 1)[1])
            elif raw.startswith("ACCEPT_CHAT:"):
                server.handle_accept_chat(session, raw.split(":", 1)[1])
            elif raw.startswith("DENY_CHAT:"):
                server.handle_deny_chat(session, raw.split(":", 1)[1])
            elif raw.startswith("STOP_CHAT:"):
                server.handle_stop_chat(session, raw.split(":", 1)[1])
            elif raw.startswith("CHAT:"):
                server.handle_chat_message(session, raw)
            elif raw.startswith("REQ_SEND_FILES:"):
                server.handle_req_send_files(session, raw.split(":", 1)[1])
            elif raw.startswith("ACCEPT_SEND_FILES:"):
                server.handle_accept_send_files(session, raw.split(":", 1)[1])
            elif raw.startswith("DENY_SEND_FILES:"):
                server.handle_deny_send_files(session, raw.split(":", 1)[1])
            elif raw.startswith("FILES_RECEIVED:"):
                server.handle_files_received(session, raw.split(":", 1)[1])
        elif msg_type == 2:
            server.handle_file_transfer(session, payload)
