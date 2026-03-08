"""
WebSocket routes for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

# Store active connections
connections: Dict[str, WebSocket] = {}


@router.websocket("/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates
    """
    await websocket.accept()
    connections[task_id] = websocket
    
    try:
        while True:
            # Keep connection alive and wait for client messages
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({
                "type": "echo",
                "message": data
            })
    except WebSocketDisconnect:
        if task_id in connections:
            del connections[task_id]


async def notify_task_update(task_id: str, data: dict):
    """
    Send update to connected WebSocket clients
    """
    if task_id in connections:
        await connections[task_id].send_json({
            "type": "task_update",
            "data": data
        })
