from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4


app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        websocket.state.connection_id = str(uuid4())[:8]
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, sender: WebSocket, message: str):
        event = {
            "type": "message",
            "sender_id": sender.state.connection_id,
            "text": message
        }
        for connection in self.active_connections:
            await connection.send_json(event)


manager = ConnectionManager()


@app.get('/health')
def health_check():
    return {"status": "ok"}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print('Client disconnected')
