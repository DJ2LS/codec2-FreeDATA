import os
import sys
# we need to add script directory to the sys path for avoiding problems with pip package
script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_directory)

import signal
import queue
import asyncio
import threading
import time
import uvicorn
import webview  # pywebview für die GUI
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import structlog
from appdirs import user_data_dir, user_cache_dir

from config import CONFIG
import audio
import service_manager
import state_manager
import websocket_manager
import event_manager

from message_system_db_manager import DatabaseManager
from schedule_manager import ScheduleManager

from api.general import router as general_router
from api.config import router as config_router
from api.devices import router as devices_router
from api.radio import router as radio_router
from api.modem import router as modem_router
from api.freedata import router as freedata_router
from api.websocket import router as websocket_router

# Constants
CONFIG_ENV_VAR = 'FREEDATA_CONFIG'
DEFAULT_CONFIG_FILE = 'config.ini'
MODEM_VERSION = "0.16.11-alpha"
API_VERSION = 3
LICENSE = 'GPL3.0'
DOCUMENTATION_URL = 'https://wiki.freedata.app'

# adjust asyncio for Windows usage to avoid an Assertion Error
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    stop_server()

app = FastAPI(lifespan=lifespan)
app.include_router(general_router, prefix="")
app.include_router(config_router, prefix="/config")
app.include_router(devices_router, prefix="/devices")
app.include_router(radio_router, prefix="/radio")
app.include_router(modem_router, prefix="/modem")
app.include_router(freedata_router, prefix="/freedata")
app.include_router(websocket_router, prefix="")

logger = structlog.get_logger()

# Ermittlung des GUI-Verzeichnisses
potential_gui_dirs = [
    "../freedata_gui/dist",                # z.B. beim Start mit "python3 server.py"
    "freedata_gui/dist",                   # z.B. beim Start mit ./tools/run-server.py
    "FreeDATA/freedata_gui/dist",          # z.B. beim Start mit bash run-server...
    os.path.join(os.path.dirname(__file__), "gui")  # z.B. beim Start als Nuitka-Bundle
]

gui_dir = None
for dir_path in potential_gui_dirs:
    if os.path.isdir(dir_path):
        gui_dir = dir_path
        break

if gui_dir:
    app.mount("/gui", StaticFiles(directory=gui_dir, html=True), name="static")
else:
    logger.warning("GUI directory not found. Please run `npm i && npm run build` inside `freedata_gui`.")

# HTTP-Middleware (Cache-Control, Logging etc.)
@app.middleware("http")
async def http_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    logger.info(f"[API] {request.method}", url=str(request.url), response_code=response.status_code)
    return response

# CORS-Einstellungen
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def set_config():
    config_file = os.getenv(CONFIG_ENV_VAR, os.path.join(script_directory, DEFAULT_CONFIG_FILE))
    if os.path.exists(config_file):
        print(f"Using config from {config_file}")
    else:
        print(f"Config file '{config_file}' not found. Exiting.")
        sys.exit(1)
    return config_file

# Signal Handler und Serverstopp
def signal_handler(sig, frame):
    print("\n------------------------------------------")
    logger.warning("[SHUTDOWN] Received SIGINT....")
    stop_server()

def stop_server():
    if hasattr(app, 'state_manager'):
        logger.warning("[SHUTDOWN] stopping ongoing transmissions....")
        try:
            for session in app.state_manager.arq_irs_sessions.values():
                session.transmission_aborted()
            for session in app.state_manager.arq_iss_sessions.values():
                session.abort_transmission(send_stop=False)
                session.transmission_aborted()
        except Exception as e:
            print(f"Error during transmission stopping: {e}")
    if hasattr(app, 'wsm'):
        app.wsm.shutdown()
    if hasattr(app, 'radio_manager'):
        app.radio_manager.stop()
    if hasattr(app, 'schedule_manager'):
        app.schedule_manager.stop()
    if hasattr(app.service_manager, 'modem_service') and app.service_manager.modem_service:
        app.service_manager.shutdown()
    if hasattr(app.service_manager, 'modem') and app.service_manager.modem:
        app.service_manager.modem.demodulator.shutdown()
    if hasattr(app.service_manager, 'modem_service'):
        app.service_manager.stop_modem()
    if hasattr(app, 'socket_interface_manager') and app.socket_interface_manager:
        app.socket_interface_manager.stop_servers()
    audio.terminate()
    logger.warning("[SHUTDOWN] Shutdown completed")
    try:
        os._exit(0)
    except Exception as e:
        logger.warning("[SHUTDOWN] Shutdown completed", error=e)

# Startet den Uvicorn-Server in einem separaten Thread (für den WebView-Modus)
def start_uvicorn_server(modemaddress, modemport):
    uvicorn.run(app, host=modemaddress, port=modemport, log_config=None, log_level="info")

# Startet das pywebview-Fenster und definiert einen on_closed Callback,
# der beim Schließen des Fensters den Server herunterfährt.
def start_gui(url):
    print("Opening webview at:", url)

    APP_NAME = "FreeDATA"
    APP_AUTHOR = ""

    # Get the proper user data directory for the current platform
    user_data_folder = user_data_dir(APP_NAME, APP_AUTHOR)

    # Ensure the directory exists
    os.makedirs(user_data_folder, exist_ok=True)
    print(user_data_folder)
    window = webview.create_window("FreeDATA", url, width=1280, height=1024, confirm_close=True)
    window.events.closing += stop_server
    webview.settings['ALLOW_DOWNLOADS'] = True
    webview.start(icon='../freedata_gui/public/icon_cube_border.png', storage_path=user_data_folder)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    app.MODEM_VERSION = MODEM_VERSION
    app.API_VERSION = API_VERSION

    config_file = set_config()
    app.config_manager = CONFIG(config_file)
    app.p2p_data_queue = queue.Queue()
    app.state_queue = queue.Queue()
    app.modem_events = queue.Queue()
    app.modem_fft = queue.Queue()
    app.modem_service = queue.Queue()
    app.event_manager = event_manager.EventManager([app.modem_events])
    app.state_manager = state_manager.StateManager(app.state_queue)
    app.schedule_manager = ScheduleManager(app.MODEM_VERSION, app.config_manager, app.state_manager, app.event_manager)
    app.service_manager = service_manager.SM(app)
    app.modem_service.put("start")
    DatabaseManager(app.event_manager).initialize_default_values()
    DatabaseManager(app.event_manager).database_repair_and_cleanup()
    app.wsm = websocket_manager.wsm()
    app.wsm.startWorkerThreads(app)

    conf = app.config_manager.read()
    modemaddress = conf['NETWORK'].get('modemaddress', '127.0.0.1')
    modemport = int(conf['NETWORK'].get('modemport', 5000))

    if not modemaddress or modemaddress == '':
        modemaddress = '127.0.0.1'


    webview_mode = "--webview" in sys.argv
    if gui_dir and os.path.isdir(gui_dir):
        url = f"http://{modemaddress}:{modemport}/gui"
        logger.info("---------------------------------------------------")
        logger.info("                                                   ")
        logger.info(f"[GUI] AVAILABLE ON {url}")
        logger.info("                                                   ")
        logger.info("---------------------------------------------------")

        if webview_mode:
            # in WebView Mode we always want local host
            modemaddress = '127.0.0.1'
            url = f"http://{modemaddress}:{modemport}/gui"

            # WebView-Mode: Start Server then open Webview
            server_thread = threading.Thread(target=start_uvicorn_server, args=(modemaddress, modemport), daemon=True)
            server_thread.start()
            time.sleep(2)
            start_gui(url)
        else:
            # CLI-Mode: Start Server blocking
            uvicorn.run(app, host=modemaddress, port=modemport, log_config=None, log_level="info")

    else:
        logger.warning("GUI not compiled, starting server anyway")
        uvicorn.run(app, host=modemaddress, port=modemport, log_config=None, log_level="info")

if __name__ == "__main__":
    main()
