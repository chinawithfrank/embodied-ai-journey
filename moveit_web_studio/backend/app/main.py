import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:
    get_package_share_directory = None

from .models import PickPlaceRequest
from .ros_bridge import RosBridge
from .state import StudioState


class Connections:
    def __init__(self, state):
        self._state = state
        self._sockets = set()

    async def connect(self, socket):
        await socket.accept()
        self._sockets.add(socket)
        await socket.send_json(self._state.snapshot().model_dump(mode='json'))

    def disconnect(self, socket):
        self._sockets.discard(socket)

    async def broadcast(self):
        for socket in list(self._sockets):
            try:
                await socket.send_json(self._state.snapshot().model_dump(mode='json'))
            except RuntimeError:
                self.disconnect(socket)


@asynccontextmanager
async def lifespan(app):
    loop = asyncio.get_running_loop()
    state = StudioState()
    connections = Connections(state)
    notify = lambda: loop.call_soon_threadsafe(
        lambda: asyncio.create_task(connections.broadcast()))
    bridge = RosBridge(state, notify)
    app.state.state = state
    app.state.connections = connections
    app.state.bridge = bridge
    bridge.start()
    try:
        yield
    finally:
        bridge.shutdown()


app = FastAPI(title='MoveIt Web Studio', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'^https?://(localhost|127\.0\.0\.1|gpu)(:\d+)?$',
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


def mount_panda_assets():
    if get_package_share_directory is None:
        return
    try:
        package_path = Path(get_package_share_directory(
            'moveit_resources_panda_description'))
    except Exception:
        return
    app.mount(
        '/assets/panda', StaticFiles(directory=package_path),
        name='panda_assets')


mount_panda_assets()


@app.get('/health')
async def health():
    return app.state.state.snapshot()


@app.get('/api/status')
async def status():
    return app.state.state.snapshot()


@app.get('/api/tasks')
async def tasks():
    return app.state.state.list_tasks()


@app.post('/api/tasks', status_code=202)
async def create_task(request: PickPlaceRequest):
    task = app.state.state.create_task(request)
    try:
        app.state.bridge.submit_task(task)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    await app.state.connections.broadcast()
    return task


@app.websocket('/ws/status')
async def websocket_status(socket: WebSocket):
    await app.state.connections.connect(socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        app.state.connections.disconnect(socket)
