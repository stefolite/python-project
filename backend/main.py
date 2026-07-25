from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect


app = FastAPI()


@app.get('/health')
def health_check():
    return {"status": "ok"}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'The message is: {data}')
    except WebSocketDisconnect:
        print('Client disconnected')
