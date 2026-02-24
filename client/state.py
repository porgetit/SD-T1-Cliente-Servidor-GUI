#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from typing import Optional, Set, List

class ChatState:
    """Estado compartido del cliente."""

    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.pending_requests: List[str] = []
        self.open_sessions: Set[str] = set()
        self.current_target: Optional[str] = None
        self.name_confirmed = threading.Event()
        self.name_error: Optional[str] = None
