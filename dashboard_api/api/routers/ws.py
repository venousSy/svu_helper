"""
WebSocket Router
================
Provides a real-time channel for dashboard clients.
Broadcasts events (e.g. withdrawal status changes) to all connected tabs
without requiring a page refresh.
"""
import json
import asyncio
from typing import Set

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["ws"])

# ── Connection manager ────────────────────────────────────────────────────────

class _ConnectionManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("WS client connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WS client disconnected", total=len(self._connections))

    async def broadcast(self, payload: dict) -> None:
        """Sends a JSON payload to every connected client."""
        if not self._connections:
            return
        message = json.dumps(payload)
        dead: Set[WebSocket] = set()
        for ws in self._connections.copy():
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections.discard(ws)


manager = _ConnectionManager()


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/notifications")
async def notifications_ws(ws: WebSocket) -> None:
    """
    Clients connect here to receive live withdrawal status updates.
    The connection is kept alive with periodic pings.
    """
    await manager.connect(ws)
    try:
        while True:
            # Keep-alive: wait for any incoming message (client ping) or just idle
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send a ping to keep the connection alive
                await ws.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)
