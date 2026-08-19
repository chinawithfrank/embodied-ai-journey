import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import MotorRequest, TaskRequest
from .recordings import RecordingManager
from .ros_bridge import RosBridge
from .state import GatewayState


class ConnectionManager:
    def __init__(self, state: GatewayState):
        self._state = state
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        await self.send_snapshot(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def send_snapshot(self, websocket: WebSocket) -> None:
        await websocket.send_json({
            'type': 'snapshot',
            'payload': self._state.snapshot().model_dump(mode='json'),
        })

    async def broadcast_snapshot(self) -> None:
        stale_connections = []
        for websocket in list(self._connections):
            try:
                await self.send_snapshot(websocket)
            except RuntimeError:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    state = GatewayState()
    connections = ConnectionManager(state)

    def notify() -> None:
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(connections.broadcast_snapshot()))

    recordings = RecordingManager(state, settings.recordings_dir, notify)
    bridge = RosBridge(state, notify)
    app.state.gateway_state = state
    app.state.connections = connections
    app.state.recordings = recordings
    app.state.bridge = bridge
    bridge.start()
    try:
        yield
    finally:
        active_recording = state.get_active_recording()
        if active_recording is not None:
            recordings.stop()
        bridge.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origin_list,
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


@app.get('/health')
async def health():
    snapshot = app.state.gateway_state.snapshot()
    return {
        'service': settings.app_name,
        'ros_available': snapshot.ros_available,
        'robot_online': snapshot.robot_online,
    }


@app.get('/api/status')
async def get_status():
    return app.state.gateway_state.snapshot()


@app.get('/api/tasks')
async def list_tasks():
    return app.state.gateway_state.list_tasks()


@app.post('/api/tasks', status_code=202)
async def create_task(request: TaskRequest):
    try:
        task = app.state.bridge.create_rotation_task(request.target_degrees)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    await app.state.connections.broadcast_snapshot()
    return task


@app.post('/api/tasks/{task_id}/cancel')
async def cancel_task(task_id: str):
    try:
        app.state.bridge.cancel_task(task_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail='Task not found.') from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await app.state.connections.broadcast_snapshot()
    return app.state.gateway_state.get_task(task_id)


@app.post('/api/motors', status_code=202)
async def set_motors(request: MotorRequest):
    try:
        app.state.bridge.set_motors(request.enabled)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {'requested_enabled': request.enabled}


@app.get('/api/logs')
async def list_logs():
    return app.state.gateway_state.list_logs()


@app.get('/api/recordings')
async def list_recordings():
    return app.state.recordings.list_recordings()


@app.post('/api/recordings', status_code=201)
async def start_recording():
    try:
        recording = app.state.recordings.start()
    except (OSError, RuntimeError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await app.state.connections.broadcast_snapshot()
    return recording


@app.post('/api/recordings/stop')
async def stop_recording():
    try:
        recording = app.state.recordings.stop()
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await app.state.connections.broadcast_snapshot()
    return recording


@app.websocket('/ws/telemetry')
async def telemetry(websocket: WebSocket):
    await app.state.connections.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.connections.disconnect(websocket)
