from fastapi import APIRouter, Request, WebSocket
router = APIRouter()

# WebSocket Event Handlers
@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.wsm.handle_connection(websocket, websocket.app.wsm.events_client_list, websocket.app.modem_events)

@router.websocket("/fft")
async def websocket_fft(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.wsm.handle_connection(websocket, websocket.app.wsm.fft_client_list, websocket.app.modem_fft)

@router.websocket("/states")
async def websocket_states(websocket: WebSocket):
    await websocket.accept()
    await websocket.app.wsm.handle_connection(websocket, websocket.app.wsm.states_client_list, websocket.app.state_queue)
